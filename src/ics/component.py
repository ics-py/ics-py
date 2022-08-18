from typing import ClassVar, Dict, List, Optional, Type, TypeVar, Union

import attr
from attr.validators import instance_of

from ics.contentline import Container
from ics.types import ContextDict, ExtraParams, RuntimeAttrValidation

ComponentType = TypeVar("ComponentType", bound="Component")
ComponentExtraParams = Dict[str, Union[ExtraParams, List[ExtraParams]]]


@attr.s
class Component(RuntimeAttrValidation):
    NAME: ClassVar[str] = "ABSTRACT-COMPONENT"
    SUBTYPES: ClassVar[List[Type["Component"]]] = []

    extra: Container = attr.ib(
        init=False, validator=instance_of(Container), metadata={"ics_ignore": True}
    )
    extra_params: ComponentExtraParams = attr.ib(
        init=False,
        factory=dict,
        validator=instance_of(dict),
        metadata={"ics_ignore": True},
    )

    def __attrs_post_init__(self):
        super().__attrs_post_init__()
        object.__setattr__(self, "extra", Container(self.NAME))

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        Component.SUBTYPES.append(cls)

    @classmethod
    def from_container(
        cls: Type[ComponentType],
        container: Container,
        context: Optional[ContextDict] = None,
    ) -> ComponentType:
        from ics import initialize_converters

        initialize_converters()
        from ics.converter.component import ComponentMeta

        return ComponentMeta.BY_TYPE[cls].load_instance(container, context)

    def populate(self, container: Container, context: Optional[ContextDict] = None):
        from ics import initialize_converters

        initialize_converters()
        from ics.converter.component import ComponentMeta

        ComponentMeta.BY_TYPE[type(self)].populate_instance(self, container, context)

    def to_container(self, context: Optional[ContextDict] = None) -> Container:
        from ics import initialize_converters

        initialize_converters()
        from ics.converter.component import ComponentMeta

        return ComponentMeta.BY_TYPE[type(self)].serialize_toplevel(self, context)

    def serialize(self, context: Optional[ContextDict] = None) -> str:
        """Creates a serialized string fit for file write."""

        return self.to_container(context).serialize()

    def strip_extras(
        self,
        all_extras=False,
        extra_properties=None,
        extra_params=None,
        property_merging=None,
    ):
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
                if not isinstance(val, list):
                    continue
                for v in val:
                    v.pop("__merge_next", None)

    def clone(self):
        """Returns an exact (shallow) copy of self"""
        # TODO deep copies?
        return attr.evolve(self)
