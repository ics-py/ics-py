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
    """docstring for Calendar"""

    _TYPE = "VCALENDAR"
    _EXTRACTORS = []

    def __init__(self, string=None, events=EventList(), creator=None):
        self._timezones = {}
        self._events = EventList()
        self._events.today = lambda: 1
        if string is not None:
            if isinstance(string, (str, unicode)):
                container = string_to_container(string)
            else:
                container = lines_to_container(string)

            # TODO : make a better API for multiple calendars
            if len(container) != 1:
                raise NotImplementedError('Multiple calendars in one file are not supported')

            self._populate(container[0])
        else:
            if events:
                self.events = events
            if creator:
                self.creator = creator

    def __unicode__(self):
        return "<Calendar with {} events>".format(len(self.events))

    @property
    def events(self):
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
