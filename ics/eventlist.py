#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals, absolute_import

from six import PY2, PY3, StringIO, string_types, text_type, integer_types
from six.moves import filter, map, range

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
