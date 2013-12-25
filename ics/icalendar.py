#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from six import PY2, PY3, StringIO, string_types, text_type, integer_types
from six.moves import filter, map, range

import parse
from utils import iso_to_arrow, iso_precision, parse_duration, Node, remove_x
from dateutil.tz import tzical
from arrow.arrow import Arrow
import arrow


class EventList(list):
    # def __init__(self, *args, **kwargs):
    #     super(EventList, self).__init__(*args, **kwargs)

    def __getitem__(self, key):
        # Integer slice
        if isinstance(key, integer_types):
            return super(EventList, self).__getitem__(key)

        if isinstance(key, Arrow):  # Single arrow slice
            start, stop = key.floor('day').span('day')
            step = 'both'
        elif not isinstance(key, slice):  # not a slice, not an int
            start, stop = arrow.get(key).floor('day').span('day')
            step = 'both'
        else:  # slice object
            if isinstance(key.start, integer_types):  # classical int slice
                return super(EventList, self).__getitem__(key)

            if key.step is None:  # Empty step
                step = 'both'
            elif not key.step in ('start', 'stop', 'both', 'any', 'inc'):  # invalid step
                raise ValueError("The step must be 'start', 'stop', 'both', 'any' or 'inc' not '{}'".format(key.step))
            else:  # valid step
                step = key.step

            start, stop = key.start, key.stop

            if not isinstance(start, Arrow) and not start is None:
                start = arrow.get(start)
            if not isinstance(stop, Arrow) and not stop is None:
                stop = arrow.get(stop)

        if start and stop:  # start and stop provided
            if step == 'start':
                return list(filter(lambda x: start < x.begin < stop, self))
            if step == 'stop':
                return list(filter(lambda x: start < x.end < stop, self))
            if step == 'both':
                return list(filter(lambda x: start < x.begin < x.end < stop, self))
            if step == 'inc':
                return list(filter(lambda x: x.begin < start < stop < x.end, self))
            if step == 'any':
                return list(filter(lambda x: (start < x.begin < stop) or (start < x.end < stop), self))
        elif start:  # only start provided
            if step in ('start', 'both'):
                return list(filter(lambda x: x.begin > start, self))
            if step == 'stop':
                return list(filter(lambda x: x.end > start, self))
        elif stop:  # only stop provided
            if step in ('stop', 'both'):
                return list(filter(lambda x: x.end < stop, self))
            if step == 'start':
                return list(filter(lambda x: x.begin > stop, self))

    def today(self):
        return self[arrow.now()]

    def on(self, time):
        if not isinstance(time, Arrow):
            time = arrow.get(time)
        return self[time]

    def now(self):
        return self[arrow.now():arrow.now().ceil('microsecond')]

    def at(self, time):
        if not isinstance(time, Arrow):
            time = arrow.get(time)
        return self[time:time.ceil('microsecond'):'one']


class Calendar(Node):
    """docstring for Calendar"""

    _TYPE = "VCALENDAR"
    _EXTRACTORS = []

    def __init__(self, string=None, events=EventList(), creator=None):
        self._timezones = {}
        self._events = EventList()
        self._events.today = lambda: 1
        if string is not None:
            if isinstance(string, (str, unicode)):
                container = parse.string_to_container(string)
            else:
                container = parse.lines_to_container(string)

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


class Event(Node):
    """Docstring for Event """

    _TYPE = "VEVENT"
    _EXTRACTORS = []

    def __init__(self, name=None, begin=None, end=None, duration=None):
        self._duration = None
        self._end_time = None
        self._begin = None
        self._begin_precision = 'day'

        self.name = name
        self.begin = begin
        if duration and end:
            raise ValueError('Event() may not specify an end and a duration at the same time')
        elif end:
            self.end = end
        elif duration:
            self.duration = duration

    def has_end(self):
        return bool(self._end_time or self._duration)

    @property
    def begin(self):
        return self._begin

    @begin.setter
    def begin(self, value):
        '''removes and and duration as well'''
        if not isinstance(value, Arrow) and not value is None:
                value = arrow.get(value)
        if value and self._end_time and value > self._end_time:
            raise ValueError('Begin must be before than end')
        self._begin = value
        self._begin_precision = 'second'

    @property
    def end(self):
        if self._duration:
            return self.begin.replace(**self._duration)
        elif self._end_time:
            return self._end_time
        else:
            # TODO : ask a .add() method to arrow devs
            return self.begin.replace(**{self._begin_precision + 's': +1})

    @end.setter
    def end(self, value):
        if not isinstance(value, Arrow) and not value is None:
                value = arrow.get(value)
        if value and value < self._begin:
            raise ValueError('End must be after than begin')

        self._end_time = value
        if value:
            self._duration = None

    @property
    def all_day(self):
        return self._begin_precision == 'day' and not self.has_end()

    def make_all_day(self):
        self._begin_precision = 'day'
        self._begin = self._begin.floor('day')
        self._duration = None
        self._end_time = None

    def __unicode__(self):
        name = "'{}' ".format(self.name) if self.name else ''
        if self.all_day:
            return "<Event {}whole-day:{}>".format(name, self.begin.strftime("%F"))
        else:
            return "<Event {}begin:{} end:{}>".format(name, self.begin.strftime("%F %X"), self.end.strftime("%F %X"))


@Event._extracts('CREATED')
def created(event, line):
    event.created = line


@Event._extracts('DTSTART')
def start(event, line):
    # TODO : check if line != None
    tz_dict = event._classmethod_kwargs['tz']
    event.begin = iso_to_arrow(line, tz_dict)
    event._begin_precision = iso_precision(line.value)


@Event._extracts('DURATION')
def duration(event, line):
    event._duration = parse_duration(line)


@Event._extracts('DTEND')
def end(event, line):
    tz_dict = event._classmethod_kwargs['tz']
    event._end_time = iso_to_arrow(line, tz_dict)


@Event._extracts('SUMMARY')
def summary(event, line):
    event.name = line.value if line else None


@Event._extracts('DESCRIPTION')
def description(event, line):
    event.description = line.value if line else None


# TODO : make uid required ?
# TODO : add option somwhere to ignore some errors
@Event._extracts('UID')
def uid(event, line):
    event.uid = line
