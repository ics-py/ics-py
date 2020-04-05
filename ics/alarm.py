from abc import ABCMeta, abstractmethod
from datetime import datetime, timedelta
from typing import List, Optional, Union

import attr
from attr.converters import optional as c_optional
from attr.validators import instance_of, optional as v_optional

from ics.attendee import Attendee
from ics.component import Component
from ics.converter.component import ComponentMeta
from ics.converter.special import AlarmConverter
from ics.grammar import ContentLine
from ics.utils import call_validate_on_inst, check_is_instance, ensure_timedelta

__all__ = ["BaseAlarm", "AudioAlarm", "CustomAlarm", "DisplayAlarm", "EmailAlarm", "NoneAlarm"]


@attr.s
class BaseAlarm(Component, metaclass=ABCMeta):
    """
    A calendar event VALARM base class
    """
    Meta = ComponentMeta("VALARM", converter_class=AlarmConverter)

    trigger: Union[timedelta, datetime, None] = attr.ib(
        default=None,
        validator=v_optional(instance_of((timedelta, datetime)))  # type: ignore
    )  # TODO is this relative to begin or end?
    repeat: int = attr.ib(default=None, validator=call_validate_on_inst)
    duration: timedelta = attr.ib(default=None, converter=c_optional(ensure_timedelta), validator=call_validate_on_inst)  # type: ignore

    def validate(self, attr=None, value=None):
        if self.repeat is not None:
            if self.repeat < 0:
                raise ValueError("Repeat must be great than or equal to 0.")
            if self.duration is None:
                raise ValueError(
                    "A definition of an alarm with a repeating trigger MUST include both the DURATION and REPEAT properties."
                )

        if self.duration is not None and self.duration.total_seconds() < 0:
            raise ValueError("Alarm duration timespan must be positive.")

    @property
    @abstractmethod
    def action(self):
        """ VALARM action to be implemented by concrete classes """
        pass


@attr.s
class AudioAlarm(BaseAlarm):
    """
    A calendar event VALARM with AUDIO option.
    """

    sound: Optional[ContentLine] = attr.ib(default=None, validator=v_optional(instance_of(ContentLine)))

    @property
    def action(self):
        return "AUDIO"


@attr.s
class CustomAlarm(BaseAlarm):
    """
    A calendar event VALARM with custom ACTION.
    """

    _action = attr.ib(default=None)

    @property
    def action(self):
        return self._action


@attr.s
class DisplayAlarm(BaseAlarm):
    """
    A calendar event VALARM with DISPLAY option.
    """

    display_text: str = attr.ib(default=None)

    @property
    def action(self):
        return "DISPLAY"


@attr.s
class EmailAlarm(BaseAlarm):
    """
    A calendar event VALARM with Email option.
    """

    subject: str = attr.ib(default=None)
    body: str = attr.ib(default=None)
    recipients: List[Attendee] = attr.ib(factory=list)

    def add_recipient(self, recipient: Attendee):
        """ Add an recipient to the recipients list """
        check_is_instance("recipient", recipient, Attendee)
        self.recipients.append(recipient)

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


def get_type_from_action(action_type):
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
