import attr
from typing import Dict, List, Optional, Any

from ics.types import URL
from ics.utils import check_is_instance
from ics.valuetype.base import ValueConverter
from ics.valuetype.generic import URIConverter, BooleanConverter
from ics.valuetype.text import RawTextConverter


@attr.s(frozen=True)
class PersonProperty(object):
    name: str = attr.ib()
    converter: ValueConverter = attr.ib(default=RawTextConverter)
    multi_value: bool = attr.ib(default=False)
    default: Any = attr.ib(default=None)

    def __get__(self, instance: "Person", owner):
        if self.name not in instance.extra:
            return self.default
        value = instance.extra[self.name]
        if self.multi_value:
            return [self.converter.parse(v) for v in value]
        else:
            if len(value) == 0:
                return self.default
            elif len(value) == 1:
                return self.converter.parse(value[0])
            else:
                raise ValueError("Expected at most one value for property %r, got %r!" % (self.name, value))

    def __set__(self, instance: "Person", value):
        if self.multi_value:
            instance.extra[self.name] = [self.converter.serialize(v) for v in value]
        else:
            instance.extra[self.name] = [self.converter.serialize(value)]

    def __delete__(self, instance: "Person"):
        instance.extra.pop(self.name, None)


@attr.s
class PersonAttrs(object):
    email: str = attr.ib()
    extra: Dict[str, List[str]] = attr.ib(factory=dict)


class Person(PersonAttrs):
    NAME = "ABSTRACT-PERSON"

    def __init__(self, email, extra=None, **kwargs):
        if extra is None:
            extra = dict()
        else:
            check_is_instance("extra", extra, dict)
        super(Person, self).__init__(email, extra)
        for key, val in kwargs.items():
            setattr(self, key, val)

    sent_by: Optional[URL] = PersonProperty("SENT-BY", URIConverter)
    common_name: str = PersonProperty("CN")
    directory: Optional[URL] = PersonProperty("DIR", URIConverter)


class Organizer(Person):
    NAME = "ORGANIZER"


class Attendee(Person):
    NAME = "ATTENDEE"

    user_type: str = PersonProperty("CUTYPE", default="INDIVIDUAL")
    """Calendar User Type: INDIVIDUAL, GROUP, RESOURCE, ROOM, UNKNOWN, ..."""
    member: List[URL] = PersonProperty("MEMBER", converter=URIConverter, multi_value=True)
    """group or list membership"""
    role: str = PersonProperty("ROLE", default="REQ-PARTICIPANT")
    """Role: CHAIR, REQ-PARTICIPANT, OPT-PARTICIPANT, NON-PARTICIPANT"""
    status: str = PersonProperty("PARTSTAT", default="NEEDS-ACTION")
    """Participation Status, possible values differ:
      Event, ToDo, Journal: NEEDS-ACTION, ACCEPTED, DECLINED
      Event, ToDo:          TENTATIVE, DELEGATED
             ToDo:          COMPLETED, IN-PROCESS"""
    rsvp: bool = PersonProperty("RSVP", converter=BooleanConverter, default=False)
    """expectation of a favor of a reply?"""
    delegated_to: List[URL] = PersonProperty("DELEGATED-TO", converter=URIConverter, multi_value=True)
    delegated_from: List[URL] = PersonProperty("DELEGATED-FROM", converter=URIConverter, multi_value=True)
