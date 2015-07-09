#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals, absolute_import

from datetime import date, datetime, timedelta, tzinfo
import six
from uuid import uuid4
import re

from . import parse


ZERO_OFFSET = timedelta(0)


class TZUTC(tzinfo):
    def utcoffset(self, dt):
        return ZERO_OFFSET

    def dst(self, dt):
        return ZERO_OFFSET

    def tzname(self, dt):
        return "UTC"

tzutc = TZUTC()


def utcnow():
    return datetime.now(tzutc)


def remove_x(container):
    for i in reversed(six.moves.range(len(container))):
        item = container[i]
        if item.name.startswith('X-'):
            del container[i]


def iso_precision(string):
    has_time = 'T' in string

    if has_time:
        date_string, time_string = string.split('T', 1)
        time_parts = re.split('[+-]', time_string, 1)
        has_seconds = time_parts[0].count(':') > 1
        has_seconds = not has_seconds and len(time_parts[0]) == 6

        if has_seconds:
            return 'second'
        else:
            return 'minute'
    else:
        return 'day'


def parse_duration(line):
    """
    Return a timedelta object from a string in the DURATION property format
    """
    DAYS, SECS = {'D': 1, 'W': 7}, {'S': 1, 'M': 60, 'H': 3600}
    sign, i = 1, 0
    if line[i] in '-+':
        if line[i] == '-':
            sign = -1
        i += 1
    if line[i] != 'P':
        raise parse.ParseError()
    i += 1
    days, secs = 0, 0
    while i < len(line):
        if line[i] == 'T':
            i += 1
            if i == len(line):
                break
        j = i
        while line[j].isdigit():
            j += 1
        if i == j:
            raise parse.ParseError()
        val = int(line[i:j])
        if line[j] in DAYS:
            days += val * DAYS[line[j]]
            DAYS.pop(line[j])
        elif line[j] in SECS:
            secs += val * SECS[line[j]]
            SECS.pop(line[j])
        else:
            raise parse.ParseError()
        i = j + 1
    return timedelta(sign * days, sign * secs)


