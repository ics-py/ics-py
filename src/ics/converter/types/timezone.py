from typing import List, Optional

from attr import Attribute

from ics.component import Component
from ics.contentline import Container
from ics.converter.base import AttributeConverter
from ics.converter.component import ComponentMeta, ImmutableComponentMeta
from ics.timezone import (
    Timezone,
    TimezoneDaylightObservance,
    TimezoneObservance,
    TimezoneStandardObservance,
)
from ics.types import ContainerItem, ContextDict
from ics.valuetype.datetime import DatetimeConverterMixin


class TimezoneMeta(ImmutableComponentMeta):
    def load_instance(
        self, container: Container, context: Optional[ContextDict] = None
    ):
        # TODO  The mandatory "DTSTART" property gives the effective onset date
        #       and local time for the time zone sub-component definition.
        #       "DTSTART" in this usage MUST be specified as a date with a local
        #       time value.

        instance = super().load_instance(container, context)
        if context is not None:
            available_tz = context.setdefault(
                DatetimeConverterMixin.CONTEXT_KEY_AVAILABLE_TZ, {}
            )
            available_tz.setdefault(instance.tzid, instance)
        return instance


class TimezoneObservanceMemberMeta(AttributeConverter):
    @property
    def filter_ics_names(self) -> List[str]:
        return [TimezoneStandardObservance.NAME, TimezoneDaylightObservance.NAME]

    def populate(
        self, component: Component, item: ContainerItem, context: ContextDict
    ) -> bool:
        assert isinstance(item, Container)
        if item.name.upper() == TimezoneStandardObservance.NAME:
            self.set_or_append_value(
                component, TimezoneStandardObservance.from_container(item, context)
            )
        elif item.name.upper() == TimezoneDaylightObservance.NAME:
            self.set_or_append_value(
                component, TimezoneDaylightObservance.from_container(item, context)
            )
        else:
            raise ValueError(
                "can't populate TimezoneObservance from {} {}: {}".format(
                    type(item), item.name, item
                )
            )
        return True

    def serialize(self, parent: Component, output: Container, context: ContextDict):
        extras = self.get_extra_params(parent)
        if extras:
            raise ValueError(
                "ComponentConverter %s can't serialize extra params %s", (self, extras)
            )
        for value in self.get_value_list(parent):
            output.append(value.to_container(context))


class TimezoneObservanceMeta(ImmutableComponentMeta):
    def __call__(self, attribute: Attribute):
        return TimezoneObservanceMemberMeta(attribute)


ComponentMeta.BY_TYPE[TimezoneObservance] = TimezoneObservanceMeta(TimezoneObservance)
ComponentMeta.BY_TYPE[TimezoneStandardObservance] = ImmutableComponentMeta(
    TimezoneStandardObservance
)
ComponentMeta.BY_TYPE[TimezoneDaylightObservance] = ImmutableComponentMeta(
    TimezoneDaylightObservance
)
ComponentMeta.BY_TYPE[Timezone] = TimezoneMeta(Timezone)
