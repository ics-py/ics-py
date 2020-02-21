import os

from ics.icalendar import Calendar
from .fixture import cal32


def test_issue_90():
    Calendar(cal32)


def test_fixtures_case_meetup():
    with open(os.path.join(os.path.dirname(__file__), "fixtures/case_meetup.ics")) as f:
        Calendar(f.read())


def test_fixtures_encoding():
    with open(os.path.join(os.path.dirname(__file__), "fixtures/encoding.ics")) as f:
        Calendar(f.read())


def test_fixtures_groupscheduled():
    with open(os.path.join(os.path.dirname(__file__), "fixtures/groupscheduled.ics")) as f:
        Calendar(f.read())


def test_fixtures_multiple():
    with open(os.path.join(os.path.dirname(__file__), "fixtures/multiple.ics")) as f:
        Calendar.parse_multiple(f.read())


def test_fixtures_recurrence():
    with open(os.path.join(os.path.dirname(__file__), "fixtures/recurrence.ics")) as f:
        Calendar(f.read())


def test_fixtures_small():
    with open(os.path.join(os.path.dirname(__file__), "fixtures/small.ics")) as f:
        Calendar(f.read())


def test_fixtures_time():
    with open(os.path.join(os.path.dirname(__file__), "fixtures/time.ics")) as f:
        Calendar(f.read().replace("BEGIN:VCALENDAR", "BEGIN:VCALENDAR\nPRODID:Fixture"))


def test_fixtures_timezoned():
    with open(os.path.join(os.path.dirname(__file__), "fixtures/timezoned.ics")) as f:
        Calendar(f.read())


def test_fixtures_utf_8_emoji():
    with open(os.path.join(os.path.dirname(__file__), "fixtures/utf-8-emoji.ics")) as f:
        Calendar(f.read())
