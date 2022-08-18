import re
import warnings
from typing import ClassVar, Iterable, Iterator, List, Match, Tuple, Union

import attr

from ics.contentline.container import (
    Container,
    ContentLine,
    ParseError,
    Patterns,
    QuotedParamValue,
    unescape_param,
)
from ics.types import ContainerItem


class ParserClass:
    def string_to_containers(self, txt: str) -> Iterator[ContainerItem]:
        return self.contentlines_to_containers(
            self.lines_to_contentlines(self.unfold_lines(self.string_to_lines(txt)))
        )

    def lines_to_containers(self, lines: Iterable[str]) -> Iterator[ContainerItem]:
        return self.contentlines_to_containers(
            self.lines_to_contentlines(self.unfold_lines(lines))
        )

    def string_to_lines(self, txt: str) -> Iterable[str]:
        # unicode newlines are interpreted as such by str.splitlines(), but not by the ics standard
        # "A:abc\x85def".splitlines() => ['A:abc', 'def'] which is wrong
        return re.split(Patterns.LINEBREAK, txt)

    def unfold_lines(self, lines: Iterable[str]) -> Iterator[Tuple[int, str]]:
        current_nr = -1
        current_lines: List[str] = []
        for line_nr, line in enumerate(lines):
            line = line.rstrip("\r\n")
            if len(line) == 0:
                continue  # ignore empty lines
            nl = re.search("[\r\n]", line)
            if nl:
                raise ParseError(
                    "Line %s:%s is not properly split and contains a newline %s: %r"
                    % (line_nr, nl.start(), nl, line)
                )
            if not current_lines:
                if line[0] in (" ", "\t"):
                    raise ParseError(
                        "Line %s is a continuation (starts with space) without a preceding line: %r"
                        % (line_nr, line)
                    )
                else:
                    current_nr = line_nr
                    current_lines = [line]
            else:
                if line[0] in (" ", "\t"):
                    current_lines.append(line[1:])
                else:
                    yield current_nr, "".join(current_lines)
                    current_nr = line_nr
                    current_lines = [line]
        if current_lines:
            yield current_nr, "".join(current_lines)

    def contentlines_to_containers(
        self, tokenized_lines: Iterable[ContentLine]
    ) -> Iterator[ContainerItem]:
        # tokenized_lines must be an iterator, so that Container.parse can consume/steal lines
        if not isinstance(tokenized_lines, Iterator):
            tokenized_lines = iter(tokenized_lines)
        for line in tokenized_lines:
            if line.name == "BEGIN":
                yield self.contentlines_to_container(line.value, tokenized_lines)
            else:
                yield line

    def contentlines_to_container(
        self, name: str, tokenized_lines: Iterable[ContentLine]
    ) -> Container:
        items: List[ContainerItem] = []
        if not name.isupper():
            warnings.warn(f"Container 'BEGIN:{name}' is not all-uppercase")
        for line in tokenized_lines:
            if line.name == "BEGIN":
                items.append(
                    self.contentlines_to_container(line.value, tokenized_lines)
                )
            elif line.name == "END":
                if line.value.upper() != name.upper():
                    raise ParseError(f"Expected END:{name}, got END:{line.value}")
                if not name.isupper():
                    warnings.warn(f"Container 'END:{name}' is not all-uppercase")
                break
            else:
                items.append(line)
        else:  # if break was not called
            raise ParseError(f"Missing END:{name}")
        return Container(name, items)  # type: ignore[arg-type]

    def lines_to_contentlines(
        self, lines: Iterable[Union[Tuple[int, str], str]]
    ) -> Iterator[ContentLine]:
        clp = ContentLineParser()
        for line in lines:
            if not isinstance(line, str):
                nr, line = line
                yield clp.parse(line, nr)
            else:
                yield clp.parse(line)


