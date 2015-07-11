import unittest
from datetime import date, datetime, timedelta, tzinfo
from dateutil.tz import tzutc
from ics.property import (property_description, ICalProperty, TextProperty,
                          DateTimeProperty, DateTimeOrDateProperty,
                          TriggerProperty)
from ics.parse import ContentLine
from ics.component import Component

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

        class ICalComponent(Component):
            prop = ICalProperty('PROP')

        c = ICalComponent()
        self.assertEqual(c.prop, None)
        c.prop = 'Test'
        self.assertEqual(c._properties,
                         {'PROP': ContentLine('PROP', value='Test')})
        self.assertEqual(c.prop, 'Test')

        # to add a property, it must be set on the component class,
        # not on the instance
        ICalComponent.test = ICalProperty('TEST')
        self.assertEqual(c.test, None)
        c.test = 'Test2'
        self.assertEqual(c._properties['TEST'],
                         ContentLine('TEST', value='Test2'))
        self.assertEqual(c.test, 'Test2')

    def test_with_data(self):

        class ICalComponent(Component):
            prop = ICalProperty('PROP')

        c = ICalComponent()
        c._properties = {'PROP': ContentLine('PROP', value='Test')}
        self.assertEqual(c.prop, 'Test')
        c.prop = 'Different'
        self.assertEqual(c._properties,
                         {'PROP': ContentLine('PROP', value='Different')})
        self.assertEqual(c.prop, 'Different')

    def test_validation(self):

        class ICalComponent(Component):
            prop = ICalProperty('PROP', 'validate_prop')

            def validate_prop(self, value):
                if value == 'one':
                    return 'two'
                else:
                    return 'three'

        c = ICalComponent()
        c._properties = {'PROP': ContentLine('PROP', value='Test')}
        self.assertEqual(c.prop, 'Test')
        c.prop = 'one'
        self.assertEqual(c._properties,
                         {'PROP': ContentLine('PROP', value='two')})
        self.assertEqual(c.prop, 'two')
        c.prop = 'four'
        self.assertEqual(c._properties,
                         {'PROP': ContentLine('PROP', value='three')})
        self.assertEqual(c.prop, 'three')

    def test_default(self):

        def default_function4():
            return 'default-prop4'

        class DefaultComponent(Component):
            prop1 = ICalProperty('PROP1', default='default-prop1')
            prop2 = ICalProperty('PROP2', default='default-prop2')
            prop3 = ICalProperty('PROP3', default='default_method3')
            prop4 = ICalProperty('PROP4', default=default_function4)

            def default_method3(self, property_name):
                return 'default-prop3'

        c = DefaultComponent()
        c._properties = {'PROP1': ContentLine('PROP1', value='Test')}
        self.assertEqual(c.prop1, 'Test')
        self.assertEqual(c.prop2, 'default-prop2')
        self.assertEqual(c.prop3, 'default-prop3')
        self.assertEqual(c.prop4, 'default-prop4')


class TestTextProperty(unittest.TestCase):

    def test_text(self):

        class TextComponent(Component):
            prop = TextProperty('PROP')

        ical_text = 'comma\\, semicolon\\; backslash\\\\ newlines\\N\\n'
        plain_text = 'comma, semicolon; backslash\\ newlines\n\n'
        c = TextComponent()
        c.prop = plain_text
        self.assertEqual(c._properties,
                         {'PROP': ContentLine('PROP', value=ical_text.lower())})
        self.assertEqual(c.prop, plain_text)
        c._properties['PROP'].value = ical_text
        self.assertEqual(c.prop, plain_text)


class TimezoneNewYork(tzinfo):
    def utcoffset(self, dt):
        return timedelta(hours=-5)
    def dst(self, dt):
        return timedelta(0)
    def tzname(self, dt):
        return 'America/New_York'
new_york = TimezoneNewYork()


class TestDateTimeProperty(unittest.TestCase):

    class DTComponent(Component):
        prop = DateTimeProperty('PROP')

        def get_timezones(self):
            return {'America/New_York': new_york}

    def test_naive_datetime(self):
        c = self.DTComponent()
        c.prop = datetime(2015, 7, 1, 6)
        self.assertEqual(c._properties,
                         {'PROP': ContentLine('PROP', value='20150701T060000')})
        self.assertEqual(c.prop, datetime(2015, 7, 1, 6))

    def test_utc_datetime(self):
        c = self.DTComponent()
        c.prop = datetime(2015, 7, 1, 6, tzinfo=tzutc())
        self.assertEqual(c._properties,
                         {'PROP': ContentLine('PROP', value='20150701T060000Z')})
        self.assertEqual(c.prop, datetime(2015, 7, 1, 6, tzinfo=tzutc()))

    def test_datetime_with_timezone(self):
        c = self.DTComponent()
        c._properties['PROP'] = ContentLine.parse(
            'PROP;TZID=America/New_York:20150701T060000')
        self.assertEqual(c.prop,
                         datetime(2015, 7, 1, 6, tzinfo=new_york))


class TestDateTimeOrDateProperty(unittest.TestCase):

    class DTComponent(Component):
        prop = DateTimeOrDateProperty('PROP')
        def get_timezones(self):
            return {'America/New_York': new_york}

    def test_naive_datetime(self):
        c = self.DTComponent()
        c.prop = datetime(2015, 7, 1, 6)
        self.assertEqual(c._properties,
                         {'PROP': ContentLine('PROP', value='20150701T060000')})
        self.assertEqual(c.prop, datetime(2015, 7, 1, 6))

    def test_utc_datetime(self):
        c = self.DTComponent()
        c.prop = datetime(2015, 7, 1, 6, tzinfo=tzutc())
        self.assertEqual(c._properties,
                         {'PROP': ContentLine('PROP', value='20150701T060000Z')})
        self.assertEqual(c.prop, datetime(2015, 7, 1, 6, tzinfo=tzutc()))

    def test_datetime_with_timezone1(self):
        c = self.DTComponent()
        c._properties['PROP'] = ContentLine.parse(
            'PROP;TZID=America/New_York:20150701T060000')
        self.assertEqual(c.prop,
                         datetime(2015, 7, 1, 6, tzinfo=new_york))

    def test_datetime_with_timezone2(self):
        c = self.DTComponent()
        c.prop = datetime(2015, 7, 1, 6, tzinfo=new_york)
        self.assertEqual(c._properties,
                         {'PROP': ContentLine.parse('PROP;TZID=America/New_York:20150701T060000')})

    def test_date(self):
        c = self.DTComponent()
        c.prop = date(2015, 7, 1)
        prop = c._properties['PROP']
        self.assertEqual(prop.name, 'PROP')
        self.assertEqual(prop.value, '20150701')
        self.assertEqual(prop.params, {'VALUE': 'DATE'})
        self.assertEqual(c.prop, date(2015, 7, 1))
