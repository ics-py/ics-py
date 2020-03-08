import unittest
from collections.abc import Iterable
from datetime import datetime

import attr
from dateutil.tz import UTC as tzutc, gettz

from ics.event import Event
from ics.grammar.parse import Container
from ics.icalendar import Calendar
from ics.todo import Todo
from .fixture import cal1, cal10, cal12, cal14, cal34


class TestCalendar(unittest.TestCase):
    fixtures = [cal1, cal10, cal12]

    def test_init(self):
        c = Calendar(creator='tests')
        self.assertEqual(c.creator, 'tests')
        self.assertSequenceEqual(c.events, [])
        self.assertSequenceEqual(c.todos, [])
        self.assertEqual(c.method, None)
        self.assertEqual(c.scale, None)
        self.assertEqual(c.extra, Container(name='VCALENDAR'))
        self.assertEqual(c._timezones, {})

    def test_selfload(self):
        def filter(attr, value):
            return not attr.name.startswith("_classmethod") and not attr.name == "_timezones"

        for fix in self.fixtures:
            c = Calendar(fix)
            d = Calendar(str(c))
            self.assertEqual(attr.asdict(c, filter=filter), attr.asdict(d, filter=filter))
            self.assertEqual(c, d)
            self.assertEqual(c.events, d.events)
            self.assertEqual(c.todos, d.todos)

            e = Calendar(str(d))
            # cannot compare str(c) and str(d) because times are encoded differently
            self.assertEqual(str(d), str(e))

    def test_repr(self):
        c = Calendar()
        self.assertEqual(c.__repr__(), '<Calendar with 0 event and 0 todo>')

        c.events.append(Event())
        c.todos.append(Todo())
        self.assertEqual(c.__repr__(), '<Calendar with 1 event and 1 todo>')

        c.events.append(Event())
        c.todos.append(Todo())
        self.assertEqual(c.__repr__(), '<Calendar with 2 events and 2 todos>')

    def test_iter(self):
        for fix in self.fixtures:
            c = Calendar(imports=fix)
            s = str(c)
            self.assertIsInstance(c, Iterable)
            i_with_no_lr = map(lambda x: x.rstrip('\n'), c)
            self.assertSequenceEqual(s.split('\n'), list(i_with_no_lr))

    def test_eq(self):
        c0, c1 = Calendar(), Calendar()
        e = Event()

        c0.events.append(e)
        c1.events.append(e)

        self.assertEqual(c0, c1)

        t = Todo()

        c0.todos.append(t)
        c1.todos.append(t)

    def test_neq_len(self):
        c0, c1 = Calendar(), Calendar()
        e1 = Event()
        e2 = Event()

        c0.events.append(e1)
        c0.events.append(e2)

        c1.events.append(e1)

        self.assertNotEqual(c0, c1)

        t1 = Todo()
        t2 = Todo()

        c0.todos.append(t1)
        c0.todos.append(t2)

        c1.todos.append(t1)

        self.assertNotEqual(c0, c1)

    def test_eq_len(self):
        c0, c1 = Calendar(), Calendar()
        e = Event()

        c0.events.append(e)
        c1.events.append(e)

        self.assertEqual(c0, c1)

        t = Todo()

        c0.todos.append(t)
        c1.todos.append(t)

        self.assertEqual(c0, c1)

    def test_neq_events(self):
        c0, c1 = Calendar(), Calendar()
        e0, e1 = Event(), Event()

        c0.events.append(e0)
        c1.events.append(e1)

        self.assertNotEqual(c0, c1)

    def test_neq_todos(self):
        c0, c1 = Calendar(), Calendar()
        t0, t1 = Todo(), Todo()

        c0.events.append(t0)
        c1.events.append(t1)

        self.assertNotEqual(c0, c1)

    def test_neq_creator(self):
        c0, c1 = Calendar(), Calendar(creator="test")
        self.assertNotEqual(c0, c1)

    def test_creator(self):

        c0 = Calendar()
        c1 = Calendar()
        c0.creator = u'42'
        with self.assertRaises(TypeError):
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
        self.assertEqual(u'2.0', c.version)
        lines = str(c).splitlines()
        self.assertEqual(lines[:3], cal10.strip().splitlines()[:3])
        self.assertEqual("VERSION:2.0", lines[1])
        self.assertIn("PRODID", lines[2])

        c = Calendar(cal14)
        self.assertEqual(u'42', c.version)

    def test_events_setter(self):

        c = Calendar(cal1)
        e = Event()
        c.events = [e]

        self.assertEqual(c.events, [e])

    def test_todos_setter(self):

        c = Calendar(cal1)
        t = Todo()
        c.todos = [t]

        self.assertEqual(c.todos, [t])

    def test_clone(self):
        c0 = Calendar()
        e = Event()
        t = Todo()
        c0.events.append(e)
        c0.todos.append(t)
        c1 = c0.clone()

        self.assertEqual(c0.events, c1.events)
        self.assertEqual(c0.todos, c1.todos)
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
        e = next(iter(c.events))
        self.assertFalse(e.all_day)
        tz = gettz('Europe/Brussels')
        self.assertEqual(datetime(2013, 10, 29, 10, 30, tzinfo=tz), e.begin)
        self.assertEqual(datetime(2013, 10, 29, 11, 30, tzinfo=tz), e.end)
        self.assertEqual(1, len(c.events))
        t = next(iter(c.todos))
        self.assertEqual(datetime(2018, 2, 18, 15, 47, tzinfo=tzutc), t.dtstamp)
        self.assertEqual('Uid', t.uid)
        self.assertEqual(1, len(c.todos))

    def test_multiple(self):
        cals = Calendar.parse_multiple(cal34)
        self.assertEqual(len(cals), 2)

        e1 = list(cals[0].events)[0]
        self.assertEqual(e1.name, "a")
        e2 = list(cals[1].events)[0]
        self.assertEqual(e2.name, "b")
