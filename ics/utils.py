from datetime import date, datetime, time, timedelta, timezone
from typing import Generator, Optional, overload
from uuid import uuid4

from dateutil.tz import UTC as dateutil_tzutc, gettz

from ics.grammar.parse import Container, ContentLine, ParseError
from ics.types import ContainerList, DatetimeLike, OptionalTZDict, TimedeltaLike

datetime_tzutc = timezone.utc
midnight = time()
DATE_FORMATS = {
    6: "%Y%m",
    8: "%Y%m%d",
    11: "%Y%m%dT%H",
    13: "%Y%m%dT%H%M",
    15: "%Y%m%dT%H%M%S"
}
TIMEDELTA_CACHE = {
    0: timedelta(),
    "day": timedelta(days=1),
    "second": timedelta(seconds=1)
}
MAX_TIMEDELTA_NEARLY_ZERO = timedelta(seconds=1) / 2


def timedelta_nearly_zero(td: timedelta) -> bool:
    return -MAX_TIMEDELTA_NEARLY_ZERO <= td <= MAX_TIMEDELTA_NEARLY_ZERO


@overload
def parse_datetime(time_container: None, available_tz: OptionalTZDict = None) -> None: ...


@overload
def parse_datetime(time_container: ContentLine, available_tz: OptionalTZDict = None) -> datetime: ...


def parse_datetime(time_container, available_tz=None):
    if time_container is None:
        return None

    tz_list = time_container.params.get('TZID')
    param_tz: Optional[str] = tz_list[0] if tz_list else None
    # if ('T' not in time_container.value) and 'DATE' in time_container.params.get('VALUE', []):
    val = time_container.value
    fixed_utc = (val[-1].upper() == 'Z')

    val = val.translate({
        ord("/"): "",
        ord("-"): "",
        ord("Z"): "",
        ord("z"): ""})
    dt = datetime.strptime(val, DATE_FORMATS[len(val)])

    if fixed_utc:
        if param_tz:
            raise ValueError("can't specify UTC via appended 'Z' and TZID param '%s'" % param_tz)
        return dt.replace(tzinfo=dateutil_tzutc)
    elif param_tz:
        selected_tz = None
        if available_tz:
            selected_tz = available_tz.get(param_tz, None)
        if selected_tz is None:
            selected_tz = gettz(param_tz)  # be lenient with missing vtimezone definitions
        return dt.replace(tzinfo=selected_tz)
    else:
        return dt


@overload
def parse_date(time_container: None, available_tz: OptionalTZDict = None) -> None: ...


@overload
def parse_date(time_container: ContentLine, available_tz: OptionalTZDict = None) -> datetime: ...


def parse_date(time_container, available_tz=None):
    dt = parse_datetime(time_container, available_tz)
    if dt:
        return ensure_datetime(dt.date())
    else:
        return None


@overload
def ensure_datetime(value: None) -> None: ...


@overload
def ensure_datetime(value: DatetimeLike) -> datetime: ...


def ensure_datetime(value):
    if value is None:
        return None
    elif isinstance(value, datetime):
        return value
    elif isinstance(value, date):
        return datetime.combine(value, midnight, tzinfo=None)
    elif isinstance(value, tuple):
        return datetime(*value)
    elif isinstance(value, dict):
        return datetime(**value)
    else:
        raise ValueError("can't construct datetime from %s" % repr(value))


def serialize_datetime(instant: datetime, is_utc: bool = False) -> str:
    if is_utc:
        return instant.strftime('%Y%m%dT%H%M%SZ')
    else:
        return instant.strftime('%Y%m%dT%H%M%S')


def serialize_datetime_to_contentline(name: str, instant: datetime, used_timezones: OptionalTZDict = None) -> ContentLine:
    # ToDo keep track of used_timezones
    if instant.tzinfo is not None:
        tzname = instant.tzinfo.tzname(instant)
        if tzname is None:
            raise ValueError("timezone of instant '%s' is not None but has no name" % instant)
        if instant.tzinfo == dateutil_tzutc or instant.tzinfo == datetime_tzutc or tzname.upper() == "UTC":
            return ContentLine(name, value=serialize_datetime(instant, True))
        if used_timezones:
            used_timezones[tzname] = instant.tzinfo
        return ContentLine(name, params={'TZID': [tzname]}, value=serialize_datetime(instant, False))
    else:
        return ContentLine(name, value=serialize_datetime(instant, False))


def serialize_date(instant: DatetimeLike) -> str:
    if not isinstance(instant, date):
        instant = ensure_datetime(instant).date()
    return instant.strftime('%Y%m%d')


def iso_precision(string: str) -> str:
    has_time = 'T' in string
    if has_time:
        return 'second'
    else:
        return 'day'


@overload
def ensure_timedelta(value: None) -> None: ...


@overload
def ensure_timedelta(value: TimedeltaLike) -> timedelta: ...


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
        raise ValueError("can't construct timedelta from %s" % repr(value))


