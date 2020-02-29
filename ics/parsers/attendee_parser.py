from ics.parsers.parser import Parser
from ics.utils import unescape_string


class PersonParser(Parser):
    def parse_cn(person: "Person", value):
        if value:
            person.common_name = unescape_string(value)

    def parse_dir(person: "Person", value):
        if value:
            person.dir = unescape_string(value)

    def parse_sent_by(person: "Person", value):
        if value:
            person.sent_by = unescape_string(value)


class AttendeeParser(PersonParser):
    def parse_rsvp(attendee: "Attendee", value):
        if value:
            attendee.rsvp = bool(value)

    def parse_role(attendee: "Attendee", value):
        if value:
            attendee.role = unescape_string(value)

    def parse_partstat(attendee: "Attendee", value):
        if value:
            attendee.partstat = unescape_string(value)

    def parse_cutype(attendee: "Attendee", value):
        if value:
            attendee.cutype = unescape_string(value)
