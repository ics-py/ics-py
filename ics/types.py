from datetime import date, datetime, tzinfo
from typing import Dict, List, Optional, TYPE_CHECKING, Union, overload

if TYPE_CHECKING:
    # noinspection PyUnresolvedReferences
    from ics.event import Event, CalendarEntryAttrs
    # noinspection PyUnresolvedReferences
    from ics.todo import Todo
    # noinspection PyUnresolvedReferences
    from ics.timespan import Timespan
    # noinspection PyUnresolvedReferences
    from ics.grammar.parse import ContentLine, Container

__all__ = [
    "ContainerItem", "ContainerList", "DatetimeLike", "OptionalDatetimeLike", "TimespanOrBegin", "EventOrTimespan",
    "EventOrTimespanOrInstant", "TodoOrTimespan", "TodoOrTimespanOrInstant", "CalendarEntryOrTimespan",
    "CalendarEntryOrTimespanOrInstant", "OptionalTZDict", "get_timespan_if_calendar_entry"
]

ContainerItem = Union["ContentLine", "Container"]
ContainerList = List[ContainerItem]

DatetimeLike = Union[datetime, date]
OptionalDatetimeLike = Union[datetime, date, None]

TimespanOrBegin = Union[datetime, date, "Timespan"]
EventOrTimespan = Union["Event", "Timespan"]
EventOrTimespanOrInstant = Union["Event", "Timespan", datetime]
TodoOrTimespan = Union["Todo", "Timespan"]
TodoOrTimespanOrInstant = Union["Todo", "Timespan", datetime]
CalendarEntryOrTimespan = Union["CalendarEntryAttrs", "Timespan"]
CalendarEntryOrTimespanOrInstant = Union["CalendarEntryAttrs", "Timespan", datetime]

OptionalTZDict = Optional[Dict[str, tzinfo]]


@overload
def get_timespan_if_calendar_entry(value: CalendarEntryOrTimespan) -> "Timespan": ...


@overload
def get_timespan_if_calendar_entry(value: datetime) -> datetime: ...


@overload
def get_timespan_if_calendar_entry(value: None) -> None: ...


def get_timespan_if_calendar_entry(value):
    from ics.event import CalendarEntryAttrs
    if isinstance(value, CalendarEntryAttrs):
        return value._timespan
    else:
        return value
