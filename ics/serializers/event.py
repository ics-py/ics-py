
# -------------------
# ----- Outputs -----
# -------------------
@Event._outputs
def o_created(event, container):
    if event.created:
        container.append(ContentLine('DTSTAMP', value=arrow_to_iso(event.created)))


@Event._outputs
def o_last_modified(event, container):
    if event.last_modified:
        instant = event.last_modified
        container.append(ContentLine('LAST-MODIFIED', value=arrow_to_iso(instant)))


@Event._outputs
def o_start(event, container):
    if event.begin and not event.all_day:
        container.append(ContentLine('DTSTART', value=arrow_to_iso(event.begin)))


@Event._outputs
def o_all_day(event, container):
    if event.begin and event.all_day:
        container.append(ContentLine('DTSTART', params={'VALUE': ['DATE']},
                                     value=arrow_date_to_iso(event.begin)))
        if event._end_time:
            container.append(ContentLine('DTEND', params={'VALUE': ['DATE']},
                                         value=arrow_date_to_iso(event.end)))


@Event._outputs
def o_duration(event, container):
    if event._duration and event.begin:
        representation = timedelta_to_duration(event._duration)
        container.append(ContentLine('DURATION', value=representation))


@Event._outputs
def o_end(event, container):
    if event.begin and event._end_time and not event.all_day:
        container.append(ContentLine('DTEND', value=arrow_to_iso(event.end)))


@Event._outputs
def o_summary(event, container):
    if event.name:
        container.append(ContentLine('SUMMARY', value=escape_string(event.name)))


@Event._outputs
def o_organizer(event, container):
    if event.organizer:
        container.append(str(event.organizer))


@Event._outputs
def o_attendee(event, container):
    for attendee in event.attendees:
        container.append(str(attendee))


@Event._outputs
def o_description(event, container):
    if event.description:
        container.append(ContentLine('DESCRIPTION', value=escape_string(event.description)))


@Event._outputs
def o_location(event, container):
    if event.location:
        container.append(ContentLine('LOCATION', value=escape_string(event.location)))


@Event._outputs
def o_geo(event, container):
    if event.geo:
        container.append(ContentLine('GEO', value='%f;%f' % event.geo))


@Event._outputs
def o_url(event, container):
    if event.url:
        container.append(ContentLine('URL', value=escape_string(event.url)))


@Event._outputs
def o_transparent(event, container):
    if event.transparent is None:
        return
    if event.transparent:
        container.append(ContentLine('TRANSP', value=escape_string('TRANSPARENT')))
    else:
        container.append(ContentLine('TRANSP', value=escape_string('OPAQUE')))


@Event._outputs
def o_uid(event, container):
    if event.uid:
        uid = event.uid
    else:
        uid = uid_gen()

    container.append(ContentLine('UID', value=uid))


@Event._outputs
def o_alarm(event, container):
    for alarm in event.alarms:
        container.append(str(alarm))


@Event._outputs
def o_status(event, container):
    if event.status:
        container.append(ContentLine('STATUS', value=event.status))


@Event._outputs
def o_classification(event, container):
    if event.classification:
        container.append(ContentLine('CLASS', value=event.classification))


@Event._outputs
def o_categories(event, container):
    if event.categories:
        container.append(ContentLine('CATEGORIES', value=','.join([escape_string(s) for s in event.categories])))
