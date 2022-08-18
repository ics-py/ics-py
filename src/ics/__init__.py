"""
   isort:skip_file
"""
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


def initialize_converters():
    # order is very important here:
    # 1) all simple value type converters
    import ics.valuetype.base
    import ics.valuetype.generic
    import ics.valuetype.text
    import ics.valuetype.datetime
    import ics.valuetype.special

    # 2) all relatively simple attribute converters and advanced component converters
    import ics.converter.base
    import ics.converter.value
    import ics.converter.types.timespan
    import ics.converter.types.various

    # 3) converters for all remaining component subclasses
    from ics.converter.component import ComponentMeta

    # vTimezone is a Component
    import ics.converter.types.timezone

    ComponentMeta.BY_TYPE[Event] = ComponentMeta(Event)
    ComponentMeta.BY_TYPE[Todo] = ComponentMeta(Todo)

    # 4) the converter for the calendar
    import ics.converter.types.calendar

    global initialize_converters
    initialize_converters = lambda: None


def dump_converters():
    from pprint import pprint

    from ics.valuetype.base import ValueConverter

    print("ValueConverter.BY_TYPE:")
    pprint(ValueConverter.BY_TYPE)
    print("ValueConverter.BY_NAME:")
    pprint(ValueConverter.BY_NAME)
    from ics.converter.base import AttributeConverter

    print("AttributeConverter.BY_TYPE:")
    pprint(AttributeConverter.BY_TYPE)
    from ics.converter.component import ComponentMeta

    print("ComponentMeta.BY_TYPE:")
    pprint(ComponentMeta.BY_TYPE)
    print("Component.SUBTYPES:")
    pprint(Component.SUBTYPES)


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

__version__ = "0.8.0-dev0"
