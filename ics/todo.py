from datetime import datetime, timedelta
from typing import Optional

import attr

from ics.event import CalendarEntryAttrs
from ics.parsers.todo_parser import TodoParser
from ics.serializers.todo_serializer import TodoSerializer
from ics.timespan import Timespan
from ics.types import DatetimeLike, EventOrTimespanOrInstant, get_timespan_if_event
from ics.utils import ensure_datetime

MAX_PERCENT = 100
MAX_PRIORITY = 9


@attr.s
class TodoAttrs(CalendarEntryAttrs):
    percent: Optional[int] = attr.ib(default=None, validator=attr.validators.in_(range(0, MAX_PERCENT + 1)))
    priority: Optional[int] = attr.ib(default=None, validator=attr.validators.in_(range(0, MAX_PRIORITY + 1)))
    completed: Optional[DatetimeLike] = attr.ib(factory=datetime.now, converter=ensure_datetime)


class Todo(TodoAttrs):
    """A todo list entry.

    Can have a start time and duration, or start and due time,
    or only start/due time.
    """

    class Meta:
        name = "VTODO"
        parser = TodoParser
        serializer = TodoSerializer

    def __init__(
            self,
            begin: DatetimeLike = None,
            due: DatetimeLike = None,
            duration: timedelta = None,
            *args, **kwargs
    ):
        super(Todo, self).__init__(Timespan(begin, due, duration), *args, **kwargs)

    ####################################################################################################################

    @property
    def begin(self) -> datetime:
        """Get or set the beginning of the todo.

        |  Will return a :class:`datetime` object.
        |  May be set to anything that :func:`datetime.__init__` understands.
        |  If a due time is defined (not a duration), .begin must not
            be set to a superior value.
        """
        return self._timespan.get_begin()

    @begin.setter
    def begin(self, value: DatetimeLike):
        self._timespan = self._timespan.replace(begin_time=ensure_datetime(value))

    @property
    def due(self) -> datetime:
        """Get or set the due of the todo.

        |  Will return a :class:`datetime` object.
        |  May be set to anything that :func:`datetime.__init__` understands.
        |  If set to a non null value, removes any already
            existing duration.
        |  Setting to None will have unexpected behavior if
            begin is not None.
        |  Must not be set to an inferior value than self.begin.
        """
        return self._timespan.get_effective_end()

    @due.setter
    def due(self, value: DatetimeLike):
        self._timespan = self._timespan.replace(end_time=ensure_datetime(value))

    @property
    def duration(self) -> Optional[timedelta]:
        """Get or set the duration of the todo.

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

    @property
    def has_due(self) -> bool:
        return self._timespan.has_end()

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

    def __lt__(self, second: EventOrTimespanOrInstant) -> bool:
        return self._timespan.__lt__(get_timespan_if_event(second))

    def __le__(self, second: EventOrTimespanOrInstant) -> bool:
        return self._timespan.__le__(get_timespan_if_event(second))

    def __gt__(self, second: EventOrTimespanOrInstant) -> bool:
        return self._timespan.__gt__(get_timespan_if_event(second))

    def __ge__(self, second: EventOrTimespanOrInstant) -> bool:
        return self._timespan.__ge__(get_timespan_if_event(second))
