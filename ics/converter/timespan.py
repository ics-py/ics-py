from typing import Dict, List, TYPE_CHECKING, cast

from ics.converter.base import AttributeConverter
from ics.grammar import Container, ContentLine
from ics.timespan import EventTimespan, Timespan, TodoTimespan
from ics.types import ContainerItem, ExtraParams, copy_extra_params
from ics.utils import ensure_datetime
from ics.valuetype.datetime import DateConverter, DatetimeConverter, DurationConverter

if TYPE_CHECKING:
    from ics.component import Component

CONTEXT_BEGIN_TIME = "timespan_begin_time"
CONTEXT_END_TIME = "timespan_end_time"
CONTEXT_DURATION = "timespan_duration"
CONTEXT_PRECISION = "timespan_precision"
CONTEXT_END_NAME = "timespan_end_name"
CONTEXT_ITEMS = "timespan_items"
CONTEXT_KEYS = [CONTEXT_BEGIN_TIME, CONTEXT_END_TIME, CONTEXT_DURATION,
                CONTEXT_PRECISION, CONTEXT_END_NAME, CONTEXT_ITEMS]


class TimespanConverter(AttributeConverter):
    @property
    def default_priority(self) -> int:
        return 10000

    @property
    def filter_ics_names(self) -> List[str]:
        return ["DTSTART", "DTEND", "DUE", "DURATION"]

    def populate(self, component: "Component", item: ContainerItem, context: Dict) -> bool:
        assert isinstance(item, ContentLine)
        self._check_component(component, context)

        seen_items = context.setdefault(CONTEXT_ITEMS, set())
        if item.name in seen_items:
            raise ValueError("duplicate value for %s in %s" % (item.name, item))
        seen_items.add(item.name)

        params = copy_extra_params(item.params)
        if item.name in ["DTSTART", "DTEND", "DUE"]:
            value_type = params.pop("VALUE", ["DATE-TIME"])
            if value_type == ["DATE-TIME"]:
                precision = "second"
            elif value_type == ["DATE"]:
                precision = "day"
            else:
                raise ValueError("can't handle %s with value type %s" % (item.name, value_type))

            if context[CONTEXT_PRECISION] is None:
                context[CONTEXT_PRECISION] = precision
            else:
                if context[CONTEXT_PRECISION] != precision:
                    raise ValueError("event with diverging begin and end time precision")

            if precision == "day":
                value = DateConverter.INST.parse(item.value, params, context)
            else:
                assert precision == "second"
                value = DatetimeConverter.INST.parse(item.value, params, context)

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
            context[CONTEXT_DURATION] = DurationConverter.INST.parse(item.value, params, context)

        return True

    def finalize(self, component: "Component", context: Dict):
        self._check_component(component, context)
        # missing values will be reported by the Timespan validator
        timespan = self.value_type(
            ensure_datetime(context[CONTEXT_BEGIN_TIME]), ensure_datetime(context[CONTEXT_END_TIME]),
            context[CONTEXT_DURATION], context[CONTEXT_PRECISION])
        if context[CONTEXT_END_NAME] and context[CONTEXT_END_NAME] != timespan._end_name():
            raise ValueError("expected to get %s value, but got %s instead"
                             % (timespan._end_name(), context[CONTEXT_END_NAME]))
        self.set_or_append_value(component, timespan)
        super(TimespanConverter, self).finalize(component, context)
        # we need to clear all values, otherwise they might not get overwritten by the next parsed Timespan
        for key in CONTEXT_KEYS:
            context.pop(key, None)

    def serialize(self, component: "Component", output: Container, context: Dict):
        self._check_component(component, context)
        value: Timespan = self.get_value(component)
        if value.is_all_day():
            value_type = {"VALUE": ["DATE"]}
            dt_conv = DateConverter.INST
        else:
            value_type = {}  # implicit default is {"VALUE": ["DATE-TIME"]}
            dt_conv = DatetimeConverter.INST

        if value.get_begin():
            params = copy_extra_params(cast(ExtraParams, self.get_extra_params(component, "begin")))
            params.update(value_type)
            dt_value = dt_conv.serialize(value.get_begin(), params, context)
            output.append(ContentLine(name="DTSTART", params=params, value=dt_value))

        if value.get_end_representation() == "end":
            end_name = {"end": "DTEND", "due": "DUE"}[value._end_name()]
            params = copy_extra_params(cast(ExtraParams, self.get_extra_params(component, end_name)))
            params.update(value_type)
            dt_value = dt_conv.serialize(value.get_effective_end(), params, context)
            output.append(ContentLine(name=end_name, params=params, value=dt_value))

        elif value.get_end_representation() == "duration":
            params = copy_extra_params(cast(ExtraParams, self.get_extra_params(component, "duration")))
            dur_value = DurationConverter.INST.serialize(value.get_effective_duration(), params, context)
            output.append(ContentLine(name="DURATION", params=params, value=dur_value))


AttributeConverter.BY_TYPE[Timespan] = TimespanConverter
AttributeConverter.BY_TYPE[EventTimespan] = TimespanConverter
AttributeConverter.BY_TYPE[TodoTimespan] = TimespanConverter
