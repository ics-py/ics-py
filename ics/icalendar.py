import copy
import warnings
from typing import Dict, Iterable, Optional, Set, Union

from six import text_type

from .component import Component
from .event import Event
from ics.grammar.parse import Container, calendar_string_to_containers
from .timeline import Timeline
from .todo import Todo
from ics.parsers.icalendar_parser import CalendarParser
from ics.serializers.icalendar_serializer import CalendarSerializer


class Calendar(Component):
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
        creator: str = None
    ):
        """Instantiates a new Calendar.

        Args:
            imports (**str**): data to be imported into the Calendar,
            events (**Set[Event]**): Events to be added to the calendar
            todos (Set[Todo]): Todos to be added to the calendar
            creator (string): uid of the creator program.

        If ``imports`` is specified, every other argument will be ignored.
        """

        self._timezones: Dict = {} # FIXME mypy
        self.events: Set[Event] = set()
        self.todos: Set[Todo] = set()
        self.extra = Container(name='VCALENDAR')
        self.scale = None
        self.method = None

        self.timeline = Timeline(self)

        if imports is not None:
            if isinstance(imports, Container):
                self._populate(imports)
            else:
                containers = calendar_string_to_containers(imports)
                if len(containers) != 1:
                    raise NotImplementedError(
                        'Multiple calendars in one file are not supported by this method. Use ics.Calendar.parse_multiple()')

                self._populate(containers[0])  # Use first calendar
        else:
            if events is not None:
                self.events.update(set(events))
            if todos is not None:
                self.todos.update(set(todos))
            self._creator = creator

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
        iterable: an iterable version of seralize(), line per line
        (with line-endings).

        Example:
            Can be used to write calendar to a file:

            >>> c = Calendar(); c.events.add(Event(name="My cool event"))
            >>> open('my.ics', 'w').writelines(c)
        """
        warnings.warn(
            "Using Calendar as Iterable is deprecated and will be removed in version 0.8. "
            "Use the explicit calendar.serialize_iter() instead.", DeprecationWarning)
        yield from self.serialize_iter()

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Calendar):
            raise NotImplementedError
        for attr in ('extra', 'scale', 'method', 'creator'):
            if self.__getattribute__(attr) != other.__getattribute__(attr):
                return False

        return (self.events == other.events) and (self.todos == other.todos)

    def __ne__(self, other: object) -> bool:
        return not self.__eq__(other)

    @property
    def creator(self) -> Optional[str]:
        """Get or set the calendar's creator.

        |  Will return a string.
        |  May be set to a string.
        |  Creator is the PRODID iCalendar property.
        |  It uniquely identifies the program that created the calendar.
        """
        return self._creator

    @creator.setter
    def creator(self, value: Optional[str]) -> None:
        if not isinstance(value, text_type):
            raise ValueError('Event.creator must be unicode data not {}'.format(type(value)))
        self._creator = value

    def clone(self):
        """
        Returns:
            Calendar: an exact deep copy of self
        """
        clone = copy.copy(self)
        clone.extra = clone.extra.clone()
        clone.events = copy.copy(self.events)
        clone.todos = copy.copy(self.todos)
        clone._timezones = copy.copy(self._timezones)
        return clone
