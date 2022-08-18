import base64
from typing import Type, Union
from urllib.parse import urlparse

from ics.types import URL, ContextDict, EmptyContext, EmptyParams, ExtraParams
from ics.valuetype.base import ValueConverter

__all__ = [
    "BinaryConverter",
    "BooleanConverter",
    "IntegerConverter",
    "FloatConverter",
    "URIConverter",
    "CalendarUserAddressConverter",
]


class BinaryConverterClass(ValueConverter[bytes]):
    @property
    def ics_type(self) -> str:
        return "BINARY"

    @property
    def python_type(self) -> Type[bytes]:
        return bytes

    def parse(
        self,
        value: str,
        params: ExtraParams = EmptyParams,
        context: ContextDict = EmptyContext,
    ) -> bytes:
        return base64.b64decode(value)

    def serialize(
        self,
        value: bytes,
        params: ExtraParams = EmptyParams,
        context: ContextDict = EmptyContext,
    ) -> str:
        return base64.b64encode(value).decode("ascii")


BinaryConverter = BinaryConverterClass()
ValueConverter.BY_TYPE[bytearray] = ValueConverter.BY_TYPE[bytes]


class BooleanConverterClass(ValueConverter[bool]):
    @property
    def ics_type(self) -> str:
        return "BOOLEAN"

    @property
    def python_type(self) -> Type[bool]:
        return bool

    def parse(
        self,
        value: str,
        params: ExtraParams = EmptyParams,
        context: ContextDict = EmptyContext,
    ) -> bool:
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
                raise ValueError(f"can't interpret '{value}' as boolean")

    def serialize(
        self,
        value: Union[bool, str],
        params: ExtraParams = EmptyParams,
        context: ContextDict = EmptyContext,
    ) -> str:
        if isinstance(value, str):
            value = self.parse(value, params, context)
        if value:
            return "TRUE"
        else:
            return "FALSE"


BooleanConverter = BooleanConverterClass()


class IntegerConverterClass(ValueConverter[int]):
    @property
    def ics_type(self) -> str:
        return "INTEGER"

    @property
    def python_type(self) -> Type[int]:
        return int

    def parse(
        self,
        value: str,
        params: ExtraParams = EmptyParams,
        context: ContextDict = EmptyContext,
    ) -> int:
        return int(value)

    def serialize(
        self,
        value: int,
        params: ExtraParams = EmptyParams,
        context: ContextDict = EmptyContext,
    ) -> str:
        return str(value)


IntegerConverter = IntegerConverterClass()


class FloatConverterClass(ValueConverter[float]):
    @property
    def ics_type(self) -> str:
        return "FLOAT"

    @property
    def python_type(self) -> Type[float]:
        return float

    def parse(
        self,
        value: str,
        params: ExtraParams = EmptyParams,
        context: ContextDict = EmptyContext,
    ) -> float:
        return float(value)

    def serialize(
        self,
        value: float,
        params: ExtraParams = EmptyParams,
        context: ContextDict = EmptyContext,
    ) -> str:
        return str(value)


FloatConverter = FloatConverterClass()


class URIConverterClass(ValueConverter[URL]):
    # TODO URI PARAMs need percent escaping, preventing all illegal characters except for ", in which they also need to wrapped
    # TODO URI values also need percent escaping (escaping COMMA characters in URI Lists), but no quoting

    @property
    def ics_type(self) -> str:
        return "URI"

    @property
    def python_type(self) -> Type[URL]:
        return URL

    def parse(
        self,
        value: str,
        params: ExtraParams = EmptyParams,
        context: ContextDict = EmptyContext,
    ) -> URL:
        return urlparse(value)

    def serialize(
        self,
        value: URL,
        params: ExtraParams = EmptyParams,
        context: ContextDict = EmptyContext,
    ) -> str:
        if isinstance(value, str):
            return value
        else:
            return value.geturl()


URIConverter = URIConverterClass()


class CalendarUserAddressConverterClass(URIConverterClass):
    @property
    def ics_type(self) -> str:
        return "CAL-ADDRESS"


CalendarUserAddressConverter = CalendarUserAddressConverterClass
