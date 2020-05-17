from typing import Dict, List, Optional

import attr

from ics.converter.component import ComponentMetaInfo


@attr.s
class Person(object):
    email: str = attr.ib()
    common_name: str = attr.ib(default=None)
    dir: Optional[str] = attr.ib(default=None)
    sent_by: Optional[str] = attr.ib(default=None)
    extra: Dict[str, List[str]] = attr.ib(factory=dict)

    MetaInfo = ComponentMetaInfo("ABSTRACT-PERSON")


class Organizer(Person):
    MetaInfo = ComponentMetaInfo("ORGANIZER")


@attr.s
class Attendee(Person):
    rsvp: Optional[bool] = attr.ib(default=None)
    role: Optional[str] = attr.ib(default=None)
    partstat: Optional[str] = attr.ib(default=None)
    cutype: Optional[str] = attr.ib(default=None)

    MetaInfo = ComponentMetaInfo("ATTENDEE")
