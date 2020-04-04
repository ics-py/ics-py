from typing import Any, List, TYPE_CHECKING, Tuple, cast

import attr

from ics.converter.base import AttributeConverter
from ics.grammar import Container, ContentLine
from ics.types import ContainerItem, ContextDict, ExtraParams, copy_extra_params
from ics.valuetype.base import ValueConverter

if TYPE_CHECKING:
    from ics.component import Component


@attr.s(frozen=True)
class AttributeValueConverter(AttributeConverter):
    value_converters: List[ValueConverter]

    def __attrs_post_init__(self):
        super(AttributeValueConverter, self).__attrs_post_init__()
        object.__setattr__(self, "value_converters", [])
        for value_type in self.value_types:
            converter = ValueConverter.BY_TYPE.get(value_type, None)
            if converter is None:
                raise ValueError("can't convert %s with ValueConverter" % value_type)
            self.value_converters.append(converter)

    @property
    def filter_ics_names(self) -> List[str]:
        return [self.ics_name]

    @property
    def ics_name(self) -> str:
        name = self.attribute.metadata.get("ics_name", None)
        if not name:
            name = self.attribute.name.upper().replace("_", "-").strip("-")
        return name

    def __parse_value(self, line: "ContentLine", value: str, context: ContextDict) -> Tuple[ExtraParams, ValueConverter]:
        params = copy_extra_params(line.params)
        value_type = params.pop("VALUE", None)
        if value_type:
            if len(value_type) != 1:
                raise ValueError("multiple VALUE type definitions in %s" % line)
            for converter in self.value_converters:
                if converter.ics_type == value_type[0]:
                    break
            else:
                raise ValueError("can't convert %s with %s" % (line, self))
        else:
            converter = self.value_converters[0]
        parsed = converter.parse(value, params, context)  # might modify params and context
        return params, parsed

    # TODO make storing/writing extra values/params configurably optional, but warn when information is lost

    def populate(self, component: "Component", item: ContainerItem, context: ContextDict) -> bool:
        assert isinstance(item, ContentLine)
        self._check_component(component, context)
        if self.is_multi_value:
            params = None
            for value in item.value_list:
                context[(self, "current_value_count")] += 1
                params, parsed = self.__parse_value(item, value, context)
                params["__merge_next"] = True  # type: ignore
                self.set_or_append_extra_params(component, params)
                self.set_or_append_value(component, parsed)
            if params is not None:
                params["__merge_next"] = False  # type: ignore
        else:
            if context[(self, "current_value_count")] > 0:
                raise ValueError("attribute %s can only be set once, second occurrence is %s" % (self.ics_name, item))
            context[(self, "current_value_count")] += 1
            params, parsed = self.__parse_value(item, item.value, context)
            self.set_or_append_extra_params(component, params)
            self.set_or_append_value(component, parsed)
        return True

    def finalize(self, component: "Component", context: ContextDict):
        self._check_component(component, context)
        if self.is_required and context[(self, "current_value_count")] < 1:
            raise ValueError("attribute %s is required but got no value" % self.ics_name)
        super(AttributeValueConverter, self).finalize(component, context)

    def __find_value_converter(self, params: ExtraParams, value: Any) -> ValueConverter:
        for nr, converter in enumerate(self.value_converters):
            if not isinstance(value, converter.python_type): continue
            if nr > 0:
                params["VALUE"] = [converter.ics_type]
            return converter
        else:
            raise ValueError("can't convert %s with %s" % (value, self))

    def serialize(self, component: "Component", output: Container, context: ContextDict):
        if self.is_multi_value:
            self.__serialize_multi(component, output, context)
        else:
            value = self.get_value(component)
            if value:
                params = copy_extra_params(cast(ExtraParams, self.get_extra_params(component)))
                converter = self.__find_value_converter(params, value)
                serialized = converter.serialize(value, params, context)
                output.append(ContentLine(name=self.ics_name, params=params, value=serialized))

    def __serialize_multi(self, component: "Component", output: "Container", context: ContextDict):
        extra_params = cast(List[ExtraParams], self.get_extra_params(component))
        values = self.get_value_list(component)
        if len(extra_params) != len(values):
            raise ValueError("length of extra params doesn't match length of parameters"
                             " for attribute %s of %r" % (self.attribute.name, component))

        merge_next = False
        current_params = None
        current_values = []

        for value, params in zip(values, extra_params):
            merge_next = False
            params = copy_extra_params(params)
            if params.pop("__merge_next", False):  # type: ignore
                merge_next = True
            converter = self.__find_value_converter(params, value)
            serialized = converter.serialize(value, params, context)  # might modify params and context

            if current_params is not None:
                if current_params != params:
                    raise ValueError()
            else:
                current_params = params

            current_values.append(serialized)

            if not merge_next:
                cl = ContentLine(name=self.ics_name, params=params)
                cl.value_list = current_values
                output.append(cl)
                current_params = None
                current_values = []

        if merge_next:
            raise ValueError("last value in value list may not have merge_next set")
