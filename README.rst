Ics.py : iCalendar for Humans
=============================

`Original repository <https://github.com/C4ptainCrunch/ics.py>`_ (GitHub) - `Bugtracker and issues <https://github.com/C4ptainCrunch/ics.py/issues>`_ (GitHub) - `PyPi package <https://pypi.python.org/pypi/ics/>`_ (ics) - `Documentation <http://icspy.readthedocs.org/>`_ (Read The Docs).

.. image:: https://travis-ci.org/C4ptainCrunch/ics.py.png?branch=master
   :target: https://travis-ci.org/C4ptainCrunch/ics.py

.. image:: https://coveralls.io/repos/C4ptainCrunch/ics.py/badge.png
   :target: https://coveralls.io/r/C4ptainCrunch/ics.py
   :alt: Coverage

.. image:: https://pypip.in/license/ics/badge.png
    :target: https://pypi.python.org/pypi/ics/
    :alt: Apache 2 License


Ics.py is a pythonic and easy iCalendar (rfc5545) library. It's goals are to read and write ics data in a developper-friendly way.

Ics.py is available for Python2 (>=2.7) *and* Python3 (>=3.3) and is Apache2 Licensed.

iCalendar is complicated, you don't like RFCs but you want/have to use the ics format and you love pythonic APIs?
Ics.py is for you!


Quickstart
----------

.. code-block:: bash

    $ pip install ics



.. code-block:: python

    >>> from ics import Calendar, Event
    >>> c = Calendar()
    >>> e = Event()
    >>> e.name = "My cool event"
    >>> e.begin = '20140101 00:00:00'
    >>> c.events.append(e)
    >>> c.events
    [<Event 'My cool event' begin:2014-01-01 00:00:00 end:2014-01-01 00:00:01>]

More examples are available in the `documentation <http://icspy.readthedocs.org/>`_.

Documentation
-------------

All the documentation (examples, api, about…) is hosted on readthedocs.org and is updated automaticaly at every commit.
Go and `get it <http://icspy.readthedocs.org/>`_!


Contribute
----------

Contribution are welcome of course! More info over `there <https://github.com/C4ptainCrunch/ics.py/blob/master/CONTRIBUTING.rst>`_ (or in the doc).


Links
-----
`Rfc5545 <http://tools.ietf.org/html/rfc5545>`_- `Vulgarisated RFC <http://www.kanzaki.com/docs/ical/>`_

.. image:: https://i.imgur.com/8iYDvvy.jpg
    :target: https://github.com/C4ptainCrunch/ics.py
    :alt: Parse ALL the calendars !