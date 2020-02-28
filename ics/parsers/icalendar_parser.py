from io import StringIO
from typing import List, TYPE_CHECKING

from dateutil.tz import tzical

from ics.event import Event
from ics.grammar.parse import ContentLine
from ics.parsers.parser import Parser, option
from ics.todo import Todo
from ics.utils import remove_sequence, remove_x

if TYPE_CHECKING:
    from ics.event import Calendar


class CalendarParser(Parser):
    @option(required=True)
    def parse_prodid(calendar: "Calendar", prodid: ContentLine):
        calendar._creator = prodid.value

    _version_default = [ContentLine(name="VERSION", value="2.0")]

    @option(required=True, default=_version_default)
    def parse_version(calendar: "Calendar", line: ContentLine):
        version = line
        # TODO : should take care of minver/maxver
        if ";" in version.value:
            _, calendar.version = version.value.split(";")
        else:
            calendar.version = version.value

    def parse_calscale(calendar: "Calendar", line: ContentLine):
        calscale = line
        if calscale:
            calendar.scale = calscale.value.lower()
            calendar.scale_params = calscale.params
        else:
            calendar.scale = "georgian"
            calendar.scale_params = {}

    def parse_method(calendar: "Calendar", line: ContentLine):
        method = line
        if method:
            calendar.method = method.value
            calendar.method_params = method.params
        else:
            calendar.method = None
            calendar.method_params = {}

    @option(multiple=True)
    def parse_vtimezone(calendar: "Calendar", vtimezones: List[ContentLine]):
        """Receives a list of VTIMEZONE blocks.

        Parses them and adds them to calendar._timezones.
        """
        for vtimezone in vtimezones:
            remove_x(vtimezone)  # Remove non standard lines from the block
            remove_sequence(
                vtimezone
            )  # Remove SEQUENCE lines because tzical does not understand them
            fake_file = StringIO()
            fake_file.write(str(vtimezone))  # Represent the block as a string
            fake_file.seek(0)
            timezones = tzical(fake_file)  # tzical does not like strings
            # timezones is a tzical object and could contain multiple timezones
            for key in timezones.keys():
                calendar._timezones[key] = timezones.get(key)

    @option(multiple=True)
    def parse_vevent(calendar: "Calendar", lines: List[ContentLine]):
        # tz=calendar._timezones gives access to the event factory to the
        # timezones list
        def event_factory(x):
            return Event._from_container(x, tz=calendar._timezones)

        calendar.events = set(map(event_factory, lines))

    @option(multiple=True)
    def parse_vtodo(calendar: "Calendar", lines: List[ContentLine]):
        # tz=calendar._timezones gives access to the event factory to the
        # timezones list
        def todo_factory(x):
            return Todo._from_container(x, tz=calendar._timezones)

        calendar.todos = set(map(todo_factory, lines))
