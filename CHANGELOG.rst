============
Ics.py changelog
============

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
