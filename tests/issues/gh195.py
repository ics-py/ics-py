import pytest

from ics import Calendar, ContentLine


def test_gh195_override_prodid():
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "X-WR-CALNAME:Jason Hines",
        "X-APPLE-CALENDAR-COLOR:#996633",
        "END:VCALENDAR",
    ]
    with pytest.raises(
        ValueError, match="attribute PRODID is required but got no value"
    ):
        Calendar(lines)

    calendar = Calendar()
    assert calendar.prodid == Calendar.DEFAULT_PRODID
    assert (
        ContentLine("PRODID", value=Calendar.DEFAULT_PRODID) in calendar.to_container()
    )

    test_prodid = "TEST_PRODID 123456 GitHub Issue 195"
    lines.insert(1, "PRODID:" + test_prodid)
    calendar = Calendar(lines)
    assert calendar.prodid == test_prodid
    assert ContentLine("PRODID", value=test_prodid) in calendar.to_container()
