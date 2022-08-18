from contextlib import contextmanager
from contextvars import ContextVar
from datetime import datetime, timedelta
from typing import Any, ClassVar, List, Optional, Tuple, Type, Union

import attr
from attr.converters import optional as c_optional
from attr.validators import in_, instance_of
from attr.validators import optional as v_optional

from ics.alarm import BaseAlarm
from ics.attendee import Attendee, Organizer
from ics.component import Component
from ics.geo import Geo, make_geo
from ics.timespan import EventTimespan, Timespan
from ics.timezone import UTC, ensure_utc, now_in_utc
from ics.types import (
    URL,
    DatetimeLike,
    EventOrTimespan,
    EventOrTimespanOrInstant,
    TimedeltaLike,
    get_timespan_if_calendar_entry,
)
from ics.utils import (
    check_is_instance,
    ensure_datetime,
    ensure_timedelta,
    uid_gen,
    validate_not_none,
)

STATUS_VALUES = (None, "TENTATIVE", "CONFIRMED", "CANCELLED")
default_uid_factory = ContextVar("ics.event.default_uid_factory", default=uid_gen)
default_dtstamp_factory = ContextVar(
    "ics.event.default_dtstamp_factory", default=now_in_utc
)


@contextmanager
def deterministic_event_data(
    uid="deterministic_uid@example.org",
    dtstamp=datetime(2000, 1, 1, 12, 0, 0, tzinfo=UTC),
):
    uid_token = default_uid_factory.set(lambda: uid)
    dtstamp_token = default_dtstamp_factory.set(lambda: dtstamp)
    try:
        yield
    finally:
        default_uid_factory.reset(uid_token)
        default_dtstamp_factory.reset(dtstamp_token)


@attr.s(eq=True, order=False)
class CalendarEntryAttrs(Component):
    timespan: Timespan = attr.ib()
    summary: Optional[str] = attr.ib(default=None)
    uid: str = attr.ib(factory=lambda: default_uid_factory.get()())

    description: Optional[str] = attr.ib(default=None)
    location: Optional[str] = attr.ib(default=None)
    url: Union[None, str, URL] = attr.ib(default=None)
    status: Optional[str] = attr.ib(default=None, converter=c_optional(str.upper), validator=in_(STATUS_VALUES))  # type: ignore[misc]

    created: Optional[datetime] = attr.ib(default=None, converter=ensure_utc)  # type: ignore[misc]
    last_modified: Optional[datetime] = attr.ib(default=None, converter=ensure_utc)  # type: ignore[misc]
    dtstamp: datetime = attr.ib(factory=lambda: default_dtstamp_factory.get()(), converter=ensure_utc, validator=validate_not_none)  # type: ignore[misc]

    alarms: List[BaseAlarm] = attr.ib(factory=list, converter=list)
    attach: List[Union[URL, bytes]] = attr.ib(factory=list, converter=list)

    # this is overridden by subclasses and then read by the Timespan converter to instantiate an object of the right subclass
    _TIMESPAN_TYPE: ClassVar[Type[Timespan]] = Timespan

    def __init_subclass__(cls):
        super().__init_subclass__()
        for cmp in ("__lt__", "__gt__", "__le__", "__ge__"):
            child_cmp, parent_cmp = getattr(cls, cmp), getattr(CalendarEntryAttrs, cmp)
            if child_cmp != parent_cmp:
                raise TypeError(f"{child_cmp} may not overwrite {parent_cmp}")

    @timespan.validator
    def validate_timespan(self, attr, value):
        check_is_instance(attr, value, self._TIMESPAN_TYPE)
        value.validate()

    ####################################################################################################################

    @property
    def begin(self) -> Optional[datetime]:
        """Get or set the beginning of the event.

        Will return a :class:`datetime` object.
        May be set to anything that :func:`datetime.__init__` understands.
        If an end is defined (not a duration), .begin must not
         be set to a superior value.
        For all-day events, the time is truncated to midnight when set.
        """
        return self.timespan.get_begin()

    @begin.setter
    def begin(self, value: DatetimeLike):
        self.timespan = self.timespan.replace(begin_time=ensure_datetime(value))

    @property
    def end(self) -> Optional[datetime]:
        """Get or set the end of the event.

        Will return a :class:`datetime` object.
        May be set to anything that :func:`datetime.__init__` understands.
        If set to a non null value, removes any already existing duration.
        Setting to None will have unexpected behavior if begin is not None.
        Must not be set to an inferior value than self.begin.
        When setting end time for for all-day events, if the end time
         is midnight, that day is not included.  Otherwise, the end is
         rounded up to midnight the next day, including the full day.
         Note that rounding is different from :func:`make_all_day`.
        """
        return self.timespan.get_effective_end()

    @end.setter
    def end(self, value: DatetimeLike):
        self.timespan = self.timespan.replace(
            end_time=ensure_datetime(value), duration=None
        )

    @property
    def duration(self) -> Optional[timedelta]:
        """Get or set the duration of the event.

        Will return a timedelta object.
        May be set to anything that timedelta() understands.
        May be set with a dict ({"days":2, "hours":6}).
        If set to a non null value, removes any already existing end time.
        Duration of an all-day event is rounded up to a full day.
        """
        return self.timespan.get_effective_duration()

    @duration.setter
    def duration(self, value: timedelta):
        self.timespan = self.timespan.replace(
            duration=ensure_timedelta(value), end_time=None
        )

    def convert_end(self, representation):
        self.timespan = self.timespan.convert_end(representation)

    @property
    def end_representation(self) -> Optional[str]:
        return self.timespan.get_end_representation()

    @property
    def has_explicit_end(self) -> bool:
        return self.timespan.has_explicit_end()

    @property
    def all_day(self) -> bool:
        return self.timespan.is_all_day()

    def make_all_day(self):
        """Transforms self to an all-day event or a time-based event.

        The event will span all the days from the begin to *and including*
         the end day.  For example, assume begin = 2018-01-01 10:37,
         end = 2018-01-02 14:44.  After make_all_day, begin = 2018-01-01
         [00:00], end = 2018-01-03 [00:00], and duration = 2 days.
        If duration is used instead of the end time, it is rounded up to an
         even day.  2 days remains 2 days, but 2 days and one second becomes 3 days.
        If neither duration not end are set, a duration of one day is implied.
        If self is already all-day, it is unchanged.
        """
        self.timespan = self.timespan.make_all_day()

    def unset_all_day(self):
        self.timespan = self.timespan.replace(precision="seconds")

    @property
    def floating(self) -> bool:
        return self.timespan.is_floating()

    def replace_timezone(self, tzinfo):
        self.timespan = self.timespan.replace_timezone(tzinfo)

    def convert_timezone(self, tzinfo):
        self.timespan = self.timespan.convert_timezone(tzinfo)

    def __str__(self) -> str:
        name = [self.__class__.__name__]
        if self.summary:
            name.append(f"'{self.summary}'")
        prefix, _, suffix = self.timespan.get_str_segments()
        return f"<{' '.join(prefix + name + suffix)}>"

    ####################################################################################################################

    def cmp_tuple(self) -> Tuple[datetime, datetime, str]:
        """Private helper method used for operator overloading.

        Returns a tuple with begin, end and summary of self.

        Implementation and usage details:
            https://github.com/ics-py/ics-py/blob/main/doc/event-cmp.rst#ordering
            https://icspy.readthedocs.io/en/main/event-cmp.html
        """
        return (*self.timespan.cmp_tuple(), self.summary or "")

    def __lt__(self, other: Any) -> bool:
        """self < other"""
        if isinstance(other, CalendarEntryAttrs):
            return self.cmp_tuple() < other.cmp_tuple()
        else:
            return NotImplemented

    def __gt__(self, other: Any) -> bool:
        """self > other"""
        if isinstance(other, CalendarEntryAttrs):
            return self.cmp_tuple() > other.cmp_tuple()
        else:
            return NotImplemented

    def __le__(self, other: Any) -> bool:
        """self <= other"""
        if isinstance(other, CalendarEntryAttrs):
            return self.cmp_tuple() <= other.cmp_tuple()
        else:
            return NotImplemented

    def __ge__(self, other: Any) -> bool:
        """self >= other"""
        if isinstance(other, CalendarEntryAttrs):
            return self.cmp_tuple() >= other.cmp_tuple()
        else:
            return NotImplemented

    def starts_within(self, second: EventOrTimespan) -> bool:
        return self.timespan.starts_within(get_timespan_if_calendar_entry(second))

    def ends_within(self, second: EventOrTimespan) -> bool:
        return self.timespan.ends_within(get_timespan_if_calendar_entry(second))

    def intersects(self, second: EventOrTimespan) -> bool:
        return self.timespan.intersects(get_timespan_if_calendar_entry(second))

    def includes(self, second: EventOrTimespanOrInstant) -> bool:
        return self.timespan.includes(get_timespan_if_calendar_entry(second))

    def is_included_in(self, second: EventOrTimespan) -> bool:
        return self.timespan.is_included_in(get_timespan_if_calendar_entry(second))


