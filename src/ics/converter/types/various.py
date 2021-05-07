import itertools
import operator
from typing import List, TYPE_CHECKING

import dateutil.rrule
from attr import Attribute

from ics import NoneAlarm, EmailAlarm, DisplayAlarm, CustomAlarm, AudioAlarm, BaseAlarm, get_type_from_action
from ics.attendee import Attendee, Organizer, Person
from ics.component import Component
from ics.converter.base import AttributeConverter
from ics.converter.component import ComponentMeta
from ics.contentline import Container, ContentLine
from ics.rrule import rrule_to_ContentLine
from ics.types import ContainerItem, ContextDict
from ics.valuetype.datetime import DatetimeConverterMixin, DatetimeConverter


def unique_justseen(iterable, key=None):
    return map(next, map(operator.itemgetter(1), itertools.groupby(iterable, key)))


class RecurrenceConverter(AttributeConverter):
    @property
    def filter_ics_names(self) -> List[str]:
        return ["RRULE", "RDATE", "EXRULE", "EXDATE", "DTSTART"]

    def populate(self, component: Component, item: ContainerItem, context: ContextDict) -> bool:
        assert isinstance(item, ContentLine)
        key = (self, "lines")
        lines = context[key]
        if lines is None:
            lines = context[key] = []
        lines.append(item)
        return True

    def post_populate(self, component: Component, context: ContextDict):
        lines_str = "".join(line.serialize(newline=True) for line in context.pop((self, "lines")))
        # TODO only feed dateutil the params it likes, add the rest as extra
        tzinfos = context.get(DatetimeConverterMixin.CONTEXT_KEY_AVAILABLE_TZ, {})
        rrule = dateutil.rrule.rrulestr(lines_str, tzinfos=tzinfos, compatible=True)
        rrule._rdate = list(unique_justseen(sorted(rrule._rdate)))
        rrule._exdate = list(unique_justseen(sorted(rrule._exdate)))
        self.set_or_append_value(component, rrule)

    def serialize(self, component: Component, output: Container, context: ContextDict):
        value = self.get_value(component)
        if not TYPE_CHECKING:
            assert isinstance(value, dateutil.rrule.rruleset)
        for rrule in itertools.chain(value._rrule, value._exrule):
            if rrule._dtstart is None: continue
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
            output.append(ContentLine(name="RDATE", value=DatetimeConverter.serialize(rdate)))
        for exdate in unique_justseen(sorted(value._exdate)):
            output.append(ContentLine(name="EXDATE", value=DatetimeConverter.serialize(exdate)))

    def post_serialize(self, component: Component, output: Container, context: ContextDict):
        context.pop("DTSTART", None)


AttributeConverter.BY_TYPE[dateutil.rrule.rruleset] = RecurrenceConverter


class PersonConverter(AttributeConverter):
    # TODO handle lists

    @property
    def filter_ics_names(self) -> List[str]:
        return []

    def populate(self, component: Component, item: ContainerItem, context: ContextDict) -> bool:
        assert isinstance(item, ContentLine)
        return False

    def serialize(self, component: Component, output: Container, context: ContextDict):
        pass


AttributeConverter.BY_TYPE[Person] = PersonConverter
AttributeConverter.BY_TYPE[Attendee] = PersonConverter
AttributeConverter.BY_TYPE[Organizer] = PersonConverter


class AlarmMemberComponentConverter(AttributeConverter):
    @property
    def filter_ics_names(self) -> List[str]:
        return [BaseAlarm.NAME]

    def populate(self, component: Component, item: ContainerItem, context: ContextDict) -> bool:
        assert isinstance(item, Container)
        self.set_or_append_value(component, get_type_from_action(item).from_container(item, context))
        return True

    def serialize(self, parent: Component, output: Container, context: ContextDict):
        extras = self.get_extra_params(parent)
        if extras:
            raise ValueError("ComponentConverter %s can't serialize extra params %s", (self, extras))
        for value in self.get_value_list(parent):
            output.append(value.to_container(context))


class AlarmMeta(ComponentMeta):
    def __call__(self, attribute: Attribute):
        return AlarmMemberComponentConverter(attribute)


ComponentMeta.BY_TYPE[BaseAlarm] = AlarmMeta(BaseAlarm)
ComponentMeta.BY_TYPE[AudioAlarm] = ComponentMeta(AudioAlarm)
ComponentMeta.BY_TYPE[CustomAlarm] = ComponentMeta(CustomAlarm)
ComponentMeta.BY_TYPE[DisplayAlarm] = ComponentMeta(DisplayAlarm)
ComponentMeta.BY_TYPE[EmailAlarm] = ComponentMeta(EmailAlarm)
ComponentMeta.BY_TYPE[NoneAlarm] = ComponentMeta(NoneAlarm)
