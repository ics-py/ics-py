from typing import Dict, Iterable, Optional, Set, Union

import attr

from ics.component import Component
from ics.event import Event
from ics.grammar.parse import Container, calendar_string_to_containers
from ics.parsers.icalendar_parser import CalendarParser
from ics.serializers.icalendar_serializer import CalendarSerializer
from ics.timeline import Timeline
from ics.todo import Todo


@attr.s
class CalendarAttrs(Component):
    _timezones: Dict = attr.ib(factory=dict, init=False, repr=False, cmp=False, hash=False)
    events: Set[Event] = attr.ib(factory=set, converter=set)
    todos: Set[Todo] = attr.ib(factory=set, converter=set)
    prodid: Optional[str] = attr.ib(default=None)
    scale: Optional[str] = attr.ib(default=None)
    method: Optional[str] = attr.ib(default=None)


class Calendar(CalendarAttrs):
    """
    Represents an unique rfc5545 iCalendar.

    Attributes:

        events: a set of Event contained in the Calendar
        todos: a set of Todo contained in the Calendar
        timeline: a Timeline instance linked to this Calendar

    """

    class Meta:
        name = 'VCALENDAR'
        parser = CalendarParser
        serializer = CalendarSerializer

    def __init__(
            self,
            imports: Union[str, Container] = None,
            events: Iterable[Event] = None,
            todos: Iterable[Todo] = None,
            creator: str = None,
            **kwargs
    ):
        """Instantiates a new Calendar.

        Args:
            imports (**str**): data to be imported into the Calendar,
            events (**Set[Event]**): Events to be added to the calendar
            todos (Set[Todo]): Todos to be added to the calendar
            creator (string): uid of the creator program.

        If ``imports`` is specified, every other argument will be ignored.
        """
        super(Calendar, self).__init__(events=events, todo=todos, prodid=creator, **kwargs)
        self.timeline = Timeline(self, None)

        if imports is not None:
            if isinstance(imports, Container):
                self._populate(imports)
            else:
                containers = calendar_string_to_containers(imports)
                if len(containers) != 1:
                    raise NotImplementedError(
                        'Multiple calendars in one file are not supported by this method. Use ics.Calendar.parse_multiple()')

                self._populate(containers[0])  # Use first calendar

    @classmethod
    def parse_multiple(cls, string):
        """"
        Parses an input string that may contain mutiple calendars
        and retruns a list of :class:`ics.event.Calendar`
        """
        containers = calendar_string_to_containers(string)
        return [cls(imports=c) for c in containers]

    def __repr__(self) -> str:
        return "<Calendar with {} event{} and {} todo{}>" \
            .format(len(self.events),
                    "s" if len(self.events) > 1 else "",
                    len(self.todos),
                    "s" if len(self.todos) > 1 else "")

    def __iter__(self) -> Iterable[str]:
        """Returns:
        iterable: an iterable version of __str__, line per line
        (with line-endings).

        Example:
            Can be used to write calendar to a file:

            >>> c = Calendar(); c.events.add(Event(name="My cool event"))
            >>> open('my.ics', 'w').writelines(c)
        """
        return iter(str(self).splitlines(keepends=True))
