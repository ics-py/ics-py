import re
import warnings
from datetime import date, datetime, time, timedelta
from typing import List, Optional, Type, cast

from dateutil.tz import UTC as dateutil_tzutc
from dateutil.tz import gettz

from ics.timespan import Timespan
from ics.timezone import Timezone, is_utc
from ics.types import (
    ContextDict,
    EmptyContext,
    EmptyParams,
    ExtraParams,
    UTCOffset,
    copy_extra_params,
)
from ics.valuetype.base import ValueConverter

__all__ = [
    "DatetimeConverterMixin",
    "DatetimeConverter",
    "DateConverter",
    "TimeConverter",
    "UTCOffsetConverter",
    "DurationConverter",
    "PeriodConverter",
]


class DatetimeConverterMixin:
    FORMATS = {6: "%Y%m", 8: "%Y%m%d"}
    CONTEXT_KEY_AVAILABLE_TZ = "DatetimeAvailableTimezones"

    def _serialize_dt(
        self,
        value: datetime,
        params: ExtraParams,
        context: ContextDict,
        utc_fmt="%Y%m%dT%H%M%SZ",
        nonutc_fmt="%Y%m%dT%H%M%S",
    ) -> str:
        if is_utc(value):
            return value.strftime(utc_fmt)

        if value.tzinfo is not None:
            tz = Timezone.from_tzinfo(value.tzinfo, context)
            if tz is not None:
                params["TZID"] = [tz.tzid]
                available_tz = context.setdefault(self.CONTEXT_KEY_AVAILABLE_TZ, {})
                available_tz.setdefault(tz.tzid, tz)
        return value.strftime(nonutc_fmt)

    def _parse_dt(
        self,
        value: str,
        params: ExtraParams,
        context: ContextDict,
        warn_no_avail_tz=True,
    ) -> datetime:
        param_tz_list: Optional[List[str]] = params.pop(
            "TZID", None
        )  # we remove the TZID from context
        if param_tz_list:
            if len(param_tz_list) > 1:
                raise ValueError("got multiple TZIDs")
            param_tz: Optional[str] = str(param_tz_list[0])  # convert QuotedParamValues
        else:
            param_tz = None
        available_tz = context.setdefault(self.CONTEXT_KEY_AVAILABLE_TZ, {})
        if available_tz is None and warn_no_avail_tz:
            warnings.warn(
                "DatetimeConverterMixin.parse called without available_tz dict in context"
            )
        fixed_utc = value[-1].upper() == "Z"

        tr_value = value.translate(
            {ord("/"): "", ord("-"): "", ord("Z"): "", ord("z"): ""}
        )
        try:
            format = self.FORMATS[len(tr_value)]
        except KeyError:
            raise ValueError(
                "couldn't find format matching %r (%s chars), tried %s"
                % (tr_value, len(tr_value), self.FORMATS)
            )
        dt = datetime.strptime(tr_value, format)

        if fixed_utc:
            if param_tz:
                raise ValueError(
                    f"can't specify UTC via appended 'Z' and TZID param '{param_tz}'"
                )
            return dt.replace(tzinfo=dateutil_tzutc)
        elif param_tz:
            selected_tz = None
            if available_tz:
                selected_tz = available_tz.get(param_tz, None)
            if selected_tz is None:
                try:
                    selected_tz = Timezone.from_tzid(
                        param_tz
                    )  # be lenient with missing vtimezone definitions
                except ValueError:
                    found_tz = gettz(param_tz)
                    import platform
                    import sys

                    if not found_tz:
                        raise ValueError(
                            "timezone %s is unknown on this system (%s on %s)"
                            % (param_tz, sys.version, platform.platform(terse=True))
                        )
                    else:
                        warnings.warn(
                            "no ics representation available for timezone %s, but known to system (%s on %s) as %s "
                            % (
                                param_tz,
                                sys.version,
                                platform.platform(terse=True),
                                found_tz,
                            )
                        )
                    selected_tz = found_tz
                available_tz.setdefault(param_tz, selected_tz)
            return dt.replace(tzinfo=selected_tz)
        else:
            return dt


