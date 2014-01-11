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

There are a more of examples in the `documentation <http://icspy.readthedocs.org/>`_

Documentation
-------------

All the documentation (examples, api, about, ...) is hosted on readthedocs.org and is updated automaticaly at every commit.
Go and `get it <http://icspy.readthedocs.org/>`_ !


Contribute
----------

Contribution are welcome of course ! More info over `there <https://github.com/C4ptainCrunch/ics.py/blob/master/CONTRIBUTING.rst>`_ (or in the doc.)
