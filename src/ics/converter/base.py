import abc
import warnings
from types import SimpleNamespace
from typing import (
    Any,
    ClassVar,
    Dict,
    Iterable,
    List,
    MutableSequence,
    Optional,
    Tuple,
    Type,
    Union,
    cast,
)

import attr

from ics.component import Component
from ics.contentline import Container
from ics.types import ContainerItem, ContextDict, ExtraParams

NoneTypes = [type(None), None]


# TODO make validation / ValueError / warnings configurable
# TODO use repr for warning messages and ensure that they don't get to long


class GenericConverter(abc.ABC):
    """
    A Converter is responsible for serializing and parsing a certain aspect (usually a member variable) of a Component.
    See `AttributeConverter` for Converters that can handle exactly one member variable, i.e. one attribute.
    See `AttributeValueConverter` for Converters that simply use one or more `ValueConverter`s to handle their attribute.
    See `MemberComponentConverter` which converts between a single attribute whose type is a subclass of `Component`
      and a `Container` of `ContentLines`, using the information stored in the `ComponentMeta` of the subclass.
    `MemberComponentConverter` then uses `ComponentMeta.load_instance` and `ComponentMeta.serialize_toplevel` to inflate
      and serialize `Component` instances.
    """

    @property
    @abc.abstractmethod
    def priority(self) -> int:
        ...

    @property
    @abc.abstractmethod
    def filter_ics_names(self) -> List[str]:
        ...

    @abc.abstractmethod
    def populate(
        self, component: Component, item: ContainerItem, context: ContextDict
    ) -> bool:
        """
        Parse the `ContentLine` or `Container` `item` (which matches one of the name returned by `filter_ics_names`)
        and add the information extracted from it to `component`.

        :param context:
        :param component:
        :param item:
        :return: True, if the line was consumed and shouldn't be stored as extra (but might still be passed on)
        """
        raise NotImplementedError()

    def post_populate(self, component: Component, context: ContextDict):
        """
        Called once a `component` is fully populated.
        """
        pass

    @abc.abstractmethod
    def serialize(self, component: Component, output: Container, context: ContextDict):
        """
        Serialize the aspect handled by this Converter.
        Take all the relevant information from `component` (and possibly `context`),
        somehow (possibly using a `ValueConverter`) convert it to ContentLine(s) or Container(s)
        and append all of them to `output`.
        """
        raise NotImplementedError()

    def post_serialize(
        self, component: Component, output: Container, context: ContextDict
    ):
        """
        Called once a `component` is fully serialized to `output`.
        """
        pass


