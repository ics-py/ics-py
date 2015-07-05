# -*- coding: utf-8 -*-
""" Properties of iCalendar objects as descriptors

In this module we use this naming convention:
A *component* is one of the primary elements of a calendar like
VCALENDAR, VEVENT or VALARM.
A *property* describes the component; depending on the type of
the component different properties are defined.
A property can have additional *parameters*.

The properties are implemented as descriptors for the components.
The values of the properties are stored in a dict on the
component.

TODO: handle multiple values
"""
import six
from datetime import datetime, date, timedelta
from collections import namedtuple

from .utils import (datetime_to_iso, parse_duration,
                    timedelta_to_duration, parse_date,
                    get_date_or_datetime, parse_cal_date, parse_cal_datetime)
from .parse import ContentLine


ICAL_PROPERTIES = {
    'VCALENDAR': {
        'properties': {
            'PRODID':   {'required': True, },
            'VERSION':  {'required': True, },
            'CALSCALE': {},
            'METHOD':   {},
        },
        'components': [
            'VEVENT',
            'VTODO',
            'VJOURNAL',
            'VFREEBUSY',
            'VTIMEZONE',
        ]
    },
    'VEVENT': {
        'properties': {
            'DTSTAMP':     {'required': True, },
            'UID':         {'required': True, },
            'DTSTART':     {},
            'CLASS':       {},
            'CREATED':     {},
            'DESCRIPTION': {},
            'GEO':         {},
            'LAST-MOD':    {},
            'LOCATION':    {},
            'ORGANIZER':   {},
            'PRIORITY':    {},
            'SEQ':         {},
            'STATUS':      {},
            'SUMMARY':     {},
            'TRANSP':      {},
            'URL':         {},
            'RECURID':     {},
            'DTEND':       {},
            'DURATION':    {},
            'RRULE':       {'multiple': True, },
            'ATTACH':      {'multiple': True, },
            'ATTENDEE':    {'multiple': True, },
            'CATEGORIES':  {'multiple': True, },
            'COMMENT':     {'multiple': True, },
            'CONTACT':     {'multiple': True, },
            'EXDATE':      {'multiple': True, },
            'RSTATUS':     {'multiple': True, },
            'RELATED':     {'multiple': True, },
            'RESOURCES':   {'multiple': True, },
            'RDATE':       {'multiple': True, },
        },
        'components': [
            'VALARM',
        ],
        'rules': [
            "There has to be a 'dtstart' in the event or a 'method' in the calendar",
            "Either 'dtend' or 'duration' may appear in a event",
            "RRULE  SHOULD NOT occur more than once",
        ]
    },
    'VTODO': {
        'properties': {
            "DTSTAMP":     {'required': True, },
            "UID":         {'required': True, },
            "CLASS":       {},
            "COMPLETED":   {},
            "CREATED":     {},
            "DESCRIPTION": {},
            "DTSTART":     {},
            "GEO":         {},
            "LAST-MOD":    {},
            "LOCATION":    {},
            "ORGANIZER":   {},
            "PERCENT":     {},
            "PRIORITY":    {},
            "RECURID":     {},
            "SEQ":         {},
            "STATUS":      {},
            "SUMMARY":     {},
            "URL":         {},
            "DUE":         {},
            "DURATION":    {},
            "RRULE":       {'multiple': True, },
            "ATTACH":      {'multiple': True, },
            "ATTENDEE":    {'multiple': True, },
            "CATEGORIES":  {'multiple': True, },
            "COMMENT":     {'multiple': True, },
            "CONTACT":     {'multiple': True, },
            "EXDATE":      {'multiple': True, },
            "RSTATUS":     {'multiple': True, },
            "RELATED":     {'multiple': True, },
            "RESOURCES":   {'multiple': True, },
            "RDATE":       {'multiple': True, },
        },
        'components': [
            "VALARM",
        ],
        'rules': [
            "RRULE  SHOULD NOT occur more than once",
            "Either 'due' or 'duration' MAY appear in a 'todoprop', but 'due' and 'duration' MUST NOT occur in the same 'todoprop'.",
            "If 'duration' appear in a 'todoprop', then 'dtstart' MUST also appear in the same 'todoprop'.",
        ],
    },
    'VJOURNAL': {
        'properties': {
            "DTSTAMP":     {'required': True, },
            "UID":         {'required': True, },
            "CLASS":       {},
            "CREATED":     {},
            "DTSTART":     {},
            "LAST-MOD":    {},
            "ORGANIZER":   {},
            "RECURID":     {},
            "SEQ":         {},
            "STATUS":      {},
            "SUMMARY":     {},
            "URL":         {},
            "RRULE":       {'multiple': True, },
            "ATTACH":      {'multiple': True, },
            "ATTENDEE":    {'multiple': True, },
            "CATEGORIES":  {'multiple': True, },
            "COMMENT":     {'multiple': True, },
            "CONTACT":     {'multiple': True, },
            "DESCRIPTION": {'multiple': True, },
            "EXDATE":      {'multiple': True, },
            "RELATED":     {'multiple': True, },
            "RDATE":       {'multiple': True, },
            "RSTATUS":     {'multiple': True, },
        },
        'components': [
        ],
        'rules': [
            "RRULE  SHOULD NOT occur more than once",
        ],
    },
    'VFREEBUSY': {
        'properties': {
            "DTSTAMP":   {'required': True, },
            "UID":       {'required': True, },
            "CONTACT":   {},
            "DTSTART":   {},
            "DTEND":     {},
            "ORGANIZER": {},
            "URL":       {},
            "ATTENDEE":  {'multiple': True, },
            "COMMENT":   {'multiple': True, },
            "FREEBUSY":  {'multiple': True, },
            "RSTATUS":   {'multiple': True, },
        },
        'components': [
        ],
        'rules': [
        ],
    },
    'VTIMEZONE': {
        'properties': {
            "TZID":     {'required': True, },
            "LAST-MOD": {},
            "TZURL":    {},
        },
        'components': [
            'STANDARD',
            'DAYLIGHT',
        ],
        'rules': [
            "One of 'STANDARD' or 'DAYLIGHT' MUST occur and each MAY occur more than once.",
        ],
    },
    'STANDARD': {
        'properties': {
            "DTSTART":      {'required': True, },
            "TZOFFSETTO":   {'required': True, },
            "TZOFFSETFROM": {'required': True, },
            "RRULE":        {'multiple': True, },
            "COMMENT":      {'multiple': True, },
            "RDATE":        {'multiple': True, },
            "TZNAME":       {'multiple': True, },
        },
        'rules': [
            "RRULE  SHOULD NOT occur more than once",
        ],
    },
    'DAYLIGHT': {
        'properties': {
            "DTSTART":      {'required': True, },
            "TZOFFSETTO":   {'required': True, },
            "TZOFFSETFROM": {'required': True, },
            "RRULE":        {'multiple': True, },
            "COMMENT":      {'multiple': True, },
            "RDATE":        {'multiple': True, },
            "TZNAME":       {'multiple': True, },
        },
        'rules': [
            "RRULE  SHOULD NOT occur more than once",
        ],
    },
    'VALARM': {
        'properties': {
            "ACTION":      {'required': True, },
            "TRIGGER":     {'required': True, },
            "DURATION":    {},
            "REPEAT":      {},
            "DESCRIPTION": {},
            "SUMMARY":     {},
            "ATTENDEE":    {'multiple': True, },
            "ATTACH":      {'multiple': True, },
        },
        'components': [
        ],
        'rules': [
            "Depending on 'action', 'description', 'summary', 'attendee' and 'attach' may be required",
            "'duration' and 'repeat' are both OPTIONAL, and MUST NOT occur more than once each; but if one occurs, so MUST the other."
        ],
    },
}

