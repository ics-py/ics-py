
# ------------------
# ----- Inputs -----
# ------------------
@Event._extracts('DTSTAMP')
def created(event, line):
    if line:
        # get the dict of vtimezones passed to the classmethod
        tz_dict = event._classmethod_kwargs['tz']
        event.created = iso_to_arrow(line, tz_dict)


@Event._extracts('LAST-MODIFIED')
def last_modified(event, line):
    if line:
        tz_dict = event._classmethod_kwargs['tz']
        event.last_modified = iso_to_arrow(line, tz_dict)


@Event._extracts('DTSTART')
def start(event, line):
    if line:
        # get the dict of vtimezones passed to the classmethod
        tz_dict = event._classmethod_kwargs['tz']
        event.begin = iso_to_arrow(line, tz_dict)
        event._begin_precision = iso_precision(line.value)


@Event._extracts('DURATION')
def duration(event, line):
    if line:
        #TODO: DRY [1]
        if event._end_time: # pragma: no cover
            raise ValueError("An event can't have both DTEND and DURATION")
        event._duration = parse_duration(line.value)


@Event._extracts('DTEND')
def end(event, line):
    if line:
        #TODO: DRY [1]
        if event._duration:
            raise ValueError("An event can't have both DTEND and DURATION")
        # get the dict of vtimezones passed to the classmethod
        tz_dict = event._classmethod_kwargs['tz']
        event._end_time = iso_to_arrow(line, tz_dict)
        # one could also save the end_precision to check that if begin_precision is day, end_precision also is


@Event._extracts('SUMMARY')
def summary(event, line):
    event.name = unescape_string(line.value) if line else None


@Event._extracts('ORGANIZER')
def organizer(event, line):
    event.organizer = unescape_string(line.value) if line else None


@Event._extracts('DESCRIPTION')
def description(event, line):
    event.description = unescape_string(line.value) if line else None


@Event._extracts('LOCATION')
def location(event, line):
    event.location = unescape_string(line.value) if line else None


@Event._extracts('GEO')
def geo(event, line):
    if line:
        latitude, _, longitude = unescape_string(line.value).partition(';')
        event.geo = float(latitude), float(longitude)


@Event._extracts('URL')
def url(event, line):
    event.url = unescape_string(line.value) if line else None


@Event._extracts('TRANSP')
def transparent(event, line):
    if line and line.value in ['TRANSPARENT', 'OPAQUE']:
        event.transparent = (line.value == 'TRANSPARENT')


# TODO : make uid required ?
# TODO : add option somewhere to ignore some errors
@Event._extracts('UID')
def uid(event, line):
    if line:
        event.uid = line.value


@Event._extracts('VALARM', multiple=True)
def alarms(event, lines):
    event.alarms = [get_type_from_container(x)._from_container(x) for x in lines]


@Event._extracts('STATUS')
def status(event, line):
    if line:
        event.status = line.value


@Event._extracts('CLASS')
def classification(event, line):
    if line:
        event.classification = line.value


@Event._extracts('CATEGORIES')
def categories(event, line):
    event.categories = set()
    if line:
        # In the regular expression: Only match unquoted commas.
        for cat in re.split("(?<!\\\\),", line.value):
            event.categories.update({unescape_string(cat)})
