import copy
from typing import Callable, Dict, Iterable, List, Optional, Set, Union

from dateutil.tz import tzical
from six import StringIO, text_type

from .component import Component, Extractor
from .event import Event
from .parse import Container, ContentLine, calendar_string_to_containers
from .timeline import Timeline
from .todo import Todo
from .utils import remove_sequence, remove_x


class Calendar(Component):
    """
    Represents an unique rfc5545 iCalendar.

    Attributes:

        events: a set of Event contained in the Calendar
        todos: a set of Todo contained in the Calendar
        timeline: a Timeline instance linked to this Calendar

    """

    _EXTRACTORS: List[Extractor] = []
    _OUTPUTS: List[Callable] = []

    class Meta:
        name = 'VCALENDAR'

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
        iterable: an iterable version of __str__, line per line
        (with line-endings).

        Example:
            Can be used to write calendar to a file:

            >>> c = Calendar(); c.events.add(Event(name="My cool event"))
            >>> open('my.ics', 'w').writelines(c)
        """
        for line in str(self).split('\n'):
            yield line + '\n'

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


# ------------------
# ----- Inputs -----
# ------------------

@Calendar._extracts('PRODID', required=True)
def prodid(calendar, prodid):
    calendar._creator = prodid.value


__version_default__ = [ContentLine(name='VERSION', value='2.0')]


@Calendar._extracts('VERSION', required=True, default=__version_default__)
def version(calendar, line):
    version = line
    # TODO : should take care of minver/maxver
    if ';' in version.value:
        _, calendar.version = version.value.split(';')
    else:
        calendar.version = version.value


@Calendar._extracts('CALSCALE')
def scale(calendar, line):
    calscale = line
    if calscale:
        calendar.scale = calscale.value.lower()
        calendar.scale_params = calscale.params
    else:
        calendar.scale = 'georgian'
        calendar.scale_params = {}


@Calendar._extracts('METHOD')
def method(calendar, line):
    method = line
    if method:
        calendar.method = method.value
        calendar.method_params = method.params
    else:
        calendar.method = None
        calendar.method_params = {}


@Calendar._extracts('VTIMEZONE', multiple=True)
def timezone(calendar, vtimezones):
    """Receives a list of VTIMEZONE blocks.

    Parses them and adds them to calendar._timezones.
    """
    for vtimezone in vtimezones:
        remove_x(vtimezone)  # Remove non standard lines from the block
        remove_sequence(vtimezone)  # Remove SEQUENCE lines because tzical does not understand them
        fake_file = StringIO()
        fake_file.write(str(vtimezone))  # Represent the block as a string
        fake_file.seek(0)
        timezones = tzical(fake_file)  # tzical does not like strings
        # timezones is a tzical object and could contain multiple timezones
        for key in timezones.keys():
            calendar._timezones[key] = timezones.get(key)


@Calendar._extracts('VEVENT', multiple=True)
def events(calendar, lines):
    # tz=calendar._timezones gives access to the event factory to the
    # timezones list
    def event_factory(x):
        return Event._from_container(x, tz=calendar._timezones)
    calendar.events = set(map(event_factory, lines))


@Calendar._extracts('VTODO', multiple=True)
def todos(calendar, lines):
    # tz=calendar._timezones gives access to the event factory to the
    # timezones list
    def todo_factory(x):
        return Todo._from_container(x, tz=calendar._timezones)
    calendar.todos = set(map(todo_factory, lines))


# -------------------
# ----- Outputs -----
# -------------------

@Calendar._outputs
def o_prodid(calendar, container):
    creator = calendar.creator if calendar.creator else \
        'ics.py - http://git.io/lLljaA'
    container.append(ContentLine('PRODID', value=creator))


@Calendar._outputs
def o_version(calendar, container):
    container.append(ContentLine('VERSION', value='2.0'))


@Calendar._outputs
def o_scale(calendar, container):
    if calendar.scale:
        container.append(ContentLine('CALSCALE', value=calendar.scale.upper()))


@Calendar._outputs
def o_method(calendar, container):
    if calendar.method:
        container.append(ContentLine('METHOD', value=calendar.method.upper()))


@Calendar._outputs
def o_events(calendar, container):
    for event in calendar.events:
        container.append(str(event))


@Calendar._outputs
def o_todos(calendar, container):
    for todo in calendar.todos:
        container.append(str(todo))
