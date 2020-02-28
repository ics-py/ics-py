from datetime import date, datetime
from typing import List, TYPE_CHECKING, Union

DatetimeLike = Union[datetime, date]
OptionalDatetimeLike = Union[datetime, date, None]

if TYPE_CHECKING:
    from ics.timespan import Timespan
    from ics.event import Event
    from ics.grammar.parse import ContentLine, Container

    TimespanOrBegin = Union[datetime, date, Timespan]
    EventOrTimespan = Union[Event, Timespan]
    EventOrTimespanOrInstant = Union[Event, Timespan, datetime]
    ContainerList = List[Union[ContentLine, Container]]
else:
    TimespanOrBegin = Union[datetime, date, "Timespan"]
    EventOrTimespan = Union["Event", "Timespan"]
    EventOrTimespanOrInstant = Union["Event", "Timespan", datetime]
    ContainerList = list


def get_timespan_if_event(value):
    if isinstance(value, Event):
        return value._timespan
    else:
        return value
