import warnings
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import attr

from ics.alarm.base import BaseAlarm
from ics.event import STATUS_ATTRIB
from ics.grammar.parse import Container
from ics.parsers.parser import Parser
from ics.serializers.serializer import Serializer
from ics.timespan import Timespan
from ics.types import DatetimeLike
from ics.utils import ensure_datetime, get_lines, uid_gen


@attr.s
class Component(object):
    class Meta:
        name = "ABSTRACT"
        parser = Parser
        serializer = Serializer

    extra: Container = attr.ib(init=False, default=None, validator=attr.validators.instance_of(Container))
    _classmethod_args: Tuple = attr.ib(init=False, default=None, repr=False, cmp=False, hash=False)
    _classmethod_kwargs: Dict = attr.ib(init=False, default=None, repr=False, cmp=False, hash=False)

    def __attrs_post_init__(self):
        self.extra = Container(self.Meta.name)

    def __init_subclass__(cls):
        if cls.__str__ != Component.__str__:
            raise TypeError("%s may not overwrite %s" % (cls, Component.__str__))

    @classmethod
    def _from_container(cls, container: Container, *args: Any, **kwargs: Any):
        k = cls()
        k._classmethod_args = args
        k._classmethod_kwargs = kwargs
        k._populate(container)

        return k

    def _populate(self, container: Container) -> None:
        if container.name != self.Meta.name:
            raise ValueError("container isn't an {}".format(self.Meta.name))

        for line_name, (parser, options) in self.Meta.parser.get_parsers().items():
            lines = get_lines(container, line_name)
            if not lines and options.required:
                if options.default:
                    lines = options.default
                    default_str = "\\n".join(map(str, options.default))
                    message = ("The %s property was not found and is required by the RFC." +
                               " A default value of \"%s\" has been used instead") % (line_name, default_str)
                    warnings.warn(message)
                else:
                    raise ValueError('A {} must have at least one {}'.format(container.name, line_name))

            if not options.multiple and len(lines) > 1:
                raise ValueError('A {} must have at most one {}'.format(container.name, line_name))

            if options.multiple:
                parser(self, lines)  # Send a list or empty list
            else:
                if len(lines) == 1:
                    parser(self, lines[0])  # Send the element
                else:
                    parser(self, None)  # Send None

        self.extra = container  # Store unused lines

    def clone(self):
        """
        Returns:
            Event: an exact copy of self"""
        return attr.evolve(self)

    def __str__(self) -> str:
        """Returns the component in an iCalendar format."""
        container = self.extra.clone()
        for output in self.Meta.serializer.get_serializers():
            output(self, container)
        return str(container)


@attr.s
class CalendarEntryAttrs(Component):
    _timespan: Timespan = attr.ib(validator=attr.validators.instance_of(Timespan))
    name: Optional[str] = attr.ib(default=None)
    uid: str = attr.ib(factory=uid_gen)

    description: Optional[str] = attr.ib(default=None)
    location: Optional[str] = attr.ib(default=None)
    url: Optional[str] = attr.ib(default=None)
    status: Optional[str] = attr.ib(default=None, **STATUS_ATTRIB)

    created: Optional[DatetimeLike] = attr.ib(factory=datetime.now, converter=ensure_datetime)
    last_modified: Optional[DatetimeLike] = attr.ib(factory=datetime.now, converter=ensure_datetime)
    # self.dtstamp = datetime.utcnow() if not dtstamp else ensure_datetime(dtstamp) # ToDo
    alarms: List[BaseAlarm] = attr.ib(factory=list, converter=list)
