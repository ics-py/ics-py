from ics import Calendar


cal_no_name = [
    "BEGIN:VCALENDAR",
    "VERSION:2.0",
    "PRODID:-//Apple Inc.//Mac OS X 10.13.5//EN",
    "CALSCALE:GREGORIAN",
    "BEGIN:VEVENT",
    r"DESCRIPTION:Title: My event",
    "END:VEVENT",
    "END:VCALENDAR",
]


cal_name = [
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

cal_xname = [
    "BEGIN:VCALENDAR",
    "VERSION:2.0",
    "PRODID:-//Apple Inc.//Mac OS X 10.13.5//EN",
    "X-WR-CALNAME:a xname",
    "END:VCALENDAR",
]

cal_name_xname = [
    "BEGIN:VCALENDAR",
    "VERSION:2.0",
    "PRODID:-//Apple Inc.//Mac OS X 10.13.5//EN",
    "NAME:a name",
    "X-WR-CALNAME:a xname",
    "END:VCALENDAR",
]


def test_cal_name():
    calendar = Calendar(cal_name)
    assert calendar.name == "a name"


def test_cal_x_name():
    calendar = Calendar(cal_xname)
    assert calendar.name == "a xname"


def test_cal_both_names():
    calendar = Calendar(cal_name_xname)
    assert calendar.name == "a name"


def test_no_default_cal_name():
    calendar = Calendar()
    assert calendar.name is None

    calendar = Calendar(cal_no_name)
    assert calendar.name is None