class DatetimeConverterClass(DatetimeConverterMixin, ValueConverter[datetime]):
    FORMATS = {
        **DatetimeConverterMixin.FORMATS,
        11: "%Y%m%dT%H",
        13: "%Y%m%dT%H%M",
        15: "%Y%m%dT%H%M%S",
    }

    @property
    def ics_type(self) -> str:
        return "DATE-TIME"

    @property
    def python_type(self) -> Type[datetime]:
        return datetime

    def serialize(
        self,
        value: datetime,
        params: ExtraParams = EmptyParams,
        context: ContextDict = EmptyContext,
    ) -> str:
        return self._serialize_dt(value, params, context)

    def parse(
        self,
        value: str,
        params: ExtraParams = EmptyParams,
        context: ContextDict = EmptyContext,
    ) -> datetime:
        return self._parse_dt(value, params, context)


DatetimeConverter = DatetimeConverterClass()


class DateConverterClass(DatetimeConverterMixin, ValueConverter[date]):
    @property
    def ics_type(self) -> str:
        return "DATE"

    @property
    def python_type(self) -> Type[date]:
        return date

    def serialize(
        self,
        value,
        params: ExtraParams = EmptyParams,
        context: ContextDict = EmptyContext,
    ):
        return value.strftime("%Y%m%d")

    def parse(
        self,
        value,
        params: ExtraParams = EmptyParams,
        context: ContextDict = EmptyContext,
    ):
        return self._parse_dt(value, params, context, warn_no_avail_tz=False).date()


DateConverter = DateConverterClass()


class TimeConverterClass(DatetimeConverterMixin, ValueConverter[time]):
    FORMATS = {2: "%H", 4: "%H%M", 6: "%H%M%S"}

    @property
    def ics_type(self) -> str:
        return "TIME"

    @property
    def python_type(self) -> Type[time]:
        return time

    def serialize(
        self,
        value,
        params: ExtraParams = EmptyParams,
        context: ContextDict = EmptyContext,
    ):
        return self._serialize_dt(
            value, params, context, utc_fmt="%H%M%SZ", nonutc_fmt="%H%M%S"
        )

    def parse(
        self,
        value,
        params: ExtraParams = EmptyParams,
        context: ContextDict = EmptyContext,
    ):
        return self._parse_dt(value, params, context).timetz()


TimeConverter = TimeConverterClass()


