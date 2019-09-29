

# ------------------
# ----- Inputs -----
# ------------------
@Todo._extracts('DTSTAMP', required=True)
def dtstamp(todo: Todo, line: ContentLine):
    if line:
        # get the dict of vtimezones passed to the classmethod
        tz_dict = todo._classmethod_kwargs['tz']
        todo.dtstamp = iso_to_arrow(line, tz_dict)


@Todo._extracts('UID', required=True)
def uid(todo: Todo, line: ContentLine):
    if line:
        todo.uid = line.value


@Todo._extracts('COMPLETED')
def completed(todo: Todo, line: ContentLine):
    if line:
        # get the dict of vtimezones passed to the classmethod
        tz_dict = todo._classmethod_kwargs['tz']
        todo.completed = iso_to_arrow(line, tz_dict)


@Todo._extracts('CREATED')
def created(todo: Todo, line: ContentLine):
    if line:
        # get the dict of vtimezones passed to the classmethod
        tz_dict = todo._classmethod_kwargs['tz']
        todo.created = iso_to_arrow(line, tz_dict)


@Todo._extracts('DESCRIPTION')
def description(todo: Todo, line: ContentLine):
    todo.description = unescape_string(line.value) if line else None


@Todo._extracts('DTSTART')
def start(todo: Todo, line: ContentLine):
    if line:
        # get the dict of vtimezones passed to the classmethod
        tz_dict = todo._classmethod_kwargs['tz']
        todo.begin = iso_to_arrow(line, tz_dict)


@Todo._extracts('LOCATION')
def location(todo: Todo, line: ContentLine):
    todo.location = unescape_string(line.value) if line else None


@Todo._extracts('PERCENT-COMPLETE')
def percent(todo: Todo, line: ContentLine):
    todo.percent = int(line.value) if line else None


@Todo._extracts('PRIORITY')
def priority(todo: Todo, line: ContentLine):
    todo.priority = int(line.value) if line else None


@Todo._extracts('SUMMARY')
def summary(todo: Todo, line: ContentLine):
    todo.name = unescape_string(line.value) if line else None


@Todo._extracts('URL')
def url(todo: Todo, line: ContentLine):
    todo.url = unescape_string(line.value) if line else None


@Todo._extracts('DUE')
def due(todo: Todo, line: ContentLine):
    if line:
        #TODO: DRY [1]
        if todo._duration:
            raise ValueError("A todo can't have both DUE and DURATION")
        # get the dict of vtimezones passed to the classmethod
        tz_dict = todo._classmethod_kwargs['tz']
        todo._due_time = iso_to_arrow(line, tz_dict)


@Todo._extracts('DURATION')
def duration(todo: Todo, line: ContentLine):
    if line:
        #TODO: DRY [1]
        if todo._due_time:  # pragma: no cover
            raise ValueError("An todo can't have both DUE and DURATION")
        todo._duration = parse_duration(line.value)


@Todo._extracts('VALARM', multiple=True)
def alarms(todo: Todo, lines: List[ContentLine]):
    todo.alarms = [get_type_from_container(x)._from_container(x) for x in lines]


@Todo._extracts('STATUS')
def status(todo: Todo, line: ContentLine):
    if line:
        todo.status = line.value
