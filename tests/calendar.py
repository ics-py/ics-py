import unittest
from collections import Iterable
from six import PY2
import arrow

from ics.parse import Container

from ics.icalendar import Calendar
from ics.event import Event

from .fixture import cal1, cal2, cal10, cal12, cal14


class TestCalendar(unittest.TestCase):

    fixtures = [cal1, cal10, cal12]

    def test_init(self):
        c = Calendar(creator='tests')
        self.assertEqual(c.creator, 'tests')
        self.assertSequenceEqual(c.events, [])
        self.assertEqual(c.method, None)
        self.assertEqual(c.scale, None)
        self.assertEqual(c._unused, Container(name='VCALENDAR'))
        self.assertEqual(c._timezones, {})

    def test_selfload(self):
        for fix in self.fixtures:
            c = Calendar(fix)
            d = Calendar(str(c))
            self.assertEqual(c, d)
            self.assertSequenceEqual(sorted(c.events), sorted(d.events))

            e = Calendar(str(d))
            # cannot compare str(c) and str(d) because times are encoded differently
            self.assertEqual(str(d), str(e))

    def test_urepr(self):
        # TODO : more cases
        c = Calendar()
        self.assertEqual(c.__urepr__(), '<Calendar with 0 event>')

        c.events.add(Event())
        self.assertEqual(c.__urepr__(), '<Calendar with 1 event>')

        c.events.add(Event())
        self.assertEqual(c.__urepr__(), '<Calendar with 2 events>')

    def test_repr(self):
        c = Calendar()
        self.assertEqual(c.__urepr__(), repr(c))

    def test_iter(self):
        for fix in self.fixtures:
            c = Calendar(imports=fix)
            s = str(c)
            self.assertIsInstance(c, Iterable)
            i_with_no_lr = map(lambda x: x.rstrip('\n'), c)
            self.assertSequenceEqual(s.split('\n'), list(i_with_no_lr))

    def test_eq(self):
        # TODO : better equality check
        c0, c1 = Calendar(), Calendar()
        e = Event()

        c0.events.add(e)
        c1.events.add(e)

        self.assertEqual(c0, c1)

    def test_neq_len(self):
        c0, c1 = Calendar(), Calendar()
        e1 = Event()
        e2 = Event()

        c0.events.add(e1)
        c0.events.add(e2)

        c1.events.add(e1)

        self.assertNotEqual(c0, c1)

    def test_eq_len(self):
        c0, c1 = Calendar(), Calendar()
        e = Event()

        c0.events.add(e)
        c1.events.add(e)

        self.assertEqual(c0, c1)

    def test_neq(self):
        c0, c1 = Calendar(), Calendar()
        e0, e1 = Event(), Event()

        c0.events.add(e0)
        c1.events.add(e1)

        self.assertNotEqual(c0, c1)

    def test_neq_creator(self):
        c0, c1 = Calendar(), Calendar(creator="test")
        self.assertNotEqual(c0, c1)

    def test_creator(self):

        c0 = Calendar()
        c1 = Calendar()
        c0.creator = u'42'
        with self.assertRaises(ValueError):
            c1.creator = 42

        self.assertEqual(c0.creator, u'42')

    def test_existing_creator(self):
        c = Calendar(cal1)
        self.assertEqual(c.creator, u'-//Apple Inc.//Mac OS X 10.9//EN')

        c.creator = u"apple_is_a_fruit"
        self.assertEqual(c.creator, u"apple_is_a_fruit")

    def test_scale(self):

        c = Calendar(cal10)

        self.assertEqual(c.scale, u'georgian')

    def test_version(self):

        c = Calendar(cal10)
        self.assertEqual(c.version, u'2.0')

        c = Calendar(cal14)
        self.assertEqual(c.version, u'42')

    def test_events_setter(self):

        c = Calendar(cal1)
        e = Event()
        c.events = [e]

        self.assertEqual(c.events, [e])

    def test_clone(self):
        c0 = Calendar()
        e = Event()
        c0.events.add(e)
        c1 = c0.clone()

        self.assertEqual(c0.events, c1.events)
        self.assertEqual(c0, c1)

    def test_multiple_calendars(self):

        with self.assertRaises(TypeError):
            Calendar() + Calendar()

    def test_init_int(self):

        with self.assertRaises(TypeError):
            Calendar(42)

    def test_imports(self):
        c = Calendar(cal1)
        self.assertEqual(c.creator, '-//Apple Inc.//Mac OS X 10.9//EN')
        self.assertEqual(c.method, 'PUBLISH')
        e = c.events[0]
        self.assertFalse(e.all_day)
        self.assertEqual(arrow.get(2013, 10, 29, 9, 30), e.begin)
        self.assertEqual(arrow.get(2013, 10, 29, 10, 30), e.end)
        self.assertEqual(1, len(c.events))
