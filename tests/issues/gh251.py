from datetime import datetime, timedelta

import pytest

from ics import Calendar, Event, __version__
from ics.event import (
    default_dtstamp_factory,
    default_uid_factory,
    deterministic_event_data,
)
from ics.timezone import UTC

CALENDAR = """
BEGIN:VCALENDAR
VERSION:2.0
PRODID:ics.py {version} - http://git.io/lLljaA
BEGIN:VEVENT
DTSTART:20000201T120000
SUMMARY:second
UID:{uid}
DTSTAMP:{dtstamp}
END:VEVENT
BEGIN:VEVENT
DTSTART:20000401T120000
SUMMARY:fourth
UID:{uid}
DTSTAMP:{dtstamp}
END:VEVENT
BEGIN:VEVENT
DTSTART:20000301T120000
SUMMARY:third
UID:{uid}
DTSTAMP:{dtstamp}
END:VEVENT
BEGIN:VEVENT
DTSTART:20000101T120000
SUMMARY:first
UID:{uid}
DTSTAMP:{dtstamp}
END:VEVENT
END:VCALENDAR
""".strip().replace(
    "\n", "\r\n"
)


def make_calendar() -> Calendar:
    cal = Calendar()
    cal.events.append(Event("second", datetime(2000, 2, 1, 12, 0)))
    cal.events.append(Event("fourth", datetime(2000, 4, 1, 12, 0)))
    cal.events.append(Event("third", datetime(2000, 3, 1, 12, 0)))
    cal.events.append(Event("first", datetime(2000, 1, 1, 12, 0)))
    return cal


@pytest.fixture(name="cal")
def calendar() -> Calendar:
    """Fixture Calendar for tests."""
    return make_calendar()


def test_chronological_order(cal: Calendar) -> None:
    assert [e.summary for e in cal.events] == ["second", "fourth", "third", "first"]

    cal.events = sorted(cal.events)
    assert [e.summary for e in cal.events] == ["first", "second", "third", "fourth"]

    cal.events = sorted(cal.events, key=lambda e: e.summary)
    assert [e.summary for e in cal.events] == ["first", "fourth", "second", "third"]


@deterministic_event_data
def test_deterministic_events_deco(cal: Calendar) -> None:
    uid = default_uid_factory.get()()
    dtstamp = default_dtstamp_factory.get()().strftime("%Y%m%dT%H%M%SZ")
    assert cal.serialize().strip() == CALENDAR.format(
        uid=uid, dtstamp=dtstamp, version=__version__
    )

    assert cal == make_calendar()
    assert cal.serialize() == make_calendar().serialize()


def test_deterministic_events_cm():
    with deterministic_event_data():
        cal1 = make_calendar()
        cal2 = make_calendar()

        uid = default_uid_factory.get()()
        dtstamp = default_dtstamp_factory.get()().strftime("%Y%m%dT%H%M%SZ")

        assert uid == default_uid_factory.get()()
        assert dtstamp == default_dtstamp_factory.get()().strftime("%Y%m%dT%H%M%SZ")

    cal3 = make_calendar()

    assert cal1.serialize().strip() == CALENDAR.format(
        uid=uid, dtstamp=dtstamp, version=__version__
    )

    assert cal1.serialize() == cal2.serialize()
    assert cal1 == cal2

    assert uid != default_uid_factory.get()()
    assert dtstamp != default_dtstamp_factory.get()().strftime("%Y%m%dT%H%M%SZ")

    assert cal1.serialize() != cal3.serialize()
    assert cal1 != cal3


def test_deterministic_events_cm_params():
    uid = "gh251-test-uid@example.com"
    dtstamp_dt = datetime.now().astimezone(UTC) - timedelta(days=1)
    dtstamp = dtstamp_dt.strftime("%Y%m%dT%H%M%SZ")

    with deterministic_event_data(uid=uid, dtstamp=dtstamp_dt):
        cal = make_calendar()
        assert uid == default_uid_factory.get()()
        assert dtstamp == default_dtstamp_factory.get()().strftime("%Y%m%dT%H%M%SZ")

    assert cal.serialize().strip() == CALENDAR.format(
        uid=uid, dtstamp=dtstamp, version=__version__
    )
    assert uid != default_uid_factory.get()()
    assert dtstamp != default_dtstamp_factory.get()().strftime("%Y%m%dT%H%M%SZ")
