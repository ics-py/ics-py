#!/usr/bin/env python
# -*- coding: utf-8 -*-

import arrow
import re
import parse


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

    if tz and not (time_container.value[-1].upper() == 'Z'):
        naive = arrow.get(time_container.value).naive
        selected_tz = available_tz.get(tz, 'UTC')
        return arrow.get(naive, selected_tz)
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


class Node(object):
    _TYPE = "ABSTRACT"

    @classmethod
    def _from_container(klass, container, *args, **kwargs):
        k = klass()
        k._classmethod_args = args
        k._classmethod_kwargs = kwargs

        if k._TYPE == "ABSTRACT":
            raise NotImplementedError('Abstract clss')
        k._populate(container)
        return k

    def _populate(self, container):
        if container.name != self._TYPE:
            raise parse.ParseError("container isn't an {}".format(), self.TYPE)

        for extractor, line_type, required, multiple in self._EXTRACTORS:
            lines = get_lines(container, line_type)
            if not lines and required:
                raise parse.ParseError('A {} must have at least one {}'.format(container.name, line_type))

            if not multiple and len(lines) > 1:
                raise parse.ParseError('A {} must have at most one {}'.format(container.name, line_type))

            if multiple:
                extractor(self, lines)
            else:
                if len(lines) == 1:
                    extractor(self, lines[0])
                else:
                    extractor(self, None)

        self._unused = container

    @classmethod
    def _extracts(klass, line_type, required=False, multiple=False):
        def decorator(fn):
            klass._EXTRACTORS.append((fn, line_type, required, multiple))
            return fn
        return decorator
