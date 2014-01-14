#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals, absolute_import
from six import PY2, PY3
from six.moves import filter, map, range

import collections


class ParseError(Exception):
    pass


class ContentLine:

    def __eq__(self, other):
        ret = (self.name == other.name
               and self.params == other.params
               and self.value == other.value)
        return ret

    __ne__ = lambda self, other: not self.__eq__(other)

    def __init__(self, name, params={}, value=''):
        self.name = name
        self.params = params
        self.value = value

    def __str__(self):
        params_str = ''
        for pname in self.params:
            params_str += ';{}={}'.format(pname, ','.join(self.params[pname]))
        ret = "{}{}:{}".format(self.name, params_str, self.value)
        return ret.encode('utf-8') if PY2 else ret

    def __repr__(self):
        return "<ContentLine '{}' with {} parameter{}. Value='{}'>" \
            .format(
                self.name,
                len(self.params),
                "s" if len(self.params) > 1 else "",
                self.value,
            )

    def __getitem__(self, item):
        return self.params[item]

    def __setitem__(self, item, *values):
        self.params[item] = [val for val in values]

    @classmethod
    def parse(cls, line):
        if ':' not in line:
            raise ParseError("No ':' in line '{}'".format(line))

        # Separe key and value
        splitted = line.split(':')
        key, value = splitted[0], ':'.join(splitted[1:]).strip()

        # Separe name and params
        splitted = key.split(';')
        name, params_strings = splitted[0], splitted[1:]

        # Separe key and values for params
        params = {}
        for paramstr in params_strings:
            if '=' not in paramstr:
                raise ParseError("No '=' in line '{}'".format(line))
            splitted = paramstr.split('=')
            pname, pvals = splitted[0], '='.join(splitted[1:])
            params[pname] = pvals.split(',')
        return cls(name, params, value)

    def clone(self):
        # dict(self.params) -> Make a copy of the dict
        return self.__class__(self.name, dict(self.params), self.value)


class Container(list):

    def __init__(self, name, *items):
        super(Container, self).__init__(items)
        self.name = name

    def __str__(self):
        if PY2:
            l = lambda x: str(x).decode('utf-8')
        else:
            l = lambda x: str(x)
        content_str = '\n'.join(map(l, self))
        if content_str:
            content_str = '\n' + content_str

        ret = 'BEGIN:{}{}\nEND:{}'.format(self.name, content_str, self.name)
        if PY2:
            return ret.encode('utf-8')
        else:
            return ret

    def __repr__(self):
        return "<Container '{}' with {} element{}>" \
            .format(self.name, len(self), "s" if len(self) > 1 else "")

    @classmethod
    def parse(cls, name, tokenized_lines):
        items = []
        for line in tokenized_lines:
            if line.name == 'BEGIN':
                items.append(Container.parse(line.value, tokenized_lines))
            elif line.name == 'END':
                if line.value != name:
                    raise ParseError(
                        "Expected END:{}, got END:{}".format(name, line.value))
                break
            else:
                items.append(line)
        return cls(name, *items)

    def clone(self):
        c = self.__class__(self.name)
        for elem in self:
            c.append(elem.clone())
        return c


def unfold_lines(physical_lines):
    if not isinstance(physical_lines, collections.Iterable):
        raise ParseError('Parameter `physical_lines` must be an iterable')
    current_line = ''
    for line in physical_lines:
        if len(line.strip()) == 0:
            continue
        elif not current_line:
            current_line = line.strip('\r')
        elif line[0] == ' ':
            # TODO : remove more spaces if needed
            current_line += line[1:].strip('\r')
        else:
            yield(current_line)
            current_line = line.strip('\r')
    if current_line:
        yield(current_line)


def tokenize_line(unfolded_lines):
    for line in unfolded_lines:
        yield ContentLine.parse(line)


def parse(tokenized_lines, block_name=None):
    res = []
    for line in tokenized_lines:
        if line.name == 'BEGIN':
            res.append(Container.parse(line.value, tokenized_lines))
        else:
            res.append(line)
    return res


def lines_to_container(lines):
    return parse(tokenize_line(unfold_lines(lines)))


def string_to_container(txt):
    return lines_to_container(txt.split('\n'))

if __name__ == "__main__":
    from tests.fixture import cal1

    def print_tree(elem, lvl=0):
        if isinstance(elem, list) or isinstance(elem, Container):
            if isinstance(elem, Container):
                print("{}{}".format('   ' * lvl, elem.name))
            for sub_elem in elem:
                print_tree(sub_elem, lvl + 1)
        elif isinstance(elem, ContentLine):
            print("{}{}{}".format('   ' * lvl,
                  elem.name, elem.params, elem.value))
        else:
            print('Wuuut?')

    cal = string_to_container(cal1)
    print_tree(cal)
