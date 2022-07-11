from datetime import *
from urllib.parse import urlparse

from dateutil.parser import isoparse

from ics import *


def test_issue_269_missing_alarms():
    c = Calendar()
    e = Event()
    e.begin = e.dtstamp = isoparse("2021-01-01 11:00:00")
    e.duration = timedelta(minutes=30)
    # TODO get rid of all the urlparse calls
    e.alarms = [
        DisplayAlarm(timedelta(minutes=0), description="ALARM!"),
        DisplayAlarm(e.begin, description="ALARM!"),
        AudioAlarm(
            timedelta(minutes=-5), attach=urlparse("http://example.com/alarm.ogg")
        ),
        AudioAlarm(
            e.begin - timedelta(minutes=5),
            attach=urlparse("http://example.com/image.jpg"),
        ),
        EmailAlarm(
            datetime.utcfromtimestamp(0),
            repeat=0,
            duration=timedelta(minutes=0),
            summary="Subject",
            description="Body",
            attendees=[Attendee(urlparse("test@example.com"), common_name="Tester")],
            attach=[urlparse("http://example.com/image.jpg")],
        ),
        EmailAlarm(
            e.begin,
            repeat=5,
            duration=timedelta(minutes=5),
            summary="Subject",
            description="Body",
            attendees=[
                Attendee(urlparse("test@example.com"), common_name="Tester"),
                Attendee(urlparse("room@example.com"), user_type="ROOM"),
            ],
        ),
        DisplayAlarm(
            timedelta(minutes=5),
            repeat=5,
            duration=timedelta(minutes=5),
            description="ALARM!",
        ),
    ]
    e.name = "Test Event"
    e.uid = "event@example.com"
    c.events.append(e)

    ser = c.serialize()
    deser = Calendar(ser)

    for a1, a2 in zip(deser.events[0].alarms, c.events[0].alarms):
        # TODO ignore __merge_next
        assert not [
            p
            for p in a1.extra_params.pop("ATTENDEES", [])
            if p != {"__merge_next": ["FALSE"]}
        ]
        assert not [
            p
            for p in a1.extra_params.pop("ATTACH", [])
            if p != {"__merge_next": ["FALSE"]}
        ]
        assert a1 == a2
    assert deser == c
    assert deser.serialize() == ser
