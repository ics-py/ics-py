import unittest
from ics.icalendar import Calendar
from ics.component import Component
from ics.parse import Container
from .fixture import cal2


class TestComponent(unittest.TestCase):

    def test_valueerror(self):

        with self.assertRaises(ValueError):
            Calendar(cal2)

    def test_abstract(self):
        with self.assertRaises(NotImplementedError):
            Component._from_container(Container(name='VCALENDAR'))

    def test_bad_type(self):
        container = Container(name='VINVALID')
        with self.assertRaises(ValueError):
            Calendar._from_container(container)
