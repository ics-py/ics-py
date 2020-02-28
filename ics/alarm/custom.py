import attr

from ics.alarm.base import BaseAlarm
from ics.parsers.alarm_parser import CustomAlarmParser
from ics.serializers.alarm_serializer import CustomAlarmSerializer
from ics.utils import validate_not_none


@attr.s
class CustomAlarm(BaseAlarm):
    """
    A calendar event VALARM with custom ACTION.
    """

    class Meta:
        name = "VALARM"
        parser = CustomAlarmParser
        serializer = CustomAlarmSerializer

    _action = attr.ib(default=None, validator=validate_not_none)

    @property
    def action(self):
        return self._action
