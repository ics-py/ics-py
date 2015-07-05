from __future__ import unicode_literals
from six import PY2, PY3
from six.moves import filter, map, range

cal1 = """
BEGIN:VCALENDAR
METHOD:PUBLISH
VERSION:2.0
X-WR-CALNAME:plop
PRODID:-//Apple Inc.//Mac OS X 10.9//EN
X-APPLE-CALENDAR-COLOR:#882F00
X-WR-TIMEZONE:Europe/Brussels
CALSCALE:GREGORIAN
BEGIN:VTIMEZONE
TZID:Europe/Brussels
BEGIN:DAYLIGHT
TZOFFSETFROM:+0100
RRULE:FREQ=YEARLY;BYMONTH=3;BYDAY=-1SU
DTSTART:19810329T020000
TZNAME:UTC+2
TZOFFSETTO:+0200
END:DAYLIGHT
BEGIN:STANDARD
TZOFFSETFROM:+0200
RRULE:FREQ=YEARLY;BYMONTH=10;BYDAY=-1SU
DTSTART:19961027T030000
TZNAME:UTC+1
TZOFFSETTO:+0100
END:STANDARD
END:VTIMEZONE
BEGIN:VEVENT
CREATED:20131024T204716Z
UID:ABBF2903-092F-4202-98B6-F757437A5B28
DTEND;TZID=Europe/Brussels:20131029T113000
TRANSP:OPAQUE
SUMMARY:dfqsdfjqkshflqsjdfhqs fqsfhlqs dfkqsldfkqsdfqsfqsfqsfs
DTSTART;TZID=Europe/Brussels:20131029T103000
DTSTAMP:20131024T204741Z
SEQUENCE:3
DESCRIPTION:Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed
 vitae facilisis enim. Morbi blandit et lectus venenatis tristique. Donec
 sit amet egestas lacus. Donec ullamcorper, mi vitae congue dictum, quam
 dolor luctus augue, id cursus purus justo vel lorem. Ut feugiat enim ips
 um, quis porta nibh ultricies congue. Pellentesque nisl mi, molestie id
 sem vel, vehicula nullam.
END:VEVENT
END:VCALENDAR
"""

calendar_without_prodid = """
BEGIN:VCALENDAR
BEGIN:VEVENT
DTEND;TZID=Europe/Berlin:20120608T212500
SUMMARY:Name
DTSTART;TZID=Europe/Berlin:20120608T202500
LOCATION:MUC
SEQUENCE:0
BEGIN:VALARM
TRIGGER:-PT1H
DESCRIPTION:Event reminder
ACTION:DISPLAY
END:VALARM
END:VEVENT
END:VCALENDAR
"""


empty_calendar = """
BEGIN:VCALENDAR
END:VCALENDAR
"""

#calendar_without_end = """BEGIN:VCALENDAR"""  # not used

empty_calendar_with_version = """
BEGIN:VCALENDAR
VERSION:2.0
END:VCALENDAR
"""

cal6 = """
DESCRIPTION:a
 b
"""

empty_calendar_with_blank_line1 = """
BEGIN:VCALENDAR

END:VCALENDAR
"""

empty_calendar_with_blank_line2 = """
BEGIN:VCALENDAR
\t
END:VCALENDAR
"""

empty_calendar_with_blank_line3 = """

BEGIN:VCALENDAR
END:VCALENDAR
"""

cal10 = """
BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Apple Inc.//Mac OS X 10.9//EN
BEGIN:VEVENT
DTEND;TZID=Europe/Berlin:20120608T212500
DTSTAMP:20131024T204741Z
SUMMARY:Name
DTSTART;TZID=Europe/Berlin:20120608T202500
LOCATION:MUC
SEQUENCE:0
BEGIN:VALARM
TRIGGER:-PT1H
DESCRIPTION:Event reminder
ACTION:DISPLAY
END:VALARM
END:VEVENT
END:VCALENDAR
"""

calendar_with_parse_error = """
BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Apple Inc.//Mac OS X 10.9//EN
END:VCAL
"""

cal12 = """
BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Apple Inc.//Mac OS X 10.8//EN
BEGIN:VEVENT
SUMMARY:Name
DTSTART;TZID=Europe/Berlin:20120608T202500
DURATION:P1DT1H
LOCATION:MUC
SEQUENCE:0
BEGIN:VALARM
TRIGGER:-PT1H
DESCRIPTION:Event reminder
ACTION:DISPLAY
END:VALARM
END:VEVENT
END:VCALENDAR
"""

