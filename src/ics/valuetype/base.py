import abc
from typing import Dict, Generic, Iterable, Type, TypeVar

from ics.types import ContextDict, EmptyContext, EmptyParams, ExtraParams

T = TypeVar("T")

__all__ = ["ValueConverter"]


class ValueConverter(Generic[T], abc.ABC):
    BY_NAME: Dict[str, "ValueConverter"] = {}
    BY_TYPE: Dict[Type, "ValueConverter"] = {}

    def __init__(self):
        ValueConverter.BY_NAME[self.ics_type] = self
        ValueConverter.BY_TYPE.setdefault(self.python_type, self)

    @property
    @abc.abstractmethod
    def ics_type(self) -> str:
        ...

    @property
    @abc.abstractmethod
    def python_type(self) -> Type[T]:
        ...

    def split_value_list(self, values: str) -> Iterable[str]:
        yield from values.split(",")

    def join_value_list(self, values: Iterable[str]) -> str:
        return ",".join(values)

    @abc.abstractmethod
    def parse(
        self,
        value: str,
        params: ExtraParams = EmptyParams,
        context: ContextDict = EmptyContext,
    ) -> T:
        ...

    @abc.abstractmethod
    def serialize(
        self,
        value: T,
        params: ExtraParams = EmptyParams,
        context: ContextDict = EmptyContext,
    ) -> str:
        ...

    def __str__(self):
        return "<" + self.__class__.__name__ + ">"

    def __hash__(self):
        return hash(type(self))
