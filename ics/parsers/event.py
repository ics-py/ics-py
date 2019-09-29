import re

from ics.alarm.utils import get_type_from_container
from ics.parsers.parser import Parser, option
from ics.utils import iso_precision, iso_to_arrow, parse_duration, unescape_string


class EventParser(Parser):
    def dtstamp(event, line):
        if line:
            # get the dict of vtimezones passed to the classmethod
            tz_dict = event._classmethod_kwargs["tz"]
            event.created = iso_to_arrow(line, tz_dict)

    def last_modified(event, line):
        if line:
            tz_dict = event._classmethod_kwargs["tz"]
            event.last_modified = iso_to_arrow(line, tz_dict)

    def dtstart(event, line):
        if line:
            # get the dict of vtimezones passed to the classmethod
            tz_dict = event._classmethod_kwargs["tz"]
            event.begin = iso_to_arrow(line, tz_dict)
            event._begin_precision = iso_precision(line.value)

    def duration(event, line):
        if line:
            # TODO: DRY [1]
            if event._end_time:  # pragma: no cover
                raise ValueError("An event can't have both DTEND and DURATION")
            event._duration = parse_duration(line.value)

    def dtend(event, line):
        if line:
            # TODO: DRY [1]
            if event._duration:
                raise ValueError("An event can't have both DTEND and DURATION")
            # get the dict of vtimezones passed to the classmethod
            tz_dict = event._classmethod_kwargs["tz"]
            event._end_time = iso_to_arrow(line, tz_dict)
            # one could also save the end_precision to check that if begin_precision is day, end_precision also is

    def summary(event, line):
        event.name = unescape_string(line.value) if line else None

    def organizer(event, line):
        event.organizer = unescape_string(line.value) if line else None

    def description(event, line):
        event.description = unescape_string(line.value) if line else None

    def location(event, line):
        event.location = unescape_string(line.value) if line else None

    def geo(event, line):
        if line:
            latitude, _, longitude = unescape_string(line.value).partition(";")
            event.geo = float(latitude), float(longitude)

    def url(event, line):
        event.url = unescape_string(line.value) if line else None

    def transp(event, line):
        if line and line.value in ["TRANSPARENT", "OPAQUE"]:
            event.transparent = line.value == "TRANSPARENT"

    # TODO : make uid required ?
    # TODO : add option somewhere to ignore some errors
    def uid(event, line):
        if line:
            event.uid = line.value

    @option(multiple=True)
    def valarm(event, lines):
        event.alarms = [get_type_from_container(x)._from_container(x) for x in lines]

    def status(event, line):
        if line:
            event.status = line.value

    def classification(event, line):
        if line:
            event.classification = line.value

    def categories(event, line):
        event.categories = set()
        if line:
            # In the regular expression: Only match unquoted commas.
            for cat in re.split("(?<!\\\\),", line.value):
                event.categories.update({unescape_string(cat)})
