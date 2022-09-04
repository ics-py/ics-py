import abc
import warnings
from typing import Any, List, MutableSequence, Optional, Type, Union, cast, Tuple

from attr import define, field, Attribute, NOTHING

from ics.component import Component
from ics.contentline import Container
from ics.types import ContainerItem, ExtraParams

try:
    from functools import cached_property
except ImportError:
    cached_property = property


# TODO make validation / ValueError / warnings configurable
# TODO use repr for warning messages and ensure that they don't get to long

class GenericConverter(abc.ABC):
    """
    A Converter is responsible for serializing and parsing a certain aspect (usually a member variable) of a Component.
    See `AttributeConverter` for Converters that can handle exactly one member variable, i.e. one attribute.
    See `AttributeValueConverter` for Converters that simply use one or more `ValueConverter`s to handle their attribute.
    See also `SubcomponentConverter`, which converts between a single attribute whose type is a subclass of `Component`
      and a `Container` of `ContentLines`, using the `ComponentMeta` information of the subclass stored in the `ConverterContext`.
    `SubcomponentConverter` then uses `ComponentMeta.load_instance` and `ComponentMeta.serialize_instance` to inflate
      and serialize `Component` instances.
    """

    @classmethod
    def copy(cls):
        return cls

    @property
    @abc.abstractmethod
    def priority(self) -> int:
        ...

    @property
    @abc.abstractmethod
    def filter_ics_names(self) -> List[str]:
        ...

    @abc.abstractmethod
    def populate(self, component: Component, item: ContainerItem) -> bool:
        """
        Parse the `ContentLine` or `Container` `item` (which matches one of the names returned by `filter_ics_names`)
        and add the information extracted from it to `component`.

        :param component:
        :param item:
        :return: True, if the line was consumed and shouldn't be stored as extra (but might still be passed on)
        """
        raise NotImplementedError()

    def post_populate(self, component: Component):
        """
        Called once a `component` is fully populated.
        """
        pass

    @abc.abstractmethod
    def serialize(self, component: Component, output: Container):
        """
        Serialize the aspect handled by this Converter.
        Take all the relevant information from `component` (and possibly the current context),
        somehow (possibly using a `ValueConverter`) convert it to ContentLine(s) or Container(s)
        and append all of them to `output`.
        """
        raise NotImplementedError()

    def post_serialize(self, component: Component, output: Container):
        """
        Called once a `component` is fully serialized to `output`.
        """
        pass


@define
class AttributeConverter(GenericConverter, abc.ABC):
    """
    An abstract Converter that can serialize and populate a single of attribute of some Component.
    See `GenericConverter` for more information.
    """

    """
    The attribute (and thus also the Component class) this AttributeConverter instance can handle.
    """
    attribute: Attribute

    """
    If this attribute can have multiple values, the type of the container to store these values in,
    e.g. `List` or `Set`. `None` if only a single value is allowed.
    """
    multi_value_type: Optional[Type[MutableSequence]] = field(default=None)
    """
    A type matching all allowed values of the `attribute`, e.g. `str` or `Union[int, float]`.
    If the attribute can have multiple values, the `multi_value_type` was stripped.
    """
    value_type: Type = field(default=None)
    """
    All concrete types a value of this attribute might have, e.g. `[str]` or `[int, float]`.
    This value contains all types obtained by unwrapping the Sequence type for `multi_value_type`s
    and also unwrapping any `Union`s and `Optional`s, stripping any `None` values.
    """
    value_types: List[Type] = field(default=None)

    def __attrs_post_init__(self):
        if not self.value_types:
            self.multi_value_type, self.value_type, self.value_types = extract_attr_type(self.attribute)

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

    def set_or_append_extra_params(self, component: Component, value: ExtraParams, name: Optional[str] = None):
        name = (name or self.attribute.name).upper()
        if self.is_multi_value:
            extras = component.extra_params.setdefault(name, [])
            cast(List[ExtraParams], extras).append(value)
        elif value:
            component.extra_params[name] = value

    def get_extra_params(self, component: Component, name: Optional[str] = None) -> Union[ExtraParams, List[ExtraParams]]:
        if self.multi_value_type:
            default: Union[ExtraParams, List[ExtraParams]] = cast(List[ExtraParams], list())
        else:
            default = ExtraParams(dict())
        name = (name or self.attribute.name).upper()
        return component.extra_params.get(name, default)

    @property
    def default_priority(self) -> int:
        return 0

    @cached_property
    def priority(self) -> int:
        return self.attribute.metadata.get("ics_priority", self.default_priority)

    @cached_property
    def is_required(self) -> bool:
        # XXX we ignore if value_type is Optional and only focus on the presence of a default value
        return self.attribute.metadata.get("ics_required", self.attribute.init and (self.attribute.default is NOTHING))

    @property
    def is_multi_value(self) -> bool:
        return self.multi_value_type is not None


def extract_attr_type(attribute: Attribute) -> Tuple[Optional[Type[MutableSequence]], Type, List[Type]]:
    """
    Extract type information on an `attribute` from its metadata.

    :return: a tuple of `multi_value_type, value_type, value_types`
        See the respective attributes of `AttributeConverter` for their meaning.
    """
    attr_type = attribute.metadata.get("ics_type", attribute.type)
    if attr_type is None:
        raise ValueError("can't convert attribute %s with AttributeConverter, "
                         "as it has no type information" % attribute)
    return unwrap_type(attr_type)


def unwrap_type(attr_type: Type) -> Tuple[Optional[Type[MutableSequence]], Type, List[Type]]:
    """
    Unwrap types wrapped by a generic `Union`, `Optional` or `Sequence` type.

    :return: a tuple of `multi_value_type, value_type, value_types`
        See the respective attributes of `AttributeConverter` for their meaning.
    """
    generic_origin = getattr(attr_type, "__origin__", attr_type)
    generic_vars: Tuple[Type, ...] = getattr(attr_type, "__args__", tuple())

    if generic_origin == Union:
        generic_vars = tuple(v for v in generic_vars if v not in (None, type(None)))
        if len(generic_vars) > 1:
            return None, generic_origin[tuple(generic_vars)], list(generic_vars)
        else:
            return None, generic_vars[0], [generic_vars[0]]

    elif issubclass(generic_origin, MutableSequence):
        if len(generic_vars) > 1:
            warnings.warn("using first parameter for List type %s" % attr_type)
        res = unwrap_type(generic_vars[0])
        assert res[0] is None
        return generic_origin, res[1], res[2]

    else:
        return None, attr_type, [attr_type]


class SubcomponentConverter(AttributeConverter):
    """
    An `AttributeConverter` that converts between a single attribute whose type is a subclass of `Component`
      and a `Container` of `ContentLines`, using the context-provided `ComponentMeta` for the subclass.
    Uses `ComponentMeta.load_instance` and `ComponentMeta.serialize_instance` to inflate
      and serialize `Component` instances.
    Transparently handles single-value and multi-value attributes.
    See `GenericConverter` for more information.
    """

    @property
    def filter_ics_names(self) -> List[str]:
        return [self.value_type.NAME]

    def populate(self, component: Component, item: ContainerItem) -> bool:
        assert isinstance(item, Container)
        self.set_or_append_value(component, self.value_type.from_container(item))
        return True

    def serialize(self, parent: Component, output: Container):
        extras = self.get_extra_params(parent)
        if extras:
            raise ValueError("ComponentConverter %s can't serialize extra params %s", (self, extras))
        for value in self.get_value_list(parent):
            output.append(value.to_container())
