from typing import TYPE_CHECKING

from ics.attendee import Attendee, Organizer
from ics.grammar.parse import ContentLine
from ics.serializers.serializer import Serializer
from ics.utils import (escape_string, serialize_date, serialize_datetime_to_contentline, serialize_duration, uid_gen)

if TYPE_CHECKING:
    from ics.event import Event
    from ics.grammar.parse import Container


class EventSerializer(Serializer):
    def serialize_dtstamp(event: "Event", container: "Container"):
        container.append(serialize_datetime_to_contentline("DTSTAMP", event.dtstamp))

    def serialize_created(event: "Event", container: "Container"):
        if event.created:
            container.append(serialize_datetime_to_contentline("CREATED", event.created))

    def serialize_last_modified(event: "Event", container: "Container"):
        if event.last_modified:
            container.append(serialize_datetime_to_contentline("LAST-MODIFIED", event.last_modified))

    def serialize_start(event: "Event", container: "Container"):
        if event.begin:
            if not event.all_day:
                container.append(serialize_datetime_to_contentline("DTSTART", event.begin))
            else:
                container.append(
                    ContentLine(
                        "DTSTART",
                        params={"VALUE": ["DATE"]},
                        value=serialize_date(event.begin),
                    )
                )

    def serialize_end(event: "Event", container: "Container"):
        if event.end_representation == "end":
            end = event.end
            assert end is not None
            if not event.all_day:
                container.append(serialize_datetime_to_contentline("DTEND", end))
            else:
                container.append(
                    ContentLine(
                        "DTSTART",
                        params={"VALUE": ["DATE"]},
                        value=serialize_date(end),
                    )
                )

    def serialize_duration(event: "Event", container: "Container"):
        if event.end_representation == "duration":
            duration = event.duration
            assert duration is not None
            container.append(ContentLine("DURATION", value=serialize_duration(duration)))

    def serialize_summary(event: "Event", container: "Container"):
        if event.name:
            container.append(ContentLine("SUMMARY", value=escape_string(event.name)))

    def serialize_organizer(event: "Event", container: "Container"):
        if event.organizer:
            organizer = event.organizer
            if isinstance(organizer, str):
                organizer = Organizer(organizer)
            container.append(organizer.serialize())

    def serialize_attendee(event: "Event", container: "Container"):
        for attendee in event.attendees:
            if isinstance(attendee, str):
                attendee = Attendee(attendee)
            container.append(attendee.serialize())

    def serialize_description(event: "Event", container: "Container"):
        if event.description:
            container.append(
                ContentLine("DESCRIPTION", value=escape_string(event.description))
            )

    def serialize_location(event: "Event", container: "Container"):
        if event.location:
            container.append(
                ContentLine("LOCATION", value=escape_string(event.location))
            )

    def serialize_geo(event: "Event", container: "Container"):
        if event.geo:
            container.append(ContentLine("GEO", value="%f;%f" % event.geo))

    def serialize_url(event: "Event", container: "Container"):
        if event.url:
            container.append(ContentLine("URL", value=escape_string(event.url)))

    def serialize_transparent(event: "Event", container: "Container"):
        if event.transparent is None:
            return
        if event.transparent:
            container.append(ContentLine("TRANSP", value=escape_string("TRANSPARENT")))
        else:
            container.append(ContentLine("TRANSP", value=escape_string("OPAQUE")))

    def serialize_uid(event: "Event", container: "Container"):
        if event.uid:
            uid = event.uid
        else:
            uid = uid_gen()

        container.append(ContentLine("UID", value=uid))

    def serialize_alarm(event: "Event", container: "Container"):
        for alarm in event.alarms:
            container.append(alarm.serialize())

    def serialize_status(event: "Event", container: "Container"):
        if event.status:
            container.append(ContentLine("STATUS", value=event.status))

    def serialize_class(event: "Event", container: "Container"):
        if event.classification:
            container.append(ContentLine("CLASS", value=event.classification))

    def serialize_categories(event: "Event", container: "Container"):
        if event.categories:
            container.append(
                ContentLine(
                    "CATEGORIES",
                    value=",".join([escape_string(s) for s in event.categories]),
                )
            )
