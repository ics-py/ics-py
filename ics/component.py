#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals, absolute_import

from six import PY2, PY3, StringIO, string_types, text_type, integer_types
from six.moves import filter, map, range

from collections import namedtuple

from .utils import get_lines


Extractor = namedtuple(
    'Extractor',
    ['function', 'type', 'required', 'multiple']
)


class Component(object):
    _TYPE = "ABSTRACT"

    @classmethod
    def _from_container(cls, container, *args, **kwargs):
        if cls._TYPE == "ABSTRACT":
            raise NotImplementedError('Abstract class, cannot instantiate.')

        k = cls()
        k._classmethod_args = args
        k._classmethod_kwargs = kwargs
        k._populate(container)

        return k

    def _populate(self, container):
        if container.name != self._TYPE:
            raise ValueError("container isn't an {}".format(self._TYPE))

        for extractor in self._EXTRACTORS:
            lines = get_lines(container, extractor.type)
            if not lines and extractor.required:
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
    def _extracts(cls, line_type, required=False, multiple=False):
        def decorator(fn):
            extractor = Extractor(
                function=fn,
                type=line_type,
                required=required,
                multiple=multiple)
            cls._EXTRACTORS.append(extractor)
            return fn
        return decorator

    @classmethod
    def _outputs(cls, fn):
        cls._OUTPUTS.append(fn)
        return fn

    def __repr__(self):
        """ - In python2: returns self.__urepr__() encoded into utf-8.
            - In python3: returns self.__urepr__()
        """
        if hasattr(self, '__urepr__'):
            return self.__urepr__().encode('utf-8') if PY2 else self.__urepr__()
        else:
            t = self.__class__.__name__
            adress = hex(id(self))
            return '<{} at {}>'.format(t, adress)

    def __str__(self):
        """Returns the component in an iCalendar format."""
        container = self._unused.clone()
        for output in self._OUTPUTS:
            output(self, container)
        return str(container)
