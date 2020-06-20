import datetime
from typing import Dict, Union, Optional, List, Any

from attr import Attribute

from ics.component import Component
from ics.converter.base import AttributeConverter
from ics.converter.component import ComponentMeta, ImmutableComponentMeta
from ics.converter.timezone_utils import Timezone_from_builtin, Timezone_from_dateutil, Timezone_from_pytz, TimezoneResult
from ics.grammar import Container, string_to_container
from ics.timezone import Timezone, UTC, is_utc, TimezoneDaylightObservance, TimezoneStandardObservance, TimezoneObservance
from ics.types import ContextDict, ContainerItem
from ics.valuetype.datetime import DatetimeConverterMixin

__all__ = [
    "Timezone_from_tzid",
    "Timezone_from_tzinfo",
    "TimezoneMeta",
]


def Timezone_from_tzid(tzid: str) -> Timezone:
    import ics_vtimezones
    tz_ics = ics_vtimezones.find_file_for_tzid(tzid)
    if not tz_ics:
        olson_tzid = ics_vtimezones.windows_to_olson(tzid)
        if olson_tzid:
            tz_ics = ics_vtimezones.find_file_for_tzid(olson_tzid)
    if not tz_ics:
        raise ValueError("no vTimezone.ics file found for %s" % tzid)
    ics_cal = string_to_container(tz_ics.read_text())
    if not (len(ics_cal) == 1 and len(ics_cal[0]) == 3 and ics_cal[0][2].name == "VTIMEZONE"):
        raise ValueError("vTimezone.ics file %s has invalid content" % tz_ics)
    return Timezone.from_container(ics_cal[0][2])


def Timezone_from_tzinfo(tzinfo: datetime.tzinfo, context: Optional[ContextDict]) -> Optional[Timezone]:
    if isinstance(tzinfo, Timezone):
        return tzinfo
    if is_utc(tzinfo):
        return UTC

    cache: Dict[Union[int, datetime.tzinfo], Optional[Timezone]] = {}
    the_id: Any = 0
    if context is not None:
        context.setdefault("tzinfo_CACHE", cache)
        try:
            hash(tzinfo)
        except TypeError:
            the_id = id(tzinfo)
        else:
            the_id = tzinfo
        if the_id in cache:
            return cache[the_id]

    tz: Union[Timezone, TimezoneResult]
    for func in (Timezone_from_builtin, Timezone_from_dateutil, Timezone_from_pytz):
        tz = func(tzinfo)
        if tz == TimezoneResult.CONTINUE:
            continue
        elif tz == TimezoneResult.LOCAL:
            if context is not None:
                cache[the_id] = None
            return None
        elif tz in [TimezoneResult.UNSERIALIZABLE, TimezoneResult.NOT_IMPLEMENTED]:
            break
        else:
            assert isinstance(tz, Timezone)
            if context is not None:
                cache[the_id] = tz
            return tz

    raise ValueError("can't produce Timezone from %s %r" % (type(tzinfo).__qualname__, tzinfo))


class TimezoneMeta(ImmutableComponentMeta):
    def load_instance(self, container: Container, context: Optional[ContextDict] = None):
        # TODO  The mandatory "DTSTART" property gives the effective onset date
        #       and local time for the time zone sub-component definition.
        #       "DTSTART" in this usage MUST be specified as a date with a local
        #       time value.

        instance = super().load_instance(container, context)
        if context is not None:
            available_tz = context.setdefault(DatetimeConverterMixin.CONTEXT_KEY_AVAILABLE_TZ, {})
            available_tz.setdefault(instance.tzid, instance)
        return instance


class TimezoneObservanceMemberMeta(AttributeConverter):
    @property
    def filter_ics_names(self) -> List[str]:
        return [TimezoneStandardObservance.NAME, TimezoneDaylightObservance.NAME]

    def populate(self, component: Component, item: ContainerItem, context: ContextDict) -> bool:
        assert isinstance(item, Container)
        if item.name.upper() == TimezoneStandardObservance.NAME:
            self.set_or_append_value(component, TimezoneStandardObservance.from_container(item, context))
        elif item.name.upper() == TimezoneDaylightObservance.NAME:
            self.set_or_append_value(component, TimezoneDaylightObservance.from_container(item, context))
        else:
            raise ValueError("can't populate TimezoneObservance from %s %s: %s" % (type(item), item.name, item))
        return True

    def serialize(self, parent: Component, output: Container, context: ContextDict):
        extras = self.get_extra_params(parent)
        if extras:
            raise ValueError("ComponentConverter %s can't serialize extra params %s", (self, extras))
        for value in self.get_value_list(parent):
            output.append(value.to_container(context))


class TimezoneObservanceMeta(ImmutableComponentMeta):
    def __call__(self, attribute: Attribute):
        return TimezoneObservanceMemberMeta(attribute)


ComponentMeta.BY_TYPE[TimezoneObservance] = TimezoneObservanceMeta(TimezoneObservance)
ComponentMeta.BY_TYPE[TimezoneStandardObservance] = ImmutableComponentMeta(TimezoneStandardObservance)
ComponentMeta.BY_TYPE[TimezoneDaylightObservance] = ImmutableComponentMeta(TimezoneDaylightObservance)
ComponentMeta.BY_TYPE[Timezone] = TimezoneMeta(Timezone)
