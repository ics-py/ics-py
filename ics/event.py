from datetime import datetime, timedelta
from typing import Any, Dict, List, NamedTuple, Optional, Set, Tuple, Union, overload

import attr
from attr.converters import optional as c_optional
from attr.validators import in_, instance_of, optional as v_optional

from ics.alarm.base import BaseAlarm
from ics.attendee import Attendee, Organizer
from ics.component import Component
from ics.parsers.event_parser import EventParser
from ics.serializers.event_serializer import EventSerializer
from ics.timespan import EventTimespan, Timespan
from ics.types import DatetimeLike, EventOrTimespan, EventOrTimespanOrInstant, TimedeltaLike, get_timespan_if_calendar_entry
from ics.utils import check_is_instance, ensure_datetime, ensure_timedelta, uid_gen, validate_not_none

STATUS_VALUES = (None, 'TENTATIVE', 'CONFIRMED', 'CANCELLED')


class Geo(NamedTuple):
    latitude: float
    longitude: float


@overload
def make_geo(value: None) -> None:
    ...


@overload
def make_geo(value: Union[Dict[str, float], Tuple[float, float]]) -> "Geo":
    ...


def make_geo(value):
    if isinstance(value, dict):
        return Geo(**value)
    elif isinstance(value, tuple):
        return Geo(*value)
    else:
        return None


@attr.s(repr=False, eq=True, order=False)
class CalendarEntryAttrs(Component):
    _timespan: Timespan = attr.ib(validator=instance_of(Timespan))
    name: Optional[str] = attr.ib(default=None)
    uid: str = attr.ib(factory=uid_gen)

    description: Optional[str] = attr.ib(default=None)
    location: Optional[str] = attr.ib(default=None)
    url: Optional[str] = attr.ib(default=None)
    status: Optional[str] = attr.ib(default=None, converter=c_optional(str.upper), validator=v_optional(in_(STATUS_VALUES)))  # type: ignore

    # TODO these three timestamps must be in UTC according to the RFC
    created: Optional[datetime] = attr.ib(default=None, converter=ensure_datetime)  # type: ignore
    last_modified: Optional[datetime] = attr.ib(default=None, converter=ensure_datetime)  # type: ignore
    dtstamp: datetime = attr.ib(factory=datetime.now, converter=ensure_datetime, validator=validate_not_none)  # type: ignore

    alarms: List[BaseAlarm] = attr.ib(factory=list, converter=list)

    def __init_subclass__(cls):
        super().__init_subclass__()
        for cmp in ("__lt__", "__gt__", "__le__", "__ge__"):
            child_cmp, parent_cmp = getattr(cls, cmp), getattr(CalendarEntryAttrs, cmp)
            if child_cmp != parent_cmp:
                raise TypeError("%s may not overwrite %s" % (child_cmp, parent_cmp))

    ####################################################################################################################

    @property
    def begin(self) -> Optional[datetime]:
        """Get or set the beginning of the event.

        |  Will return a :class:`datetime` object.
        |  May be set to anything that :func:`datetime.__init__` understands.
        |  If an end is defined (not a duration), .begin must not
            be set to a superior value.
        |  For all-day events, the time is truncated to midnight when set.
        """
        return self._timespan.get_begin()

    @begin.setter
    def begin(self, value: DatetimeLike):
        self._timespan = self._timespan.replace(begin_time=ensure_datetime(value))

    @property
    def end(self) -> Optional[datetime]:
        """Get or set the end of the event.

        |  Will return a :class:`datetime` object.
        |  May be set to anything that :func:`datetime.__init__` understands.
        |  If set to a non null value, removes any already
            existing duration.
        |  Setting to None will have unexpected behavior if
            begin is not None.
        |  Must not be set to an inferior value than self.begin.
        |  When setting end time for for all-day events, if the end time
            is midnight, that day is not included.  Otherwise, the end is
            rounded up to midnight the next day, including the full day.
            Note that rounding is different from :func:`make_all_day`.
        """
        return self._timespan.get_effective_end()

    @end.setter
    def end(self, value: DatetimeLike):
        self._timespan = self._timespan.replace(end_time=ensure_datetime(value), duration=None)

    @property
    def duration(self) -> Optional[timedelta]:
        """Get or set the duration of the event.

        |  Will return a timedelta object.
        |  May be set to anything that timedelta() understands.
        |  May be set with a dict ({"days":2, "hours":6}).
        |  If set to a non null value, removes any already
            existing end time.
        |  Duration of an all-day event is rounded up to a full day.
        """
        return self._timespan.get_effective_duration()

    @duration.setter
    def duration(self, value: timedelta):
        self._timespan = self._timespan.replace(duration=ensure_timedelta(value), end_time=None)

    def convert_end(self, representation):
        self._timespan = self._timespan.convert_end(representation)

    @property
    def end_representation(self):
        return self._timespan.get_end_representation()

    @property
    def has_explicit_end(self) -> bool:
        return self._timespan.has_explicit_end()

    @property
    def all_day(self):
        return self._timespan.is_all_day()

    def make_all_day(self):
        """Transforms self to an all-day event or a time-based event.

        |  The event will span all the days from the begin to *and including*
            the end day.  For example, assume begin = 2018-01-01 10:37,
            end = 2018-01-02 14:44.  After make_all_day, begin = 2018-01-01
            [00:00], end = 2018-01-03 [00:00], and duration = 2 days.
        |  If duration is used instead of the end time, it is rounded up to an
            even day.  2 days remains 2 days, but 2 days and one second becomes 3 days.
        |  If neither duration not end are set, a duration of one day is implied.
        |  If self is already all-day, it is unchanged.
        """
        self._timespan = self._timespan.make_all_day()

    def unset_all_day(self):
        self._timespan = self._timespan.replace(precision="seconds")

    @property
    def floating(self):
        return self._timespan.is_floating()

    def replace_timezone(self, tzinfo):
        self._timespan = self._timespan.replace_timezone(tzinfo)

    def convert_timezone(self, tzinfo):
        self._timespan = self._timespan.convert_timezone(tzinfo)

    @property
    def timespan(self) -> Timespan:
        return self._timespan

    def __repr__(self) -> str:
        name = [self.__class__.__name__]
        if self.name:
            name.append("'%s'" % self.name)
        prefix, _, suffix = self._timespan.get_str_segments()
        return "<%s>" % (" ".join(prefix + name + suffix))

    ####################################################################################################################

    def cmp_tuple(self):
        return (*self.timespan.cmp_tuple(), self.name or "")

    def __lt__(self, other: Any) -> bool:
        if isinstance(other, CalendarEntryAttrs):
            return self.cmp_tuple() < other.cmp_tuple()
        else:
            return NotImplemented

    def __gt__(self, other: Any) -> bool:
        if isinstance(other, CalendarEntryAttrs):
            return self.cmp_tuple() > other.cmp_tuple()
        else:
            return NotImplemented

    def __le__(self, other: Any) -> bool:
        if isinstance(other, CalendarEntryAttrs):
            return self.cmp_tuple() <= other.cmp_tuple()
        else:
            return NotImplemented

    def __ge__(self, other: Any) -> bool:
        if isinstance(other, CalendarEntryAttrs):
            return self.cmp_tuple() >= other.cmp_tuple()
        else:
            return NotImplemented

    def starts_within(self, second: EventOrTimespan) -> bool:
        return self._timespan.starts_within(get_timespan_if_calendar_entry(second))

    def ends_within(self, second: EventOrTimespan) -> bool:
        return self._timespan.ends_within(get_timespan_if_calendar_entry(second))

    def intersects(self, second: EventOrTimespan) -> bool:
        return self._timespan.intersects(get_timespan_if_calendar_entry(second))

    def includes(self, second: EventOrTimespanOrInstant) -> bool:
        return self._timespan.includes(get_timespan_if_calendar_entry(second))

    def is_included_in(self, second: EventOrTimespan) -> bool:
        return self._timespan.is_included_in(get_timespan_if_calendar_entry(second))


