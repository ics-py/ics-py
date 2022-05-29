from __future__ import annotations

from datetime import datetime, timedelta, date

from freezegun import freeze_time
import pytest

from ics import Calendar, Event
from ics.timezone import UTC


@pytest.fixture
def calendar() -> Calendar:
    """Fixture calendar with all day events to use in tests."""
    cal = Calendar()
    cal.events.extend([
        Event("second", datetime(2000, 2, 1, 12, 0)),
        Event("fourth", datetime(2000, 4, 1, 12, 0)),
        Event("third", datetime(2000, 3, 1, 12, 0)),
        Event("first", datetime(2000, 1, 1, 12, 0)),
    ])
    return cal


@pytest.fixture
def calendar_datetime_events() -> Calendar:
    """Fixture calendar with events to use in tests."""
    cal = Calendar()
    cal.events.extend([
        Event(
            "first",
            begin=datetime(2000, 1, 1, 11, 0),
            end=datetime(2000, 1, 1, 11, 30)
        ),
        Event("second",
            begin=datetime(2000, 1, 1, 12, 0),
            end=datetime(2000, 1, 1, 13, 0),
        ),
        Event("third",
            begin=datetime(2000, 1, 2, 12, 0),
            end=datetime(2000, 1, 2, 13, 0),
        )
    ])
    return cal


def test_iteration(calendar: Calendar) -> None:
    """Test chronological iteration of a timeline.""" 
    assert [e.summary for e in calendar.timeline] == [
        "first", "second", "third", "fourth"
    ]

def test_on(calendar: Calendar) -> None:
    """Test returning events on a particualr day."""
    assert [e.summary for e in calendar.timeline.on(date(2000, 1, 1))] == ["first"]
    assert [e.summary for e in calendar.timeline.on(date(2000, 2, 1))] == ["second"]
    assert [e.summary for e in calendar.timeline.on(datetime(2000, 3, 1, 6, 0))] == [
        "third"
    ]


def test_start_after(calendar: Calendar) -> None:
    """Test chronological iteration starting at a specific time."""
    assert [e.summary for e in calendar.timeline.start_after(date(2000, 2, 1))] == [
        "second", "third", "fourth"
    ]


@pytest.mark.parametrize(
    "at_datetime,expected_events",
    [
        (datetime(2000, 1, 1, 11, 15), ["first"]),
        (datetime(2000, 1, 1, 11, 59), []),
        (datetime(2000, 1, 1, 12, 0), ["second"]),
        (datetime(2000, 1, 1, 12, 30), ["second"]),
        (datetime(2000, 1, 1, 12, 59), ["second"]),
        (datetime(2000, 1, 1, 13, 0), []),
    ],
)
def test_at(calendar_datetime_events: Calendar, at_datetime: datetime, expected_events: list[str]) -> None:
    """Test returning events at a specific time."""
    assert [
        e.summary for e in calendar_datetime_events.timeline.at(at_datetime)
    ] == expected_events


@freeze_time("2000-01-01 12:30:00")
def test_now(calendar_datetime_events: Calendar) -> None:
    assert [e.summary for e in calendar_datetime_events.timeline.now()] == ["second"]


@freeze_time("2000-01-01 13:00:00")
def test_now_no_match(calendar_datetime_events: Calendar) -> None:
    assert [e.summary for e in calendar_datetime_events.timeline.now()] == []


@freeze_time("2000-01-01 12:30:00")
def test_today(calendar_datetime_events: Calendar) -> None:
    assert [e.summary for e in calendar_datetime_events.timeline.today()] == ["first", "second"]


@pytest.mark.parametrize(
    "start,end,expected_events",
    [
        (datetime(2000, 1, 1, 10, 00), datetime(2000, 1, 2, 14, 00), ["first", "second", "third"]),
        (datetime(2000, 1, 1, 10, 00), datetime(2000, 1, 1, 14, 00), ["first", "second"]),
        (datetime(2000, 1, 1, 12, 00), datetime(2000, 1, 2, 14, 00), ["second", "third"]),
        (datetime(2000, 1, 1, 12, 00), datetime(2000, 1, 1, 14, 00), ["second"]),
    ],
)
def test_included(calendar_datetime_events: Calendar, start: datetime, end: datetime, expected_events: list[str]) -> None:
    assert [
        e.summary for e in calendar_datetime_events.timeline.included(start, end)
    ] == expected_events
