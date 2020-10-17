import platform
from collections import UserString

import attr
import functools
import re
from typing import MutableSequence, Tuple, List, Union

from ics.types import ContainerItem, ExtraParams, RuntimeAttrValidation, copy_extra_params
from ics.utils import limit_str_length, validate_truthy

allow_frozen_exceptions = True
if platform.python_implementation() == "PyPy":
    # we can't raise frozen exceptions from an exception handler on pypy, see attrs#703:
    # https://github.com/python-attrs/attrs/issues/703
    allow_frozen_exceptions = False


@attr.s(slots=True, frozen=allow_frozen_exceptions, auto_exc=True)  # type: ignore[misc]
class ParseError(Exception):
    msg: str = attr.ib()
    line_nr: int = attr.ib(default=-1)
    col: Union[int, Tuple[int, int]] = attr.ib(default=-1)
    line: str = attr.ib(default=None)
    state: str = attr.ib(default=None)

    def __str__(self):
        strs = ["Line"]
        if self.line_nr != -1:
            strs.append(" %s" % self.line_nr)
            if self.col != -1:
                if isinstance(self.col, int):
                    strs.append(":%s" % (self.col,))
                else:
                    strs.append(":%s-%s" % self.col)
        strs.append(" ")
        strs.append(self.msg)
        if self.line:
            strs.append(": ")
            strs.append(self.line)
        if self.state:
            strs.append(" (")
            strs.append(self.state)
            strs.append(")")
        return "".join(strs)


class QuotedParamValue(UserString):
    pass

    @classmethod
    def maybe_unquote(cls, txt: str) -> Union["QuotedParamValue", str]:
        if not txt:
            return txt
        if txt[0] == Patterns.DQUOTE:
            assert len(txt) >= 2
            assert txt[-1] == Patterns.DQUOTE
            return cls(txt[1:-1])
        else:
            return txt


def escape_param(string: Union[str, QuotedParamValue]) -> str:
    return str(string).translate(
        {ord("\""): "^'",
         ord("^"): "^^",
         ord("\n"): "^n",
         ord("\r"): ""})


def unescape_param(string: str) -> str:
    def repl(match):
        g = match.group(1)
        if g == "n":
            return "\n"
        elif g == "^":
            return "^"
        elif g == "'":
            return "\""
        elif len(g) == 0:
            raise ParseError("parameter value '%s' may not end with an escape sequence" % string)
        else:
            raise ParseError("invalid escape sequence ^%s in parameter value '%s'" % (g, string))

    return re.sub(r"\^(.?)", repl, string)


class Patterns:
    CONTROL = "\x00-\x08\x0A-\x1F\x7F"  # All the controls except HTAB
    DQUOTE = "\""
    LINEBREAK = "\r?\n|\r"
    LINEFOLD = "(" + LINEBREAK + ")[ \t]"
    QSAFE_CHARS = "[^" + CONTROL + DQUOTE + "]*"
    SAFE_CHARS = "[^" + CONTROL + DQUOTE + ",:;]*"
    VALUE_CHARS = "[^" + CONTROL + "]*"
    IDENTIFIER = "[a-zA-Z0-9-]+"

    PVAL = "(?P<pval>" + DQUOTE + QSAFE_CHARS + DQUOTE + "|" + SAFE_CHARS + ")"
    PVALS = PVAL + "(," + PVAL + ")*"
    PARAM = "(?P<pname>" + IDENTIFIER + ")=(?P<pvals>" + PVALS + ")"
    LINE = "(?P<name>" + IDENTIFIER + ")(;" + PARAM + ")*:(?P<value>" + VALUE_CHARS + ")"


@attr.s(slots=True)
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

    # TODO store value type for jCal
    line_nr: int = attr.ib(default=-1, eq=False)

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


@attr.s(slots=True, repr=False)
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
        if isinstance(i, str):
            return tuple(cl for cl in self.data if cl.name == i)
        elif isinstance(i, slice):
            return attr.evolve(self, data=self.data[i])
        else:
            return self.data[i]

    def __delitem__(self, i):
        if isinstance(i, str):
            self.data = [cl for cl in self.data if cl.name != i]
        else:
            del self.data[i]

    def __setitem__(self, index, value):  # index might be slice and value might be iterable
        self.data.__setitem__(index, value)
        attr.validate(self)

    __contains__ = _wrap_list_func(list.__contains__)
    __iter__ = _wrap_list_func(list.__iter__)
    __len__ = _wrap_list_func(list.__len__)
    __reversed__ = _wrap_list_func(list.__reversed__)
    clear = _wrap_list_func(list.clear)
    count = _wrap_list_func(list.count)
    index = _wrap_list_func(list.index)
    pop = _wrap_list_func(list.pop)
    remove = _wrap_list_func(list.remove)
    reverse = _wrap_list_func(list.reverse)
