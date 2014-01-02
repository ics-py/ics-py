#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals, absolute_import

from six import PY2, PY3, StringIO, string_types, text_type, integer_types
from six.moves import filter, map, range

from arrow.arrow import Arrow
import arrow

from .utils import get_arrow


class EventList(list):

    """EventList is a subclass of the standard list.

    It can be used as a list but also has super slicing capabilities
    and some helpers.
    """

    def __init__(self, *args, **kwargs):
        """Instanciates a new EventList.

        Accepts same arguments as list() and pass them all to list().
        """
        super(EventList, self).__init__(*args, **kwargs)

    def __getitem__(self, sl):
        """Slices EventList.
        |  If sl is conventional (like [10], [4:12], [3:100:2], [::-1], …),
            it slices the EventList like a classical list().
        |  If one of the 3 arguments ([start:stop:step]) is not None or an int,
            slicing differs.

        |  In that case, `start` and `stop` are considerated like instants
            (or None) and `step` like a modificator.
        |  `start` and `stop` will be converted to Arrow objects (or None)
            with arrow.get().

        - start (arrow.get() compatible or Arrow or None): \
        lower included bond,
        - stop (arrow.get() compatible or Arrow or None): \
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
        elif not sl.step in ('begin', 'end', 'both', 'any', 'inc'):
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
        """Returns all events that occurs today.

        If `strict` is True, events will be returned only if they are
        strictly *included* in today.
        """
        return self[arrow.now()]

    def on(self, day, strict=False):
        """Returns all events that occurs on `day`.

        |  If `strict` is True, events will be returned only if they are
            strictly *included* in `day`.
        |  `day` will be parsed by arrow.get() if it's not
            an Arrow object.
        """
        if not isinstance(day, Arrow):
            day = arrow.get(day)
        return self[day]

    def now(self):
        """Returns all events that occurs now."""
        return self[arrow.now():arrow.now().ceil('microsecond')]

    def at(self, instant):
        """Returns all events that are occuring at that instant.

        `instant` will be parsed by arrow.get() if it's not an Arrow object.
        """
        if not isinstance(instant, Arrow):
            instant = arrow.get(instant)
        return self[instant:instant.ceil('microsecond'):'one']

    def concurrent(self, event):
        """Returns all events that are overlapping `event`."""
        a = self[event.begin:event.start:'any']
        b = self[None:event.begin:'start']
        c = self[event.end:None:'stop']
        return list(set(a) | (set(b) & set(c)))

    def _remove_duplicates(self):
        seen = set()
        for i in reversed(range(len(self))):
            if self[i] in seen:
                del self[i]
            else:
                seen.add(self[i])

    def __add__(self, *args, **kwargs):
        ret = super(EventList, self).__add__(*args, **kwargs)
        ret = EventList(ret)
        ret._remove_duplicates()
        return ret
