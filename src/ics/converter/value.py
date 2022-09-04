from itertools import zip_longest
from typing import Any, List, Tuple, cast, Optional

from attr import define, field

from ics.component import Component
from ics.contentline import Container, ContentLine
from ics.converter.base import AttributeConverter
from ics.types import ContainerItem, ExtraParams, copy_extra_params
from ics.valuetype.base import ValueConverter


@define
class ValueAttributeConverter(AttributeConverter):
    """
    An `AttributeConverter` that simply use one or more `ValueConverter`s to handle their (single) attribute.
    Transparently handles single-value and multi-value attributes.
    See `GenericConverter` for more information.
    """

    # Cached information for parsing and serialization.
    value_converters: List[ValueConverter] = field(init=False)

    cur_value_count: int = field(init=False, default=0)
    cur_component: Optional[Component] = field(init=False, default=None)

    def __attrs_post_init__(self):
        super().__attrs_post_init__()
        from ics.converter.context import ConverterContext
        ctx = ConverterContext.CURRENT()
        self.value_converters = [ctx.converter_factory_for_type(vt, ValueConverter) for vt in self.value_types]

    @property
    def ics_name(self) -> str:
        name = self.attribute.metadata.get("ics_name", None)
        if not name:
            name = self.attribute.name.upper().replace("_", "-").strip("-")
        return name

    @property
    def filter_ics_names(self) -> List[str]:
        return [self.ics_name]

    def populate(self, component: Component, item: ContainerItem) -> bool:
        assert isinstance(item, ContentLine)

        if self.cur_component is None:
            self.cur_component = component
            self.cur_value_count = 0
        else:
            assert self.cur_component is component

        if self.is_multi_value:
            params, converter = self.__find_value_parser(item)
            for value in converter.split_value_list(item.value):
                self.cur_value_count += 1
                params = copy_extra_params(params)
                parsed = converter.parse(value, params)  # might modify params and context
                params["__merge_next"] = ["TRUE"]
                self.set_or_append_extra_params(component, params)
                self.set_or_append_value(component, parsed)
            if params is not None:
                # note that this value was the last value in a list stored in a single ContentLine
                params["__merge_next"] = ["FALSE"]
        else:
            if self.cur_value_count > 0:
                raise ValueError("attribute %s can only be set once, second occurrence is %s" % (self.ics_name, item))
            self.cur_value_count += 1
            params, converter = self.__find_value_parser(item)
            parsed = converter.parse(item.value, params)  # might modify params and context
            self.set_or_append_extra_params(component, params)
            self.set_or_append_value(component, parsed)
        return True

    def __find_value_parser(self, line: ContentLine) -> Tuple[ExtraParams, ValueConverter]:
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
        return params, converter

    def post_populate(self, component: Component):
        if self.is_required and not self.cur_value_count:
            raise ValueError("attribute %s is required but got no value" % self.ics_name)
        self.cur_component = None
        self.cur_value_count = 0

    def serialize(self, component: Component, output: Container):
        if self.is_multi_value:
            self.__serialize_multi(component, output)
        else:
            value = self.get_value(component)
            if value is not None:
                params = copy_extra_params(cast(ExtraParams, self.get_extra_params(component)))
                converter = self.__find_value_serializer(params, value)
                serialized = converter.serialize(value, params)  # might modify params and context
                output.append(ContentLine(name=self.ics_name, params=params, value=serialized))

    def __serialize_multi(self, component: Component, output: Container):
        extra_params = cast(List[ExtraParams], self.get_extra_params(component))
        values = self.get_value_list(component)
        if extra_params and len(extra_params) != len(values):
            raise ValueError("length of extra params doesn't match length of parameters"
                             " for attribute %s of %r" % (self.attribute.name, component))

        merge_next = False
        current_params = None
        current_values = []

        for value, params in zip_longest(values, extra_params):
            merge_next = False
            params = copy_extra_params(params)
            if params.pop("__merge_next", None) == ["TRUE"]:
                merge_next = True
            converter = self.__find_value_serializer(params, value)
            serialized = converter.serialize(value, params)  # might modify params and context

            if current_params is not None:
                if current_params != params:
                    raise ValueError()
            else:
                current_params = params

            current_values.append(serialized)

            if not merge_next:
                cl = ContentLine(name=self.ics_name, params=params, value=converter.join_value_list(current_values))
                output.append(cl)
                current_params = None
                current_values = []

        if merge_next:
            raise ValueError("last value in value list may not have merge_next set")

    def __find_value_serializer(self, params: ExtraParams, value: Any) -> ValueConverter:
        for nr, converter in enumerate(self.value_converters):
            if not isinstance(value, converter.python_type): continue
            if nr > 0:
                params["VALUE"] = [converter.ics_type]
            return converter
        else:
            raise ValueError("can't convert %s %r with %s" % (type(value), value, self))


# monkeypatch ValueConverter to be callable
ValueConverter.__call__ = ValueAttributeConverter
