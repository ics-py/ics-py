import functools
from datetime import date, datetime, timedelta, tzinfo as TZInfo
from enum import Enum
from typing import Any, Dict, Optional, Tuple, Union, overload

import attr
from attr.validators import instance_of, optional as v_optional

from ics.types import TimespanOrBegin
from ics.utils import TIMEDELTA_CACHE, ceil_datetime_to_midnight, ensure_datetime, floor_datetime_to_midnight, timedelta_nearly_zero


class NormalizeIgnore(Enum):
    ONLY_FLOATING = 1
    ONLY_WITH_TZ = 2


Normalization = Union[TZInfo, None, NormalizeIgnore]
TimespanTuple = Tuple[datetime, datetime]
NullableTimespanTuple = Tuple[Optional[datetime], Optional[datetime]]
CMP_DATETIME_NONE_DEFAULT = datetime.min


@overload
def normalize(value: "Timespan", normalization: Normalization) -> "Timespan": ...


@overload
def normalize(value: Union[Tuple, Dict, datetime, date], normalization: Normalization) -> datetime: ...


@overload
def normalize(value: None, normalization: Normalization) -> None: ...


def normalize(value, normalization):
    """
    Normalize datetime or timespan instances to make naive/floating ones (without timezone, i.e. tzinfo == None)
    comparable to aware ones with a fixed timezone.
    The options from NormalizeIgnore will lead to the ignored type being converted to None.
    If None is selected as normalization, the timezone information will be stripped from aware datetimes.
    If the normalization is set to any tzinfo instance, naive datetimes will be interpreted in that timezone.
    """
    if not isinstance(value, Timespan):
        value = ensure_datetime(value)
        floating = (value.tzinfo is None)
        replace_timezone = lambda value, tzinfo: value.replace(tzinfo=tzinfo)
    else:
        floating = value.is_floating()
        replace_timezone = Timespan.replace_timezone

    if floating:
        if normalization is NormalizeIgnore.ONLY_FLOATING:
            return value
        elif normalization is NormalizeIgnore.ONLY_WITH_TZ:
            return None
        elif normalization is None:
            return value
        else:
            return replace_timezone(value, normalization)
    else:
        if normalization is NormalizeIgnore.ONLY_FLOATING:
            return None
        elif normalization is NormalizeIgnore.ONLY_WITH_TZ:
            return value
        elif normalization is None:
            return replace_timezone(value, normalization)
        else:
            return value


