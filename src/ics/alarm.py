from abc import ABCMeta, abstractmethod
from datetime import datetime, timedelta
from typing import List, Type, Union

import attr
from attr.converters import optional as c_optional
from attr.validators import instance_of
from attr.validators import optional as v_optional

from ics.attendee import Attendee
from ics.component import Component
from ics.types import URL
from ics.utils import check_is_instance, ensure_timedelta

__all__ = [
    "BaseAlarm",
    "AudioAlarm",
    "CustomAlarm",
    "DisplayAlarm",
    "EmailAlarm",
    "NoneAlarm",
    "get_type_from_action",
]


@attr.s
class BaseAlarm(Component, metaclass=ABCMeta):
    """
    A calendar event VALARM base class
    """

    NAME = "VALARM"

    trigger: Union[timedelta, datetime, None] = attr.ib(
        default=None, validator=v_optional(instance_of((timedelta, datetime)))
    )
    repeat: int = attr.ib(default=None)
    duration: timedelta = attr.ib(default=None, converter=c_optional(ensure_timedelta))  # type: ignore[misc]

    @property
    @abstractmethod
    def action(self):
        """VALARM action to be implemented by concrete classes"""
        ...


@attr.s
class AudioAlarm(BaseAlarm):
    """
    A calendar event VALARM with AUDIO option.
    """

    attach: Union[URL, bytes, None] = attr.ib(default=None)

    @property
    def action(self):
        return "AUDIO"


@attr.s
class CustomAlarm(BaseAlarm):
    """
    A calendar event VALARM with custom ACTION.
    """

    _action: str = attr.ib(default=None)

    @property
    def action(self):
        return self._action


@attr.s
class DisplayAlarm(BaseAlarm):
    """
    A calendar event VALARM with DISPLAY option.
    """

    description: str = attr.ib(default=None)

    @property
    def action(self):
        return "DISPLAY"


@attr.s
class EmailAlarm(BaseAlarm):
    """
    A calendar event VALARM with Email option.
    """

    summary: str = attr.ib(default=None)  # message subject
    description: str = attr.ib(default=None)  # message body
    attendees: List[Attendee] = attr.ib(
        factory=list, metadata={"ics_name": "ATTENDEE"}
    )  # message recipients
    attach: List[Union[URL, bytes, None]] = attr.ib(factory=list)  # e-mail attachments

    def add_attendee(self, attendee: Attendee):
        """Add an attendee to the attendee list"""
        check_is_instance("attendee", attendee, Attendee)
        self.attendees.append(attendee)

    @property
    def action(self):
        return "EMAIL"


class NoneAlarm(BaseAlarm):
    """
    A calendar event VALARM with NONE option.
    """

    @property
    def action(self):
        return "NONE"


def get_type_from_action(action_type) -> Type[BaseAlarm]:
    if action_type == "DISPLAY":
        return DisplayAlarm
    elif action_type == "AUDIO":
        return AudioAlarm
    elif action_type == "NONE":
        return NoneAlarm
    elif action_type == "EMAIL":
        return EmailAlarm
    else:
        return CustomAlarm
