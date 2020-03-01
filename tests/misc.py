import os
import unittest

from ics import Event
from ics.icalendar import Calendar

from .fixture import cal32

DIR = os.path.dirname(__file__)


class TestEvent(unittest.TestCase):
    def test_issue_90(self):
        Calendar(cal32)

    def test_romeo_juliet(self):
        with open(os.path.join(DIR, "samples/wikisource/Romeo-and-Juliet.ics")) as f:
            event: Event = next(iter(Calendar(f.read()).events))
        with open(os.path.join(DIR, "samples/wikisource/Romeo-and-Juliet.txt")) as f:
            self.assertEqual(event.description, f.read())
