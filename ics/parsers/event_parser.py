import re
from typing import List, TYPE_CHECKING

from ics.alarm.utils import get_type_from_container
from ics.attendee import Attendee, Organizer
from ics.grammar.parse import ContentLine
from ics.parsers.parser import Parser, option
from ics.utils import iso_precision, parse_datetime, parse_duration, unescape_string

if TYPE_CHECKING:
    from ics.event import Event


class EventParser(Parser):
    def parse_dtstamp(event: "Event", line: ContentLine):
        if line:
            # get the dict of vtimezones passed to the classmethod
            tz_dict = event._classmethod_kwargs["tz"]
            event.created = parse_datetime(line, tz_dict)

    def parse_last_modified(event: "Event", line: ContentLine):
        if line:
            tz_dict = event._classmethod_kwargs["tz"]
            event.last_modified = parse_datetime(line, tz_dict)

    def parse_dtstart(event: "Event", line: ContentLine):
        if line:
            # get the dict of vtimezones passed to the classmethod
            tz_dict = event._classmethod_kwargs["tz"]
            event._timespan = event._timespan.replace(
                begin_time=parse_datetime(line, tz_dict),
                precision=iso_precision(line.value)
            )

    def parse_duration(event: "Event", line: ContentLine):
        if line:
            event._timespan = event._timespan.replace(
                duration=parse_duration(line.value)
            )

    def parse_dtend(event: "Event", line: ContentLine):
        if line:
            tz_dict = event._classmethod_kwargs["tz"]
            event._timespan = event._timespan.replace(
                end_time=parse_datetime(line, tz_dict)
            )

    def parse_summary(event: "Event", line: ContentLine):
        event.name = unescape_string(line.value) if line else None

    def parse_organizer(event: "Event", line: ContentLine):
        event.organizer = Organizer.parse(line) if line else None

    @option(multiple=True)
    def parse_attendee(event: "Event", lines: List[ContentLine]):
        for line in lines:
            event.attendees.add(Attendee.parse(line))

    def parse_description(event: "Event", line: ContentLine):
        event.description = unescape_string(line.value) if line else None

    def parse_location(event: "Event", line: ContentLine):
        event.location = unescape_string(line.value) if line else None

    def parse_geo(event: "Event", line: ContentLine):
        if line:
            latitude, _, longitude = unescape_string(line.value).partition(";")
            event.geo = float(latitude), float(longitude)

    def parse_url(event: "Event", line: ContentLine):
        event.url = unescape_string(line.value) if line else None

    def parse_transp(event: "Event", line: ContentLine):
        if line and line.value in ["TRANSPARENT", "OPAQUE"]:
            event.transparent = line.value == "TRANSPARENT"

    # TODO : make uid required ?
    def parse_uid(event: "Event", line: ContentLine):
        if line:
            event.uid = line.value

    @option(multiple=True)
    def parse_valarm(event, lines: List[ContentLine]):
        event.alarms = [get_type_from_container(x)._from_container(x) for x in lines]

    def parse_status(event: "Event", line: ContentLine):
        if line:
            event.status = line.value

    def parse_class(event: "Event", line: ContentLine):
        if line:
            event.classification = line.value

    def parse_categories(event: "Event", line: ContentLine):
        event.categories = set()
        if line:
            # In the regular expression: Only match unquoted commas.
            for cat in re.split("(?<!\\\\),", line.value):
                event.categories.update({unescape_string(cat)})
