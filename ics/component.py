#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals, absolute_import

from six import PY2, PY3, StringIO, string_types, text_type, integer_types
from six.moves import filter, map, range

from collections import namedtuple

from .utils import get_lines


Extractor = namedtuple('Extractor', ['function', 'type', 'required', 'multiple'])


class Component(object):
    _TYPE = "ABSTRACT"

    @classmethod
    def _from_container(klass, container, *args, **kwargs):
        if klass._TYPE == "ABSTRACT":
            raise NotImplementedError('Abstract class, cannot instaciate')

        k = klass()
        k._classmethod_args = args
        k._classmethod_kwargs = kwargs
        k._populate(container)

        return k

    def _populate(self, container):
        if container.name != self._TYPE:
            raise ValueError("container isn't an {}".format(), self.TYPE)

        for extractor in self._EXTRACTORS:
            lines = get_lines(container, extractor.type)
            if not lines and extractor.required:
                raise ValueError('A {} must have at least one {}'.format(container.name, extractor.type))

            if not extractor.multiple and len(lines) > 1:
                raise ValueError('A {} must have at most one {}'.format(container.name, extractor.type))

            if extractor.multiple:
                extractor.function(self, lines) # Send a list or empty list
            else:
                if len(lines) == 1:
                    extractor.function(self, lines[0]) # Send the element
                else:
                    extractor.function(self, None) # Send None

        self._unused = container # Store unused lines

    @classmethod
    def _extracts(klass, line_type, required=False, multiple=False):
        def decorator(fn):
            extractor = Extractor(function=fn, type=line_type, required=required, multiple=multiple)
            klass._EXTRACTORS.append(extractor)
            return fn
        return decorator

    @classmethod
    def _outputs(klass, fn):
        klass._OUTPUTS.append(fn)
        return fn

    def __repr__(self):
        '''    - In python2: returns self.__unicode__() encoded into utf-8.
            - In python3: returns self.__unicode__()'''
        if hasattr(self, '__unicode__'):
            return self.__unicode__().encode('utf-8') if PY2 else self.__unicode__()
        else:
            super(Component, self).__repr__()

    def __str__(self):
        '''Returns the component in an iCalendar format.'''
        container = self._unused.clone()
        for output in self._OUTPUTS:
            output(self, container)
        return str(container)
