class BaseAlarmSerializer(Serializer):

    # -------------------
    # ----- Outputs -----
    # -------------------
    @BaseAlarm._outputs
    def o_trigger(alarm, container):
        if not alarm.trigger:
            raise ValueError("Alarm must have a trigger")

        if type(alarm.trigger) is timedelta:
            representation = timedelta_to_duration(alarm.trigger)
            container.append(ContentLine("TRIGGER", value=representation))
        else:
            container.append(
                ContentLine(
                    "TRIGGER",
                    params={"VALUE": ["DATE-TIME"]},
                    value=arrow_to_iso(alarm.trigger),
                )
            )


    @BaseAlarm._outputs
    def o_duration(alarm, container):
        if alarm.duration:
            representation = timedelta_to_duration(alarm.duration)
            container.append(ContentLine("DURATION", value=representation))


    @BaseAlarm._outputs
    def o_repeat(alarm, container):
        if alarm.repeat:
            container.append(ContentLine("REPEAT", value=alarm.repeat))


    @BaseAlarm._outputs
    def o_action(alarm, container):
        container.append(ContentLine("ACTION", value=alarm.action))


class CustomAlarmSerializer(BaseAlarmSerializer):
    pass

class AudioAlarmSerializer(BaseAlarmSerializer):

    # -------------------
    # ----- Outputs -----
    # -------------------
    @AudioAlarm._outputs
    def o_attach(alarm, container):
        if alarm._sound:
            container.append(str(alarm._sound))

class DisplayAlarmSerializer(BaseAlarmSerializer):

    # -------------------
    # ----- Outputs -----
    # -------------------
    @DisplayAlarm._outputs
    def o_description(alarm, container):
        container.append(
            ContentLine("DESCRIPTION", value=escape_string(alarm.display_text or ""))
        )

class EmailAlarmSerializer(BaseAlarmSerializer):

    # -------------------
    # ----- Outputs -----
    # -------------------
    @EmailAlarm._outputs
    def o_body(alarm, container):
        container.append(ContentLine("DESCRIPTION", value=escape_string(alarm.body or "")))


    @EmailAlarm._outputs
    def o_subject(alarm, container):
        container.append(ContentLine("SUMMARY", value=escape_string(alarm.subject or "")))


    @EmailAlarm._outputs
    def o_recipients(alarm, container):
        for email in alarm.recipients:
            container.append(
                ContentLine("ATTENDEE", value=escape_string("mailto:%s" % email))
            )
