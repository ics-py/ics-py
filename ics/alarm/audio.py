from typing import Optional

from ics.alarm.base import BaseAlarm

from ics.grammar.parse import ContentLine
from typing import Union
from datetime import datetime, timedelta

from ics.serializers.alarm_serializer import AudioAlarmSerializer
from ics.parsers.alarm_parser import AudioAlarmParser


class AudioAlarm(BaseAlarm):
    """
    A calendar event VALARM with AUDIO option.
    """

    class Meta:
        name = "VALARM"
        parser = AudioAlarmParser
        serializer = AudioAlarmSerializer

    def __init__(
        self,
        trigger: Union[timedelta, datetime] = None,
        repeat: int = None,
        duration: timedelta = None,
    ):

        super().__init__(trigger, repeat, duration)
        self._sound: Optional[ContentLine] = None

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
