from typing import TYPE_CHECKING, List

from ics.alarm.utils import get_type_from_container
from ics.parse import ContentLine
from ics.parsers.parser import Parser, option
from ics.utils import iso_to_arrow, parse_duration, unescape_string

if TYPE_CHECKING:
    from .todo import Todo


class CalendarParser(Parser):
    @option(required=True)
    def dtstamp(todo: "Todo", line: ContentLine):
        if line:
            # get the dict of vtimezones passed to the classmethod
            tz_dict = todo._classmethod_kwargs["tz"]
            todo.dtstamp = iso_to_arrow(line, tz_dict)

    @option(required=True)
    def uid(todo: "Todo", line: ContentLine):
        if line:
            todo.uid = line.value

    def completed(todo: "Todo", line: ContentLine):
        if line:
            # get the dict of vtimezones passed to the classmethod
            tz_dict = todo._classmethod_kwargs["tz"]
            todo.completed = iso_to_arrow(line, tz_dict)

    def created(todo: "Todo", line: ContentLine):
        if line:
            # get the dict of vtimezones passed to the classmethod
            tz_dict = todo._classmethod_kwargs["tz"]
            todo.created = iso_to_arrow(line, tz_dict)

    def description(todo: "Todo", line: ContentLine):
        todo.description = unescape_string(line.value) if line else None

    def start(todo: "Todo", line: ContentLine):
        if line:
            # get the dict of vtimezones passed to the classmethod
            tz_dict = todo._classmethod_kwargs["tz"]
            todo.begin = iso_to_arrow(line, tz_dict)

    def location(todo: "Todo", line: ContentLine):
        todo.location = unescape_string(line.value) if line else None

    def percent_complete(todo: "Todo", line: ContentLine):
        todo.percent = int(line.value) if line else None

    def priority(todo: "Todo", line: ContentLine):
        todo.priority = int(line.value) if line else None

    def summary(todo: "Todo", line: ContentLine):
        todo.name = unescape_string(line.value) if line else None

    def url(todo: "Todo", line: ContentLine):
        todo.url = unescape_string(line.value) if line else None

    def due(todo: "Todo", line: ContentLine):
        if line:
            # TODO: DRY [1]
            if todo._duration:
                raise ValueError("A todo can't have both DUE and DURATION")
            # get the dict of vtimezones passed to the classmethod
            tz_dict = todo._classmethod_kwargs["tz"]
            todo._due_time = iso_to_arrow(line, tz_dict)

    def duration(todo: "Todo", line: ContentLine):
        if line:
            # TODO: DRY [1]
            if todo._due_time:  # pragma: no cover
                raise ValueError("An todo can't have both DUE and DURATION")
            todo._duration = parse_duration(line.value)

    @option(multiple=True)
    def valarm(todo: "Todo", lines: List[ContentLine]):
        todo.alarms = [get_type_from_container(x)._from_container(x) for x in lines]

    def status(todo: "Todo", line: ContentLine):
        if line:
            todo.status = line.value
