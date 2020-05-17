from typing import ClassVar, Dict, Iterable, Iterator, List, Optional, Union

import attr
from attr.validators import instance_of

from ics.component import Component
from ics.converter.base import AttributeConverter, ics_attr_meta
from ics.converter.component import ComponentMetaInfo, InflatedComponentMeta
from ics.event import Event
from ics.contentline import Container, string_to_containers
from ics.timeline import Timeline
from ics.timezone import Timezone
from ics.todo import Todo
from ics.types import ContainerItem, ContextDict
from ics.valuetype.datetime import DatetimeConverterMixin


class CalendarTimezoneConsumer(AttributeConverter):
    @property
    def filter_ics_names(self) -> List[str]:
        return Timezone.MetaInfo.container_name

    def populate(self, component: "Component", item: ContainerItem, context: ContextDict) -> bool:
        return item.name == "VTIMEZONE" and isinstance(item, Container)

    def serialize(self, component: "Component", output: Container, context: ContextDict):
        return


@attr.s
class CalendarAttrs(Component):
    version: str = attr.ib(validator=instance_of(str))  # default set by Calendar.DEFAULT_VERSION
    prodid: str = attr.ib(validator=instance_of(str))  # default set by Calendar.DEFAULT_PRODID
    scale: Optional[str] = attr.ib(default=None)
    method: Optional[str] = attr.ib(default=None)

    _timezones: List[Timezone] = attr.ib(factory=list, converter=list, metadata=ics_attr_meta(converter=CalendarTimezoneConsumer),
                                         init=False, repr=False, eq=False, order=False, hash=False)
    events: List[Event] = attr.ib(factory=list, converter=list)
    todos: List[Todo] = attr.ib(factory=list, converter=list)


class CalendarMeta(InflatedComponentMeta):
    def _populate_attrs(self, instance: "Component", container: Container, context: ContextDict):
        avail_tz: Dict[str, Timezone] = context.setdefault(DatetimeConverterMixin.CONTEXT_KEY_AVAILABLE_TZ, {})
        for child in container:
            if child.name == "VTIMEZONE" and isinstance(child, Container):
                tz = Timezone.from_container(child)
                avail_tz.setdefault(tz.tzid, tz)

        super()._populate_attrs(instance, container, context)

        instance._timezones = context[DatetimeConverterMixin.CONTEXT_KEY_AVAILABLE_TZ].values()

    def _serialize_attrs(self, component: "Component", context: ContextDict, container: Container):
        assert isinstance(component, Calendar)
        avail_tz: Dict[str, Timezone] = context.setdefault(DatetimeConverterMixin.CONTEXT_KEY_AVAILABLE_TZ, {})
        for tz in component._timezones:
            avail_tz.setdefault(tz.tzid, tz)

        super()._serialize_attrs(component, context, container)

        timezones = [tz.to_container() for tz in context[DatetimeConverterMixin.CONTEXT_KEY_AVAILABLE_TZ].values()]
        container.data = timezones + container.data


class Calendar(CalendarAttrs):
    """
    Represents an unique RFC 5545 iCalendar.

    Attributes:

        events: a list of `Event`s contained in the Calendar
        todos: a list of `Todo`s contained in the Calendar
        timeline: a `Timeline` instance for iterating this Calendar in chronological order

    """

    MetaInfo = ComponentMetaInfo("VCALENDAR", inflated_meta_class=CalendarMeta)
    DEFAULT_VERSION: ClassVar[str] = "2.0"
    DEFAULT_PRODID: ClassVar[str] = "ics.py - http://git.io/lLljaA"

    def __init__(
            self,
            imports: Union[str, Container, None] = None,
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
                self.populate(imports)
            else:
                if isinstance(imports, str):
                    containers = iter(string_to_container(imports))
                else:
                    containers = iter(lines_to_container(imports))
                try:
                    container = next(containers)
                    if not isinstance(container, Container):
                        raise ValueError("can't populate from %s" % type(container))
                    self.populate(container)
                except StopIteration:
                    raise ValueError("string didn't contain any ics data")
                try:
                    next(containers)
                    raise ValueError("Multiple calendars in one file are not supported by this method."
                                     "Use ics.Calendar.parse_multiple()")
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
        """"
        Parses an input string that may contain mutiple calendars
        and retruns a list of :class:`ics.event.Calendar`
        """
        containers = string_to_containers(string)
        return [cls(imports=c) for c in containers]

    def __str__(self) -> str:
        return "<Calendar with {} event{} and {} todo{}>".format(
            len(self.events),
            "s" if len(self.events) > 1 else "",
            len(self.todos),
            "s" if len(self.todos) > 1 else "")

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
