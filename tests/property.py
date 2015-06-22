import unittest

from ics.property import (property_description, ICalProperty)
from ics.parse import ContentLine

class TestPropertyDescription(unittest.TestCase):

    def test_property_description(self):
        data = [
            ('standard',
             'VEVENT', 'DESCRIPTION',
             ICalProperty, False, False
             ),
            ('required',
             'VCALENDAR', 'PRODID',
             ICalProperty, True, False
             ),
            ('multiple',
             'VEVENT', 'ATTENDEE',
             ICalProperty, False, True
             ),
            ('non-existent property',
             'VEVENT', 'NONEXISTENT',
             ICalProperty, False, True
             ),
            ('non-existent component',
             'NONEXISTENT', 'DESCRIPTION',
             ICalProperty, False, True
             ),
        ]
        for (description,
             component, prop,
             ptype, required, multiple) in data:
            desc = property_description(component, prop)
            self.assertEqual(desc.type, ptype,
                             description+": type is {}".format(repr(desc.type)))
            self.assertEqual(desc.required, required, description)
            self.assertEqual(desc.multiple, multiple, description)


class TestICalProperty(unittest.TestCase):

    def test_without_data(self):

        class Component(object):
            _properties = {}
            prop = ICalProperty('PROP')

        c = Component()
        self.assertEqual(c.prop, None)
        c.prop = 'Test'
        self.assertEqual(c._properties,
                         {'PROP': ContentLine('PROP', value='Test')})
        self.assertEqual(c.prop, 'Test')

        # this way the properties can be set on the component classes
        Component.test = ICalProperty('TEST')
        self.assertEqual(c.test, None)
        c.test = 'Test2'
        self.assertEqual(c._properties['TEST'],
                         ContentLine('TEST', value='Test2'))
        self.assertEqual(c.test, 'Test2')

    def test_with_data(self):

        class Component(object):
            _properties = {'PROP': ContentLine('PROP', value='Test')}
            prop = ICalProperty('PROP')

        c = Component()
        self.assertEqual(c.prop, 'Test')
        c.prop = 'Different'
        self.assertEqual(c._properties,
                         {'PROP': ContentLine('PROP', value='Different')})
        self.assertEqual(c.prop, 'Different')

    def test_validation(self):

        class Component(object):
            _properties = {'PROP': ContentLine('PROP', value='Test')}
            prop = ICalProperty('PROP', 'validate_prop')

            def validate_prop(self, value):
                if value == 'one':
                    return 'two'
                else:
                    return 'three'

        c = Component()
        self.assertEqual(c.prop, 'Test')
        c.prop = 'one'
        self.assertEqual(c._properties,
                         {'PROP': ContentLine('PROP', value='two')})
        self.assertEqual(c.prop, 'two')
        c.prop = 'four'
        self.assertEqual(c._properties,
                         {'PROP': ContentLine('PROP', value='three')})
        self.assertEqual(c.prop, 'three')

