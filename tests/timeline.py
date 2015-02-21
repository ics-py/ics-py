import unittest
import arrow
from time import time

from ics.event import Event
from ics.timeline import Timeline
from ics.icalendar import Calendar


class TestTimeline(unittest.TestCase):

    def test_type(self):

        c = Calendar()
        self.assertIsInstance(c.timeline, Timeline)

    def test_iter_is_ordered(self):
        c = Calendar()
        c.events.add(Event(begin=1236))
        c.events.add(Event(begin=1235))
        c.events.add(Event(begin=1234))

        last = None
        for event in c.timeline:
            if last is not None:
                self.assertGreaterEqual(event, last)
            last = event

    def test_iter_over_all(self):
        c = Calendar()
        c.events.add(Event(begin=1234))
        c.events.add(Event(begin=1235))
        c.events.add(Event(begin=1236))

        i = 0
        for event in c.timeline:
            i += 1

        self.assertEqual(i, 3)

    def test_iter_does_not_show_undefined_events(self):
        c = Calendar()

        empty = Event()
        c.events.add(empty)
        c.events.add(Event(begin=1234))
        c.events.add(Event(begin=1235))

        for event in c.timeline:
            self.assertIsNot(empty, event)
