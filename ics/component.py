import warnings
from typing import Any, Dict, Tuple, Type, TypeVar

import attr
from attr.validators import instance_of

from ics.grammar.parse import Container
from ics.parsers.parser import Parser
from ics.serializers.serializer import Serializer
from ics.utils import get_lines

ComponentType = TypeVar('ComponentType', bound='Component')
PLACEHOLDER_CONTAINER = Container("PLACEHOLDER")


@attr.s
class Component(object):
    class Meta:
        name = "ABSTRACT"
        parser = Parser
        serializer = Serializer

    extra: Container = attr.ib(init=False, default=PLACEHOLDER_CONTAINER, validator=instance_of(Container), cmp=False)
    _classmethod_args: Tuple = attr.ib(init=False, default=None, repr=False, cmp=False, hash=False)
    _classmethod_kwargs: Dict = attr.ib(init=False, default=None, repr=False, cmp=False, hash=False)

    def __attrs_post_init__(self):
        if self.extra is PLACEHOLDER_CONTAINER:
            self.extra = Container(self.Meta.name)

    def __init_subclass__(cls):
        if cls.__str__ != Component.__str__:
            raise TypeError("%s may not overwrite %s" % (cls, Component.__str__))

    @classmethod
    def _from_container(cls: Type[ComponentType], container: Container, *args: Any, **kwargs: Any) -> ComponentType:
        k = cls()
        k._classmethod_args = args
        k._classmethod_kwargs = kwargs
        k._populate(container)
        return k

    def _populate(self, container: Container) -> None:
        if container.name != self.Meta.name:
            raise ValueError("container isn't an {}".format(self.Meta.name))

        for line_name, (parser, options) in self.Meta.parser.get_parsers().items():
            lines = get_lines(container, line_name)
            if not lines and options.required:
                if options.default:
                    lines = options.default
                    default_str = "\\n".join(map(str, options.default))
                    message = ("The %s property was not found and is required by the RFC." +
                               " A default value of \"%s\" has been used instead") % (line_name, default_str)
                    warnings.warn(message)
                else:
                    raise ValueError('A {} must have at least one {}'.format(container.name, line_name))

            if not options.multiple and len(lines) > 1:
                raise ValueError('A {} must have at most one {}'.format(container.name, line_name))

            if options.multiple:
                parser(self, lines)  # Send a list or empty list
            else:
                if len(lines) == 1:
                    parser(self, lines[0])  # Send the element
                else:
                    parser(self, None)  # Send None

        self.extra = container  # Store unused lines

    def clone(self):
        """
        Returns:
            Event: an exact copy of self"""
        return attr.evolve(self)

    def serialize(self) -> Container:
        container = self.extra.clone()
        for output in self.Meta.serializer.get_serializers():
            output(self, container)
        return container

    def __str__(self) -> str:
        """Returns the component in an iCalendar format."""
        return str(self.serialize())
