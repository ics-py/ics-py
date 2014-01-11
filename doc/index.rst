.. ics.py documentation master file, created by
   sphinx-quickstart on Thu Dec 26 11:05:27 2013.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Ics.py : iCalendar for Humans
=============================

(Release |version|)

Ics.py is a pythonic and easy iCalendar (rfc5545) library. It's goals are to read and write ics data in a developper-friendly way.

It is written in Python (>=2.7 and >=3.3) and is  :ref:`Apache2 Licensed <apache2>`.

iCalendar is complicated, you don't like RFCs but you want/have to use the ics format and you love pythonic APIs? ics.py is for you!

Quickstart
==========


Install using `pip <http://www.pip-installer.org/>`_ (or :ref:`another method <installation>`).
::

    $ pip install ics


Import a calendar from a file
-----------------------------

.. code-block:: pycon \

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


.. code-block:: pycon \

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

.. code-block:: pycon \

>>> with open('my.ics', 'w') as f:
>>>     f.writelines(c)
>>> # And it's done !

iCalendar-formatted data is also available in a string

.. code-block:: pycon \
>>> str(c)
'BEGIN:VCALENDAR\nPRODID:...




Guide
=====

.. toctree::
   :maxdepth: 2

   installation
   api
   about

* :ref:`genindex`
* :ref:`search`