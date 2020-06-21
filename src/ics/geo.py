from typing import Dict, NamedTuple, Tuple, Union, overload


class Geo(NamedTuple):
    latitude: float
    longitude: float


@overload
def make_geo(value: None) -> None:
    ...


@overload
def make_geo(value: Union[Dict[str, float], Tuple[float, float]]) -> "Geo":
    ...


def make_geo(value):
    if isinstance(value, dict):
        return Geo(**value)
    elif isinstance(value, tuple):
        return Geo(*value)
    else:
        return None
