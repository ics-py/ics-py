#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals, absolute_import

from six import PY2, StringIO, string_types
from six.moves import range

from dateutil.tz import tzical
import copy
import collections

from .component import Component
from .event import Event
from .eventlist import EventList
from .parse import (
    lines_to_container,
    string_to_container,
    Container,
)
from .property import TextProperty, VersionProperty


class Calendar(Component):

    """Represents an unique rfc5545 iCalendar."""

    _TYPE = 'VCALENDAR'
    _EXTRACTORS = []
    _OUTPUTS = []
    _known_components = (
        ('VEVENT', Event, '_events'),
        # VTIMEZONE is dealt with independently
    )

    creator = TextProperty('PRODID', default='ics.py - http://git.io/lLljaA')
    version = VersionProperty('VERSION', default='2.0')
    # TODO : should take care of minver/maxver
    scale = TextProperty('CALSCALE', default='GREGORIAN')
    method = TextProperty('METHOD')

    def __init__(self, imports=None, events=None, creator=None):
        """Instantiates a new Calendar.

        Args:
            imports (string or list of lines/strings): data to be imported into the Calendar(),
            events (list of Events or EventList): will be casted to :class:`ics.eventlist.EventList`
            creator (string): uid of the creator program.

        If `imports` is specified, __init__ ignores every other argument.
        """
        # TODO : implement a file-descriptor import and a filename import
        super(Calendar, self).__init__()
        self._timezones = {}
        self._events = EventList()
        self.scale = None
        self.method = None

        if imports is not None:
            if isinstance(imports, string_types):
                container = string_to_container(imports)
            elif isinstance(imports, collections.Iterable):
                container = lines_to_container(imports)
            else:
                raise TypeError("Expecting a sequence or a string")

            # TODO : make a better API for multiple calendars
            if len(container) != 1:
                raise NotImplementedError(
                    'Multiple calendars in one file are not supported')

            self._populate(container[0])  # Use first calendar
        else:
            self._events = events or EventList()
            if creator is not None:
                self.creator = creator

    def __urepr__(self):
        """Returns:
            unicode: representation (__repr__) of the calendar.

        Should not be used directly. Use self.__repr__ instead.
        """
        return "<Calendar with {} event{}>" \
            .format(len(self.events), "s" if len(self.events) > 1 else "")

    def __iter__(self):
        """Returns:
        iterable: an iterable version of __str__, line per line
        (with line-endings).

        Example:
            Can be used to write calendar to a file:

            >>> c = Calendar(); c.append(Event(name="My cool event"))
            >>> open('my.ics', 'w').writelines(c)
        """
        for line in str(self).split('\n'):
            l = line + '\n'
            if PY2:
                l = l.encode('utf-8')
            yield l

    def __eq__(self, other):
        if len(self.events) != len(other.events):
            return False
        for i in range(len(self.events)):
            if not self.events[i] == other.events[i]:
                return False
        for attr in ('scale', 'method', 'creator'):
            if self.__getattribute__(attr) != other.__getattribute__(attr):
                return False

        return True

    def __ne__(self, other):
        return not self.__eq__(other)

    @property
    def events(self):
        """Get or set the list of calendar's events.

        |  Will return an EventList object (similar to python list).
        |  May be set to a list or an EventList
            (otherwise will raise a ValueError).
        |  If setted, will override all pre-existing events.
        """
        return self._events

    @events.setter
    def events(self, value):
        if isinstance(value, EventList):
            self._events = value
        elif isinstance(value, collections.Iterable):
            self._events = EventList(value)
        else:
            raise ValueError(
                'Calendar.events must be an EventList or an iterable')

    def clone(self):
        """
        Returns:
            Calendar: an exact deep copy of self
        """
        clone = copy.copy(self)
        clone._properties = copy.copy(clone._properties)
        clone._components = copy.copy(clone._components)
        clone.events = EventList(self.events)
        clone._timezones = copy.copy(self._timezones)
        return clone

    def __add__(self, other):
        events = self.events + other.events
        return Calendar(events)

    def get_timezones(self):
        return self._timezones
# TODO: add_timezone or set_timezones

    def _build_components(self):
        super(Calendar, self)._build_components()
        # parse timezones
        for vtimezone in self._components['VTIMEZONE']:
            timezones = tzical(StringIO(str(vtimezone)))  # tzical does not like strings
            for key in timezones.keys():
                self._timezones[key] = timezones.get(key)
