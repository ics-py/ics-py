from datetime import datetime, time, timedelta
from typing import NamedTuple, Optional, Tuple, Union

MIDNIGHT = time()
TIMEDELTA_CACHE = {
    0: timedelta(),
    "day": timedelta(days=1),
    "second": timedelta(seconds=1)
}


def floor_datetime_to_midnight(value: datetime):
    return datetime.combine(value.date(), MIDNIGHT, tzinfo=value.tzinfo)


def ceil_datetime_to_midnight(value: datetime):
    floored = floor_datetime_to_midnight(value)
    if floored != value:
        return floored + TIMEDELTA_CACHE["day"]
    else:
        return floored


def floor_timedelta_to_days(value):
    return value - (value % TIMEDELTA_CACHE["day"])


def ceil_timedelta_to_days(value):
    mod = value % TIMEDELTA_CACHE["day"]
    if mod == TIMEDELTA_CACHE[0]:
        return value
    else:
        return value + TIMEDELTA_CACHE["day"] - mod


class _Timespan(NamedTuple):
    begin_time: datetime
    end_time: datetime
    duration: timedelta
    precision: str


class Timespan(_Timespan):
    __slots__ = ()

    def __new__(cls, begin_time: Optional[datetime] = None, end_time: Optional[datetime] = None,
                duration: Optional[timedelta] = None, precision: str = "second"):
        if begin_time is not None and not isinstance(begin_time, datetime):
            raise ValueError("begin_time must be a datetime, not %s" % (type(begin_time),))
        if end_time is not None and not isinstance(end_time, datetime):
            raise ValueError("end_time must be a datetime, not %s" % (type(end_time),))
        if duration is not None and not isinstance(duration, timedelta):
            raise ValueError("duration must be a timedelta, not %s" % (type(duration),))
        if precision not in ("day", "second"):
            raise ValueError("illegal precision value '%s'" % (precision,))

        self = super(Timespan, cls).__new__(cls, begin_time, end_time, duration, precision)
        self.validate()
        return self

    def replace(self, begin_time: Union[bool, Optional[datetime]] = False, end_time: Union[bool, Optional[datetime]] = False,
                duration: Union[bool, Optional[timedelta]] = False, precision: Union[bool, str] = False) -> "Timespan":
        if begin_time is False:
            begin_time = self.begin_time
        if end_time is False:
            end_time = self.end_time
        if duration is False:
            duration = self.duration
        if precision is False:
            precision = self.precision
        return type(self)(begin_time=begin_time, end_time=end_time, duration=duration, precision=precision)

    def replace_timezone(self, tzinfo) -> "Timespan":
        if self.is_all_day():
            raise ValueError("can't replace timezone of all-day event")
        if self.get_begin() is None:
            return self
        begin = self.get_begin().replace(tzinfo=tzinfo)
        if self.end_time:
            return self.replace(begin_time=begin, end_time=self.end_time.replace(tzinfo=tzinfo))
        else:
            return self.replace(begin_time=begin)

    def convert_timezone(self, tzinfo) -> "Timespan":
        if self.is_all_day():
            raise ValueError("can't convert timezone of all-day event")
        if self.is_floating():
            raise ValueError("can't convert timezone of timezone-naive floating event, use replace_timezone")
        if self.get_begin() is None:
            return self
        begin = self.get_begin().astimezone(tzinfo)
        if self.end_time:
            return self.replace(begin_time=begin, end_time=self.end_time.astimezone(tzinfo))
        else:
            return self.replace(begin_time=begin)

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
                if self.precision is not None and self.get_effective_duration() % TIMEDELTA_CACHE[self.precision] != TIMEDELTA_CACHE[0]:
                    raise ValueError("effective duration value %s has higher precision than set precision %s" %
                                     (self.get_effective_duration(), self.precision))

            if self.duration is not None:
                if self.duration < TIMEDELTA_CACHE[0]:
                    raise ValueError("event duration must be positive")
                if self.precision == "day" and self.duration < TIMEDELTA_CACHE["day"]:
                    raise ValueError("all-day event duration must be at least one day")
                if self.precision is not None and self.duration % TIMEDELTA_CACHE[self.precision] != TIMEDELTA_CACHE[0]:
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
        if self.get_begin():
            suffix.append("begin:")
            if self.is_all_day():
                suffix.append(self.get_begin().strftime('%Y-%m-%d'))
            else:
                suffix.append(str(self.get_begin()))
        if self.has_end():
            if self.get_end_representation() == "end":
                suffix.append("fixed")
            suffix.append("end:")
            if self.is_all_day():
                suffix.append(self.get_effective_end().strftime('%Y-%m-%d'))
            else:
                suffix.append(str(self.get_effective_end()))
            if self.get_end_representation() == "duration":
                suffix.append("fixed")
            suffix.append("duration:")
            suffix.append(str(self.duration))

        return prefix, [self.__class__.__name__], suffix

    def __str__(self) -> str:
        prefix, name, suffix = self.get_str_segments()
        return "<%s>" % (" ".join(prefix + name + suffix))

    ####################################################################################################################

    def make_all_day(self) -> "Timespan":
        if self.is_all_day():
            return self  # Do nothing if we already are a all day event
        if self.get_begin() is None:
            return self.replace(None, None, None, "day")

        begin = floor_datetime_to_midnight(self.get_begin()).replace(tzinfo=None)

        old_end = self.get_effective_end()
        end = None
        if self.get_end_representation() is not None:
            end = ceil_datetime_to_midnight(old_end).replace(tzinfo=None)
            if end == begin:  # we also add another day if the duration would be 0 otherwise
                end = end + TIMEDELTA_CACHE["day"]

        if self.get_end_representation() == "duration":
            return self.replace(begin, None, end - begin, "day")
        else:
            return self.replace(begin, end, None, "day")

    def convert_end(self, representation) -> "Timespan":
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
        return self.begin_time.tzinfo is None

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

    def __normalize_timespans(self, second: "Timespan") -> Tuple["Timespan", "Timespan"]:
        if not isinstance(self, Timespan) or not isinstance(second, Timespan):
            raise NotImplementedError("cannot compare %s and %s as timespans" % (type(self), type(second)))
        first = self
        if first.is_floating() != second.is_floating():
            # TODO check whether converting to floating is okay or whether we should convert to the given timezon
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
        if not isinstance(self, Timespan) or not isinstance(second, datetime):
            raise NotImplementedError("cannot compare %s and %s as timespans/datetime" % (type(self), type(second)))
        if self.is_floating() and second.tzinfo is not None:
            second = second.replace(tzinfo=None)
        return self, second

    def starts_within(self, second: "Timespan") -> bool:
        first, second = self.__normalize_timespans(second)
        # the event doesn't include its end instant / day
        return second.get_begin() <= first.get_begin() < second.get_effective_end()

    def ends_within(self, second: "Timespan") -> bool:
        first, second = self.__normalize_timespans(second)
        # the event doesn't include its end instant / day
        return second.get_begin() <= first.get_effective_end() < second.get_effective_end()

    def intersects(self, second: "Timespan") -> bool:
        first, second = self.__normalize_timespans(second)
        return (first.starts_within(second) or first.ends_within(second) or
                second.starts_within(first) or second.ends_within(first))

    def includes(self, second: Union["Timespan", datetime]) -> bool:
        if isinstance(second, datetime):
            first, second = self.__normalize_datetime(second)
            # the event doesn't include its end instant / day
            return first.get_begin() <= second < first.get_effective_end()

        first, second = self.__normalize_timespans(second)
        return second.starts_within(first) and second.ends_within(first)

    def is_included_in(self, second: "Timespan") -> bool:
        return second.includes(self)

    def compare(self, extract_dt, op, second: Union["Timespan", datetime]) -> bool:
        if isinstance(second, datetime):
            first, second = self.__normalize_datetime(second)
            return op(extract_dt(first), second)
        else:
            first, second = self.__normalize_timespans(second)
            return op(extract_dt(first), extract_dt(second))

    def __lt__(self, second: Union["Timespan", datetime]) -> bool:
        if isinstance(second, datetime):
            first, second = self.__normalize_datetime(second)
            # the event doesn't include its end instant / day, so we are less even if they are the same
            return first.get_effective_end() <= second
        elif isinstance(second, Timespan):
            first, second = self.__normalize_timespans(second)
            return first.get_begin() < second.get_begin() or (
                    first.get_begin() == second.get_begin() and
                    first.get_effective_end() < second.get_effective_end()
            )
        else:
            return NotImplemented

    def __le__(self, second: Union["Timespan", datetime]) -> bool:
        if isinstance(second, datetime):
            first, second = self.__normalize_datetime(second)
            return first.get_effective_end() <= second or first.includes(second)
        elif isinstance(second, Timespan):
            first, second = self.__normalize_timespans(second)
            return first.get_begin() < second.get_begin() or (
                    first.get_begin() == second.get_begin() and
                    first.get_effective_end() <= second.get_effective_end()
            )
        else:
            return NotImplemented

    def __gt__(self, second: Union["Timespan", datetime]) -> bool:
        if isinstance(second, datetime):
            first, second = self.__normalize_datetime(second)
            return first.get_begin() > second
        elif isinstance(second, Timespan):
            first, second = self.__normalize_timespans(second)
            return first.get_begin() > second.get_begin() or (
                    first.get_begin() == second.get_begin() and
                    first.get_effective_end() > second.get_effective_end()
            )
        else:
            return NotImplemented

    def __ge__(self, second: Union["Timespan", datetime]) -> bool:
        if isinstance(second, datetime):
            first, second = self.__normalize_datetime(second)
            return first.get_begin() >= second or first.includes(second)
        elif isinstance(second, Timespan):
            first, second = self.__normalize_timespans(second)
            return first.get_begin() > second.get_begin() or (
                    first.get_begin() == second.get_begin() and
                    first.get_effective_end() >= second.get_effective_end()
            )
        else:
            return NotImplemented

    def __eq__(self, o: object) -> bool:
        return super(Timespan, self).__eq__(o)

    def same_timespan(self, second: "Timespan") -> bool:
        first, second = self.__normalize_timespans(second)
        return first.get_begin() == second.get_begin() and first.get_effective_end() == second.get_effective_end()

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