PropertyDesc = namedtuple(
    'PropertyDesc',
    ['type', 'required', 'multiple']
)

# If MEMOIZE_DATA is True,
# setting properties memoizes their python value.
# Is False for development/debugging purposes.
MEMOIZE_DATA = False


def property_description(component, line):
    """ Return a description of the property of this component

    Defaults to PropertyDesc(type=ICalProperty, required=False,
        multiple=False)
    For unknown components or properties 'multiple' is True
    """
    comp_def = ICAL_PROPERTIES.get(component, {'properties': {}})
    definition = comp_def['properties'].get(line, {'multiple': True})
    return PropertyDesc(
        type=definition.get('type', ICalProperty),
        required=definition.get('required', False),
        multiple=definition.get('multiple', False))


class ICalProperty(object):
    """ Property for an ical object implemented as descriptor
    """
    def __init__(self, ical_name,
                 validation=None,
                 default=None,
                 create_on_access=False):
        """ Initialize the property

        Args:
            ical_name (string): the name of this property in the rfc 5545
            validation (string): name of a method of the instance used to
                validate (and process) the input.
                The method must return the validated value.
            default (value of appropriate type
                     or method name of the instance
                     or function not expecting parameters):
                to be used when the property is accessed but not defined.
                The expected interface of the method is like this:
                `def default(self, property_name):`
                where `property_name` is the ical_name of the property.
                It should return a python value of the appropriate type.
                The method or function is called for every access to the
                property as long as it is not set.
            create_on_access: if there is no value for the property
                when it is accessed, set the result of `default`

        `required` and `multiple` are ignored when `parent_type` is given
        """
        self.ical_name = ical_name
        self.validation = validation
        self.default = default
        self.create_on_access = create_on_access
        self.memoized = False

    def __get__(self, instance, owner):
        if MEMOIZE_DATA and self.memoized:
            return self.memo
        if self.ical_name in instance._properties:
            line = instance._properties[self.ical_name]
            return self._memoize(self.to_python(line, instance))
        default = self._get_default(instance)
        if self.create_on_access:
            self.__set__(instance, default)
        return default

    def _get_default(self, instance):
        if self.default:
            if callable(self.default):
                return self.default()
            if (isinstance(self.default, six.string_types) and
                    callable(getattr(instance, self.default, None))):
                return getattr(instance, self.default)(self.ical_name)
            return self.default
        return None

    def __set__(self, instance, value):
        """ Set the value of the property

        Before the value is set, the validation method of the instance is
        called. This method can change the value and should raise an
        exception, if the value doesn't fit.

        Args:
            value: the new value of the property.
            This can be a string or a tuple in the form of (value, params).
        """
        if self.validation:
            value = getattr(instance, self.validation)(value)
        if value is None:
            if self.ical_name in instance._properties:
                # Setting a property to None is deleting it
                self.__delete__(instance)
        else:
            self._memoize(value)
            p_value = self.from_python(value)
            instance._properties[self.ical_name] = p_value

    def __delete__(self, instance):
        if self.required(instance):
            raise TypeError("{} is required for {}".format(
                            self.ical_name, instance._TYPE))
        del instance._properties[self.ical_name]
        self._memoize(None)

    def from_python(self, value, params={}):
        """ Translate a python data type to the format of iCalendar
        """
        return ContentLine(self.ical_name, value=value, params=params)

    def to_python(self, line, instance):
        """ Translate the format of an iCalendar property to a python value
        """
        return line.value

    def required(self, instance):
        """ Return True if this property is required for this instance
        """
        return property_description(instance._TYPE, self.ical_name).required

    def multiple(self, instance):
        """ Return True if this property can occur multiple times in this instance
        """
        return property_description(instance._TYPE, self.ical_name).multiple

    def _memoize(self, value):
        if MEMOIZE_DATA:
            self.memoized = True
            self.memo = value
        return value


