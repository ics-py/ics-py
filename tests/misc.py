import os
import unittest

from ics import Event
from ics.icalendar import Calendar
from .fixture import cal32


class TestEvent(unittest.TestCase):
    def test_issue_90(self):
        Calendar(cal32)

    def test_fixtures_case_meetup(self):
        with open(os.path.join(os.path.dirname(__file__), "fixtures/case_meetup.ics")) as f:
            Calendar(f.read())

    def test_fixtures_encoding(self):
        with open(os.path.join(os.path.dirname(__file__), "fixtures/encoding.ics")) as f:
            Calendar(f.read())

    def test_fixtures_groupscheduled(self):
        with open(os.path.join(os.path.dirname(__file__), "fixtures/groupscheduled.ics")) as f:
            Calendar(f.read())

    def test_fixtures_multiple(self):
        with open(os.path.join(os.path.dirname(__file__), "fixtures/multiple.ics")) as f:
            Calendar.parse_multiple(f.read())

    def test_fixtures_recurrence(self):
        with open(os.path.join(os.path.dirname(__file__), "fixtures/recurrence.ics")) as f:
            Calendar(f.read())

    def test_fixtures_small(self):
        with open(os.path.join(os.path.dirname(__file__), "fixtures/small.ics")) as f:
            Calendar(f.read())

    def test_fixtures_time(self):
        with open(os.path.join(os.path.dirname(__file__), "fixtures/time.ics")) as f:
            Calendar(f.read().replace("BEGIN:VCALENDAR", "BEGIN:VCALENDAR\nPRODID:Fixture"))

    def test_fixtures_timezoned(self):
        with open(os.path.join(os.path.dirname(__file__), "fixtures/timezoned.ics")) as f:
            Calendar(f.read())

    def test_fixtures_utf_8_emoji(self):
        with open(os.path.join(os.path.dirname(__file__), "fixtures/utf-8-emoji.ics")) as f:
            Calendar(f.read())

    def test_fixtures_romeo_juliet(self):
        with open(os.path.join(os.path.dirname(__file__), "fixtures/Romeo-and-Juliet.ics")) as f:
            event: Event = next(iter(Calendar(f.read()).events))
        with open(os.path.join(os.path.dirname(__file__), "fixtures/Romeo-and-Juliet.txt")) as f:
            self.assertEqual(event.description, f.read())

    def test_fixtures_spaces(self):
        with open(os.path.join(os.path.dirname(__file__), "fixtures/spaces.ics")) as f:
            Calendar(f.read())