@attr.s(slots=True)
class ContentLineParser:
    line: str = attr.ib(default=None)
    line_nr: int = attr.ib(default=None)
    delims: Iterator[Match] = attr.ib(default=None)
    delim: Match = attr.ib(default=None)
    cl: ContentLine = attr.ib(default=None)
    param_value_start: int = attr.ib(default=None)
    param_values: List[Union[str, QuotedParamValue]] = attr.ib(default=None)

    always_check: ClassVar[bool] = False

    def error(self, msg: str, col: Union[int, Tuple[int, int]] = -1) -> ParseError:
        return ParseError(msg, self.line_nr, col, self.line, str(self))

    def next_delim(self):
        try:
            self.delim = next(self.delims)
        except StopIteration:
            raise self.error("does not contain name-value separator ':'")

    def parse(self, line, line_nr=-1):
        self.line = line
        self.line_nr = line_nr
        self.delims = iter(re.finditer("[:;]", self.line))
        self.next_delim()
        name = self.line[: self.delim.start()]
        self.cl = ContentLine(name, line_nr=self.line_nr)

        while True:
            # everything before delim.start() is already processed and we should start reading at delim.end()
            if self.delim.group() == ":":
                self.cl.value = self.line[self.delim.end() :]
                if self.always_check:
                    self.check_parsed_line()
                return self.cl

            assert self.delim.group() == ";"
            self.parse_param()

    def parse_param(self):
        try:
            param_delim = self.line.index("=", self.delim.end())
        except ValueError:
            raise self.error("contains param without value", self.delim.end())

        # read comma-separated and possibly quoted param values
        param_name = self.line[self.delim.end() : param_delim]
        self.cl.params[param_name] = self.param_values = []
        self.param_value_start = param_delim + 1
        self.next_delim()  # proceed to delim after param value list
        has_further_param_value = True
        while has_further_param_value:
            if self.delim.start() <= self.param_value_start:
                raise self.error(
                    "contains param with an empty value",
                    (self.delim.start(), self.param_value_start),
                )

            if self.line[self.param_value_start] == Patterns.DQUOTE:
                has_further_param_value = self.parse_quoted_param_val()
            else:
                has_further_param_value = self.parse_raw_param_val()

    def parse_quoted_param_val(self):
        self.param_value_start += 1  # skip the quote
        try:
            param_quote_stop = self.line.index(Patterns.DQUOTE, self.param_value_start)
        except ValueError:
            raise self.error(
                "contains param missing a closing quote", self.param_value_start
            )
        self.param_values.append(
            QuotedParamValue(
                unescape_param(self.line[self.param_value_start : param_quote_stop])
            )
        )

        # reposition the delims sequence, skipping any delimiter until right after the closing quote
        self.param_value_start = param_quote_stop + 1
        while self.delim.start() < self.param_value_start:
            self.next_delim()

        # continue with whatever comes after the closing quote
        if self.delim.start() == self.param_value_start:
            return False  # this was the last value for this param
        if self.line[self.param_value_start] == ",":
            self.param_value_start += (
                1  # skip the comma and continue with the next param value
            )
            return True  # there's a next value following for this param
        else:
            raise self.error(
                "contains param with content trailing after closing quote",
                (self.param_value_start, self.delim.start()),
            )

    def parse_raw_param_val(self):
        param_comma = self.line.find(",", self.param_value_start, self.delim.start())
        if param_comma < 0:
            self.param_values.append(
                unescape_param(self.line[self.param_value_start : self.delim.start()])
            )
            return False  # this was the last value for this param
        else:
            self.param_values.append(
                unescape_param(self.line[self.param_value_start : param_comma])
            )
            self.param_value_start = param_comma + 1
            return True  # there's a next value following for this param

    def check_parsed_line(self):
        assert re.match(Patterns.IDENTIFIER, self.cl.name)
        for key, vals in self.cl.params.items():
            assert re.match(Patterns.IDENTIFIER, key)
            for val in vals:
                if isinstance(val, QuotedParamValue):
                    assert re.match(Patterns.QSAFE_CHARS, str(val))
                else:
                    assert re.match(Patterns.SAFE_CHARS, val)
        assert re.match(Patterns.VALUE_CHARS, self.cl.name)
