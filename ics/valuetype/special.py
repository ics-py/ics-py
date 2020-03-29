from typing import Type

from ics.geo import Geo
from ics.valuetype.base import ValueConverter


class GeoConverter(ValueConverter[Geo]):

    @property
    def ics_type(self) -> str:
        return "X-GEO"

    @property
    def python_type(self) -> Type[Geo]:
        return Geo

    def parse(self, value: str) -> Geo:
        latitude, sep, longitude = value.partition(";")
        if not sep:
            raise ValueError("geo must have two float values")
        return Geo(float(latitude), float(longitude))

    def serialize(self, value: Geo) -> str:
        return "%f;%f" % value
