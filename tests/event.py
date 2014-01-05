import unittest
from ics.event import Event


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
