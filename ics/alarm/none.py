from ics.alarm.base import BaseAlarm
from ics.parsers.alarm_parser import NoneAlarmParser
from ics.serializers.alarm_serializer import NoneAlarmSerializer


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
