from datetime import date, datetime
from typing import TYPE_CHECKING, Union

DatetimeLike = Union[datetime, date]
OptionalDatetimeLike = Union[datetime, date, None]

if TYPE_CHECKING:
    from ics.timespan import Timespan

    TimespanOrBegin = Union[datetime, date, Timespan]
else:
    TimespanOrBegin = Union[datetime, date, "Timespan"]
