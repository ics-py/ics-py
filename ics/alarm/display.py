import copy

from ics.alarm.base import BaseAlarm
from ics.parse import ContentLine
from ics.utils import escape_string, unescape_string
from typing import Union
from datetime import datetime, timedelta


from ics.serializers.alarm import DisplayAlarmSerializer
from ics.parsers.alarm import DisplayAlarmParser


class DisplayAlarm(BaseAlarm):
    """
    A calendar event VALARM with DISPLAY option.
    """

    class Meta:
        name = "VALARM"
        parser = DisplayAlarmParser
        serializer = DisplayAlarmSerializer


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
