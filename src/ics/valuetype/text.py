import re
import warnings
from typing import Iterable, Iterator, Type

from ics.types import ContextDict, EmptyContext, EmptyParams, ExtraParams
from ics.utils import next_after_str_escape
from ics.valuetype.base import ValueConverter

__all__ = ["TextConverter"]


class TextConverter(ValueConverter[str]):

    @property
    def ics_type(self) -> str:
        return "TEXT"

    @property
    def python_type(self) -> Type[str]:
        return str

    def parse(self, value: str, params: ExtraParams = EmptyParams, context: ContextDict = EmptyContext) -> str:
        return self.unescape_text(value)

    def serialize(self, value: str, params: ExtraParams = EmptyParams, context: ContextDict = EmptyContext) -> str:
        return self.escape_text(value)

    def split_value_list(self, values: str) -> Iterable[str]:
        it = iter(values.split(","))
        for val in it:
            while val.endswith("\\") and not val.endswith("\\\\"):
                val += "," + next_after_str_escape(it, full_str=values)
            yield val

    def join_value_list(self, values: Iterable[str]) -> str:
        def checked_iter():
            for value in values:
                m = re.search(r"\\[;,]|" + "[\n\r]", value)
                if m:
                    warnings.warn("TEXT value in list may not contain %s: %s" % (m, value))
                yield value

        return ",".join(checked_iter())

    @classmethod
    def escape_text(cls, string: str) -> str:
        return string.translate(
            {ord("\\"): "\\\\",
             ord(";"): "\\;",
             ord(","): "\\,",
             ord("\n"): "\\n",
             ord("\r"): "\\r"})

    @classmethod
    def unescape_text(cls, string: str) -> str:
        return "".join(cls.unescape_text_iter(string))

    @classmethod
    def unescape_text_iter(cls, string: str) -> Iterator[str]:
        it = iter(string)
        for c1 in it:
            if c1 == "\\":
                c2 = next_after_str_escape(it, full_str=string)
                if c2 == ";":
                    yield ";"
                elif c2 == ",":
                    yield ","
                elif c2 == "n" or c2 == "N":
                    yield "\n"
                elif c2 == "r" or c2 == "R":
                    yield "\r"
                elif c2 == "\\":
                    yield "\\"
                else:
                    raise ValueError("can't handle escaped character '%s'" % c2)
            elif c1 in ";,\n\r":
                raise ValueError("unescaped character '%s' in TEXT value" % c1)
            else:
                yield c1
