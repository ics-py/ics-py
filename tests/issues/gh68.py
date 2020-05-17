from dateutil.tz import gettz

from ics import Event
from ics.grammar import lines_to_container


def test_issue_68_timezone_dropped():
    event = Event.from_container(lines_to_container([
        "BEGIN:VEVENT",
        "DTSTART;TZID=Europe/Berlin:20151104T190000",
        "END:VEVENT"
    ])[0])
    tz = event.begin.tzinfo
    assert tz == gettz("Europe/Berlin")
    assert tz.tzname(event.begin) == "CET"
