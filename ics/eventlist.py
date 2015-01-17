#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals, absolute_import
from collections import Iterable

from six import PY2, PY3, StringIO, string_types, text_type, integer_types
from six.moves import filter, map, range

from arrow.arrow import Arrow
import arrow

from .utils import get_arrow
from .event import Event


class EventList(list):

    """EventList is a subclass of the standard :class:`list`.

    It can be used as a list but also has super slicing capabilities and some helpers.
    """

    def __init__(self, arg=[]):
        """Instanciates a new :class:`ics.eventlist.EventList`.

            Args:
                arg (iterable): same argument as list() and pass it to list().
            Raises:
                ValueError: if `arg`contains elements which are not :class:`ics.event.Event`
        """

        super(EventList, self).__init__()
        self.sort()

        for elem in arg:
            if not isinstance(elem, Event):
                raise ValueError('EventList takes only iterables with elements of type "Event" not {}'
                    .format(type(elem)))
            else:
                self.append(elem)

    def __getitem__(self, sl):
        """Slices :class:`ics.eventlist.EventList`.

        Note : an :class:`ics.eventlist.EventList` is always sorted and the slices \
        returned by this method will be sorted too.

        If sl is conventional (like [10], [4:12], [3:100:2], [::-1], …),\
        it slices the :class:`ics.eventlist.EventList` like a classical list().
        If one of the 3 arguments ([start:stop:step]) is not None or an int,\
        slicing differs.

        In that case, `start` and `stop` are considerated like instants\
        (or None) and `step` like a modificator.
        `start` and `stop` will be converted to :class:`Arrow` objects (or None)\
        with :func:`arrow.get`.

        - start (:class:`Arrow-convertible`): \
        lower included bond,
        - stop (:class:`Arrow-convertible`): \
        upper, non included, bond.

        Modificators:
            - begin: the beginning of the events has to be \
            between the bonds.
            - end: the end of the events has to be \
            between the bonds.
            - both: both the end and the beginning have to be \
            between the bonds.
            - any: either (or both) the start of the beginning has to be \
            between the bonds.
            - inc: the events have to include be bonds \
            (start < event.begin < event.end < stop).
        """
        # Integer slice
        if isinstance(sl, integer_types):
            return super(EventList, self).__getitem__(sl)

        if isinstance(sl, Arrow):  # Single arrow slice
            begin, end = sl.floor('day').span('day')
            return self[begin:end:'both']

        # not a slice, not an int, try to convert it to an Arrow
        if not isinstance(sl, slice):
            begin, end = get_arrow(sl).floor('day').span('day')
            return self[begin:end:'both']

        # now it has to be a slice
        int_or_none = integer_types + (type(None), )
        if isinstance(sl.start, int_or_none) \
            and isinstance(sl.stop, int_or_none) \
                and isinstance(sl.step, int_or_none):
            # classical slice
            return super(EventList, self).__getitem__(sl)

        # now we have a slice and it's a special one
        if sl.step is None:  # Empty step -> default value
            step = 'both'
        # invalid step
        elif sl.step not in ('begin', 'end', 'both', 'any', 'inc'):
            raise ValueError(
                "The step must be 'begin', 'end', 'both', 'any', 'inc' \
or None not '{}'".format(sl.step))
        else:  # valid step
            step = sl.step

        begin, end = get_arrow(sl.start), get_arrow(sl.stop)
        condition0 = lambda x: True

        if begin:
            condition_begin1 = lambda x: condition0(x) and x.begin > begin
            condition_end1 = lambda x: condition0(x) and x.end > begin
            if step == 'begin':
                condition1 = condition_begin1
            elif step == 'end':
                condition1 = condition_end1
            elif step == 'any':
                condition1 = lambda x: condition_begin1(x) or \
                    condition_end1(x)
            elif step == 'both':
                condition1 = lambda x: condition_begin1(x) and \
                    condition_end1(x)
        else:
            condition1 = condition0

        if end:
            condition_begin2 = lambda x: condition1(x) and x.begin < end
            condition_end2 = lambda x: condition1(x) and x.end < end
            if step == 'begin':
                condition2 = condition_begin2
            elif step == 'end':
                condition2 = condition_end2
            elif step == 'any':
                condition2 = lambda x: condition_begin2(x) or \
                    condition_end2(x)
            elif step == 'both':
                condition2 = lambda x: condition_begin2(x) and \
                    condition_end2(x)
        else:
            condition2 = condition1

        if step == 'inc':
            if not begin or not end:
                return []
            condition2 = lambda x: x.begin < begin and end < x.end

        return list(filter(condition2, self))

    def today(self, strict=False):
        """Args:
            strict (bool): if True events will be returned only if they are\
            strictly *included* in `day`.

        Returns:
            list<Event>: all events that occurs today
        """
        return self[arrow.now()]

    def on(self, day, strict=False):
        """Args:
            day (Arrow-convertible)
            strict (bool): if True events will be returned only if they are\
            strictly *included* in `day`.

        Returns:
            list<Event>: all events that occurs on `day`
        """
        if not isinstance(day, Arrow):
            day = arrow.get(day)
        return self[day]

    def now(self):
        """
        Returns:
            list<Event>: all events that occurs now
        """
        now = []
        for event in self:
            if event.begin <= arrow.now() <= event.end:
                now.append(event)
        return now

    def at(self, instant):
        """Args:
            instant (Arrow-convertible)

        Returns:
            list<Event>: all events that are occuring during `instant`.
        """
        at = []
        for event in self:
            if event.begin <= instant <= event.end:
                at.append(event)
        return at

    def concurrent(self, event):
        """Args:
            event (Event)
        Returns:
            list<Event>: all events that are overlapping `event`
        """
        a = self[event.begin:event.end:'any']
        b = self[None:event.begin:'begin']
        c = self[event.end:None:'end']
        return list(set(a) | (set(b) & set(c)))

    def _remove_duplicates(self):
        seen = set()
        for i in reversed(range(len(self))):
            if self[i] in seen:
                del self[i]
            else:
                seen.add(self[i])

    def __add__(self, *args, **kwargs):
        """Add 2 :class:`ics.eventlist.EventList`.

        Returns:
            EventList: a new EventList containing\
            a copy of each :class:`ics.event.Event` in the union of both EventList"""
        ret = super(EventList, self).__add__(*args, **kwargs)
        ret = EventList(ret)
        ret._remove_duplicates()
        return ret

    def __urepr__(self):
        return "<EventList {}>".format(super(EventList, self).__repr__())

    def clone(self):
        """
        Returns:
            Copy of `self` containing copies of underlying Event
        """
        events = map(lambda x: x.clone(), self)
        return EventList(events)

    def __setitem__(self, key, val):
        """Set an item or a slice. Verifies that all items are instance of :class:`ics.event.Event`"""
        if isinstance(key, slice):
            acc = []
            for elem in val:
                if not isinstance(elem, Event):
                    raise ValueError('EventList may only contain elements of type "Event" not {}'
                        .format(type(elem)))
                else:
                    acc.append(elem)
            val = acc
        elif not isinstance(val, Event):
            raise ValueError('EventList may only contain elements of type "Event" not {}'
                .format(type(val)))
        super(EventList, self).__setitem__(key, val)
        self.sort()

    def __setslice__(self, i, j, val):
        """Compatibility for python2"""
        return self.__setitem__(slice(i, j), val)

    def append(self, elem):
        """Append a element to self and verifies that it's an :class:`ics.event.Event`.

        Args:
            elem (Event): element to be appended
        Raises:
            ValueError: if `elem` is not a :class:`ics.event.Event`
        """
        if not isinstance(elem, Event):
            raise ValueError('EventList may only contain elements of type "Event" not {}'
                .format(type(elem)))
        super(EventList, self).append(elem)
        self.sort()
