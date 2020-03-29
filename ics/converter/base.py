import abc
import warnings
from typing import Any, ClassVar, Dict, List, MutableSequence, Optional, TYPE_CHECKING, Tuple, Type, Union, cast

import attr

from ics.grammar import Container
from ics.types import ContainerItem

if TYPE_CHECKING:
    from ics.component import Component, ExtraParams
    from ics.converter.component import InflatedComponentMeta


class GenericConverter(abc.ABC):
    @property
    @abc.abstractmethod
    def priority(self) -> int:
        pass

    @property
    @abc.abstractmethod
    def filter_ics_names(self) -> List[str]:
        pass

    @abc.abstractmethod
    def populate(self, component: "Component", item: ContainerItem, context: Dict) -> bool:
        """
        :param context:
        :param component:
        :param item:
        :return: True, if the line was consumed and shouldn't be stored as extra (but might still be passed on)
        """
        pass

    def finalize(self, component: "Component", context: Dict):
        pass

    @abc.abstractmethod
    def serialize(self, component: "Component", output: Container, context: Dict):
        pass


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
        multi_value_type, value_type, value_types = extract_attr_type(self.attribute)
        _priority = self.attribute.metadata.get("ics_priority", self.default_priority)
        is_required = self.attribute.metadata.get("ics_required", None)
        if is_required is None:
            if not self.attribute.init:
                is_required = False
            elif self.attribute.default is not attr.NOTHING:
                is_required = False
            else:
                is_required = True
        for key, value in locals().items():  # all variables created in __attrs_post_init__ will be set on self
            if key == "self" or key.startswith("__"): continue
            object.__setattr__(self, key, value)

    def _check_component(self, component: "Component", context: Dict):
        if context[(self, "current_component")] is None:
            context[(self, "current_component")] = component
            context[(self, "current_value_count")] = 0
        else:
            if context[(self, "current_component")] is not component:
                raise ValueError("must call finalize before call to populate with another component")

    def finalize(self, component: "Component", context: Dict):
        context[(self, "current_component")] = None
        context[(self, "current_value_count")] = 0

    def set_or_append_value(self, component: "Component", value: Any):
        if self.multi_value_type is not None:
            container = getattr(component, self.attribute.name)
            if container is None:
                container = self.multi_value_type()
                setattr(component, self.attribute.name, container)
            container.append(value)
        else:
            setattr(component, self.attribute.name, value)

    def get_value(self, component: "Component") -> Any:
        return getattr(component, self.attribute.name)

    def get_value_list(self, component: "Component") -> List[Any]:
        if self.is_multi_value:
            return list(self.get_value(component))
        else:
            return [self.get_value(component)]

    def set_or_append_extra_params(self, component: "Component", value: "ExtraParams", name: Optional[str] = None):
        name = name or self.attribute.name
        if self.is_multi_value:
            extras = component.extra_params.setdefault(name, [])
            cast(List["ExtraParams"], extras).append(value)
        elif value:
            component.extra_params[name] = value

    def get_extra_params(self, component: "Component", name: Optional[str] = None) -> Union["ExtraParams", List["ExtraParams"]]:
        default: Union["ExtraParams", List["ExtraParams"]] = list() if self.multi_value_type else dict()
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
            from ics.component import Component
            if issubclass(value_type, Component):
                meta: "InflatedComponentMeta" = cast("InflatedComponentMeta", value_type.Meta)
                return meta(attribute)
            elif value_type in AttributeConverter.BY_TYPE:
                return AttributeConverter.BY_TYPE[value_type](attribute)

        from ics.converter.value import AttributeValueConverter
        return AttributeValueConverter(attribute)


def extract_attr_type(attribute: attr.Attribute) -> Tuple[Optional[Type[MutableSequence]], Type, List[Type]]:
    attr_type = attribute.metadata.get("ics_type", attribute.type)
    if attr_type is None:
        raise ValueError("can't convert attribute %s with AttributeConverter, "
                         "as it has no type information" % attribute)
    generic_origin = getattr(attr_type, "__origin__", attr_type)
    generic_vars = getattr(attr_type, "__args__", tuple())

    if generic_origin == Union:
        generic_vars = [v for v in generic_vars if v is not type(None)]
        if len(generic_vars) > 1:
            return None, generic_origin[tuple(generic_vars)], list(generic_vars)
        else:
            return None, generic_vars[0], [generic_vars[0]]

    elif issubclass(generic_origin, MutableSequence):
        if len(generic_vars) > 1:
            warnings.warn("using first parameter for List type %s" % attr_type)
        return generic_origin, generic_vars[0], [generic_vars[0]]

    else:
        return None, attr_type, [attr_type]


def ics_attr_meta(name: str = None,
                  ignore: bool = None,
                  type: Type = None,
                  required: bool = None,
                  priority: int = None,
                  converter: Type[AttributeConverter] = None) -> Dict[str, Any]:
    data: Dict[str, Any] = {}
    if name:
        data["ics_name"] = name
    if ignore is not None:
        data["ics_ignore"] = ignore
    if type is not None:
        data["ics_type"] = type
    if required is not None:
        data["ics_required"] = required
    if priority is not None:
        data["ics_priority"] = priority
    if converter is not None:
        data["ics_converter"] = converter
    return data
