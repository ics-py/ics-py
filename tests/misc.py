from ics.icalendar import Calendar
from .fixture import cal32


def test_issue_90():
    Calendar(cal32)
