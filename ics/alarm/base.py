from abc import ABCMeta, abstractmethod
from datetime import datetime, timedelta
from typing import Any, Union

import attr

from ics.component import Component
from ics.grammar.parse import Container
from ics.parsers.alarm_parser import BaseAlarmParser
from ics.serializers.alarm_serializer import BaseAlarmSerializer
from ics.utils import get_lines


def call_validate_on_inst(inst, attr, value):
    inst.validate(attr, value)


@attr.s
class BaseAlarm(Component, metaclass=ABCMeta):
    """
    A calendar event VALARM base class
    """

    class Meta:
        name = "VALARM"
        parser = BaseAlarmParser
        serializer = BaseAlarmSerializer

    trigger: Union[timedelta, datetime] = attr.ib(
        default=None, validator=attr.validators.instance_of((timedelta, datetime)))
    repeat: int = attr.ib(default=None, validator=call_validate_on_inst)
    duration: timedelta = attr.ib(default=None, validator=call_validate_on_inst)

    def validate(self):
        if self.repeat is not None:
            if self.repeat < 0:
                raise ValueError("Repeat must be great than or equal to 0.")
            if self.duration is None:
                raise ValueError(
                    "A definition of an alarm with a repeating trigger MUST include both the DURATION and REPEAT properties."
                )

        if self.duration is not None and self.duration.total_seconds() < 0:
            raise ValueError("Alarm duration timespan must be positive.")

    @classmethod
    def _from_container(cls, container: Container, *args: Any, **kwargs: Any):
        ret = super()._from_container(container, *args, **kwargs)
        get_lines(ret.extra, "ACTION", keep=False)  # Just drop the ACTION line
        return ret

    @property
    @abstractmethod
    def action(self):
        """ VALARM action to be implemented by concrete classes
        """
        raise NotImplementedError("Base class cannot be instantiated directly")

    def __repr__(self):
        value = "{0} trigger:{1}".format(type(self).__name__, self.trigger)
        if self.repeat:
            value += " repeat:{0} duration:{1}".format(self.repeat, self.duration)

        return "<{0}>".format(value)
