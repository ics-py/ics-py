import unittest
from ics.icalendar import Calendar
from .fixture import cal2

class TestComponent(unittest.TestCase):

    def test_valueerror(self):

        with self.assertRaises(ValueError):
            Calendar(cal2)

