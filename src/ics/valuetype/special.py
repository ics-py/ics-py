import abc
from typing import Type, Generic
from urllib.parse import urlparse

from ics import Attendee, Organizer
from ics.attendee import Person
from ics.geo import Geo
from ics.types import ContextDict, EmptyContext, EmptyParams, ExtraParams, copy_extra_params
from ics.valuetype.base import ValueConverter, T

__all__ = ["GeoConverter"]


class GeoConverterClass(ValueConverter[Geo]):

    @property
    def ics_type(self) -> str:
        return "X-GEO"

    @property
    def python_type(self) -> Type[Geo]:
        return Geo

    def parse(self, value: str, params: ExtraParams = EmptyParams, context: ContextDict = EmptyContext) -> Geo:
        latitude, sep, longitude = value.partition(";")
        if not sep:
            raise ValueError("geo must have two float values")
        return Geo(float(latitude), float(longitude))

    def serialize(self, value: Geo, params: ExtraParams = EmptyParams, context: ContextDict = EmptyContext) -> str:
        return "%f;%f" % value


GeoConverter = GeoConverterClass()


class PersonConverter(Generic[T], ValueConverter[T], abc.ABC):
    def parse(self, value: str, params: ExtraParams = EmptyParams, context: ContextDict = EmptyContext) -> T:
        val = self.python_type(email=urlparse(value), extra=dict(params))
        params.clear()
        return val

    def serialize(self, value: T, params: ExtraParams = EmptyParams, context: ContextDict = EmptyContext) -> str:
        if isinstance(value, Person):
            params.update(value.extra)
            value = value.email
        if isinstance(value, str):
            return value
        else:
            return value.geturl()


class OrganizerConverterClass(PersonConverter[Organizer]):
    @property
    def ics_type(self) -> str:
        return "ORGANIZER"

    @property
    def python_type(self) -> Type[Organizer]:
        return Organizer


OrganizerConverter = OrganizerConverterClass()


class AttendeeConverterClass(PersonConverter[Attendee]):
    @property
    def ics_type(self) -> str:
        return "ATTENDEE"

    @property
    def python_type(self) -> Type[Attendee]:
        return Attendee


AttendeeConverter = AttendeeConverterClass()