class UTCOffsetConverterClass(ValueConverter[UTCOffset]):
    @property
    def ics_type(self) -> str:
        return "UTC-OFFSET"

    @property
    def python_type(self) -> Type[UTCOffset]:
        return UTCOffset

    def parse(
        self,
        value: str,
        params: ExtraParams = EmptyParams,
        context: ContextDict = EmptyContext,
    ) -> UTCOffset:
        match = re.fullmatch(
            r"(?P<sign>\+|-|)(?P<hours>[0-9]{2})(?P<minutes>[0-9]{2})(?P<seconds>[0-9]{2})?",
            value,
        )
        if not match:
            raise ValueError("value '%s' is not a valid UTCOffset")
        groups = match.groupdict()
        sign = groups.pop("sign")
        td = timedelta(**{k: int(v) for k, v in groups.items() if v})
        if sign == "-":
            return cast(UTCOffset, -td)
        else:
            return cast(UTCOffset, td)

    def serialize(
        self,
        value: UTCOffset,
        params: ExtraParams = EmptyParams,
        context: ContextDict = EmptyContext,
    ) -> str:
        assert value is not None
        seconds = value.total_seconds()
        if seconds < 0:
            seconds *= -1
            res = "-"
        else:
            res = "+"

        # hours
        res += "%02d" % (seconds // 3600)
        seconds %= 3600

        # minutes
        res += "%02d" % (seconds // 60)
        seconds %= 60

        if seconds:
            # seconds
            res += "%02d" % seconds

        return res


UTCOffsetConverter = UTCOffsetConverterClass()


class DurationConverterClass(ValueConverter[timedelta]):
    @property
    def ics_type(self) -> str:
        return "DURATION"

    @property
    def python_type(self) -> Type[timedelta]:
        return timedelta

    def parse(
        self,
        value: str,
        params: ExtraParams = EmptyParams,
        context: ContextDict = EmptyContext,
    ) -> timedelta:
        DAYS = {"D": 1, "W": 7}
        SECS = {"S": 1, "M": 60, "H": 3600}

        sign, i = 1, 0
        if value[i] in "-+":
            if value[i] == "-":
                sign = -1
            i += 1
        if value[i] != "P":
            raise ValueError(f"Error while parsing {value}")
        i += 1
        days, secs = 0, 0
        while i < len(value):
            if value[i] == "T":
                i += 1
                if i == len(value):
                    break
            j = i
            while value[j].isdigit():
                j += 1
            if i == j:
                raise ValueError(f"Error while parsing {value}")
            val = int(value[i:j])
            if value[j] in DAYS:
                days += val * DAYS[value[j]]
                DAYS.pop(value[j])
            elif value[j] in SECS:
                secs += val * SECS[value[j]]
                SECS.pop(value[j])
            else:
                raise ValueError(f"Error while parsing {value}")
            i = j + 1
        return timedelta(sign * days, sign * secs)

    def serialize(
        self,
        value: timedelta,
        params: ExtraParams = EmptyParams,
        context: ContextDict = EmptyContext,
    ) -> str:
        ONE_DAY_IN_SECS = 3600 * 24
        total = abs(int(value.total_seconds()))
        days = total // ONE_DAY_IN_SECS
        seconds = total % ONE_DAY_IN_SECS

        res = ""
        if days:
            res += str(days) + "D"
        if seconds:
            res += "T"
            if seconds // 3600:
                res += str(seconds // 3600) + "H"
                seconds %= 3600
            if seconds // 60:
                res += str(seconds // 60) + "M"
                seconds %= 60
            if seconds:
                res += str(seconds) + "S"

        if not res:
            res = "T0S"
        if value.total_seconds() >= 0:
            return "P" + res
        else:
            return f"-P{res}"


DurationConverter = DurationConverterClass()


class PeriodConverterClass(DatetimeConverterMixin, ValueConverter[Timespan]):
    @property
    def ics_type(self) -> str:
        return "PERIOD"

    @property
    def python_type(self) -> Type[Timespan]:
        return Timespan

    def parse(
        self,
        value: str,
        params: ExtraParams = EmptyParams,
        context: ContextDict = EmptyContext,
    ):
        start, sep, end = value.partition("/")
        if not sep:
            raise ValueError("PERIOD '%s' must contain the separator '/'")
        if end.startswith("P"):  # period-start = date-time "/" dur-value
            return Timespan(
                begin_time=self._parse_dt(start, params, context),
                duration=DurationConverter.parse(end, params, context),
            )
        else:  # period-explicit = date-time "/" date-time
            end_params = copy_extra_params(
                params
            )  # ensure that the first parse doesn't remove TZID also needed by the second call
            return Timespan(
                begin_time=self._parse_dt(start, params, context),
                end_time=self._parse_dt(end, end_params, context),
            )

    def serialize(
        self,
        value: Timespan,
        params: ExtraParams = EmptyParams,
        context: ContextDict = EmptyContext,
    ) -> str:
        # note: there are no DATE to DATE / all-day periods
        begin = value.get_begin()
        if begin is None:
            raise ValueError("PERIOD must have a begin timestamp")
        if value.get_end_representation() == "duration":
            duration = cast(timedelta, value.get_effective_duration())
            return "{}/{}".format(
                self._serialize_dt(begin, params, context),
                DurationConverter.serialize(duration, params, context),
            )
        else:
            end = value.get_effective_end()
            if end is None:
                raise ValueError("PERIOD must have a end timestamp")
            end_params = copy_extra_params(params)
            res = "{}/{}".format(
                self._serialize_dt(begin, params, context),
                self._serialize_dt(end, end_params, context),
            )
            if end_params != params:
                raise ValueError(
                    "Begin and end time of PERIOD %s must serialize to the same params! "
                    "Got %s != %s." % (value, params, end_params)
                )
            return res


PeriodConverter = PeriodConverterClass()
