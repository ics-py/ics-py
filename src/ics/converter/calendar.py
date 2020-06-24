import itertools
from typing import Dict, List

from ics import Calendar
from ics.component import Component
from ics.converter.base import GenericConverter, sort_converters
from ics.converter.component import ComponentMeta
from ics.grammar import Container
from ics.timezone import Timezone
from ics.types import ContainerItem, ContextDict
from ics.valuetype.datetime import DatetimeConverterMixin

__all__ = [
    "CalendarTimezoneConverter",
    "CalendarMeta",
]


class CalendarTimezoneConverter(GenericConverter):
    @property
    def priority(self) -> int:
        return 600

    @property
    def filter_ics_names(self) -> List[str]:
        return [Timezone.NAME]

    def populate(self, component: Component, item: ContainerItem, context: ContextDict) -> bool:
        return item.name == Timezone.NAME and isinstance(item, Container)

    def serialize(self, component: Component, output: Container, context: ContextDict):
        context["VTIMEZONES_AFTER"] = len(output)


class CalendarMeta(ComponentMeta):
    def find_converters(self):
        return sort_converters(itertools.chain(super(CalendarMeta, self).find_converters(), (CalendarTimezoneConverter(),)))

    def _populate_attrs(self, instance: Component, container: Container, context: ContextDict):
        assert isinstance(instance, Calendar)
        avail_tz: Dict[str, Timezone] = context.setdefault(DatetimeConverterMixin.CONTEXT_KEY_AVAILABLE_TZ, {})
        for child in container:
            if child.name == Timezone.NAME and isinstance(child, Container):
                tz = Timezone.from_container(child)
                avail_tz.setdefault(tz.tzid, tz)

        super()._populate_attrs(instance, container, context)

    def _serialize_attrs(self, component: Component, context: ContextDict, container: Container):
        assert isinstance(component, Calendar)
        context.setdefault(DatetimeConverterMixin.CONTEXT_KEY_AVAILABLE_TZ, {})
        super()._serialize_attrs(component, context, container)

        timezones = [tz.to_container() for tz in context[DatetimeConverterMixin.CONTEXT_KEY_AVAILABLE_TZ].values()]
        split = context["VTIMEZONES_AFTER"]
        container.data = container.data[:split] + timezones + container.data[split:]


ComponentMeta.BY_TYPE[Calendar] = CalendarMeta(Calendar)
