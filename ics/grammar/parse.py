import collections
import re
from typing import Dict, List

import attr
import tatsu

from ics.grammar.contentline import contentlineParser

# grammar_path = Path(__file__).parent.joinpath('contentline.ebnf')
#
# with open(grammar_path) as fd:
#     GRAMMAR = tatsu.compile(fd.read())

GRAMMAR = contentlineParser()


@attr.s(auto_exc=True)
class ParseError(Exception):
    line: str = attr.ib(default="")
    nr: int = attr.ib(default=-1)


class ContentLine:
    """
    Represents one property line.

    For example:

    ``FOO;BAR=1:YOLO`` is represented by

    ``ContentLine('FOO', {'BAR': ['1']}, 'YOLO'))``

    Args:

        name:   The name of the property (uppercased for consistency and
                easier comparison)
        params: A map name:list of values
        value:  The value of the property
    """

    def __eq__(self, other):
        ret = (self.name == other.name and
               self.params == other.params and
               self.value == other.value)
        return ret

    def __ne__(self, other):
        return not self.__eq__(other)

    def __init__(self, name: str, params: Dict[str, List[str]] = {}, value: str = ''):
        self.name = name.upper()
        self.params = params
        self.value = value

    def __str__(self):
        params_str = ''
        for pname in self.params:
            params_str += ';{}={}'.format(pname, ','.join(self.params[pname]))
        return "{}{}:{}".format(self.name, params_str, self.value)

    def __repr__(self):
        return "<ContentLine '{}' with {} parameter{}. Value='{}'>".format(
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
    def parse(cls, line, nr=-1):
        """Parse a single iCalendar-formatted line into a ContentLine"""
        if "\n" in line or "\r" in line:
            raise ValueError("ContentLine can only contain escaped newlines")
        try:
            ast = GRAMMAR.parse(line)
        except tatsu.exceptions.FailedToken:
            raise ParseError(line, nr)

        name = ''.join(ast['name'])
        value = ''.join(ast['value'])
        params = {}
        for param_ast in ast.get('params', []):
            param_name = ''.join(param_ast["name"])
            param_values = [''.join(x["value"]) for x in param_ast["values"]]
            params[param_name] = param_values
        return cls(name, params, value)

    def clone(self):
        """Makes a copy of itself"""
        # dict(self.params) -> Make a copy of the dict
        return self.__class__(self.name, dict(self.params), self.value)


class Container(list):
    """Represents an iCalendar object.
    Contains a list of ContentLines or Containers.

    Args:

        name: the name of the object (VCALENDAR, VEVENT etc.)
        items: Containers or ContentLines
    """

    def __init__(self, name: str, *items: List):
        super(Container, self).__init__(items)
        self.name = name

    def __str__(self):
        name = self.name
        ret = ['BEGIN:' + name]
        for line in self:
            ret.append(str(line))
        ret.append('END:' + name)
        return "\r\n".join(ret)

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
        """Makes a copy of itself"""
        c = self.__class__(self.name)
        for elem in self:
            c.append(elem.clone())
        return c


def unfold_lines(physical_lines, with_linenr=False):
    if not isinstance(physical_lines, collections.abc.Iterable):
        raise ParseError('Parameter `physical_lines` must be an iterable')
    current_nr = -1
    current_line = ''
    for nr, line in enumerate(physical_lines):
        if len(line.strip()) == 0:
            continue
        elif not current_line:
            current_nr = nr
            current_line = line.strip('\r')
        elif line[0] in (' ', '\t'):
            current_line += line[1:].strip('\r')
        else:
            if with_linenr:
                yield current_nr, current_line
            else:
                yield current_line
            current_nr = nr
            current_line = line.strip('\r')
    if current_line:
        if with_linenr:
            yield current_nr, current_line
        else:
            yield current_line


def tokenize_line(unfolded_lines):
    for line in unfolded_lines:
        if isinstance(line, tuple):
            yield ContentLine.parse(line[1], line[0])
        else:
            yield ContentLine.parse(line)


def parse(tokenized_lines, block_name=None):
    res = []
    for line in tokenized_lines:
        if line.name == 'BEGIN':
            res.append(Container.parse(line.value, tokenized_lines))
        else:
            res.append(line)
    return res


def lines_to_container(lines, linewise=True):
    if linewise:
        return parse(tokenize_line(unfold_lines(lines, with_linenr=True)))  # linewise
    else:
        return string_to_container("\r\n".join(lines), linewise)  # full-string


def string_to_container(txt, linewise=True):
    if linewise:
        return lines_to_container(txt.split("\n"), linewise)  # linewise
    else:
        return parse(string_to_content_lines(txt))  # full-string


def string_to_content_lines(txt):
    txt = re.sub("\r?\n[ \t]", "", txt)
    ast = GRAMMAR.parse(txt, rule_name='full')
    for line in ast:
        line = line[0]
        name = ''.join(line['name'])
        value = ''.join(line['value'])
        params = {}
        for param_ast in line.get('params', []):
            param_name = ''.join(param_ast["name"])
            param_values = [''.join(x["value"]) for x in param_ast["values"]]
            params[param_name] = param_values
        yield ContentLine(name, params, value)


def calendar_string_to_containers(string):
    if not isinstance(string, str):
        raise TypeError("Expecting a string")
    return string_to_container(string)
