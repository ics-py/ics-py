import datetime
from urllib.parse import urlparse

from dateutil.rrule import rruleset

from ics import Calendar, ContentLine, Event, EventTimespan, Organizer, Timezone
from ics.timezone import TimezoneDaylightObservance

rrule = rruleset()
rrule.rdate(datetime.datetime(2021, 3, 14, 2, 0))
tzinfo = Timezone(
    "America/Toronto",
    observances=[
        TimezoneDaylightObservance(
            tzoffsetfrom=datetime.timedelta(days=-1, seconds=68400),
            tzoffsetto=datetime.timedelta(days=-1, seconds=72000),
            rrule=rrule,
            tzname="EDT",
            comment=None,
        )
    ],
)
tzinfo.extra_params["TZID"] = {"X-RICAL-TZSOURCE": ["TZINFO"]}
organizer = Organizer(
    email=urlparse("mailto:infosouth@someptc.ca"),
    common_name="Some Physical Therapy Centres",
)
event = Event(
    timespan=EventTimespan(
        begin_time=datetime.datetime(2021, 7, 19, 9, 0, tzinfo=tzinfo),
        end_time=datetime.datetime(2021, 7, 19, 10, 0, tzinfo=tzinfo),
        duration=None,
        precision="second",
    ),
    summary="A. Person (MVA Physio Subsequent)",
    uid="20124@somephysioclinic.janeapp.com",
    description="",
    location="Some Physical Therapy Centres - 1234 St Unnamed Blvd, 123, Ottawa",
    url=None,
    status="CONFIRMED",
    created=None,
    last_modified=None,
    dtstamp=datetime.datetime(
        2021, 8, 18, 11, 32, 51, tzinfo=Timezone.from_tzid("UTC")
    ),
    alarms=[],
    attach=[],
    classification=None,
    transparent=None,
    organizer=organizer,
    geo=None,
    attendees=[],
    categories=[],
)
event.extra.append(ContentLine(name="SEQUENCE", value="6044449"))
calendar = Calendar(
    version="2.0",
    prodid="-//com.denhaven2/NONSGML ri_cal gem//EN",
    events=[event],
    todos=[],
)
calendar.extra.extend(
    [
        ContentLine(name="CALSCALE", value="GREGORIAN"),
        ContentLine(
            name="X-WR-CALNAME",
            value=":Some Physical Therapy Centres Appointments",
        ),
    ]
)
calendar.extra_params["PRODID"] = {"X-RICAL-TZSOURCE": ["TZINFO"]}


def cmp(a, b):
    assert a.events[0].begin.tzinfo.extra_params == tzinfo.extra_params
    assert a.events[0].begin.tzinfo == tzinfo
    assert (
        a.events[0].begin.tzinfo.extra_params == b.events[0].begin.tzinfo.extra_params
    )
    assert a.events[0].begin.tzinfo == b.events[0].begin.tzinfo
    assert a.events[0] == b.events[0]
    assert a.extra_params == b.extra_params
    assert a.extra == b.extra
    assert a == b


def test_issue_268_tzinfo_x_parm():
    inp = r"""
BEGIN:VCALENDAR
PRODID;X-RICAL-TZSOURCE=TZINFO:-//com.denhaven2/NONSGML ri_cal gem//EN
CALSCALE:GREGORIAN
VERSION:2.0
X-WR-CALNAME::Some Physical Therapy Centres Appointments
BEGIN:VTIMEZONE
TZID;X-RICAL-TZSOURCE=TZINFO:America/Toronto
BEGIN:DAYLIGHT
DTSTART:20210314T020000
RDATE:20210314T020000
TZOFFSETFROM:-0500
TZOFFSETTO:-0400
TZNAME:EDT
END:DAYLIGHT
END:VTIMEZONE
BEGIN:VEVENT
DTEND;TZID=America/Toronto;VALUE=DATE-TIME:20210719T100000
STATUS:CONFIRMED
DTSTART;TZID=America/Toronto;VALUE=DATE-TIME:20210719T090000
DTSTAMP;VALUE=DATE-TIME:20210818T113251Z
UID:20124@somephysioclinic.janeapp.com
DESCRIPTION:
SUMMARY:A. Person (MVA Physio Subsequent)
ORGANIZER;CN="Some Physical Therapy Centres":mailto:infosouth@someptc
 .ca
LOCATION:Some Physical Therapy Centres - 1234 St Unnamed Blvd\, 123\, O
 ttawa
SEQUENCE:6044449
END:VEVENT
END:VCALENDAR
""".strip()
    cal = Calendar(inp)
    cmp(cal, calendar)
    ser = cal.serialize()
    deser = Calendar(ser)
    cmp(cal, deser)
