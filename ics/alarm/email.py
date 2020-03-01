from datetime import datetime, timedelta
from typing import List, Union

from ics.alarm.base import BaseAlarm
from ics.attendee import Attendee
from ics.parsers.alarm_parser import EmailAlarmParser
from ics.serializers.alarm_serializer import EmailAlarmSerializer


class EmailAlarm(BaseAlarm):
    """
    A calendar event VALARM with Email option.
    """

    class Meta:
        name = "VALARM"
        parser = EmailAlarmParser
        serializer = EmailAlarmSerializer

    def __init__(
            self,
            trigger: Union[timedelta, datetime] = None,
            repeat: int = None,
            duration: timedelta = None,
            subject: str = None,
            body: str = None,
            recipients: List[Attendee] = None,
    ):
        super().__init__(trigger, repeat, duration)

        self.subject = subject
        self.body = body
        self.recipients = recipients if recipients else []

    @property
    def action(self):
        return "EMAIL"
