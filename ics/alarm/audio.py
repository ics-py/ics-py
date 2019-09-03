from ics.alarm.base import BaseAlarm
import copy

from ics.parse import ContentLine
from typing import Union
from datetime import datetime, timedelta


class AudioAlarm(BaseAlarm):
    """
    A calendar event VALARM with AUDIO option.
    """

    # This ensures we copy the existing extractors and outputs from the base class, rather than referencing the array.
    _EXTRACTORS = copy.copy(BaseAlarm._EXTRACTORS)
    _OUTPUTS = copy.copy(BaseAlarm._OUTPUTS)

    def __init__(
        self,
        trigger: Union[timedelta, datetime] = None,
        repeat: int = None,
        duration: timedelta = None,
    ):

        super().__init__(trigger, repeat, duration)
        self._sound = None

    @property
    def action(self):
        return "AUDIO"

    @property
    def sound(self):
        return self._sound

    @sound.setter
    def sound(self, sound):
        assert isinstance(sound, ContentLine)
        self._sound = sound


# ------------------
# ----- Inputs -----
# ------------------
@AudioAlarm._extracts("ATTACH")
def attach(alarm, line):
    if line:
        alarm._sound = line


# -------------------
# ----- Outputs -----
# -------------------
@AudioAlarm._outputs
def o_attach(alarm, container):
    if alarm._sound:
        container.append(str(alarm._sound))