def parse_duration(line: str) -> timedelta:
    """
    Return a timedelta object from a string in the DURATION property format
    """
    DAYS = {'D': 1, 'W': 7}
    SECS = {'S': 1, 'M': 60, 'H': 3600}

    sign, i = 1, 0
    if line[i] in '-+':
        if line[i] == '-':
            sign = -1
        i += 1
    if line[i] != 'P':
        raise ParseError("Error while parsing %s" % line)
    i += 1
    days, secs = 0, 0
    while i < len(line):
        if line[i] == 'T':
            i += 1
            if i == len(line):
                break
        j = i
        while line[j].isdigit():
            j += 1
        if i == j:
            raise ParseError("Error while parsing %s" % line)
        val = int(line[i:j])
        if line[j] in DAYS:
            days += val * DAYS[line[j]]
            DAYS.pop(line[j])
        elif line[j] in SECS:
            secs += val * SECS[line[j]]
            SECS.pop(line[j])
        else:
            raise ParseError("Error while parsing %s" % line)
        i = j + 1
    return timedelta(sign * days, sign * secs)


def serialize_duration(dt: timedelta) -> str:
    """
    Return a string according to the DURATION property format
    from a timedelta object
    """
    ONE_DAY_IN_SECS = 3600 * 24
    total = abs(int(dt.total_seconds()))
    days = total // ONE_DAY_IN_SECS
    seconds = total % ONE_DAY_IN_SECS

    res = ''
    if days:
        res += str(days) + 'D'
    if seconds:
        res += 'T'
        if seconds // 3600:
            res += str(seconds // 3600) + 'H'
            seconds %= 3600
        if seconds // 60:
            res += str(seconds // 60) + 'M'
            seconds %= 60
        if seconds:
            res += str(seconds) + 'S'

    if not res:
        res = 'T0S'
    if dt.total_seconds() >= 0:
        return 'P' + res
    else:
        return '-P%s' % res


###############################################################################
# Rounding Utils

@overload
def floor_datetime_to_midnight(value: datetime) -> datetime: ...


@overload
def floor_datetime_to_midnight(value: date) -> date: ...


@overload
def floor_datetime_to_midnight(value: None) -> None: ...


def floor_datetime_to_midnight(value):
    if value is None:
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    return datetime.combine(ensure_datetime(value).date(), midnight, tzinfo=value.tzinfo)


@overload
def ceil_datetime_to_midnight(value: datetime) -> datetime: ...


@overload
def ceil_datetime_to_midnight(value: date) -> date: ...


@overload
def ceil_datetime_to_midnight(value: None) -> None: ...


def ceil_datetime_to_midnight(value):
    if value is None:
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    floored = floor_datetime_to_midnight(value)
    if floored != value:
        return floored + TIMEDELTA_CACHE["day"]
    else:
        return floored


def floor_timedelta_to_days(value: timedelta) -> timedelta:
    return value - (value % TIMEDELTA_CACHE["day"])


def ceil_timedelta_to_days(value: timedelta) -> timedelta:
    mod = value % TIMEDELTA_CACHE["day"]
    if mod == TIMEDELTA_CACHE[0]:
        return value
    else:
        return value + TIMEDELTA_CACHE["day"] - mod


###############################################################################
# String Utils


def get_lines(container: Container, name: str, keep: bool = False) -> ContainerList:
    # FIXME this can be done so much faster by using bucketing
    lines = []
    for i in reversed(range(len(container))):
        item = container[i]
        if item.name == name:
            lines.append(item)
            if not keep:
                del container[i]
    return lines


def remove_x(container: Container) -> None:
    for i in reversed(range(len(container))):
        item = container[i]
        if item.name.startswith('X-'):
            del container[i]


def remove_sequence(container: Container) -> None:
    for i in reversed(range(len(container))):
        item = container[i]
        if item.name == 'SEQUENCE':
            del container[i]


def uid_gen() -> str:
    uid = str(uuid4())
    return "{}@{}.org".format(uid, uid[:4])


def escape_string(string: str) -> str:
    return string.translate(
        {ord("\\"): "\\\\",
         ord(";"): "\\;",
         ord(","): "\\,",
         ord("\n"): "\\n",
         ord("\r"): "\\r"})


def unescape_string(string: str) -> str:
    return "".join(unescape_string_iter(string))


def unescape_string_iter(string: str) -> Generator[str, None, None]:
    it = iter(string)
    for c1 in it:
        if c1 == "\\":
            c2 = next(it)
            if c2 == ";":
                yield ";"
            elif c2 == ",":
                yield ","
            elif c2 == "n" or c2 == "N":
                yield "\n"
            elif c2 == "r" or c2 == "R":
                yield "\r"
            elif c2 == "\\":
                yield "\\"
            else:
                raise ValueError("can't handle escaped character '%s'" % c2)
        else:
            yield c1


###############################################################################

def validate_not_none(inst, attr, value):
    if value is None:
        raise ValueError(
            "'{name}' may not be None".format(
                name=attr.name
            )
        )


def validate_truthy(inst, attr, value):
    if not bool(value):
        raise ValueError(
            "'{name}' must be truthy (got {value!r})".format(
                name=attr.name, value=value
            )
        )


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
