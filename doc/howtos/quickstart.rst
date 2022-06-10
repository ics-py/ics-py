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

:class:`Calendar` objects each represent an unique RFC 5545 iCalendar. They contain :class:`Event`, :class:`Todo` and :class:`Timeline` iterators.

Time and date are represented as :class:`datetime` objects.

.. code-block:: python

 from datetime import datetime
 from ics import Calendar, Event
 c = Calendar()
 e = Event()
 e.summary = "My cool event"
 e.description = "A meaningful description"
 e.begin = datetime.fromisoformat('2022-06-06T12:05:23+02:00')
 e.end = datetime.fromisoformat('2022-06-06T13:05:23+02:00')
 c.events.append(e)
 c
 # Calendar(extra=Container('VCALENDAR', []), extra_params={}, version='2.0', prodid='ics.py 0.8.0-dev - http://git.io/lLljaA', scale=None, method=None, events=[Event(extra=Container('VEVENT', []), extra_params={}, timespan=EventTimespan(begin_time=datetime.datetime(2022, 6, 6, 12, 5, 23, tzinfo=datetime.timezone(datetime.timedelta(seconds=7200))), end_time=None, duration=None, precision='second'), summary=None, uid='ed7975c7-01f1-42eb-bfc4-435afd76b33d@ed79.org', description=None, location=None, url=None, status=None, created=None, last_modified=None, dtstamp=datetime.datetime(2022, 6, 6, 19, 28, 14, 575558, tzinfo=Timezone.from_tzid('UTC')), alarms=[], attach=[], classification=None, transparent=None, organizer=None, geo=None, attendees=[], categories=[])], todos=[])

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

 with open('my.ics', 'w') as f:
     f.write(c.serialize())

Managing attendees
------------------

Adding attendees

.. code-block:: python

 from ics import Attendee
 a = Attendee('all@organization.com')
 e.add_attendee(a)
 e.attendees
 # [Attendee(email='all@organization.com', extra={})]

Modifying attendees, find all possible attributes and values in :class:`Attendee`

.. code-block:: python

 e.attendees
 # [Attendee(email='all@organization.com', extra={})]
 e.attendees[0].common_name = 'ALL'
 e.attendees
 # [Attendee(email='all@organization.com', extra={'CN': ['ALL']})]

Removing attendees

.. code-block:: python

 e.attendees
 # [Attendee(email='all@organization.com', extra={'CN': ['ALL']})]
 del e.attendees[0]
 e.attendees
 # []
