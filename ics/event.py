import copy
from datetime import datetime, timedelta
from typing import (Dict, Iterable, List, NamedTuple, Optional, Set,
                    Tuple, Union)

from arrow import Arrow

from .alarm.base import BaseAlarm
from .attendee import Attendee, Organizer
from .component import Component
from ics.grammar.parse import Container
from .types import ArrowLike
from .utils import (get_arrow, uid_gen)
from ics.parsers.event_parser import EventParser
from ics.serializers.event_serializer import EventSerializer


class Geo(NamedTuple):
    latitude: float
    longitude: float


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

        self._duration: Optional[timedelta] = None
        self._end_time: Optional[ArrowLike] = None
        self._begin: Optional[ArrowLike] = None
        self._begin_precision = None
        self._status: Optional[str] = None
        self._classification: Optional[str] = None

        self.organizer: Optional[Organizer] = organizer
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
        self.begin = begin

        if duration and end:
            raise ValueError(
                'Event() may not specify an end and a duration \
                at the same time')
        elif end:  # End was specified
            self.end = end
        elif duration:  # Duration was specified
            self.duration = duration

        if alarms is not None:
            self.alarms = list(alarms)
        self.status = status
        self.classification = classification

        if categories is not None:
            self.categories.update(set(categories))

        if attendees is not None:
            self.attendees.update(set(attendees))

    def has_end(self) -> bool:
        """
        Return:
            bool: self has an end
        """
        return bool(self._end_time or self._duration)

    def add_attendee(self, attendee: Attendee):
        """ Add an attendee to the attendees set
        """
        self.attendees.add(attendee)

    @property
    def begin(self) -> Arrow:
        """Get or set the beginning of the event.

        |  Will return an :class:`Arrow` object.
        |  May be set to anything that :func:`Arrow.get` understands.
        |  If an end is defined (not a duration), .begin must not
            be set to a superior value.
        """
        return self._begin

    @begin.setter
    def begin(self, value: ArrowLike):
        value = get_arrow(value)
        if value and self._end_time and value > self._end_time:
            raise ValueError('Begin must be before end')
        self._begin = value
        self._begin_precision = 'second'

    @property
    def end(self) -> Arrow:
        """Get or set the end of the event.

        |  Will return an :class:`Arrow` object.
        |  May be set to anything that :func:`Arrow.get` understands.
        |  If set to a non null value, removes any already
            existing duration.
        |  Setting to None will have unexpected behavior if
            begin is not None.
        |  Must not be set to an inferior value than self.begin.
        """

        if self._duration:  # if end is duration defined
            # return the beginning + duration
            return self.begin + self._duration
        elif self._end_time:  # if end is time defined
            if self.all_day:
                return self._end_time
            else:
                return self._end_time
        elif self._begin:  # if end is not defined
            if self.all_day:
                return self._begin + timedelta(days=1)
            else:
                # instant event
                return self._begin
        else:
            return None

    @end.setter
    def end(self, value: ArrowLike):
        value = get_arrow(value)
        if value and self._begin and value < self._begin:
            raise ValueError('End must be after begin')

        self._end_time = value
        if value:
            self._duration = None

    @property
    def duration(self) -> Optional[timedelta]:
        """Get or set the duration of the event.

        |  Will return a timedelta object.
        |  May be set to anything that timedelta() understands.
        |  May be set with a dict ({"days":2, "hours":6}).
        |  If set to a non null value, removes any already
            existing end time.
        """
        if self._duration:
            return self._duration
        elif self.end:
            # because of the clever getter for end, this also takes care of all_day events
            return self.end - self.begin
        else:
            # event has neither start, nor end, nor duration
            return None

    @duration.setter
    def duration(self, value: timedelta):
        if isinstance(value, dict):
            value = timedelta(**value)
        elif isinstance(value, timedelta):
            value = value
        elif value is not None:
            value = timedelta(value)

        if value:
            self._end_time = None

        self._duration = value

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

    @property
    def all_day(self):
        """
        Return:
            bool: self is an all-day event
        """
        # the event may have an end, also given in 'day' precision
        return self._begin_precision == 'day'

    def make_all_day(self) -> None:
        """Transforms self to an all-day event.

        The event will span all the days from the begin to the end day.
        """
        if self.all_day:
            # Do nothing if we already are a all day event
            return

        begin_day = self.begin.floor('day')
        end_day = self.end.floor('day')

        self._begin = begin_day

        # for a one day event, we don't need a _end_time
        if begin_day == end_day:
            self._end_time = None
        else:
            self._end_time = end_day + timedelta(days=1)

        self._duration = None
        self._begin_precision = 'day'

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

    def __repr__(self) -> str:
        name = "'{}' ".format(self.name) if self.name else ''
        if self.all_day:
            assert self._begin
            if not self._end_time or self._begin == self._end_time:
                return "<all-day Event {}{}>".format(name, self.begin.strftime('%Y-%m-%d'))
            else:
                return "<all-day Event {}begin:{} end:{}>".format(name, self._begin.strftime('%Y-%m-%d'), self._end_time.strftime('%Y-%m-%d'))
        elif self.begin is None:
            return "<Event '{}'>".format(self.name) if self.name else "<Event>"
        else:
            return "<Event {}begin:{} end:{}>".format(name, self.begin, self.end)

    def starts_within(self, other) -> bool:
        if not isinstance(other, Event):
            raise NotImplementedError(
                'Cannot compare Event and {}'.format(type(other)))
        return self.begin >= other.begin and self.begin <= other.end

    def ends_within(self, other) -> bool:
        if not isinstance(other, Event):
            raise NotImplementedError(
                'Cannot compare Event and {}'.format(type(other)))
        return self.end >= other.begin and self.end <= other.end

    def intersects(self, other) -> bool:
        if not isinstance(other, Event):
            raise NotImplementedError(
                'Cannot compare Event and {}'.format(type(other)))
        return (self.starts_within(other)
                or self.ends_within(other)
                or other.starts_within(self)
                or other.ends_within(self))

    __xor__ = intersects

    def includes(self, other) -> bool:
        if isinstance(other, Event):
            return other.starts_within(self) and other.ends_within(self)
        if isinstance(other, datetime):
            return self.begin <= other and self.end >= other
        raise NotImplementedError(
            'Cannot compare Event and {}'.format(type(other)))

    def is_included_in(self, other) -> bool:
        if isinstance(other, Event):
            return other.includes(self)
        raise NotImplementedError(
            'Cannot compare Event and {}'.format(type(other)))

    __in__ = is_included_in

    def __lt__(self, other) -> bool:
        if isinstance(other, Event):
            if self.begin is None and other.begin is None:
                if self.name is None and other.name is None:
                    return False
                elif self.name is None:
                    return True
                elif other.name is None:
                    return False
                else:
                    return self.name < other.name
            # if we arrive here, at least one of self.begin
            # and other.begin is not None
            # so if they are equal, they are both Arrow
            elif self.begin == other.begin:
                if self.end is None:
                    return True
                elif other.end is None:
                    return False
                else:
                    return self.end < other.end
            else:
                return self.begin < other.begin
        if isinstance(other, datetime):
            return self.begin < other
        raise NotImplementedError(
            'Cannot compare Event and {}'.format(type(other)))

    def __le__(self, other) -> bool:
        if isinstance(other, Event):
            if self.begin is None and other.begin is None:
                if self.name is None and other.name is None:
                    return True
                elif self.name is None:
                    return True
                elif other.name is None:
                    return False
                else:
                    return self.name <= other.name
            elif self.begin == other.begin:
                if self.end is None:
                    return True
                elif other.end is None:
                    return False
                else:
                    return self.end <= other.end
            else:
                return self.begin <= other.begin
        if isinstance(other, datetime):
            return self.begin <= other
        raise NotImplementedError(
            'Cannot compare Event and {}'.format(type(other)))

    def __gt__(self, other) -> bool:
        return not self.__le__(other)

    def __ge__(self, other) -> bool:
        return not self.__lt__(other)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Event):
            return (self.name == other.name
            and self.begin == other.begin
            and self.end == other.end
            and self.duration == other.duration
            and self.description == other.description
            and self.created == other.created
            and self.last_modified == other.last_modified
            and self.location == other.location
            and self.url == other.url
            and self.transparent == other.transparent
            and self.alarms == other.alarms
            and self.attendees == other.attendees
            and self.categories == other.categories
            and self.status == other.status
            and self.organizer == other.organizer)
        raise NotImplementedError(
            'Cannot compare Event and {}'.format(type(other)))

    def time_equals(self, other) -> bool:
        return (self.begin == other.begin) and (self.end == other.end)

    def join(self, other, *args, **kwarg):
        """Create a new event which covers the time range of two intersecting events

        All extra parameters are passed to the Event constructor.

        Args:
            other: the other event

        Returns:
            a new Event instance
        """
        event = Event(*args, **kwarg)
        if self.intersects(other):
            if self.starts_within(other):
                event.begin = other.begin
            else:
                event.begin = self.begin

            if self.ends_within(other):
                event.end = other.end
            else:
                event.end = self.end

            return event
        raise ValueError('Cannot join {} with {}: they don\'t intersect.'.format(self, other))

    __and__ = join

    def clone(self):
        """
        Returns:
            Event: an exact copy of self"""
        clone = copy.copy(self)
        clone.extra = clone.extra.clone()
        clone.alarms = copy.copy(self.alarms)
        clone.categories = copy.copy(self.categories)
        return clone

    def __hash__(self) -> int:
        """
        Returns:
            int: hash of self. Based on self.uid."""
        return int(''.join(map(lambda x: '%.3d' % ord(x), self.uid)))
