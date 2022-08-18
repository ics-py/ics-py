from ics import Event
from ics.contentline import lines_to_container
from ics.timezone import Timezone


def test_issue_68_timezone_dropped():
    event = Event.from_container(
        lines_to_container(
            ["BEGIN:VEVENT", "DTSTART;TZID=Europe/Berlin:20151104T190000", "END:VEVENT"]
        )
    )
    tz = event.begin.tzinfo
    assert tz == Timezone.from_tzid("Europe/Berlin")
    assert tz.tzname(event.begin) == "CET"
