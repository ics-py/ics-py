from datetime import timedelta

from ics.grammar.parse import ContentLine
from ics.serializers.serializer import Serializer
from ics.utils import escape_string, serialize_datetime_to_contentline, serialize_duration


class BaseAlarmSerializer(Serializer):
    def serialize_trigger(alarm, container):
        if not alarm.trigger:
            raise ValueError("Alarm must have a trigger")

        if isinstance(alarm.trigger, timedelta):
            representation = serialize_duration(alarm.trigger)
            container.append(ContentLine("TRIGGER", value=representation))
        else:
            cl = serialize_datetime_to_contentline("TRIGGER", alarm.trigger)
            cl.params["VALUE"] = ["DATE-TIME"]
            container.append(cl)

    def serialize_duration(alarm, container):
        if alarm.duration:
            representation = serialize_duration(alarm.duration)
            container.append(ContentLine("DURATION", value=representation))

    def serialize_repeat(alarm, container):
        if alarm.repeat:
            container.append(ContentLine("REPEAT", value=alarm.repeat))

    def serialize_action(alarm, container):
        container.append(ContentLine("ACTION", value=alarm.action))


class CustomAlarmSerializer(BaseAlarmSerializer):
    pass


class AudioAlarmSerializer(BaseAlarmSerializer):
    def serialize_attach(alarm, container):
        if alarm.sound:
            container.append(str(alarm.sound))


class DisplayAlarmSerializer(BaseAlarmSerializer):
    def serialize_description(alarm, container):
        container.append(
            ContentLine("DESCRIPTION", value=escape_string(alarm.display_text or ""))
        )


class EmailAlarmSerializer(BaseAlarmSerializer):
    def serialize_body(alarm, container):
        container.append(
            ContentLine("DESCRIPTION", value=escape_string(alarm.body or ""))
        )

    def serialize_subject(alarm, container):
        container.append(
            ContentLine("SUMMARY", value=escape_string(alarm.subject or ""))
        )

    def serialize_recipients(alarm, container):
        for attendee in alarm.recipients:
            container.append(attendee.serialize())


class NoneAlarmSerializer(BaseAlarmSerializer):
    pass
