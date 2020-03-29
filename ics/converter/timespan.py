from typing import Dict, List, TYPE_CHECKING, cast

from ics.converter.base import AttributeConverter
from ics.grammar import Container, ContentLine
from ics.timespan import EventTimespan, Timespan, TodoTimespan
from ics.types import ContainerItem
from ics.utils import ensure_datetime
from ics.valuetype.datetime import DateConverter, DatetimeConverter, DurationConverter

if TYPE_CHECKING:
    from ics.component import Component, ExtraParams


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
        params = dict(item.params)
        if item.name in ["DTSTART", "DTEND", "DUE"]:
            value_type = params.pop("VALUE", ["DATE-TIME"])
            if value_type == ["DATE-TIME"]:
                precision = "second"
            elif value_type == ["DATE"]:
                precision = "day"
            else:
                raise ValueError("can't handle %s with value type %s" % (item.name, value_type))

            if context["timespan_precision"] is None:
                context["timespan_precision"] = precision
            else:
                if context["timespan_precision"] != precision:
                    raise ValueError("event with diverging begin and end time precision")

            if precision == "day":
                value = DateConverter.INST.parse(item.value)
            else:
                assert precision == "second"
                value = DatetimeConverter.INST.parse(item.value)

            if item.name == "DTSTART":
                self.set_or_append_extra_params(component, params, name="begin")
                context["timespan_begin_time"] = value
            else:
                self.set_or_append_extra_params(component, params, name="end")  # FIXME due?
                context["timespan_end_time"] = value

        else:
            assert item.name == "DURATION"
            self.set_or_append_extra_params(component, params, name="duration")
            context["timespan_duration"] = DurationConverter.INST.parse(item.value)

        return True

    def finalize(self, component: "Component", context: Dict):
        self._check_component(component, context)
        self.set_or_append_value(component, self.value_type(
            ensure_datetime(context["timespan_begin_time"]),
            ensure_datetime(context["timespan_end_time"]),
            context["timespan_duration"], context["timespan_precision"]))
        super(TimespanConverter, self).finalize(component, context)

    def serialize(self, component: "Component", output: Container, context: Dict):
        self._check_component(component, context)
        value: Timespan = self.get_value(component)
        if value.is_all_day():
            value_type = {"VALUE": ["DATE"]}
            dt_conv = DateConverter.INST
        else:
            value_type = {"VALUE": ["DATE-TIME"]}
            dt_conv = DatetimeConverter.INST

        if value.get_begin():
            params: "ExtraParams" = cast("ExtraParams", self.get_extra_params(component, "begin"))
            params = dict(**params, **value_type)
            output.append(ContentLine(name="DTSTART", params=params, value=dt_conv.serialize(value.get_begin())))

        if value.get_end_representation() == "end":
            end_name = {"end": "DTEND", "due": "DUE"}[value._end_name()]
            params = cast("ExtraParams", self.get_extra_params(component, end_name))
            params = dict(**params, **value_type)
            output.append(ContentLine(name=end_name, params=params, value=dt_conv.serialize(value.get_effective_end())))

        elif value.get_end_representation() == "duration":
            params = cast("ExtraParams", self.get_extra_params(component, "duration"))
            output.append(ContentLine(
                name="DURATION",
                params=params,
                value=DurationConverter.INST.serialize(value.get_effective_duration())))


AttributeConverter.BY_TYPE[Timespan] = TimespanConverter
AttributeConverter.BY_TYPE[EventTimespan] = TimespanConverter
AttributeConverter.BY_TYPE[TodoTimespan] = TimespanConverter
