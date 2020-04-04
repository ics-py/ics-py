import abc
import inspect
from typing import Dict, Generic, Type, TypeVar

from ics.types import EmptyDict, ExtraParams

T = TypeVar('T')


class ValueConverter(abc.ABC, Generic[T]):
    BY_NAME: Dict[str, "ValueConverter"] = {}
    BY_TYPE: Dict[Type, "ValueConverter"] = {}
    INST: "ValueConverter[T]"

    def __init_subclass__(cls) -> None:
        super().__init_subclass__()
        if not inspect.isabstract(cls):
            cls.INST = cls()
            ValueConverter.BY_NAME[cls.INST.ics_type] = cls.INST
            ValueConverter.BY_TYPE.setdefault(cls.INST.python_type, cls.INST)

    @property
    @abc.abstractmethod
    def ics_type(self) -> str:
        pass

    @property
    @abc.abstractmethod
    def python_type(self) -> Type[T]:
        pass

    @abc.abstractmethod
    def parse(self, value: str, params: ExtraParams = EmptyDict, context: Dict = EmptyDict) -> T:
        pass

    @abc.abstractmethod
    def serialize(self, value: T, params: ExtraParams = EmptyDict, context: Dict = EmptyDict) -> str:
        pass

    def __str__(self):
        return "<" + self.__class__.__name__ + ">"

    def __hash__(self):
        return hash(type(self))
