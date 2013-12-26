ics.py
======

ics.py is a Python (2 and 3) icalendar (rfc5545) parser.

examples
========
.. code-block:: python

	from ics import Calendar
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


License
-------
ics.py is under the Apache 2 software license because... bah ! Why not ?

	Copyright 2013 Nikita Marchant

	Licensed under the Apache License, Version 2.0 (the "License");
	you may not use this file except in compliance with the License.
	You may obtain a copy of the License at

	http://www.apache.org/licenses/LICENSE-2.0

	Unless required by applicable law or agreed to in writing, software
	distributed under the License is distributed on an "AS IS" BASIS,
	WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
	See the License for the specific language governing permissions and
	limitations under the License.

ics.py uses heavily arrow (Apache license) and python-dateutil (GPL licensed).

ics.py includes also something like 10 lines of arrow's code (in utils.iso_precision) which are ©Chris Smith. Thanks to him!