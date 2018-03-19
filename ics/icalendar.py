#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals, absolute_import

from six import PY2, PY3, StringIO, string_types, text_type, integer_types
from six.moves import filter, map, range

from dateutil.tz import tzical
import copy
import collections

from .component import Component
from .timeline import Timeline
from .event import Event
from .todo import Todo
from .parse import (
    lines_to_container,
    string_to_container,
    ContentLine,
    Container,
)
from .utils import remove_x


class Calendar(Component):

    """Represents an unique rfc5545 iCalendar."""

    _TYPE = 'VCALENDAR'
    _EXTRACTORS = []
    _OUTPUTS = []

    def __init__(self, imports=None, events=None, todos=None, creator=None):
        """Instantiates a new Calendar.

        Args:
            imports (string or list of lines/strings): data to be imported into the Calendar(),
            events (list of Event): :class:`ics.event.Event`s to be added to the calendar
            todos (list of Todo): :class:`ics.event.Todo`s to be added to the calendar
            creator (string): uid of the creator program.

        If `imports` is specified, every other argument will be ignored.
        """
        # TODO : implement a file-descriptor import and a filename import

        self._timezones = {}
        self.events = set()
        self.todos = set()
        self._unused = Container(name='VCALENDAR')
        self.scale = None
        self.method = None

        self.timeline = Timeline(self)

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
            if events is not None:
                self.events.update(set(events))
            if todos is not None:
                self.todos.update(set(todos))
            self._creator = creator

    def __urepr__(self):
        """Returns:
            unicode: representation (__repr__) of the calendar.

        Should not be used directly. Use self.__repr__ instead.
        """
        return "<Calendar with {} event{} and {} todo{}>" \
            .format(len(self.events),
                    "s" if len(self.events) > 1 else "",
                    len(self.todos),
                    "s" if len(self.todos) > 1 else "")

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

        for attr in ('_unused', 'scale', 'method', 'creator'):
            if self.__getattribute__(attr) != other.__getattribute__(attr):
                return False

        return (self.events == other.events) and (self.todos == other.todos)

    def __ne__(self, other):
        return not self.__eq__(other)

    @property
    def creator(self):
        """Get or set the calendar's creator.

        |  Will return a string.
        |  May be set to a string.
        |  Creator is the PRODID iCalendar property.
        |  It uniquely identifies the program that created the calendar.
        """
        return self._creator

    @creator.setter
    def creator(self, value):
        if not isinstance(value, text_type):
            raise ValueError('Event.creator must be unicode data not {}'.format(type(value)))
        self._creator = value

    def clone(self):
        """
        Returns:
            Calendar: an exact deep copy of self
        """
        clone = copy.copy(self)
        clone._unused = clone._unused.clone()
        clone.events = copy.copy(self.events)
        clone.todos = copy.copy(self.todos)
        clone._timezones = copy.copy(self._timezones)
        return clone


# ------------------
# ----- Inputs -----
# ------------------

@Calendar._extracts('PRODID', required=True)
def prodid(calendar, prodid):
    calendar._creator = prodid.value


__version_default__ = [ContentLine(name='VERSION', value='2.0')]


@Calendar._extracts('VERSION', required=True, default=__version_default__)
def version(calendar, line):
    version = line
    # TODO : should take care of minver/maxver
    if ';' in version.value:
        _, calendar.version = version.value.split(';')
    else:
        calendar.version = version.value


@Calendar._extracts('CALSCALE')
def scale(calendar, line):
    calscale = line
    if calscale:
        calendar.scale = calscale.value.lower()
        calendar.scale_params = calscale.params
    else:
        calendar.scale = 'georgian'
        calendar.scale_params = {}


@Calendar._extracts('METHOD')
def method(calendar, line):
    method = line
    if method:
        calendar.method = method.value
        calendar.method_params = method.params
    else:
        calendar.method = None
        calendar.method_params = {}


@Calendar._extracts('VTIMEZONE', multiple=True)
def timezone(calendar, vtimezones):
    """Receives a list of VTIMEZONE blocks.

    Parses them and adds them to calendar._timezones.
    """
    for vtimezone in vtimezones:
        remove_x(vtimezone)  # Remove non standard lines from the block
        fake_file = StringIO()
        fake_file.write(str(vtimezone))  # Represent the block as a string
        fake_file.seek(0)
        timezones = tzical(fake_file)  # tzical does not like strings
        # timezones is a tzical object and could contain multiple timezones
        for key in timezones.keys():
            calendar._timezones[key] = timezones.get(key)


@Calendar._extracts('VEVENT', multiple=True)
def events(calendar, lines):
    # tz=calendar._timezones gives access to the event factory to the
    # timezones list
    def event_factory(x):
        return Event._from_container(x, tz=calendar._timezones)
    calendar.events = list(map(event_factory, lines))


@Calendar._extracts('VTODO', multiple=True)
def todos(calendar, lines):
    # tz=calendar._timezones gives access to the event factory to the
    # timezones list
    def todo_factory(x):
        return Todo._from_container(x, tz=calendar._timezones)
    calendar.todos = list(map(todo_factory, lines))


# -------------------
# ----- Outputs -----
# -------------------

@Calendar._outputs
def o_prodid(calendar, container):
    creator = calendar.creator if calendar.creator else \
        'ics.py - http://git.io/lLljaA'
    container.append(ContentLine('PRODID', value=creator))


@Calendar._outputs
def o_version(calendar, container):
    container.append(ContentLine('VERSION', value='2.0'))


@Calendar._outputs
def o_scale(calendar, container):
    if calendar.scale:
        container.append(ContentLine('CALSCALE', value=calendar.scale.upper()))


@Calendar._outputs
def o_method(calendar, container):
    if calendar.method:
        container.append(ContentLine('METHOD', value=calendar.method.upper()))


@Calendar._outputs
def o_events(calendar, container):
    for event in calendar.events:
        container.append(str(event))


@Calendar._outputs
def o_todos(calendar, container):
    for todo in calendar.todos:
        container.append(str(todo))
