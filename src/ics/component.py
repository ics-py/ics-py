from typing import ClassVar, Dict, List, Type, TypeVar, Union

import attr
from attr.validators import instance_of

from ics.converter.component import ComponentMeta
from ics.grammar import Container
from ics.types import ExtraParams, RuntimeAttrValidation

PLACEHOLDER_CONTAINER = Container("PLACEHOLDER")
ComponentType = TypeVar('ComponentType', bound='Component')
ComponentExtraParams = Dict[str, Union[ExtraParams, List[ExtraParams]]]


@attr.s
class Component(RuntimeAttrValidation):
    Meta: ClassVar[ComponentMeta] = ComponentMeta("ABSTRACT-COMPONENT")

    extra: Container = attr.ib(init=False, default=PLACEHOLDER_CONTAINER, validator=instance_of(Container), metadata={"ics_ignore": True})
    extra_params: ComponentExtraParams = attr.ib(init=False, factory=dict, validator=instance_of(dict), metadata={"ics_ignore": True})

    def __attrs_post_init__(self):
        super(Component, self).__attrs_post_init__()
        if self.extra is PLACEHOLDER_CONTAINER:
            self.extra = Container(self.Meta.container_name)

    def __init_subclass__(cls):
        super().__init_subclass__()
        cls.Meta.inflate(cls)

    @classmethod
    def from_container(cls: Type[ComponentType], container: Container) -> ComponentType:
        return cls.Meta.load_instance(container)

    def populate(self, container: Container):
        self.Meta.populate_instance(self, container)

    def to_container(self) -> Container:
        return self.Meta.serialize_toplevel(self)

    def serialize(self) -> str:
        return self.to_container().serialize()

    def strip_extras(self, all_extras=False, extra_properties=None, extra_params=None, property_merging=None):
        if extra_properties is None:
            extra_properties = all_extras
        if extra_params is None:
            extra_params = all_extras
        if property_merging is None:
            property_merging = all_extras
        if not any([extra_properties, extra_params, property_merging]):
            raise ValueError("need to strip at least one thing")
        if extra_properties:
            self.extra.clear()
        if extra_params:
            self.extra_params.clear()
        elif property_merging:
            for val in self.extra_params.values():
                if not isinstance(val, list): continue
                for v in val:
                    v.pop("__merge_next", None)

    def clone(self):
        """Returns an exact (shallow) copy of self"""
        # TODO deep copies?
        return attr.evolve(self)
