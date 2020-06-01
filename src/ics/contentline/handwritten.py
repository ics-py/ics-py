import re
from typing import Tuple, Iterator, Union

from ics.contentline.common import *


class HandwrittenParser(Parser):
    def lines_to_contentlines(self, lines: Iterator[Union[Tuple[int, str], str]]) -> Iterator[ContentLine]:
        for line in lines:
            if not isinstance(line, str):
                nr, line = line
                yield ContentLineParser(line, nr).parse(self.regex_impl)
            else:
                yield ContentLineParser(line).parse(self.regex_impl)


class ContentLineParser(object):
    __slots__ = [
        "line", "line_nr", "delims", "delim", "cl", "param_value_start", "param_values",
    ]

    def __init__(self, line, line_nr=-1):
        self.line = line
        self.line_nr = line_nr

    def error(self, msg: str, col: Union[int, Tuple[int, int]] = -1) -> ParseError:
        return ParseError(msg, self.line_nr, col, self.line, str(self))

    def __str__(self):
        return str({s: getattr(self, s) for s in self.__slots__ if hasattr(self, s)})

    def next_delim(self):
        try:
            self.delim = next(self.delims)
        except StopIteration:
            raise self.error("does not contain name-value separator ':'")

    def parse(self, regex_impl=re):
        self.delims = iter(regex_impl.finditer("[:;]", self.line))
        self.next_delim()
        name = self.line[:self.delim.start()]
        self.cl = ContentLine(name, line_nr=self.line_nr)

        while True:
            # everything before delim.start() is already processed and we should start reading at delim.end()
            if self.delim.group() == ":":
                self.cl.value = self.line[self.delim.end():]
                return self.cl

            assert self.delim.group() == ";"
            self.parse_param()

    def parse_param(self):
        try:
            param_delim = self.line.index("=", self.delim.end())
        except ValueError:
            raise self.error("contains param without value", self.delim.end())

        # read comma-separated and possibly quoted param values
        param_name = self.line[self.delim.end():param_delim]
        self.cl.params[param_name] = self.param_values = []
        self.param_value_start = param_delim + 1
        self.next_delim()  # proceed to delim after param value list
        has_further_param_value = True
        while has_further_param_value:
            if self.delim.start() <= self.param_value_start:
                raise self.error("contains param with an empty value", (self.delim.start(), self.param_value_start))

            if self.line[self.param_value_start] == Patterns.DQUOTE:
                has_further_param_value = self.parse_quoted_param_val()
            else:
                has_further_param_value = self.parse_raw_param_val()

    def parse_quoted_param_val(self):
        self.param_value_start += 1  # skip the quote
        try:
            param_quote_stop = self.line.index(Patterns.DQUOTE, self.param_value_start)
        except ValueError:
            raise self.error("contains param missing a closing quote", self.param_value_start)
        self.param_values.append(QuotedParamValue(self.line[self.param_value_start:param_quote_stop]))

        # reposition the delims sequence, skipping any delimiter until right after the closing quote
        self.param_value_start = param_quote_stop + 1
        while self.delim.start() < self.param_value_start:
            self.next_delim()

        # continue with whatever comes after the closing quote
        if self.delim.start() == self.param_value_start:
            return False  # this was the last value for this param
        if self.line[self.param_value_start] == ",":
            self.param_value_start += 1  # skip the comma and continue with the next param value
            return True  # there's a next value following for this param
        else:
            raise self.error("contains param with content trailing after closing quote",
                             (self.param_value_start, self.delim.start()))

    def parse_raw_param_val(self):
        param_comma = self.line.find(",", self.param_value_start, self.delim.start())
        if param_comma < 0:
            self.param_values.append(self.line[self.param_value_start:self.delim.start()])
            return False  # this was the last value for this param
        else:
            self.param_values.append(self.line[self.param_value_start:param_comma])
            self.param_value_start = param_comma + 1
            return True  # there's a next value following for this param

    def check(self, regex_impl=re):
        assert regex_impl.match(Patterns.IDENTIFIER, self.cl.name)
        for key, vals in self.cl.params.items():
            assert regex_impl.match(Patterns.IDENTIFIER, key)
            for val in vals:
                if isinstance(QuotedParamValue, val):
                    assert regex_impl.match(Patterns.QSAFE_CHARS, val.data)
                else:
                    assert regex_impl.match(Patterns.SAFE_CHARS, val.data)
        assert regex_impl.match(Patterns.VALUE_CHARS, self.cl.name)
