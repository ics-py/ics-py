from typing import Dict, List, Optional

import attr

from ics.converter.component import ComponentMeta


@attr.s
class Person(object):
    email: str = attr.ib()
    common_name: str = attr.ib(default=None)
    dir: Optional[str] = attr.ib(default=None)
    sent_by: Optional[str] = attr.ib(default=None)
    extra: Dict[str, List[str]] = attr.ib(factory=dict)

    Meta = ComponentMeta("ABSTRACT-PERSON")


class Organizer(Person):
    Meta = ComponentMeta("ORGANIZER")


@attr.s
class Attendee(Person):
    rsvp: Optional[bool] = attr.ib(default=None)
    role: Optional[str] = attr.ib(default=None)
    partstat: Optional[str] = attr.ib(default=None)
    cutype: Optional[str] = attr.ib(default=None)

    Meta = ComponentMeta("ATTENDEE")
