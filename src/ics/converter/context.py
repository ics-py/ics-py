import functools
from collections import defaultdict
from contextvars import ContextVar
from types import SimpleNamespace
from typing import Dict, Type, Callable, List, Optional, Iterable, TypeVar

import dateutil.rrule
from attr import define, field, Attribute, fields

from ics import Container
from ics.component import ComponentType, Component
from ics.converter.base import GenericConverter, extract_attr_type, SubcomponentConverter
from ics.converter.value import ValueAttributeConverter
from ics.utils import check_is_instance

try:
    from typing import Protocol
except ImportError:
    Protocol = object

T = TypeVar('T')

CURRENT_CONVERTER = ContextVar('CURRENT_CONVERTER')


class ConverterFactory(Protocol):
    """
    Something that gives you an AttributeConverter if you call it with an attr.Attribute.
    This includes ValueConverter (monkey-patched by ValueAttributeConverter), ComponentMeta, and any AttributeConverter subclass:

        Key                ConverterFactory            ConverterFactory.call(attr)
        Type            -> ValueConverter           -> ValueAttributeConverter*
        Type            -> Type[AttributeConverter] -> AttributeConverter*
        Type[Component] -> ComponentMeta*           -> SubcomponentConverter*

    *: stores state and cannot be shared between Converter instances / threads, see ConverterFactory.copy
    """

    def __call__(self, a: Attribute) -> GenericConverter:
        pass

    def copy(self) -> "ConverterFactory":
        pass


def sets_self_as_cur_converter(f):
    @functools.wraps(f)
    def wrapper(self, *args, **kwargs):
        if CURRENT_CONVERTER.get() == self:
            return f(self, *args, **kwargs)
        else:
            reset = CURRENT_CONVERTER.set(self)
            try:
                return f(self, *args, **kwargs)
            finally:
                CURRENT_CONVERTER.reset(reset)

    return wrapper


@define
class ConverterContext(object):
    """
    Non-threadsafe central entry point to (de-)serialization.
    Holds a mapping of types to (contextmanager-local, non-threadsafe) Converter instances.
    Sets itself as CURRENT_CONVERTER when used as entry point.
    Knows how to instantiate yet unused Converters from its value_converters (ValueConverter.BY_TYPE) and component_converters (ComponentMeta.BY_TYPE) settings.
    """

    @classmethod
    def CURRENT(cls):
        conv = CURRENT_CONVERTER.get(None)
        if conv is None:
            conv = ConverterContext()
            CURRENT_CONVERTER.set(conv)
            conv.initialize_default()
        return conv

    @sets_self_as_cur_converter
    def from_container(self, cls: Type[ComponentType], container: Container) -> ComponentType:
        return self.converter_factory_for_type(cls, ComponentMeta).load_instance(container)

    @sets_self_as_cur_converter
    def populate(self, component: Component, container: Container):
        self.converter_factory_for_type(type(component), ComponentMeta).populate_instance(component, container)

    @sets_self_as_cur_converter
    def to_container(self, component: Component) -> Container:
        return self.converter_factory_for_type(type(component), ComponentMeta).serialize_instance(component)

    ###############################################

    data = field(factory=SimpleNamespace)
    # error = attr.ib(factory=ErrorNamespace)
    converters: Dict[Type, ConverterFactory] = field(factory=dict, init=False)

    def copy_from(self, other: "ConverterContext"):
        for t, conv in other.converters.items():
            self.converters[t] = conv.copy()

    def initialize_default(self):
        self.converters.clear()

        from ics.valuetype.base import ValueConverter
        import ics.valuetype.datetime
        import ics.valuetype.generic
        import ics.valuetype.special
        import ics.valuetype.text
        __keep = [ics.valuetype.datetime, ics.valuetype.generic, ics.valuetype.special, ics.valuetype.text]
        for vc in ValueConverter.INSTANCES:
            self.converters[vc.python_type] = vc

        from ics import Calendar, Timespan, EventTimespan, TodoTimespan, NoneAlarm, EmailAlarm, DisplayAlarm, CustomAlarm, AudioAlarm, BaseAlarm, Timezone

        from ics.converter.types.various import AlarmMeta, RecurrenceConverter
        self.converters[dateutil.rrule.rruleset] = RecurrenceConverter
        self.converters[BaseAlarm] = AlarmMeta(BaseAlarm)
        self.converters[AudioAlarm] = AlarmMeta(AudioAlarm)
        self.converters[CustomAlarm] = AlarmMeta(CustomAlarm)
        self.converters[DisplayAlarm] = AlarmMeta(DisplayAlarm)
        self.converters[EmailAlarm] = AlarmMeta(EmailAlarm)
        self.converters[NoneAlarm] = AlarmMeta(NoneAlarm)

        from ics.converter.types.timespan import TimespanConverter
        self.converters[Timespan] = TimespanConverter
        self.converters[EventTimespan] = TimespanConverter
        self.converters[TodoTimespan] = TimespanConverter

        from ics.timezone import TimezoneObservance
        from ics.converter.types.timezone import TimezoneMeta, TimezoneObservanceMeta
        self.converters[TimezoneObservance] = TimezoneObservanceMeta(TimezoneObservance)
        # TODO
        # self.converters[TimezoneStandardObservance] = ImmutableComponentMeta(TimezoneStandardObservance)
        # self.converters[TimezoneDaylightObservance] = ImmutableComponentMeta(TimezoneDaylightObservance)
        self.converters[Timezone] = TimezoneMeta(Timezone)

        # prevent default ComponentMeta initialization, but build CalendarMeta last
        self.converters[Calendar] = None

        for ct in Component.SUBTYPES:
            if ct not in self.converters:
                self.converters[ct] = ComponentMeta(ct)

        from ics.converter.types.calendar import CalendarMeta
        self.converters[Calendar] = CalendarMeta(Calendar)

    ###############################################

    def converter_factory_for_type(self, cls: Type, conv_type: Type[T] = ConverterFactory) -> T:
        conv = self.converters.get(cls, None)
        if conv is None:
            raise ValueError("No converter known for type %s!" % cls)
        if conv_type is not ConverterFactory and not isinstance(conv, conv_type):
            raise ValueError("Got converter %s for type %s, but expected a %s!" % (conv, cls, conv_type))
        return conv

    def converter_for_attribute(self, attribute: Attribute) -> Optional[GenericConverter]:
        """
        Create a Converter instance for field `attribute` of some class.
        FIXME:
        First check whether the `value_type` (see `extract_attr_type`) is a subclass of `Component`
          and use a `SubcomponentConverter` from the registered `ComponentMeta.BY_TYPE` if that was the case.
        Then, see if an explicit `AttributeConverter.BY_TYPE` was registered
          and create an appropriate instance for the `attribute` if that was the case.
        As last resort, create a `AttributeValueConverter` and hope that `ValueConverter.BY_TYPE` contains
          `ValueConverter`s for all possible types.

        Whether multi-value attributes are correctly handled depends on the `Converter` used,
          `AttributeValueConverter` and `SubcomponentConverter` correctly handle multi-value attributes.
        Note that `Union`s can only by handled by `AttributeValueConverter`.
        """
        if attribute.metadata.get("ics_ignore", not attribute.init):
            return None
        converter = attribute.metadata.get("ics_converter", None)
        if converter:
            return converter(attribute)

        multi_value_type, value_type, value_types = extract_attr_type(attribute)
        if len(value_types) == 1:
            assert [value_type] == value_types
            return self.converter_factory_for_type(value_type)(attribute)
        else:
            attr_type = attribute.metadata.get("ics_type", attribute.type)
            if attr_type in self.converters:
                return self.converter_factory_for_type(value_type)(attribute)
            else:
                return ValueAttributeConverter(attribute)


