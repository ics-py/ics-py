#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals, absolute_import
from typing import List, Dict, Tuple, Any, Callable, Optional, TypeVar
import warnings
from collections import namedtuple

from .utils import get_lines
from .parse import Container, ContentLine


Extractor = namedtuple(
    'Extractor',
    ['function', 'type', 'required', 'multiple', 'default']
)

# FIXME Any should be Self + Union[List[ContentLine], ContentLine]
ExtractorT = TypeVar('ExtractorT', bound=Callable[[Any, Any], None])
OutputT = TypeVar('OutputT', bound=Callable[[Any, Container], None]) # FIXME Any should be Self


class Component(object):
    _TYPE = "ABSTRACT"
    _EXTRACTORS: List[Extractor]
    _OUTPUTS: List[Callable]

    _classmethod_args: Tuple
    _classmethod_kwargs: Dict

    @classmethod
    def _from_container(cls, container: Container, *args: Any, **kwargs: Any) -> Component:
        if cls._TYPE == "ABSTRACT":
            raise NotImplementedError('Abstract class, cannot instantiate.')

        k = cls()
        k._classmethod_args = args
        k._classmethod_kwargs = kwargs
        k._populate(container)

        return k

    def _populate(self, container: Container) -> None:
        if container.name != self._TYPE:
            raise ValueError("container isn't an {}".format(self._TYPE))

        for extractor in self._EXTRACTORS:
            lines = get_lines(container, extractor.type)
            if not lines and extractor.required:
                if extractor.default:
                    lines = extractor.default
                    default_str = "\\n".join(map(str, extractor.default))
                    message = ("The %s property was not found and is required by the RFC." +
                        " A default value of \"%s\" has been used instead") % (extractor.type, default_str)
                    warnings.warn(message)
                else:
                    raise ValueError(
                        'A {} must have at least one {}'
                        .format(container.name, extractor.type))

            if not extractor.multiple and len(lines) > 1:
                raise ValueError(
                    'A {} must have at most one {}'
                    .format(container.name, extractor.type))

            if extractor.multiple:
                extractor.function(self, lines)  # Send a list or empty list
            else:
                if len(lines) == 1:
                    extractor.function(self, lines[0])  # Send the element
                else:
                    extractor.function(self, None)  # Send None

        self._unused = container  # Store unused lines

    @classmethod
    def _extracts(
        cls, line_type: str, required: bool = False,
        multiple: bool = False, default: Optional[List[ContentLine]] = None
    ) -> Callable[[ExtractorT], ExtractorT]:
        def decorator(fn):
            extractor = Extractor(
                function=fn,
                type=line_type,
                required=required,
                multiple=multiple,
                default=default)
            cls._EXTRACTORS.append(extractor)
            return fn
        return decorator

    @classmethod
    def _outputs(cls, fn: OutputT) -> OutputT:
        cls._OUTPUTS.append(fn)
        return fn

    def __str__(self) -> str:
        """Returns the component in an iCalendar format."""
        container = self._unused.clone()
        for output in self._OUTPUTS:
            output(self, container)
        return str(container)
