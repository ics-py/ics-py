import unittest
from collections import defaultdict
from datetime import timedelta, datetime
from ics.eventlist import EventList
from ics.event import Event
from ics.icalendar import Calendar
from ics.utils import utcnow
from .fixture import cal1

SECOND = timedelta(seconds=1)
MINUTE = timedelta(minutes=1)
HOUR = timedelta(hours=1)
DAY = timedelta(days=1)
YEAR = 365*DAY

BEGIN = utcnow().replace(microsecond=0)  # Events don't handle microseconds
END = BEGIN + 3*HOUR


class TestEventList(unittest.TestCase):

    def test_evlist(self):

        l = EventList()
        self.assertEqual(len(l), 0)

        e = Event(begin=100, end=101)
        l.append(e)

        self.assertEqual(len(l), 1)
        self.assertEqual(l[0], e)

    def test_today(self):

        l = EventList()
        e = Event(begin=BEGIN, end=BEGIN+SECOND)
        l.append(e)

        self.assertEqual(l.today(), [e])
        l.append(Event(begin=BEGIN, end=BEGIN+DAY))
        self.assertEqual(l.today(strict=True), [e])

    def test_on(self):

        l = EventList()
        c = Calendar(cal1)
        l.append(c.events[0])
        day = "2013-10-29"
        self.assertIn(c.events[0], l.on(day))

    def test_now_large(self):

        l = EventList()
        e = Event("test", BEGIN-YEAR, BEGIN+YEAR)
        l.append(e)

        self.assertIn(e, l.now())

    def test_now_short(self):

        l = EventList()
        t = utcnow()
        e = Event("test", t-SECOND, t+SECOND)
        l.append(e)

        self.assertIn(e, l.now())

    def test_at_is_now(self):

        l = EventList()
        e = Event("test", BEGIN-SECOND, BEGIN+SECOND)
        l.append(e)

        self.assertIn(e, l.at(BEGIN))

    def test_at_is_sooner(self):

        l = EventList()
        instant = BEGIN - MINUTE
        e = Event("test", BEGIN - 59*SECOND, BEGIN + SECOND)
        l.append(e)

        self.assertNotIn(e, l.at(instant))

    def test_at_is_later(self):

        l = EventList()
        instant = BEGIN + 60*SECOND
        e = Event("test", BEGIN - SECOND, BEGIN + 59*SECOND)
        l.append(e)

        self.assertNotIn(e, l.at(instant))

    def test_getitem(self):

        l = EventList()
        e = Event("test", BEGIN-SECOND, BEGIN+SECOND)
        l.append(e)
        getitem = l.__getitem__(e.begin)
        # getitem = l[e.begin]

        self.assertEqual([e], getitem)

    def test_getitem_datetime(self):

        l = EventList()
        t = datetime(2013, 3, 3, 10)
        e = Event("t", t, t+HOUR)
        l.append(e)

        self.assertEqual([e], l['2013-03-03'])

    def test_concurrent(self):

        l = EventList()
        e0 = Event("t0", BEGIN - HOUR, BEGIN + HOUR)
        e1 = Event("t1", BEGIN - 59*MINUTE, BEGIN + 59*MINUTE)
        l.append(e0)

        self.assertEqual([e0], l.concurrent(e1))

    def test_remove_duplicate_same(self):

        l = EventList()
        e = Event("t", BEGIN, END)
        l.append(e)
        l.append(e)
        l._remove_duplicates()

        self.assertEqual(1, len(l))

    def test_remove_duplicate_diff(self):

        l = EventList()
        e0 = Event("t0", BEGIN, END)
        e1 = Event("t0", BEGIN, END)
        l.append(e0)
        l.append(e1)
        l._remove_duplicates()

        self.assertEqual(2, len(l))

    def test_add_(self):

        l0 = EventList()
        l1 = EventList()
        e = Event("t", BEGIN, END)
        l0.append(e)
        l1.append(e)
        l2 = l0 + l1

        self.assertEqual(1, len(l2))

    def test_modifiers(self):
        schemata = (
            ('     start    stop   ', 'begin', 'end', 'both', 'any', 'inc', 'e.begin',    'e.end'),
            ('+---+  |        |    ',  False,  False,  False, False, False, BEGIN-2*HOUR, BEGIN-HOUR),
            ('   +---+        |    ',  False,  False,  False, False, False, BEGIN-HOUR,   BEGIN),
            ('   +---+-+      |    ',  False,   True,  False,  True, False, BEGIN-HOUR,   BEGIN+HOUR),
            ('    +--+--------+    ',  False,   True,  False,  True, False, BEGIN-HOUR,   END),
            ('    +--+--------+-+  ',  False,  False,  False,  True, False, BEGIN-HOUR,   END+HOUR),
            ('       +-----+  |    ',   True,   True,   True,  True, False, BEGIN,        END-HOUR),
            ('       +--------+    ',   True,   True,   True,  True, False, BEGIN,        END),
            ('       +--------+-+  ',   True,  False,  False,  True, False, BEGIN,        END+HOUR),
            ('       | +---+  |    ',   True,   True,   True,  True,  True, BEGIN+HOUR,   END-HOUR),
            ('       | +------+    ',   True,   True,   True,  True, False, BEGIN+HOUR,   END),
            ('       | +------+--+ ',   True,  False,  False,  True, False, BEGIN+HOUR,   END+HOUR),
            ('       |        +---+',  False,  False,  False, False, False, END,          END+HOUR),
            ('       |        |+--+',  False,  False,  False, False, False, END+HOUR,     END+2*HOUR),
        )
        names = schemata[0]
        expected_results = defaultdict(list)
        all_events = EventList()
        for line in schemata[1:]:
            e = Event(line[0], begin=line[-2], end=line[-1])
            all_events.append(e)
            for i in range(1, len(names)-2):
                if line[i]:
                    expected_results[names[i]].append(e.name)
        for modifier in names[1:-2]:
            self.assertEqual([event.name for event in all_events[BEGIN:END:modifier]],
                             expected_results[modifier])

    def test_inc_empty(self):

        l = EventList()
        l = l[::'inc']

        self.assertEqual([], l)

    def test_inc(self):

        l = EventList()
        e0 = Event(begin=BEGIN, end=END)
        l.append(e0)
        l = l[BEGIN - MINUTE:END + MINUTE:'inc']

        self.assertEqual([e0], l)

    def test_end(self):

        l = EventList()
        e1 = Event(begin=BEGIN + 10*MINUTE, end=END - 10*MINUTE)
        l.append(e1)
        l = l[:END:'end']

        self.assertEqual([e1], l)

    def test_raise(self):

        l = EventList()

        with self.assertRaises(ValueError):
            l[::'dne']
            l[BEGIN::'cni']
            l[BEGIN:END:'htob']
            l[:END:'nigeb']

    def test_begin(self):

        l = EventList()
        e1 = Event(begin=BEGIN + 10*MINUTE, end=END - 10*MINUTE)
        l.append(e1)
        l = l[BEGIN::'begin']

        self.assertEqual([e1], l)

    def test_both(self):

        l = EventList()
        e1 = Event(begin=BEGIN + 10*MINUTE, end=END - 10*MINUTE)
        l.append(e1)
        l = l[BEGIN:END:]

        self.assertEqual([e1], l)

    def test_set_slice_fail(self):

        l = EventList()
        for i in range(6):
            l.append(Event())
        with self.assertRaises(ValueError):
            l[2:4] = [Event(), "coucou, tu veux voir ma b*** ?"]

    def test_set_slice(self):

        fix = [Event(), Event(), Event(), Event(), Event(), Event()]
        fix2 = [Event(name="test"), Event(name="test2")]

        l = EventList(fix)
        l[2:4] = fix2
        fix[2:4] = fix2

        self.assertSequenceEqual(sorted(fix), sorted(l))

    def test_set_elem_fail(self):
        l = EventList([Event(), Event()])
        with self.assertRaises(ValueError):
            l[3] = "plop"
