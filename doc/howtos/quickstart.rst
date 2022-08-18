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

.. code-block:: python

 c = ics.Calendar()
 e = ics.Event()
 a = ics.Attendee()

Importing a Calendar from a URL
--------------------------------

Download the calender file through requests or any other library.
Error handling is recommended.

.. code-block:: python

 from ics import Calendar
 import requests

 url = "https://urlab.be/events/urlab.ics"
 try:
     c = Calendar(requests.get(url).text)
 except Exception as e:
     print(e)

 print(c)
 # <Calendar with 118 events and 0 todo>
 print(c.events[2])
 # <Event 'TechMardi 20/2015' begin: 2015-12-08 17:30:00+00:00 fixed end: 2015-12-08 22:00:00+00:00 duration: 4:30:00>
 e = list(c.timeline)[0]
 print("Event '{}' started {}".format(e.summary, e.begin))
 # Event 'Workshop Git' started 2015-11-16 17:30:00+00:00

Creating a new Calendar and Add Events
--------------------------------------

:class:`Calendar` objects each represent an unique RFC 5545 iCalendar. They contain :class:`Event`, :class:`Todo` and :class:`Timeline` iterators.

Time and date are represented as :class:`datetime` objects and can be expressed as ISO 8601 strings or with the class constructor.

.. code-block:: python

 from datetime import datetime, timezone, timedelta
 from ics import Calendar, Event

 c = Calendar()
 e = Event()
 e.summary = "My cool event"
 e.description = "A meaningful description"
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
 c.events.append(e)
 c
 # Calendar(extra=Container('VCALENDAR', []), extra_params={}, version='2.0', prodid='ics.py 0.8.0-dev - http://git.io/lLljaA', scale=None, method=None, events=[Event(extra=Container('VEVENT', []), extra_params={}, timespan=EventTimespan(begin_time=datetime.datetime(2022, 6, 6, 12, 5, 23, tzinfo=datetime.timezone(datetime.timedelta(seconds=7200))), end_time=datetime.datetime(2022, 6, 6, 12, 5, 23, tzinfo=datetime.timezone(datetime.timedelta(seconds=7200))), duration=None, precision='second'), summary='My cool event', uid='e10e6921-5838-4dab-9467-fffcb8091cc3@e10e.org', description='A meaningful description', location=None, url=None, status=None, created=None, last_modified=None, dtstamp=datetime.datetime(2022, 6, 30, 12, 41, 24, 624188, tzinfo=Timezone.from_tzid('UTC')), alarms=[], attach=[], classification=None, transparent=None, organizer=None, geo=None, attendees=[], categories=[])], todos=[])

Get event datetime object details
---------------------------------

.. code-block:: python

 e.cmp_tuple()
 # (datetime.datetime(2022, 6, 6, 12, 5, 23, tzinfo=datetime.timezone(datetime.timedelta(seconds=7200))), datetime.datetime(2022, 6, 6, 13, 5, 23, tzinfo=datetime.timezone(datetime.timedelta(seconds=7200))), 'My cool event')

Converting to all-day event
---------------------------

Transforms event to a rounded-up all-day event.

.. code-block:: python

 e.cmp_tuple()
 # (datetime.datetime(2022, 6, 6, 12, 5, 23, tzinfo=datetime.timezone(datetime.timedelta(seconds=7200))), datetime.datetime(2022, 6, 6, 13, 5, 23, tzinfo=datetime.timezone(datetime.timedelta(seconds=7200))), 'My cool event')
 e.make_all_day()
 e.cmp_tuple()
 # (datetime.datetime(2022, 6, 6, 0, 0, tzinfo=tzlocal()), datetime.datetime(2022, 6, 7, 0, 0, tzinfo=tzlocal()), 'My cool event')


Exporting a calendar to a file
------------------------------

.. code-block:: python

 with open("my.ics", "w") as f:
     f.write(c.serialize())

Managing attendees
------------------

* Adding attendees

.. code-block:: python

 from ics import Attendee

 a = Attendee("all@organization.com")
 e.add_attendee(a)
 e.attendees
 # [Attendee(email='all@organization.com', extra={})]

* Modifying attendees, find all possible attributes and values in :class:`Attendee`

.. code-block:: python

 e.attendees
 # [Attendee(email='all@organization.com', extra={})]
 e.attendees[0].common_name = "ALL"
 e.attendees
 # [Attendee(email='all@organization.com', extra={'CN': ['ALL']})]

* Removing attendees

.. code-block:: python

 e.attendees
 # [Attendee(email='all@organization.com', extra={'CN': ['ALL']})]
 del e.attendees[0]
 e.attendees
 # []
