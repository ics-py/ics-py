import warnings
from typing import Dict, List, Optional

import attr

from ics.grammar.parse import ContentLine
from ics.parsers.attendee_parser import AttendeeParser, PersonParser
from ics.serializers.attendee_serializer import AttendeeSerializer, PersonSerializer
from ics.utils import escape_string, unescape_string


@attr.s
class Person(object):
    email: str = attr.ib()
    common_name: str = attr.ib(default=None)
    dir: Optional[str] = attr.ib(default=None)
    sent_by: Optional[str] = attr.ib(default=None)
    extra: Dict[str, List[str]] = attr.ib(factory=dict)

    def __attrs_post_init__(self):
        if not self.common_name:
            self.common_name = self.email

    class Meta:
        name = "ABSTRACT-PERSON"
        parser = PersonParser
        serializer = PersonSerializer

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


@attr.s
class Attendee(Person):
    rsvp: Optional[bool] = attr.ib(default=None)
    role: Optional[str] = attr.ib(default=None)
    partstat: Optional[str] = attr.ib(default=None)
    cutype: Optional[str] = attr.ib(default=None)

    class Meta:
        name = 'ATTENDEE'
        parser = AttendeeParser
        serializer = AttendeeSerializer
