#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals, absolute_import

from six import PY2, PY3, StringIO, string_types, text_type, integer_types
from six.moves import filter, map, range

import arrow
import copy
from datetime import timedelta

from .component import Component
from .utils import (
    parse_duration,
    timedelta_to_duration,
    iso_to_arrow,
    iso_precision,
    get_arrow,
    arrow_to_iso,
    arrow_date_to_iso,
    uid_gen,
    unescape_string,
    escape_string,
)
from .parse import ContentLine, Container


class Event(Component):

    """A calendar event.

    Can be full-day or between two instants.
    Can be defined by a beginning instant and\
    a duration *or* end instant.
    """

    _TYPE = "VEVENT"
    _EXTRACTORS = []
    _OUTPUTS = []

    def __init__(self,
                 name=None,
                 begin=None,
                 end=None,
                 duration=None,
                 uid=None,
                 description=None,
                 created=None,
                 location=None,
                 url=None,
                 transparent=False):
        """Instantiates a new :class:`ics.event.Event`.

        Args:
            name (string) : rfc5545 SUMMARY property
            begin (Arrow-compatible)
            end (Arrow-compatible)
            duration (datetime.timedelta)
            uid (string): must be unique
            description (string)
            created (Arrow-compatible)
            location (string)
            url (string)
            transparent (Boolean)

        Raises:
            ValueError: if `end` and `duration` are specified at the same time
        """

        self._duration = None
        self._end_time = None
        self._begin = None
        self._begin_precision = None
        self.uid = uid_gen() if not uid else uid
        self.description = description
        self.created = get_arrow(created)
        self.location = location
        self.url = url
        self.transparent = transparent
        self._unused = Container(name='VEVENT')

        self.name = name
        self.begin = begin
        # TODO: DRY [1]
        if duration and end:
            raise ValueError(
                'Event() may not specify an end and a duration \
                at the same time')
        elif end:  # End was specified
            self.end = end
        elif duration:  # Duration was specified
            self.duration = duration

    def has_end(self):
        """
        Return:
            bool: self has an end
        """
        return bool(self._end_time or self._duration)

    @property
    def begin(self):
        """Get or set the beginning of the event.

        |  Will return an :class:`Arrow` object.
        |  May be set to anything that :func:`Arrow.get` understands.
        |  If an end is defined (not a duration), .begin must not
            be set to a superior value.
        """
        return self._begin

    @begin.setter
    def begin(self, value):
        value = get_arrow(value)
        if value and self._end_time and value > self._end_time:
            raise ValueError('Begin must be before end')
        self._begin = value
        self._begin_precision = 'second'

    @property
    def end(self):
        """Get or set the end of the event.

        |  Will return an :class:`Arrow` object.
        |  May be set to anything that :func:`Arrow.get` understands.
        |  If set to a non null value, removes any already
            existing duration.
        |  Setting to None will have unexpected behavior if
            begin is not None.
        |  Must not be set to an inferior value than self.begin.
        """

        if self._duration:  # if end is duration defined
            # return the beginning + duration
            return self.begin + self._duration
        elif self._end_time:  # if end is time defined
            if self.all_day:
                return self._end_time + timedelta(days=1)
            else:
                return self._end_time
        elif self._begin:  # if end is not defined
            if self.all_day:
                return self._begin + timedelta(days=1)
            else:
                # instant event
                return self._begin
        else:
            return None

    @end.setter
    def end(self, value):
        value = get_arrow(value)
        if value and value < self._begin:
            raise ValueError('End must be after begin')

        self._end_time = value
        if value:
            self._duration = None

    @property
    def duration(self):
        """Get or set the duration of the event.

        |  Will return a timedelta object.
        |  May be set to anything that timedelta() understands.
        |  May be set with a dict ({"days":2, "hours":6}).
        |  If set to a non null value, removes any already
            existing end time.
        """
        if self._duration:
            return self._duration
        elif self.end:
            # because of the clever getter for end, this also takes care of all_day events
            return self.end - self.begin
        else:
            # event has neither start, nor end, nor duration
            return None

    @duration.setter
    def duration(self, value):
        if isinstance(value, dict):
            value = timedelta(**value)
        elif isinstance(value, timedelta):
            value = value
        elif value is not None:
            value = timedelta(value)

        if value:
            self._end_time = None

        self._duration = value

    @property
    def all_day(self):
        """
        Return:
            bool: self is an all-day event
        """
        # the event may have an end, also given in 'day' precision
        return self._begin_precision == 'day'

    def make_all_day(self):
        """Transforms self to an all-day event.

        The event will span all the days from the begin to the end day.
        """
        was_instant = self.duration == timedelta(0)
        old_end = self.end
        self._duration = None
        self._begin_precision = 'day'
        self._begin = self._begin.floor('day')
        if was_instant:
            self._end_time = None
            return
        floored_end = old_end.floor('day')
        # this "overflooring" must be done because end times are not included in the interval
        calculated_end = floored_end - timedelta(days=1) if floored_end == old_end else floored_end
        if calculated_end == self._begin:
            # for a one day event, we don't need to save the _end_time
            self._end_time = None
        else:
            self._end_time = calculated_end

    def __urepr__(self):
        """Should not be used directly. Use self.__repr__ instead.

        Returns:
            unicode: a unicode representation (__repr__) of the event.
        """
        name = "'{}' ".format(self.name) if self.name else ''
        if self.all_day:
            if not self._end_time or self._begin == self._end_time:
                return "<all-day Event {}{}>".format(name, self.begin.strftime("%F"))
            else:
                return "<all-day Event {}begin:{} end:{}>".format(name, self._begin.strftime("%F"), self._end_time.strftime("%F"))
        elif self.begin is None:
            return "<Event '{}'>".format(self.name) if self.name else "<Event>"
        else:
            return "<Event {}begin:{} end:{}>".format(name, self.begin, self.end)

    def __lt__(self, other):
        if not isinstance(other, Event):
            raise NotImplementedError(
                'Cannot compare Event and {}'.format(type(other)))
        if self.begin is None and other.begin is None:
            if self.name is None and other.name is None:
                return False
            elif self.name is None:
                return True
            elif other.name is None:
                return False
            else:
                return self.name < other.name
        return self.begin < other.begin

    def __le__(self, other):
        if not isinstance(other, Event):
            raise NotImplementedError(
                'Cannot compare Event and {}'.format(type(other)))
        if self.begin is None and other.begin is None:
            if self.name is None and other.name is None:
                return True
            elif self.name is None:
                return True
            elif other.name is None:
                return False
            else:
                return self.name <= other.name
        return self.begin <= other.begin

    def __gt__(self, other):
        if not isinstance(other, Event):
            raise NotImplementedError(
                'Cannot compare Event and {}'.format(type(other)))
        if self.begin is None and other.begin is None:
            return self.name > other.name
        return self.begin > other.begin

    def __ge__(self, other):
        if not isinstance(other, Event):
            raise NotImplementedError(
                'Cannot compare Event and {}'.format(type(other)))
        if self.begin is None and other.begin is None:
            return self.name >= other.name
        return self.begin >= other.begin

    def __or__(self, other):
        begin, end = None, None
        if self.begin and other.begin:
            begin = max(self.begin, other.begin)
        if self.end and other.end:
            end = min(self.end, other.end)
        return (begin, end) if begin and end and begin < end else (None, None)

    def __eq__(self, other):
        """Two events are considered equal if they have the same uid."""
        return self.uid == other.uid

    def clone(self):
        """
        Returns:
            Event: an exact copy of self"""
        clone = copy.copy(self)
        clone._unused = clone._unused.clone()
        return clone

    def __hash__(self):
        """
        Returns:
            int: hash of self. Based on self.uid."""
        return int(''.join(map(lambda x: '%.3d' % ord(x), self.uid)))


