import warnings
from typing import List, TYPE_CHECKING

from ics.attendee import Attendee
from ics.grammar.parse import ContentLine
from ics.parsers.parser import Parser, option
from ics.utils import parse_datetime, parse_duration, unescape_string

if TYPE_CHECKING:
    from ics.alarm import *
    from ics.alarm.base import BaseAlarm


class BaseAlarmParser(Parser):
    @option(required=True)
    def parse_trigger(alarm: "BaseAlarm", line: ContentLine):
        if line.params.get("VALUE", [""])[0] == "DATE-TIME":
            alarm.trigger = parse_datetime(line)
        elif line.params.get("VALUE", ["DURATION"])[0] == "DURATION":
            alarm.trigger = parse_duration(line.value)
        else:
            warnings.warn(
                "ics.py encountered a TRIGGER of unknown type '%s'. It has been ignored."
                % line.params["VALUE"][0]
            )

    def parse_duration(alarm: "BaseAlarm", line: ContentLine):
        if line:
            alarm._duration = parse_duration(line.value)

    def parse_repeat(alarm: "BaseAlarm", line: ContentLine):
        if line:
            alarm._repeat = int(line.value)


class CustomAlarmParser(BaseAlarmParser):
    @option(required=True)
    def parse_attach(alarm: "CustomAlarm", line: ContentLine):
        if line:
            alarm._action = line.value


class AudioAlarmParser(BaseAlarmParser):
    def parse_attach(alarm: "AudioAlarm", line: ContentLine):
        if line:
            alarm._sound = line


class DisplayAlarmParser(BaseAlarmParser):
    @option(required=True)
    def parse_description(alarm: "DisplayAlarm", line: ContentLine):
        alarm.display_text = unescape_string(line.value) if line else None


class EmailAlarmParser(BaseAlarmParser):
    @option(required=True)
    def parse_description(alarm: "EmailAlarm", line: ContentLine):
        alarm.body = unescape_string(line.value) if line else None

    @option(required=True)
    def parse_summary(alarm: "EmailAlarm", line: ContentLine):
        alarm.subject = unescape_string(line.value) if line else None

    @option(required=True, multiple=True)
    def parse_attendee(alarm: "EmailAlarm", lines: List[ContentLine]):
        for line in lines:
            alarm.recipients.append(Attendee.parse(line))


class NoneAlarmParser(BaseAlarmParser):
    pass
