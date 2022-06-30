from typing import TYPE_CHECKING

import arrow

from ics.grammar.parse import Container, ContentLine
from ics.serializers.serializer import Serializer
from ics.utils import (arrow_to_iso, escape_string, timedelta_to_duration,
                       uid_gen)

if TYPE_CHECKING:
    from ics.todo import Todo


class TodoSerializer(Serializer):
    def serialize_dtstamp(todo: "Todo", container: Container):
        if todo.dtstamp:
            instant = todo.dtstamp
        else:
            instant = arrow.now()

        container.append(ContentLine("DTSTAMP", value=arrow_to_iso(instant)))

    def serialize_uid(todo: "Todo", container: Container):
        if todo.uid:
            uid = todo.uid
        else:
            uid = uid_gen()

        container.append(ContentLine("UID", value=uid))

    def serialize_completed(todo: "Todo", container: Container):
        if todo.completed:
            container.append(
                ContentLine("COMPLETED", value=arrow_to_iso(todo.completed))
            )

    def serialize_created(todo: "Todo", container: Container):
        if todo.created:
            container.append(ContentLine("CREATED", value=arrow_to_iso(todo.created)))

    def serialize_description(todo: "Todo", container: Container):
        if todo.description:
            container.append(
                ContentLine("DESCRIPTION", value=escape_string(todo.description))
            )

    def serialize_start(todo: "Todo", container: Container):
        if todo.begin:
            container.append(ContentLine("DTSTART", value=arrow_to_iso(todo.begin)))

    def serialize_location(todo: "Todo", container: Container):
        if todo.location:
            container.append(
                ContentLine("LOCATION", value=escape_string(todo.location))
            )

    def serialize_percent(todo: "Todo", container: Container):
        if todo.percent is not None:
            container.append(ContentLine("PERCENT-COMPLETE", value=str(todo.percent)))

    def serialize_priority(todo: "Todo", container: Container):
        if todo.priority is not None:
            container.append(ContentLine("PRIORITY", value=str(todo.priority)))

    def serialize_summary(todo: "Todo", container: Container):
        if todo.name:
            container.append(ContentLine("SUMMARY", value=escape_string(todo.name)))

    def serialize_url(todo: "Todo", container: Container):
        if todo.url:
            container.append(ContentLine("URL", value=escape_string(todo.url)))

    def serialize_due(todo: "Todo", container: Container):
        if todo._due_time:
            container.append(ContentLine("DUE", value=arrow_to_iso(todo._due_time)))

    def serialize_duration(todo: "Todo", container: Container):
        if todo._duration:
            representation = timedelta_to_duration(todo._duration)
            container.append(ContentLine("DURATION", value=representation))

    def serialize_alarm(todo: "Todo", container: Container):
        for alarm in todo.alarms:
            container.append(alarm.serialize())

    def serialize_status(todo: "Todo", container: Container):
        if todo.status:
            container.append(ContentLine("STATUS", value=todo.status))