# ------------------
# ----- Inputs -----
# ------------------
@Event._extracts('DTSTAMP')
def created(event, line):
    if line:
        # get the dict of vtimezones passed to the classmethod
        tz_dict = event._classmethod_kwargs['tz']
        event.created = iso_to_arrow(line, tz_dict)


@Event._extracts('DTSTART')
def start(event, line):
    if line:
        # get the dict of vtimezones passed to the classmethod
        tz_dict = event._classmethod_kwargs['tz']
        event.begin = iso_to_arrow(line, tz_dict)
        event._begin_precision = iso_precision(line.value)


@Event._extracts('DURATION')
def duration(event, line):
    if line:
        #TODO: DRY [1]
        if event._end_time: # pragma: no cover
            raise ValueError("An event can't have both DTEND and DURATION")
        event._duration = parse_duration(line.value)


@Event._extracts('DTEND')
def end(event, line):
    if line:
        #TODO: DRY [1]
        if event._duration:
            raise ValueError("An event can't have both DTEND and DURATION")
        # get the dict of vtimezones passed to the classmethod
        tz_dict = event._classmethod_kwargs['tz']
        event._end_time = iso_to_arrow(line, tz_dict)
        # one could also save the end_precision to check that if begin_precision is day, end_precision also is


@Event._extracts('SUMMARY')
def summary(event, line):
    event.name = unescape_string(line.value) if line else None


