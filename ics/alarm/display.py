import copy

from ics.alarm.base import BaseAlarm
from ics.parse import ContentLine
from ics.utils import escape_string, unescape_string
from typing import Union
from datetime import datetime, timedelta


class DisplayAlarm(BaseAlarm):
    """
    A calendar event VALARM with DISPLAY option.
    """

    # This ensures we copy the existing extractors and outputs from the base class, rather than referencing the array.
    _EXTRACTORS = copy.copy(BaseAlarm._EXTRACTORS)
    _OUTPUTS = copy.copy(BaseAlarm._OUTPUTS)

    def __init__(
        self,
        trigger: Union[timedelta, datetime] = None,
        repeat: int = None,
        duration: timedelta = None,
        display_text: str = None,
    ):

        super().__init__(trigger, repeat, duration)

        self.display_text = display_text

    @property
    def action(self):
        return "DISPLAY"


# ------------------
# ----- Inputs -----
# ------------------
@DisplayAlarm._extracts("DESCRIPTION", required=True)
def description(alarm, line):
    alarm.display_text = unescape_string(line.value) if line else None


# -------------------
# ----- Outputs -----
# -------------------
@DisplayAlarm._outputs
def o_description(alarm, container):
    container.append(
        ContentLine("DESCRIPTION", value=escape_string(alarm.display_text or ""))
    )
