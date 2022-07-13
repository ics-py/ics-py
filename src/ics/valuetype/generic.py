import base64
from typing import Type, Union, Generic
from urllib.parse import urlparse

from attr import frozen

from ics.types import EmptyParams, ExtraParams, URL, singleton
from ics.valuetype.base import ValueConverter, T

__all__ = [
    "BytesConverter",
    "BytearrayConverter",
    "BooleanConverter",
    "IntegerConverter",
    "FloatConverter",
    "URIConverter",
    "CalendarUserAddressConverter"
]


@frozen
class BinaryConverter(ValueConverter[T], Generic[T]):
    value_type: Type[T]

    @property
    def ics_type(self) -> str:
        return "BINARY"

    @property
    def python_type(self) -> Type[T]:
        return self.value_type

    def parse(self, value: str, params: ExtraParams = EmptyParams) -> T:
        return self.value_type(base64.b64decode(value))

    def serialize(self, value: T, params: ExtraParams = EmptyParams) -> str:
        return base64.b64encode(value).decode("ascii")


BytesConverter = BinaryConverter[bytes](bytes)
BytearrayConverter = BinaryConverter[bytearray](bytearray)


@singleton
class BooleanConverter(ValueConverter[bool]):
    @property
    def ics_type(self) -> str:
        return "BOOLEAN"

    @property
    def python_type(self) -> Type[bool]:
        return bool

    def parse(self, value: str, params: ExtraParams = EmptyParams) -> bool:
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
                raise ValueError("can't interpret '%s' as boolean" % value)

    def serialize(self, value: Union[bool, str], params: ExtraParams = EmptyParams) -> str:
        if isinstance(value, str):
            value = self.parse(value, params)
        if value:
            return "TRUE"
        else:
            return "FALSE"


@singleton
class IntegerConverter(ValueConverter[int]):
    @property
    def ics_type(self) -> str:
        return "INTEGER"

    @property
    def python_type(self) -> Type[int]:
        return int

    def parse(self, value: str, params: ExtraParams = EmptyParams) -> int:
        return int(value)

    def serialize(self, value: int, params: ExtraParams = EmptyParams) -> str:
        return str(value)


@singleton
class FloatConverter(ValueConverter[float]):
    @property
    def ics_type(self) -> str:
        return "FLOAT"

    @property
    def python_type(self) -> Type[float]:
        return float

    def parse(self, value: str, params: ExtraParams = EmptyParams) -> float:
        return float(value)

    def serialize(self, value: float, params: ExtraParams = EmptyParams) -> str:
        return str(value)


@singleton
class URIConverter(ValueConverter[URL]):
    # TODO URI PARAMs need percent escaping, preventing all illegal characters except for ", in which they also need to wrapped
    # TODO URI values also need percent escaping (escaping COMMA characters in URI Lists), but no quoting
    # TODO do not parse URIs?

    @property
    def ics_type(self) -> str:
        return "URI"

    @property
    def python_type(self) -> Type[URL]:
        return URL

    def parse(self, value: str, params: ExtraParams = EmptyParams) -> URL:
        return urlparse(value)

    def serialize(self, value: URL, params: ExtraParams = EmptyParams) -> str:
        if isinstance(value, str):
            return value
        else:
            return value.geturl()


@singleton
class CalendarUserAddressConverter(type(URIConverter)):
    @property
    def ics_type(self) -> str:
        return "CAL-ADDRESS"
