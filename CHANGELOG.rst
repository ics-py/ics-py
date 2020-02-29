============
Ics.py changelog
============


**************
0.7
**************

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

**************
0.6
**************

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


**************
0.5
**************

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
   well: https://github.com/C4ptainCrunch/ics.py/issues/155. You can expect them to
   be fixed in 0.6 but not before.

Misc:
 - Improve TRIGGER DURATION parsing logic (thanks @jessejoe)
 - Event equality now checks all fields (except uid)
 - Alarms in Event and Todo are now consistently lists and not a mix between set() and list()

Thanks also to @t00n, @aureooms, @chauffer, @seants, @davidjb, @xaratustrah, @Philiptpp

**************
0.4
**************

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
 - Lots of small bugfixes

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
