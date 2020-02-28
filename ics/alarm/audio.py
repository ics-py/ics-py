from typing import Optional

import attr

from ics.alarm.base import BaseAlarm
from ics.grammar.parse import ContentLine
from ics.parsers.alarm_parser import AudioAlarmParser
from ics.serializers.alarm_serializer import AudioAlarmSerializer


@attr.s
class AudioAlarm(BaseAlarm):
    """
    A calendar event VALARM with AUDIO option.
    """

    class Meta:
        name = "VALARM"
        parser = AudioAlarmParser
        serializer = AudioAlarmSerializer

    sound: Optional[ContentLine] = attr.ib(default=None, validator=attr.validators.instance_of(ContentLine))

    @property
    def action(self):
        return "AUDIO"
