import abc
from typing import Generic, Iterable, Type, TypeVar, ClassVar, List

from ics.types import EmptyParams, ExtraParams

T = TypeVar('T')

__all__ = ["ValueConverter"]


class ValueConverter(Generic[T], abc.ABC):
    INSTANCES: ClassVar[List["ValueConverter"]] = []

    def __init__(self):
        ValueConverter.INSTANCES.append(self)

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
    def parse(self, value: str, params: ExtraParams = EmptyParams) -> T:
        ...

    @abc.abstractmethod
    def serialize(self, value: T, params: ExtraParams = EmptyParams) -> str:
        ...

    def __str__(self):
        return "<%s (%s -> %s)>" % (type(self).__name__, self.ics_type, self.python_type.__name__)

    def __repr__(self):
        return type(self).__qualname__

    def __hash__(self):
        return hash(type(self))

    def copy(self):
        return self  # state-less singleton
