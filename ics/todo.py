# mypy: ignore_errors
# this is because mypy doesn't like the converter of CalendarEntryAttrs.{created,last_modified,dtstamp} and due to some
# bug confuses the files

import functools
import warnings
from datetime import datetime, timedelta
from typing import Optional

import attr
from attr.validators import in_, optional as v_optional

from ics.event import CalendarEntryAttrs
from ics.parsers.todo_parser import TodoParser
from ics.serializers.todo_serializer import TodoSerializer
from ics.timespan import Timespan
from ics.types import DatetimeLike
from ics.utils import ensure_datetime

MAX_PERCENT = 100
MAX_PRIORITY = 9


def deprecated_due(fun):
    @functools.wraps(fun)
    def wrapper(*args, **kwargs):
        msg = "Call to deprecated function {}. Use `due` instead of `end` for class Todo."
        warnings.warn(
            msg.format(fun.__name__),
            category=DeprecationWarning
        )
        return fun(*args, **kwargs)

    return wrapper


@attr.s(repr=False)
class TodoAttrs(CalendarEntryAttrs):
    percent: Optional[int] = attr.ib(default=None, validator=v_optional(in_(range(0, MAX_PERCENT + 1))))
    priority: Optional[int] = attr.ib(default=None, validator=v_optional(in_(range(0, MAX_PRIORITY + 1))))
    completed: Optional[datetime] = attr.ib(factory=datetime.now, converter=ensure_datetime)  # type: ignore


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
        super(Todo, self).__init__(
            Timespan(ensure_datetime(begin), ensure_datetime(due), duration),
            *args, **kwargs)

    ####################################################################################################################

    def convert_due(self, representation):
        if representation == "due":
            representation = "end"
        super(Todo, self).convert_end(representation)

    due = property(TodoAttrs.end.fget, TodoAttrs.end.fset)  # type: ignore
    due_representation = property(TodoAttrs.end_representation.fget)  # type: ignore
    has_due = property(TodoAttrs.has_end.fget)  # type: ignore
    due_within = TodoAttrs.ends_within

    end = property(deprecated_due(TodoAttrs.end.fget), deprecated_due(TodoAttrs.end.fset))  # type: ignore
    convert_end = deprecated_due(TodoAttrs.convert_end)
    end_representation = property(deprecated_due(TodoAttrs.end_representation.fget))  # type: ignore
    has_end = property(deprecated_due(TodoAttrs.has_end.fget))  # type: ignore
    ends_within = deprecated_due(TodoAttrs.ends_within)
