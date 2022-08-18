from typing import Iterable

from ics.contentline.container import (
    Container,
    ContentLine,
    ParseError,
    QuotedParamValue,
)
from ics.contentline.parser import ParserClass
from ics.types import ContainerItem
from ics.utils import one

Parser = ParserClass()
string_to_containers = Parser.string_to_containers
lines_to_containers = Parser.lines_to_containers


def string_to_container(txt: str) -> ContainerItem:
    return one(string_to_containers(txt))


def lines_to_container(lines: Iterable[str]) -> ContainerItem:
    return one(lines_to_containers(lines))


__all__ = [
    "ParseError",
    "QuotedParamValue",
    "ContentLine",
    "Container",
    "Parser",
    "string_to_containers",
    "lines_to_containers",
    "string_to_container",
    "lines_to_container",
]
