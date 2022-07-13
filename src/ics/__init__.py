from .alarm import *
from .alarm import __all__ as all_alarms
from .attendee import Attendee, Organizer
from .component import Component
from .contentline import Container, ContentLine
from .event import Event
from .geo import Geo
from .icalendar import Calendar
from .rrule import rrule_eq  # ensure the monkey-patching is done
from .timespan import EventTimespan, Timespan, TodoTimespan
from .timezone import Timezone
from .todo import Todo

__all__ = [
    *all_alarms,
    "Attendee",
    "Calendar",
    "Component",
    "Container",
    "ContentLine",
    "Event",
    "EventTimespan",
    "Geo",
    "Organizer",
    "Timezone",
    "Timespan",
    "Todo",
    "TodoTimespan",
    "__version__",
]

__version__ = "0.8.0-dev"
