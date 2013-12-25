ics.py
======

ics.py is a Python (2 and 3) icalendar (rfc5545) parser.

examples
========
.. code-block:: python

	from icalendar import Calendar
	from urllib2 import urlopen
	url = "http://hackeragenda.urlab.be/events/events.ics"
	c = Calendar(urlopen(url).read().decode('iso-8859-1'))
	c
	>>> <icalendar.Calendar at 0x10c00e210>

	c.events
	>>> [<icalendar.Event at 0x10c00e350>,
	>>> <icalendar.Event at 0x10c00e3d0>,
	>>> <icalendar.Event at 0x10c00e490>]

	e = c.events[10]

	e.begin, e.end
	>>> (<Arrow [2012-11-28T19:00:00+00:00]>, <Arrow [2012-11-28T12:00:00+00:00]>)

	"Event '{}' started {}".format(e.name, e.begin.humanize())
	>>> "Event 'Special guest: Mitch Altman [voidwarranties]' started a year ago"


You may also create new calendars and events

.. code-block:: python

	c = Calendar()
	c.creator =  "ics.py by C4"

	e = Event()
	e.name = "My cool event"
	c.events.append(e)

	c.events
	>>> [<icalendar.Event at 0x10573b390>]