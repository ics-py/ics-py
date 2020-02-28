import attr

from ics.alarm.base import BaseAlarm
from ics.parsers.alarm_parser import DisplayAlarmParser
from ics.serializers.alarm_serializer import DisplayAlarmSerializer


@attr.s
class DisplayAlarm(BaseAlarm):
    """
    A calendar event VALARM with DISPLAY option.
    """

    class Meta:
        name = "VALARM"
        parser = DisplayAlarmParser
        serializer = DisplayAlarmSerializer

    display_text: str = attr.ib(default=None)

    @property
    def action(self):
        return "DISPLAY"
