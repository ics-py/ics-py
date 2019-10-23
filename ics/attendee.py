from typing import Any, Dict

from ics.grammar.parse import ContentLine


class Attendee(object):

    def __init__(self, email: str, common_name: str = None, rsvp: bool = None) -> None:
        self.email = email
        self.common_name = common_name or email
        self.rsvp = rsvp

    def __str__(self) -> str:
        """Returns the attendee in an iCalendar format."""
        return str(ContentLine('ATTENDEE', params=self._get_params(), value='mailto:%s' % self.email))

    def _get_params(self) -> Dict[str, Any]:
        params: Dict[str, Any] = {}
        if self.common_name:
            params['CN'] = ["'%s'" % self.common_name]

        if self.rsvp:
            params['RSVP'] = [self.rsvp]

        return params
