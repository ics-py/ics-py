from collections import defaultdict
from typing import (
    Any,
    Callable,
    ClassVar,
    Dict,
    Iterable,
    List,
    Optional,
    Tuple,
    Type,
    cast,
)

import attr
from attr import Attribute

from ics.component import Component
from ics.contentline import Container
from ics.converter.base import AttributeConverter, GenericConverter, sort_converters
from ics.types import ContainerItem, ContextDict
from ics.utils import check_is_instance


@attr.s(frozen=True)
class MemberComponentConverter(AttributeConverter):
    """
    An `AttributeConverter` that converts between a single attribute whose type is a subclass of `Component`
      and a `Container` of `ContentLines`, using the information stored in the `ComponentMeta` of the subclass.
    Uses `ComponentMeta.load_instance` and `ComponentMeta.serialize_toplevel` to inflate
      and serialize `Component` instances.
    Transparently handles single-value and multi-value attributes.
    See `GenericConverter` for more information.
    """

    meta: "ComponentMeta" = attr.ib()

    @property
    def filter_ics_names(self) -> List[str]:
        return [self.meta.component_type.NAME]

    def populate(
        self, component: Component, item: ContainerItem, context: ContextDict
    ) -> bool:
        assert isinstance(item, Container)
        self.set_or_append_value(component, self.meta.load_instance(item, context))
        return True

    def serialize(self, parent: Component, output: Container, context: ContextDict):
        extras = self.get_extra_params(parent)
        if extras:
            raise ValueError(
                "ComponentConverter %s can't serialize extra params %s", (self, extras)
            )
        for value in self.get_value_list(parent):
            # don't force self.meta for serialization, but use the meta registered for the concrete type of value
            output.append(value.to_container(context))


@attr.s(frozen=True)
class ComponentMeta:
    """
    Meta information on how a subclass of `Component`, the `component_type`, needs to be parsed and serialized.
    All needed information is generated upon instantiation of this class and cached for later use.
    Existing instances can be looked up `BY_TYPE`.
    """

    BY_TYPE: ClassVar[Dict[Type, "ComponentMeta"]] = {}

    component_type: Type[Component] = attr.ib()

    # Cached information for parsing and serialization.
    converters: Tuple[GenericConverter, ...]
    converter_lookup: Dict[str, Tuple[GenericConverter]]
    post_populate_hooks: Tuple[Callable]
    post_serialize_hooks: Tuple[Callable]

    def __attrs_post_init__(self):
        object.__setattr__(self, "converters", tuple(self.find_converters()))
        converter_lookup = defaultdict(list)
        post_populate_hooks = []
        post_serialize_hooks = []
        for converter in self.converters:
            for name in converter.filter_ics_names:
                converter_lookup[name].append(converter)
            # ignore the hooks if they're the still the base-class no-ops
            if GenericConverter.post_populate not in (
                converter.post_populate,
                getattr(converter.post_populate, "__func__", None),
            ):
                post_populate_hooks.append(converter.post_populate)
            if GenericConverter.post_serialize not in (
                converter.post_serialize,
                getattr(converter.post_serialize, "__func__", None),
            ):
                post_serialize_hooks.append(converter.post_serialize)
        object.__setattr__(
            self,
            "converter_lookup",
            {k: tuple(vs) for k, vs in converter_lookup.items()},
        )
        object.__setattr__(self, "post_populate_hooks", tuple(post_populate_hooks))
        object.__setattr__(self, "post_serialize_hooks", tuple(post_serialize_hooks))

    def find_converters(self) -> Iterable[GenericConverter]:
        """
        Get a sorted list of all converters needed for instances of `component_type`.
        Override this method to modify the auto-discovered list of converters.
        """
        return sort_converters(
            AttributeConverter.get_converter_for(a)
            for a in attr.fields(self.component_type)
        )

    def __call__(self, attribute: Attribute) -> AttributeConverter:
        """
        Create a `AttributeConverter` for an `attribute` of type `component_type`.
        """
        return MemberComponentConverter(attribute, self)

    def load_instance(
        self, container: Container, context: Optional[ContextDict] = None
    ):
        """
        Create and populate an instance of `component_type` from `container`.
        """
        instance = self.component_type()
        self.populate_instance(instance, container, context)
        return instance

    def populate_instance(
        self,
        instance: Component,
        container: Container,
        context: Optional[ContextDict] = None,
    ):
        if container.name != self.component_type.NAME:
            raise ValueError(
                f"container {container.name} is no {self.component_type.NAME}"
            )
        check_is_instance(
            "instance", instance, (self.component_type, MutablePseudoComponent)
        )
        if not context:
            context = ContextDict(defaultdict(lambda: None))

        self._populate_attrs(instance, container, context)

    def _populate_attrs(
        self, instance: Component, container: Container, context: ContextDict
    ):
        for line in container:
            consumed = False
            for conv in self.converter_lookup.get(line.name, []):
                if conv.populate(instance, line, context):
                    consumed = True
            if not consumed:
                instance.extra.append(line)

        for hook in self.post_populate_hooks:
            hook(instance, context)

    def serialize_toplevel(
        self, component: Component, context: Optional[ContextDict] = None
    ):
        check_is_instance("instance", component, self.component_type)
        if not context:
            context = ContextDict(defaultdict(lambda: None))
        container = Container(
            component.extra.name
        )  # allow overwriting the name by setting the name of the extras
        self._serialize_attrs(component, context, container)
        return container

    def _serialize_attrs(
        self, component: Component, context: ContextDict, container: Container
    ):
        for conv in self.converters:
            conv.serialize(component, container, context)
        container.extend(component.extra)
        for hook in self.post_serialize_hooks:
            hook(component, container, context)


