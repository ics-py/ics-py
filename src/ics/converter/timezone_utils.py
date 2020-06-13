import datetime
from typing import Optional

import dateutil

from ics.timezone import Timezone, UTC
from ics_vtimezones import find_file_for_tzfile_path, windows_to_olson

__all__ = [
    "LocalTimezone",
    "UnserializeableTimezone",
    "Timezone_from_offset",
    "Timezone_from_builtin",
    "Timezone_from_dateutil",
    "Timezone_from_pytz",
]


def LocalTimezone() -> Timezone:
    return


def UnserializeableTimezone(name: str, tzinfo: datetime.tzinfo) -> Timezone:
    return


def Timezone_from_offset(name: str, offset: datetime.timedelta) -> Timezone:
    return


def Timezone_from_builtin(tzinfo: datetime.tzinfo) -> Optional[Timezone]:
    if isinstance(tzinfo, datetime.timezone):
        return Timezone_from_offset(tzinfo._name, tzinfo._offset)
    else:
        return None


def Timezone_from_dateutil(tzinfo: datetime.tzinfo) -> Optional[Timezone]:
    if isinstance(tzinfo, dateutil.tz.tzfile) and tzinfo._filename:
        if tzinfo._filename.endswith("etc/localtime") \
                or tzinfo._filename.endswith("zoneinfo/localtime") \
                or tzinfo == dateutil.tz.gettz():
            return LocalTimezone()
        else:
            return find_file_for_tzfile_path(tzinfo._filename)
    elif dateutil.tz.tzwin and isinstance(tzinfo, dateutil.tz.tzwin):
        return find_file_for_tzfile_path(windows_to_olson(tzinfo._name))
    elif dateutil.tz.tzwinlocal and isinstance(tzinfo, dateutil.tz.tzwinlocal):
        return LocalTimezone()  # tzinfo._display
    elif isinstance(tzinfo, dateutil.tz.tzlocal):
        return UnserializeableTimezone(str(tzinfo._tznames), tzinfo)
    elif isinstance(tzinfo, dateutil.tz.tzstr):
        return UnserializeableTimezone(tzinfo._s, tzinfo)
    elif isinstance(tzinfo, (dateutil.tz.tzical, dateutil.tz._tzicalvtz)):
        return None
    elif isinstance(tzinfo, dateutil.tz.tzrange):
        # tzrange has no __str__
        return None
    else:
        return None


def Timezone_from_pytz(tzinfo: datetime.tzinfo) -> Optional[Timezone]:
    try:
        import pytz
        import pytz.tzinfo
        import pytz.reference
    except ImportError:
        return None

    if tzinfo == pytz.utc:
        return UTC
    elif isinstance(tzinfo, pytz.tzinfo.DstTzInfo):
        return None
    elif isinstance(tzinfo, pytz.tzinfo.StaticTzInfo):
        return Timezone_from_offset(tzinfo.tzname(None), tzinfo.utcoffset(None))
    elif isinstance(tzinfo, pytz.tzinfo.BaseTzInfo):
        return None
    elif isinstance(tzinfo, pytz.reference.FixedOffset):
        return Timezone_from_offset(tzinfo.tzname(None), tzinfo.utcoffset(None))
    elif isinstance(tzinfo, pytz.reference.LocalTimezone):
        return None
    elif isinstance(tzinfo, pytz.reference.USTimeZone):
        return None
    else:
        return None
