How to ?
========

We got some recurrent/interesting questions on GitHub and
by email [#email]_. Here are some answers that might be interesting
to others.

Is there a way to export to format *X* ?
----------------------------------------

ics.py does not support exporting data to any other file format than
the one specified in the rfc5545 and this is not expected to change.

Nevertheless, you might want to have a look at the rfc7265
https://tools.ietf.org/html/rfc7265
that describes a 1 to 1 conversion between the iCalendar format and
a JSON format.

You might want to take a look at this implementation
https://github.com/mozilla-comm/ical.js/wiki
Please contact us if you know other good quality implementations of
converters between iCalendar and jCalendar

There is also no straightforward to export your data to a tabular
format (let's say something like CSV or a Pandas DataFrame)
because the iCalendar is hierarchical *by design*: a VCALENDAR has
multiple VTODO and VEVENT and a VEVENT contains multiple VALARM and
so on.

ics.py does not support the property *Y*, i'm stuck
----------------------------------------------------

Please take a look at :ref:`this section <coverage>`.


Known bugs
----------

Issues with all-day events
~~~~~~~~~~~~~~~~~~~~~~~~~~

The semantics of all-day events in the pyton API were badly defined
in the early versions of ics.py and this led to incoherence and
bugs. See this
`GitHub thread <https://github.com/ics-py/ics-py/issues/155>`_
for more info.

Datetimes are converted to UTC at parsing time
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

ics.py always uses UTC for internal representation of dates.
This is wrong and leads to many problems. See this
`GitHub thread <https://github.com/ics-py/ics-py/issues/188>`_
for more info.

.. rubric:: Footnotes

.. [#email] Please don't send us questions by email, GitHub is much
   more suited for questions
.. [#malformed] An exception to this rule is already made with
   VALARM. ics.py already any type of ``ACTION`` while the rfc only
   accepts a fixed set.
.. [#errors] Known errors are Apple iCloud omitting ``PRODID`` and
   badly other client outputting formatted line splits.
