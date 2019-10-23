import warnings
from collections import namedtuple
from typing import Any, Dict, Tuple

from ics.grammar.parse import Container
from .utils import get_lines
from .serializers.serializer import Serializer
from .parsers.parser import Parser

Extractor = namedtuple(
    'Extractor',
    ['function', 'type', 'required', 'multiple', 'default']
)


class Component(object):

    class Meta:
        name = "ABSTRACT"
        parser = Parser
        serializer = Serializer

    _classmethod_args: Tuple
    _classmethod_kwargs: Dict

    @classmethod
    def _from_container(cls, container: Container, *args: Any, **kwargs: Any):
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
                    raise ValueError(
                        'A {} must have at least one {}'
                        .format(container.name, line_name))

            if not options.multiple and len(lines) > 1:
                raise ValueError(
                    'A {} must have at most one {}'
                    .format(container.name, line_name))

            if options.multiple:
                parser(self, lines)  # Send a list or empty list
            else:
                if len(lines) == 1:
                    parser(self, lines[0])  # Send the element
                else:
                    parser(self, None)  # Send None

        self.extra = container  # Store unused lines

    def __str__(self) -> str:
        """Returns the component in an iCalendar format."""
        container = self.extra.clone()
        for output in self.Meta.serializer.get_serializers():
            output(self, container)
        return str(container)
