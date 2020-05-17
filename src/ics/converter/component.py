from collections import defaultdict
from typing import Dict, Iterable, List, Optional, TYPE_CHECKING, Tuple, Type, cast

import attr
from attr import Attribute

from ics.converter.base import AttributeConverter, GenericConverter
from ics.contentline import Container
from ics.types import ContainerItem, ContextDict
from ics.utils import check_is_instance

if TYPE_CHECKING:
    from ics.component import Component


@attr.s(frozen=True)
class MemberComponentConverter(AttributeConverter):
    meta: "ComponentMeta" = attr.ib()

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


EMPTY_CONVERTERS = tuple()


@attr.s(frozen=True)
class ComponentMeta(object):
    container_name: str = attr.ib()
    component_type: Type["Component"] = attr.ib()

    converter_class: Type[MemberComponentConverter] = attr.ib(default=MemberComponentConverter)
    converters: Tuple[GenericConverter, ...] = attr.ib(default=EMPTY_CONVERTERS)

    converter_lookup: Dict[str, List[GenericConverter]]

    def __attrs_post_init__(self):
        if self.converters is EMPTY_CONVERTERS:
            converters = cast(Iterable["AttributeConverter"], filter(bool, (
                AttributeConverter.get_converter_for(a) for a in attr.fields(self.component_type))))
        else:
            converters = self.converters
        object.__setattr__(self, "converters", tuple(sorted(converters, key=lambda c: c.priority)))

        object.__setattr__(self, "converter_lookup", defaultdict(list))
        for converter in self.converters:
            for name in converter.filter_ics_names:
                self.converter_lookup[name].append(converter)

        self.component_type.Meta = self
        AttributeConverter.BY_TYPE[self.component_type] = self

    def __call__(self, attribute: Attribute):
        converter_class = self.converter_class or MemberComponentConverter
        return converter_class(attribute, self)

    def load_instance(self, container: Container, context: Optional[ContextDict] = None):
        instance = self.component_type()
        self.populate_instance(instance, container, context)
        return instance

    def populate_instance(self, instance: "Component", container: Container, context: Optional[ContextDict] = None):
        if container.name != self.container_name:
            raise ValueError("container isn't an {}".format(self.container_name))
        check_is_instance("instance", instance, self.component_type)
        if not context:
            context = ContextDict(defaultdict(lambda: None))

        self._populate_attrs(instance, container, context)

    def _populate_attrs(self, instance: "Component", container: Container, context: ContextDict):
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
        check_is_instance("instance", component, self.component_type)
        if not context:
            context = ContextDict(defaultdict(lambda: None))
        container = Container(self.container_name)
        self._serialize_attrs(component, context, container)
        return container

    def _serialize_attrs(self, component: "Component", context: ContextDict, container: Container):
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
