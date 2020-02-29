from ics.grammar.parse import ContentLine
from ics.serializers.serializer import Serializer
from ics.utils import escape_string


class PersonSerializer(Serializer):
    def serialize_cn(person: "Person", line: ContentLine):
        if person.common_name:
            line.params["CN"] = [escape_string(person.common_name)]

    def serialize_dir(person: "Person", line: ContentLine):
        if person.dir:
            line.params["DIR"] = [escape_string(person.dir)]

    def serialize_sent_by(person: "Person", line: ContentLine):
        if person.sent_by:
            line.params["SENT-BY"] = [escape_string(person.sent_by)]


class AttendeeSerializer(PersonSerializer):
    def serialize_rsvp(attendee: "Attendee", line: ContentLine):
        if attendee.rsvp is not None:
            line.params["RSVP"] = [attendee.rsvp]

    def serialize_role(attendee: "Attendee", line: ContentLine):
        if attendee.role:
            line.params["ROLE"] = [escape_string(attendee.role)]

    def serialize_partstat(attendee: "Attendee", line: ContentLine):
        if attendee.partstat:
            line.params["PARTSTAT"] = [escape_string(attendee.partstat)]

    def serialize_cutype(attendee: "Attendee", line: ContentLine):
        if attendee.cutype:
            line.params["CUTYPE"] = [escape_string(attendee.cutype)]
