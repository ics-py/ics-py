import copy
from datetime import datetime, timedelta
from typing import Iterable, List, Optional

import arrow
from six.moves import map

from .alarm.base import BaseAlarm
from .component import Component
from ics.grammar.parse import Container
from .utils import get_arrow, uid_gen

from ics.parsers.todo_parser import TodoParser
from ics.serializers.todo_serializer import TodoSerializer


class Todo(Component):

    """A todo list entry.

    Can have a start time and duration, or start and due time,
    or only start/due time.
    """

    class Meta:
        name = "VTODO"
        parser = TodoParser
        serializer = TodoSerializer

    def __init__(self,
                 dtstamp=None,
                 uid: str = None,
                 completed=None,
                 created=None,
                 description: str = None,
                 begin=None,
                 location: str = None,
                 percent: int = None,
                 priority: int = None,
                 name: str = None,
                 url: str = None,
                 due=None,
                 duration: timedelta = None,
                 alarms: Iterable[BaseAlarm] = None,
                 status: str = None):
        """Instantiates a new :class:`ics.todo.Todo`.

        Args:
            uid (string): must be unique
            dtstamp (Arrow-compatible)
            completed (Arrow-compatible)
            created (Arrow-compatible)
            description (string)
            begin (Arrow-compatible)
            location (string)
            percent (int): 0-100
            priority (int): 0-9
            name (string) : rfc5545 SUMMARY property
            url (string)
            due (Arrow-compatible)
            duration (datetime.timedelta)
            alarms (:class:`ics.alarm.Alarm`)
            status (string)

        Raises:
            ValueError: if `duration` and `due` are specified at the same time
        """

        self._percent: Optional[int] = None
        self._priority: Optional[int] = None
        self._begin = None
        self._due_time = None
        self._duration = None

        self.uid = uid_gen() if not uid else uid
        self.dtstamp = arrow.now() if not dtstamp else get_arrow(dtstamp)
        self.completed = get_arrow(completed)
        self.created = get_arrow(created)
        self.description = description
        self.begin = begin
        self.location = location
        self.percent = percent
        self.priority = priority
        self.name = name
        self.url = url
        self.alarms: List[BaseAlarm] = list()
        self.extra = Container(name='VTODO')

        if duration and due:
            raise ValueError(
                'Todo() may not specify a duration and due date\
                at the same time')
        elif duration:
            if not begin:
                raise ValueError(
                    'Todo() must specify a begin if a duration\
                    is specified')
            self.duration = duration
        elif due:
            self.due = due

        if alarms is not None:
            self.alarms = list(alarms)
        self.status = status

    @property
    def percent(self) -> Optional[int]:
        return self._percent

    @percent.setter
    def percent(self, value: Optional[int]):
        if value:
            value = int(value)
            if value < 0 or value > 100:
                raise ValueError('percent must be [0, 100]')
        self._percent = value

    @property
    def priority(self) -> Optional[int]:
        return self._priority

    @priority.setter
    def priority(self, value: Optional[int]):
        if value:
            value = int(value)
            if value < 0 or value > 9:
                raise ValueError('priority must be [0, 9]')
        self._priority = value

    @property
    def begin(self):
        """Get or set the beginning of the todo.

        |  Will return an :class:`Arrow` object.
        |  May be set to anything that :func:`Arrow.get` understands.
        |  If a due time is defined (not a duration), .begin must not
            be set to a superior value.
        """
        return self._begin

    @begin.setter
    def begin(self, value):
        value = get_arrow(value)
        if value and self._due_time and value > self._due_time:
            raise ValueError('Begin must be before due time')
        self._begin = value

    @property
    def due(self):
        """Get or set the end of the todo.

        |  Will return an :class:`Arrow` object.
        |  May be set to anything that :func:`Arrow.get` understands.
        |  If set to a non null value, removes any already
            existing duration.
        |  Setting to None will have unexpected behavior if
            begin is not None.
        |  Must not be set to an inferior value than self.begin.
        """

        if self._duration:
            # if due is duration defined return the beginning + duration
            return self.begin + self._duration
        elif self._due_time:
            # if due is time defined
            return self._due_time
        else:
            return None

    @due.setter
    def due(self, value):
        value = get_arrow(value)
        if value and self._begin and value < self._begin:
            raise ValueError('Due must be after begin')

        self._due_time = value

        if value:
            self._duration = None

    @property
    def duration(self):
        """Get or set the duration of the todo.

        |  Will return a timedelta object.
        |  May be set to anything that timedelta() understands.
        |  May be set with a dict ({"days":2, "hours":6}).
        |  If set to a non null value, removes any already
            existing end time.
        """
        if self._duration:
            return self._duration
        elif self.due:
            return self.due - self.begin
        else:
            # todo has neither due, nor start and duration
            return None

    @duration.setter
    def duration(self, value):
        if isinstance(value, dict):
            value = timedelta(**value)
        elif isinstance(value, timedelta):
            value = value
        elif value is not None:
            value = timedelta(value)

        self._duration = value

        if value:
            self._due_time = None

    @property
    def status(self) -> Optional[str]:
        return self._status

    @status.setter
    def status(self, value: Optional[str]):
        if isinstance(value, str):
            value = value.upper()
        statuses = (None, 'NEEDS-ACTION', 'COMPLETED', 'IN-PROCESS', 'CANCELLED')
        if value not in statuses:
            raise ValueError('status must be one of %s' % ", ".join([repr(x) for x in statuses]))
        self._status = value

    def __repr__(self) -> str:
        if self.name is None:
            return "<Todo>"
        if self.begin is None and self.due is None:
            return "<Todo '{}'>".format(self.name)
        if self.due is None:
            return "<Todo '{}' begin:{}>".format(self.name, self.begin)
        if self.begin is None:
            return "<Todo '{}' due:{}>".format(self.name, self.due)
        return "<Todo '{}' begin:{} due:{}>".format(self.name, self.begin, self.due)

    def __lt__(self, other) -> bool:
        if isinstance(other, Todo):
            if self.due is None and other.due is None:
                if self.name is None and other.name is None:
                    return False
                elif self.name is None:
                    return True
                elif other.name is None:
                    return False
                else:
                    return self.name < other.name
            return self.due < other.due
        if isinstance(other, datetime):
            if self.due:
                return self.due < other
        raise NotImplementedError(
            'Cannot compare Todo and {}'.format(type(other)))

    def __le__(self, other) -> bool:
        if isinstance(other, Todo):
            if self.due is None and other.due is None:
                if self.name is None and other.name is None:
                    return True
                elif self.name is None:
                    return True
                elif other.name is None:
                    return False
                else:
                    return self.name <= other.name
            return self.due <= other.due
        if isinstance(other, datetime):
            if self.due:
                return self.due <= other
        raise NotImplementedError(
            'Cannot compare Todo and {}'.format(type(other)))

    def __gt__(self, other) -> bool:
        if isinstance(other, Todo):
            if self.due is None and other.due is None:
                if self.name is None and other.name is None:
                    return False
                elif self.name is None:
                    return False
                elif other.name is None:
                    return True
                else:
                    return self.name > other.name
            return self.due > other.due
        if isinstance(other, datetime):
            if self.due:
                return self.due > other
        raise NotImplementedError(
            'Cannot compare Todo and {}'.format(type(other)))

    def __ge__(self, other) -> bool:
        if isinstance(other, Todo):
            if self.due is None and other.due is None:
                if self.name is None and other.name is None:
                    return True
                elif self.name is None:
                    return True
                elif other.name is None:
                    return False
                else:
                    return self.name >= other.name
            return self.due >= other.due
        if isinstance(other, datetime):
            if self.due:
                return self.due >= other
        raise NotImplementedError(
            'Cannot compare Todo and {}'.format(type(other)))

    def __eq__(self, other) -> bool:
        """Two todos are considered equal if they have the same uid."""
        if isinstance(other, Todo):
            return self.uid == other.uid
        raise NotImplementedError(
            'Cannot compare Todo and {}'.format(type(other)))

    def __ne__(self, other) -> bool:
        """Two todos are considered not equal if they do not have the same uid."""
        if isinstance(other, Todo):
            return self.uid != other.uid
        raise NotImplementedError(
            'Cannot compare Todo and {}'.format(type(other)))

    def clone(self):
        """
        Returns:
            Todo: an exact copy of self"""
        clone = copy.copy(self)
        clone.extra = clone.extra.clone()
        clone.alarms = copy.copy(self.alarms)
        return clone

    def __hash__(self):
        """
        Returns:
            int: hash of self. Based on self.uid."""
        return int(''.join(map(lambda x: '%.3d' % ord(x), self.uid)))
