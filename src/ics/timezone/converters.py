import datetime
from enum import Enum
from typing import Union, cast, Optional, Dict, Any

import dateutil

from ics.contentline import string_to_containers
from ics.timezone import Timezone, UTC, TimezoneStandardObservance, RRULE_EPOCH_START, is_utc
from ics.types import UTCOffset, ContextDict
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


def Timezone_from_tzid(tzid: str) -> Timezone:
    import ics_vtimezones  # type: ignore
    tz_ics = ics_vtimezones.find_vtimezone_ics_file(tzid)
    if not tz_ics:
        olson_tzid = ics_vtimezones.windows_to_olson(tzid)
        if olson_tzid:
            tz_ics = ics_vtimezones.find_vtimezone_ics_file(olson_tzid)
    if not tz_ics:
        raise ValueError("no vTimezone.ics file found for %s" % tzid)
    ics_cal = string_to_containers(tz_ics.read_text())
    if not (len(ics_cal) == 1 and len(ics_cal[0]) == 3 and ics_cal[0][2].name == "VTIMEZONE"):
        raise ValueError("vTimezone.ics file %s has invalid content" % tz_ics)
    return Timezone.from_container(ics_cal[0][2])


def Timezone_from_tzinfo(tzinfo: datetime.tzinfo, context: Optional[ContextDict] = None) -> Optional[Timezone]:
    if isinstance(tzinfo, Timezone):
        return tzinfo
    if is_utc(tzinfo):
        return UTC

    cache: Dict[Union[int, datetime.tzinfo], Optional[Timezone]] = {}
    the_id: Any = 0
    if context is not None:
        context.setdefault("tzinfo_CACHE", cache)
        try:
            hash(tzinfo)
        except TypeError:
            the_id = id(tzinfo)
        else:
            the_id = tzinfo
        if the_id in cache:
            return cache[the_id]

    tz: Union[Timezone, TimezoneResult]
    for func in TIMEZONE_CONVERTERS:
        tz = func(tzinfo)
        if tz == TimezoneResult.CONTINUE:
            continue
        elif tz == TimezoneResult.LOCAL:
            if context is not None:
                cache[the_id] = None
            return None
        elif tz in [TimezoneResult.UNSERIALIZABLE, TimezoneResult.NOT_IMPLEMENTED]:
            break
        else:
            assert isinstance(tz, Timezone)
            if context is not None:
                cache[the_id] = tz
            return tz

    raise ValueError("can't produce Timezone from %s %r (%s)" % (type(tzinfo).__qualname__, tzinfo, tz))


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
    module = type(tzinfo).__module__
    if not (module == "pytz" or module.startswith("pytz.")):
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
