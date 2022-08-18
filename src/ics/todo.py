# mypy: ignore_errors
# this is because mypy doesn't like the converter of CalendarEntryAttrs.{created,last_modified,dtstamp} and due to some
# bug confuses the files

from datetime import datetime
from typing import ClassVar, Optional, Type

import attr
from attr.validators import in_
from attr.validators import optional as v_optional

from ics.event import CalendarEntryAttrs
from ics.timespan import Timespan, TodoTimespan
from ics.types import DatetimeLike, TimedeltaLike
from ics.utils import ensure_datetime, ensure_timedelta

MAX_PERCENT = 100
MAX_PRIORITY = 9


@attr.s(eq=True, order=False)  # order methods are provided by CalendarEntryAttrs
class TodoAttrs(CalendarEntryAttrs):
    percent: Optional[int] = attr.ib(
        default=None, validator=v_optional(in_(range(0, MAX_PERCENT + 1)))
    )
    priority: Optional[int] = attr.ib(
        default=None, validator=v_optional(in_(range(0, MAX_PRIORITY + 1)))
    )
    completed: Optional[datetime] = attr.ib(default=None, converter=ensure_datetime)


class Todo(TodoAttrs):
    """A todo list entry.

    Can have a start time and duration, or start and due time,
    or only start or due time.
    """

    NAME = "VTODO"
    _TIMESPAN_TYPE: ClassVar[Type[Timespan]] = TodoTimespan

    def __init__(
        self,
        begin: DatetimeLike = None,
        due: DatetimeLike = None,
        duration: TimedeltaLike = None,
        *args,
        **kwargs
    ):
        if (
            begin is not None or due is not None or duration is not None
        ) and "timespan" in kwargs:
            raise ValueError(
                "can't specify explicit timespan together with any of begin, due or duration"
            )
        kwargs.setdefault(
            "timespan",
            TodoTimespan(
                ensure_datetime(begin), ensure_datetime(due), ensure_timedelta(duration)
            ),
        )
        super().__init__(kwargs.pop("timespan"), *args, **kwargs)

    ####################################################################################################################

    def convert_end(self, representation):
        if representation == "due":
            representation = "end"
        super().convert_end(representation)

    due = property(TodoAttrs.end.fget, TodoAttrs.end.fset)
    convert_due = convert_end  # see above
    due_representation = property(TodoAttrs.end_representation.fget)
    has_explicit_due = property(TodoAttrs.has_explicit_end.fget)
    due_within = TodoAttrs.ends_within
