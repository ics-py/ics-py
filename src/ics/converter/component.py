from collections import defaultdict
from typing import Dict, Iterable, List, Optional, TYPE_CHECKING, Tuple, Type, cast

import attr
from attr import Attribute

from ics.converter.base import AttributeConverter, GenericConverter
from ics.grammar import Container
from ics.types import ContainerItem, ContextDict

if TYPE_CHECKING:
    from ics.component import Component


@attr.s(frozen=True)
class ComponentMeta(object):
    container_name: str = attr.ib()
    converter_class: Type["ComponentConverter"] = attr.ib(default=None)

    def inflate(self, component_type: Type["Component"]):
        if component_type.Meta is not self:
            raise ValueError("can't inflate %s for %s, it's meta is %s" % (self, component_type, component_type.Meta))
        converters = cast(Iterable["AttributeConverter"], filter(bool, (
            AttributeConverter.get_converter_for(a)
            for a in attr.fields(component_type)
        )))
        component_type.Meta = InflatedComponentMeta(
            component_type=component_type,
            converters=tuple(sorted(converters, key=lambda c: c.priority)),
            container_name=self.container_name,
            converter_class=self.converter_class or ComponentConverter)


@attr.s(frozen=True)
class InflatedComponentMeta(ComponentMeta):
    converters: Tuple[GenericConverter, ...] = attr.ib(default=None)
    component_type: Type["Component"] = attr.ib(default=None)

    converter_lookup: Dict[str, List[GenericConverter]]

    def __attrs_post_init__(self):
        object.__setattr__(self, "converter_lookup", defaultdict(list))
        for converter in self.converters:
            for name in converter.filter_ics_names:
                self.converter_lookup[name].append(converter)

    def __call__(self, attribute: Attribute):
        return self.converter_class(attribute, self)

    def load_instance(self, container: Container, context: Optional[ContextDict] = None):
        instance = self.component_type()
        self.populate_instance(instance, container, context)
        return instance

    def populate_instance(self, instance: "Component", container: Container, context: Optional[ContextDict] = None):
        if container.name != self.container_name:
            raise ValueError("container isn't an {}".format(self.container_name))
        if not context:
            context = ContextDict(defaultdict(lambda: None))

        for line in container:
            consumed = False
            for conv in self.converter_lookup[line.name]:
                if conv.populate(instance, line, context):
                    consumed = True
            if not consumed:
                instance.extra.append(line)

        for conv in self.converters:
            conv.finalize(instance, context)

    def serialize_toplevel(self, component: "Component", context: Optional[ContextDict] = None):
        if not context:
            context = ContextDict(defaultdict(lambda: None))
        container = Container(self.container_name)
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
        self._check_component(parent, context)
        extras = self.get_extra_params(parent)
        if extras:
            raise ValueError("ComponentConverter %s can't serialize extra params %s", (self, extras))
        for value in self.get_value_list(parent):
            output.append(self.meta.serialize_toplevel(value, context))
