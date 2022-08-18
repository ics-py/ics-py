from ics import Calendar

lines = [
    "BEGIN:VCALENDAR",
    "VERSION:2.0",
    "PRODID:-//Apple Inc.//Mac OS X 10.13.5//EN",
    "CALSCALE:GREGORIAN",
    "BEGIN:VEVENT",
    r"DESCRIPTION:Title: UN127 Advanced Bash Shell Prog\nCustomer: Buzzy\nRefe",
    r" rence: 17-17719 \n",
    "END:VEVENT",
    "END:VCALENDAR",
]


def test_issue_210_embedded_newlines():
    calendar = Calendar(lines)
    description = calendar.events[0].description
    assert description.endswith("19 \n")
    assert (
        description
        == "Title: UN127 Advanced Bash Shell Prog\nCustomer: Buzzy\nReference: 17-17719 \n"
    )
    assert description.splitlines() == [
        "Title: UN127 Advanced Bash Shell Prog",
        "Customer: Buzzy",
        "Reference: 17-17719 ",
    ]
