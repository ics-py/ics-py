from datetime import datetime, date
from typing import Union

DatetimeLike = Union[datetime, date]
OptionalDatetimeLike = Union[datetime, date, None]
TimespanOrBegin = Union[datetime, date, "Timespan"]
