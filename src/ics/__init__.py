def load_converters():
    from ics.converter.base import AttributeConverter
    from ics.converter.component import ComponentConverter
    from ics.converter.special import TimezoneConverter, AlarmConverter, PersonConverter, RecurrenceConverter
    from ics.converter.timespan import TimespanConverter
    from ics.converter.value import AttributeValueConverter
    from ics.valuetype.base import ValueConverter
    from ics.valuetype.datetime import DateConverter, DatetimeConverter, DurationConverter, PeriodConverter, TimeConverter, UTCOffsetConverter
    from ics.valuetype.generic import BinaryConverter, BooleanConverter, CalendarUserAddressConverter, FloatConverter, IntegerConverter, RecurConverter, URIConverter
    from ics.valuetype.text import TextConverter
    from ics.valuetype.special import GeoConverter


load_converters()  # make sure that converters are initialized before any Component classes are defined

from .alarm import *  # noqa
from .alarm import __all__ as all_alarms
from .attendee import Attendee, Organizer
from .component import Component
from .event import Event
from .geo import Geo
from .grammar import Container, ContentLine
from .icalendar import Calendar
from .timespan import EventTimespan, Timespan, TodoTimespan
from .todo import Todo

__all__ = [
    *all_alarms,
    "Attendee",
    "Event",
    "Calendar",
    "Organizer",
    "Timespan",
    "EventTimespan",
    "TodoTimespan",
    "Todo",
    "Component",
    "__version__"
]

__version__ = "0.9.0-dev"
