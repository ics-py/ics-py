from typing import Dict, List

import attr

from ics import Calendar
from ics.component import Component
from ics.converter.base import AttributeConverter
from ics.converter.component import ComponentMeta
from ics.grammar import Container
from ics.timezone import Timezone
from ics.types import ContainerItem, ContextDict
from ics.valuetype.datetime import DatetimeConverterMixin

__all__ = [
    "CalendarTimezoneConsumer",
    "CalendarMeta",
]


class CalendarTimezoneConsumer(AttributeConverter):
    @property
    def filter_ics_names(self) -> List[str]:
        return [Timezone.NAME]

    def populate(self, component: Component, item: ContainerItem, context: ContextDict) -> bool:
        return item.name == Timezone.NAME and isinstance(item, Container)

    def serialize(self, component: Component, output: Container, context: ContextDict):
        return


class CalendarMeta(ComponentMeta):
    def find_converters(self):
        timezones_field = attr.fields(Calendar).timezones
        return [c for c in super().find_converters() if c.attribute != timezones_field] + [CalendarTimezoneConsumer(timezones_field)]

    def _populate_attrs(self, instance: Component, container: Container, context: ContextDict):
        assert isinstance(instance, Calendar)
        avail_tz: Dict[str, Timezone] = context.setdefault(DatetimeConverterMixin.CONTEXT_KEY_AVAILABLE_TZ, {})
        for child in container:
            if child.name == Timezone.NAME and isinstance(child, Container):
                tz = Timezone.from_container(child)
                avail_tz.setdefault(tz.tzid, tz)

        super()._populate_attrs(instance, container, context)

        instance.timezones = context[DatetimeConverterMixin.CONTEXT_KEY_AVAILABLE_TZ].values()

    def _serialize_attrs(self, component: Component, context: ContextDict, container: Container):
        assert isinstance(component, Calendar)
        avail_tz: Dict[str, Timezone] = context.setdefault(DatetimeConverterMixin.CONTEXT_KEY_AVAILABLE_TZ, {})
        for tz in component.timezones:
            avail_tz.setdefault(tz.tzid, tz)

        super()._serialize_attrs(component, context, container)

        timezones = [tz.to_container() for tz in context[DatetimeConverterMixin.CONTEXT_KEY_AVAILABLE_TZ].values()]
        container.data = timezones + container.data


ComponentMeta.BY_TYPE[Calendar] = CalendarMeta(Calendar)