calendar_with_duration_and_end = """
BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Apple Inc.//Mac OS X 10.9//EN
BEGIN:VEVENT
SUMMARY:Name
DTSTART;TZID=Europe/Berlin:20120608T202500
DTEND;TZID=Europe/Berlin:20120608T212500
DURATION:P1DT1H
LOCATION:MUC
SEQUENCE:0
BEGIN:VALARM
TRIGGER:-PT1H
DESCRIPTION:Event reminder
ACTION:DISPLAY
END:VALARM
END:VEVENT
END:VCALENDAR
"""

cal14 = """
BEGIN:VCALENDAR
VERSION:2.0;42
PRODID:-//Apple Inc.//Mac OS X 10.9//EN
END:VCALENDAR
"""

cal15 = """
BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Apple Inc.//Mac OS X 10.9//EN

BEGIN:VEVENT
SUMMARY:Hello, \\n World\\; This is a backslash : \\\\ and another new \\N line
DTSTART;TZID=Europe/Berlin:20120608T202500
DTEND;TZID=Europe/Berlin:20120608T212500
LOCATION:MUC
END:VEVENT

BEGIN:VEVENT
SUMMARY:Some special \\; chars
DTSTART;TZID=Europe/Berlin:20130608T202501
DTEND;TZID=Europe/Berlin:20130608T212501
LOCATION:In\\, every text field
DESCRIPTION:Yes\\, all of them\\;
END:VEVENT

END:VCALENDAR
"""

# Event with URL
cal16 = """
BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Apple Inc.//Mac OS X 10.9//EN

BEGIN:VEVENT
SUMMARY:Hello, \\n World\\; This is a backslash : \\\\ and another new \\N line
DTSTART;TZID=Europe/Berlin:20120608T202500
DTEND;TZID=Europe/Berlin:20120608T212500
LOCATION:MUC
URL:http://example.com/pub/calendars/jsmith/mytime.ics
END:VEVENT

END:VCALENDAR
"""

unfolded_calendar_without_prodid = [
    'BEGIN:VCALENDAR',
    'BEGIN:VEVENT',
    'DTEND;TZID=Europe/Berlin:20120608T212500',
    'SUMMARY:Name',
    'DTSTART;TZID=Europe/Berlin:20120608T202500',
    'LOCATION:MUC',
    'SEQUENCE:0',
    'BEGIN:VALARM',
    'TRIGGER:-PT1H',
    'DESCRIPTION:Event reminder',
    'ACTION:DISPLAY',
    'END:VALARM',
    'END:VEVENT',
    'END:VCALENDAR',
]

unfolded_cal1 = [
    'BEGIN:VCALENDAR',
    'METHOD:PUBLISH',
    'VERSION:2.0',
    'X-WR-CALNAME:plop',
    'PRODID:-//Apple Inc.//Mac OS X 10.9//EN',
    'X-APPLE-CALENDAR-COLOR:#882F00',
    'X-WR-TIMEZONE:Europe/Brussels',
    'CALSCALE:GREGORIAN',
    'BEGIN:VTIMEZONE',
    'TZID:Europe/Brussels',
    'BEGIN:DAYLIGHT',
    'TZOFFSETFROM:+0100',
    'RRULE:FREQ=YEARLY;BYMONTH=3;BYDAY=-1SU',
    'DTSTART:19810329T020000',
    'TZNAME:UTC+2',
    'TZOFFSETTO:+0200',
    'END:DAYLIGHT',
    'BEGIN:STANDARD',
    'TZOFFSETFROM:+0200',
    'RRULE:FREQ=YEARLY;BYMONTH=10;BYDAY=-1SU',
    'DTSTART:19961027T030000',
    'TZNAME:UTC+1',
    'TZOFFSETTO:+0100',
    'END:STANDARD',
    'END:VTIMEZONE',
    'BEGIN:VEVENT',
    'CREATED:20131024T204716Z',
    'UID:ABBF2903-092F-4202-98B6-F757437A5B28',
    'DTEND;TZID=Europe/Brussels:20131029T113000',
    'TRANSP:OPAQUE',
    'SUMMARY:dfqsdfjqkshflqsjdfhqs fqsfhlqs dfkqsldfkqsdfqsfqsfqsfs',
    'DTSTART;TZID=Europe/Brussels:20131029T103000',
    'DTSTAMP:20131024T204741Z',
    'SEQUENCE:3',
    'DESCRIPTION:Lorem ipsum dolor sit amet, consectetur adipiscing elit. \
Sedvitae facilisis enim. Morbi blandit et lectus venenatis tristique. \
Donecsit amet egestas lacus. Donec ullamcorper, mi vitae congue dictum, \
quamdolor luctus augue, id cursus purus justo vel lorem. \
Ut feugiat enim ipsum, quis porta nibh ultricies congue. \
Pellentesque nisl mi, molestie idsem vel, vehicula nullam.',
    'END:VEVENT',
    'END:VCALENDAR',
]

unfolded_cal6 = ['DESCRIPTION:ab']
