#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import parse
from utils import iso_to_arrow, iso_precision, parse_duration, Node, remove_x
from dateutil.tz import tzical
import StringIO


class Calendar(Node):
    """docstring for Calendar"""

    _TYPE = "VCALENDAR"
    _EXTRACTORS = []

    def __init__(self, string=None):
        self._timezones = {}
        self.events = []
        if string is not None:
            if isinstance(string, (str, unicode)):
                container = parse.string_to_container(string)
            else:
                container = parse.lines_to_container(string)

            # TODO : make a better API for multiple calendars
            if len(container) != 1:
                raise NotImplementedError('Multiple calendars in one file are not supported')

            self._populate(container[0])

    def __repr__(self):
        return "<Calendar with {} events>".format(len(self.events))


@Calendar._extracts('PRODID', required=True)
def prodid(calendar, line):
    prodid = line
    calendar.creator = prodid.value
    calendar.creator_params = prodid.params


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
        fake_file = StringIO.StringIO()
        fake_file.write(str(isotz))
        fake_file.seek(0)
        timezones = tzical(fake_file)
        for key in timezones.keys():
            calendar._timezones[key] = timezones.get(key)


@Calendar._extracts('VEVENT', multiple=True)
def events(calendar, lines):
    calendar.events = map(lambda x: Event._from_container(x, tz=calendar._timezones), lines)


class Event(Node):
    """Docstring for Event """

    _TYPE = "VEVENT"
    _EXTRACTORS = []

    @property
    def end(self):
        if self._duration:
            return self.begin.replace(**self._duration)
        elif self._end_time:
            return self._end_time
        else:
            # TODO : ask a .add() method to arrow devs
            return self.begin.replace(**{self._begin_precision + 's': +1})

    def __repr__(self):
        if self._begin_precision == 'day':
            return "<Event '{}' begin:{} end:{}>".format(self.name, self.begin.strftime("%F"), self.end.strftime("%F"))
        else:
            return "<Event '{}' begin:{} end:{}>".format(self.name, self.begin.strftime("%F %X"), self.end.strftime("%F %X"))


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
