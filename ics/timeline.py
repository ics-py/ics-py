import heapq
from datetime import date, datetime, timedelta
from typing import Iterable, Iterator, TYPE_CHECKING, Tuple

import attr

from ics.event import Event
from ics.timespan import Normalization, Timespan, normalize
from ics.types import DatetimeLike, OptionalDatetimeLike, TimespanOrBegin
from ics.utils import ceil_datetime_to_midnight, ensure_datetime

if TYPE_CHECKING:
    from ics.icalendar import Calendar


@attr.s
class Timeline(object):
    """
    `Timeline`s allow iterating all event from a `Calendar` in chronological order, optionally also filtering events
    according to their timestamps.
    See the documentation of :func:`ics.timespan.normalize` for details on normalization methods to make datetimes
    with and without timezone comparable.
    """

    _calendar: "Calendar" = attr.ib()
    _normalization: Normalization = attr.ib()

    def normalize_datetime(self, instant: DatetimeLike) -> datetime:
        """
        Create a normalized datetime instance for the given instance.
        """
        return normalize(instant, self._normalization)

    def normalize_timespan(self, start: TimespanOrBegin, stop: OptionalDatetimeLike = None) -> Timespan:
        """
        Create a normalized timespan between `start` and `stop`.
        Alternatively, this method can be called directly with a single timespan as parameter.
        """
        if isinstance(start, Timespan):
            if stop is not None:
                raise ValueError("can't specify a Timespan and an additional stop time")
            timespan = start
        else:
            timespan = Timespan(ensure_datetime(start), ensure_datetime(stop))
        return timespan.normalize(self._normalization)

    def iterator(self) -> Iterator[Tuple[Timespan, Event]]:
        """
        Iterates on every event from the :class:`ics.icalendar.Calendar` in chronological order

        Note:
            - chronological order is defined by the comparison operators in :class:`ics.timespan.Timespan`
            - Events with no `begin` will not appear here. (To list all events in a `Calendar` use `Calendar.events`)
        """
        # Using a heap is faster than sorting if the number of events (n) is
        # much bigger than the number of events we extract from the iterator (k).
        # Complexity: O(n + k log n).
        heap: Iterable[Tuple[Timespan, Event]] = (
            (e.timespan.normalize(self._normalization), e)
            for e in self._calendar.events)
        heap = [t for t in heap if t[0]]
        heapq.heapify(heap)
        while heap:
            yield heapq.heappop(heap)

    def __iter__(self) -> Iterator[Event]:
        """
        Iterates on every event from the :class:`ics.icalendar.Calendar` in chronological order

        Note:
            - chronological order is defined by the comparison operators in :class:`ics.timespan.Timespan`
            - Events with no `begin` will not appear here. (To list all events in a `Calendar` use `Calendar.events`)
        """
        for _, e in self.iterator():
            yield e

    def included(self, start: TimespanOrBegin, stop: OptionalDatetimeLike = None) -> Iterator[Event]:
        """
        Iterates (in chronological order) over every event that is included in the timespan between `start` and `stop`.
        Alternatively, this method can be called directly with a single timespan as parameter.
        """
        query = self.normalize_timespan(start, stop)
        for timespan, event in self.iterator():
            if timespan.is_included_in(query):
                yield event

    def overlapping(self, start: TimespanOrBegin, stop: OptionalDatetimeLike = None) -> Iterator[Event]:
        """
        Iterates (in chronological order) over every event that has an intersection with the timespan between `start` and `stop`.
        Alternatively, this method can be called directly with a single timespan as parameter.
        """
        query = self.normalize_timespan(start, stop)
        for timespan, event in self.iterator():
            if timespan.intersects(query):
                yield event

    def start_after(self, instant: DatetimeLike) -> Iterator[Event]:
        """
        Iterates (in chronological order) on every event from the :class:`ics.icalendar.Calendar` in chronological order.
        The first event of the iteration has a starting date greater (later) than `instant`.
        """
        instant = self.normalize_datetime(instant)
        for timespan, event in self.iterator():
            if timespan.begin_time is not None and timespan.begin_time > instant:
                yield event

    def at(self, instant: DatetimeLike) -> Iterator[Event]:
        """
        Iterates (in chronological order) over all events that are occuring during `instant`.
        """
        instant = self.normalize_datetime(instant)
        for timespan, event in self.iterator():
            if timespan.includes(instant):
                yield event

    def on(self, instant: DatetimeLike, strict: bool = False) -> Iterator[Event]:
        """
        Iterates (in chronological order) over all events that occurs on `day`.

        :param strict: if True events will be returned only if they are strictly *included* in `day`
        """
        query = self.normalize_timespan(instant, ceil_datetime_to_midnight(instant) - timedelta.min)
        if strict:
            return self.included(query)
        else:
            return self.overlapping(query)

    def today(self, strict: bool = False) -> Iterator[Event]:
        """
        Iterates (in chronological order) over all events that occurs today.

        :param strict: if True events will be returned only if they are strictly *included* in `day`
        """
        return self.on(date.today(), strict=strict)

    def now(self) -> Iterator[Event]:
        """
        Iterates (in chronological order) over all events that occur right now.
        """
        return self.at(datetime.utcnow())
