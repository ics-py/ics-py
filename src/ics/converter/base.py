import warnings

import abc
import attr
from types import SimpleNamespace
from typing import Any, ClassVar, Dict, List, MutableSequence, Optional, Tuple, Type, Union, cast, Iterable

from ics.component import Component
from ics.contentline import Container
from ics.types import ContainerItem, ContextDict, ExtraParams

NoneTypes = [type(None), None]

__all__ = [
    "GenericConverter",
    "AttributeConverter",
    "extract_attr_type",
    "unwrap_type",
]


# TODO make validation / ValueError / warnings configurable
# TODO use repr for warning messages and ensure that they don't get to long

class GenericConverter(abc.ABC):
    @property
    @abc.abstractmethod
    def priority(self) -> int:
        ...

    @property
    @abc.abstractmethod
    def filter_ics_names(self) -> List[str]:
        ...

    @abc.abstractmethod
    def populate(self, component: Component, item: ContainerItem, context: ContextDict) -> bool:
        """
        :param context:
        :param component:
        :param item:
        :return: True, if the line was consumed and shouldn't be stored as extra (but might still be passed on)
        """
        raise NotImplementedError()

    def post_populate(self, component: Component, context: ContextDict):
        raise NotImplementedError()

    @abc.abstractmethod
    def serialize(self, component: Component, output: Container, context: ContextDict):
        raise NotImplementedError()

    def post_serialize(self, component: Component, output: Container, context: ContextDict):
        raise NotImplementedError()


@attr.s(frozen=True)
class AttributeConverter(GenericConverter, abc.ABC):
    BY_TYPE: ClassVar[Dict[Type, Type["AttributeConverter"]]] = {}

    attribute: attr.Attribute = attr.ib()

    multi_value_type: Optional[Type[MutableSequence]]
    value_type: Type
    value_types: List[Type]
    _priority: int
    is_required: bool

    def __attrs_post_init__(self):
        v = SimpleNamespace()
        v.multi_value_type, v.value_type, v.value_types = extract_attr_type(self.attribute)
        v._priority = self.attribute.metadata.get("ics_priority", self.default_priority)
        v.is_required = self.attribute.metadata.get("ics_required", None)
        if v.is_required is None:
            if not self.attribute.init:
                v.is_required = False
            elif self.attribute.default is not attr.NOTHING:
                v.is_required = False
            else:
                v.is_required = True
        for key, value in v.__dict__.items():  # all variables created in __attrs_post_init__.v will be set on self
            object.__setattr__(self, key, value)

    def set_or_append_value(self, component: Component, value: Any):
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
        if self.is_multi_value:
            return list(self.get_value(component))
        else:
            return [self.get_value(component)]

    def set_or_append_extra_params(self, component: Component, value: ExtraParams, name: Optional[str] = None):
        name = name or self.attribute.name
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
        name = name or self.attribute.name
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


def extract_attr_type(attribute: attr.Attribute) -> Tuple[Optional[Type[MutableSequence]], Type, List[Type]]:
    attr_type = attribute.metadata.get("ics_type", attribute.type)
    if attr_type is None:
        raise ValueError("can't convert attribute %s with AttributeConverter, "
                         "as it has no type information" % attribute)
    return unwrap_type(attr_type)


def unwrap_type(attr_type: Type) -> Tuple[Optional[Type[MutableSequence]], Type, List[Type]]:
    generic_origin = getattr(attr_type, "__origin__", attr_type)
    generic_vars = getattr(attr_type, "__args__", tuple())

    if generic_origin == Union:
        generic_vars = [v for v in generic_vars if v not in NoneTypes]
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


def sort_converters(converters: Iterable[Optional[GenericConverter]]) -> List[GenericConverter]:
    converters = cast(Iterable[GenericConverter], filter(bool, converters))
    return sorted(converters, key=lambda c: c.priority, reverse=True)