@Event._extracts('DESCRIPTION')
def description(event, line):
    event.description = unescape_string(line.value) if line else None


@Event._extracts('LOCATION')
def location(event, line):
    event.location = unescape_string(line.value) if line else None


@Event._extracts('URL')
def url(event, line):
    event.url = unescape_string(line.value) if line else None


@Event._extracts('TRANSP')
def transparent(event, line):
    if line:
        event.transparent = line.value == 'TRANSPARENT'


# TODO : make uid required ?
# TODO : add option somewhere to ignore some errors
@Event._extracts('UID')
def uid(event, line):
    if line:
        event.uid = line.value


# -------------------
# ----- Outputs -----
# -------------------
@Event._outputs
def o_created(event, container):
    if event.created:
        instant = event.created
    else:
        instant = arrow.now()

    container.append(ContentLine('DTSTAMP', value=arrow_to_iso(instant)))


@Event._outputs
def o_start(event, container):
    if event.begin and not event.all_day:
        container.append(ContentLine('DTSTART', value=arrow_to_iso(event.begin)))


@Event._outputs
def o_all_day(event, container):
    if event.begin and event.all_day:
        container.append(ContentLine('DTSTART', params={'VALUE': ('DATE',)},
                                     value=arrow_date_to_iso(event.begin)))


@Event._outputs
def o_duration(event, container):
    # TODO : DURATION
    if event._duration and event.begin:
        representation = timedelta_to_duration(event._duration)
        container.append(ContentLine('DURATION', value=representation))


@Event._outputs
def o_end(event, container):
    if event.begin and event._end_time:
        container.append(ContentLine('DTEND', value=arrow_to_iso(event.end)))


@Event._outputs
def o_summary(event, container):
    if event.name:
        container.append(ContentLine('SUMMARY', value=escape_string(event.name)))


@Event._outputs
def o_description(event, container):
    if event.description:
        container.append(ContentLine('DESCRIPTION', value=escape_string(event.description)))


@Event._outputs
def o_location(event, container):
    if event.location:
        container.append(ContentLine('LOCATION', value=escape_string(event.location)))


@Event._outputs
def o_url(event, container):
    if event.url:
        container.append(ContentLine('URL', value=escape_string(event.url)))


@Event._outputs
def o_transparent(event, container):
    if event.transparent:
        container.append(ContentLine('TRANSP', value=escape_string('TRANSPARENT')))
    else:
        container.append(ContentLine('TRANSP', value=escape_string('OPAQUE')))


@Event._outputs
def o_uid(event, container):
    if event.uid:
        uid = event.uid
    else:
        uid = uid_gen()

    container.append(ContentLine('UID', value=uid))
