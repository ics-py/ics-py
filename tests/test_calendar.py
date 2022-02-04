from ics import Calendar

lines = [
    "BEGIN:VCALENDAR",
    "VERSION:2.0",
    "PRODID:-//Apple Inc.//Mac OS X 10.13.5//EN",
    "CALSCALE:GREGORIAN",
    "BEGIN:VEVENT",
    r"DESCRIPTION:Title: My event",
    "END:VEVENT",
    "END:VCALENDAR",
]


def test_cal_name():
    calendar = Calendar(lines)

    assert calendar.name == Calendar.DEFAULT_CALNAME
