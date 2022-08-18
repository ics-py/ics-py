import warnings
from datetime import date, datetime, timedelta
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    Iterator,
    List,
    MutableMapping,
    NewType,
    Optional,
    Tuple,
    Union,
    cast,
    overload,
)
from urllib.parse import ParseResult

import attr

if TYPE_CHECKING:
    # noinspection PyUnresolvedReferences
    # noinspection PyUnresolvedReferences
    from ics.contentline import Container, ContentLine
    from ics.event import CalendarEntryAttrs, Event

    # noinspection PyUnresolvedReferences
    from ics.timespan import Timespan

    # noinspection PyUnresolvedReferences
    from ics.todo import Todo

__all__ = [
    "ContainerItem",
    "ContainerList",
    "URL",
    "DatetimeLike",
    "OptionalDatetimeLike",
    "TimedeltaLike",
    "OptionalTimedeltaLike",
    "TimespanOrBegin",
    "EventOrTimespan",
    "EventOrTimespanOrInstant",
    "TodoOrTimespan",
    "TodoOrTimespanOrInstant",
    "CalendarEntryOrTimespan",
    "CalendarEntryOrTimespanOrInstant",
    "get_timespan_if_calendar_entry",
    "RuntimeAttrValidation",
    "EmptyDict",
    "ExtraParams",
    "EmptyParams",
    "ContextDict",
    "EmptyContext",
    "copy_extra_params",
]

ContainerItem = Union["ContentLine", "Container"]
ContainerList = List[ContainerItem]
URL = ParseResult


class UTCOffsetMeta(type):
    def __instancecheck__(cls, instance):
        return isinstance(instance, timedelta)


class UTCOffset(timedelta, metaclass=UTCOffsetMeta):
    pass


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
    from ics.event import (  # noqa: F811 # pyflakes considers this a redef of the unused if TYPE_CHECKING import above
        CalendarEntryAttrs,
    )

    if isinstance(value, CalendarEntryAttrs):
        return value.timespan
    else:
        return value


@attr.s
class RuntimeAttrValidation:
    """
    Mixin that automatically calls the converters and validators of `attr` attributes.
    The library itself only calls these in the generated `__init__` method, with
    this mixin they are also called when later (re-)assigning an attribute, which
    is handled by `__setattr__`. This makes setting attributes as versatile as specifying
    them as init parameters and also ensures that the guarantees of validators are
    preserved even after creation of the object, at a small runtime cost.
    """

    def __attrs_post_init__(self):
        object.__setattr__(self, "__post_init__", True)

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
        super().__setattr__(key, value)


class EmptyDictType(MutableMapping[Any, None]):
    """An empty, immutable dict that returns `None` for any key. Useful as default value for function arguments."""

    def __getitem__(self, k: Any) -> None:
        return None

    def __setitem__(self, k: Any, v: None) -> None:
        warnings.warn(f"{self.__class__.__name__}[{k!r}] = {v} ignored")
        return

    def __delitem__(self, v: Any) -> None:
        warnings.warn(f"del {self.__class__.__name__}[{v!r}] ignored")
        return

    def __len__(self) -> int:
        return 0

    def __iter__(self) -> Iterator[Any]:
        return iter([])


EmptyDict = EmptyDictType()
ExtraParams = NewType("ExtraParams", Dict[str, List[str]])
EmptyParams = cast("ExtraParams", EmptyDict)
ContextDict = NewType("ContextDict", Dict[Any, Any])  # defaultdict(lambda: None)
EmptyContext = cast("ContextDict", EmptyDict)


def copy_extra_params(old: Optional[ExtraParams]) -> ExtraParams:
    new: ExtraParams = ExtraParams(dict())
    if not old:
        return new
    for key, value in old.items():
        if isinstance(value, str):
            new[key] = value
        elif isinstance(value, list):
            new[key] = list(value)
        else:
            raise ValueError(
                "can't convert extra param {} with value of type {}: {}".format(
                    key, type(value), value
                )
            )
    return new
