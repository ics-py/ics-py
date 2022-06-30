from ics.grammar.parse import ContentLine
from ics.serializers.serializer import Serializer


class CalendarSerializer(Serializer):
    def serialize_0version(calendar, container):  # 0version will be sorted first
        container.append(ContentLine("VERSION", value="2.0"))

    def serialize_1prodid(calendar, container):  # 1prodid will be sorted second
        if calendar.creator:
            creator = calendar.creator
        else:
            creator = "ics.py - http://git.io/lLljaA"

        container.append(ContentLine("PRODID", value=creator))

    def serialize_calscale(calendar, container):
        if calendar.scale:
            container.append(ContentLine("CALSCALE", value=calendar.scale.upper()))

    def serialize_method(calendar, container):
        if calendar.method:
            container.append(ContentLine("METHOD", value=calendar.method.upper()))

    def serialize_event(calendar, container):
        for event in calendar.events:
            container.append(event.serialize())

    def serialize_todo(calendar, container):
        for todo in calendar.todos:
            container.append(todo.serialize())