class ImmutableComponentMeta(ComponentMeta):
    """
    `ComponentMeta` for sublasses of `Component` that are should be immutable, i.e. with `@attr.s(frozen=True)`.
    To still allows easily populating these classes, a `MutablePseudoComponent` is populated instead of an instance.
    The constructor of the instance is then called with all attribute values collected by the `MutablePseudoComponent`.
    """

    def load_instance(
        self, container: Container, context: Optional[ContextDict] = None
    ):
        mpcomp = MutablePseudoComponent(self.component_type)
        comp = cast(Component, mpcomp)
        self.populate_instance(comp, container, context)
        instance = self.component_type(
            **{
                k.lstrip("_"): v
                for k, v in mpcomp._MutablePseudoComponent__data.items()
            }
        )  # type: ignore[call-arg,attr-defined]
        instance.extra.extend(comp.extra)
        instance.extra_params.update(comp.extra_params)
        return instance


class MutablePseudoComponent:
    """
    A drop-in class that can be used for populating immutable `Component`s.
    Once all attributes are populated, the stored values can be used to create the instance in one go.
    Takes default values from the respective `Component` subclass.
    """

    def __init__(self, comp: Type[Component]):
        object.__setattr__(self, "NAME", comp.NAME)
        object.__setattr__(self, "extra", Container(comp.NAME))
        object.__setattr__(self, "extra_params", {})
        data = {}
        for field in attr.fields(comp):
            if not field.init:
                continue
            elif isinstance(field.default, attr.Factory):  # type: ignore[arg-type]
                assert field.default is not None
                if field.default.takes_self:
                    data[field.name] = field.default.factory(self)
                else:
                    data[field.name] = field.default.factory()
            elif field.default != attr.NOTHING:
                data[field.name] = field.default
        object.__setattr__(self, "_MutablePseudoComponent__data", data)

    def __getattr__(self, name: str) -> Any:
        return self._MutablePseudoComponent__data[name]

    def __setattr__(self, name: str, value: Any) -> None:
        assert name not in ("NAME", "extra", "extra_params")
        self._MutablePseudoComponent__data[name] = value

    def __delattr__(self, name: str) -> None:
        del self._MutablePseudoComponent__data[name]

    @staticmethod
    def from_container(*args, **kwargs):
        raise NotImplementedError()

    @staticmethod
    def populate(*args, **kwargs):
        raise NotImplementedError()

    @staticmethod
    def to_container(*args, **kwargs):
        raise NotImplementedError()

    @staticmethod
    def serialize(*args, **kwargs):
        raise NotImplementedError()

    @staticmethod
    def strip_extras(*args, **kwargs):
        raise NotImplementedError()

    @staticmethod
    def clone(*args, **kwargs):
        raise NotImplementedError()
