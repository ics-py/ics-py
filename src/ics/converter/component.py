from collections import defaultdict
from typing import Dict, Iterable, List, Optional, Tuple, Type, cast, ClassVar

import attr
from attr import Attribute

from ics.component import Component
from ics.converter.base import AttributeConverter, GenericConverter
from ics.contentline import Container
from ics.types import ContainerItem, ContextDict
from ics.utils import check_is_instance

__all__ = [
    "MemberComponentConverter",
    "ComponentMeta",
]


@attr.s(frozen=True)
class MemberComponentConverter(AttributeConverter):
    meta: "ComponentMeta" = attr.ib()

    @property
    def filter_ics_names(self) -> List[str]:
        return [self.meta.component_type.NAME]

    def populate(self, component: Component, item: ContainerItem, context: ContextDict) -> bool:
        assert isinstance(item, Container)
        self._check_component(component, context)
        self.set_or_append_value(component, self.meta.load_instance(item, context))
        return True

    def serialize(self, parent: Component, output: Container, context: ContextDict):
        self._check_component(parent, context)
        extras = self.get_extra_params(parent)
        if extras:
            raise ValueError("ComponentConverter %s can't serialize extra params %s", (self, extras))
        for value in self.get_value_list(parent):
            output.append(self.meta.serialize_toplevel(value, context))


@attr.s(frozen=True)
class ComponentMeta(object):
    BY_TYPE: ClassVar[Dict[Type, "ComponentMeta"]] = {}

    component_type: Type[Component] = attr.ib()

    converters: Tuple[GenericConverter, ...]
    converter_lookup: Dict[str, Tuple[GenericConverter]]

    def __attrs_post_init__(self):
        object.__setattr__(self, "converters", tuple(self.find_converters()))
        converter_lookup = defaultdict(list)
        for converter in self.converters:
            for name in converter.filter_ics_names:
                converter_lookup[name].append(converter)
        object.__setattr__(self, "converter_lookup", {k: tuple(vs) for k, vs in converter_lookup.items()})

        AttributeConverter.BY_TYPE[self.component_type] = self

    def find_converters(self) -> Iterable["AttributeConverter"]:
        converters = cast(Iterable["AttributeConverter"], filter(bool, (
            AttributeConverter.get_converter_for(a) for a in attr.fields(self.component_type))))
        return sorted(converters, key=lambda c: c.priority)

    def __call__(self, attribute: Attribute):
        return MemberComponentConverter(attribute, self)

    def load_instance(self, container: Container, context: Optional[ContextDict] = None):
        instance = self.component_type()
        self.populate_instance(instance, container, context)
        return instance

    def populate_instance(self, instance: "Component", container: Container, context: Optional[ContextDict] = None):
        if container.name != self.component_type.NAME:
            raise ValueError("container isn't an {}".format(self.component_type.NAME))
        check_is_instance("instance", instance, self.component_type)
        if not context:
            context = ContextDict(defaultdict(lambda: None))

        self._populate_attrs(instance, container, context)

    def _populate_attrs(self, instance: Component, container: Container, context: ContextDict):
        for line in container:
            consumed = False
            for conv in self.converter_lookup[line.name]:
                if conv.populate(instance, line, context):
                    consumed = True
            if not consumed:
                instance.extra.append(line)

        for conv in self.converters:
            conv.finalize(instance, context)

    def serialize_toplevel(self, component: Component, context: Optional[ContextDict] = None):
        check_is_instance("instance", component, self.component_type)
        if not context:
            context = ContextDict(defaultdict(lambda: None))
        container = Container(self.component_type.NAME)
        self._serialize_attrs(component, context, container)
        return container

    def _serialize_attrs(self, component: Component, context: ContextDict, container: Container):
        for conv in self.converters:
            conv.serialize(component, container, context)
        container.extend(component.extra)
        return container


@attr.s(frozen=True)
class ComponentConverter(AttributeConverter):
    meta: InflatedComponentMeta = attr.ib()

    @property
    def filter_ics_names(self) -> List[str]:
        return [self.meta.container_name]

    def populate(self, component: "Component", item: ContainerItem, context: ContextDict) -> bool:
        assert isinstance(item, Container)
        self._check_component(component, context)
        self.set_or_append_value(component, self.meta.load_instance(item, context))
        return True

    def serialize(self, parent: "Component", output: Container, context: ContextDict):
        extras = self.get_extra_params(parent)
        if extras:
            raise ValueError("ComponentConverter %s can't serialize extra params %s", (self, extras))
        for value in self.get_value_list(parent):
            output.append(self.meta.serialize_toplevel(value, context))


for ComponentClass in Component.SUBTYPES:
    ComponentMeta.BY_TYPE[ComponentClass] = ComponentMeta(ComponentClass)
