#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals, absolute_import

from six import PY2, PY3, StringIO, string_types, text_type, integer_types
from six.moves import filter, map, range

from dateutil.tz import tzical
from arrow.arrow import Arrow
import arrow

from .component import Component
from .event import Event
from .eventlist import EventList
from .parse import lines_to_container, string_to_container
from .utils import remove_x


class Calendar(Component):
    '''Represents a unique rfc5545 icalendar.'''

    _TYPE = "VCALENDAR"
    _EXTRACTORS = []

    def __init__(self, imports=None, events=EventList(), creator=None):
        '''Instanciates a new Calendar.
        Optional arguments:
            - imports (string or list of lines/strings) : data to be imported into the Calendar()
            - events (list of Events or EventList) : if Events: will use to construct internal EventList. If EventList : will use event in place of creating a new internal EventList
            - creator (string) : uid of the creator program
        If 'imports' is specified, __init__ ignores every other argument.'''
        # TODO : implement a file-descriptor import and a filename import

        self._timezones = {}
        self._events = EventList()

        if imports is not None:
            # TODO : Check python3 types
            if isinstance(imports, (str, unicode)):
                container = string_to_container(imports)
            else:
                container = lines_to_container(imports)

            # TODO : make a better API for multiple calendars
            if len(container) != 1:
                raise NotImplementedError('Multiple calendars in one file are not supported')

            self._populate(container[0]) # Use first calendar
        else:
            self._events = events
            self._creator = creator

    def __unicode__(self):
        '''Return a unicode representation (__repr__) of the calendar.
        Should not be used directly. Use self.__repr__ instead'''
        return "<Calendar with {} events>".format(len(self.events))

    @property
    def events(self):
        '''Get or set the list of calendar's events.
        Will return an EventList object (similar to python list).
        May be setted to a list or an EventList (otherwise will raise a ValueError).
        If setted, will override all pre-existing events.'''
        return self._events

    @events.setter
    def events(self, value):
        if isinstance(value, list):
            self._events = EventList(value)
        elif isinstance(value, EventList):
            self._events = value
        else:
            raise ValueError('Calendar.events must be a list or a EventList')

    @property
    def creator(self):
        '''Get or set the calendar's creator.
        Will return a string.
        May be setted to a string.
        Creator is the PRODID icalendar property. It uniquely identifies the program that created the calendar.'''
        return self._creator

    @creator.setter
    def creator(self, value):
        if isinstance(value, string_types) and PY2:
            self._creator = unicode(value)
        elif isinstance(value, text_type):
            self._creator = value
        else:
            value = str(value)
            if PY2:
                value = unicode(value)
            self._creator = value


@Calendar._extracts('PRODID', required=True)
def prodid(calendar, prodid):
    calendar._creator = prodid.value


@Calendar._extracts('VERSION', required=True)
def version(calendar, line):
    version = line
    #TODO : should take care of minver/maxver
    if ';' in version.value:
        _, calendar.version = version.value.split(';')
    else:
        calendar.version = version.value


@Calendar._extracts('CALSCALE')
def scale(calendar, line):
    calscale = line
    if calscale:
        calendar.scale = calscale.value
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
def timezone(calendar, lines):
    for isotz in lines:
        remove_x(isotz)
        fake_file = StringIO()
        fake_file.write(str(isotz))
        fake_file.seek(0)
        timezones = tzical(fake_file)
        for key in timezones.keys():
            calendar._timezones[key] = timezones.get(key)


@Calendar._extracts('VEVENT', multiple=True)
def events(calendar, lines):
    calendar.events = list(map(lambda x: Event._from_container(x, tz=calendar._timezones), lines))
