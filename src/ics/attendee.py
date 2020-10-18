from typing import Dict, List, Optional

import attr


@attr.s
class Person(object):
    NAME = "ABSTRACT-PERSON"

    email: str = attr.ib()
    common_name: str = attr.ib(default=None)
    dir: Optional[str] = attr.ib(default=None)
    sent_by: Optional[str] = attr.ib(default=None)
    extra: Dict[str, List[str]] = attr.ib(factory=dict)


class Organizer(Person):
    NAME = "ORGANIZER"


@attr.s
class Attendee(Person):
    NAME = "ATTENDEE"

    rsvp: Optional[bool] = attr.ib(default=None)
    role: Optional[str] = attr.ib(default=None)
    partstat: Optional[str] = attr.ib(default=None)
    cutype: Optional[str] = attr.ib(default=None)
