from itertools import zip_longest
from typing import Any, List, Tuple, cast

import attr

from ics.component import Component
from ics.contentline import Container, ContentLine
from ics.converter.base import AttributeConverter
from ics.types import ContainerItem, ContextDict, ExtraParams, copy_extra_params
from ics.valuetype.base import ValueConverter


@attr.s(frozen=True)
class AttributeValueConverter(AttributeConverter):
    """
    An `AttributeConverter` that simply use one or more `ValueConverter`s to handle their (single) attribute.
    Transparently handles single-value and multi-value attributes.
    See `GenericConverter` for more information.
    """

    # Cached information for parsing and serialization.
    value_converters: List[ValueConverter]

    def __attrs_post_init__(self):
        super().__attrs_post_init__()
        object.__setattr__(self, "value_converters", [])
        for value_type in self.value_types:
            converter = ValueConverter.BY_TYPE.get(value_type, None)
            if converter is None:
                raise ValueError(
                    "can't convert attribute {} of type {} with ValueConverter".format(
                        self.attribute, value_type
                    )
                )
            self.value_converters.append(converter)

    @property
    def ics_name(self) -> str:
        name = self.attribute.metadata.get("ics_name", None)
        if not name:
            name = self.attribute.name.upper().replace("_", "-").strip("-")
        return name

    @property
    def filter_ics_names(self) -> List[str]:
        return [self.ics_name]

    def populate(
        self, component: Component, item: ContainerItem, context: ContextDict
    ) -> bool:
        assert isinstance(item, ContentLine)

        if context[(self, "current_component")] is None:
            context[(self, "current_component")] = component
            context[(self, "current_value_count")] = 0
        else:
            assert context[(self, "current_component")] is component

        if self.is_multi_value:
            params, converter = self.__prepare_params(item)
            for value in converter.split_value_list(item.value):
                context[(self, "current_value_count")] += 1
                params = copy_extra_params(params)
                parsed = converter.parse(
                    value, params, context
                )  # might modify params and context
                params["__merge_next"] = ["TRUE"]
                self.set_or_append_extra_params(component, params)
                self.set_or_append_value(component, parsed)
            if params is not None:
                # note that this value was the last value in a list stored in a single ContentLine
                params["__merge_next"] = ["FALSE"]
        else:
            if context[(self, "current_value_count")] > 0:
                raise ValueError(
                    "attribute {} can only be set once, second occurrence is {}".format(
                        self.ics_name, item
                    )
                )
            context[(self, "current_value_count")] += 1
            params, converter = self.__prepare_params(item)
            parsed = converter.parse(
                item.value, params, context
            )  # might modify params and context
            self.set_or_append_extra_params(component, params)
            self.set_or_append_value(component, parsed)
        return True

    # TODO make storing/writing extra values/params configurably optional, but warn when information is lost
    # TODO better handling of multi-type attributes, maybe try all available converters if no direct candidate was found / worked

    def __prepare_params(self, line: ContentLine) -> Tuple[ExtraParams, ValueConverter]:
        params = copy_extra_params(line.params)
        value_type = params.pop("VALUE", None)
        if value_type:
            if len(value_type) != 1:
                raise ValueError(f"multiple VALUE type definitions in {line}")
            for converter in self.value_converters:
                if converter.ics_type == value_type[0]:
                    break
            else:
                raise ValueError(f"can't convert {line} with {self}")
        else:
            converter = self.value_converters[0]
        return params, converter

    def post_populate(self, component: Component, context: ContextDict):
        if self.is_required and not context[(self, "current_value_count")]:
            raise ValueError(f"attribute {self.ics_name} is required but got no value")
        context[(self, "current_component")] = None
        context[(self, "current_value_count")] = 0

    def serialize(self, component: Component, output: Container, context: ContextDict):
        if self.is_multi_value:
            self.__serialize_multi(component, output, context)
        else:
            value = self.get_value(component)
            if value is not None:
                params = copy_extra_params(
                    cast(ExtraParams, self.get_extra_params(component))
                )
                converter = self.__find_value_converter(params, value)
                serialized = converter.serialize(value, params, context)
                output.append(
                    ContentLine(name=self.ics_name, params=params, value=serialized)
                )

    def __serialize_multi(
        self, component: Component, output: Container, context: ContextDict
    ):
        extra_params = cast(List[ExtraParams], self.get_extra_params(component))
        values = self.get_value_list(component)
        if extra_params and len(extra_params) != len(values):
            raise ValueError(
                "length of extra params doesn't match length of parameters"
                " for attribute %s of %r" % (self.attribute.name, component)
            )

        merge_next = False
        current_params = None
        current_values = []

        for value, params in zip_longest(values, extra_params):
            merge_next = False
            params = copy_extra_params(params)
            if params.pop("__merge_next", None) == ["TRUE"]:
                merge_next = True
            converter = self.__find_value_converter(params, value)
            serialized = converter.serialize(
                value, params, context
            )  # might modify params and context

            if current_params is not None:
                if current_params != params:
                    raise ValueError()
            else:
                current_params = params

            current_values.append(serialized)

            if not merge_next:
                cl = ContentLine(
                    name=self.ics_name,
                    params=params,
                    value=converter.join_value_list(current_values),
                )
                output.append(cl)
                current_params = None
                current_values = []

        if merge_next:
            raise ValueError("last value in value list may not have merge_next set")

    def __find_value_converter(self, params: ExtraParams, value: Any) -> ValueConverter:
        for nr, converter in enumerate(self.value_converters):
            if not isinstance(value, converter.python_type):
                continue
            if nr > 0:
                params["VALUE"] = [converter.ics_type]
            return converter
        else:
            raise ValueError(f"can't convert {type(value)} {value!r} with {self}")
