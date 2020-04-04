from typing import Dict, Type

from ics.geo import Geo
from ics.types import EmptyDict, ExtraParams
from ics.valuetype.base import ValueConverter


class GeoConverter(ValueConverter[Geo]):

    @property
    def ics_type(self) -> str:
        return "X-GEO"

    @property
    def python_type(self) -> Type[Geo]:
        return Geo

    def parse(self, value: str, params: ExtraParams = EmptyDict, context: Dict = EmptyDict) -> Geo:
        latitude, sep, longitude = value.partition(";")
        if not sep:
            raise ValueError("geo must have two float values")
        return Geo(float(latitude), float(longitude))

    def serialize(self, value: Geo, params: ExtraParams = EmptyDict, context: Dict = EmptyDict) -> str:
        return "%f;%f" % value
