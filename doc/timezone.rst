vTimezone Handling
==================

This chapter describes how `ics.py` handles the timezones that come with the python datetimes you pass to it
and also the timezone information embedded into ics files.
But first, let's grab the required imports and make sure we have a well-defined timezone set.

::

    >>> from dateutil.tz import gettz
    >>> from datetime import datetime as dt
    >>> from ics import Event, Calendar, Timezone
    >>> import os, time
    >>> os.environ['TZ'] = "Etc/GMT-2"
    >>> time.tzset()
    >>> time.tzname
    ('+02', '+02')

Let's create some simple event and have a look at its timezone information:

::

    >>> t = dt(2020, 4, 1, 18, 0)
    >>> e = Event(begin=t, uid="test", dtstamp=t)
    >>> e.begin
    datetime.datetime(2020, 4, 1, 18, 0)
    >>> e.dtstamp
    datetime.datetime(2020, 4, 1, 16, 0, tzinfo=Timezone.from_tzid('UTC'))
    >>> e.timespan.is_floating(), e.begin.tzinfo is None
    (True, True)
    >>> from ics.timezone import UTC, is_utc
    >>> is_utc(e.dtstamp), e.dtstamp.tzinfo == UTC # prefer is_utc to comparing with UTC
    (True, True)
    >>> print(e.serialize())  # doctest: +NORMALIZE_WHITESPACE
    BEGIN:VEVENT
    DTSTART:20200401T180000
    UID:test
    DTSTAMP:20200401T160000Z
    END:VEVENT

Unsurprisingly, the event kept the begin timezone we passed in.
As we used a naïve datetime object, the ``tzinfo`` is ``None`` and we consider the timespan floating.
This means that it will be interpreted as local time, but see the section on comparing datetime for more details on this.
Every event has an additional ``dtstamp`` field, which represents the time its ics representation was created.
The RFC standard requires that this property is always an UTC timestamp, which ics.py happily ensures.
The example also shows the recommended way for checking whether a datetime objects is in UTC using the ``is_utc()`` function,
which unlike simple equality comparison also checks for the UTC implementations of other libraries (like datetime, dateutil and pytz).

Now let's see what happens when we use a real timezone, e.g. the Olson timezone for New York, accessed through dateutil's ``gettz``:

::

    >>> e.begin = t.replace(tzinfo=gettz('America/New York'))
    >>> e.begin
    datetime.datetime(2020, 4, 1, 18, 0, tzinfo=tzfile('/usr/share/zoneinfo/America/New_York'))
    >>> print(Calendar(events=[e]).serialize())  # doctest: +ELLIPSIS,+NORMALIZE_WHITESPACE
    BEGIN:VCALENDAR
    VERSION:2.0
    PRODID:ics.py 0.8.0-dev0 - http://git.io/lLljaA
    BEGIN:VTIMEZONE
    TZID:/ics.py/2020.1/America/New_York
    ...
    END:VTIMEZONE
    BEGIN:VEVENT
    DTSTART;TZID=/ics.py/2020.1/America/New_York:20200401T180000
    UID:test
    DTSTAMP:20200401T160000Z
    END:VEVENT
    END:VCALENDAR

The ics file carries a full vTimezone specification, allowing the timezone to be exactly reconstructed on any system, even ones that don't have the IANA database available.
This data was provided by the `ics_vtimezone <https://github.com/N-Coder/ics_vtimezone>`__ package and you can find the full vTimezone object that was embedded
`in its data folder <https://github.com/N-Coder/ics_vtimezones/blob/master/src/ics_vtimezones/data/zoneinfo/America/New_York.ics>`__.
Having a separate project from ics.py allows regular database updates when the timezone data changes
(which is not as seldom as you might think) without having to do a new release of ``ics.py``.
Similar to ``pytz``, the project follows the ``YYYY.minor`` `calendar versioning <https://calver.org/>`__ scheme representing the periodic updates of its data,
while ``ics.py`` uses `semantic versioning <https://semver.org/>`__ to allow ensuring compatibility with its more gradually evolving code-base.
As the timezone database get's updated from time to time and we're actually storing a snapshot of it, the timezones get these weird ``/ics.py/2020.1/`` prefixes.
They provide an unique identifier for different revisions of a timezone and prevent our future selves from accidentally misinterpreting a datetime stored in the past.

Do I get my tzinfo objects back?
--------------------------------

Note that deserializing the same event again won't yield the exact same tzinfo object from dateutil, but actually the interpretation of the vTimezone information embedded in the ics file.
The two ``tzinfo`` objects are thus unequal, but the respective ``datetime`` objects still compare equal, as datetimes are compared by the absolute UTC timestamp ignoring their actual timezone:

::

    >>> e2 = Calendar(Calendar(events=[e]).serialize()).events[0]
    >>> e2.begin
    datetime.datetime(2020, 4, 1, 18, 0, tzinfo=Timezone.from_tzid('/ics.py/2020.1/America/New_York'))
    >>> # the tzinfo objects are different
    >>> e.begin.tzinfo == e2.begin.tzinfo
    False
    >>> # but the datetimes still compare equal, as they represent the same instant in UTC
    >>> e.begin == e2.begin
    True
    >>> # similar to when a datetime is converted to the same instant in a different timezone
    >>> e.begin == e.begin.astimezone(gettz("Asia/Hong Kong"))
    True

Interpreting TZIDs and tzinfo objects
-------------------------------------

