import base64
from typing import Type
from urllib.parse import ParseResult as URL, urlparse

from dateutil.rrule import rrule

from ics.valuetype.base import ValueConverter


class TextConverter(ValueConverter[str]):

    @property
    def ics_type(self) -> str:
        return "TEXT"

    @property
    def python_type(self) -> Type[str]:
        return str

    def parse(self, value: str) -> str:
        return value

    def serialize(self, value: str) -> str:
        return value


class BinaryConverter(ValueConverter[bytes]):

    @property
    def ics_type(self) -> str:
        return "BINARY"

    @property
    def python_type(self) -> Type[bytes]:
        return bytes

    def parse(self, value: str) -> bytes:
        return base64.b64decode(value)

    def serialize(self, value: bytes) -> str:
        return base64.b64encode(value).decode("ascii")


ValueConverter.BY_TYPE[bytearray] = ValueConverter.BY_TYPE[bytes]


class BooleanConverter(ValueConverter[bool]):

    @property
    def ics_type(self) -> str:
        return "BOOLEAN"

    @property
    def python_type(self) -> Type[bool]:
        return bool

    def parse(self, value: str) -> bool:
        if value == "TRUE":
            return True
        elif value == "FALSE":
            return False
        else:
            value = value.upper()
            if value == "TRUE":
                return True
            elif value == "FALSE":
                return False
            elif value in ["T", "Y", "YES", "ON", "1"]:
                return True
            elif value in ["F", "N", "NO", "OFF", "0"]:
                return False
            else:
                raise ValueError("can't interpret '%s' as boolen" % value)

    def serialize(self, value: bool) -> str:
        if value:
            return "TRUE"
        else:
            return "FALSE"


class IntegerConverter(ValueConverter[int]):

    @property
    def ics_type(self) -> str:
        return "INTEGER"

    @property
    def python_type(self) -> Type[int]:
        return int

    def parse(self, value: str) -> int:
        return int(value)

    def serialize(self, value: int) -> str:
        return str(value)


class FloatConverter(ValueConverter[float]):

    @property
    def ics_type(self) -> str:
        return "FLOAT"

    @property
    def python_type(self) -> Type[float]:
        return float

    def parse(self, value: str) -> float:
        return float(value)

    def serialize(self, value: float) -> str:
        return str(value)


class RecurConverter(ValueConverter[rrule]):

    @property
    def ics_type(self) -> str:
        return "RECUR"

    @property
    def python_type(self) -> Type[rrule]:
        return rrule

    def parse(self, value: str) -> rrule:
        # this won't be called unless a class specifies an attribute with type: rrule
        raise NotImplementedError("parsing 'RECUR' is not yet supported")

    def serialize(self, value: rrule) -> str:
        raise NotImplementedError("serializing 'RECUR' is not yet supported")


class URIConverter(ValueConverter[URL]):

    @property
    def ics_type(self) -> str:
        return "URI"

    @property
    def python_type(self) -> Type[URL]:
        return URL

    def parse(self, value: str) -> URL:
        return urlparse(value)

    def serialize(self, value: URL) -> str:
        if isinstance(value, str):
            return value
        else:
            return value.geturl()


class CalendarUserAddressConverter(URIConverter):

    @property
    def ics_type(self) -> str:
        return "CAL-ADDRESS"
