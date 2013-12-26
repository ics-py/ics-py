#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals, absolute_import

from six import PY2, PY3, StringIO, string_types, text_type, integer_types
from six.moves import filter, map, range

import arrow
from arrow.arrow import Arrow
tzutc = arrow.utcnow().tzinfo

import re

from . import parse


def remove_x(container):
    for i in reversed(range(len(container))):
        item = container[i]
        if item.name.startswith('X-'):
            del container[i]


def iso_to_arrow(time_container, available_tz={}):
    if time_container is None:
        return None

    # TODO : raise if not iso date
    tz_list = time_container.params.get('TZID')
    # TODO : raise if len(tz_list) > 1 or if tz is not a valid tz
    # TODO : see if timezone is registered as a VTIMEZONE
    if tz_list and len(tz_list) > 0:
        tz = tz_list[0]
    else:
        tz = None
    if (not 'T' in time_container.value) and 'DATE' in time_container.params.get('VALUE', []):
        val = time_container.value + 'T0000'
    else:
        val = time_container.value

    if tz and not (val[-1].upper() == 'Z'):
        naive = arrow.get(val).naive
        selected_tz = available_tz.get(tz, 'UTC')
        return arrow.get(naive, selected_tz)
    else:
        return arrow.get(val)

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


def get_lines(container, name):
    lines = []
    for i in reversed(range(len(container))):
        item = container[i]
        if item.name == name:
            lines.append(item)
            del container[i]
    return lines


def parse_duration(duration):
    return None


def get_arrow(value):
    if value is None:
        return None
    elif isinstance(value, Arrow):
        return value
    elif isinstance(value, tuple):
        return arrow.get(*value)
    elif isinstance(value, dict):
        return arrow.get(**value)
    else:
        return arrow.get(value)


def arrow_to_iso(instant):
    # set to utc, make iso, remove timzone
    instant = arrow.get(instant.astimezone(tzutc)).format('YYYYMMDDTHHmmss')
    return instant + 'Z'