@attr.s(repr=False, eq=True, order=False)  # order methods are provided by CalendarEntryAttrs
class EventAttrs(CalendarEntryAttrs):
    classification: Optional[str] = attr.ib(default=None, validator=v_optional(instance_of(str)))

    transparent: Optional[bool] = attr.ib(default=None)
    organizer: Optional[Organizer] = attr.ib(default=None, validator=v_optional(instance_of(Organizer)))
    geo: Optional[Geo] = attr.ib(default=None, converter=make_geo)  # type: ignore

    attendees: List[Attendee] = attr.ib(factory=list, converter=list)
    categories: Set[str] = attr.ib(factory=set, converter=set)

    def add_attendee(self, attendee: Attendee):
        """ Add an attendee to the attendees set """
        check_is_instance("attendee", attendee, Attendee)
        self.attendees.append(attendee)


class Event(EventAttrs):
    """A calendar event.

    Can be full-day or between two instants.
    Can be defined by a beginning instant and
    a duration *or* end instant.

    Unsupported event attributes can be found in `event.extra`,
    a :class:`ics.parse.Container`. You may add some by appending a
    :class:`ics.parse.ContentLine` to `.extra`
    """

    _timespan: EventTimespan = attr.ib(validator=instance_of(EventTimespan))

    class Meta:
        name = "VEVENT"
        parser = EventParser
        serializer = EventSerializer

    def __init__(
            self,
            name: str = None,
            begin: DatetimeLike = None,
            end: DatetimeLike = None,
            duration: TimedeltaLike = None,
            *args, **kwargs
    ):
        """Instantiates a new :class:`ics.event.Event`.

        Args:
            name: rfc5545 SUMMARY property
            begin (datetime)
            end (datetime)
            duration
            uid: must be unique
            description
            created (datetime)
            last_modified (datetime)
            location
            url
            transparent
            alarms
            attendees
            categories
            status
            organizer
            classification

        Raises:
            ValueError: if `end` and `duration` are specified at the same time
        """
        if (begin is not None or end is not None or duration is not None) and "timespan" in kwargs:
            raise ValueError("can't specify explicit timespan together with any of begin, end or duration")
        kwargs.setdefault("timespan", EventTimespan(ensure_datetime(begin), ensure_datetime(end), ensure_timedelta(duration)))
        super(Event, self).__init__(kwargs.pop("timespan"), name, *args, **kwargs)
