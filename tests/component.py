import unittest
from ics.icalendar import Calendar
from ics.component import Component
from ics.parse import Container

fix1 = "BEGIN:BASETEST\r\nATTR:FOOBAR\r\nEND:BASETEST"

fix2 = "BEGIN:BASETEST\r\nATTR:FOO\r\nATTR2:BAR\r\nEND:BASETEST"


class TestComponent(unittest.TestCase):

    def test_abstract(self):
        with self.assertRaises(NotImplementedError):
            Component._from_container(Container(name='VCALENDAR'))

    def test_bad_type(self):
        container = Container(name='VINVALID')
        with self.assertRaises(ValueError):
            Calendar._from_container(container)

    def test_no_urepr(self):
        class Dummy(Component):
            pass
        d = Dummy()
        adress = hex(id(d))
        self.assertEqual('<Dummy at {}>'.format(adress), repr(d))



