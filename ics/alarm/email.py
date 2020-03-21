from typing import List

import attr

from ics.alarm.base import BaseAlarm
from ics.attendee import Attendee
from ics.parsers.alarm_parser import EmailAlarmParser
from ics.serializers.alarm_serializer import EmailAlarmSerializer
from ics.utils import check_is_instance


@attr.s(repr=False)
class EmailAlarm(BaseAlarm):
    """
    A calendar event VALARM with Email option.
    """

    class Meta:
        name = "VALARM"
        parser = EmailAlarmParser
        serializer = EmailAlarmSerializer

    subject: str = attr.ib(default=None)
    body: str = attr.ib(default=None)
    recipients: List[Attendee] = attr.ib(factory=list)  # TODO this is a set for Event

    def add_recipient(self, recipient: Attendee):
        """ Add an recipient to the recipients list """
        check_is_instance("recipient", recipient, Attendee)
        self.recipients.append(recipient)

    @property
    def action(self):
        return "EMAIL"
