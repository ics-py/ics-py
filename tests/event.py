import unittest
from datetime import timedelta
from ics.event import Event
from ics.icalendar import Calendar
from .fixture import cal12, cal13


class TestEvent(unittest.TestCase):

    def test_event(self):
        e = Event(begin=0, end=20)
        self.assertEqual(e.begin.timestamp, 0)
        self.assertEqual(e.end.timestamp, 20)
        self.assertTrue(e.has_end())
        self.assertFalse(e.all_day)

        f = Event(begin=10, end=30)
        self.assertTrue(e < f)
        self.assertTrue(e <= f)
        self.assertTrue(f > e)
        self.assertTrue(f >= e)

    def test_or(self):
        g = Event(begin=0, end=10) | Event(begin=10, end=20)
        self.assertEqual(g, (None, None))

        g = Event(begin=0, end=20) | Event(begin=10, end=30)
        self.assertEqual(tuple(map(lambda x: x.timestamp, g)), (10, 20))

        g = Event(begin=0, end=20) | Event(begin=5, end=15)
        self.assertEqual(tuple(map(lambda x: x.timestamp, g)), (5, 15))

        g = Event() | Event()
        self.assertEqual(g, (None, None))

    def test_event_with_duration(self):
        c = Calendar(cal12)
        e = c.events[0]
        self.assertEqual(e._duration, timedelta(1, 3600))
        self.assertEqual(e.end - e.begin, timedelta(1, 3600))

    def test_not_duration_and_end(self):
        self.assertRaises(ValueError, Calendar, cal13)

    def test_duration_output(self):
        e = Event(begin=0, duration=timedelta(1, 23))
        lines = str(e).split('\n')
        self.assertIn('DTSTART:19700101T000000Z', lines)
        self.assertIn('DURATION:P1DT23S', lines)

    def test_make_all_day(self):
        e = Event(begin=0, end=20)
        begin = e.begin
        e.make_all_day()
        self.assertEqual(e.begin, begin)
        self.assertEqual(e._end_time, None)
        self.assertEqual(e._duration, None)
