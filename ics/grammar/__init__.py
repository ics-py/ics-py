import functools
import re
import warnings
from collections import UserString
from typing import Generator, List, MutableSequence, Union

import attr
import importlib_resources  # type: ignore
import tatsu  # type: ignore
from tatsu.exceptions import FailedToken  # type: ignore

from ics.types import ContainerItem, ExtraParams, RuntimeAttrValidation, copy_extra_params
from ics.utils import limit_str_length, next_after_str_escape, validate_truthy

__all__ = ["ParseError", "QuotedParamValue", "ContentLine", "Container", "string_to_container"]

GRAMMAR = tatsu.compile(importlib_resources.read_text(__name__, "contentline.ebnf"))


class ParseError(Exception):
    pass


class QuotedParamValue(UserString):
    pass


@attr.s
class ContentLine(RuntimeAttrValidation):
    """
    Represents one property line.

    For example:

    ``FOO;BAR=1:YOLO`` is represented by

    ``ContentLine('FOO', {'BAR': ['1']}, 'YOLO'))``
    """

    name: str = attr.ib(converter=str.upper)  # type: ignore
    params: ExtraParams = attr.ib(factory=lambda: ExtraParams(dict()))
    value: str = attr.ib(default="")

    # TODO store value type for jCal and line number for error messages

    def serialize(self):
        return "".join(self.serialize_iter())

    def serialize_iter(self, newline=False):
        yield self.name
        for pname in self.params:
            yield ";"
            yield pname
            yield "="
            for nr, pval in enumerate(self.params[pname]):
                if nr > 0:
                    yield ","
                if isinstance(pval, QuotedParamValue) or re.search("[:;,]", pval):
                    # Property parameter values that contain the COLON, SEMICOLON, or COMMA character separators
                    # MUST be specified as quoted-string text values.
                    # TODO The DQUOTE character is used as a delimiter for parameter values that contain
                    #  restricted characters or URI text.
                    # TODO Property parameter values that are not in quoted-strings are case-insensitive.
                    yield '"%s"' % escape_param(pval)
                else:
                    yield escape_param(pval)
        yield ":"
        yield self.value
        if newline:
            yield "\r\n"

    def __getitem__(self, item):
        return self.params[item]

    def __setitem__(self, item, values):
        self.params[item] = list(values)

    @classmethod
    def parse(cls, line):
        """Parse a single iCalendar-formatted line into a ContentLine"""
        if "\n" in line or "\r" in line:
            raise ValueError("ContentLine can only contain escaped newlines")
        try:
            ast = GRAMMAR.parse(line)
        except FailedToken:
            raise ParseError()
        else:
            return cls.interpret_ast(ast)

    @classmethod
    def interpret_ast(cls, ast):
        name = ast['name']
        value = ast['value']
        params = ExtraParams(dict())
        for param_ast in ast.get('params', []):
            param_name = param_ast["name"]
            params[param_name] = []
            for param_value_ast in param_ast["values_"]:
                val = unescape_param(param_value_ast["value"])
                if param_value_ast["quoted"] == "true":
                    val = QuotedParamValue(val)
                params[param_name].append(val)
        return cls(name, params, value)

    def clone(self):
        """Makes a copy of itself"""
        return attr.evolve(self, params=copy_extra_params(self.params))

    def __str__(self):
        return "%s%s='%s'" % (self.name, self.params or "", limit_str_length(self.value))


def _wrap_list_func(list_func):
    @functools.wraps(list_func)
    def wrapper(self, *args, **kwargs):
        return list_func(self.data, *args, **kwargs)

    return wrapper


