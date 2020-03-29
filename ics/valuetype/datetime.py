import re
from datetime import date, datetime, time, timedelta
from typing import Optional, Type, cast

from dateutil.tz import UTC as dateutil_tzutc, gettz, tzoffset as UTCOffset

from ics.timespan import Timespan
from ics.types import OptionalTZDict
from ics.utils import ensure_datetime, is_utc
from ics.valuetype.base import ValueConverter


class DatetimeConverterMixin(object):
    FORMATS = {
        6: "%Y%m",
        8: "%Y%m%d"
    }

    def serialize(self, value: datetime) -> str:  # type: ignore
        if is_utc(value):
            return value.strftime('%Y%m%dT%H%M%SZ')
        else:
            return value.strftime('%Y%m%dT%H%M%S')

    def parse(self, value: str, param_tz: Optional[str] = None, available_tz: OptionalTZDict = None) -> datetime:  # type: ignore
        # TODO pass and handle available_tz
        fixed_utc = (value[-1].upper() == 'Z')

        value = value.translate({
            ord("/"): "",
            ord("-"): "",
            ord("Z"): "",
            ord("z"): ""})
        dt = datetime.strptime(value, self.FORMATS[len(value)])

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


class DatetimeConverter(DatetimeConverterMixin, ValueConverter[datetime]):
    FORMATS = {
        **DatetimeConverterMixin.FORMATS,
        11: "%Y%m%dT%H",
        13: "%Y%m%dT%H%M",
        15: "%Y%m%dT%H%M%S"
    }

    @property
    def ics_type(self) -> str:
        return "DATE-TIME"

    @property
    def python_type(self) -> Type[datetime]:
        return datetime


class DateConverter(DatetimeConverterMixin, ValueConverter[date]):
    @property
    def ics_type(self) -> str:
        return "DATE"

    @property
    def python_type(self) -> Type[date]:
        return date

    def serialize(self, value):
        return value.strftime('%Y%m%d')

    def parse(self, *args, **kwargs):
        return super().parse(*args, **kwargs).date()


class TimeConverter(DatetimeConverterMixin, ValueConverter[time]):
    FORMATS = {
        2: "%H",
        4: "%H%M",
        6: "%H%M%S"
    }

    @property
    def ics_type(self) -> str:
        return "TIME"

    @property
    def python_type(self) -> Type[time]:
        return time

    def serialize(self, value):
        return value.strftime('%H%M%S')

    def parse(self, *args, **kwargs):
        return super().parse(*args, **kwargs).timetz()


class UTCOffsetConverter(ValueConverter[UTCOffset]):
    @property
    def ics_type(self) -> str:
        return "UTC-OFFSET"

    @property
    def python_type(self) -> Type[UTCOffset]:
        return UTCOffset

    def parse(self, value: str) -> UTCOffset:
        match = re.fullmatch(r"(?P<sign>\+|-|)(?P<hours>[0-9]{2})(?P<minutes>[0-9]{2})(?P<seconds>[0-9]{2})?", value)
        if not match:
            raise ValueError("value '%s' is not a valid UTCOffset")
        groups = match.groupdict()
        sign = groups.pop("sign")
        td = timedelta(**{k: int(v) for k, v in groups.items() if v})
        if sign == "-":
            td *= -1
        return UTCOffset(value, td)

    def serialize(self, value: UTCOffset) -> str:
        offset = value.utcoffset(None)
        assert offset is not None
        seconds = offset.seconds
        if seconds < 0:
            res = "-"
        else:
            res = "+"

        # hours
        res += '%02d' % (seconds // 3600)
        seconds %= 3600

        # minutes
        res += '%02d' % (seconds // 60)
        seconds %= 60

        if seconds:
            # seconds
            res += '%02d' % seconds

        return res


class DurationConverter(ValueConverter[timedelta]):
    @property
    def ics_type(self) -> str:
        return "DURATION"

    @property
    def python_type(self) -> Type[timedelta]:
        return timedelta

    def parse(self, value: str) -> timedelta:
        DAYS = {'D': 1, 'W': 7}
        SECS = {'S': 1, 'M': 60, 'H': 3600}

        sign, i = 1, 0
        if value[i] in '-+':
            if value[i] == '-':
                sign = -1
            i += 1
        if value[i] != 'P':
            raise ValueError("Error while parsing %s" % value)
        i += 1
        days, secs = 0, 0
        while i < len(value):
            if value[i] == 'T':
                i += 1
                if i == len(value):
                    break
            j = i
            while value[j].isdigit():
                j += 1
            if i == j:
                raise ValueError("Error while parsing %s" % value)
            val = int(value[i:j])
            if value[j] in DAYS:
                days += val * DAYS[value[j]]
                DAYS.pop(value[j])
            elif value[j] in SECS:
                secs += val * SECS[value[j]]
                SECS.pop(value[j])
            else:
                raise ValueError("Error while parsing %s" % value)
            i = j + 1
        return timedelta(sign * days, sign * secs)

    def serialize(self, value: timedelta) -> str:
        ONE_DAY_IN_SECS = 3600 * 24
        total = abs(int(value.total_seconds()))
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
        if value.total_seconds() >= 0:
            return 'P' + res
        else:
            return '-P%s' % res


class PeriodConverter(DatetimeConverterMixin, ValueConverter[Timespan]):

    @property
    def ics_type(self) -> str:
        return "PERIOD"

    @property
    def python_type(self) -> Type[Timespan]:
        return Timespan

    def parse(self, value: str, *args, **kwargs):
        start, sep, end = value.partition("/")
        if not sep:
            raise ValueError("PERIOD '%s' must contain the separator '/'")
        if end.startswith("P"):  # period-start = date-time "/" dur-value
            return Timespan(begin_time=ensure_datetime(super(PeriodConverter, self).parse(start, *args, **kwargs)),
                            duration=DurationConverter.INST.parse(end))
        else:  # period-explicit = date-time "/" date-time
            return Timespan(begin_time=ensure_datetime(super(PeriodConverter, self).parse(start, *args, **kwargs)),
                            end_time=ensure_datetime(super(PeriodConverter, self).parse(end, *args, **kwargs)))

    def serialize(self, value: Timespan) -> str:  # type: ignore
        begin = value.get_begin()
        if begin is None:
            raise ValueError("PERIOD must have a begin timestamp")
        if value.get_end_representation() == "duration":
            return "%s/%s" % (
                super(PeriodConverter, self).serialize(begin),
                DurationConverter.INST.serialize(cast(timedelta, value.get_effective_duration()))
            )
        else:
            end = value.get_effective_end()
            if end is None:
                raise ValueError("PERIOD must have a end timestamp")
            return "%s/%s" % (
                super(PeriodConverter, self).serialize(begin),
                super(PeriodConverter, self).serialize(end)
            )