class TextProperty(ICalProperty):
    """ ICalProperty with 'TEXT' value type
    """
    def from_python(self, value, params={}):
        value = six.text_type(value)
        if value:
            value = value.replace("\\", "\\\\")
            value = value.replace(";", "\\;")
            value = value.replace(",", "\\,")
            value = value.replace("\n", "\\n")
        return ContentLine(self.ical_name, value=value, params=params)

    def to_python(self, line, instance):
        if not line:
            return None
        value = line.value
        if value:
            value = value.replace("\\;", ";")
            value = value.replace("\\,", ",")
            value = value.replace("\\n", "\n")
            value = value.replace("\\N", "\n")
            value = value.replace("\\\\", "\\")
        return value


class DateTimeProperty(ICalProperty):
    """ ICalProperty with 'DATE-TIME' value type
    """
    def from_python(self, value, params={}):
        return ContentLine(self.ical_name, value=datetime_to_iso(value),
                           params=params)

    def to_python(self, line, instance):
        return parse_cal_datetime(line, instance.get_timezones())


class DateTimeOrDateProperty(ICalProperty):
    """ ICalProperty with 'DATE-TIME' or 'DATE' value type
    """
    def __set__(self, instance, value):
        value = get_date_or_datetime(value)
        if self.validation:
            value = getattr(instance, self.validation)(value)
        if value is None:
            if self.ical_name in instance._properties:
                # Setting a property to None means deleting it
                self.__delete__(instance)
        else:
            p_value = self.from_python(value)
            instance._properties[self.ical_name] = p_value

    def from_python(self, value, params={}):
        params = params or {}
        if isinstance(value, date) and not isinstance(value, datetime):
            params['VALUE'] = 'DATE'
            s_value = value.strftime('%Y%m%d')
        else:
            s_value = value.strftime('%Y%m%dT%H%M%S')
            if value.tzinfo:
                # handle timezone
                if value.tzinfo.utcoffset(value):
                    params['TZID'] = [value.tzinfo.tzname(value)]
                else:
                    # UTC
                    s_value += 'Z'
        return ContentLine(self.ical_name, value=s_value, params=params)

    def to_python(self, line, instance):
        value = line.value
        params = line.params or {}
        if params.get('VALUE') == 'DATE':
            return parse_cal_date(value)
        return parse_cal_datetime(line, instance.get_timezones())


class DurationProperty(ICalProperty):
    """ ICalProperty with 'DURATION' value type

    |  Will return a timedelta object.
    |  May be set to anything that timedelta() understands.
    |  May be set with a dict ({"days":2, "hours":6}).
    """

    def from_python(self, value, params={}):
        if isinstance(value, dict):
            value = timedelta(**value)
        elif value is not None and not isinstance(value, timedelta):
            value = timedelta(value)
        return ContentLine(self.ical_name,
                           value=timedelta_to_duration(value),
                           params=params)

    def to_python(self, line, instance):
        return parse_duration(line.value)


class VersionProperty(ICalProperty):
    """ ICalProperty for calendar 'VERSION'

    |  If there is a minversion and a maxversion,
    |  it will return the maxversion
    """

    def to_python(self, line, instance):
        if ';' in line.value:
            return line.value.split(';', 1)[1]
        return line.value
