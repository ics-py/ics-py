#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals, absolute_import

from six import PY2, PY3, StringIO, string_types, text_type, integer_types
from six.moves import filter, map, range

from arrow.arrow import Arrow
import arrow


class EventList(list):
    '''EventList is a subclass of the standard list.
    It can be used as a list but also has super slicing capabilities and some helpers.'''

    def __init__(self, *args, **kwargs):
        '''Instanciates a new EventList. Accepts same arguments as list() and pass them all to list()'''
        super(EventList, self).__init__(*args, **kwargs)

    def __getitem__(self, key):
        '''Slices EventList.
        If the slice is conventional (like [10], [4:12], [3:100:2], [::-1], etc) it slices the EventList like a classical list().
        If one of the 3 arguments ([start:stop:step]) is not None or an int, slicing differs.

        In that case, 'start' and 'stop' are considerated like instants (or None) and 'step' like a modificator.
        'start' and 'stop' will be converted to Arrow objects (or None) with arrow.get().

        ... MOARZ info coming soon ...
        '''
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

    def today(self, strict=False):
        '''Return all events that occurs today.
        If strict is True, events will be returned only if they are strictly *included* in today'''
        return self[arrow.now()]

    def on(self, day, strict=False):
        '''Return all events that occurs on 'day'.
        If strict is True, events will be returned only if they are strictly *included* in 'day'.
        'day' will be parsed by arrow.get() if it's not an Arrow object.'''
        if not isinstance(day, Arrow):
            day = arrow.get(day)
        return self[day]

    def now(self):
        '''Return all events that occurs now.'''
        return self[arrow.now():arrow.now().ceil('microsecond')]

    def at(self, instant):
        '''Return all events that are occuring at that instant.
        'instant' will be parsed by arrow.get() if it's not an Arrow object'''
        if not isinstance(instant, Arrow):
            instant = arrow.get(instant)
        return self[instant:instant.ceil('microsecond'):'one']
