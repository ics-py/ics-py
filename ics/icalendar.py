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
from .parse import lines_to_container, string_to_container, ContentLine
from .utils import remove_x


class Calendar(Component):
    '''Represents an unique rfc5545 iCalendar.'''

    _TYPE = "VCALENDAR"
    _EXTRACTORS = []
    _OUTPUTS = []

    def __init__(self, imports=None, events=EventList(), creator=None):
        '''Instanciates a new Calendar.
        Optional arguments:
            - imports (string or list of lines/strings): data to be imported into the Calendar()
            - events (list of Events or EventList): if Events: will use to construct internal EventList. If EventList : will use event in place of creating a new internal EventList
            - creator (string): uid of the creator program
        If 'imports' is specified, __init__ ignores every other argument.'''
        # TODO : implement a file-descriptor import and a filename import
        # TODO __add__ to merge 2 Calendars

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

    def __iter__(self):
        '''Returns an iterable version of __str__, line per line (with line-endings).
        Can be used to write calendar to a file: open('my.ics').writelines(calendar)'''
        for line in str(self).decode('utf-8').split('\n'):
            yield (line + '\n').encode('utf-8')

    def __str__(self):
        '''Return the calendar as an iCalendar formatted string'''
        return super(Calendar, self).__str__()

    @property
    def events(self):
        '''Get or set the list of calendar's events.
        Will return an EventList object (similar to python list).
        May be set to a list or an EventList (otherwise will raise a ValueError).
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
        May be set to a string.
        Creator is the PRODID iCalendar property. It uniquely identifies the program that created the calendar.'''
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


######################
####### Inputs #######

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
def timezone(calendar, vtimezones):
    '''Receives a list of VTIMEZONE blocks.
    Parses them and adds them to calendar._timezones'''
    for vtimezone in vtimezones:
        remove_x(vtimezone) # Remove non standard lines from the block
        fake_file = StringIO()
        fake_file.write(str(vtimezone)) # Represent the block as a string
        fake_file.seek(0)
        timezones = tzical(fake_file) # tzical does not like strings
        # timezones is a tzical object and could contain multiple timezones
        for key in timezones.keys():
            calendar._timezones[key] = timezones.get(key)


@Calendar._extracts('VEVENT', multiple=True)
def events(calendar, lines):
    # tz=calendar._timezones gives access to the event factory to the timezones list
    event_factory = lambda x: Event._from_container(x, tz=calendar._timezones)
    calendar.events = list(map(event_factory, lines))


######################
###### Outputs #######

@Calendar._outputs
def o_prodid(calendar, container):
    creator = calendar.creator if calendar.creator else 'ics.py - http://git.io/lLljaA'
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
