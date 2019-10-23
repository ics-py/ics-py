from ics.alarm.base import BaseAlarm
import copy
from typing import Union
from datetime import datetime, timedelta

from ics.serializers.alarm_serializer import CustomAlarmSerializer
from ics.parsers.alarm_parser import CustomAlarmParser


class CustomAlarm(BaseAlarm):
    """
    A calendar event VALARM with custom ACTION.
    """

    class Meta:
        name = "VALARM"
        parser = CustomAlarmParser
        serializer = CustomAlarmSerializer

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
