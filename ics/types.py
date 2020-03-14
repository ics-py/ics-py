from datetime import date, datetime, timedelta, tzinfo
from typing import Any, Dict, List, Optional, TYPE_CHECKING, Tuple, Union, overload

import attr

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

DatetimeLike = Union[Tuple, Dict, datetime, date]
OptionalDatetimeLike = Union[Tuple, Dict, datetime, date, None]
TimedeltaLike = Union[Tuple, Dict, timedelta]
OptionalTimedeltaLike = Union[Tuple, Dict, timedelta, None]

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


@attr.s(these={})
class RuntimeAttrValidation(object):
    __post_init__ = False
    __attr_fields__: Dict[str, Any] = {}

    def __attrs_post_init__(self):
        self.__post_init__ = True

    def __setattr__(self, key, value):
        if self.__post_init__:
            cls = self.__class__
            if not cls.__attr_fields__:
                cls.__attr_fields__ = attr.fields_dict(cls)
            try:
                field = cls.__attr_fields__[key]
            except KeyError:
                pass
            else:  # when no KeyError was thrown
                if field.converter is not None:
                    value = field.converter(value)
                if field.validator is not None:
                    field.validator(self, field, value)
        super(RuntimeAttrValidation, self).__setattr__(key, value)
