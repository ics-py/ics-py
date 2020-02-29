import warnings
from typing import Dict, List

from ics.grammar.parse import ContentLine
from ics.parsers.attendee_parser import AttendeeParser, PersonParser
from ics.serializers.attendee_serializer import AttendeeSerializer, PersonSerializer
from ics.utils import escape_string, unescape_string


class Person(object):
    class Meta:
        name = "ABSTRACT-PERSON"
        parser = PersonParser
        serializer = PersonSerializer

    def __init__(self, email: str, common_name: str = None, dir: str = None, sent_by: str = None) -> None:
        self.email = email
        self.common_name = common_name or email
        self.dir = dir
        self.sent_by = sent_by
        self.extra: Dict[str, List[str]] = {}

    @classmethod
    def parse(cls, line: ContentLine) -> "Person":
        email = unescape_string(line.value)
        if email.lower().startswith("mailto:"):
            email = email[len("mailto:"):]
        val = cls(email)
        val.populate(line)
        return val

    def populate(self, line: ContentLine) -> None:
        if line.name != self.Meta.name:
            raise ValueError("line isn't an {}".format(self.Meta.name))

        params = dict(line.params)
        for param_name, (parser, options) in self.Meta.parser.get_parsers().items():
            values = params.pop(param_name, [])
            if not values and options.required:
                if options.default:
                    values = options.default
                    default_str = "\\n".join(map(str, options.default))
                    message = ("The %s property was not found and is required by the RFC." +
                               " A default value of \"%s\" has been used instead") % (param_name, default_str)
                    warnings.warn(message)
                else:
                    raise ValueError('A {} must have at least one {}'.format(line.name, param_name))

            if not options.multiple and len(values) > 1:
                raise ValueError('A {} must have at most one {}'.format(line.name, param_name))

            if options.multiple:
                parser(self, values)  # Send a list or empty list
            else:
                if len(values) == 1:
                    parser(self, values[0])  # Send the element
                else:
                    parser(self, None)  # Send None

        self.extra = params  # Store unused lines

    def serialize(self) -> ContentLine:
        line = ContentLine(self.Meta.name, params=self.extra, value=escape_string('mailto:%s' % self.email))
        for output in self.Meta.serializer.get_serializers():
            output(self, line)
        return line

    def __str__(self) -> str:
        """Returns the attendee in an ContentLine format."""
        return str(self.serialize())


class Organizer(Person):
    class Meta:
        name = 'ORGANIZER'
        parser = PersonParser
        serializer = PersonSerializer


class Attendee(Person):
    def __init__(self, email: str, common_name: str = None, dir: str = None, sent_by: str = None,
                 rsvp: bool = None, role: str = None, partstat: str = None, cutype: str = None) -> None:
        super().__init__(email, common_name, dir, sent_by)
        self.rsvp = rsvp
        self.role = role
        self.partstat = partstat
        self.cutype = cutype

    class Meta:
        name = 'ATTENDEE'
        parser = AttendeeParser
        serializer = AttendeeSerializer
