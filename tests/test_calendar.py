from ics import Calendar

cal = [
    "BEGIN:VCALENDAR",
    "VERSION:2.0",
    "PRODID:-//Apple Inc.//Mac OS X 10.13.5//EN",
    "Name:a name",
    "CALSCALE:GREGORIAN",
    "BEGIN:VEVENT",
    r"DESCRIPTION:Title: My event",
    "END:VEVENT",
    "END:VCALENDAR",
]

cal2 = [
    "BEGIN:VCALENDAR",
    "VERSION:2.0",
    "PRODID:-//Apple Inc.//Mac OS X 10.13.5//EN",
    "X-WR-CALNAME:a xname",
    "END:VCALENDAR",
]

cal3 = [
    "BEGIN:VCALENDAR",
    "VERSION:2.0",
    "PRODID:-//Apple Inc.//Mac OS X 10.13.5//EN",
    "X-WR-CALNAME:a xname",
    "END:VCALENDAR",
]


def test_cal_name():
    calendar = Calendar(cal)
    assert calendar.name == "a name"

def test_cal_x_name():
    calendar = Calendar(cal2)
    assert calendar.name == "a xname"

def test_cal_both_names():
    calendar = Calendar(cal2)
    # FIXME: what behavior should we expect here?
    # FIXME: In both cases, we need a test and we need to document it.
    assert calendar.name == "a name"

def test_no_default_cal_name():
    calendar = Calendar()
    assert calendar.name is None
