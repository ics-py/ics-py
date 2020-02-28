from datetime import datetime, timedelta
from typing import Dict, List, NamedTuple, Optional, Set, Tuple, Union

import attr

from ics.alarm.base import BaseAlarm
from ics.attendee import Attendee, Organizer
from ics.component import Component
from ics.parsers.event_parser import EventParser
from ics.serializers.event_serializer import EventSerializer
from ics.timespan import Timespan
from ics.types import DatetimeLike, EventOrTimespan, EventOrTimespanOrInstant, get_timespan_if_event
from ics.utils import check_is_instance, ensure_datetime, uid_gen

STATUS_ATTRIB = dict(
    converter=lambda s: s.upper(),
    validator=attr.validators.in_((None, 'TENTATIVE', 'CONFIRMED', 'CANCELLED')))


class Geo(NamedTuple):
    latitude: float
    longitude: float

    @classmethod
    def make(cls, value: Union[Dict[str, float], Tuple[float, float], None]):
        if isinstance(value, dict):
            return Geo(**value)
        elif isinstance(value, tuple):
            return Geo(*value)
        else:
            return None


@attr.s
class CalendarEntryAttrs(Component):
    _timespan: Timespan = attr.ib(validator=attr.validators.instance_of(Timespan))
    name: Optional[str] = attr.ib(default=None)
    uid: str = attr.ib(factory=uid_gen)

    description: Optional[str] = attr.ib(default=None)
    location: Optional[str] = attr.ib(default=None)
    url: Optional[str] = attr.ib(default=None)
    status: Optional[str] = attr.ib(default=None, **STATUS_ATTRIB)

    created: Optional[DatetimeLike] = attr.ib(factory=datetime.now, converter=ensure_datetime)
    last_modified: Optional[DatetimeLike] = attr.ib(factory=datetime.now, converter=ensure_datetime)
    # self.dtstamp = datetime.utcnow() if not dtstamp else ensure_datetime(dtstamp) # ToDo
    alarms: List[BaseAlarm] = attr.ib(factory=list, converter=list)


@attr.s
class EventsAttrs(CalendarEntryAttrs):
    classification: Optional[str] = attr.ib(default=None)

    transparent: Optional[bool] = attr.ib(default=None)
    organizer: Optional[Organizer] = attr.ib(default=None, validator=attr.validators.instance_of(Organizer))
    geo: Optional[Geo] = attr.ib(converter=Geo.make, default=None)

    attendees: Set[Attendee] = attr.ib(factory=set, converter=set)
    categories: Set[str] = attr.ib(factory=set, converter=set)

    def add_attendee(self, attendee: Attendee):
        """ Add an attendee to the attendees set """
        check_is_instance("attendee", attendee, Attendee)
        self.attendees.add(attendee)


class Event(EventsAttrs):
    """A calendar event.

    Can be full-day or between two instants.
    Can be defined by a beginning instant and
    a duration *or* end instant.

    Unsupported event attributes can be found in `event.extra`,
    a :class:`ics.parse.Container`. You may add some by appending a
    :class:`ics.parse.ContentLine` to `.extra`
    """

    class Meta:
        name = "VEVENT"
        parser = EventParser
        serializer = EventSerializer

    def __init__(
            self,
            name: str = None,
            begin: DatetimeLike = None,
            end: DatetimeLike = None,
            duration: timedelta = None,
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
        super(Event, self).__init__(Timespan(begin, end, duration), name, *args, **kwargs)

    ####################################################################################################################

    @property
    def begin(self) -> datetime:
        """Get or set the beginning of the event.

        |  Will return a :class:`datetime` object.
        |  May be set to anything that :func:`datetime.__init__` understands.
        |  If an end is defined (not a duration), .begin must not
            be set to a superior value.
        """
        return self._timespan.get_begin()

    @begin.setter
    def begin(self, value: DatetimeLike):
        self._timespan = self._timespan.replace(begin_time=ensure_datetime(value))

    @property
    def end(self) -> datetime:
        """Get or set the end of the event.

        |  Will return a :class:`datetime` object.
        |  May be set to anything that :func:`datetime.__init__` understands.
        |  If set to a non null value, removes any already
            existing duration.
        |  Setting to None will have unexpected behavior if
            begin is not None.
        |  Must not be set to an inferior value than self.begin.
        """
        return self._timespan.get_effective_end()

    @end.setter
    def end(self, value: DatetimeLike):
        self._timespan = self._timespan.replace(end_time=ensure_datetime(value))

    @property
    def duration(self) -> Optional[timedelta]:
        """Get or set the duration of the event.

        |  Will return a timedelta object.
        |  May be set to anything that timedelta() understands.
        |  May be set with a dict ({"days":2, "hours":6}).
        |  If set to a non null value, removes any already
            existing end time.
        """
        return self._timespan.get_effective_duration()

    @duration.setter
    def duration(self, value: timedelta):
        self._timespan = self._timespan.replace(duration=value)

    def convert_end(self, representation):
        self._timespan = self._timespan.convert_end(representation)

    @property
    def end_representation(self):
        return self._timespan.get_end_representation()

    @property
    def has_end(self) -> bool:
        return self._timespan.has_end()

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
        name = [self.__class__.__name__, "'%s'" % (self.name or "",)]
        prefix, _, suffix = self._timespan.get_str_segments()
        return "<%s>" % (" ".join(prefix + name + suffix))

    ####################################################################################################################

    # TODO allow use with same parameters as Timeline.normalize_timespan

    def starts_within(self, second: EventOrTimespan) -> bool:
        return self._timespan.starts_within(get_timespan_if_event(second))

    def ends_within(self, second: EventOrTimespan) -> bool:
        return self._timespan.ends_within(get_timespan_if_event(second))

    def intersects(self, second: EventOrTimespan) -> bool:
        return self._timespan.intersects(get_timespan_if_event(second))

    def includes(self, second: EventOrTimespanOrInstant) -> bool:
        return self._timespan.includes(get_timespan_if_event(second))

    def is_included_in(self, second: EventOrTimespan) -> bool:
        return self._timespan.is_included_in(get_timespan_if_event(second))

    def compare(self, extract_dt, op, second: EventOrTimespanOrInstant) -> bool:
        return self._timespan.compare(extract_dt, op, get_timespan_if_event(second))

    def __lt__(self, second: EventOrTimespanOrInstant) -> bool:
        return self._timespan.__lt__(get_timespan_if_event(second))

    def __le__(self, second: EventOrTimespanOrInstant) -> bool:
        return self._timespan.__le__(get_timespan_if_event(second))

    def __gt__(self, second: EventOrTimespanOrInstant) -> bool:
        return self._timespan.__gt__(get_timespan_if_event(second))

    def __ge__(self, second: EventOrTimespanOrInstant) -> bool:
        return self._timespan.__ge__(get_timespan_if_event(second))

    def same_timespan(self, second: EventOrTimespan) -> bool:
        return self._timespan.same_timespan(get_timespan_if_event(second))

    def union_timespan(self, second: EventOrTimespanOrInstant):
        self._timespan = self._timespan.union(get_timespan_if_event(second))