We do our best to interpret TZIDs and convert arbitrary Python tzinfo objects without having to guess.
We favour correctness over completeness, so you might find some arcane IDs or tzinfo implementations that fail to be converted.
If you think that some case you found should be supported and you also know how that could be done, we'd be glad to merge your PR for that.

::

    >>> Timezone.from_tzid("/citadel.org/20190914_1/America/New_York")
    Timezone.from_tzid('/ics.py/2020.1/America/New_York')
    >>> Timezone.from_tzinfo(gettz("America/New York"))
    Timezone.from_tzid('/ics.py/2020.1/America/New_York')
    >>> cal = Calendar("""
    ... BEGIN:VCALENDAR
    ... VERSION:2.0
    ... PRODID:Some Software that doesn't write vTimezones
    ... BEGIN:VEVENT
    ... DTSTART;TZID=America/New_York:20200401T180000
    ... END:VEVENT
    ... BEGIN:VEVENT
    ... DTSTART;TZID=W. Europe Standard Time:20200401T180000
    ... END:VEVENT
    ... END:VCALENDAR
    ... """.strip())
    >>> cal.events[0].begin
    datetime.datetime(2020, 4, 1, 18, 0, tzinfo=Timezone.from_tzid('/ics.py/2020.1/America/New_York'))
    >>> cal.events[1].begin # english windows timezone names work, too
    datetime.datetime(2020, 4, 1, 18, 0, tzinfo=Timezone.from_tzid('/ics.py/2020.1/Europe/Berlin'))
    >>> Calendar("""
    ... BEGIN:VCALENDAR
    ... VERSION:2.0
    ... PRODID:Some Software that doesn't write vTimezones
    ... BEGIN:VEVENT
    ... DTSTART;TZID=Mitteleuropäische Sommerzeit:20200401T180000
    ... END:VEVENT
    ... END:VCALENDAR
    ... """.strip())  # localized ones unfortunately don't  # doctest: +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
    ...
    ValueError: no vTimezone.ics file found for Mitteleuropäische Sommerzeit
    <BLANKLINE>
    During handling of the above exception, another exception occurred:
    <BLANKLINE>
    Traceback (most recent call last):
    ...
    ValueError: timezone Mitteleuropäische Sommerzeit is unknown on this system ...

Converting to the builtin vTimezone definition
----------------------------------------------

Additionally, it allows you to convert vTimezone objects from an external source to the ``ics.py`` version, warning you if the definitions differ
and this conversion would lead to some timestamps being interpreted differently.
This is especially useful if you are merging ics files from multiple different sources and want to normalize their timezone representations and remove duplicate definitions.

::

    >>> citadel = """
    ... BEGIN:VTIMEZONE
    ... TZID:/citadel.org/20190914_1/America/New_York
    ... LAST-MODIFIED:20190914T160252Z
    ... X-LIC-LOCATION:America/New_York
    ... BEGIN:DAYLIGHT
    ... TZNAME:EDT
    ... TZOFFSETFROM:-0500
    ... TZOFFSETTO:-0400
    ... DTSTART:19700308T020000
    ... RRULE:FREQ=YEARLY;BYMONTH=3;BYDAY=2SU
    ... END:DAYLIGHT
    ... BEGIN:STANDARD
    ... TZNAME:EST
    ... TZOFFSETFROM:-0400
    ... TZOFFSETTO:-0500
    ... DTSTART:19701101T020000
    ... RRULE:FREQ=YEARLY;BYMONTH=11;BYDAY=1SU
    ... END:STANDARD
    ... END:VTIMEZONE
    ... """.strip()
    >>> from ics.contentline import string_to_container
    >>> tz = Timezone.from_container(string_to_container(citadel))
    >>> tz  # doctest: +SKIP
    Timezone('/citadel.org/20190914_1/America/New_York', observances=[
        TimezoneDaylightObservance(extra=Container('DAYLIGHT', []), extra_params={},
            tzoffsetfrom=datetime.timedelta(days=-1, seconds=68400),
            tzoffsetto=datetime.timedelta(days=-1, seconds=72000),
            rrule=rruleset(
                rrule=[rrule(
                    'interval'=1, 'count'=None,
                    'dtstart'=datetime.datetime(1970, 3, 8, 2, 0),
                    'freq'=0, 'until'=None, 'wkst'=0,
                    'bymonth'=(3,), 'byweekday'=(SU(+2),))],
                exrule=[], rdate=[datetime.datetime(1970, 3, 8, 2, 0)], exdate=[]),
            tzname='EDT', comment=None),
        TimezoneStandardObservance(extra=Container('STANDARD', []), extra_params={},
            tzoffsetfrom=datetime.timedelta(days=-1, seconds=72000),
            tzoffsetto=datetime.timedelta(days=-1, seconds=68400),
            rrule=rruleset(
                rrule=[rrule(
                    'interval'=1, 'count'=None,
                    'dtstart'=datetime.datetime(1970, 11, 1, 2, 0),
                    'freq'=0, 'until'=None, 'wkst'=0,
                    'bymonth'=(11,), 'byweekday'=(SU(+1),))],
                exrule=[], rdate=[datetime.datetime(1970, 11, 1, 2, 0)], exdate=[]),
            tzname='EST', comment=None)])
    >>> tz.to_builtin()
    Timezone.from_tzid('/ics.py/2020.1/America/New_York')
    >>> tz.to_builtin().observances == tz.observances
    True
