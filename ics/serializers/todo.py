
# -------------------
# ----- Outputs -----
# -------------------
@Todo._outputs
def o_dtstamp(todo: Todo, container: Container):
    if todo.dtstamp:
        instant = todo.dtstamp
    else:
        instant = arrow.now()

    container.append(ContentLine('DTSTAMP',
                                 value=arrow_to_iso(instant)))


@Todo._outputs
def o_uid(todo: Todo, container: Container):
    if todo.uid:
        uid = todo.uid
    else:
        uid = uid_gen()

    container.append(ContentLine('UID', value=uid))


@Todo._outputs
def o_completed(todo: Todo, container: Container):
    if todo.completed:
        container.append(ContentLine('COMPLETED',
                                     value=arrow_to_iso(todo.completed)))


@Todo._outputs
def o_created(todo: Todo, container: Container):
    if todo.created:
        container.append(ContentLine('CREATED',
                                     value=arrow_to_iso(todo.created)))


@Todo._outputs
def o_description(todo: Todo, container: Container):
    if todo.description:
        container.append(ContentLine('DESCRIPTION',
                                     value=escape_string(todo.description)))


@Todo._outputs
def o_start(todo: Todo, container: Container):
    if todo.begin:
        container.append(ContentLine('DTSTART',
                                     value=arrow_to_iso(todo.begin)))


@Todo._outputs
def o_location(todo: Todo, container: Container):
    if todo.location:
        container.append(ContentLine('LOCATION',
                                     value=escape_string(todo.location)))


@Todo._outputs
def o_percent(todo: Todo, container: Container):
    if todo.percent is not None:
        container.append(ContentLine('PERCENT-COMPLETE',
                                     value=str(todo.percent)))


@Todo._outputs
def o_priority(todo: Todo, container: Container):
    if todo.priority is not None:
        container.append(ContentLine('PRIORITY',
                                     value=str(todo.priority)))


@Todo._outputs
def o_summary(todo: Todo, container: Container):
    if todo.name:
        container.append(ContentLine('SUMMARY',
                                     value=escape_string(todo.name)))


@Todo._outputs
def o_url(todo: Todo, container: Container):
    if todo.url:
        container.append(ContentLine('URL',
                                     value=escape_string(todo.url)))


@Todo._outputs
def o_due(todo: Todo, container: Container):
    if todo._due_time:
        container.append(ContentLine('DUE',
                                     value=arrow_to_iso(todo._due_time)))


@Todo._outputs
def o_duration(todo: Todo, container: Container):
    if todo._duration:
        representation = timedelta_to_duration(todo._duration)
        container.append(ContentLine('DURATION',
                                     value=representation))


@Todo._outputs
def o_alarm(todo: Todo, container: Container):
    for alarm in todo.alarms:
        container.append(str(alarm))


@Todo._outputs
def o_status(todo: Todo, container: Container):
    if todo.status:
        container.append(ContentLine('STATUS', value=todo.status))
