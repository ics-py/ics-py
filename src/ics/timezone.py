import datetime
from typing import Optional, overload

import attr
import dateutil
import dateutil.tz

from ics.component import Component
from ics.converter.component import ComponentMetaInfo
from ics.types import ContextDict, DatetimeLike
from ics.utils import check_is_instance, ensure_datetime


@attr.s(frozen=True)
class Timezone(Component, datetime.tzinfo):
    MetaInfo = ComponentMetaInfo("VTIMEZONE")

    tzid: str = attr.ib()
    tzinfo_inst: datetime.tzinfo = attr.ib()

    @classmethod
    def from_tzid(cls, tzid: str) -> "Timezone":
        from ics.converter.timezone import Timezone_from_tzid
        return Timezone_from_tzid(tzid)

    @classmethod
    def from_tzinfo(cls, tzinfo: datetime.tzinfo, context: ContextDict) -> "Timezone":
        from ics.converter.timezone import Timezone_from_tzinfo
        return Timezone_from_tzinfo(tzinfo, context)

    def tzname(self, dt: Optional[datetime.datetime]) -> Optional[str]:
        return self.tzinfo_inst.tzname(dt.replace(tzinfo=self.tzinfo_inst))

    def utcoffset(self, dt: Optional[datetime.datetime]) -> Optional[datetime.timedelta]:
        return self.tzinfo_inst.utcoffset(dt.replace(tzinfo=self.tzinfo_inst))

    def dst(self, dt: Optional[datetime.datetime]) -> Optional[datetime.timedelta]:
        return self.tzinfo_inst.dst(dt.replace(tzinfo=self.tzinfo_inst))

    def fromutc(self, dt: datetime.datetime) -> datetime.datetime:
        return self.tzinfo_inst.fromutc(dt.replace(tzinfo=self.tzinfo_inst))


UTC = Timezone("UTC", dateutil.tz.UTC)


@overload
def ensure_utc(value: None) -> None: ...


@overload
def ensure_utc(value: DatetimeLike) -> datetime.datetime: ...


def ensure_utc(value):
    value = ensure_datetime(value)
    if value is not None:
        value = value.astimezone(UTC)
    return value


def now_in_utc() -> datetime.datetime:
    return datetime.datetime.now(tz=UTC)


@overload
def is_utc(value: datetime.datetime) -> bool: ...


@overload
def is_utc(value: datetime.tzinfo) -> bool: ...


def is_utc(value):
    if isinstance(value, datetime.datetime):
        tz = value.tzinfo
    else:
        tz = value

    if tz is None:
        return False
    if tz in [datetime.timezone.utc, dateutil.tz.UTC, UTC]:
        return True
    if isinstance(tz, dateutil.tz.tzutc) or type(tz).__qualname__ == "pytz.UTC":
        return True
    if isinstance(tz, Timezone) and tz.tzid.upper() == "UTC":
        return True
    if str(tz).upper() == "UTC":
        return True

    return False


def validate_utc(inst, attr, value):
    check_is_instance(attr.name, value, datetime)
    if not is_utc(value):
        raise ValueError(
            "'{name}' must be in timezone UTC (got {value!r} which has tzinfo {tzinfo!r})".format(
                name=attr.name, value=value, tzinfo=value.tzinfo
            )
        )