@define
class ComponentMeta(object):
    """
    Meta information on how a subclass of `Component`, the `component_type`, needs to be parsed and serialized.
    All needed information is generated upon instantiation of this class and cached for later use.
    Existing instances can be looked up `BY_TYPE`.
    """

    component_type: Type[Component]

    populate_lookup: Dict[str, List[GenericConverter]] = field(init=False)
    post_populate_hooks: List[Callable] = field(init=False, factory=list)

    serialize_order_pre: List[GenericConverter] = field(init=False, factory=list)
    serialize_order_post: List[GenericConverter] = field(init=False, factory=list)
    post_serialize_hooks: List[Callable] = field(init=False, factory=list)

    def __attrs_post_init__(self):
        self.populate_lookup = defaultdict(list)
        converters = sorted(filter(bool, self.find_attribute_converters()),
                            key=lambda c: c.priority, reverse=True)
        for converter in converters:
            if converter.priority >= 0:
                self.serialize_order_pre.append(converter)
            else:
                self.serialize_order_post.append(converter)
            for name in converter.filter_ics_names:
                self.populate_lookup[name].append(converter)
            # ignore the hooks if they're the still the base-class no-ops
            if GenericConverter.post_populate not in (
                    converter.post_populate, getattr(converter.post_populate, "__func__", None)
            ):
                self.post_populate_hooks.append(converter.post_populate)
            if GenericConverter.post_serialize not in (
                    converter.post_serialize, getattr(converter.post_serialize, "__func__", None)
            ):
                self.post_serialize_hooks.append(converter.post_serialize)

    @property
    def converters(self):
        return self.serialize_order_pre + self.serialize_order_post

    def __call__(self, attribute: Attribute) -> SubcomponentConverter:
        return SubcomponentConverter(attribute)

    def copy(self):
        return type(self)(self.component_type)

    def find_attribute_converters(self) -> Iterable[GenericConverter]:
        """
        Get a sorted list of all converters needed for instances of `component_type`.
        Override this method to modify the auto-discovered list of converters.
        """
        return (ConverterContext.CURRENT().converter_for_attribute(a) for a in fields(self.component_type))

    def load_instance(self, container: Container):
        """
        Create and populate an instance of `component_type` from `container`.
        """
        instance = self.component_type()
        self.populate_instance(instance, container)
        return instance

    def populate_instance(self, instance: Component, container: Container):
        if container.name != self.component_type.NAME:
            raise ValueError("container {} is no {}".format(container.name, self.component_type.NAME))
        check_is_instance("instance", instance, self.component_type)
        self._populate_attrs(instance, container)

    def _populate_attrs(self, instance: Component, container: Container):
        for line in container:
            consumed = False
            for conv in self.populate_lookup.get(line.name, []):
                if conv.populate(instance, line):
                    consumed = True
            if not consumed:
                instance.extra.append(line)

        for hook in self.post_populate_hooks:
            hook(instance)

    def serialize_instance(self, component: Component):
        check_is_instance("instance", component, self.component_type)
        container = Container(component.extra.name)  # allow overwriting the name by setting the name of the extras
        self._serialize_attrs(component, container)
        return container

    def _serialize_attrs(self, component: Component, container: Container):
        for conv in self.serialize_order_pre:
            conv.serialize(component, container)
        container.extend(component.extra)
        for conv in self.serialize_order_post:
            conv.serialize(component, container)
        for hook in self.post_serialize_hooks:
            hook(component, container)
