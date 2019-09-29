import copy

from ics.alarm.base import BaseAlarm
from ics.parse import ContentLine
from ics.utils import escape_string, unescape_string
from typing import Union, List
from datetime import datetime, timedelta


class EmailAlarm(BaseAlarm):
    """
    A calendar event VALARM with Email option.
    """

    # This ensures we copy the existing extractors and outputs from the base class, rather than referencing the array.
    _EXTRACTORS = copy.copy(BaseAlarm._EXTRACTORS)
    _OUTPUTS = copy.copy(BaseAlarm._OUTPUTS)

    def __init__(
        self,
        trigger: Union[timedelta, datetime] = None,
        repeat: int = None,
        duration: timedelta = None,
        subject: str = None,
        body: str = None,
        recipients: List[str] = None,
    ):

        super().__init__(trigger, repeat, duration)

        self.subject = subject
        self.body = body
        self.recipients = recipients if recipients else []
