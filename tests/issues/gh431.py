"""Test for GitHub issue #431: zero-length duration produces invalid 'P' string.

A zero-length timedelta should serialize as 'P0S' (or similar valid form),
not as bare 'P'.
"""

import datetime

from ics.valuetype.datetime import DurationConverter


def test_issue_431_zero_duration():
    """A zero timedelta must serialize to 'P0S', not bare 'P'."""
    result = DurationConverter.serialize(datetime.timedelta(0))
    assert result != "P", f"Zero duration produced bare 'P', expected 'P0S' or similar"
    assert result == "P0S" or result == "PT0S"


def test_issue_431_zero_duration_in_alarm():
    """A TRIGGER with zero offset must produce valid duration in ICS output."""
    from ics import Calendar, Event
    from ics.alarm import DisplayAlarm

    cal = Calendar()
    e = Event(
        summary="Test",
        begin=datetime.datetime(2024, 1, 1, 12, 0, 0),
    )
    alarm = DisplayAlarm(trigger=datetime.timedelta(0), description="Now!")
    e.alarms.append(alarm)
    cal.events.append(e)

    output = cal.serialize()
    # Must not contain bare "TRIGGER:P\r\n"
    assert "TRIGGER:P\r\n" not in output
    # Should contain a valid duration like PT0S
    assert "TRIGGER:PT0S" in output or "TRIGGER:P0S" in output
