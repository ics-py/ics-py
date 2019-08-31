from ics.alarm.base import BaseAlarm
import copy


class NoneAlarm(BaseAlarm):
    """
    A calendar event VALARM with NONE option.
    """

    # This ensures we copy the existing extractors and outputs from the base class, rather than referencing the array.
    _EXTRACTORS = copy.copy(BaseAlarm._EXTRACTORS)
    _OUTPUTS = copy.copy(BaseAlarm._OUTPUTS)

    @property
    def action(self):
        return "NONE"