@functools.total_ordering
@attr.s(slots=True, frozen=True, eq=True, order=False)
class Timespan(object):
    begin_time: Optional[datetime] = attr.ib(validator=v_optional(instance_of(datetime)), default=None)
    end_time: Optional[datetime] = attr.ib(validator=v_optional(instance_of(datetime)), default=None)
    duration: Optional[timedelta] = attr.ib(validator=v_optional(instance_of(timedelta)), default=None)
    precision: str = attr.ib(default="second")

    def _end_name(self) -> str:
        raise NotImplementedError()

    def __attrs_post_init__(self):
        self.validate()

    def replace(
            self,
            begin_time: Optional[datetime] = False,  # type: ignore
            end_time: Optional[datetime] = False,  # type: ignore
            duration: Optional[timedelta] = False,  # type: ignore
            precision: str = False  # type: ignore
    ) -> "Timespan":
        if begin_time is False:
            begin_time = self.begin_time
        if end_time is False:
            end_time = self.end_time
        if duration is False:
            duration = self.duration
        if precision is False:
            precision = self.precision
        return type(self)(begin_time=begin_time, end_time=end_time, duration=duration, precision=precision)

    def replace_timezone(self: "Timespan", tzinfo: Optional[TZInfo]) -> "Timespan":
        if self.is_all_day():
            raise ValueError("can't replace timezone of all-day event")
        begin = self.get_begin()
        if begin is not None:
            begin = begin.replace(tzinfo=tzinfo)
        if self.end_time is not None:
            return self.replace(begin_time=begin, end_time=self.end_time.replace(tzinfo=tzinfo))
        else:
            return self.replace(begin_time=begin)

    def convert_timezone(self, tzinfo: Optional[TZInfo]) -> "Timespan":
        if self.is_all_day():
            raise ValueError("can't convert timezone of all-day timespan")
        if self.is_floating():
            raise ValueError("can't convert timezone of timezone-naive floating timespan, use replace_timezone")
        begin = self.get_begin()
        if begin is not None:
            begin = begin.astimezone(tzinfo)
        if self.end_time is not None:
            return self.replace(begin_time=begin, end_time=self.end_time.astimezone(tzinfo))
        else:
            return self.replace(begin_time=begin)

    def normalize(self, normalization: Normalization) -> "Timespan":
        return normalize(self, normalization)

    def validate(self):
        def validate_timeprecision(value, name):
            if self.precision == "day":
                if floor_datetime_to_midnight(value) != value:
                    raise ValueError("%s time value %s has higher precision than set precision %s" % (name, value, self.precision))
                if value.tzinfo is not None:
                    raise ValueError("all-day timespan %s time %s can't have a timezone" % (name, value))

        if self.begin_time is not None:
            validate_timeprecision(self.begin_time, "begin")

            if self.end_time is not None:
                validate_timeprecision(self.end_time, self._end_name())
                if self.begin_time > self.end_time:
                    raise ValueError("begin time must be before " + self._end_name() + " time")
                if self.precision == "day" and self.end_time < (self.begin_time + TIMEDELTA_CACHE["day"]):
                    raise ValueError("all-day timespan duration must be at least one day")
                if self.duration is not None:
                    raise ValueError("can't set duration together with " + self._end_name() + " time")
                if self.begin_time.tzinfo is None and self.end_time.tzinfo is not None:
                    raise ValueError(self._end_name() + " time may not have a timezone as the begin time doesn't either")
                if self.begin_time.tzinfo is not None and self.end_time.tzinfo is None:
                    raise ValueError(self._end_name() + " time must have a timezone as the begin time also does")
                if not timedelta_nearly_zero(self.get_effective_duration() % TIMEDELTA_CACHE[self.precision]):
                    raise ValueError("effective duration value %s has higher precision than set precision %s" %
                                     (self.get_effective_duration(), self.precision))

            if self.duration is not None:
                if self.duration < TIMEDELTA_CACHE[0]:
                    raise ValueError("timespan duration must be positive")
                if self.precision == "day" and self.duration < TIMEDELTA_CACHE["day"]:
                    raise ValueError("all-day timespan duration must be at least one day")
                if not timedelta_nearly_zero(self.duration % TIMEDELTA_CACHE[self.precision]):
                    raise ValueError("duration value %s has higher precision than set precision %s" %
                                     (self.duration, self.precision))

        else:
            if self.end_time is not None:
                # Todos might have end/due time without begin
                validate_timeprecision(self.end_time, self._end_name())

            if self.duration is not None:
                raise ValueError("timespan without begin time can't have duration")

    def get_str_segments(self):
        if self.is_all_day():
            prefix = ["all-day"]
        elif self.is_floating():
            prefix = ["floating"]
        else:
            prefix = []

        suffix = []

        begin = self.begin_time
        if begin is not None:
            suffix.append("begin:")
            if self.is_all_day():
                suffix.append(begin.strftime('%Y-%m-%d'))
            else:
                suffix.append(str(begin))

        end = self.get_effective_end()
        end_repr = self.get_end_representation()
        if end is not None:
            if end_repr == "end":
                suffix.append("fixed")
            suffix.append(self._end_name() + ":")
            if self.is_all_day():
                suffix.append(end.strftime('%Y-%m-%d'))
            else:
                suffix.append(str(end))

        duration = self.get_effective_duration()
        if duration is not None and end_repr is not None:
            if end_repr == "duration":
                suffix.append("fixed")
            suffix.append("duration:")
            suffix.append(str(duration))

        return prefix, [self.__class__.__name__], suffix

    def __str__(self) -> str:
        prefix, name, suffix = self.get_str_segments()
        return "<%s>" % (" ".join(prefix + name + suffix))

    def __bool__(self):
        return self.begin_time is not None or self.end_time is not None

    ####################################################################################################################

    def make_all_day(self) -> "Timespan":
        if self.is_all_day():
            return self  # Do nothing if we already are a all day timespan

        begin = self.begin_time
        if begin is not None:
            begin = floor_datetime_to_midnight(begin).replace(tzinfo=None)

        end = self.get_effective_end()
        if end is not None:
            end = ceil_datetime_to_midnight(end).replace(tzinfo=None)
            if end == begin:  # we also add another day if the duration would be 0 otherwise
                end = end + TIMEDELTA_CACHE["day"]

        if self.get_end_representation() == "duration":
            assert end is not None
            return self.replace(begin, None, end - begin, "day")
        else:
            return self.replace(begin, end, None, "day")

    def convert_end(self, target: Optional[str]) -> "Timespan":
        current = self.get_end_representation()
        current_is_end = current == "end" or current == self._end_name()
        target_is_end = target == "end" or target == self._end_name()
        if current == target or (current_is_end and target_is_end):
            return self
        elif current_is_end and target == "duration":
            return self.replace(end_time=None, duration=self.get_effective_duration())
        elif current == "duration" and target_is_end:
            return self.replace(end_time=self.get_effective_end(), duration=None)
        elif target is None:
            return self.replace(end_time=None, duration=None)
        else:
            raise ValueError("can't convert from representation %s to %s" % (current, target))

    ####################################################################################################################

    def get_begin(self) -> Optional[datetime]:
        return self.begin_time

    def get_effective_end(self) -> Optional[datetime]:
        if self.end_time is not None:
            return self.end_time
        elif self.begin_time is not None:
            duration = self.get_effective_duration()
            if duration is not None:
                return self.begin_time + duration

        return None

    def get_effective_duration(self) -> Optional[timedelta]:
        if self.duration is not None:
            return self.duration
        elif self.end_time is not None and self.begin_time is not None:
            return self.end_time - self.begin_time
        else:
            return None

    def get_precision(self) -> str:
        return self.precision

    def is_all_day(self) -> bool:
        return self.precision == "day"

    def is_floating(self) -> bool:
        if self.begin_time is None:
            if self.end_time is None:
                return True
            else:
                return self.end_time.tzinfo is None
        else:
            return self.begin_time.tzinfo is None

    def get_end_representation(self) -> Optional[str]:
        if self.duration is not None:
            return "duration"
        elif self.end_time is not None:
            return "end"
        else:
            return None

    def has_explicit_end(self) -> bool:
        return self.get_end_representation() is not None

    ####################################################################################################################

    @overload
    def timespan_tuple(self, default: None = None) -> NullableTimespanTuple:
        ...

    @overload
    def timespan_tuple(self, default: datetime) -> TimespanTuple:
        ...

    def timespan_tuple(self, default=None):
        # Tuple[datetime, None] is not possible as duration defaults to 0s or 1d as soon as begin time is not None
        return self.get_begin() or default, self.get_effective_end() or default

    def __normalize_timespans(self, second: "Timespan") -> Tuple["Timespan", "Timespan"]:
        """
        Normalize this timespan to allow comparision with the given second timespan.
        If one of the timespans is naive/floating (without timezone, i.e. tzinfo == None) and the other one is aware
        with a fixed timezone, the timezone information will be stripped from the aware instance.
        This is similar to calling `normalize` with `normalization=None` if both are not already directly comparable.
        """
        if not isinstance(second, Timespan):
            raise NotImplementedError("cannot compare %s and %s as timespans" % (type(self), type(second)))
        first = self
        if not first or not second:
            # also includes timespan.begin is None
            return first, second
        assert first.get_begin() is not None \
               and first.get_effective_end() is not None \
               and second.get_begin() is not None \
               and second.get_effective_end() is not None
        if first.is_floating() != second.is_floating():
            if not first.is_floating():
                first = first.replace_timezone(None)
                assert first.is_floating()
            else:
                assert not second.is_floating()
                second = second.replace_timezone(None)
                assert second.is_floating()
        assert first.is_floating() == second.is_floating()
        return first, second

    def __normalize_datetime(self, second: datetime) -> Tuple["Timespan", datetime]:
        """
        Normalize this timespan to allow comparision with the given second datetime.
        If this instance is naive/floating (without timezone, i.e. tzinfo == None) and the datetime is aware
        with a fixed timezone, the timezone information will be stripped from the aware datetime instance.
        This is similar to calling `normalize` with `normalization=None` if both are not already directly comparable.
        """
        if not isinstance(second, datetime):
            raise NotImplementedError("cannot compare %s and %s as timespans/datetime" % (type(self), type(second)))
        if self and self.is_floating() and second.tzinfo is not None:
            second = second.replace(tzinfo=None)
        return self, second

    def starts_within(self, second: "Timespan") -> bool:
        first, second = self.__normalize_timespans(second)

        if first.begin_time is None:
            raise ValueError("first timespan %s has no begin time" % first)

        if second.begin_time is None:
            raise ValueError("second timespan %s has no begin time" % second)
        second_end = second.get_effective_end()
        if second_end is None:
            raise ValueError("second timespan %s has no " + self._end_name() + " time" % second)

        # the timespan doesn't include its end instant / day
        return second.begin_time <= first.begin_time < second_end

    def ends_within(self, second: "Timespan") -> bool:
        first, second = self.__normalize_timespans(second)

        first_end = first.get_effective_end()
        if first_end is None:
            raise ValueError("first timespan %s has no " + self._end_name() + " time" % first)

        if second.begin_time is None:
            raise ValueError("second timespan %s has no begin time" % second)
        second_end = second.get_effective_end()
        if second_end is None:
            raise ValueError("second timespan %s has no " + self._end_name() + " time" % second)

        # the timespan doesn't include its end instant / day
        return second.begin_time <= first_end < second_end

    def intersects(self, second: "Timespan") -> bool:
        first, second = self.__normalize_timespans(second)
        return (first.starts_within(second) or first.ends_within(second) or
                second.starts_within(first) or second.ends_within(first))

    def includes(self, second: Union["Timespan", datetime]) -> bool:
        if isinstance(second, datetime):
            first, second = self.__normalize_datetime(second)

            if first.begin_time is None:
                raise ValueError("first timespan %s has no begin time" % first)
            first_end = first.get_effective_end()
            if first_end is None:
                raise ValueError("first timespan %s has no " + self._end_name() + " time" % first)

            # the timespan doesn't include its end instant / day
            return first.begin_time <= second < first_end

        first, second = self.__normalize_timespans(second)
        return second.starts_within(first) and second.ends_within(first)

    __contains__ = includes

    def is_included_in(self, second: "Timespan") -> bool:
        return second.includes(self)

    @overload
    def cmp_tuples(self, second: TimespanOrBegin, default: None = None) -> Tuple[NullableTimespanTuple, NullableTimespanTuple]:
        ...

    @overload
    def cmp_tuples(self, second: TimespanOrBegin, default: datetime) -> Tuple[TimespanTuple, TimespanTuple]:
        ...

    @overload
    def cmp_tuples(self, second: Any, default: Any = None) -> None:
        ...

    def cmp_tuples(self, second: Any, default=None):
        if isinstance(second, datetime):
            first, second = self.__normalize_datetime(second)
            return first.timespan_tuple(default=default), \
                   (second, default)
        elif isinstance(second, Timespan):
            first, second = self.__normalize_timespans(second)
            return first.timespan_tuple(default=default), \
                   second.timespan_tuple(default=default)
        else:
            return None

    def __lt__(self, second: Any) -> bool:
        tuples = self.cmp_tuples(second, CMP_DATETIME_NONE_DEFAULT)
        if tuples is None:
            return NotImplemented
        else:
            return tuples[0] < tuples[1]

    def is_identical(self, second: "Timespan") -> bool:
        return isinstance(second, Timespan) and attr.astuple(self) == attr.astuple(second)

    def union(self, second: Union["Timespan", datetime]) -> "Timespan":
        """
        this will fail more often than work, mostly due to non-compatible is_floating and is_all_day values
        """
        if isinstance(second, datetime):
            return self.replace(begin_time=min(self.get_begin(), second),
                                end_time=max(self.get_effective_end(), second))
        else:
            return self.replace(begin_time=min(self.get_begin(), second.get_begin()),
                                end_time=max(self.get_effective_end(), second.get_effective_end()))


class EventTimespan(Timespan):
    def _end_name(self):
        return "end"

    def validate(self):
        super(EventTimespan, self).validate()
        if self.begin_time is None and self.end_time is not None:
            raise ValueError("event timespan without begin time can't have end time")

    def get_effective_duration(self) -> timedelta:
        if self.duration is not None:
            return self.duration
        elif self.end_time is not None and self.begin_time is not None:
            return self.end_time - self.begin_time
        elif self.is_all_day():
            return TIMEDELTA_CACHE["day"]
        else:
            return TIMEDELTA_CACHE[0]


class TodoTimespan(Timespan):
    def _end_name(self):
        return "due"
