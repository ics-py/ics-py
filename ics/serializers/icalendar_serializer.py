from ics.parse import ContentLine
from ics.serializers.serializer import Serializer


class CalendarSerializer(Serializer):
    def serialize_prodid(calendar, container):
        if calendar.creator:
            creator = calendar.creator
        else:
            creator = "ics.py - http://git.io/lLljaA"

        container.append(ContentLine("PRODID", value=creator))

    def serialize_version(calendar, container):
        container.append(ContentLine("VERSION", value="2.0"))

    def serialize_calscale(calendar, container):
        if calendar.scale:
            container.append(ContentLine("CALSCALE", value=calendar.scale.upper()))

    def serialize_method(calendar, container):
        if calendar.method:
            container.append(ContentLine("METHOD", value=calendar.method.upper()))

    def serialize_event(calendar, container):
        for event in calendar.events:
            container.append(str(event))

    def serialize_todo(calendar, container):
        for todo in calendar.todos:
            container.append(str(todo))
