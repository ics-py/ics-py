import copy

from ics.alarm.base import BaseAlarm
from ics.parse import ContentLine
from ics.utils import escape_string, unescape_string


class AudioAlarm(BaseAlarm):
    """
    A calendar event VALARM with AUDIO option.
    """

    # This ensures we copy the existing extractors and outputs from the base class, rather than referencing the array.
    _EXTRACTORS = copy.copy(BaseAlarm._EXTRACTORS)
    _OUTPUTS = copy.copy(BaseAlarm._OUTPUTS)

    def __init__(self,
                 attach=None,
                 attach_params=None,
                 **kwargs):
        """
        Instantiates a new :class:`ics.alarm.AudioAlarm`.

        Adheres to RFC5545 VALARM standard: http://icalendar.org/iCalendar-RFC-5545/3-6-6-alarm-component.html

        Args:
            attach (string) : RFC5545 ATTACH property, pointing to an audio object
            attach_params (dict) : RFC5545 attachparam values
            kwargs (dict) : Args to :func:`ics.alarm.Alarm.__init__`
        """
        super(AudioAlarm, self).__init__(**kwargs)
        self.attach = attach
        self.attach_params = attach_params

    @property
    def action(self):
        return 'AUDIO'

    def __repr__(self):
        value = '{0} trigger:{1}'.format(type(self).__name__, self.trigger)
        if self.repeat:
            value += ' repeat:{0} duration:{1}'.format(self.repeat, self.duration)

        if self.attach:
            value += ' attach:{0}'.format(self.attach)
            if self.attach_params:
                value += ' attach_params:{0}'.format(self.attach_params)

        return '<{0}>'.format(value)


# ------------------
# ----- Inputs -----
# ------------------
@AudioAlarm._extracts('ATTACH')
def attach(alarm, line):
    if line:
        if line.value:
            alarm.attach = unescape_string(line.value)

        if line.params:
            alarm.attach_params = line.params


# -------------------
# ----- Outputs -----
# -------------------
@AudioAlarm._outputs
def o_attach(alarm, container):
    if alarm.attach:
        container.append(ContentLine('ATTACH', params=alarm.attach_params or {}, value=escape_string(alarm.attach)))
