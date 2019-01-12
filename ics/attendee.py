#!/usr/bin/env python
# -*- coding: utf-8 -*-

from .parse import ContentLine


class Attendee(object):

    def __init__(self, email, common_name=None, rsvp=None):
        self.email = email
        self.common_name = common_name or email
        self.rsvp = rsvp

    def __str__(self):
        """Returns the attendee in an iCalendar format."""
        return str(ContentLine('ATTENDEE', params=self.get_params(), value='mailto:%s' % self.email))

    def get_params(self):
        params = {}
        if self.common_name:
            params.update({'CN': ["'%s'" % self.common_name]})

        if self.rsvp:
            params.update({'RSVP': [self.rsvp]})

        return params
