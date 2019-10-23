from typing import Any, Dict

from ics.grammar.parse import ContentLine


class Organizer(object):

    def __init__(self, email: str, common_name: str = None, dir: str = None, sent_by: str = None):
        self.email = email
        self.common_name = common_name or email
        self.dir = dir
        self.sent_by = sent_by

    def __str__(self) -> str:
        """Returns the attendee in an iCalendar format."""
        return str(ContentLine('ORGANIZER',
                               params=self._get_params(), value='mailto:%s' % self.email))

    def _get_params(self) -> Dict[str, Any]:
        params = {}
        if self.common_name:
            params.update({'CN': ["'%s'" % self.common_name]})

        if self.dir:
            params.update({'DIR': ["'%s'" % self.dir]})

        if self.sent_by:
            params.update({'SENT-BY': ["'%s'" % self.sent_by]})

        return params
