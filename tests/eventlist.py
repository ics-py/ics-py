import unittest
import arrow
from ics.eventlist import EventList
from ics.event import Event
from ics.icalendar import Calendar
from .fixture import cal1


class TestEventList(unittest.TestCase):

    from time import time

    def test_evlist(self):

        l = EventList()
        t = self.time()

        self.assertEqual(len(l), 0)

        e = Event(begin=t, end=t + 1)
        l.append(e)

        self.assertEqual(len(l), 1)
        self.assertEqual(l[0], e)

    def test_today(self):

        l = EventList()
        t = self.time()

        e = Event(begin=t, end=t + 1)
        l.append(e)

        self.assertEqual(l.today(), [e])
        l.append(Event(begin=t, end=t + 86400))
        self.assertEqual(l.today(strict=True), [e])

    def test_on(self):

        l = EventList()

        c = Calendar(cal1)
        l.append(c.events[0])
        day = "2013-10-29"
        self.assertIn(c.events[0], l.on(day))

    def test_now_large(self):

        l = EventList()
        t = arrow.now()

        e = Event("test", t.replace(years=-1), t.replace(years=+1))
        l.append(e)

        self.assertIn(e, l.now())

    def test_now_short(self):

        l = EventList()
        t = arrow.now()

        e = Event("test", t.replace(seconds=-1), t.replace(seconds=+1))
        l.append(e)

        self.assertIn(e, l.now())

    def test_at_is_now(self):

        l = EventList()
        t = arrow.now()
        instant = arrow.now()

        e = Event("test", t.replace(seconds=-1), t.replace(seconds=+1))
        l.append(e)

        self.assertIn(e, l.at(instant))

    def test_at_is_sooner(self):

        l = EventList()
        t = arrow.now()
        instant = arrow.now().replace(minutes=-1)

        e = Event("test", t.replace(seconds=-59), t.replace(seconds=+1))
        l.append(e)

        self.assertNotIn(e, l.at(instant))

    def test_at_is_later(self):

        l = EventList()
        t = arrow.now()
        instant = arrow.now().replace(minutes=+1)

        e = Event("test", t.replace(seconds=-1), t.replace(seconds=+59))
        l.append(e)

        self.assertNotIn(e, l.at(instant))

    def test_getitem(self):

        l = EventList()
        t = arrow.now()

        e = Event("test", t.replace(seconds=-1), t.replace(seconds=+1))
        l.append(e)
        getitem = l.__getitem__(e.begin)
        getitem = l[e.begin]

        self.assertEqual([e], getitem)

    def test_getitem_arrow(self):

        l = EventList()
        t = arrow.get("20130303T101010")

        e = Event("t", t.replace(hours=-1), t.replace(hours=+1))
        l.append(e)
        t = t.format('YYYY-MM-DD')

        self.assertEqual([e], l[t])

    def test_concurrent(self):

        l = EventList()
        t = arrow.now()

        e0 = Event("t0", t.replace(hours=-1), t.replace(hours=+1))
        e1 = Event("t1", t.replace(minutes=-59), t.replace(hours=+59))
        l.append(e0)

        self.assertEqual([e0], l.concurrent(e1))

    def test_remove_duplicate_same(self):

        l = EventList()
        t = arrow.now()

        e = Event("t", t.replace(hours=-1), t.replace(hours=+1))
        l.append(e)
        l.append(e)
        l._remove_duplicates()

        self.assertEqual(1, len(l))

    def test_remove_duplicate_diff(self):

        l = EventList()
        t = arrow.now()

        e0 = Event("t0", t.replace(hours=-1), t.replace(hours=+1))
        e1 = Event("t0", t.replace(hours=-1), t.replace(hours=+1))
        l.append(e0)
        l.append(e1)
        l._remove_duplicates()

        self.assertEqual(2, len(l))

    def test_add_(self):

        l0 = EventList()
        l1 = EventList()
        t = arrow.now()

        e = Event("t", t.replace(hours=-1), t.replace(hours=+1))
        l0.append(e)
        l1.append(e)
        l2 = l0 + l1

        self.assertEqual(1, len(l2))

    def test_inc_empty(self):

        l = EventList()
        l = l[::'inc']

        self.assertEqual([], l)

    def test_inc(self):

        l = EventList()
        t = arrow.now()

        e0 = Event(begin=t.replace(hours=-1), end=t.replace(hours=+1))
        e1 = Event(begin=t.replace(minutes=-30), end=t.replace(minutes=+30))
        l.append(e0)
        l = l[e1.begin:e1.end:'inc']

        self.assertEqual([e0], l)

    def test_end(self):

        l = EventList()
        t = arrow.now()

        e0 = Event(begin=t.replace(hours=-1), end=t.replace(hours=+1))
        e1 = Event(begin=t.replace(minutes=-30), end=t.replace(minutes=+30))
        l.append(e1)
        l = l[:e0.end:'end']

        self.assertEqual([e1], l)

    def test_raise(self):

        l = EventList()
        t = arrow.now()

        e = Event(begin=t.replace(hours=-1), end=t.replace(hours=+1))

        with self.assertRaises(ValueError):
            l[::'dne']
            l[e.begin::'cni']
            l[e.begin:e.end:'htob']
            l[:e.end:'nigeb']

    def test_begin(self):

        l = EventList()
        t = arrow.now()

        e0 = Event(begin=t.replace(hours=-1), end=t.replace(hours=+1))
        e1 = Event(begin=t.replace(minutes=-30), end=t.replace(minutes=+30))
        l.append(e1)
        l = l[e0.begin::'begin']

        self.assertEqual([e1], l)

    def test_both(self):

        l = EventList()
        t = arrow.now()

        e0 = Event(begin=t.replace(hours=-1), end=t.replace(hours=+1))
        e1 = Event(begin=t.replace(minutes=-30), end=t.replace(minutes=+30))
        l.append(e1)
        l = l[e0.begin:e0.end:]

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
