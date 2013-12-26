.. ics.py documentation master file, created by
   sphinx-quickstart on Thu Dec 26 11:05:27 2013.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Ics.py : iCalendar for Humans
=============================

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
	>>> (<Arrow [2012-11-28T19:00:00+00:00]>,
	>>> <Arrow [2012-11-28T12:00:00+00:00]>)

	"Event '{}' started {}".format(e.name, e.begin.humanize())
	>>> "Event 'Mitch Altman @voidwarranties' started a year ago"


You may also create new calendars and events

.. code-block:: python

	c = Calendar()
	c.creator =  "ics.py by C4"

	e = Event()
	e.name = "My cool event"
	c.events.append(e)

	c.events
	>>> [<icalendar.Event at 0x10573b390>]


.. Contents:

.. .. toctree::
..    :maxdepth: 2



.. Indices and tables
.. ==================

.. * :ref:`genindex`
.. * :ref:`modindex`
.. * :ref:`search`

