from datetime import datetime, timedelta

from dateutil.tz import gettz

from ics import Calendar, Container, Event
from ics.timezone import Timezone

vevent = [
    "BEGIN:VEVENT",
    "SUMMARY:Jobba",
    "DTSTART;TZID={tzid}:20200121T070000",
    "DTEND;TZID={tzid}:20200121T153000",
    "UID:040000008200E00074C5B7101A82E00800000000B01768504EA0D5010000000000000000100000001A9B2363ACC29B4A85D65E582DC139B7",
    "CLASS:PUBLIC",
    "PRIORITY:5",
    "DTSTAMP:20191230T164515Z",
    "TRANSP:OPAQUE",
    "STATUS:CONFIRMED",
    "SEQUENCE:0",
    "END:VEVENT",
]

vtimezone = [
    "BEGIN:VTIMEZONE",
    "TZID:{tzid}",
    "BEGIN:DAYLIGHT",
    "TZOFFSETFROM:{offsmall}",
    "RRULE:FREQ=YEARLY;BYMONTH=3;BYDAY=-1SU",
    "DTSTART:19810329T020000",
    "TZNAME:MESZ",
    "TZOFFSETTO:{offbig}",
    "END:DAYLIGHT",
    "BEGIN:STANDARD",
    "TZOFFSETFROM:{offbig}",
    "RRULE:FREQ=YEARLY;BYMONTH=10;BYDAY=-1SU",
    "DTSTART:19961027T030000",
    "TZNAME:MEZ",
    "TZOFFSETTO:{offsmall}",
    "END:STANDARD",
    "END:VTIMEZONE",
]


def fmt(lines, **kwargs):
    return [s.format(**kwargs) for s in lines]


fixture1 = [
    "BEGIN:VCALENDAR",
    "PRODID:Tom",
    "VERSION:2.0",
    *fmt(vevent, tzid="Europe/Berlin"),
    "END:VCALENDAR",
]
fixture2_tz = fmt(vtimezone, tzid="W. Europe Standard Time", offbig="+0200", offsmall="+0100")
fixture2 = [
    "BEGIN:VCALENDAR",
    "PRODID:Tom",
    "VERSION:2.0",
    *fixture2_tz,
    *fmt(vevent, tzid="W. Europe Standard Time"),
    "END:VCALENDAR",
]
fixture3_tz = fmt(vtimezone, tzid="Europe/Berlin", offbig="+0900", offsmall="+0800")
fixture3 = [
    "BEGIN:VCALENDAR",
    "PRODID:Tom",
    "VERSION:2.0",
    *fixture3_tz,
    *fmt(vevent, tzid="Europe/Berlin"),
    "END:VCALENDAR",
]


def test_issue_181_timezone_ignored():
    cal1 = Calendar(fixture1)
    cal2 = Calendar(fixture2)
    cal3 = Calendar(fixture3)
    begin1 = cal1.events[0].begin
    begin2 = cal2.events[0].begin
    begin3 = cal3.events[0].begin
    tzinfo1 = begin1.tzinfo
    tzinfo2 = begin2.tzinfo
    tzinfo3 = begin3.tzinfo
    assert isinstance(tzinfo1, Timezone)
    assert tzinfo1 == Timezone.from_tzid("Europe/Berlin")
    assert tzinfo1.tzid.endswith("Europe/Berlin")
    assert tzinfo1.tzname(begin1) == "CET"
    assert tzinfo1.utcoffset(begin1) == timedelta(hours=1)
    assert isinstance(tzinfo2, Timezone)
    assert tzinfo2 == Timezone.from_container(Container("VTIMEZONE", fixture2_tz))
    assert tzinfo2.tzid == "W. Europe Standard Time"
    assert tzinfo2.tzname(begin2) == "MEZ"
    assert tzinfo2.utcoffset(begin2) == timedelta(hours=1)
    assert isinstance(tzinfo3, Timezone)
    assert tzinfo3 == Timezone.from_container(Container("VTIMEZONE", fixture3_tz))
    assert tzinfo3.tzid == "Europe/Berlin"
    assert tzinfo3.tzname(begin3) == "MEZ"
    assert tzinfo3.utcoffset(begin3) == timedelta(hours=8)


def test_issue_188_timezone_dropped():
    assert "DTSTART;TZID={tzid}:20200121T070000".format(tzid="Europe/Berlin") in Calendar(fixture1).serialize()
    assert "DTSTART;TZID={tzid}:20200121T070000".format(tzid="W. Europe Standard Time") in Calendar(fixture2).serialize()
    assert "DTSTART;TZID={tzid}:20200121T070000".format(tzid="Europe/Berlin") in Calendar(fixture3).serialize()

    event = Event(begin=datetime(2014, 1, 1, 0, 0, 0, tzinfo=gettz("US/Pacific")))
    ser = Calendar(events=[event]).serialize()
    assert "DTSTART:20140101T000000Z" not in ser
    assert "DTSTART;TZID=US/Pacific:20140101T000000" in ser
    assert Calendar(ser).events[0] == event
