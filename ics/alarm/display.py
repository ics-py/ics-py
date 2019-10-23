from ics.alarm.base import BaseAlarm
from typing import Union
from datetime import datetime, timedelta


from ics.serializers.alarm_serializer import DisplayAlarmSerializer
from ics.parsers.alarm_parser import DisplayAlarmParser


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
