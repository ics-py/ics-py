from typing import List, TYPE_CHECKING

from dateutil.rrule import rruleset

from ics.attendee import Attendee, Organizer, Person
from ics.converter.base import AttributeConverter
from ics.converter.component import MemberComponentConverter
from ics.contentline import Container, ContentLine
from ics.types import ContainerItem, ContextDict

if TYPE_CHECKING:
    from ics.component import Component


class RecurrenceConverter(AttributeConverter):
    # TODO handle extras?
    # TODO pass and handle available_tz / tzinfos

    @property
    def filter_ics_names(self) -> List[str]:
        return ["RRULE", "RDATE", "EXRULE", "EXDATE", "DTSTART"]

    def populate(self, component: "Component", item: ContainerItem, context: ContextDict) -> bool:
        assert isinstance(item, ContentLine)
        self._check_component(component, context)
        # self.lines.append(item)
        return False

    def finalize(self, component: "Component", context: ContextDict):
        self._check_component(component, context)
        # rrulestr("\r\n".join(self.lines), tzinfos={}, compatible=True)

    def serialize(self, component: "Component", output: Container, context: ContextDict):
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

    def populate(self, component: "Component", item: ContainerItem, context: ContextDict) -> bool:
        assert isinstance(item, ContentLine)
        self._check_component(component, context)
        return False

    def serialize(self, component: "Component", output: Container, context: ContextDict):
        pass


AttributeConverter.BY_TYPE[Person] = PersonConverter
AttributeConverter.BY_TYPE[Attendee] = PersonConverter
AttributeConverter.BY_TYPE[Organizer] = PersonConverter


class AlarmConverter(MemberComponentConverter):
    def populate(self, component: "Component", item: ContainerItem, context: ContextDict) -> bool:
        # TODO handle trigger: Union[timedelta, datetime, None] before duration
        assert isinstance(item, Container)
        self._check_component(component, context)

        from ics.alarm import get_type_from_action
        alarm_type = get_type_from_action(item)
        instance = alarm_type()
        alarm_type.InflatedMeta().populate_instance(instance, item, context)
        self.set_or_append_value(component, instance)
        return True
