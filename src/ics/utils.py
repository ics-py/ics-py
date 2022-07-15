from datetime import date, datetime, time, timedelta, timezone
from typing import overload
from uuid import uuid4

from ics.types import DatetimeLike, TimedeltaLike

datetime_tzutc = timezone.utc

MIDNIGHT = time()
TIMEDELTA_ZERO = timedelta()
TIMEDELTA_DAY = timedelta(days=1)
TIMEDELTA_SECOND = timedelta(seconds=1)
TIMEDELTA_CACHE = {0: TIMEDELTA_ZERO, "day": TIMEDELTA_DAY, "second": TIMEDELTA_SECOND}
MAX_TIMEDELTA_NEARLY_ZERO = timedelta(seconds=1) / 2


@overload
def ensure_datetime(value: None) -> None:
    ...


@overload
def ensure_datetime(value: DatetimeLike) -> datetime:
    ...


def ensure_datetime(value):
    if value is None:
        return None
    elif isinstance(value, datetime):
        return value
    elif isinstance(value, date):
        return datetime.combine(value, MIDNIGHT, tzinfo=None)
    elif isinstance(value, tuple):
        return datetime(*value)
    elif isinstance(value, dict):
        return datetime(**value)
    else:
        raise ValueError(f"can't construct datetime from {repr(value)}")


@overload
def ensure_timedelta(value: None) -> None:
    ...


@overload
def ensure_timedelta(value: TimedeltaLike) -> timedelta:
    ...


def ensure_timedelta(value):
    if value is None:
        return None
    elif isinstance(value, timedelta):
        return value
    elif isinstance(value, tuple):
        return timedelta(*value)
    elif isinstance(value, dict):
        return timedelta(**value)
    else:
        raise ValueError(f"can't construct timedelta from {repr(value)}")


###############################################################################
# Rounding Utils


def timedelta_nearly_zero(td: timedelta) -> bool:
    return -MAX_TIMEDELTA_NEARLY_ZERO <= td <= MAX_TIMEDELTA_NEARLY_ZERO


@overload
def floor_datetime_to_midnight(value: datetime) -> datetime:
    ...


@overload
def floor_datetime_to_midnight(value: date) -> date:
    ...


@overload
def floor_datetime_to_midnight(value: None) -> None:
    ...


def floor_datetime_to_midnight(value):
    if value is None:
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    return datetime.combine(
        ensure_datetime(value).date(), MIDNIGHT, tzinfo=value.tzinfo
    )


@overload
def ceil_datetime_to_midnight(value: datetime) -> datetime:
    ...


@overload
def ceil_datetime_to_midnight(value: date) -> date:
    ...


@overload
def ceil_datetime_to_midnight(value: None) -> None:
    ...


def ceil_datetime_to_midnight(value):
    if value is None:
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    floored = floor_datetime_to_midnight(value)
    if floored != value:
        return floored + TIMEDELTA_DAY
    else:
        return floored


def floor_timedelta_to_days(value: timedelta) -> timedelta:
    return value - (value % TIMEDELTA_DAY)


def ceil_timedelta_to_days(value: timedelta) -> timedelta:
    mod = value % TIMEDELTA_DAY
    if mod == TIMEDELTA_ZERO:
        return value
    else:
        return value + TIMEDELTA_DAY - mod


###############################################################################
# String Utils


def limit_str_length(val):
    return str(val)  # TODO limit_str_length


def next_after_str_escape(it, full_str):
    try:
        return next(it)
    except StopIteration as e:
        raise ValueError(
            f"value '{full_str}' may not end with an escape sequence"
        ) from e


def uid_gen() -> str:
    uid = str(uuid4())
    return f"{uid}@{uid[:4]}.org"


###############################################################################


def validate_not_none(inst, attr, value):
    if value is None:
        raise ValueError(f"'{attr.name}' may not be None")


def validate_truthy(inst, attr, value):
    if not bool(value):
        raise ValueError(f"'{attr.name}' must be truthy (got {value!r})")


def check_is_instance(name, value, clazz):
    if not isinstance(value, clazz):
        raise TypeError(
            "'{name}' must be {type!r} (got {value!r} that is a "
            "{actual!r}).".format(
                name=name,
                type=clazz,
                actual=value.__class__,
                value=value,
            ),
            name,
            clazz,
            value,
        )


def call_validate_on_inst(inst, attr, value):
    inst.validate(attr, value)


def one(
    iterable,
    too_short="Too few items in iterable, expected one but got zero!",
    too_long="Expected exactly one item in iterable, but got {first!r}, {second!r}, and possibly more!",
):
    it = iter(iterable)
    try:
        first = next(it)
    except StopIteration as e:
        raise ValueError(too_short.format(iter=it)) from e
    try:
        second = next(it)
    except StopIteration:
        return first
    raise ValueError(too_long.format(first=first, second=second, iter=it))
