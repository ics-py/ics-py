#!/usr/bin/env python
# -*- coding: utf-8 -*-

from collections import OrderedDict

from .parse import ContentLine


class Attendee(object):

    def __init__(self, email, common_name=None, rsvp=None):
        self.email = email
        self.common_name = common_name
        self.rsvp = rsvp

    @property
    def email(self):
        return self._email

    @email.setter
    def email(self, value):
        if isinstance(value, str):
            self._email = value
        else:
            raise ValueError("email should be a str")

    @property
    def common_name(self):
        return self._common_name

    @common_name.setter
    def common_name(self, value):
        if value is None:
            self._common_name = self.email
        elif isinstance(value, str):
            self._common_name = value
        else:
            raise ValueError("common_name should be None or str")

    @property
    def rsvp(self):
        return self._rsvp

    @rsvp.setter
    def rsvp(self, value):
        if value is None:
            self._rsvp = value
        elif value is True:
            self._rsvp = True
        elif value is False:
            self._rsvp = False
        elif value.upper() == "TRUE":
            self._rsvp = True
        elif value.upper() == "FALSE":
            self._rsvp = False
        else:
            raise ValueError("RSVP should be None, TRUE or FALSE")

    def __str__(self):
        """Returns the attendee in an iCalendar format."""
        return str(ContentLine('ATTENDEE', params=self.get_params(), value='mailto:%s' % self.email))

    def get_params(self):
        params = OrderedDict()
        if self.common_name:
            params.update({'CN': ['%s' % self.common_name]})

        if self.rsvp is not None:
            params.update({'RSVP': ["TRUE" if self.rsvp else "FALSE"]})

        return params
