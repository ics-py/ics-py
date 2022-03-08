import itertools
from typing import Dict, List

from ics import Calendar
from ics.component import Component
from ics.converter.base import GenericConverter, sort_converters
from ics.converter.component import ComponentMeta
from ics.contentline import Container
from ics.timezone import Timezone
from ics.types import ContainerItem, ContextDict
from ics.valuetype.datetime import DatetimeConverterMixin


class CalendarMeta(ComponentMeta):
    """Slightly modified meta class for Calendars.

    * makes sure that `Timezone`s are always loaded first and that all
      contained timezones are serialized.
    * when present, X-WR-CALNAME is being written to NAME. In case both
      X-WR-CALNAME and NAME are present, NAME takes precedence as it's the
      only property defined in the RFC-7986.

    """

    def find_converters(self):
        return sort_converters(itertools.chain(
            super(CalendarMeta, self).find_converters(),
            (CalendarTimezoneConverter(), CalendarNameConverter())
        ))

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

        # serialize all used timezones
        timezones = [tz.to_container() for tz in context[DatetimeConverterMixin.CONTEXT_KEY_AVAILABLE_TZ].values()]
        # insert them at the place where they usually would have been serialized
        split = context["VTIMEZONES_AFTER"]
        container.data = container.data[:split] + timezones + container.data[split:]


class CalendarTimezoneConverter(GenericConverter):
    @property
    def priority(self) -> int:
        return 500

    @property
    def filter_ics_names(self) -> List[str]:
        return [Timezone.NAME]

    def populate(self, component: Component, item: ContainerItem, context: ContextDict) -> bool:
        # don't actually load anything, as that has already been done before all other deserialization in `CalendarMeta`
        return item.name == Timezone.NAME and isinstance(item, Container)

    def serialize(self, component: Component, output: Container, context: ContextDict):
        # store the place where we should insert all the timezones
        context["VTIMEZONES_AFTER"] = len(output)


class CalendarNameConverter(GenericConverter):
    @property
    def priority(self) -> int:
        return 600

    @property
    def filter_ics_names(self) -> List[str]:
        return ["NAME", "X-WR-CALNAME"]

    def populate(self, component: Component, item: ContainerItem, context: ContextDict) -> bool:
        if item.name == "NAME":
            return True
        if item.name == "X-WR-CALNAME":
            if component.name is not None:
                return False

            component.name = item.value
            return False

    def serialize(self, component: Component, output: Container, context: ContextDict):
        pass


ComponentMeta.BY_TYPE[Calendar] = CalendarMeta(Calendar)
