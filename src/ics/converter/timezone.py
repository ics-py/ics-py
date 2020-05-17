import datetime
from io import StringIO
from typing import Dict, Optional, TextIO, Tuple, Union

import dateutil

from ics.component import Component
from ics.converter.base import AttributeConverter
from ics.converter.component import InflatedComponentMeta
from ics.converter.timezone_utils import Timezone_from_builtin, Timezone_from_dateutil, Timezone_from_pytz
from ics.grammar import Container, string_to_container
from ics.timezone import Timezone, UTC, is_utc
from ics.types import ContextDict
from ics.valuetype.datetime import DatetimeConverterMixin


def tzical_from_str(val: str, filter_unknown: bool = False) -> Tuple[str, datetime.tzinfo]:
    fake_file = StringIO()
    if filter_unknown:
        for line in val.splitlines(keepends=True):
            if not line.startswith("X-") and not line.startswith("SEQUENCE"):
                fake_file.write(line)
    else:
        fake_file.write(val)
    fake_file.seek(0)
    return tzical_from_io(fake_file)


def tzical_from_io(val: TextIO) -> Tuple[str, datetime.tzinfo]:
    tzicals = dateutil.tz.tzical(val)
    tzids = tzicals.keys()
    if len(tzids) != 1:
        raise ValueError("got invalid amount of timezones: %s" % tzids)
    return tzids[0], tzicals.get()


def Timezone_from_tzid(tzid: str) -> Timezone:
    import ics_vtimezones
    tz_ics = ics_vtimezones.find_file_for_tzid(tzid)
    if not tz_ics:
        raise ValueError("no vTimezone.ics file found for %s" % tzid)
    ics_str = tz_ics.read_text()

    timezone = Timezone(*tzical_from_str(ics_str, filter_unknown=True))
    ics_cal = string_to_container(ics_str)
    if not (len(ics_cal) == 1 and len(ics_cal[0]) == 3 and ics_cal[0][2].name == "VTIMEZONE"):
        raise ValueError("vTimezone.ics file %s has invalid content" % tz_ics)
    timezone.extra.data.extend(ics_cal[0][2].data)

    return timezone


def Timezone_from_tzinfo(tzinfo: datetime.tzinfo, context: ContextDict) -> Timezone:
    if isinstance(tzinfo, Timezone):
        return tzinfo
    if is_utc(tzinfo):
        return UTC

    cache: Dict[Union[int, datetime.tzinfo], Timezone] = context.setdefault("tzinfo_CACHE", {})
    try:
        hash(tzinfo)
    except TypeError:
        the_id = id(tzinfo)
    else:
        the_id = tzinfo
    if the_id in cache:
        return cache[the_id]

    tz = Timezone_from_builtin(tzinfo)
    if not tz:
        tz = Timezone_from_dateutil(tzinfo)
    if not tz:
        tz = Timezone_from_pytz(tzinfo)
    if not tz:
        raise ValueError("can't produce Timezone from %s %r" % (type(tzinfo).__qualname__, tzinfo))

    cache[the_id] = tz
    return tz


class InflatedTimezoneMeta(InflatedComponentMeta):
    def load_instance(self, container: Container, context: Optional[ContextDict] = None):
        timezone = Timezone(*tzical_from_str(container.serialize(), filter_unknown=True))
        timezone.extra.data.extend(container.data)
        if context is not None:
            available_tz = context.setdefault(DatetimeConverterMixin.CONTEXT_KEY_AVAILABLE_TZ, {})
            available_tz.setdefault(timezone.tzid, timezone)
        return timezone

    def populate_instance(self, instance: "Component", container: Container, context: Optional[ContextDict] = None):
        raise RuntimeError("can't populate an existing Timezone")

    def serialize_toplevel(self, component: "Component", context: Optional[ContextDict] = None):
        if not component.extra:
            raise ValueError("can't serialize Timezone object without extra data")
        return component.extra


object.__setattr__(Timezone.MetaInfo, "inflated_meta_class", InflatedTimezoneMeta)
object.__setattr__(Timezone.MetaInfo, "converters", [])
