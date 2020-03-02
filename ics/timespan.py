import functools
from datetime import date, datetime, timedelta, tzinfo as TZInfo
from enum import Enum
from typing import Any, Dict, Optional, Tuple, Union, cast, overload

import attr
from attr.validators import instance_of, optional as v_optional

from ics.utils import TIMEDELTA_CACHE, ceil_datetime_to_midnight, ensure_datetime, floor_datetime_to_midnight, timedelta_nearly_zero

CMP_DATETIME_NONE_DEFAULT = datetime.min


class NormalizeIgnore(Enum):
    ONLY_FLOATING = 1
    ONLY_WITH_TZ = 2


Normalization = Union[TZInfo, None, NormalizeIgnore]


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


@attr.s(slots=True, frozen=True, cmp=False)
@functools.total_ordering
class Timespan(object):
    begin_time: Optional[datetime] = attr.ib(validator=v_optional(instance_of(datetime)), default=None)
    end_time: Optional[datetime] = attr.ib(validator=v_optional(instance_of(datetime)), default=None)
    duration: Optional[timedelta] = attr.ib(validator=v_optional(instance_of(timedelta)), default=None)
    precision: str = attr.ib(default="second")

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
        if begin is None:
            return self
        begin = begin.replace(tzinfo=tzinfo)
        if self.end_time:
            return self.replace(begin_time=begin, end_time=self.end_time.replace(tzinfo=tzinfo))
        else:
            return self.replace(begin_time=begin)

    def convert_timezone(self, tzinfo: Optional[TZInfo]) -> "Timespan":
        if self.is_all_day():
            raise ValueError("can't convert timezone of all-day event")
        if self.is_floating():
            raise ValueError("can't convert timezone of timezone-naive floating event, use replace_timezone")
        begin = self.get_begin()
        if begin is None:
            return self
        begin = begin.astimezone(tzinfo)
        if self.end_time:
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
                    raise ValueError("all-day event %s time %s can't have a timezone" % (name, value))

        if self.begin_time is not None:
            validate_timeprecision(self.begin_time, "begin")

            if self.end_time is not None:
                validate_timeprecision(self.end_time, "end")
                if self.begin_time > self.end_time:
                    raise ValueError("begin time must be before end time")
                if self.precision == "day" and self.end_time < (self.begin_time + TIMEDELTA_CACHE["day"]):
                    raise ValueError("all-day event duration must be at least one day")
                if self.duration is not None:
                    raise ValueError("can't set duration together with end time")
                if self.begin_time.tzinfo is None and self.end_time.tzinfo is not None:
                    raise ValueError("end time may not have a timezone as the begin time doesn't either")
                if self.begin_time.tzinfo is not None and self.end_time.tzinfo is None:
                    raise ValueError("end time must have a timezone as the begin time also does")
                if not timedelta_nearly_zero(self.get_effective_duration() % TIMEDELTA_CACHE[self.precision]):
                    raise ValueError("effective duration value %s has higher precision than set precision %s" %
                                     (self.get_effective_duration(), self.precision))

            if self.duration is not None:
                if self.duration < TIMEDELTA_CACHE[0]:
                    raise ValueError("event duration must be positive")
                if self.precision == "day" and self.duration < TIMEDELTA_CACHE["day"]:
                    raise ValueError("all-day event duration must be at least one day")
                if not timedelta_nearly_zero(self.duration % TIMEDELTA_CACHE[self.precision]):
                    raise ValueError("duration value %s has higher precision than set precision %s" %
                                     (self.duration, self.precision))

        else:
            if self.end_time is not None:
                raise ValueError("event without begin time can't have end time")
            if self.duration is not None:
                raise ValueError("event without begin time can't have duration")

    def get_str_segments(self):
        if self.is_all_day():
            prefix = ["all-day"]
        elif self.is_floating():
            prefix = ["floating"]
        else:
            prefix = []

        suffix = []
        if self.begin_time:
            suffix.append("begin:")
            if self.is_all_day():
                suffix.append(self.begin_time.strftime('%Y-%m-%d'))
            else:
                suffix.append(str(self.begin_time))
        if self.has_end():
            if self.get_end_representation() == "end":
                suffix.append("fixed")
            suffix.append("end:")
            end = cast(datetime, self.get_effective_end())
            if self.is_all_day():
                suffix.append(end.strftime('%Y-%m-%d'))
            else:
                suffix.append(str(end))
            if self.get_end_representation() == "duration":
                suffix.append("fixed")
            suffix.append("duration:")
            suffix.append(str(self.duration))

        return prefix, [self.__class__.__name__], suffix

    def __str__(self) -> str:
        prefix, name, suffix = self.get_str_segments()
        return "<%s>" % (" ".join(prefix + name + suffix))

    def __bool__(self):
        return self.get_begin() is not None

    ####################################################################################################################

    def make_all_day(self) -> "Timespan":
        if self.is_all_day():
            return self  # Do nothing if we already are a all day event
        if self.begin_time is None:
            return self.replace(None, None, None, "day")

        begin = floor_datetime_to_midnight(self.begin_time).replace(tzinfo=None)

        old_end = self.get_effective_end()
        end = None
        if self.get_end_representation() is not None:
            old_end = cast(datetime, old_end)
            end = ceil_datetime_to_midnight(old_end).replace(tzinfo=None)
            if end == begin:  # we also add another day if the duration would be 0 otherwise
                end = end + TIMEDELTA_CACHE["day"]

        if self.get_end_representation() == "duration":
            assert end is not None
            return self.replace(begin, None, end - begin, "day")
        else:
            return self.replace(begin, end, None, "day")

    def convert_end(self, representation: Optional[str]) -> "Timespan":
        current = self.get_end_representation()
        if current == representation:
            return self
        elif current == "end" and representation == "duration":
            return self.replace(end_time=None, duration=self.get_effective_duration())
        elif current == "duration" and representation == "end":
            return self.replace(end_time=self.get_effective_end(), duration=None)
        elif representation is None:
            return self.replace(end_time=None, duration=None)
        else:
            raise ValueError("can't convert from representation %s to %s" % (current, representation))

    ####################################################################################################################

    def get_begin(self) -> Optional[datetime]:
        return self.begin_time

    def get_effective_end(self) -> Optional[datetime]:
        if self.end_time is not None:
            return self.end_time
        elif self.begin_time is not None:
            return self.begin_time + self.get_effective_duration()
        else:
            return None

    def get_effective_duration(self) -> timedelta:
        if self.duration is not None:
            return self.duration
        elif self.end_time is not None and self.begin_time is not None:
            return self.end_time - self.begin_time
        elif self.is_all_day():
            return TIMEDELTA_CACHE["day"]
        else:
            return TIMEDELTA_CACHE[0]

    def get_precision(self) -> str:
        return self.precision

    def is_all_day(self) -> bool:
        return self.precision == "day"

    def is_floating(self) -> bool:
        return self.begin_time is None or self.begin_time.tzinfo is None

    def get_end_representation(self) -> Optional[str]:
        if self.duration is not None:
            return "duration"
        elif self.end_time is not None:
            return "end"
        else:
            return None

    def has_end(self) -> bool:
        return self.get_end_representation() is not None

    ####################################################################################################################

    @overload
    def timespan_tuple(self, default: None = None) -> Union[Tuple[None, None], Tuple[datetime, datetime]]:
        ...

    @overload
    def timespan_tuple(self, default: datetime) -> Tuple[datetime, datetime]:
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
            raise ValueError("first event %s has no begin time" % first)

        if second.begin_time is None:
            raise ValueError("second event %s has no begin time" % second)
        second_end = second.get_effective_end()
        if second_end is None:
            raise ValueError("second event %s has no end time" % second)

        # the event doesn't include its end instant / day
        return second.begin_time <= first.begin_time < second_end

    def ends_within(self, second: "Timespan") -> bool:
        first, second = self.__normalize_timespans(second)

        first_end = first.get_effective_end()
        if first_end is None:
            raise ValueError("first event %s has no end time" % first)

        if second.begin_time is None:
            raise ValueError("second event %s has no begin time" % second)
        second_end = second.get_effective_end()
        if second_end is None:
            raise ValueError("second event %s has no end time" % second)

        # the event doesn't include its end instant / day
        return second.begin_time <= first_end < second_end

    def intersects(self, second: "Timespan") -> bool:
        first, second = self.__normalize_timespans(second)
        return (first.starts_within(second) or first.ends_within(second) or
                second.starts_within(first) or second.ends_within(first))

    def includes(self, second: Union["Timespan", datetime]) -> bool:
        if isinstance(second, datetime):
            first, second = self.__normalize_datetime(second)

            if first.begin_time is None:
                raise ValueError("first event %s has no begin time" % first)
            first_end = first.get_effective_end()
            if first_end is None:
                raise ValueError("first event %s has no end time" % first)

            # the event doesn't include its end instant / day
            return first.begin_time <= second < first_end

        first, second = self.__normalize_timespans(second)
        return second.starts_within(first) and second.ends_within(first)

    __contains__ = includes

    def is_included_in(self, second: "Timespan") -> bool:
        return second.includes(self)

    def __lt__(self, second: Any) -> bool:
        if isinstance(second, datetime):
            first, second = self.__normalize_datetime(second)
            return first.timespan_tuple(default=CMP_DATETIME_NONE_DEFAULT) \
                   < (second, CMP_DATETIME_NONE_DEFAULT)
        elif isinstance(second, Timespan):
            first, second = self.__normalize_timespans(second)
            return first.timespan_tuple(default=CMP_DATETIME_NONE_DEFAULT) \
                   < second.timespan_tuple(default=CMP_DATETIME_NONE_DEFAULT)
        else:
            return NotImplemented

    def __eq__(self, second: Any) -> bool:
        if isinstance(second, datetime):
            first, second = self.__normalize_datetime(second)
            return (first.get_begin() or CMP_DATETIME_NONE_DEFAULT) \
                   == (second or CMP_DATETIME_NONE_DEFAULT)
        elif isinstance(second, Timespan):
            first, second = self.__normalize_timespans(second)
            return first.timespan_tuple(default=CMP_DATETIME_NONE_DEFAULT) \
                   == second.timespan_tuple(default=CMP_DATETIME_NONE_DEFAULT)
        else:
            return NotImplemented

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
