from typing import TYPE_CHECKING

from ics.grammar.parse import Container, ContentLine
from ics.serializers.serializer import Serializer
from ics.utils import (escape_string, serialize_datetime_to_contentline, serialize_duration, uid_gen)

if TYPE_CHECKING:
    from ics.todo import Todo


class TodoSerializer(Serializer):
    def serialize_dtstamp(todo: "Todo", container: "Container"):
        container.append(serialize_datetime_to_contentline("DTSTAMP", todo.dtstamp))

    def serialize_created(todo: "Todo", container: "Container"):
        if todo.created:
            container.append(serialize_datetime_to_contentline("CREATED", todo.created))

    def serialize_last_modified(todo: "Todo", container: "Container"):
        if todo.last_modified:
            container.append(serialize_datetime_to_contentline("LAST-MODIFIED", todo.last_modified))

    def serialize_uid(todo: "Todo", container: Container):
        if todo.uid:
            uid = todo.uid
        else:
            uid = uid_gen()

        container.append(ContentLine("UID", value=uid))

    def serialize_completed(todo: "Todo", container: Container):
        if todo.completed:
            container.append(
                serialize_datetime_to_contentline("COMPLETED", todo.completed)
            )

    def serialize_description(todo: "Todo", container: Container):
        if todo.description:
            container.append(
                ContentLine("DESCRIPTION", value=escape_string(todo.description))
            )

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

    def serialize_start(todo: "Todo", container: Container):
        if todo.begin:
            container.append(serialize_datetime_to_contentline("DTSTART", todo.begin))

    def serialize_due(todo: "Todo", container: Container):
        if todo.due_representation == "end":
            due = todo.due
            assert due is not None
            container.append(serialize_datetime_to_contentline("DUE", due))

    def serialize_duration(todo: "Todo", container: Container):
        if todo.due_representation == "duration":
            duration = todo.duration
            assert duration is not None
            container.append(ContentLine("DURATION", value=serialize_duration(duration)))

    def serialize_alarm(todo: "Todo", container: Container):
        for alarm in todo.alarms:
            container.append(alarm.serialize())

    def serialize_status(todo: "Todo", container: Container):
        if todo.status:
            container.append(ContentLine("STATUS", value=todo.status))