def timedelta_to_duration(dt):
    """
    Return a string according to the DURATION property format
    from a timedelta object
    """
    days, secs = dt.days, dt.seconds
    res = 'P'
    if days // 7:
        res += str(days // 7) + 'W'
        days %= 7
    if days:
        res += str(days) + 'D'
    if secs:
        res += 'T'
        if secs // 3600:
            res += str(secs // 3600) + 'H'
            secs %= 3600
        if secs // 60:
            res += str(secs // 60) + 'M'
            secs %= 60
        if secs:
            res += str(secs) + 'S'
    return res


def datetime_to_iso(instant):
    if instant.tzinfo:
        # set to utc, make iso, remove timezone
        instant = instant.astimezone(tzutc)
        return instant.strftime('%Y%m%dT%H%M%SZ')
    # naive
    return instant.strftime('%Y%m%dT%H%M%S')


def get_date_or_datetime(value, tz=None):
    """ Tries to read a date/datetime from whatever it gets.

    Usually it will return a datetime,
    except when it is passed a date
    or a string without hours, minutes and seconds
    If tz (timezone) is None, it will return a naive datetime,
    except when it gets an int or float,
    which are interpreted as timestamp in UTC.
    """
    if value is None:
        return None
    elif isinstance(value, date):  # True for date and datetime
        return value
    elif isinstance(value, tuple):
        return datetime(*value, tzinfo=tz)
    elif isinstance(value, dict):
        if tz is not None:
            value['tzinfo'] = tz
        return datetime(**value)
    elif isinstance(value, six.string_types):
        return parse_date_or_datetime(value, tz=tz)
    elif isinstance(value, (six.integer_types, float)):
        return datetime.fromtimestamp(value, tz=tz or tzutc)


DATETIME_PATTERNS = (
    (r'(?P<year>\d{4})/(?P<month>\d{2})/(?P<day>\d{2}).(?P<hour>\d{2}):(?P<minute>\d{2}):(?P<second>\d{2})',
     datetime),  # YYYY/MM/DD?HH:mm:ss
    (r'(?P<year>\d{4})/(?P<month>\d{2})/(?P<day>\d{2}).(?P<hour>\d{2}):(?P<minute>\d{2})',
     datetime),  # YYYY/MM/DD?HH:mm
    (r'(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2}).(?P<hour>\d{2}):(?P<minute>\d{2}):(?P<second>\d{2})',
     datetime),  # YYYY-MM-DD?HH:mm:ss
    (r'(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2}).(?P<hour>\d{2}):(?P<minute>\d{2})',
     datetime),  # YYYY-MM-DD?HH:mm
    (r'(?P<year>\d{4})(?P<month>\d{2})(?P<day>\d{2}).(?P<hour>\d{2})(?P<minute>\d{2})(?P<second>\d{2})',
     datetime),  # YYYYMMDD?HHmmss
    (r'(?P<year>\d{4})(?P<month>\d{2})(?P<day>\d{2}).(?P<hour>\d{2})(?P<minute>\d{2})',
     datetime),  # YYYYMMDD?HHmm
    (r'(?P<year>\d{4})/(?P<month>\d{2})/(?P<day>\d{2})', date),  # YYYY/MM/DD
    (r'(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})', date),  # YYYY-MM-DD
    (r'(?P<year>\d{4})(?P<month>\d{2})(?P<day>\d{2})', date),  # YYYYMMDD
)


def parse_date_or_datetime(value, tz=None):
    if not isinstance(value, six.string_types):
        raise ValueError('String type expected, got {}'.format(type(value).__name__))
    for pattern, _type in DATETIME_PATTERNS:
        match = re.match(pattern, value)
        if match:
            kwargs = dict((key, int(val))
                          for key, val in match.groupdict().items())
            if _type == datetime:
                kwargs['tzinfo'] = tz
            return _type(**kwargs)

DATE_PATTERNS = (
    (re.compile(r'^\d{8}$'), '%Y%m%d'),
    (re.compile(r'^\d{4}/\d{2}/\d{2}$'), '%Y/%m/%d'),
    (re.compile(r'^\d{4}-\d{2}-\d{2}$'), '%Y-%m-%d'),
)


def parse_date(value):
    """ If `value` is a string representing a date, return the date,
    else return `value` unchanged
    """
    if isinstance(value, six.string_types):
        for pattern, format in DATE_PATTERNS:
            if pattern.match(value):
                return datetime.strptime(value, format).date()
    return value


def parse_cal_date(value):
    """ Parse a date value as specified in RFC5545
    """
    return datetime.strptime(value, '%Y%m%d').date()


DATETIME_PATTERN = re.compile(
    r"(\d{4})(\d{2})(\d{2})T(\d{2})(\d{2})(\d{2})")


def parse_cal_datetime(contentline, timezones={}):
    """ Parse a datetime value as specified in RFC5545

    FORM #1: DATE WITH LOCAL TIME:
        19980118T230000
    FORM #2: DATE WITH UTC TIME
        19980119T070000Z
    FORM #3: DATE WITH LOCAL TIME AND TIME ZONE REFERENCE
        TZID=America/New_York:19980119T020000

    If there should be more than one TZID (which should not occur)
    the first one is used.
    """
    if contentline is None:
        return None

    tz_list = contentline.params.get('TZID')
    val = contentline.value

    if val[-1].upper() == 'Z':  # FORM #2
        tzinfo = tzutc
        val = val[:-1]
    elif tz_list:  # FORM #3
        tzinfo = timezones.get(tz_list[0])
    else:  # FORM #1
        tzinfo = None
    args = [int(i) for i in DATETIME_PATTERN.match(val).groups()]
    if tzinfo:
        return datetime(*args, tzinfo=tzinfo)
    return datetime(*args)

    # TODO : raise if not iso date
    # TODO : see if timezone is registered as a VTIMEZONE


def uid_gen():
    uid = str(uuid4())
    return "{}@{}.org".format(uid, uid[:4])


def is_date(value):
    return isinstance(value, date) and not isinstance(value, datetime)
