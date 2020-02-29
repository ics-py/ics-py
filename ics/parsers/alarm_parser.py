import warnings

from ics.attendee import Attendee
from ics.parsers.parser import Parser, option
from ics.utils import iso_to_arrow, parse_duration, unescape_string


class BaseAlarmParser(Parser):
    @option(required=True)
    def parse_trigger(alarm, line):
        if line.params.get("VALUE", [""])[0] == "DATE-TIME":
            alarm.trigger = iso_to_arrow(line)
        elif line.params.get("VALUE", ["DURATION"])[0] == "DURATION":
            alarm.trigger = parse_duration(line.value)
        else:
            warnings.warn(
                "ics.py encountered a TRIGGER of unknown type '%s'. It has been ignored."
                % line.params["VALUE"][0]
            )

    def parse_duration(alarm, line):
        if line:
            alarm._duration = parse_duration(line.value)

    def parse_repeat(alarm, line):
        if line:
            alarm._repeat = int(line.value)


class CustomAlarmParser(BaseAlarmParser):
    def parse_action(alarm, line, required=True):
        print(line)
        if line:
            alarm._action = line.value


class AudioAlarmParser(BaseAlarmParser):
    def parse_attach(alarm, line):
        if line:
            alarm._sound = line


class DisplayAlarmParser(BaseAlarmParser):
    @option(required=True)
    def parse_description(alarm, line):
        alarm.display_text = unescape_string(line.value) if line else None


class EmailAlarmParser(BaseAlarmParser):
    @option(required=True)
    def parse_description(alarm, line):
        alarm.body = unescape_string(line.value) if line else None

    @option(required=True)
    def parse_summary(alarm, line):
        alarm.subject = unescape_string(line.value) if line else None

    @option(required=True, multiple=True)
    def parse_attendee(alarm, lines):
        for line in lines:
            alarm.recipients.append(Attendee.parse(line))


class NoneAlarmParser(BaseAlarmParser):
    pass