@attr.s(eq=True, order=False)  # order methods are provided by CalendarEntryAttrs
class EventAttrs(CalendarEntryAttrs):
    classification: Optional[str] = attr.ib(
        default=None, validator=v_optional(instance_of(str))
    )

    transparent: Optional[bool] = attr.ib(default=None)
    organizer: Optional[Organizer] = attr.ib(
        default=None, validator=v_optional(instance_of(Organizer))
    )
    geo: Optional[Geo] = attr.ib(default=None, converter=make_geo)

    attendees: List[Attendee] = attr.ib(
        factory=list, converter=list, metadata={"ics_name": "ATTENDEE"}
    )
    categories: List[str] = attr.ib(factory=list, converter=list)

    def add_attendee(self, attendee: Attendee):
        """Add an attendee to the attendees set"""
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

    NAME = "VEVENT"
    _TIMESPAN_TYPE: ClassVar[Type[Timespan]] = EventTimespan

    def __init__(
        self,
        summary: str = None,
        begin: DatetimeLike = None,
        end: DatetimeLike = None,
        duration: TimedeltaLike = None,
        *args,
        **kwargs,
    ):
        """Initializes a new :class:`ics.event.Event`.

        Raises:
            ValueError: if `timespan` and any of `begin`, `end` or `duration`
             are specified at the same time,
             or if validation of the timespan fails (see :method:`ics.timespan.Timespan.validate`).
        """
        if (
            begin is not None or end is not None or duration is not None
        ) and "timespan" in kwargs:
            raise ValueError(
                "can't specify explicit timespan together with any of begin, end or duration"
            )
        kwargs.setdefault(
            "timespan",
            EventTimespan(
                ensure_datetime(begin), ensure_datetime(end), ensure_timedelta(duration)
            ),
        )
        super().__init__(kwargs.pop("timespan"), summary, *args, **kwargs)
