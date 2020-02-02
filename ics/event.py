import copy
from datetime import datetime, timedelta
from typing import (Dict, Iterable, List, NamedTuple, Optional, Set,
                    Tuple, Union)

from arrow import Arrow

from ics.grammar.parse import Container
from ics.parsers.event_parser import EventParser
from ics.serializers.event_serializer import EventSerializer
from .alarm.base import BaseAlarm
from .attendee import Attendee
from .component import Component
from .organizer import Organizer
from .timespan import Timespan
from .types import ArrowLike
from .utils import (get_arrow, uid_gen)


class Geo(NamedTuple):
    latitude: float
    longitude: float


EventOrTimespan = Union["Event", Timespan]
EventOrTimespanOrInstant = Union["Event", Timespan, datetime]


def get_timespan_if_event(value):
    if isinstance(value, Event):
        return value._timespan
    else:
        return value


class Event(Component):
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

    def __init__(self,
                 name: str = None,
                 begin: ArrowLike = None,
                 end: ArrowLike = None,
                 duration: timedelta = None,
                 uid: str = None,
                 description: str = None,
                 created: ArrowLike = None,
                 last_modified: ArrowLike = None,
                 location: str = None,
                 url: str = None,
                 transparent: bool = None,
                 alarms: Iterable[BaseAlarm] = None,
                 attendees: Iterable[Attendee] = None,
                 categories: Iterable[str] = None,
                 status: str = None,
                 organizer: Organizer = None,
                 geo=None,
                 classification: str = None,
                 ) -> None:
        """Instantiates a new :class:`ics.event.Event`.

        Args:
            name: rfc5545 SUMMARY property
            begin (Arrow-compatible)
            end (Arrow-compatible)
            duration
            uid: must be unique
            description
            created (Arrow-compatible)
            last_modified (Arrow-compatible)
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

        self._timespan: Timespan = Timespan(begin, end, duration)
        self._status: Optional[str] = None
        self._classification: Optional[str] = None

        self.organizer: Optional[str] = None
        self.uid: str = uid_gen() if not uid else uid
        self.description: Optional[str] = description
        self.created: Optional[ArrowLike] = get_arrow(created)
        self.last_modified: Optional[ArrowLike] = get_arrow(last_modified)
        self.location: Optional[str] = location
        self.url: Optional[str] = url
        self.transparent: Optional[bool] = transparent
        self.alarms: List[BaseAlarm] = list()
        self.attendees: Set[Attendee] = set()
        self.categories: Set[str] = set()
        self.geo = geo
        self.extra = Container(name='VEVENT')

        self.name = name

        if alarms is not None:
            self.alarms = list(alarms)
        self.status = status
        self.classification = classification

        if categories is not None:
            self.categories.update(set(categories))

        if attendees is not None:
            self.attendees.update(set(attendees))

    def clone(self):
        """
        Returns:
            Event: an exact copy of self"""
        clone = copy.copy(self)
        clone.extra = clone.extra.clone()
        clone.alarms = copy.copy(self.alarms)
        clone.categories = copy.copy(self.categories)
        # don't need to copy timespan as it is immutable
        return clone

    ####################################################################################################################

    @property
    def begin(self) -> datetime:
        """Get or set the beginning of the event.

        |  Will return an :class:`Arrow` object.
        |  May be set to anything that :func:`Arrow.get` understands.
        |  If an end is defined (not a duration), .begin must not
            be set to a superior value.
        |  For all-day events, the time is truncated to midnight when set.
        """
        return self._timespan.get_begin()

    @begin.setter
    def begin(self, value: ArrowLike):
        if isinstance(value, Arrow):
            value = value.datetime
        self._timespan = self._timespan.replace(begin_time=value)

    @property
    def end(self) -> datetime:
        """Get or set the end of the event.

        |  Will return an :class:`Arrow` object.
        |  May be set to anything that :func:`Arrow.get` understands.
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
    def end(self, value: ArrowLike):
        if isinstance(value, Arrow):
            value = value.datetime
        self._timespan = self._timespan.replace(end_time=value)

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

    ####################################################################################################################

    @property
    def status(self) -> Optional[str]:
        return self._status

    @status.setter
    def status(self, value: Optional[str]):
        if isinstance(value, str):
            value = value.upper()
        statuses = (None, 'TENTATIVE', 'CONFIRMED', 'CANCELLED')
        if value not in statuses:
            raise ValueError('status must be one of %s' % ", ".join([repr(x) for x in statuses]))
        self._status = value

    @property
    def classification(self):
        return self._classification

    @classification.setter
    def classification(self, value):
        if value is not None:
            if not isinstance(value, str):
                raise ValueError('classification must be a str')
            self._classification = value
        else:
            self._classification = None

    @property
    def geo(self) -> Optional[Geo]:
        """Get or set the geo position of the event.

        |  Will return a namedtuple object.
        |  May be set to any Geo, tuple or dict with latitude and longitude keys.
        |  If set to a non null value, removes any already
            existing geo.
        """
        return self._geo

    @geo.setter
    def geo(self, value: Union[Dict[str, float], Tuple[float, float], Geo, None]):
        if isinstance(value, dict):
            latitude, longitude = value['latitude'], value['longitude']
            value = Geo(latitude, longitude)
        elif value is not None:
            latitude, longitude = value
            value = Geo(latitude, longitude)
        self._geo = value

    def add_attendee(self, attendee: Attendee):
        """ Add an attendee to the attendees set
        """
        self.attendees.add(attendee)

    ####################################################################################################################

    def __repr__(self) -> str:
        name = [self.__class__.__name__, "'%s'" % (self.name or "",)]
        prefix, _, suffix = self._timespan.get_str_segments()
        return "<%s>" % (" ".join(prefix + name + suffix))

    def __hash__(self) -> int:
        """
        Returns:
            int: hash of self. Based on self.uid."""
        return hash(self.uid)

    ####################################################################################################################

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

    def __eq__(self, o: object) -> bool:
        return self.__class__ == o.__class__ and self.__dict__ == o.__dict__

    def same_timespan(self, second: EventOrTimespan) -> bool:
        return self._timespan.same_timespan(get_timespan_if_event(second))

    def union_timespan(self, second: EventOrTimespanOrInstant):
        self._timespan = self._timespan.union(get_timespan_if_event(second))
