class BaseAlarmParser(Parser):

    # ------------------
    # ----- Inputs -----
    # ------------------
    @BaseAlarm._extracts("TRIGGER", required=True)
    def trigger(alarm, line):
        if line.params.get("VALUE", [""])[0] == "DATE-TIME":
            alarm.trigger = iso_to_arrow(line)
        elif line.params.get("VALUE", ["DURATION"])[0] == "DURATION":
            alarm.trigger = parse_duration(line.value)
        else:
            warnings.warn("ics.py encountered a TRIGGER of unknown type '%s'. It has been ignored." % line.params["VALUE"][0])


    @BaseAlarm._extracts("DURATION")
    def duration(alarm, line):
        if line:
            alarm._duration = parse_duration(line.value)


    @BaseAlarm._extracts("REPEAT")
    def repeat(alarm, line):
        if line:
            alarm._repeat = int(line.value)

class CustomAlarmParser(BaseAlarmParser):

    @CustomAlarm._extracts("ACTION")
    def action(alarm, line, required=True):
        print(line)
        if line:
            alarm._action = line.value


class AudioAlarmParser(BaseAlarmParser):


        @AudioAlarm._extracts("ATTACH")
        def attach(alarm, line):
            if line:
                alarm._sound = line


class DisplayAlarmParser(BaseAlarmParser):

    # ------------------
    # ----- Inputs -----
    # ------------------
    @DisplayAlarm._extracts("DESCRIPTION", required=True)
    def description(alarm, line):
        alarm.display_text = unescape_string(line.value) if line else None


class EmailAlarmParser(BaseAlarmParser):

    # ------------------
    # ----- Inputs -----
    # ------------------
    @EmailAlarm._extracts("DESCRIPTION", required=True)
    def body(alarm, line):
        alarm.body = unescape_string(line.value) if line else None


    @EmailAlarm._extracts("SUMMARY", required=True)
    def subject(alarm, line):
        alarm.subject = unescape_string(line.value) if line else None


    @EmailAlarm._extracts("ATTENDEE", required=True, multiple=True)
    def recipient(alarm, line):
        email = unescape_string(line.value)
        alarm.recipients.append(email)
