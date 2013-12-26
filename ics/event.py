#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals, absolute_import

from six import PY2, PY3, StringIO, string_types, text_type, integer_types
from six.moves import filter, map, range

from arrow.arrow import Arrow
import arrow

from .component import Component
from .utils import parse_duration, iso_to_arrow, iso_precision


class Event(Component):
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
