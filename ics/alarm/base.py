#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals, absolute_import

import copy
from datetime import datetime, timedelta
from typing import Callable, List, Optional, Union
from abc import ABCMeta, abstractmethod
import warnings

from ics.component import Component, Extractor
from ics.utils import (
    arrow_to_iso,
    get_arrow,
    iso_to_arrow,
    parse_duration,
    timedelta_to_duration,
)
from ics.parse import ContentLine, Container


class BaseAlarm(Component, metaclass=ABCMeta):
    """
    A calendar event VALARM base class
    """

    _TYPE = "VALARM"
    _EXTRACTORS: List[Extractor] = []
    _OUTPUTS: List[Callable] = []

    def __init__(
        self,
        trigger: Union[timedelta, datetime] = None,
        repeat: int = None,
        duration: timedelta = None,
    ) -> None:
        """
        Instantiates a new :class:`ics.alarm.BaseAlarm`.

        Adheres to RFC5545 VALARM standard: http://icalendar.org/iCalendar-RFC-5545/3-6-6-alarm-component.html

        Args:
            trigger (datetime.timedelta OR datetime.datetime) : Timespan to alert before parent action, or absolute time to alert
            repeat (integer) : How many times to repeat the alarm
            duration (datetime.timedelta) : Duration between repeats

        Raises:
            ValueError: If trigger, repeat, or duration do not match the RFC spec.
        """
        # Set initial values
        self._trigger: Optional[Union[timedelta, datetime]] = None
        self._repeat: Optional[int] = None
        self._duration: Optional[timedelta] = None

        # Validate and parse
        self.trigger = trigger

        # XOR repeat and duration
        if (repeat is not None) and (duration is None):
            raise ValueError(
                "A definition of an alarm with a repeating trigger MUST include both the DURATION and REPEAT properties."
            )

        if repeat:
            self.repeat = repeat

        if duration:
            self.duration = duration

        self.extra = Container(name="VALARM")

    @property
    def trigger(self) -> Optional[Union[timedelta, datetime]]:
        """The trigger condition for the alarm

        | Returns either a timedelta or datetime object
        """
        return self._trigger

    @trigger.setter
    def trigger(self, value: Optional[Union[timedelta, datetime]]) -> None:
        if isinstance(value, datetime):
            value = get_arrow(value)

        self._trigger = value

    @property
    def repeat(self) -> Optional[int]:
        """Number of times to repeat alarm

        | Returns an integer for number of alarm repeats
        | Value must be >= 0
        """
        return self._repeat

    @repeat.setter
    def repeat(self, value: Optional[int]) -> None:
        if value is not None and value < 0:
            raise ValueError("Repeat must be great than or equal to 0.")

        self._repeat = value

    @property
    def duration(self) -> Optional[timedelta]:
        """Duration between alarm repeats

        | Returns a timedelta object
        | Timespan must return positive total_seconds() value
        """
        return self._duration

    @duration.setter
    def duration(self, value: Optional[timedelta]) -> None:
        if value is not None and value.total_seconds() < 0:
            raise ValueError("Alarm duration timespan must be positive.")

        self._duration = value

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

    def __ne__(self, other) -> bool:
        return not self.__eq__(other)

    def __eq__(self, other) -> bool:
        """Two alarms are considered equal if they have the same type and base values."""

        return (
            type(self) is type(other)
            and self.trigger == other.trigger
            and self.repeat == other.repeat
            and self.duration == other.duration
        )

    def clone(self):
        """
        Returns:
            Alarm: an exact copy of self"""
        clone = copy.copy(self)
        clone.extra = clone.extra.clone()
        return clone


# ------------------
# ----- Inputs -----
# ------------------
@BaseAlarm._extracts("TRIGGER", required=True)
def trigger(alarm, line):
    if line.params.get("VALUE", [""])[0] == "DATE-TIME":
        alarm.trigger = iso_to_arrow(line)
    elif line.params.get("VALUE", ["DURATION"])[0] == "DURATION":
        alarm.trigger = parse_duration(line.value)
    else:
        warnings.warn("ics.py encountered a TRIGGER of unknown type '%s'. It has been ignored." % line.params["VALUE"][0])


@BaseAlarm._extracts("DURATION")
def duration(alarm, line):
    if line:
        alarm._duration = parse_duration(line.value)


@BaseAlarm._extracts("REPEAT")
def repeat(alarm, line):
    if line:
        alarm._repeat = int(line.value)


# -------------------
# ----- Outputs -----
# -------------------
@BaseAlarm._outputs
def o_trigger(alarm, container):
    if not alarm.trigger:
        raise ValueError("Alarm must have a trigger")

    if type(alarm.trigger) is timedelta:
        representation = timedelta_to_duration(alarm.trigger)
        container.append(ContentLine("TRIGGER", value=representation))
    else:
        container.append(
            ContentLine(
                "TRIGGER",
                params={"VALUE": ["DATE-TIME"]},
                value=arrow_to_iso(alarm.trigger),
            )
        )


@BaseAlarm._outputs
def o_duration(alarm, container):
    if alarm.duration:
        representation = timedelta_to_duration(alarm.duration)
        container.append(ContentLine("DURATION", value=representation))


@BaseAlarm._outputs
def o_repeat(alarm, container):
    if alarm.repeat:
        container.append(ContentLine("REPEAT", value=alarm.repeat))


@BaseAlarm._outputs
def o_action(alarm, container):
    container.append(ContentLine("ACTION", value=alarm.action))