@attr.s(repr=False)
class Container(MutableSequence[ContainerItem]):
    """Represents an iCalendar object.
    Contains a list of ContentLines or Containers.

    Args:

        name: the name of the object (VCALENDAR, VEVENT etc.)
        items: Containers or ContentLines
    """

    name: str = attr.ib(converter=str.upper, validator=validate_truthy)  # type:ignore
    data: List[ContainerItem] = attr.ib(converter=list, default=[],
                                        validator=lambda inst, attr, value: inst.check_items(*value))

    def __str__(self):
        return "%s[%s]" % (self.name, ", ".join(str(cl) for cl in self.data))

    def __repr__(self):
        return "%s(%r, %s)" % (type(self).__name__, self.name, repr(self.data))

    def serialize(self):
        return "".join(self.serialize_iter())

    def serialize_iter(self, newline=False):
        yield "BEGIN:"
        yield self.name
        yield "\r\n"
        for line in self:
            yield from line.serialize_iter(newline=True)
        yield "END:"
        yield self.name
        if newline:
            yield "\r\n"

    @classmethod
    def parse(cls, name, tokenized_lines):
        items = []
        if not name.isupper():
            warnings.warn("Container 'BEGIN:%s' is not all-uppercase" % name)
        for line in tokenized_lines:
            if line.name == 'BEGIN':
                items.append(cls.parse(line.value, tokenized_lines))
            elif line.name == 'END':
                if line.value.upper() != name.upper():
                    raise ParseError(
                        "Expected END:{}, got END:{}".format(name, line.value))
                if not name.isupper():
                    warnings.warn("Container 'END:%s' is not all-uppercase" % name)
                break
            else:
                items.append(line)
        else:  # if break was not called
            raise ParseError("Missing END:{}".format(name))
        return cls(name, items)

    def clone(self, items=None, deep=False):
        """Makes a copy of itself"""
        if items is None:
            items = self.data
        if deep:
            items = (item.clone() for item in items)
        return attr.evolve(self, data=items)

    @staticmethod
    def check_items(*items):
        from ics.utils import check_is_instance
        if len(items) == 1:
            check_is_instance("item", items[0], (ContentLine, Container))
        else:
            for nr, item in enumerate(items):
                check_is_instance("item %s" % nr, item, (ContentLine, Container))

    def __setitem__(self, index, value):  # index might be slice and value might be iterable
        self.data.__setitem__(index, value)
        attr.validate(self)

    def insert(self, index, value):
        self.check_items(value)
        self.data.insert(index, value)

    def append(self, value):
        self.check_items(value)
        self.data.append(value)

    def extend(self, values):
        self.data.extend(values)
        attr.validate(self)

    def __getitem__(self, i):
        if isinstance(i, slice):
            return attr.evolve(self, data=self.data[i])
        else:
            return self.data[i]

    __contains__ = _wrap_list_func(list.__contains__)
    __delitem__ = _wrap_list_func(list.__delitem__)
    __iter__ = _wrap_list_func(list.__iter__)
    __len__ = _wrap_list_func(list.__len__)
    __reversed__ = _wrap_list_func(list.__reversed__)
    clear = _wrap_list_func(list.clear)
    count = _wrap_list_func(list.count)
    index = _wrap_list_func(list.index)
    pop = _wrap_list_func(list.pop)
    remove = _wrap_list_func(list.remove)
    reverse = _wrap_list_func(list.reverse)


def escape_param(string: Union[str, QuotedParamValue]) -> str:
    return str(string).translate(
        {ord("\""): "^'",
         ord("^"): "^^",
         ord("\n"): "^n",
         ord("\r"): ""})


def unescape_param(string: str) -> str:
    return "".join(unescape_param_iter(string))


def unescape_param_iter(string: str) -> Generator[str, None, None]:
    it = iter(string)
    for c1 in it:
        if c1 == "^":
            c2 = next_after_str_escape(it, full_str=string)
            if c2 == "n":
                yield "\n"
            elif c2 == "^":
                yield "^"
            elif c2 == "'":
                yield "\""
            else:
                yield c1
                yield c2
        else:
            yield c1


def unfold_lines(physical_lines):
    current_line = ''
    for line in physical_lines:
        line = line.rstrip('\r')
        if not current_line:
            current_line = line
        elif line[0] in (' ', '\t'):
            current_line += line[1:]
        else:
            yield current_line
            current_line = line
    if current_line:
        yield current_line


def tokenize_line(unfolded_lines):
    for line in unfolded_lines:
        yield ContentLine.parse(line)


def parse(tokenized_lines):
    # tokenized_lines must be an iterator, so that Container.parse can consume/steal lines
    tokenized_lines = iter(tokenized_lines)
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
    return lines_to_container(txt.splitlines())
