Quickstart
==========

.. meta::
   :keywords: quickstart

.. topic:: Abstract

   In this document, we show you how to make first contact with ics.py.

.. contents::  Content
   :local:


Conventions
-----------

c = ics.Calendar()
e = ics.Event()

Importing a Calendar from a File
--------------------------------

.. code-block:: python

    from ics import Calendar
    import requests

    url = "https://urlab.be/events/urlab.ics"
    c = Calendar(requests.get(url).text)

    c
    # <Calendar with 118 events and 0 todo>
    c.events
    # {<Event 'Visite de "Fab Bike"' begin:2016-06-21T15:00:00+00:00 end:2016-06-21T17:00:00+00:00>,
    # <Event 'Le lundi de l'embarqué: Adventure in Espressif Non OS SDK edition' begin:2018-02-19T17:00:00+00:00 end:2018-02-19T22:00:00+00:00>,
    #  ...}
    e = list(c.timeline)[0]
    "Event '{}' started {}".format(e.name, e.begin.humanize())
    # "Event 'Workshop Git' started 2 years ago"


Creating a new Calendar and Add Events
--------------------------------------

.. code-block:: python

    from ics import Calendar, Event
    c = Calendar()
    e = Event()
    e.name = "My cool event"
    e.begin = '2014-01-01 00:00:00'
    c.events.add(e)
    c.events
    # {<Event 'My cool event' begin:2014-01-01 00:00:00 end:2014-01-01 00:00:01>}

Get event datetime object details
---------------------------------

.. code-block:: python

   e.cmp_tuple()
   # (datetime.datetime(2022, 6, 6, 12, 5, 23, tzinfo=datetime.timezone(datetime.timedelta(seconds=7200))), datetime.datetime(2022, 6, 6, 13, 5, 23, tzinfo=datetime.timezone(datetime.timedelta(seconds=7200))), 'My cool event')

Exporting a Calendar to a File
------------------------------

.. code-block:: python

    with open('my.ics', 'w') as f:
        f.write(c)
    # And it's done !

    # iCalendar-formatted data is also available in a string
    str(c)
    # 'BEGIN:VCALENDAR\nPRODID:...
