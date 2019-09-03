from ics.alarm.base import BaseAlarm
import copy
from typing import Union
from datetime import datetime, timedelta


class CustomAlarm(BaseAlarm):
    """
    A calendar event VALARM with custom ACTION.
    """

    # This ensures we copy the existing extractors and outputs from the base class, rather than referencing the array.
    _EXTRACTORS = copy.copy(BaseAlarm._EXTRACTORS)
    _OUTPUTS = copy.copy(BaseAlarm._OUTPUTS)

    def __init__(
        self,
        trigger: Union[timedelta, datetime] = None,
        repeat: int = None,
        duration: timedelta = None,
        action: str = None,
    ) -> None:
        super().__init__(trigger, repeat, duration)

        self._action = action

    @property
    def action(self):
        return self._action


@CustomAlarm._extracts("ACTION")
def action(alarm, line, required=True):
    print(line)
    if line:
        alarm._action = line.value
