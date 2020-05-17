# mypy: ignore_errors
# this is because mypy doesn't like the converter of CalendarEntryAttrs.{created,last_modified,dtstamp} and due to some
# bug confuses the files

import functools
import warnings
from datetime import datetime
from typing import Optional

import attr
from attr.validators import in_, instance_of, optional as v_optional

from ics.converter.component import ComponentMetaInfo
from ics.event import CalendarEntryAttrs
from ics.timespan import TodoTimespan
from ics.types import DatetimeLike, TimedeltaLike
from ics.utils import ensure_datetime, ensure_timedelta

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


@attr.s(eq=True, order=False)  # order methods are provided by CalendarEntryAttrs
class TodoAttrs(CalendarEntryAttrs):
    percent: Optional[int] = attr.ib(default=None, validator=v_optional(in_(range(0, MAX_PERCENT + 1))))
    priority: Optional[int] = attr.ib(default=None, validator=v_optional(in_(range(0, MAX_PRIORITY + 1))))
    completed: Optional[datetime] = attr.ib(default=None, converter=ensure_datetime)


class Todo(TodoAttrs):
    """A todo list entry.

    Can have a start time and duration, or start and due time,
    or only start or due time.
    """
    _timespan: TodoTimespan = attr.ib(validator=instance_of(TodoTimespan))

    MetaInfo = ComponentMetaInfo("VTODO")

    def __init__(
            self,
            begin: DatetimeLike = None,
            due: DatetimeLike = None,
            duration: TimedeltaLike = None,
            *args, **kwargs
    ):
        if (begin is not None or due is not None or duration is not None) and "timespan" in kwargs:
            raise ValueError("can't specify explicit timespan together with any of begin, due or duration")
        kwargs.setdefault("timespan", TodoTimespan(ensure_datetime(begin), ensure_datetime(due), ensure_timedelta(duration)))
        super(Todo, self).__init__(kwargs.pop("timespan"), *args, **kwargs)

    ####################################################################################################################

    def convert_due(self, representation):
        if representation == "due":
            representation = "end"
        super(Todo, self).convert_end(representation)

    due = property(TodoAttrs.end.fget, TodoAttrs.end.fset)
    # convert_due = TodoAttrs.convert_end  # see above
    due_representation = property(TodoAttrs.end_representation.fget)
    has_explicit_due = property(TodoAttrs.has_explicit_end.fget)
    due_within = TodoAttrs.ends_within

    end = property(deprecated_due(TodoAttrs.end.fget), deprecated_due(TodoAttrs.end.fset))
    convert_end = deprecated_due(TodoAttrs.convert_end)
    end_representation = property(deprecated_due(TodoAttrs.end_representation.fget))
    has_explicit_end = property(deprecated_due(TodoAttrs.has_explicit_end.fget))
    ends_within = deprecated_due(TodoAttrs.ends_within)
