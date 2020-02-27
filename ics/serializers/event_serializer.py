from ics.attendee import Attendee, Organizer
from ics.grammar.parse import ContentLine
from ics.serializers.serializer import Serializer
from ics.utils import (arrow_date_to_iso, arrow_to_iso, escape_string,
                       timedelta_to_duration, uid_gen)


class EventSerializer(Serializer):
    def serialize_created(event, container):
        if event.created:
            container.append(ContentLine("DTSTAMP", value=arrow_to_iso(event.created)))

    def serialize_last_modified(event, container):
        if event.last_modified:
            instant = event.last_modified
            container.append(ContentLine("LAST-MODIFIED", value=arrow_to_iso(instant)))

    def serialize_start(event, container):
        if event.begin and not event.all_day:
            container.append(ContentLine("DTSTART", value=arrow_to_iso(event.begin)))

    def serialize_all_day(event, container):
        if event.begin and event.all_day:
            container.append(
                ContentLine(
                    "DTSTART",
                    params={"VALUE": ["DATE"]},
                    value=arrow_date_to_iso(event.begin),
                )
            )
            if event._end_time:
                container.append(
                    ContentLine(
                        "DTEND",
                        params={"VALUE": ["DATE"]},
                        value=arrow_date_to_iso(event.end),
                    )
                )

    def serialize_duration(event, container):
        if event._duration and event.begin:
            representation = timedelta_to_duration(event._duration)
            container.append(ContentLine("DURATION", value=representation))

    def serialize_end(event, container):
        if event.begin and event._end_time and not event.all_day:
            container.append(ContentLine("DTEND", value=arrow_to_iso(event.end)))

    def serialize_summary(event, container):
        if event.name:
            container.append(ContentLine("SUMMARY", value=escape_string(event.name)))

    def serialize_organizer(event, container):
        if event.organizer:
            organizer = event.organizer
            if isinstance(organizer, str):
                organizer = Organizer(organizer)
            container.append(organizer.serialize())

    def serialize_attendee(event, container):
        for attendee in event.attendees:
            if isinstance(attendee, str):
                attendee = Attendee(attendee)
            container.append(attendee.serialize())

    def serialize_description(event, container):
        if event.description:
            container.append(
                ContentLine("DESCRIPTION", value=escape_string(event.description))
            )

    def serialize_location(event, container):
        if event.location:
            container.append(
                ContentLine("LOCATION", value=escape_string(event.location))
            )

    def serialize_geo(event, container):
        if event.geo:
            container.append(ContentLine("GEO", value="%f;%f" % event.geo))

    def serialize_url(event, container):
        if event.url:
            container.append(ContentLine("URL", value=escape_string(event.url)))

    def serialize_transparent(event, container):
        if event.transparent is None:
            return
        if event.transparent:
            container.append(ContentLine("TRANSP", value=escape_string("TRANSPARENT")))
        else:
            container.append(ContentLine("TRANSP", value=escape_string("OPAQUE")))

    def serialize_uid(event, container):
        if event.uid:
            uid = event.uid
        else:
            uid = uid_gen()

        container.append(ContentLine("UID", value=uid))

    def serialize_alarm(event, container):
        for alarm in event.alarms:
            container.append(str(alarm))

    def serialize_status(event, container):
        if event.status:
            container.append(ContentLine("STATUS", value=event.status))

    def serialize_class(event, container):
        if event.classification:
            container.append(ContentLine("CLASS", value=event.classification))

    def serialize_categories(event, container):
        if event.categories:
            container.append(
                ContentLine(
                    "CATEGORIES",
                    value=",".join([escape_string(s) for s in event.categories]),
                )
            )
