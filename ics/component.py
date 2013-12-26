#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals, absolute_import

from six import PY2, PY3, StringIO, string_types, text_type, integer_types
from six.moves import filter, map, range

from .parse import ParseError
from .utils import get_lines


class Component(object):
    _TYPE = "ABSTRACT"

    @classmethod
    def _from_container(klass, container, *args, **kwargs):
        k = klass()
        k._classmethod_args = args
        k._classmethod_kwargs = kwargs

        if k._TYPE == "ABSTRACT":
            raise NotImplementedError('Abstract clss')
        k._populate(container)
        return k

    def _populate(self, container):
        if container.name != self._TYPE:
            raise ParseError("container isn't an {}".format(), self.TYPE)

        for extractor, line_type, required, multiple in self._EXTRACTORS:
            lines = get_lines(container, line_type)
            if not lines and required:
                raise ParseError('A {} must have at least one {}'.format(container.name, line_type))

            if not multiple and len(lines) > 1:
                raise ParseError('A {} must have at most one {}'.format(container.name, line_type))

            if multiple:
                extractor(self, lines)
            else:
                if len(lines) == 1:
                    extractor(self, lines[0])
                else:
                    extractor(self, None)

        self._unused = container

    @classmethod
    def _extracts(klass, line_type, required=False, multiple=False):
        def decorator(fn):
            klass._EXTRACTORS.append((fn, line_type, required, multiple))
            return fn
        return decorator

    def __repr__(self):
        if PY2:
            return self.__unicode__().encode('utf-8')
        else:
            return self.__unicode__()
