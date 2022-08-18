import warnings
from datetime import datetime, timedelta
from datetime import tzinfo as TZInfo
from enum import IntEnum
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    NamedTuple,
    Optional,
    TypeVar,
    Union,
    cast,
    overload,
)

import attr
from attr.validators import instance_of
from attr.validators import optional as v_optional
from dateutil.tz import tzlocal

from ics.types import DatetimeLike
from ics.utils import (
    TIMEDELTA_CACHE,
    TIMEDELTA_DAY,
    TIMEDELTA_ZERO,
    ceil_datetime_to_midnight,
    ensure_datetime,
    floor_datetime_to_midnight,
    timedelta_nearly_zero,
)

if TYPE_CHECKING:
    # Literal is new in python 3.8, but backported via typing_extensions
    # we don't need typing_extensions as actual (dev-)dependency as mypy has builtin support
    from typing_extensions import Literal

    # noinspection PyUnresolvedReferences
    from ics.event import CalendarEntryAttrs

CalendarEntryT = TypeVar("CalendarEntryT", bound="CalendarEntryAttrs")


class NormalizationAction(IntEnum):
    IGNORE = 0  # == False
    REPLACE = 1  # == True
    CONVERT = 2  # == True, default if True is passed


@attr.s
class Normalization:
    replacement: Union[TZInfo, Callable[[], TZInfo], None] = attr.ib()
    normalize_floating: Union[NormalizationAction, bool] = attr.ib(
        NormalizationAction.CONVERT
    )
    normalize_with_tz: Union[NormalizationAction, bool] = attr.ib(
        NormalizationAction.CONVERT
    )

    @overload
    def normalize(self, value: "Timespan") -> "Timespan":
        ...

    # pyflakes < 2.2 reports 'redefinition of unused' for overloaded class members
    @overload
    def normalize(self, value: DatetimeLike) -> datetime:
        ...

    @overload
    def normalize(self, value: CalendarEntryT) -> CalendarEntryT:
        ...

    @overload
    def normalize(self, value: None) -> None:
        ...

    def normalize(self, value):
        """
        Normalize datetime or timespan instances to make naive/floating ones (without timezone, i.e. tzinfo == None)
        comparable to aware ones with a fixed timezone.
        If None is selected as replacement, the timezone information will be stripped from aware datetimes.
        If the replacement is set to any tzinfo instance, naive datetimes will be interpreted in that timezone.
        """
        if value is None:
            return None
        elif isinstance(value, Timespan):
            floating = value.is_floating()
            replace_timezone = Timespan.replace_timezone
            convert_timezone = Timespan.convert_timezone
        elif (
            (hasattr(value, "is_floating") or hasattr(value, "floating"))
            and hasattr(value, "replace_timezone")
            and hasattr(value, "convert_timezone")
        ):
            if hasattr(value, "is_floating"):
                floating = value.is_floating()
            else:
                floating = value.floating

            def replace_timezone(value, tzinfo):
                value.replace_timezone(tzinfo=tzinfo)
                return value

            def convert_timezone(value, tzinfo):
                value.convert_timezone(tzinfo=tzinfo)
                return value

        else:
            value = ensure_datetime(value)
            floating = value.tzinfo is None
            replace_timezone = lambda value, tzinfo: value.replace(tzinfo=tzinfo)
            convert_timezone = lambda value, tzinfo: value.astimezone(tz=tzinfo)

        if floating and self.normalize_floating:
            action = (
                replace_timezone
                if self.normalize_floating is NormalizationAction.REPLACE
                else convert_timezone
            )
        elif not floating and self.normalize_with_tz:
            action = (
                replace_timezone
                if self.normalize_with_tz is NormalizationAction.REPLACE
                else convert_timezone
            )
        else:
            return value

        replacement = self.replacement
        if callable(replacement):
            replacement = replacement()
        return action(value, replacement)


