import re

from ics import Organizer, Attendee
from ics.alarm.utils import get_type_from_container
from ics.parsers.parser import Parser, option
from ics.utils import (iso_precision, iso_to_arrow, parse_duration,
                       unescape_string)


class EventParser(Parser):
    def parse_dtstamp(event, line):
        if line:
            # get the dict of vtimezones passed to the classmethod
            tz_dict = event._classmethod_kwargs["tz"]
            event.created = iso_to_arrow(line, tz_dict)

    def parse_last_modified(event, line):
        if line:
            tz_dict = event._classmethod_kwargs["tz"]
            event.last_modified = iso_to_arrow(line, tz_dict)

    def parse_dtstart(event, line):
        if line:
            # get the dict of vtimezones passed to the classmethod
            tz_dict = event._classmethod_kwargs["tz"]
            event.begin = iso_to_arrow(line, tz_dict)
            event._begin_precision = iso_precision(line.value)

    def parse_duration(event, line):
        if line:
            # TODO: DRY [1]
            if event._end_time:  # pragma: no cover
                raise ValueError("An event can't have both DTEND and DURATION")
            event._duration = parse_duration(line.value)

    def parse_dtend(event, line):
        if line:
            # TODO: DRY [1]
            if event._duration:
                raise ValueError("An event can't have both DTEND and DURATION")
            # get the dict of vtimezones passed to the classmethod
            tz_dict = event._classmethod_kwargs["tz"]
            event._end_time = iso_to_arrow(line, tz_dict)
            # one could also save the end_precision to check that if begin_precision is day, end_precision also is

    def parse_summary(event, line):
        event.name = unescape_string(line.value) if line else None

    def parse_organizer(event, line):
        event.organizer = Organizer.parse(line) if line else None

    @option(multiple=True)
    def parse_attendee(event, lines):
        for line in lines:
            event.attendees.add(Attendee.parse(line))

    def parse_description(event, line):
        event.description = unescape_string(line.value) if line else None

    def parse_location(event, line):
        event.location = unescape_string(line.value) if line else None

    def parse_geo(event, line):
        if line:
            latitude, _, longitude = unescape_string(line.value).partition(";")
            event.geo = float(latitude), float(longitude)

    def parse_url(event, line):
        event.url = unescape_string(line.value) if line else None

    def parse_transp(event, line):
        if line and line.value in ["TRANSPARENT", "OPAQUE"]:
            event.transparent = line.value == "TRANSPARENT"

    # TODO : make uid required ?
    # TODO : add option somewhere to ignore some errors
    def parse_uid(event, line):
        if line:
            event.uid = line.value

    @option(multiple=True)
    def parse_valarm(event, lines):
        event.alarms = [get_type_from_container(x)._from_container(x) for x in lines]

    def parse_status(event, line):
        if line:
            event.status = line.value

    def parse_class(event, line):
        if line:
            event.classification = line.value

    def parse_categories(event, line):
        event.categories = set()
        if line:
            # In the regular expression: Only match unquoted commas.
            for cat in re.split("(?<!\\\\),", line.value):
                event.categories.update({unescape_string(cat)})
