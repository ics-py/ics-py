from abc import ABCMeta, abstractmethod
from datetime import datetime, timedelta
from typing import Any, Type, Union

import attr
from attr.converters import optional as c_optional
from attr.validators import instance_of, optional as v_optional

from ics.component import Component, ComponentType
from ics.grammar.parse import Container
from ics.parsers.alarm_parser import BaseAlarmParser
from ics.serializers.alarm_serializer import BaseAlarmSerializer
from ics.utils import ensure_timedelta, get_lines


def call_validate_on_inst(inst, attr, value):
    inst.validate(attr, value)


@attr.s(repr=False)
class BaseAlarm(Component, metaclass=ABCMeta):
    """
    A calendar event VALARM base class
    """

    class Meta:
        name = "VALARM"
        parser = BaseAlarmParser
        serializer = BaseAlarmSerializer

    trigger: Union[timedelta, datetime, None] = attr.ib(
        default=None,
        validator=v_optional(instance_of((timedelta, datetime)))  # type: ignore
    )
    repeat: int = attr.ib(default=None, validator=call_validate_on_inst)
    duration: timedelta = attr.ib(default=None, converter=c_optional(ensure_timedelta), validator=call_validate_on_inst)

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

    @classmethod
    def _from_container(cls: Type[ComponentType], container: Container, *args: Any, **kwargs: Any) -> ComponentType:
        ret = super(BaseAlarm, cls)._from_container(container, *args, **kwargs)  # type: ignore
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
