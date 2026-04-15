"""Test for GitHub issue #411: RSVP parameter leads to TypeError on serialization.

Parsing a calendar with ATTENDEE lines containing RSVP=TRUE should
round-trip correctly without raising TypeError.
"""

from ics import Calendar
from ics.attendee import Attendee

ICS_WITH_RSVP = """\
BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Test//Test//EN
BEGIN:VEVENT
DTSTART:20240101T120000Z
DTEND:20240101T130000Z
SUMMARY:Test Event
ATTENDEE;RSVP=TRUE;CN=Alice:mailto:alice@example.com
ATTENDEE;RSVP=FALSE;CN=Bob:mailto:bob@example.com
END:VEVENT
END:VCALENDAR
"""


def test_issue_411_rsvp_roundtrip():
    """Parsing and re-serializing a calendar with RSVP=TRUE must not crash."""
    cal = Calendar(ICS_WITH_RSVP)
    events = list(cal.events)
    assert len(events) == 1

    attendees = list(events[0].attendees)
    assert len(attendees) == 2

    # Verify RSVP values are accessible as bools
    rsvp_values = {a.common_name: a.rsvp for a in attendees}
    assert rsvp_values["Alice"] is True
    assert rsvp_values["Bob"] is False

    # The critical test: serialization must not raise TypeError
    output = cal.serialize()
    assert "RSVP=TRUE" in output
    assert "RSVP=FALSE" in output
