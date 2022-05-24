from datetime import datetime, timedelta, date

from ics import Calendar, Event
from ics.timezone import UTC


def make_calendar():
    """Create a test calendar for use in tests."""
    cal = Calendar()
    cal.events.extend([
        Event("second", datetime(2000, 2, 1, 12, 0)),
        Event("fourth", datetime(2000, 4, 1, 12, 0)),
        Event("third", datetime(2000, 3, 1, 12, 0)),
        Event("first", datetime(2000, 1, 1, 12, 0)),
    ])
    return cal


def test_iteration():
    """Test chronological iteration of a timeline.""" 
    cal = make_calendar()
    assert [e.summary for e in cal.timeline] == [
        "first", "second", "third", "fourth"
    ]

def test_on():
    """Test returning events on a particualr day."""
    cal = make_calendar()
    timeline = cal.timeline
    assert [e.summary for e in cal.timeline.on(date(2000, 1, 1))] == ["first"]
    assert [e.summary for e in cal.timeline.on(date(2000, 2, 1))] == ["second"]
    assert [e.summary for e in cal.timeline.on(datetime(2000, 3, 1, 6, 0))] == [
        "third"
    ]


def test_start_after():
    """Test chronological iteration starting at a specific time."""
    cal = make_calendar()
    timeline = cal.timeline

    assert [e.summary for e in cal.timeline.start_after(date(2000, 2, 1))] == [
        "second", "third", "fourth"
    ]


def test_at():
    """Test returning events at a specific time."""
    cal = Calendar()
    cal.events.extend([
        Event(
            "earlier",
            begin=datetime(2000, 1, 1, 11, 0),
            end=datetime(2000, 1, 1, 11, 30)
        ),
        Event("event",
            begin=datetime(2000, 1, 1, 12, 0),
            end=datetime(2000, 1, 1, 13, 0),
        ),
        Event("later",
            begin=datetime(2000, 1, 2, 12, 0),
            end=datetime(2000, 1, 2, 13, 0),
        )
    ])
    assert [
        e.summary for e in cal.timeline.at(datetime(2000, 1, 1, 11, 59))
    ] == []
    assert [
        e.summary for e in cal.timeline.at(datetime(2000, 1, 1, 12, 0))
    ] == ["event"]
    assert [
        e.summary for e in cal.timeline.at(datetime(2000, 1, 1, 12, 30))
    ] == ["event"]
    assert [
        e.summary for e in cal.timeline.at(datetime(2000, 1, 1, 12, 59))
    ] == ["event"]
    assert [
        e.summary for e in cal.timeline.at(datetime(2000, 1, 1, 13, 0))
    ] == []


def test_now():
    now = datetime.now()

    cal = Calendar()
    cal.events.extend([
        Event(
            "before",
            begin=(now - timedelta(days=3)),
            end=(now - timedelta(days=2)),
        ),
        Event(
            "after",
            begin=(now + timedelta(days=2)),
            end=(now + timedelta(days=2)),
        ),
        Event(
            "now",
            begin=(now - timedelta(days=1)),
            end=(now + timedelta(days=1)),
        ),
    ])
    assert [e.summary for e in cal.timeline.now()] == ["now"]


def test_included():
    cal = Calendar()
    cal.events.extend([
        Event(
            "first",
            begin=datetime(2000, 1, 1, 11, 0),
            end=datetime(2000, 1, 1, 11, 30)
        ),
        Event(
            "second",
            begin=datetime(2000, 1, 1, 12, 0),
            end=datetime(2000, 1, 1, 13, 0),
        ),
        Event(
            "third",
            begin=datetime(2000, 1, 2, 12, 0),
            end=datetime(2000, 1, 2, 13, 0),
        ),
    ])
    assert [
        e.summary for e in cal.timeline.included(
            datetime(2000, 1, 1, 10, 00),
            datetime(2000, 1, 2, 14, 00),
        )
    ] == ["first", "second", "third"]
    assert [
        e.summary for e in cal.timeline.included(
            datetime(2000, 1, 1, 10, 00),
            datetime(2000, 1, 1, 14, 00),
        )
    ] == ["first", "second"]
    assert [
        e.summary for e in cal.timeline.included(
            datetime(2000, 1, 1, 12, 00),
            datetime(2000, 1, 2, 14, 00),
        )
    ] == ["second", "third"]
    assert [
        e.summary for e in cal.timeline.included(
            datetime(2000, 1, 1, 12, 00),
            datetime(2000, 1, 1, 14, 00),
        )
    ] == ["second"]
