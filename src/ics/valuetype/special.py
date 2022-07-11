import abc
from typing import Type, Generic, TypeVar, Union, cast
from urllib.parse import urlparse

from ics import Attendee, Organizer
from ics.attendee import Person
from ics.geo import Geo
from ics.types import EmptyParams, ExtraParams, URL, singleton
from ics.valuetype.base import ValueConverter

__all__ = ["GeoConverter", "OrganizerConverter", "AttendeeConverter"]


@singleton
class GeoConverter(ValueConverter[Geo]):
    @property
    def ics_type(self) -> str:
        return "X-GEO"

    @property
    def python_type(self) -> Type[Geo]:
        return Geo

    def parse(self, value: str, params: ExtraParams = EmptyParams) -> Geo:
        latitude, sep, longitude = value.partition(";")
        if not sep:
            raise ValueError("geo must have two float values")
        return Geo(float(latitude), float(longitude))

    def serialize(self, value: Geo, params: ExtraParams = EmptyParams) -> str:
        return "%f;%f" % value


P = TypeVar('P', bound=Person)


class PersonConverter(Generic[P], ValueConverter[P], abc.ABC):
    def parse(self, value: str, params: ExtraParams = EmptyParams) -> P:
        val = self.python_type(email=urlparse(value), extra=dict(params))
        params.clear()
        return val

    def serialize(self, value: Union[P, str], params: ExtraParams = EmptyParams) -> str:
        if isinstance(value, Person):
            params.update(value.extra)
            value = value.email
        if isinstance(value, str):
            return value
        else:
            return cast(URL, value).geturl()


@singleton
class OrganizerConverter(PersonConverter[Organizer]):
    @property
    def ics_type(self) -> str:
        return "ORGANIZER"

    @property
    def python_type(self) -> Type[Organizer]:
        return Organizer


@singleton
class AttendeeConverter(PersonConverter[Attendee]):
    @property
    def ics_type(self) -> str:
        return "ATTENDEE"

    @property
    def python_type(self) -> Type[Attendee]:
        return Attendee
