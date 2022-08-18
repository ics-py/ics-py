import datetime
import functools
import warnings
from typing import ClassVar, List, Optional, cast, overload

import attr
import dateutil
import dateutil.rrule
import dateutil.tz
from attr.validators import instance_of
from dateutil.tz._common import _tzinfo

from ics.component import Component
from ics.types import URL, ContextDict, DatetimeLike, UTCOffset
from ics.utils import TIMEDELTA_ZERO, check_is_instance, ensure_datetime

__all__ = [
    "ensure_utc",
    "now_in_utc",
    "is_utc",
    "validate_utc",
    "TimezoneObservance",
    "TimezoneStandardObservance",
    "TimezoneDaylightObservance",
    "Timezone",
    "RRULE_EPOCH_START",
    "UTC",
]


@overload
def ensure_utc(value: None) -> None:
    ...


@overload
def ensure_utc(value: DatetimeLike) -> datetime.datetime:
    ...


def ensure_utc(value):
    value = ensure_datetime(value)
    if value is not None:
        value = value.astimezone(UTC)
    return value


def now_in_utc() -> datetime.datetime:
    return datetime.datetime.now(tz=UTC)


@overload
def is_utc(value: datetime.datetime) -> bool:
    ...


@overload
def is_utc(value: datetime.tzinfo) -> bool:
    ...


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
    if isinstance(tz, Timezone) and tz.tzid.upper() in ["UTC", "ETC/UTC"]:
        return True
    if str(tz).upper() in ["UTC", "ETC/UTC"]:
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


def rrule_to_rruleset(val):
    if isinstance(val, dateutil.rrule.rrule):
        rruleset = dateutil.rrule.rruleset()
        rruleset.rrule(val)
        return rruleset
    else:
        return val


@attr.s(slots=True, frozen=True)
class TimezoneObservance(Component):
    tzoffsetfrom: UTCOffset = attr.ib()
    tzoffsetto: UTCOffset = attr.ib()
    rrule: dateutil.rrule.rruleset = attr.ib(converter=rrule_to_rruleset, validator=instance_of(dateutil.rrule.rruleset))  # type: ignore[misc]

    tzname: Optional[str] = attr.ib(default=None)
    comment: Optional[str] = attr.ib(default=None)

    is_dst: ClassVar[bool] = False

    @property
    def tzoffsetdiff(self) -> datetime.timedelta:
        return self.tzoffsetto - self.tzoffsetfrom


class TimezoneStandardObservance(TimezoneObservance):
    NAME = "STANDARD"


class TimezoneDaylightObservance(TimezoneObservance):
    NAME = "DAYLIGHT"

    is_dst: ClassVar[bool] = True


@attr.s(frozen=True, repr=False)
class Timezone(Component, _tzinfo):
    NAME = "VTIMEZONE"

    tzid: str = attr.ib()
    observances: List[TimezoneObservance] = attr.ib(factory=list)
    tzurl: Optional[URL] = attr.ib(default=None)
    last_modified: Optional[datetime.datetime] = attr.ib(default=None, converter=ensure_utc)  # type: ignore[misc]

    @classmethod
    def from_tzid(cls, tzid: str) -> "Timezone":
        from ics.timezone.converters import Timezone_from_tzid

        return Timezone_from_tzid(tzid)

    @classmethod
    def from_tzinfo(
        cls, tzinfo: datetime.tzinfo, context: Optional[ContextDict] = None
    ) -> Optional["Timezone"]:
        from ics.timezone.converters import Timezone_from_tzinfo

        return Timezone_from_tzinfo(tzinfo, context)

    @property
    def is_builtin(self):
        import ics_vtimezones  # type: ignore

        return is_utc(self) or self.tzid.startswith(ics_vtimezones.BUILTIN_TZID_PREFIX)

    def to_builtin(self) -> "Timezone":
        if self.is_builtin:
            return self
        else:
            builtin = Timezone.from_tzid(self.tzid)
            if builtin.observances != self.observances:
                warnings.warn(
                    "Converting {} to built-in Timezone {} might change interpretation of some timestamps.".format(
                        self, builtin
                    )
                )
            return builtin

    def __attrs_post_init__(self):
        super().__attrs_post_init__()
        if len(self.observances) >= 2:
            # one lru cache per Timezone instance, so no Timezone hashing is needed
            func = functools.lru_cache(10)(self._find_observance_cachable)
            object.__setattr__(self, "_find_observance_cachable", func)

    def __str__(self):
        return self.tzid

    def __repr__(self):
        if self.is_builtin:
            return f"Timezone.from_tzid({self.tzid!r})"
        else:
            return f"Timezone({self.tzid!r}, observances={self.observances!r})"

    def _find_observance(self, dt):
        if len(self.observances) < 2:
            return self.observances[0]

        return self._find_observance_cachable(dt.replace(tzinfo=None))

    def _find_observance_cachable(self, dt):
        # adapted from dateutil.tz.tz._tzicalvtz._find_comp

        lastcompdt = lastcomp = None
        for comp in self.observances:
            if comp.tzoffsetdiff < TIMEDELTA_ZERO and getattr(dt, "fold", 0):
                compdt = comp.rrule.before(dt - comp.tzoffsetdiff, inc=True)
            else:
                compdt = comp.rrule.before(dt, inc=True)
            if compdt and (not lastcompdt or lastcompdt < compdt):
                lastcompdt = compdt
                lastcomp = comp

        if lastcomp:
            return lastcomp
        else:
            # RFC says nothing about what to do when a given time is before the first onset date.
            # We'll look for the first standard component,
            # or the first component, if none is found.
            for comp in self.observances:
                if not comp.is_dst:
                    return comp

            return self.observances[0]

    def utcoffset(self, dt):
        if dt is None:
            return None
        else:
            return self._find_observance(dt).tzoffsetto

    def dst(self, dt):
        comp = self._find_observance(dt)
        if comp.is_dst:
            return comp.tzoffsetdiff
        else:
            return TIMEDELTA_ZERO

    def tzname(self, dt):
        return self._find_observance(dt).tzname


RRULE_EPOCH_START = dateutil.rrule.rrule(
    freq=dateutil.rrule.YEARLY, dtstart=datetime.datetime(1970, 1, 1), count=1
)
UTC = Timezone(
    "UTC",
    [
        TimezoneStandardObservance(
            cast(UTCOffset, TIMEDELTA_ZERO),
            cast(UTCOffset, TIMEDELTA_ZERO),
            RRULE_EPOCH_START,
            "UTC",
        )
    ],
)
