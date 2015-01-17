import unittest
from collections import Iterable
from six import PY2
import arrow

from ics.parse import Container

from ics.icalendar import Calendar
from ics.event import Event
from ics.eventlist import EventList

from .fixture import cal1, cal2, cal10, cal12, cal14


class TestCalendar(unittest.TestCase):

    fixtures = [cal1, cal10, cal12]

    def test_init(self):
        c = Calendar(creator='tests')
        self.assertEqual(c.creator, 'tests')
        self.assertIsInstance(c.events, EventList)
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

        c.events.append(Event())
        self.assertEqual(c.__urepr__(), '<Calendar with 1 event>')

        c.events.append(Event())
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

    def test_eventlist_is_same(self):
        c = Calendar()
        l = EventList()
        c.events = l
        self.assertIs(c.events, l)

    def test_empty_list_to_eventlist(self):
        c = Calendar()
        l = []
        c.events = l
        self.assertIsNot(c.events, l)
        self.assertIsInstance(c.events, EventList)
        self.assertSequenceEqual(sorted(c.events), sorted(l))

    def test_list_to_eventlist(self):
        c = Calendar()
        l = [Event(), Event(), Event(name='plop')]
        c.events = l
        self.assertIsNot(c.events, l)
        self.assertIsInstance(c.events, EventList)
        self.assertSequenceEqual(sorted(c.events), sorted(l))

    def test_eventlist_move(self):
        e = Event()
        c = Calendar()
        c.events.append(e)

        d = Calendar(events=c.events)

        self.assertIs(c.events, d.events)
        self.assertSequenceEqual([e], d.events)
        self.assertIs(e, d.events[0])

    def test_eq(self):
        # TODO : better equality check
        c0, c1 = Calendar(), Calendar()
        e = Event()

        c0.events.append(e)
        c1.events.append(e)

        self.assertEqual(c0, c1)

    def test_neq_len(self):
        c0, c1 = Calendar(), Calendar()
        e = Event()

        c0.events.append(e)
        c0.events.append(e)

        c1.events.append(e)

        self.assertNotEqual(c0, c1)

    def test_eq_len(self):
        c0, c1 = Calendar(), Calendar()
        e = Event()

        c0.events.append(e)
        c1.events.append(e)

        self.assertEqual(c0, c1)

    def test_neq(self):
        c0, c1 = Calendar(), Calendar()
        e0, e1 = Event(), Event()

        c0.events.append(e0)
        c1.events.append(e1)

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

    def test_events_eventlist(self):

        c = Calendar()
        l = EventList()
        e = Event()
        l.append(e)
        c.events = l

        self.assertEqual(c.events, [e])

    def test_events_set_int(self):

        c = Calendar()

        with self.assertRaises(ValueError):
            c.events = 42

    def test_clone(self):
        c0 = Calendar()
        e = Event()
        c0.events.append(e)
        c1 = c0.clone()

        self.assertTrue(len(c0.events) == len(c1.events))
        self.assertEqual(c0.events[0], c1.events[0])
        self.assertEqual(c0, c1)

    def test_multiple_calendars(self):

        with self.assertRaises(NotImplementedError):
            Calendar() + Calendar()

    def test_init_int(self):

        with self.assertRaises(TypeError):
            Calendar(42)

    def test_events_set_string(self):

        c = Calendar(cal1)
        e = "42"
        with self.assertRaises(ValueError):
            c.events = e

    def test_imports(self):
        c = Calendar(cal1)
        self.assertEqual(c.creator, '-//Apple Inc.//Mac OS X 10.9//EN')
        self.assertEqual(c.method, 'PUBLISH')
        self.assertIsInstance(c.events, EventList)
        e = c.events[0]
        self.assertFalse(e.all_day)
        self.assertEqual(arrow.get(2013, 10, 29, 9, 30), e.begin)
        self.assertEqual(arrow.get(2013, 10, 29, 10, 30), e.end)
        self.assertEqual(1, len(c.events))