@attr.s(frozen=True)
class AttributeConverter(GenericConverter, abc.ABC):
    """
    A Converter that can serialize and populate a single of attribute of some Component.
    See `GenericConverter` for more information.
    """

    """
    A mapping which describes which attribute types can be handled by which AttributeConverter subclasses.
    To obtain a Converter instance, use `AttributeConverter.BY_TYPE[value_type](attribute)`.
    See `extract_attr_type` for how to extract the value type.
    Used by `ComponentMeta.find_converters` to find all converters for a Components' attributes.
    """
    BY_TYPE: ClassVar[Dict[Type, Type["AttributeConverter"]]] = {}

    """
    The attribute (and thus also the Component class) this AttributeConverter instance can handle.
    """
    attribute: attr.Attribute = attr.ib()

    """
    If this attribute can have multiple values, the type of the container to store these values in,
    e.g. `List` or `Set`. `None` if only a single value is allowed.
    """
    multi_value_type: Optional[Type[MutableSequence]]
    """
    A type matching all allowed values of the `attribute`, e.g. `str` or `Union[int, float]`.
    """
    value_type: Type
    """
    All concrete types a value of this attribute might have, e.g. `[str]` or `[int, float]`.
    """
    value_types: List[Type]
    _priority: int
    is_required: bool

    def __attrs_post_init__(self):
        v = SimpleNamespace()
        v.multi_value_type, v.value_type, v.value_types = extract_attr_type(
            self.attribute
        )
        v._priority = self.attribute.metadata.get("ics_priority", self.default_priority)
        v.is_required = self.attribute.metadata.get("ics_required", None)
        if v.is_required is None:
            if not self.attribute.init:
                v.is_required = False
            elif self.attribute.default is not attr.NOTHING:
                v.is_required = False
            else:
                v.is_required = True
                # we ignore if value_type is Optional and only focus on the presence of a default value
        for key, value in v.__dict__.items():
            # all variables created in __attrs_post_init__.v will be set on self
            object.__setattr__(self, key, value)

    def set_or_append_value(self, component: Component, value: Any):
        """
        Set the value of a single-valued attribute or append a value to a container attribute,
        optionally creating a `multi_value_type` container if the attribute was `None`.
        """
        if self.multi_value_type is not None:
            container = getattr(component, self.attribute.name)
            if container is None:
                container = self.multi_value_type()
                setattr(component, self.attribute.name, container)
            container.append(value)
        else:
            setattr(component, self.attribute.name, value)

    def get_value(self, component: Component) -> Any:
        return getattr(component, self.attribute.name)

    def get_value_list(self, component: Component) -> List[Any]:
        """
        Get the list of multiple values or the single value wrapped in a list.
        """
        if self.is_multi_value:
            return list(self.get_value(component))
        else:
            return [self.get_value(component)]

    def set_or_append_extra_params(
        self, component: Component, value: ExtraParams, name: Optional[str] = None
    ):
        name = (name or self.attribute.name).upper()
        if self.is_multi_value:
            extras = component.extra_params.setdefault(name, [])
            cast(List[ExtraParams], extras).append(value)
        elif value:
            component.extra_params[name] = value

    def get_extra_params(
        self, component: Component, name: Optional[str] = None
    ) -> Union[ExtraParams, List[ExtraParams]]:
        if self.multi_value_type:
            default: Union[ExtraParams, List[ExtraParams]] = cast(
                List[ExtraParams], list()
            )
        else:
            default = ExtraParams(dict())
        name = (name or self.attribute.name).upper()
        return component.extra_params.get(name, default)

    @property
    def default_priority(self) -> int:
        return 0

    @property
    def priority(self) -> int:
        return self._priority

    @property
    def is_multi_value(self) -> bool:
        return self.multi_value_type is not None

    @staticmethod
    def get_converter_for(attribute: attr.Attribute) -> Optional["AttributeConverter"]:
        """
        Create a Converter instance for field `attribute` of some class.
        First check whether the `value_type` (see `extract_attr_type`) is a subclass of `Component`
          and use a `MemberComponentConverter` from the registered `ComponentMeta.BY_TYPE` if that was the case.
        Then, see if an explicit `AttributeConverter.BY_TYPE` was registered
          and create an appropriate instance for the `attribute` if that was the case.
        As last resort, create a `AttributeValueConverter` and hope that `ValueConverter.BY_TYPE` contains
          `ValueConverter`s for all possible types.

        Whether multi-value attributes are correctly handled depends on the `Converter` used,
          `AttributeValueConverter` and `MemberComponentConverter` correctly handle multi-value attributes.
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
            from ics.converter.component import ComponentMeta

            if value_type in ComponentMeta.BY_TYPE:
                return ComponentMeta.BY_TYPE[value_type](attribute)
            if value_type in AttributeConverter.BY_TYPE:
                return AttributeConverter.BY_TYPE[value_type](attribute)

        from ics.converter.value import AttributeValueConverter

        return AttributeValueConverter(attribute)


def extract_attr_type(
    attribute: attr.Attribute,
) -> Tuple[Optional[Type[MutableSequence]], Type, List[Type]]:
    """
    Extract type information on an `attribute` from its metadata.

    :return: a tuple of `multi_value_type, value_type, value_types`
        See the respective attributes of `AttributeConverter` for their meaning.
    """
    attr_type = attribute.metadata.get("ics_type", attribute.type)
    if attr_type is None:
        raise ValueError(
            "can't convert attribute %s with AttributeConverter, "
            "as it has no type information" % attribute
        )
    return unwrap_type(attr_type)


def unwrap_type(
    attr_type: Type,
) -> Tuple[Optional[Type[MutableSequence]], Type, List[Type]]:
    """
    Unwrap types wrapped by a generic `Union`, `Optional` or `Container` type.

    :return: a tuple of `multi_value_type, value_type, value_types`
        See the respective attributes of `AttributeConverter` for their meaning.
    """
    generic_origin = getattr(attr_type, "__origin__", attr_type)
    generic_vars: Tuple[Type, ...] = getattr(attr_type, "__args__", tuple())

    if generic_origin == Union:
        generic_vars = tuple(v for v in generic_vars if v not in NoneTypes)
        if len(generic_vars) > 1:
            return None, generic_origin[tuple(generic_vars)], list(generic_vars)
        else:
            return None, generic_vars[0], [generic_vars[0]]

    elif issubclass(generic_origin, MutableSequence):
        if len(generic_vars) > 1:
            warnings.warn(f"using first parameter for List type {attr_type}")
        res = unwrap_type(generic_vars[0])
        assert res[0] is None
        return generic_origin, res[1], res[2]

    else:
        return None, attr_type, [attr_type]


def sort_converters(
    converters: Iterable[Optional[GenericConverter]],
) -> List[GenericConverter]:
    """
    Sort a list of converters according to their priority.
    """
    converters = cast(Iterable[GenericConverter], filter(bool, converters))
    return sorted(converters, key=lambda c: c.priority, reverse=True)
