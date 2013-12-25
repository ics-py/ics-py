#!/usr/bin/env python
# -*- coding: utf-8 -*-

from itertools import islice
import arrow
import parse
import re


def window(iterable, size):
    if not size > 0:
        raise ValueError("Window size must be greater than 0")

    i = 0
    while True:
        l = list(islice(iterable, i, i + size))
        if len(l) < size and i > 0 or len(l) == 0:
            raise StopIteration()

        yield l
        i += 1


def iso_to_arrow(time_container):
    # TODO : raise if not iso date
    tz_list = time_container.params.get('TZID')
    # TODO : raise if len(tz_list) > 1 or if tz is not a valid tz
    if tz_list and len(tz_list) > 0:
        tz = tz_list[0]
    else:
        tz = None

    if tz and not (time_container.value[-1].upper() == 'Z'):
        naive = arrow.get(time_container.value).naive
        return arrow.get(naive, tz)
    else:
        return arrow.get(time_container.value)

    # TODO : support floating (ie not bound to any time zone) times (cf http://www.kanzaki.com/docs/ical/dateTime.html)


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


def get_line(container, name):
    #TODO replace len(list())
    lines = list(filter(lambda x: x.name == name, container))
    if len(lines) != 1:
        raise parse.ParseError('A {} must have one and only one {}'.format(container.name, name))
    return list(lines)[0]


def get_optional_line(container, name):
    lines = list(filter(lambda x: x.name == name, container))
    if len(lines) > 1:
        raise parse.ParseError('A {} must have at most one {}'.format(container.name, name))
    elif len(lines) == 0:
        return None
    else:
        return lines[0]


def parse_duration(duration):
    return None
