#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals, absolute_import
from collections import Iterable

from six import PY2, PY3, StringIO, string_types, text_type, integer_types
from six.moves import filter, map, range

from arrow.arrow import Arrow
import arrow

from datetime import datetime, time, timedelta
from .utils import get_arrow, get_date_or_datetime
from .event import Event


class EventList(list):

    """EventList is a subclass of the standard :class:`list`.

    It can be used as a list but also has super slicing capabilities
    and some helpers.
    """

    def __init__(self, arg=[]):
        """Instantiates a new :class:`ics.eventlist.EventList`.

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

        In that case, `start` and `stop` are considered as instants\
        (or None) and `step` like a modificator.
        `start` and `stop` will be converted to :class:`datetime` objects (or None)\
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

        if not isinstance(sl, slice) and not isinstance(sl, datetime):
            # not an int, not a slice, not a datetime,
            # try to convert it to a datetime
            sl = get_date_or_datetime(sl)

        if isinstance(sl, datetime):  # Single datetime slice
            begin = datetime.combine(sl.date(), time(0))
            end = begin + timedelta(1)
            sl = slice(begin, end, 'both')

        # now it has to be a slice
        int_or_none = integer_types + (type(None), )
        if (isinstance(sl.start, int_or_none) and
                isinstance(sl.stop, int_or_none) and
                isinstance(sl.step, int_or_none)):
            # classical slice
            return super(EventList, self).__getitem__(sl)

        # now we have a slice and it's a special one
        step = sl.step or 'both'  # Empty step -> default value
        begin = get_date_or_datetime(sl.start)
        end = get_date_or_datetime(sl.stop)

        def _begin(event):
            return ((begin is None or event.begin > begin) and
                    (end is None or event.begin < end))

        def _end(event):
            return ((begin is None or event.end > begin) and
                    (end is None or event.end < end))

        def _both(event):
            return ((begin is None or event.begin > begin and event.end > begin) and
                    (end is None or event.begin < end and event.end < end))

        def _any(event):
            return ((begin is None or event.begin > begin or event.end > begin) and
                    (end is None or event.begin < end or event.end < end))

        def _inc(event):
            return (begin is not None and end is None and
                    event.begin < begin or event.end < end)

        def _error(event):
            msg = "The step must be 'begin', 'end', 'both', 'any', 'inc' or None not '{}'"
            raise ValueError(msg.format(step))

        modificators = {'begin': _begin,
                        'end': _end,
                        'both': _both,
                        'any': _any,
                        'inc': _inc, }
        return list(filter(modificators.get(step, _error), self))

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
