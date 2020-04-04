from datetime import tzinfo
from typing import ClassVar, Iterable, List, Optional, Union

import attr
from attr.validators import instance_of

from ics.component import Component
from ics.converter.component import ComponentMeta
from ics.event import Event
from ics.grammar import Container, calendar_string_to_containers
from ics.timeline import Timeline
from ics.todo import Todo


@attr.s
class CalendarAttrs(Component):
    version: str = attr.ib(validator=instance_of(str))  # default set by Calendar.Meta.DEFAULT_VERSION
    prodid: str = attr.ib(validator=instance_of(str))  # default set by Calendar.Meta.DEFAULT_PRODID
    scale: Optional[str] = attr.ib(default=None)
    method: Optional[str] = attr.ib(default=None)

    _timezones: List[tzinfo] = attr.ib(factory=list, converter=list)  # , init=False, repr=False, eq=False, order=False, hash=False)
    events: List[Event] = attr.ib(factory=list, converter=list)
    todos: List[Todo] = attr.ib(factory=list, converter=list)


class Calendar(CalendarAttrs):
    """
    Represents an unique RFC 5545 iCalendar.

    Attributes:

        events: a list of `Event`s contained in the Calendar
        todos: a list of `Todo`s contained in the Calendar
        timeline: a `Timeline` instance for iterating this Calendar in chronological order

    """

    Meta = ComponentMeta("VCALENDAR")
    DEFAULT_VERSION: ClassVar[str] = "2.0"
    DEFAULT_PRODID: ClassVar[str] = "ics.py - http://git.io/lLljaA"

    def __init__(
            self,
            imports: Union[str, Container] = None,
            events: Optional[Iterable[Event]] = None,
            todos: Optional[Iterable[Todo]] = None,
            creator: str = None,
            **kwargs
    ):
        """Initializes a new Calendar.

        Args:
            imports (**str**): data to be imported into the Calendar,
            events (**Iterable[Event]**): `Event`s to be added to the calendar
            todos (**Iterable[Todo]**): `Todo`s to be added to the calendar
            creator (**string**): uid of the creator program.
        """
        if events is None:
            events = tuple()
        if todos is None:
            todos = tuple()
        kwargs.setdefault("version", self.DEFAULT_VERSION)
        kwargs.setdefault("prodid", creator if creator is not None else self.DEFAULT_PRODID)
        super(Calendar, self).__init__(events=events, todos=todos, **kwargs)  # type: ignore
        self.timeline = Timeline(self, None)

        if imports is not None:
            if isinstance(imports, Container):
                self.Meta.populate_instance(self, imports)  # type:ignore
            else:
                containers = calendar_string_to_containers(imports)
                if len(containers) != 1:
                    raise NotImplementedError(
                        'Multiple calendars in one file are not supported by this method. Use ics.Calendar.parse_multiple()')

                self.Meta.populate_instance(self, containers[0])  # type:ignore

    @property
    def creator(self) -> str:
        return self.prodid

    @creator.setter
    def creator(self, value: str):
        self.prodid = value

    @classmethod
    def parse_multiple(cls, string):
        """"
        Parses an input string that may contain mutiple calendars
        and retruns a list of :class:`ics.event.Calendar`
        """
        containers = calendar_string_to_containers(string)
        return [cls(imports=c) for c in containers]

    def __iter__(self) -> Iterable[str]:
        """Returns:
        iterable: an iterable version of __str__, line per line
        (with line-endings).

        Example:
            Can be used to write calendar to a file:

            >>> c = Calendar(); c.events.append(Event(summary="My cool event"))
            >>> open('my.ics', 'w').writelines(c)
        """
        return iter(str(self).splitlines(keepends=True))
