#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals, absolute_import

from six import integer_types
from six.moves import filter, map, range

from datetime import datetime, date, time, timedelta
from .utils import get_date_or_datetime, utcnow
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
            - any: the beginning has to be before stop and the end \
            has to be after start, i.e. the event and the start-stop-period \
            have to overlap.
            - inc: the events have to include be bonds \
            (start < event.begin < event.end < stop).

        Usually the beginning is not considered to be between the bonds \
        if it is equal to 'stop', as well as the end if it is equal to 'start'. \
        (In these cases the Event doesn't overlap the timespan except \
        for one single moment.)

          start    stop     'begin' 'end' 'both' 'any' 'inc'
            |        |
     +---+  |        |        no      no    no     no    no
        +---+        |        no      no    no     no    no
        +---+-+      |        no     yes    no    yes    no
         +--+--------+        no     yes    no    yes    no
         +--+--------+-+      no      no    no    yes    no
            +-----+  |       yes     yes   yes    yes    no
            +--------+       yes     yes   yes    yes    no
            +--------+-+     yes      no    no    yes    no
            | +---+  |       yes     yes   yes    yes   yes
            | +------+       yes     yes   yes    yes    no
            | +------+--+    yes      no    no    yes    no
            |        +---+    no      no    no     no    no
            |        |+--+    no      no    no     no    no
        """
        # Integer slice
        if isinstance(sl, integer_types):
            return super(EventList, self).__getitem__(sl)

        if not isinstance(sl, slice) and not isinstance(sl, datetime):
            # not an int, not a slice, not a datetime,
            # try to convert it to a datetime
            sl = get_date_or_datetime(sl)

        if isinstance(sl, date):  # True for date and datetime
            if isinstance(sl, datetime):  # Single datetime slice
                begin = datetime.combine(sl.date(),
                                         time(0, tzinfo=sl.tzinfo))
                end = begin + timedelta(1)
                sl = slice(begin, end, 'both')
            else:  # Single date slice
                sl = slice(sl, None, '_date')

        # now it has to be a slice
        int_or_none = integer_types + (type(None), )
        if (isinstance(sl.start, int_or_none) and
                isinstance(sl.stop, int_or_none) and
                isinstance(sl.step, int_or_none)):
            # classical slice
            return super(EventList, self).__getitem__(sl)

        # now we have a slice and it's a special one
        modifier = sl.step or 'both'  # Empty step -> default value
        start = get_date_or_datetime(sl.start)
        stop = get_date_or_datetime(sl.stop)
        print 'start', start
        print 'stop', stop

        if modifier not in ('begin', 'end', 'both', 'any', 'inc', '_date', None):
            msg = "The step must be 'begin', 'end', 'both', 'any', 'inc' or None not '{}'"
            raise ValueError(msg.format(modifier))

        def _begin(event):
            return ((start is None or (event.begin >= start)) and
                    (stop is None or (event.begin < stop)))

        def _end(event):
            return ((start is None or event.end > start) and
                    (stop is None or event.end <= stop))

        def _both(event):
            return ((start is None or event.begin >= start and event.end > start) and
                    (stop is None or event.begin < stop and event.end <= stop))

        def _any(event):
            return ((start is None or event.begin > start or event.end > start) and
                    (stop is None or event.begin < stop or event.end < stop))

        def _inc(event):
            return (start is not None and stop is not None and
                    event.begin > start and event.end < stop)

        def _date(event):
            # start is a date.
            # return only events on this day.
            return (event.begin.date() == start and
                    event.end.date() == start)

        routines = {'begin': _begin,
                    'end': _end,
                    'both': _both,
                    'any': _any,
                    '_date': _date,
                    'inc': _inc, }
        return list(filter(routines[modifier], self))

    def today(self, strict=False):
        """Args:
            strict (bool): if True events will be returned only if they are\
            strictly *included* in `day`.

        Returns:
            list<Event>: all events that occurs today
        """
        return self[utcnow()]

    def on(self, day, strict=False):
        """Args:
            day (Arrow-convertible)
            strict (bool): if True events will be returned only if they are\
            strictly *included* in `day`.

        Returns:
            list<Event>: all events that occurs on `day`
        """
        day = get_date_or_datetime(day)
        if hasattr(day, 'date'):
            day = day.date()
        return self[day]

    def now(self):
        """
        Returns:
            list<Event>: all events that occurs now
        """
        return [event for event in self
                if event.begin <= utcnow() <= event.end]

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
