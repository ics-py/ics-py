#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals, absolute_import
import heapq

from six import PY2, PY3, StringIO, string_types, text_type, integer_types
from six.moves import filter, map, range

from arrow.arrow import Arrow
import arrow

from .utils import get_arrow
from .event import Event


class Timeline(object):

    def __init__(self, calendar):
        """Instanciates a new Timeline.
        (You should not have to instanciate a new timeline by yourself)

        Args:
            calendar : :class:`ics.icalendar.Calendar`
        """
        self._calendar = calendar

    def __iter__(self):
        """Iterates on every event from the :class:`ics.icalendar.Calendar` in chronological order

        Note :
            - chronological order is defined by the comparaison operators in :class:`ics.event.Event`
            - Events with no `begin` will not appear here. (To list all events in a `Calendar` use `Calendar.events`)
        """
        # Using a heap is faster than sorting if the number of events (n) is
        # much bigger than the number of events we extract from the iterator (k).
        # Complexity: O(n + k log n).
        heap = [x for x in self._calendar.events if x.begin is not None]
        heapq.heapify(heap)
        while heap:
            yield heapq.heappop(heap)

    def included(self, start, stop):
        """Iterates (in chronological order) over every event that is included
        in the timespan between `start` and `stop`

        Args:
            start : (Arrow object)
            stop : (Arrow object)
        """
        for event in self:
            if (start <= event.begin <= stop # if start is between the bonds
            and start <= event.end <= stop): # and stop is between the bonds
                yield event

    def overlapping(self, start, stop):
        """Iterates (in chronological order) over every event that has an intersection
        with the timespan between `start` and `stop`

        Args:
            start : (Arrow object)
            stop : (Arrow object)
        """
        for event in self:
            if ((start <= event.begin <= stop # if start is between the bonds
            or start <= event.end <= stop) # or stop is between the bonds
            or event.begin <= start and event.end >= stop): # or event is a superset of [start,stop]
                yield event

    def start_after(self, instant):
        """Iterates (in chronological order) on every event from the :class:`ics.icalendar.Calendar` in chronological order.
        The first event of the iteration has a starting date greater (later) than `instant`

        Args:
            instant : (Arrow object) starting point of the iteration
        """
        for event in self:
            if event.begin > instant:
                yield event

    def at(self, instant):
        """Iterates (in chronological order) over all events that are occuring during `instant`.

        Args:
            instant (Arrow object)
        """

        for event in self:
            if event.begin <= instant <= event.end:
                yield event

    def on(self, day, strict=False):
        """Iterates (in chronological order) over all events that occurs on `day`

        Args:
            day (Arrow object)
            strict (bool): if True events will be returned only if they are\
            strictly *included* in `day`.
        """
        day_start, day_stop = day.floor('day').span('day')
        if strict:
            return self.included(day_start, day_stop)
        else:
            return self.overlapping(day_start, day_stop)

    def today(self, strict=False):
        """Iterates (in chronological order) over all events that occurs today

        Args:
            strict (bool): if True events will be returned only if they are\
            strictly *included* in `day`.
        """
        return self.on(arrow.now(), strict=strict)

    def now(self):
        """Iterates (in chronological order) over all events that occurs now
        """
        return self.at(arrow.now())
