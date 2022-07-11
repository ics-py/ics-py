from typing import Any, Dict, Generic, Iterable, List, TypeVar

import attr

from ics.utils import check_is_instance
from ics.valuetype.base import ValueConverter
from ics.valuetype.generic import BooleanConverter, URIConverter
from ics.valuetype.text import RawTextConverter

T = TypeVar("T")


@attr.s(frozen=True)
class PersonProperty(Generic[T]):
    name: str = attr.ib()
    converter: ValueConverter[T] = attr.ib(default=RawTextConverter)
    default: Any = attr.ib(default=None)

    def __get__(self, instance: "Person", owner) -> T:
        if self.name not in instance.extra:
            return self.default
        value = instance.extra[self.name]
        if len(value) == 0:
            return self.default
        elif len(value) == 1:
            return self.converter.parse(value[0])
        else:
            raise ValueError(
                "Expected at most one value for property {!r}, got {!r}!".format(
                    self.name, value
                )
            )

    def __set__(self, instance: "Person", value: T):
        instance.extra[self.name] = [self.converter.serialize(value)]

    def __delete__(self, instance: "Person"):
        instance.extra.pop(self.name, None)


@attr.s(frozen=True)
class PersonMultiProperty(Generic[T]):
    name: str = attr.ib()
    converter: ValueConverter[T] = attr.ib(default=RawTextConverter)
    default: Any = attr.ib(default=None)

    def __get__(self, instance: "Person", owner) -> List[T]:
        if self.name not in instance.extra:
            return self.default
        return [self.converter.parse(v) for v in instance.extra[self.name]]

    def __set__(self, instance: "Person", value: Iterable[T]):
        instance.extra[self.name] = [self.converter.serialize(v) for v in value]

    def __delete__(self, instance: "Person"):
        instance.extra.pop(self.name, None)


@attr.s
class PersonAttrs:
    email: str = attr.ib()
    extra: Dict[str, List[str]] = attr.ib(factory=dict)


class Person(PersonAttrs):
    NAME = "ABSTRACT-PERSON"

    def __init__(self, email, extra=None, **kwargs):
        if extra is None:
            extra = dict()
        else:
            check_is_instance("extra", extra, dict)
        super().__init__(email, extra)
        for key, val in kwargs.items():
            setattr(self, key, val)

    sent_by = PersonProperty("SENT-BY", URIConverter)
    common_name = PersonProperty[str]("CN")
    directory = PersonProperty("DIR", URIConverter)


class Organizer(Person):
    NAME = "ORGANIZER"


class Attendee(Person):
    NAME = "ATTENDEE"

    user_type = PersonProperty[str]("CUTYPE", default="INDIVIDUAL")
    """Calendar User Type: INDIVIDUAL, GROUP, RESOURCE, ROOM, UNKNOWN, ..."""
    member = PersonMultiProperty("MEMBER", converter=URIConverter)
    """group or list membership"""
    role = PersonProperty[str]("ROLE", default="REQ-PARTICIPANT")
    """Role: CHAIR, REQ-PARTICIPANT, OPT-PARTICIPANT, NON-PARTICIPANT"""
    status = PersonProperty[str]("PARTSTAT", default="NEEDS-ACTION")
    """Participation Status, possible values differ:
      Event, ToDo, Journal: NEEDS-ACTION, ACCEPTED, DECLINED
      Event, ToDo:          TENTATIVE, DELEGATED
             ToDo:          COMPLETED, IN-PROCESS"""
    rsvp = PersonProperty("RSVP", converter=BooleanConverter, default=False)
    """expectation of a favor of a reply?"""
    delegated_to = PersonMultiProperty("DELEGATED-TO", converter=URIConverter)
    delegated_from = PersonMultiProperty("DELEGATED-FROM", converter=URIConverter)
