from datetime import date, datetime
from typing import Union

DatetimeLike = Union[datetime, date]
OptionalDatetimeLike = Union[datetime, date, None]
TimespanOrBegin = Union[datetime, date, "Timespan"]
