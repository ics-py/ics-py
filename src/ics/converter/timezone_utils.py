from enum import Enum

import datetime
import dateutil
from typing import Union, cast

from ics.timezone import Timezone, UTC, TimezoneStandardObservance, RRULE_EPOCH_START
from ics.types import UTCOffset
from ics.utils import TIMEDELTA_ZERO

__all__ = [
    "TimezoneResult",
    "Timezone_from_offset",
    "Timezone_from_builtin",
    "Timezone_from_dateutil",
    "Timezone_from_pytz",
    "TIMEZONE_CONVERTERS",
]


class TimezoneResult(Enum):
    CONTINUE = 1
    LOCAL = 2
    UNSERIALIZABLE = 3
    NOT_IMPLEMENTED = 4


def Timezone_from_offset(name: str, offset: datetime.timedelta) -> Timezone:
    return Timezone(name, [TimezoneStandardObservance(
        cast(UTCOffset, TIMEDELTA_ZERO),
        cast(UTCOffset, offset),
        RRULE_EPOCH_START,
        name)])


def Timezone_from_builtin(tzinfo: datetime.tzinfo) -> Union[Timezone, TimezoneResult]:
    if isinstance(tzinfo, datetime.timezone):
        return Timezone_from_offset(tzinfo._name, tzinfo._offset)  # type: ignore[attr-defined]
    elif type(tzinfo).__qualname__ == "ZoneInfo":
        from zoneinfo import ZoneInfo
        assert isinstance(tzinfo, ZoneInfo)
        if tzinfo.key:
            return Timezone.from_tzid(tzinfo.key)
        else:
            return TimezoneResult.UNSERIALIZABLE
    else:
        return TimezoneResult.CONTINUE


def Timezone_from_dateutil(tzinfo: datetime.tzinfo) -> Union[Timezone, TimezoneResult]:
    if isinstance(tzinfo, dateutil.tz.tzfile):
        filename = tzinfo._filename  # type: ignore[attr-defined]
        if not filename:
            return TimezoneResult.UNSERIALIZABLE
        elif filename.endswith("localtime"):
            return TimezoneResult.LOCAL
        else:
            return Timezone.from_tzid(filename)
    elif dateutil.tz.tzwin and isinstance(tzinfo, dateutil.tz.tzwin):  # type: ignore[attr-defined]
        return Timezone.from_tzid(tzinfo._name)
    elif dateutil.tz.tzwinlocal and isinstance(tzinfo, dateutil.tz.tzwinlocal):  # type: ignore[attr-defined]
        return TimezoneResult.LOCAL  # tzinfo._display
    elif isinstance(tzinfo, dateutil.tz.tzlocal):
        return TimezoneResult.LOCAL  # tzinfo._tznames
    elif isinstance(tzinfo, dateutil.tz.tzstr):
        return TimezoneResult.NOT_IMPLEMENTED
    elif isinstance(tzinfo, (dateutil.tz.tzical, dateutil.tz._tzicalvtz)):  # type: ignore[attr-defined]
        return TimezoneResult.NOT_IMPLEMENTED
    elif isinstance(tzinfo, dateutil.tz.tzrange):
        return TimezoneResult.NOT_IMPLEMENTED
    else:
        return TimezoneResult.CONTINUE


def Timezone_from_pytz(tzinfo: datetime.tzinfo) -> Union[Timezone, TimezoneResult]:
    if not (type(tzinfo).__module__ == "pytz" or type(tzinfo).__module__.startswith("pytz.")):
        return TimezoneResult.CONTINUE

    try:
        import pytz
        import pytz.tzinfo  # type: ignore
        import pytz.reference  # type: ignore
    except ImportError:
        return TimezoneResult.CONTINUE

    if tzinfo == pytz.utc:
        return UTC
    elif isinstance(tzinfo, pytz.tzinfo.DstTzInfo):
        return TimezoneResult.NOT_IMPLEMENTED
    elif isinstance(tzinfo, pytz.tzinfo.StaticTzInfo):
        return Timezone_from_offset(tzinfo.tzname(None), tzinfo.utcoffset(None))
    elif isinstance(tzinfo, pytz.reference.FixedOffset):
        return Timezone_from_offset(tzinfo.tzname(None), tzinfo.utcoffset(None))
    elif isinstance(tzinfo, pytz.reference.LocalTimezone):
        return TimezoneResult.LOCAL
    elif isinstance(tzinfo, pytz.reference.USTimeZone):
        return TimezoneResult.NOT_IMPLEMENTED
    else:
        return TimezoneResult.CONTINUE


TIMEZONE_CONVERTERS = [Timezone_from_builtin, Timezone_from_dateutil, Timezone_from_pytz]
