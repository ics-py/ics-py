#!/usr/bin/env python
# -*- coding: utf-8 -*-

from .parse import ContentLine


class Organizer(object):

    def __init__(self, email, common_name=None, dir=None, sent_by=None):
        self.email = email
        self.common_name = common_name or email
        self.dir = dir
        self.sent_by = sent_by

    def __str__(self):
        """Returns the attendee in an iCalendar format."""
        return str(ContentLine('ORGANIZER',
                               params=self.get_params(), value='mailto:%s' % self.email))

    def get_params(self):
        params = {}
        if self.common_name:
            params.update({'CN': ["'%s'" % self.common_name]})

        if self.dir:
            params.update({'DIR': ["'%s'" % self.dir]})

        if self.sent_by:
            params.update({'SENT-BY': ["'%s'" % self.sent_by]})

        return params
