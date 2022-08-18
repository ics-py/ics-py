from datetime import date, datetime, timedelta

import pytest

from ics import Calendar, Event, Timezone, Todo
from ics.event import deterministic_event_data
from ics.timezone import UTC

SUMMARY = "test summary"


@deterministic_event_data()
@pytest.mark.parametrize(
    "begin,end,duration",
    [
        (
            datetime.fromisoformat("2022-09-16 12:00"),
            datetime.fromisoformat("2022-09-16 12:30"),
            timedelta(minutes=30),
        ),
        (
            date.fromisoformat("2022-09-16"),
            date.fromisoformat("2022-09-17"),
            timedelta(hours=24),
        ),
        (
            datetime.fromisoformat("2022-09-16 06:00"),
            datetime.fromisoformat("2022-09-17 08:30"),
            timedelta(days=1, hours=2, minutes=30),
        ),
    ],
)
def test_duration(begin: datetime, end: datetime, duration: timedelta) -> None:
    event = Event(SUMMARY, begin, end)
    assert event.duration == duration


@deterministic_event_data()
def test_comparisons() -> None:
    event1 = Event(SUMMARY, date(2022, 9, 6), date(2022, 9, 7))
    event2 = Event(SUMMARY, date(2022, 9, 8), date(2022, 9, 10))
    assert event1 < event2
    assert event1 <= event2
    assert event2 >= event1
    assert event2 > event1


@deterministic_event_data()
def test_within_and_includes() -> None:
    event1 = Event(SUMMARY, date(2022, 9, 6), date(2022, 9, 10))
    event2 = Event(SUMMARY, date(2022, 9, 7), date(2022, 9, 8))
    event3 = Event(SUMMARY, date(2022, 9, 9), date(2022, 9, 11))

    assert not event1.starts_within(event2)
    assert not event1.starts_within(event3)
    assert event2.starts_within(event1)
    assert not event2.starts_within(event3)
    assert event3.starts_within(event1)
    assert not event3.starts_within(event2)

    assert not event1.ends_within(event2)
    assert event1.ends_within(event3)
    assert event2.ends_within(event1)
    assert not event2.ends_within(event3)
    assert not event3.ends_within(event1)
    assert not event3.ends_within(event2)
    assert event2 > event1

    assert event1.includes(event2)
    assert not event1.includes(event3)
    assert not event2.includes(event1)
    assert not event2.includes(event3)
    assert not event3.includes(event1)
    assert not event3.includes(event2)

    assert not event1.is_included_in(event2)
    assert not event1.is_included_in(event3)
    assert event2.is_included_in(event1)
    assert not event2.is_included_in(event3)
    assert not event3.is_included_in(event1)
    assert not event3.is_included_in(event2)


@deterministic_event_data()
@pytest.mark.parametrize(
    "event1,event2,expect_intersects",
    [
        (
            Event(
                SUMMARY,
                date(2022, 9, 16),
                date(2022, 9, 17),
            ),
            Event(
                SUMMARY,
                date(2022, 9, 18),
                date(2022, 9, 19),
            ),
            False,
        ),
        (
            Event(
                SUMMARY,
                date(2022, 9, 16),
                date(2022, 9, 19),
            ),
            Event(
                SUMMARY,
                date(2022, 9, 17),
                date(2022, 9, 18),
            ),
            True,
        ),
        (
            Event(
                SUMMARY,
                date(2022, 9, 16),
                date(2022, 9, 18),
            ),
            Event(
                SUMMARY,
                date(2022, 9, 17),
                date(2022, 9, 19),
            ),
            True,
        ),
    ],
)
def test_intersects(event1: Event, event2: Event, expect_intersects: bool) -> None:
    assert event2.intersects(event1) == expect_intersects
