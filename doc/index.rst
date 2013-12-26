.. ics.py documentation master file, created by
   sphinx-quickstart on Thu Dec 26 11:05:27 2013.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Ics.py : iCalendar for Humans
=============================

(Release |version|)

Ics.py is an :ref:`Apache2 Licensed <apache2>` iCalendar (rfc5545) library, written in Python 2 & 3, for human beings.

Quickstart
----------


Install using `pip <http://www.pip-installer.org/>`_ (or :ref:`another method <installation>`).
::

    $ pip install requests


Import a calendar from a file
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    from ics import Calendar
    from urllib2 import urlopen
    url = "http://hackeragenda.urlab.be/events/events.ics"
    c = Calendar(urlopen(url).read().decode('iso-8859-1'))
    c
    >>> <Calendar with 42 events>

    c.events
    >>> [<Event 'SmartMonday #1' begin:2013-12-13 20:00:00 end:2013-12-13 23:00:00>,
    >>> <Event 'RFID workshop' begin:2013-12-06 12:00:00 end:2013-12-06 19:00:00>,
    >>> ...]

    e = c.events[10]

    "Event '{}' started {}".format(e.name, e.begin.humanize())
    >>> "Event 'Mitch Altman soldering workshop' started 6 days ago"


Create a new calendar and add events
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    c = Calendar()
    e = Event()
    e.name = "My cool event"
    e.begin = '20140101 00:00:00'
    c.events.append(e)

    c.events
    >>> [<Event 'My cool event' begin:2014-01-01 00:00:00 end:2014-01-01 00:00:01>]


API
===

.. autoclass:: ics.icalendar.Calendar
    :members:
    :special-members: __unicode__, __init__

.. autoclass:: ics.event.Event
    :members:
    :special-members: __unicode__, __init__

.. autoclass:: ics.eventlist.EventList
    :members:
    :special-members: __getitem__, __init__


.. Contents:

.. .. toctree::
..    :maxdepth: 2



.. Indices and tables
.. ==================

.. * :ref:`genindex`
.. * :ref:`modindex`
.. * :ref:`search`

