from datetime import tzinfo
from typing import ClassVar, Iterable, Iterator, List, Optional, Union, overload

import attr
from attr.validators import instance_of

from ics.component import Component
from ics.contentline import Container, lines_to_containers, string_to_containers
from ics.event import Event
from ics.timeline import Timeline
from ics.timespan import Normalization, NormalizationAction
from ics.todo import Todo


@attr.s
class CalendarAttrs(Component):
    version: str = attr.ib(
        validator=instance_of(str), metadata={"ics_priority": 1000}
    )  # default set by Calendar.DEFAULT_VERSION
    prodid: str = attr.ib(
        validator=instance_of(str), metadata={"ics_priority": 900}
    )  # default set by Calendar.DEFAULT_PRODID
    scale: Optional[str] = attr.ib(default=None, metadata={"ics_priority": 800})
    method: Optional[str] = attr.ib(default=None, metadata={"ics_priority": 700})
    # CalendarTimezoneConverter has priority 600

    events: List[Event] = attr.ib(
        factory=list, converter=list, metadata={"ics_priority": -100}
    )
    todos: List[Todo] = attr.ib(
        factory=list, converter=list, metadata={"ics_priority": -200}
    )


class Calendar(CalendarAttrs):
    """
    Represents an unique RFC 5545 iCalendar.

    Attributes:

        events: a list of `Event`s contained in the Calendar
        todos: a list of `Todo`s contained in the Calendar
        timeline: a `Timeline` instance for iterating this Calendar in chronological order

    """

    NAME = "VCALENDAR"
    DEFAULT_VERSION: ClassVar[str] = "2.0"
    DEFAULT_PRODID: ClassVar[str] = "ics.py 0.8.0-dev0 - http://git.io/lLljaA"

    def __init__(
        self,
        imports: Union[str, Container, None] = None,
        events: Optional[Iterable[Event]] = None,
        todos: Optional[Iterable[Todo]] = None,
        creator: str = None,
        **kwargs,
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
        kwargs.setdefault(
            "prodid", creator if creator is not None else self.DEFAULT_PRODID
        )
        super().__init__(events=events, todos=todos, **kwargs)  # type: ignore[arg-type]
        self.timeline = Timeline(self, None)

        if imports is not None:
            if isinstance(imports, Container):
                self.populate(imports)
            else:
                if isinstance(imports, str):
                    containers = iter(string_to_containers(imports))
                else:
                    containers = iter(lines_to_containers(imports))
                try:
                    container = next(containers)
                    if not isinstance(container, Container):
                        raise ValueError(f"can't populate from {type(container)}")
                    self.populate(container)
                except StopIteration:
                    raise ValueError("string didn't contain any ics data")
                try:
                    next(containers)
                    raise ValueError(
                        "Multiple calendars in one file are not supported by this method."
                        "Use ics.Calendar.parse_multiple()"
                    )
                except StopIteration:
                    pass

    @property
    def creator(self) -> str:
        return self.prodid

    @creator.setter
    def creator(self, value: str):
        self.prodid = value

    @classmethod
    def parse_multiple(cls, string):
        """ "
        Parses an input string that may contain mutiple calendars
        and retruns a list of :class:`ics.event.Calendar`
        """
        containers = string_to_containers(string)
        return [cls(imports=c) for c in containers]

    @overload
    def normalize(self, normalization: Normalization):
        ...

    @overload
    def normalize(
        self,
        value: tzinfo,
        normalize_floating: NormalizationAction,
        normalize_with_tz: NormalizationAction,
    ):
        ...

    def normalize(self, normalization, *args, **kwargs):
        if isinstance(normalization, Normalization):
            if args or kwargs:
                raise ValueError(
                    "can't pass args or kwargs when a complete Normalization is given"
                )
        else:
            normalization = Normalization(normalization, *args, **kwargs)
        self.events = [
            e if e.all_day else normalization.normalize(e) for e in self.events
        ]
        self.todos = [
            e if e.all_day else normalization.normalize(e) for e in self.todos
        ]

    def __str__(self) -> str:
        return "<Calendar with {} event{} and {} todo{}>".format(
            len(self.events),
            "" if len(self.events) == 1 else "s",
            len(self.todos),
            "" if len(self.todos) == 1 else "s",
        )

    def __iter__(self) -> Iterator[str]:
        """Returns:
        iterable: an iterable version of __str__, line per line
        (with line-endings).

        Example:
            Can be used to write calendar to a file:

            >>> c = Calendar(); c.events.append(Event(summary="My cool event"))
            >>> open('my.ics', 'w').writelines(c)
        """
        return iter(self.serialize().splitlines(keepends=True))