# using datetime.min might lead to problems when doing timezone conversions / comparisions (e.g. by subtracting an 1 hour offset)
CMP_DATETIME_NONE_DEFAULT = datetime(1900, 1, 1, 0, 0)
CMP_NORMALIZATION = Normalization(
    normalize_floating=True, normalize_with_tz=False, replacement=tzlocal
)


class TimespanTuple(NamedTuple):
    begin: datetime
    end: datetime


class NullableTimespanTuple(NamedTuple):
    begin: Optional[datetime]
    end: Optional[datetime]


TimespanT = TypeVar("TimespanT", bound="Timespan")


@attr.s(slots=True, frozen=True, eq=True, order=False)
class Timespan:
    begin_time: Optional[datetime] = attr.ib(
        validator=v_optional(instance_of(datetime)), default=None
    )
    end_time: Optional[datetime] = attr.ib(
        validator=v_optional(instance_of(datetime)), default=None
    )
    duration: Optional[timedelta] = attr.ib(
        validator=v_optional(instance_of(timedelta)), default=None
    )
    precision: str = attr.ib(default="second")

    def _end_name(self) -> str:
        return "end"

    def __attrs_post_init__(self):
        self.validate()

    def replace(
        self: TimespanT,
        begin_time: Union[datetime, None, "Literal[False]"] = False,
        end_time: Union[datetime, None, "Literal[False]"] = False,
        duration: Union[timedelta, None, "Literal[False]"] = False,
        precision: Union[str, "Literal[False]"] = False,
    ) -> TimespanT:
        if begin_time is False:
            begin_time = self.begin_time
        if end_time is False:
            end_time = self.end_time
        if duration is False:
            duration = self.duration
        if precision is False:
            precision = self.precision
        return type(self)(
            begin_time=cast(Optional[datetime], begin_time),
            end_time=cast(Optional[datetime], end_time),
            duration=cast(Optional[timedelta], duration),
            precision=cast(str, precision),
        )

    def replace_timezone(self: TimespanT, tzinfo: Optional[TZInfo]) -> TimespanT:
        if self.is_all_day():
            raise ValueError("can't replace timezone of all-day event")
        begin = self.get_begin()
        if begin is not None:
            begin = begin.replace(tzinfo=tzinfo)
        if self.end_time is not None:
            return self.replace(
                begin_time=begin, end_time=self.end_time.replace(tzinfo=tzinfo)
            )
        else:
            return self.replace(begin_time=begin)

    def convert_timezone(self: TimespanT, tzinfo: Optional[TZInfo]) -> TimespanT:
        if self.is_all_day():
            raise ValueError("can't convert timezone of all-day timespan")
        if self.is_floating():
            warnings.warn(
                "interpreting missing timezone of timezone-naive floating timespan as local time for conversion, "
                "use replace_timezone for deterministic results"
            )
        begin = self.get_begin()
        if begin is not None:
            begin = begin.astimezone(tzinfo)
        if self.end_time is not None:
            return self.replace(
                begin_time=begin, end_time=self.end_time.astimezone(tzinfo)
            )
        else:
            return self.replace(begin_time=begin)

    def validate(self):
        def validate_timeprecision(value, name):
            if self.precision == "day":
                if floor_datetime_to_midnight(value) != value:
                    raise ValueError(
                        "{} time value {} has higher precision than set precision {}".format(
                            name, value, self.precision
                        )
                    )
                if value.tzinfo is not None:
                    raise ValueError(
                        f"all-day timespan {name} time {value} can't have a timezone"
                    )

        if self.begin_time is not None:
            validate_timeprecision(self.begin_time, "begin")

            if self.end_time is not None:
                validate_timeprecision(self.end_time, self._end_name())
                if self.begin_time > self.end_time:
                    raise ValueError(
                        "begin time must be before " + self._end_name() + " time"
                    )
                if self.precision == "day" and self.end_time < (
                    self.begin_time + TIMEDELTA_DAY
                ):
                    raise ValueError(
                        "all-day timespan duration must be at least one day"
                    )
                if self.duration is not None:
                    raise ValueError(
                        "can't set duration together with " + self._end_name() + " time"
                    )
                if self.begin_time.tzinfo is None and self.end_time.tzinfo is not None:
                    raise ValueError(
                        self._end_name()
                        + " time may not have a timezone as the begin time doesn't either"
                    )
                if self.begin_time.tzinfo is not None and self.end_time.tzinfo is None:
                    raise ValueError(
                        self._end_name()
                        + " time must have a timezone as the begin time also does"
                    )
                duration = self.get_effective_duration()
                if duration and not timedelta_nearly_zero(
                    duration % TIMEDELTA_CACHE[self.precision]
                ):
                    raise ValueError(
                        "effective duration value %s has higher precision than set precision %s"
                        % (self.get_effective_duration(), self.precision)
                    )

            if self.duration is not None:
                if self.duration < TIMEDELTA_ZERO:
                    raise ValueError("timespan duration must be positive")
                if self.precision == "day" and self.duration < TIMEDELTA_DAY:
                    raise ValueError(
                        "all-day timespan duration must be at least one day"
                    )
                if not timedelta_nearly_zero(
                    self.duration % TIMEDELTA_CACHE[self.precision]
                ):
                    raise ValueError(
                        "duration value %s has higher precision than set precision %s"
                        % (self.duration, self.precision)
                    )

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
                suffix.append(begin.strftime("%Y-%m-%d"))
            else:
                suffix.append(str(begin))

        end = self.get_effective_end()
        end_repr = self.get_end_representation()
        if end is not None:
            if end_repr == "end":
                suffix.append("fixed")
            suffix.append(self._end_name() + ":")
            if self.is_all_day():
                suffix.append(end.strftime("%Y-%m-%d"))
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
        return f"<{' '.join(prefix + name + suffix)}>"

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
            if (
                end == begin
            ):  # we also add another day if the duration would be 0 otherwise
                end = end + TIMEDELTA_DAY

        if self.get_end_representation() == "duration":
            assert end is not None
            assert begin is not None
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
            raise ValueError(f"can't convert from representation {current} to {target}")

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
    def timespan_tuple(
        self, default: None = None, normalization: Normalization = None
    ) -> NullableTimespanTuple:
        ...

    @overload
    def timespan_tuple(
        self, default: datetime, normalization: Normalization = None
    ) -> TimespanTuple:
        ...

    def timespan_tuple(self, default=None, normalization=None):
        if normalization:
            return TimespanTuple(
                normalization.normalize(self.get_begin() or default),
                normalization.normalize(self.get_effective_end() or default),
            )
        else:
            return TimespanTuple(
                self.get_begin() or default, self.get_effective_end() or default
            )

    def cmp_tuple(self) -> TimespanTuple:
        """Get event timespan details

        Will  return a :class:`TimespanTuple` object.
        A nested tuple containing e.begin, e.end and e.name.
        """
        return self.timespan_tuple(
            default=CMP_DATETIME_NONE_DEFAULT, normalization=CMP_NORMALIZATION
        )

    def __require_tuple_components(self, values, *required):
        for nr, (val, req) in enumerate(zip(values, required)):
            if req and val is None:
                event = "this event" if nr < 2 else "other event"
                prop = "begin" if nr % 2 == 0 else "end"
                raise ValueError(f"{event} has no {prop} time")

    def starts_within(self, other: "Timespan") -> bool:
        first = cast(
            TimespanTuple, self.timespan_tuple(normalization=CMP_NORMALIZATION)
        )
        second = cast(
            TimespanTuple, other.timespan_tuple(normalization=CMP_NORMALIZATION)
        )
        self.__require_tuple_components(first + second, True, False, True, True)

        # the timespan doesn't include its end instant / day
        return second.begin <= first.begin < second.end

    def ends_within(self, other: "Timespan") -> bool:
        first = cast(
            TimespanTuple, self.timespan_tuple(normalization=CMP_NORMALIZATION)
        )
        second = cast(
            TimespanTuple, other.timespan_tuple(normalization=CMP_NORMALIZATION)
        )
        self.__require_tuple_components(first + second, False, True, True, True)

        # the timespan doesn't include its end instant / day
        return second.begin <= first.end < second.end

    def intersects(self, other: "Timespan") -> bool:
        first = cast(
            TimespanTuple, self.timespan_tuple(normalization=CMP_NORMALIZATION)
        )
        second = cast(
            TimespanTuple, other.timespan_tuple(normalization=CMP_NORMALIZATION)
        )
        self.__require_tuple_components(first + second, True, True, True, True)

        # the timespan doesn't include its end instant / day
        return (
            second.begin <= first.begin < second.end
            or second.begin <= first.end < second.end
            or first.begin <= second.begin < first.end
            or first.begin <= second.end < first.end
        )

    def includes(self, other: Union["Timespan", datetime]) -> bool:
        if isinstance(other, datetime):
            first = cast(
                TimespanTuple, self.timespan_tuple(normalization=CMP_NORMALIZATION)
            )
            other = CMP_NORMALIZATION.normalize(other)
            self.__require_tuple_components(first, True, True)

            # the timespan doesn't include its end instant / day
            return first.begin <= other < first.end

        else:
            first = cast(
                TimespanTuple, self.timespan_tuple(normalization=CMP_NORMALIZATION)
            )
            second = cast(
                TimespanTuple, other.timespan_tuple(normalization=CMP_NORMALIZATION)
            )
            self.__require_tuple_components(first + second, True, True, True, True)

            # the timespan doesn't include its end instant / day
            return first.begin <= second.begin and second.end < first.end

    __contains__ = includes

    def is_included_in(self, other: "Timespan") -> bool:
        first = cast(
            TimespanTuple, self.timespan_tuple(normalization=CMP_NORMALIZATION)
        )
        second = cast(
            TimespanTuple, other.timespan_tuple(normalization=CMP_NORMALIZATION)
        )
        self.__require_tuple_components(first + second, True, True, True, True)

        # the timespan doesn't include its end instant / day
        return second.begin <= first.begin and first.end < second.end

    def __lt__(self, other: Any) -> bool:
        if isinstance(other, Timespan):
            return self.cmp_tuple() < other.cmp_tuple()
        else:
            return NotImplemented

    def __gt__(self, other: Any) -> bool:
        if isinstance(other, Timespan):
            return self.cmp_tuple() > other.cmp_tuple()
        else:
            return NotImplemented

    def __le__(self, other: Any) -> bool:
        if isinstance(other, Timespan):
            return self.cmp_tuple() <= other.cmp_tuple()
        else:
            return NotImplemented

    def __ge__(self, other: Any) -> bool:
        if isinstance(other, Timespan):
            return self.cmp_tuple() >= other.cmp_tuple()
        else:
            return NotImplemented


class EventTimespan(Timespan):
    def _end_name(self):
        return "end"

    def validate(self):
        super().validate()
        if self.begin_time is None and self.end_time is not None:
            raise ValueError("event timespan without begin time can't have end time")

    def get_effective_duration(self) -> timedelta:
        if self.duration is not None:
            return self.duration
        elif self.end_time is not None and self.begin_time is not None:
            return self.end_time - self.begin_time
        elif self.is_all_day():
            return TIMEDELTA_DAY
        else:
            return TIMEDELTA_ZERO


class TodoTimespan(Timespan):
    def _end_name(self):
        return "due"

    def timespan_tuple(self, default=None, normalization=None):
        # Todos compare by (due, begin) instead of (begin, end)
        return tuple(
            reversed(
                super().timespan_tuple(default=default, normalization=normalization)
            )
        )
