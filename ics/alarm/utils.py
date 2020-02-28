from ics.utils import get_lines


def get_type_from_action(action_type):
    if action_type == "DISPLAY":
        from ics.alarm import DisplayAlarm
        return DisplayAlarm
    elif action_type == "AUDIO":
        from ics.alarm import AudioAlarm
        return AudioAlarm
    elif action_type == "NONE":
        from ics.alarm import NoneAlarm
        return NoneAlarm
    elif action_type == 'EMAIL':
        from ics.alarm import EmailAlarm
        return EmailAlarm
    else:
        from ics.alarm import CustomAlarm
        return CustomAlarm


def get_type_from_container(container):
    action_type_lines = get_lines(container, "ACTION", keep=True)
    if len(action_type_lines) > 1:
        raise ValueError("Too many ACTION parameters in VALARM")

    action_type = action_type_lines[0]
    return get_type_from_action(action_type.value)
