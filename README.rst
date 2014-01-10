Ics.py : iCalendar for Humans
=============================

.. image:: https://travis-ci.org/C4ptainCrunch/ics.py.png?branch=master
   :target: https://travis-ci.org/C4ptainCrunch/ics.py

.. image:: https://coveralls.io/repos/C4ptainCrunch/ics.py/badge.png
   :target: https://coveralls.io/r/C4ptainCrunch/ics.py

.. image:: https://pypip.in/license/ics/badge.png
    :target: https://pypi.python.org/pypi/ics/
    :alt: License

.. image:: http://b.repl.ca/v1/Awesomeness-9000+-FD6C9E.png
    :target: https://pypi.python.org/pypi/ics/
    :alt: Awesomeness


(Release 0.1.1)

Ics.py is a pythonic and easy iCalendar (rfc5545) library. It's goals are to read and write ics data in a developper-friendly way.

It is written in Python (>=2.7 and >=3.3) and is Apache2 Licensed.

iCalendar is complicated, you don't like RFCs but you want/have to use the ics format and you love pythonic APIs? ics.py is for you!

Quickstart
==========


.. code-block:: bash

    $ pip install ics


Import a calendar from a file
-----------------------------

.. code-block:: pycon

    >>> from ics import Calendar
    >>> from urllib2 import urlopen # import requests
    >>> url = "http://hackeragenda.urlab.be/events/events.ics"
    >>> c = Calendar(urlopen(url).read().decode('iso-8859-1'))
    >>> # could also use 'requests' here
    >>> # c = Calendar(requests.get(url).text)
    >>> c
    <Calendar with 42 events>

    >>> c.events
    [<Event 'SmartMonday #1' begin:2013-12-13 20:00:00 end:2013-12-13 23:00:00>,
    <Event 'RFID workshop' begin:2013-12-06 12:00:00 end:2013-12-06 19:00:00>,
    ...]

    >>> e = c.events[10]

    >>> "Event '{}' started {}".format(e.name, e.begin.humanize())
    "Event 'Mitch Altman soldering workshop' started 6 days ago"


Create a new calendar and add events
------------------------------------


.. code-block:: pycon

    >>> from ics import Calendar, Event
    >>> c = Calendar()
    >>> e = Event()
    >>> e.name = "My cool event"
    >>> e.begin = '20140101 00:00:00'
    >>> c.events.append(e)

    >>> c.events
    [<Event 'My cool event' begin:2014-01-01 00:00:00 end:2014-01-01 00:00:01>]

Export a Calendar to a file
---------------------------

.. code-block:: pycon

    >>> with open('my.ics', 'w') as f:
    >>>     f.writelines(c)
    >>> # And it's done !

iCalendar-formatted data is also available in a string

.. code-block:: pycon

    >>> str(c)
    'BEGIN:VCALENDAR\nPRODID:...


License
=======
ics.py is under the Apache 2 software license because… bah! Why not?

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
