import copy

from ics.alarm.base import BaseAlarm
from ics.parse import ContentLine
from ics.utils import escape_string, unescape_string


class DisplayAlarm(BaseAlarm):
    """
    A calendar event VALARM with DISPLAY option.
    """

    # This ensures we copy the existing extractors and outputs from the base class, rather than referencing the array.
    _EXTRACTORS = copy.copy(BaseAlarm._EXTRACTORS)
    _OUTPUTS = copy.copy(BaseAlarm._OUTPUTS)

    def __init__(self,
                 description=None,
                 **kwargs):
        """
        Instantiates a new :class:`ics.alarm.DisplayAlarm`.

        Adheres to RFC5545 VALARM standard: http://icalendar.org/iCalendar-RFC-5545/3-6-6-alarm-component.html

        Args:
            description (string) : RFC5545 DESCRIPTION property
            kwargs (dict) : Args to :func:`ics.alarm.Alarm.__init__`
        """
        super(DisplayAlarm, self).__init__(**kwargs)
        self.description = description

    @property
    def action(self):
        return 'DISPLAY'

    def __repr__(self):
        value = '{0} trigger:{1}'.format(type(self).__name__, self.trigger)
        if self.repeat:
            value += ' repeat:{0} duration:{1}'.format(self.repeat, self.duration)

        value += ' description:{0}'.format(self.description)

        return '<{0}>'.format(value)


# ------------------
# ----- Inputs -----
# ------------------
@DisplayAlarm._extracts('DESCRIPTION', required=True)
def description(alarm, line):
    alarm.description = unescape_string(line.value) if line else None


# -------------------
# ----- Outputs -----
# -------------------
@DisplayAlarm._outputs
def o_description(alarm, container):
    container.append(ContentLine('DESCRIPTION', value=escape_string(alarm.description or '')))
