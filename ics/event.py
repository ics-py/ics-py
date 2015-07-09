#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals, absolute_import

from six.moves import map

import copy
from datetime import date, time, timedelta

from .component import Component
from .utils import utcnow, uid_gen, is_date
from .property import (TextProperty, DateTimeProperty, DateTimeOrDateProperty,
                       DurationProperty)


class Event(Component):
    """A calendar event.

    Can be full-day or between two instants.
    Can be defined by a beginning instant and\
    a duration *or* end instant.
    """
    name = TextProperty('SUMMARY')
    begin = DateTimeOrDateProperty('DTSTART', validation='_validate_begin')
    end = DateTimeOrDateProperty('DTEND',
                                 validation='_validate_end',
                                 default='_default_end')
    duration = DurationProperty('DURATION',
                                validation='_validate_duration',
                                default='_default_duration')
    summary = TextProperty('SUMMARY')
    description = TextProperty('DESCRIPTION')
    location = TextProperty('LOCATION')
    url = TextProperty('URL')
    created = DateTimeProperty('DTSTAMP', default='_default_created',
                               create_on_access=True)
    uid = TextProperty('UID', default=uid_gen, create_on_access=True)

    _TYPE = "VEVENT"
    _EXTRACTORS = []
    _OUTPUTS = []

    def __init__(self,
                 name=None,
                 begin=None,
                 end=None,
                 duration=None,
                 uid=None,
                 description=None,
                 created=None,
                 location=None,
                 url=None):
        """Instantiate a new :class:`ics.event.Event`.

        Args:
            name (string)
            begin (date-or-datetime-convertible)
            end (date-or-datetime-convertible)
            duration (datetime.timedelta)
            uid (string): must be unique
            description (string)
            created (datetime-convertible)
            location (string)
            url (string)

        Raises:
            ValueError: if `end` and `duration` are specified at the same time

        Comment:
            Handling of all day events has changed a bit from the previous
            versions
        """
        super(Event, self).__init__()
        self.no_validation = False  # bypass all validation when `True`
        if name is not None:
            self.name = name
        if begin is not None:
            self.begin = begin
        if duration and end:
            raise ValueError(
                'Event() may not specify an end and a duration at the same time')
        if end is not None:
            self.end = end
            # temp = self.end
        if duration is not None:
            self.duration = duration
        if uid is not None:
            self.uid = uid
        if description is not None:
            self.description = description
        if created is not None:
            self.created = created
        if location is not None:
            self.location = location
        if url is not None:
            self.url = url

    def has_end(self):
        """
        Return:
            bool: self has an end
        """
        return bool(self._has_end() or self._has_duration())

    def _validate_begin(self, value):
        if not self.no_validation and value:
            if is_date(value):
                self.make_all_day()
            if self._has_end() and value > self.end:
                raise ValueError('Begin must be before end')
        return value

    def _default_end(self, property_name):
        if self._has_duration() and self.begin:  # if end is duration defined
            # return the beginning + duration
            if self.all_day:
                # The end day belongs to the event
                return self.begin + self.duration - timedelta(1)
            else:
                return self.begin + self.duration
        elif self.begin:
            if self.all_day:
                # According to RFC 5545 "DTEND" is set to a calendar date
                # after "DTSTART" if the VEVENT spans more than one date.
                # If DTEND is not specified, the VEVENT should be only
                # one day
                return self.begin
            else:
                # This is how it was implemented previously.
                # Is this good?
                return self.begin + timedelta(seconds=1)
        else:
            return None

    def _validate_end(self, value):
        """Validate the end of the event.

        May be set to anything that :func:`ics-utils.get_date_or_datetime` 
        understands.
        If set to a non null value, removes any already existing duration.
        Setting to None will have unexpected behavior if begin is not None.
        Must not be set to a lower value than self.begin.
        """
        if not self.no_validation and value:
            if self.all_day and hasattr(value, 'date'):
                value = value.date()
            if self.begin and value < self.begin:
                raise ValueError('End must be after begin')
            if self._has_duration():
                del self.duration
        return value

    def _default_duration(self, property_name):
        if self._has_end():
            if self.all_day:
                return self.end - self.begin + timedelta(1)
            return self.end - self.begin
        if self.all_day:
            return timedelta(1)
        if self.begin:
            # This is how it was implemented previously.
            # Is this good?
            return timedelta(seconds=1)
        return None

    def _validate_duration(self, value):
        if not self.no_validation and value and self._has_end():
            del self.end
        return value

    def _has_end(self):
        return 'DTEND' in self._properties

    def _has_duration(self):
        return 'DURATION' in self._properties

    @property
    def all_day(self):
        """
        Return:
            bool: self is an all-day event
        """
        return is_date(self.begin)

    def make_all_day(self):
        """Transforms self to an all-day event.

        The day will begin on the day of self.begin.
        """
        self.no_validation = True
        if not self.all_day:
            if self.begin:
                self.begin = self.begin.date()
            if self._has_duration():
                self.duration = timedelta(days=self.duration.days)
            elif self._has_end() and not is_date(self.end):
                # if the event ended at 0:00,
                # the next day should not be included in the all-day version
                if self.end.time() == time(0):
                    self.end = self.end.date() - timedelta(1)
                else:
                    self.end = self.end.date()
        self.no_validation = False

    def _default_created(self, property_name):
        return utcnow()

    def __urepr__(self):
        """Should not be used directly. Use self.__repr__ instead.

        Returns:
            unicode: a unicode representation (__repr__) of the event.
        """
        name = "'{}' ".format(self.name) if self.name else ''
        if self.all_day:
            return "<all-day Event {}{}>".format(name, self.begin.strftime("%F"))
        elif self.begin is None:
            return "<Event '{}'>".format(self.name) if self.name else "<Event>"
        else:
            return "<Event {}begin:{} end:{}>".format(name, self.begin, self.end)

    def __lt__(self, other):
        if not isinstance(other, Event):
            raise NotImplementedError(
                'Cannot compare Event and {}'.format(type(other)))
        if self.begin is None and other.begin is None:
            if self.name is None and other.name is None:
                return False
            elif self.name is None:
                return True
            elif other.name is None:
                return False
            else:
                return self.name < other.name
        return self.begin < other.begin

    def __le__(self, other):
        if not isinstance(other, Event):
            raise NotImplementedError(
                'Cannot compare Event and {}'.format(type(other)))
        if self.begin is None and other.begin is None:
            if self.name is None and other.name is None:
                return True
            elif self.name is None:
                return True
            elif other.name is None:
                return False
            else:
                return self.name <= other.name
        return self.begin <= other.begin

    def __gt__(self, other):
        if not isinstance(other, Event):
            raise NotImplementedError(
                'Cannot compare Event and {}'.format(type(other)))
        if self.begin is None and other.begin is None:
            return self.name > other.name
        return self.begin > other.begin

    def __ge__(self, other):
        if not isinstance(other, Event):
            raise NotImplementedError(
                'Cannot compare Event and {}'.format(type(other)))
        if self.begin is None and other.begin is None:
            return self.name >= other.name
        return self.begin >= other.begin

    def __or__(self, other):
        """ Return a 2-tuple of datetimes
        with begin and end of the period the two events overlap
        or (None, None) if they don't overlap
        """
        begin, end = None, None
        if self.begin and other.begin:
            begin = max(self.begin, other.begin)
        if self.end and other.end:
            end = min(self.end, other.end)
        return (begin, end) if begin and end and begin < end else (None, None)

    def __eq__(self, other):
        """Two events are considered equal if they have the same uid."""
        return self.uid == other.uid

    def clone(self):
        """
        Returns:
            Event: an exact copy of self"""
        self.uid  # make sure that there is a uid
        clone = copy.copy(self)
        clone._properties = copy.copy(clone._properties)
        clone._components = copy.copy(clone._components)
        return clone

    def __hash__(self):
        """
        Returns:
            int: hash of self. Based on self.uid."""
        return int(''.join(map(lambda x: '%.3d' % ord(x), self.uid)))

    def validate(self):
        """ Validate the event
        """
        super(Event, self).validate()
        if self._has_end() and self._has_duration():
            raise ValueError('Event() may not specify an end and a duration '
                             'at the same time')
