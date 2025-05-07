=========
Changelog
=========

*Major releases are named in honor of influential women who shaped modern computer technology*

All notable changes to this project will be documented in this file.

The format is based on `Keep a Changelog <https://keepachangelog.com/en/1.0.0/>`_,
and this project adheres to `Semantic Versioning <https://semver.org/spec/v2.0.0.html>`_.


***************************
0.8 (in dev) - Grace Hopper
***************************

*Grace Hopper was mathematician and rear admiral who was a pioneer in developing computer technology,
helping to devise UNIVAC I, the first commercial electronic computer and FLOW-MATIC on which COBOL was based*.

This is a major release in the life of ics.py as it fixes a lot of long standing
(design) issues with timespans, removes `arrow` and introduces `attrs`.
Thank you @N-Coder for the huge work you put in this!

What's new in 0.8?
------------------

**Lists instead of sets**

`Calendar.events`, `Calendar.todos`, `Event.attendees` and `Event.alarms` are now all instances of `list` instead
`set` in order to keep the order they had in the original ics file.
Use `.append()` instead of `.add()` to insert new entries.
Example:

.. code-block:: python

 c = Calendar()
 e = Event()
 e.summary = "My cool event"
 c.events.append(e)

**Serialization**

`Calendar`, `Event`, ... have a new string / serialization behaviour:

- `__repr__` returns a full, valid python representation, is fast and can't throw exceptions
- `__str__` returns a short human-readable description, is fast and can't throw exceptions
- `serialize` returns the full RFC5545 ics representation is string form, is still pretty fast and usually shouldn't
  throw exceptions (except for when you pass in data that can't be serialized, this potentially includes old
  `Arrow` instances)
This means that for example to write a `Calendar` to a file, you should do something like:

.. code-block:: python

 c = ics.Calendar()
 with open("my.ics", "w") as f:
     f.write(c.serialize())

**Removal of `arrow`**

Our dependency on `arrow` is now removed. Please now exclusively use built-in `datetime` and `timedelta` instead.
Example:

.. code-block:: python

 e = Event()
 e.begin = datetime.fromisoformat("2022-06-06T12:05:23+02:00")
 e.end = datetime(
     year=2022,
     month=6,
     day=6,
     hour=12,
     minute=5,
     second=23,
     tzinfo=timezone(timedelta(seconds=7200)),
 )

Exhaustive list
---------------

**Added**
 - Support for parsing and serializing timezones
 - `Calendar` constructor / parse methods
 - Support for Python 3.12 and 3.13
 - Dependency on `attrs`. `Calendar`, `Event`, ... are all now `attrs` classes.

**Changed**
 - New string / serialization behaviour (see above)
 - Renamed `Event.name` to `Event.summary`
 - Some attributes now have further validators that restrict which values they can be set to
 - `Event.attendees` and `Event.organizer` now must be instances of the respective classes, plain strings with the e-mail
   are no longer allowed
 - To avoid user error, `extra` can now only contain nested `Container` and `ContentLine`, no plain strings
 - The method `Event.has_end()` has been removed in favor if now property `Event.has_explicit_end` as any the RFC
   says that every `Event` with a begin time has an end.

**Removed**
 - Support for `EOL <https://devguide.python.org/versions/>`_ Python 3.8 and below
 - Dependency on `arrow` (see above)
 - `Calendar._timezones` attribute
 - `Event.join()`

**Fixed**
 - Fix all-day issues
 - Fix timezone issues
 - Fix SEQUENCE bug

**Internal changes**
 - `ics.grammar.parse` has been moved to `ics.grammar`.
 - The inner `Meta` classes were replaced by a single `NAME` class attribute
 - The `Component` conversion methods are now called `from_container` and `to_container`.
 - For `ContentLine`/`Container` there's now a `serialize` method to convert them to ics strings.
 - Introduced Timespan
 - `dtstamp` and `created` have been separated, `dtstamp` is the only one set automatically

*****
0.7.2
*****

This is a bugfix release.

Bug fix:
 - Add a lower bound (`>=19.1.0`) on the required version of
   `attrs` `#353 <https://github.com/ics-py/ics-py/issues/353>`_ (bug introduced in 0.7.1)


*****
0.7.1
*****

This release contains a few minor changes and introduces deprecations for
features that will be removed in 0.8.

Deprecation:
 - Add warnings about breaking changes in v0.8 to `Calendar.str()` and `.iter()`.

Minor changes:
 - Add a dependency on `attrs <https://pypi.org/project/attrs/>`_.
 - Remove the upper bound on the version of `arrow <https://pypi.org/project/arrow/>`_.
 - Backport optimizations for TatSu parser from 0.8

Bug fix:
 - Fix "falsey" (`bool(x) is False`) alarm trigger (i.e. `timedelta(0)`) not being serialized
   `#269 <https://github.com/ics-py/ics-py/issues/269>`_

Known bugs:
 - Missing lower bound on the required version of `attrs` (`>=19.1.0`) `#353 <https://github.com/ics-py/ics-py/issues/353>`_

***********************
0.7 - Katherine Johnson
***********************

*Katherine Johnson was a mathematician whose calculations of orbital mechanics at NASA
were critical to the success of the firsts crewed spaceflights.
She helped pioneer the use of computers to perform these tasks at NASA.*

Special thanks to @N-Coder for making 0.7 happen!

Breaking changes:
 - Remove useless `day` argument from `Timeline.today()`
 - Attendee and Organizer attributes are now classes and can not be set to `str`.

