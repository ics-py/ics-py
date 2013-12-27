#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals, absolute_import

from six import PY2, PY3, StringIO, string_types, text_type, integer_types
from six.moves import filter, map, range

import arrow
from uuid import uuid4

from .component import Component
from .utils import parse_duration, iso_to_arrow, iso_precision, get_arrow, arrow_to_iso
from .parse import ContentLine


class Event(Component):
    '''A calendar event.
    Can be full-day or between two instants.
    Can be defined by a begin instant and a {duration,end instant}'''
    # TODO : order events
    _TYPE = "VEVENT"
    _EXTRACTORS = []
    _OUTPUTS = []

    def __init__(self, name=None, begin=None, end=None, duration=None):
        '''Instanciates a new Event.
        Optional arguments:
            - name (string)
            - begin (arrow.get() compatible or Arrow)
            - end (arrow.get() compatible or Arrow)
            - duration
        'end' and 'duration' may not be specified at the same time (raises ValueError)'''

        self._duration = None
        self._end_time = None
        self._begin = None
        self._begin_precision = 'day'
        self.uid = str(uuid4())
        self.description = None

        self.name = name
        self.begin = begin
        if duration and end:
            raise ValueError('Event() may not specify an end and a duration at the same time')
        elif end: # End was specified
            self.end = end
        elif duration: # Duration was specified
            self.duration = duration

    def has_end(self):
        '''bool. Event has an end.'''
        return bool(self._end_time or self._duration)

    @property
    def begin(self):
        '''Get or set the beginning of the event.
        Will return an Arrow object. May be set to anything that arrow.get() understands.
        If an end is defined (not a duration), .begin must not be set to a superior value.'''
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
        '''Get or set the end of the event.
        Will return an Arrow object. May be set to anything that arrow.get() understands.
        If setted to a non null value, removes any already existing duration.
        Setting to None will have unexpected behavior if begin is not None.
        Must not be setted to an inferior value than self.begin'''

        if self._duration: # if end is duration defined
            return self.begin.replace(**self._duration) # return the beginning + duration
        elif self._end_time: # if end is time defined
            return self._end_time
        else: # if end is not defined
            # return beginning + precision
            return self.begin.replace(**{self._begin_precision + 's': +1})

    @end.setter
    def end(self, value):
        value = get_arrow(value)
        if value and value < self._begin:
            raise ValueError('End must be after than begin')

        self._end_time = value
        if value:
            self._duration = None

    @property
    def all_day(self):
        '''Bool: event is an all-day event'''
        return self._begin_precision == 'day' and not self.has_end()

    def make_all_day(self):
        '''Transforms an event to a all-day event.
        The day will be the day of self.begin.'''
        self._begin_precision = 'day'
        self._begin = self._begin.floor('day')
        self._duration = None
        self._end_time = None

    def __unicode__(self):
        '''Return a unicode representation (__repr__) of the event.
        Should not be used directly. Use self.__repr__ instead.'''
        name = "'{}' ".format(self.name) if self.name else ''
        if self.all_day:
            return "<all-day Event {} :{}>".format(name, self.begin.strftime("%F"))
        else:
            return "<Event {}begin:{} end:{}>".format(name, self.begin.strftime("%F %X"), self.end.strftime("%F %X"))

    def __str__(self):
        '''Return the event as an iCalendar formatted string'''
        return super(Event, self).__str__()


######################
####### Inputs #######

@Event._extracts('DTSTAMP')
def created(event, line):
    event.created = line


@Event._extracts('DTSTART')
def start(event, line):
    if line:
        tz_dict = event._classmethod_kwargs['tz'] # get the dict of vtimezeones passed to the classmethod
        event.begin = iso_to_arrow(line, tz_dict)
        event._begin_precision = iso_precision(line.value)


@Event._extracts('DURATION')
def duration(event, line):
    if line:
        event._duration = parse_duration(line)


@Event._extracts('DTEND')
def end(event, line):
    if line:
        tz_dict = event._classmethod_kwargs['tz'] # get the dict of vtimezeones passed to the classmethod
        event._end_time = iso_to_arrow(line, tz_dict)


@Event._extracts('SUMMARY')
def summary(event, line):
    event.name = line.value if line else None


@Event._extracts('DESCRIPTION')
def description(event, line):
    event.description = line.value if line else None


# TODO : make uid required ?
# TODO : add option somewhere to ignore some errors
@Event._extracts('UID')
def uid(event, line):
    event.uid = line


######################
###### Outputs #######
@Event._outputs
def o_created(event, container):
    if event.created:
        instant = arrow_to_iso(event.created)
    else:
        instant = arrow.now()

    container.append(ContentLine('DTSTAMP', value=arrow_to_iso(instant)))


@Event._outputs
def o_start(event, container):
    if event.begin:
        container.append(ContentLine('DTSTART', value=arrow_to_iso(event.begin)))

    # TODO : take care of precision


@Event._outputs
def o_duration(event, container):
    # TODO : DURATION
    pass


@Event._outputs
def o_end(event, container):
    if event.end:
        container.append(ContentLine('DTEND', value=arrow_to_iso(event.end)))


@Event._outputs
def o_summary(event, container):
    if event.name:
        container.append(ContentLine('SUMMARY', value=event.name))


@Event._outputs
def o_description(event, container):
    if event.description:
        container.append(ContentLine('DESCRIPTION', value=event.description))


@Event._outputs
def o_uid(event, container):
    if event.uid:
        uid = event.uid
    else:
        uid = str(uuid4())
        uid = "{}@{}.org".format(uid, uid[:4])
    container.append(ContentLine('UID', value=uid))
