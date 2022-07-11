from typing import List, cast

from ics.component import Component
from ics.contentline import Container, ContentLine
from ics.converter.base import AttributeConverter
from ics.timespan import EventTimespan, Timespan, TodoTimespan
from ics.types import ContainerItem, ContextDict, ExtraParams, copy_extra_params
from ics.utils import ensure_datetime
from ics.valuetype.base import ValueConverter
from ics.valuetype.datetime import DateConverter, DatetimeConverter, DurationConverter

CONTEXT_BEGIN_TIME = "timespan_begin_time"
CONTEXT_END_TIME = "timespan_end_time"
CONTEXT_DURATION = "timespan_duration"
CONTEXT_PRECISION = "timespan_precision"
CONTEXT_END_NAME = "timespan_end_name"
CONTEXT_ITEMS = "timespan_items"
CONTEXT_KEYS = [
    CONTEXT_BEGIN_TIME,
    CONTEXT_END_TIME,
    CONTEXT_DURATION,
    CONTEXT_PRECISION,
    CONTEXT_END_NAME,
    CONTEXT_ITEMS,
]


class TimespanConverter(AttributeConverter):
    @property
    def default_priority(self) -> int:
        return 1000

    @property
    def filter_ics_names(self) -> List[str]:
        return ["DTSTART", "DTEND", "DUE", "DURATION"]

    def populate(
        self, component: Component, item: ContainerItem, context: ContextDict
    ) -> bool:
        assert isinstance(item, ContentLine)
        seen_items = context.setdefault(CONTEXT_ITEMS, set())
        if item.name in seen_items:
            raise ValueError(f"duplicate value for {item.name} in {item}")
        seen_items.add(item.name)

        params = copy_extra_params(item.params)
        if item.name in ["DTSTART", "DTEND", "DUE"]:
            value_type = params.pop("VALUE", ["DATE-TIME"])
            if value_type == ["DATE-TIME"]:
                precision = "second"
                value = DatetimeConverter.parse(item.value, params, context)
            elif value_type == ["DATE"]:
                precision = "day"
                value = DateConverter.parse(item.value, params, context)
            else:
                raise ValueError(
                    f"can't handle {item.name} with value type {value_type}"
                )

            if context.setdefault(CONTEXT_PRECISION, precision) != precision:
                raise ValueError("event with diverging begin and end time precision")

            if item.name == "DTSTART":
                self.set_or_append_extra_params(component, params, name="begin")
                context[CONTEXT_BEGIN_TIME] = value
            else:
                end_name = {"DTEND": "end", "DUE": "due"}[item.name]
                context[CONTEXT_END_NAME] = end_name
                self.set_or_append_extra_params(component, params, name=end_name)
                context[CONTEXT_END_TIME] = value

        else:
            assert item.name == "DURATION"
            self.set_or_append_extra_params(component, params, name="duration")
            context[CONTEXT_DURATION] = DurationConverter.parse(
                item.value, params, context
            )

        return True

    def post_populate(self, component: Component, context: ContextDict):
        timespan_type = getattr(component, "_TIMESPAN_TYPE", self.value_type)
        timespan = timespan_type(
            ensure_datetime(context[CONTEXT_BEGIN_TIME]),
            ensure_datetime(context[CONTEXT_END_TIME]),
            context[CONTEXT_DURATION],
            context[CONTEXT_PRECISION],
        )
        # missing values will be reported by the Timespan validator
        if (
            context[CONTEXT_END_NAME]
            and context[CONTEXT_END_NAME] != timespan._end_name()
        ):
            raise ValueError(
                "expected to get %s value, but got %s instead"
                % (timespan._end_name(), context[CONTEXT_END_NAME])
            )
        self.set_or_append_value(component, timespan)
        # we need to clear all values, otherwise they might not get overwritten by the next parsed Timespan
        for key in CONTEXT_KEYS:
            context.pop(key, None)

    def serialize(self, component: Component, output: Container, context: ContextDict):
        value: Timespan = self.get_value(component)
        dt_conv: ValueConverter
        if value.is_all_day():
            value_type = {"VALUE": ["DATE"]}
            dt_conv = DateConverter
        else:
            value_type = {}  # implicit default is {"VALUE": ["DATE-TIME"]}
            dt_conv = DatetimeConverter

        if value.get_begin():
            # prevent rrule serializer from adding its own DTSTART value
            assert "DTSTART" not in context
            context["DTSTART"] = value.get_begin()

            params = copy_extra_params(
                cast(ExtraParams, self.get_extra_params(component, "begin"))
            )
            params.update(value_type)
            dt_value = dt_conv.serialize(value.get_begin(), params, context)
            output.append(ContentLine(name="DTSTART", params=params, value=dt_value))

        if value.get_end_representation() == "end":
            end_name = {"end": "DTEND", "due": "DUE"}[value._end_name()]
            params = copy_extra_params(
                cast(ExtraParams, self.get_extra_params(component, end_name))
            )
            params.update(value_type)
            dt_value = dt_conv.serialize(value.get_effective_end(), params, context)
            output.append(ContentLine(name=end_name, params=params, value=dt_value))

        elif value.get_end_representation() == "duration":
            params = copy_extra_params(
                cast(ExtraParams, self.get_extra_params(component, "duration"))
            )
            duration = value.get_effective_duration()
            assert duration is not None
            dur_value = DurationConverter.serialize(duration, params, context)
            output.append(ContentLine(name="DURATION", params=params, value=dur_value))

    def post_serialize(
        self, component: Component, output: Container, context: ContextDict
    ):
        context.pop("DTSTART", None)


AttributeConverter.BY_TYPE[Timespan] = TimespanConverter
AttributeConverter.BY_TYPE[EventTimespan] = TimespanConverter
AttributeConverter.BY_TYPE[TodoTimespan] = TimespanConverter
