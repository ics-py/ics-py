from typing import List

from attr import Attribute
from dateutil.rrule import rruleset

from ics.alarm import *
from ics.attendee import Attendee, Organizer, Person
from ics.component import Component
from ics.converter.base import AttributeConverter
from ics.converter.component import ComponentMeta
from ics.contentline import Container, ContentLine
from ics.types import ContainerItem, ContextDict

__all__ = [
    "RecurrenceConverter",
    "PersonConverter",
    "AlarmConverter",
]


class RecurrenceConverter(AttributeConverter):
    # TODO handle extras?
    # TODO pass and handle available_tz / tzinfos

    @property
    def filter_ics_names(self) -> List[str]:
        return ["RRULE", "RDATE", "EXRULE", "EXDATE", "DTSTART"]

    def populate(self, component: Component, item: ContainerItem, context: ContextDict) -> bool:
        assert isinstance(item, ContentLine)
        self._check_component(component, context)
        # self.lines.append(item)
        return False

    def finalize(self, component: Component, context: ContextDict):
        self._check_component(component, context)
        # rrulestr("\r\n".join(self.lines), tzinfos={}, compatible=True)

    def serialize(self, component: Component, output: Container, context: ContextDict):
        pass
        # value = rruleset()
        # for rrule in value._rrule:
        #     output.append(ContentLine("RRULE", value=re.match("^RRULE:(.*)$", str(rrule)).group(1)))
        # for exrule in value._exrule:
        #     output.append(ContentLine("EXRULE", value=re.match("^RRULE:(.*)$", str(exrule)).group(1)))
        # for rdate in value._rdate:
        #     output.append(ContentLine(name="RDATE", value=DatetimeConverter.INST.serialize(rdate)))
        # for exdate in value._exdate:
        #     output.append(ContentLine(name="EXDATE", value=DatetimeConverter.INST.serialize(exdate)))


AttributeConverter.BY_TYPE[rruleset] = RecurrenceConverter


class PersonConverter(AttributeConverter):
    # TODO handle lists

    @property
    def filter_ics_names(self) -> List[str]:
        return []

    def populate(self, component: Component, item: ContainerItem, context: ContextDict) -> bool:
        assert isinstance(item, ContentLine)
        self._check_component(component, context)
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
        self._check_component(component, context)
        self.set_or_append_value(component, get_type_from_action(item).from_container(item, context))
        return True

    def serialize(self, parent: Component, output: Container, context: ContextDict):
        self._check_component(parent, context)
        extras = self.get_extra_params(parent)
        if extras:
            raise ValueError("ComponentConverter %s can't serialize extra params %s", (self, extras))
        for value in self.get_value_list(parent):
            output.append(value.to_container(context))


class AlarmMeta(ComponentMeta):
    def __call__(self, attribute: Attribute):
        return AlarmMemberComponentConverter(attribute)


ComponentMeta.BY_TYPE[BaseAlarm] = AlarmMeta(BaseAlarm)
ComponentMeta.BY_TYPE[AudioAlarm] = AlarmMeta(AudioAlarm)
ComponentMeta.BY_TYPE[CustomAlarm] = AlarmMeta(CustomAlarm)
ComponentMeta.BY_TYPE[DisplayAlarm] = AlarmMeta(DisplayAlarm)
ComponentMeta.BY_TYPE[EmailAlarm] = AlarmMeta(EmailAlarm)
ComponentMeta.BY_TYPE[NoneAlarm] = AlarmMeta(NoneAlarm)
