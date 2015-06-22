#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals, absolute_import

from six import PY2

from collections import defaultdict
import itertools

from .parse import ContentLine, Container
from .property import property_description


class Component(object):
    _TYPE = "ABSTRACT"
    _known_components = ()

    def __init__(self):
        self._properties = {}
        self._components = defaultdict(list)
        self.parent = None

    @classmethod
    def _from_container(cls, container, *args, **kwargs):
        if cls._TYPE == "ABSTRACT":
            raise NotImplementedError('Abstract class, cannot instantiate.')

        k = cls()
        k.parent = kwargs.get('parent')
        k._populate(container)

        return k

    def _populate(self, container):
        """ Build the component from the container
        """
        if container.name != self._TYPE:
            raise ValueError("container isn't an {}".format(self._TYPE))

        for e in container:
            if isinstance(e, ContentLine):
                self._add_property(e)
            else:
                self._add_component(e)
        self._build_components()

    def _build_components(self):
        """ Build the dependant components
        """
        for name, component, attribute in self._known_components:
            for container in self._components[name]:
                comp = component._from_container(container, parent=self)
                getattr(self, attribute).append(comp)

    def _add_property(self, line):
        if property_description(self._TYPE, line.name).multiple:
            if line.name in self._properties:
                self._properties[line.name].append(line)
            else:
                self._properties[line.name] = [line]
        else:
            if line.name in self._properties:
                raise AttributeError('{} must only occur once in a {}'.format(
                    line.name, self._TYPE))
            self._properties[line.name] = line
            self._properties[line.name].single = True

    def _add_component(self, container):
        self._components[container.name].append(container)

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

    def get_container(self):
        container = Container(self._TYPE)
        for name, value in self._properties.items():
            if property_description(self._TYPE, name).multiple:
                container.extend(value)
            else:
                container.append(value)
        for components in self._components.values():
            container.extend(components)
        return container

    def __str__(self):
        """Returns the component in an iCalendar format."""
        return str(self.get_container())

    def get_timezones(self):
        if self.parent:
            return self.parent.get_timezones()
        return {}
