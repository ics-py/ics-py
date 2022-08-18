import itertools
import operator
from typing import TYPE_CHECKING, Iterable, List, Optional, cast

import attr
import dateutil.rrule

from ics import (
    AudioAlarm,
    BaseAlarm,
    CustomAlarm,
    DisplayAlarm,
    EmailAlarm,
    NoneAlarm,
    get_type_from_action,
)
from ics.component import Component
from ics.contentline import Container, ContentLine
from ics.converter.base import AttributeConverter, GenericConverter, sort_converters
from ics.converter.component import ComponentMeta
from ics.rrule import rrule_to_ContentLine
from ics.types import ContainerItem, ContextDict, ExtraParams, copy_extra_params
from ics.utils import one
from ics.valuetype.datetime import DatetimeConverter, DatetimeConverterMixin


def unique_justseen(iterable, key=None):
    return map(next, map(operator.itemgetter(1), itertools.groupby(iterable, key)))


class RecurrenceConverter(AttributeConverter):
    @property
    def filter_ics_names(self) -> List[str]:
        return ["RRULE", "RDATE", "EXRULE", "EXDATE", "DTSTART"]

    def populate(
        self, component: Component, item: ContainerItem, context: ContextDict
    ) -> bool:
        assert isinstance(item, ContentLine)
        key = (self, "lines")
        lines = context[key]
        if lines is None:
            lines = context[key] = []
        lines.append(item)
        return True

    def post_populate(self, component: Component, context: ContextDict):
        lines_str = "".join(
            line.serialize(newline=True) for line in context.pop((self, "lines"))
        )
        # TODO only feed dateutil the params it likes, add the rest as extra
        tzinfos = context.get(DatetimeConverterMixin.CONTEXT_KEY_AVAILABLE_TZ, {})
        rrule = dateutil.rrule.rrulestr(lines_str, tzinfos=tzinfos, compatible=True)
        rrule._rdate = list(unique_justseen(sorted(rrule._rdate)))  # type: ignore
        rrule._exdate = list(unique_justseen(sorted(rrule._exdate)))  # type: ignore
        self.set_or_append_value(component, rrule)

    def serialize(self, component: Component, output: Container, context: ContextDict):
        value = self.get_value(component)
        if not TYPE_CHECKING:
            assert isinstance(value, dateutil.rrule.rruleset)
        for rrule in itertools.chain(value._rrule, value._exrule):
            if rrule._dtstart is None:
                continue
            # check that the rrule uses the same DTSTART as a possible Timespan(Converter)
            dtstart = context["DTSTART"]
            if dtstart:
                if dtstart != rrule._dtstart:
                    raise ValueError("differing DTSTART values")
            else:
                context["DTSTART"] = rrule._dtstart
                dt_value = DatetimeConverter.serialize(rrule._dtstart, context=context)
                output.append(ContentLine(name="DTSTART", value=dt_value))

        for rrule in value._rrule:
            output.append(rrule_to_ContentLine(rrule))
        for exrule in value._exrule:
            cl = rrule_to_ContentLine(exrule)
            cl.name = "EXRULE"
            output.append(cl)
        for rdate in unique_justseen(sorted(value._rdate)):
            output.append(
                ContentLine(name="RDATE", value=DatetimeConverter.serialize(rdate))
            )
        for exdate in unique_justseen(sorted(value._exdate)):
            output.append(
                ContentLine(name="EXDATE", value=DatetimeConverter.serialize(exdate))
            )

    def post_serialize(
        self, component: Component, output: Container, context: ContextDict
    ):
        context.pop("DTSTART", None)


AttributeConverter.BY_TYPE[dateutil.rrule.rruleset] = RecurrenceConverter


class AlarmActionConverter(GenericConverter):
    CONTEXT_FIELD = "ALARM_ACTION"

    @property
    def priority(self) -> int:
        return 1000

    @property
    def filter_ics_names(self) -> List[str]:
        return ["ACTION"]

    def populate(
        self, component: Component, item: ContainerItem, context: ContextDict
    ) -> bool:
        assert isinstance(item, ContentLine)
        assert issubclass(type(component), get_type_from_action(item.value))
        if item.params:
            component.extra_params["ACTION"] = copy_extra_params(item.params)
        return True

    def serialize(self, component: Component, output: Container, context: ContextDict):
        assert isinstance(component, BaseAlarm)
        output.append(
            ContentLine(
                name="ACTION",
                params=cast(ExtraParams, component.extra_params.get("ACTION", {})),
                value=component.action,
            )
        )


class AlarmMeta(ComponentMeta):
    def find_converters(self) -> Iterable[GenericConverter]:
        convs: List[GenericConverter] = [
            c
            for c in (
                AttributeConverter.get_converter_for(a)
                for a in attr.fields(self.component_type)
            )
            if c is not None
        ]
        convs.append(AlarmActionConverter())
        return sort_converters(convs)

    def load_instance(
        self, container: Container, context: Optional[ContextDict] = None
    ):
        clazz = get_type_from_action(
            one(
                container["ACTION"],
                too_short="VALARM must have exactly one ACTION!",
                too_long="VALARM must have exactly one ACTION, but got {first!r}, {second!r}, and possibly more!",
            ).value
        )
        instance = clazz()
        ComponentMeta.BY_TYPE[clazz].populate_instance(instance, container, context)
        return instance


ComponentMeta.BY_TYPE[BaseAlarm] = AlarmMeta(BaseAlarm)
ComponentMeta.BY_TYPE[AudioAlarm] = AlarmMeta(AudioAlarm)
ComponentMeta.BY_TYPE[CustomAlarm] = AlarmMeta(CustomAlarm)
ComponentMeta.BY_TYPE[DisplayAlarm] = AlarmMeta(DisplayAlarm)
ComponentMeta.BY_TYPE[EmailAlarm] = AlarmMeta(EmailAlarm)
ComponentMeta.BY_TYPE[NoneAlarm] = AlarmMeta(NoneAlarm)
