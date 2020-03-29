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
    from ics.grammar import ContentLine, Container

__all__ = [
    "ContainerItem", "ContainerList",

    "DatetimeLike", "OptionalDatetimeLike",
    "TimedeltaLike", "OptionalTimedeltaLike",

    "TimespanOrBegin",
    "EventOrTimespan",
    "EventOrTimespanOrInstant",
    "TodoOrTimespan",
    "TodoOrTimespanOrInstant",
    "CalendarEntryOrTimespan",
    "CalendarEntryOrTimespanOrInstant",

    "OptionalTZDict",

    "get_timespan_if_calendar_entry",

    "RuntimeAttrValidation",
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
def get_timespan_if_calendar_entry(value: CalendarEntryOrTimespan) -> "Timespan":
    ...


@overload
def get_timespan_if_calendar_entry(value: datetime) -> datetime:
    ...


@overload
def get_timespan_if_calendar_entry(value: None) -> None:
    ...


def get_timespan_if_calendar_entry(value):
    from ics.event import CalendarEntryAttrs  # noqa

    if isinstance(value, CalendarEntryAttrs):
        return value._timespan
    else:
        return value


@attr.s
class RuntimeAttrValidation(object):
    """
    Mixin that automatically calls the converters and validators of `attr` attributes.
    The library itself only calls these in the generated `__init__` method, with
    this mixin they are also called when later (re-)assigning an attribute, which
    is handled by `__setattr__`. This makes setting attributes as versatile as specifying
    them as init parameters and also ensures that the guarantees of validators are
    preserved even after creation of the object, at a small runtime cost.
    """

    def __attrs_post_init__(self):
        self.__post_init__ = True

    def __setattr__(self, key, value):
        if getattr(self, "__post_init__", None):
            cls = self.__class__  # type: Any
            if not getattr(cls, "__attr_fields__", None):
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
