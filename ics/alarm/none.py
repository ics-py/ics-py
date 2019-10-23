from ics.alarm.base import BaseAlarm

from ics.serializers.alarm_serializer import NoneAlarmSerializer
from ics.parsers.alarm_parser import NoneAlarmParser


class NoneAlarm(BaseAlarm):
    """
    A calendar event VALARM with NONE option.
    """

    class Meta:
        name = "VALARM"
        parser = NoneAlarmParser
        serializer = NoneAlarmSerializer

    @property
    def action(self):
        return "NONE"
