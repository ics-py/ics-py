#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals, absolute_import

from six.moves import map

import arrow
import copy
from datetime import date, timedelta

from .component import Component
from .utils import get_arrow, uid_gen
from .parse import Container
from .property import (TextProperty, DateTimeProperty, DateTimeOrDateProperty,
                       DurationProperty)


class Event(Component):
    """A calendar event.

    Can be full-day or between two instants.
    Can be defined by a beginning instant and\
    a duration *or* end instant.
    """
    name = TextProperty('SUMMARY')
    begin = DateTimeOrDateProperty('DTSTART', validation='_validate_begin')
    end = DateTimeOrDateProperty('DTEND',
                                 validation='_validate_end',
                                 default='_default_end')
    duration = DurationProperty('DURATION',
                                validation='_validate_duration',
                                default='_default_duration')
    summary = TextProperty('SUMMARY')
    description = TextProperty('DESCRIPTION')
    location = TextProperty('LOCATION')
    url = TextProperty('URL')
    created = DateTimeProperty('DTSTAMP', default=arrow.now)
    uid = TextProperty('UID', default=uid_gen)

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
                 url=None):
        """Instantiates a new :class:`ics.event.Event`.

        Args:
            name (string)
            begin (Arrow-compatible)
            end (Arrow-compatible)
            duration (datetime.timedelta)
            uid (string): must be unique
            description (string)
            created (Arrow-compatible)
            location (string)
            url (string)

        Raises:
            ValueError: if `end` and `duration` are specified at the same time

        Comment:
            Handling of all day events has changed a bit from the previous
        """
        super(Event, self).__init__()
        if name is not None:
            self.name = name
        if begin is not None:
            self.begin = begin
        if duration and end:
            raise ValueError(
                'Event() may not specify an end and a duration at the same time')
        if end is not None:
            self.end = end
        if duration is not None:
            self.duration = duration
        if uid is not None:
            self.uid = uid
        if description is not None:
            self.description = description
        if created is not None:
            self.created = created
        if location is not None:
            self.location = location
        if url is not None:
            self.url = url

    def has_end(self):
        """
        Return:
            bool: self has an end
        """
        return bool(self._has_end_time() or self._has_duration())

    def _validate_begin(self, value):
        value = get_arrow(value)
        if value and self._has_end_time and value > self.end:
            raise ValueError('Begin must be before end')

    def _default_end(self, property_name):
        if self._has_duration():  # if end is duration defined
            # return the beginning + duration
            return self.begin + self.duration
        elif self.begin:
            if isinstance(self.begin, date):
                # According to RFC 5545 "DTEND" is set to a calendar date
                # after "DTSTART" if the VEVENT spans more than one date.
                # If DTEND is not specified, the VEVENT should be only
                # one day
                return self.begin
            else:
                # This is how it was implemented previously.
                # Is this good?
                return self.begin + timedelta(seconds=1)
        else:
            return None

    def _validate_end(self, value):
        """Validate the end of the event.

        |  May be set to anything that :func:`Arrow.get` understands.
        |  If set to a non null value, removes any already
            existing duration.
        |  Setting to None will have unexpected behavior if
            begin is not None.
        |  Must not be set to a lower value than self.begin.
        """
        if value:
            if value < self.begin:
                raise ValueError('End must be after begin')
            if self._has_duration():
                del self.duration

    def _default_duration(self, property_name):
        if self._has_end():
            return self.end - self.begin
        else:
            return None

    def _validate_duration(self, value):
        if value and self._has_end_time():
            del self.end

    def _has_end_time(self):
        return 'END' in self._properties

    def _has_duration(self):
        return 'DURATION' in self._properties

    @property
    def all_day(self):
        """
        Return:
            bool: self is an all-day event
        """
        return isinstance(self.begin, date)

    def make_all_day(self):
        """Transforms self to an all-day event.

        The day will be the day of self.begin.
        """
        self.begin = self.begin.date()
        self.duration = None
        self.end = None

    def __urepr__(self):
        """Should not be used directly. Use self.__repr__ instead.

        Returns:
            unicode: a unicode representation (__repr__) of the event.
        """
        name = "'{}' ".format(self.name) if self.name else ''
        if self.all_day:
            return "<all-day Event {}{}>".format(name, self.begin.strftime("%F"))
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
        # We have to compare the properties themselves,
        # because when uid should not be set,
        # a simple 'self.uid == other.uid' would invoke uid_gen
        return self._properties.get('UID') == other._properties.get('UID')

    def clone(self):
        """
        Returns:
            Event: an exact copy of self"""
        self.uid  # make sure that there is a uid
        clone = copy.copy(self)
        clone._properties = copy.copy(clone._properties)
        clone._components = copy.copy(clone._components)
        return clone

    def __hash__(self):
        """
        Returns:
            int: hash of self. Based on self.uid."""
        return int(''.join(map(lambda x: '%.3d' % ord(x), self.uid)))
