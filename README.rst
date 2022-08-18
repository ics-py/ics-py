ics.py `0.8.0-dev0` : iCalendar for Humans
==========================================

`Original repository <https://github.com/ics-py/ics-py>`_ (GitHub) -
`Bugtracker and issues <https://github.com/ics-py/ics-py/issues>`_ (GitHub) -
`PyPi package <https://pypi.python.org/pypi/ics/>`_ (ics) -
`Documentation <http://icspy.readthedocs.org/>`_ (Read The Docs).


.. image:: https://img.shields.io/github/license/ics-py/ics-py.svg
    :target: https://pypi.python.org/pypi/ics/
    :alt: Apache 2 License


Ics.py is a pythonic and easy iCalendar library.
Its goals are to read and write ics data in a developer friendly way.

iCalendar is a widely-used and useful format but not user friendly.
Ics.py is there to give you the ability of creating and reading this
format without any knowledge of it.

It should be able to parse every calendar that respects the
`rfc5545 <http://tools.ietf.org/html/rfc5545>`_ and maybe some more…
It also outputs rfc compliant calendars.

iCalendar (file extension `.ics`) is used by Google Calendar,
Apple Calendar, Android and many more.


Ics.py is available for Python 3.7, 3.8, 3.9, 3.10, 3.11 and is Apache2 Licensed.



Quickstart
----------

.. code-block:: bash

    $ pip install ics

.. code-block:: python

 from datetime import datetime
 from ics import Calendar, Event

 c = Calendar()
 e = Event()
 e.summary = "My cool event"
 e.description = "A meaningful description"
 e.begin = datetime.fromisoformat("2022-06-06T12:05:23+02:00")
 e.end = datetime.fromisoformat("2022-06-06T13:05:23+02:00")
 c.events.append(e)
 c
 # Calendar(extra=Container('VCALENDAR', []), extra_params={}, version='2.0', prodid='ics.py 0.8.0-dev0 - http://git.io/lLljaA', scale=None, method=None, events=[Event(extra=Container('VEVENT', []), extra_params={}, timespan=EventTimespan(begin_time=datetime.datetime(2022, 6, 6, 12, 5, 23, tzinfo=datetime.timezone(datetime.timedelta(seconds=7200))), end_time=None, duration=None, precision='second'), summary=None, uid='ed7975c7-01f1-42eb-bfc4-435afd76b33d@ed79.org', description=None, location=None, url=None, status=None, created=None, last_modified=None, dtstamp=datetime.datetime(2022, 6, 6, 19, 28, 14, 575558, tzinfo=Timezone.from_tzid('UTC')), alarms=[], attach=[], classification=None, transparent=None, organizer=None, geo=None, attendees=[], categories=[])], todos=[])
 with open("my.ics", "w") as f:
     f.write(c.serialize())

More examples are available in the
`documentation <http://icspy.readthedocs.org/>`_.

Documentation
-------------

All the `documentation <http://icspy.readthedocs.org/>`_ is hosted on
`readthedocs.org <http://readthedocs.org/>`_ and is updated automatically
at every commit.

* `Quickstart <http://icspy.readthedocs.org/>`_
* `API <https://icspy.readthedocs.io/en/stable/api.html>`_
* `About <https://icspy.readthedocs.io/en/stable/about.html>`_


Contribute
----------

Contribution are welcome of course! For more information and how to setup, see
`contributing <https://github.com/ics-py/ics-py/blob/master/CONTRIBUTING.rst>`_.



Links
-----
* `rfc5545 <http://tools.ietf.org/html/rfc5545>`_
* `Vulgarised RFC <http://www.kanzaki.com/docs/ical/>`_

.. image:: http://i.imgur.com/KnSQg48.jpg
    :target: https://github.com/ics-py/ics-py
    :alt: Parse ALL the calendars!
    :align: center
