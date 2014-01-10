import unittest
from collections import Iterable
from six import PY3
PY2 = not PY3
from ics.icalendar import Calendar
from ics.event import Event
from ics.eventlist import EventList
from .fixture import cal1, cal2, cal10


class TestCalendar(unittest.TestCase):

    def test_imports(self):
        c = Calendar(cal1)
        self.assertEqual(1, len(c.events))

    def test_events(self):
        e = Event(begin=0, end=30)
        c = Calendar()
        c.events.append(e)
        d = Calendar(events=c.events)
        self.assertEqual(1, len(d.events))
        self.assertEqual(e, d.events[0])

    def test_selfload(self):
        c = Calendar(cal1)
        d = Calendar(str(c))
        self.assertEqual(c, d)
        for i in range(len(c.events)):
            e, f = c.events[i], d.events[i]
            self.assertEqual(e, f)
            self.assertEqual(e.begin, f.begin)
            self.assertEqual(e.end, f.end)
            self.assertEqual(e.name, f.name)

    def test_iter(self):
        c = cal2
        it = "".join(i for i in iter(c))

        if PY2:
            self.assertEqual(c, it)
            self.assertSequenceEqual(c, it)
        self.assertTrue(isinstance(c, Iterable))

    def test_iter_(self):
        c = Calendar()
        e = Event(begin=0, end=10)
        c.events.append(e)

        self.assertTrue(isinstance(c, Iterable))
        self.assertTrue(type(iter(c)), Iterable)

    def test_unicode(self):
        c = Calendar()
        e = Event(begin=0, end=30)
        c.events.append(e)

        self.assertEqual('<Calendar with 1 event>', c.__unicode__())
        if PY2:
            self.assertEqual('<Calendar with 1 event>', unicode(c))

    def test_eq(self):
        c0 = Calendar()
        c1 = Calendar()
        e = Event(begin=0, end=30)
        c0.events.append(e)
        c1.events.append(e)

        self.assertEqual(c0, c1)

    def test_eq_len(self):
        c0 = Calendar()
        c1 = Calendar()
        e = Event(begin=0, end=30)
        c0.events.append(e)
        c1.events.append(e)

        c0.events.append(e)

        self.assertNotEqual(c0, c1)

    def test_not_eq(self):
        c0 = Calendar()
        c1 = Calendar()
        e0 = Event(begin=0, end=30)
        e1 = Event(begin=0, end=30)
        c0.events.append(e0)
        c1.events.append(e1)

        self.assertNotEqual(c0, c1)

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

    def test_creator(self):

        c0 = Calendar()
        c1 = Calendar()
        c2 = Calendar()
        c0.creator = u'42'
        c1.creator = 42
        c2.creator = '42'

        self.assertEqual(c0.creator, u'42')
        self.assertEqual(c1.creator, u'42')
        self.assertEqual(c2.creator, u'42')

    def test_existing_creator(self):

        c = Calendar(cal1)

        self.assertEqual(c.creator, u'-//Apple Inc.//Mac OS X 10.9//EN')

        c.creator = "apple_is_a_fruit"

        self.assertEqual(c.creator, "apple_is_a_fruit")

    def test_scale(self):

        c = Calendar(cal10)

        self.assertEqual(c.scale, u'georgian')

    def test_version(self):

        c = Calendar(cal10)

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

    # def test_events_set_string(self):

    #     c = Calendar(cal1)
    #     e = "42"
    #     with self.assertRaises(ValueError):
    #         c.events = e