Minor changes:
 - Add support for Python 3.8
 - Ensure `VERSION` is the first line of a `VCALENDAR` and `PRODID` is second.

Bug fixes:
 - Fix regression in the support of emojis (and other unicode chars) while
   parsing. (Thanks @Azhrei)
 - Fix a bug preventing an EmailAlarm to be instantiated
 - Fix multiple bugs in Organizer and Attendees properties.
   (See #207, #209, #217, #218)

*******************
0.6 - Sophie Wilson
*******************

*Sophie Wilson is an computer scientist who was instrumental in designing the
BBC Micro, including the BBC BASIC language, and the ARM instruction set*

Major changes:
 - Drop support for Python 3.5. Python 3.7 is now distributed in both Ubuntu LTS
   and Debian stable, the PSF is providing only security fixes for 3.5. It's time
   to move on !
 - Add `竜 TatSu <https://pypi.org/project/TatSu/>`_ as a dependency.
   This enables us to have a real PEG parser and not a combination of
   regexes and string splitting.
 - The previously private `._unused` is now renamed to public `.extra` and
   becomes documented.
 - The Alarms have been deeply refactored (see the docs for more detail) and
   many bugs have been fixed.

Minor changes:
 - Add mypy
 - Add GEO (thanks @johnnoone !)
 - `Calendar.parse_multiple()` now accepts streams of multiple calendars.
 - `Calendar()` does not accept iterables to be parsed anymore (only a single
   string)
 - Add support for classification (#177, thanks @PascalBru !)
 - Support arrow up to <0.15
 - Cleanup the logic for component parsers/serializers: they are now in their own
   files and are registered via the `Meta` class

Bug fixes:
 - Events no longer have the TRANSP property by default (Fixes #190)
 - Fix parsing of quoted values as well as escaped semi-columns (#185 and #193)


********************
0.5 - Adele Goldberg
********************

*Adele Goldberg is a computer scientist who participated in developing Smalltalk-80 and
various concepts related to object-oriented programming while working as a researcher at Xerox.*

This is the first version to be Python 3 only.

This release happens a bit more than a year after the previous one and was made to
distribute latest changes to everyone and remove the confusion between master and PyPi.

Please note that it may contain (lot of) bugs and not be fully polished.
This is still alpha quality software!

Highlights and breaking changes:
 - Drop support for Python 2, support Python from 3.5 to 3.8
 - Upgrade arrow to 0.11 and fix internal call to arrow to specify the string
   format (thanks @muffl0n, @e-c-d and @chauffer)

Additions:
 - LAST-MODIFIED attribute support (thanks @Timic3)
 - Support for Organizers to Events (thanks @danieltellez and kayluhb)
 - Support for Attendees to Events (thanks @danieltellez and kayluhb)
 - Support for Event and Todo status (thanks @johnnoone)

Bug fixes:
 - Fix all-day events lasting multiple days by using a DTEND with a date and not a datetime (thanks @raspbeguy)
 - Fix off by one error on the DTEND on all day events (issues #92 and #150)
 - Fix SEQUENCE in VTIMEZONE error
 - Fixed NONE type support for Alarms (thanks @zagnut007)

Known issues:
 - There are known problems with all-day events. This GitHub issue summarizes them
   well: https://github.com/ics-py/ics-py/issues/155. You can expect them to
   be fixed in 0.6 but not before.

Misc:
 - Improve TRIGGER DURATION parsing logic (thanks @jessejoe)
 - Event equality now checks all fields (except uid)
 - Alarms in Event and Todo are now consistently lists and not a mix between set() and list()

Thanks also to @t00n, @aureooms, @chauffer, @seants, @davidjb, @xaratustrah, @Philiptpp

**************************
0.4 - Elizabeth J. Feinler
**************************

*Elizabeth J. Feinler is an information scientist. She led the NIC for the ARPANET
as it evolved into the Defense Data Network (DDN) and then the Internet.*

Last version to support Python 2.7 and 3.3.

This version is by far the one with the most contributors, thank you !

Highlights:
 - Todo/VTODO support (thanks @tgamauf)
 - Add event arithmetics (thanks @guyzmo)
 - Support for alarms/`VALARM` (thanks @rkeilty)
 - Support for categories (thanks @perette)

Misc:
 - Make the parser work with tabbed whitespace (thanks @mrmadcow)
 - Better error messages (thanks @guyzmo)
 - Support input with missing `VERSION` (thanks @prashnts)
 - Support for Time Transparency/`TRANSP` (thanks @GMLudo)
 - All day events not omit the timezone (thanks @Trii)
 - Multi-day events fixes (thanks @ConnyOnny)
 - Fix `TZID` drop when `VTIMEZONE` is empty (thanks @ConnyOnny)
 - Better test coverage (thanks @aureooms)

Breaking Changes:
 - Removed EventList class

Thank you also to @davidjb, @etnarek, @jammon

*******
0.3.1
*******
 - Pin arrow to 0.4.2

*****
0.3
*****
 - Events in an `EventList()` are now always sorted
 - Freeze the version of Arrow (they made backwards-incompatible changes)
 - Add a lot of tests
 - Lots of small bug fixes

*******
0.1.3
*******
- FIX : broken install. Again.

*******
0.1.2
*******
 - FIX : broken install

*******
0.1.1
*******
 - FIX : wrong `super()` and add output documentation

****
0.1
****
 - First version
