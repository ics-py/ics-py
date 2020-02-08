.. _`misc`:

Misc
============


Known limitations
-----------------

ics.py has a some known limitations due to the complexity of some parts
of the rfc5545 specification or the lack of time of the developers.
Here is a non-exhaustive list of the most notable.

Missing support for recurrent events
************************************

Events in the iCalendar specification my have a ``RRULE`` property that
defines a rule or repeating pattern (Todos may have those too).
At the moment, ics.py does not have support for either parsing of this
property of its usage in the :class:`ics.timeline.Timeline` class
as designing a Pythonic API proved challenging.

Support of ``RRULE`` is expected to be implemented before version 1.0.

.. _`coverage`:

Coverage of the rfc5545 is not 100%
***********************************

ics.py does not indeed support the full rfc5545 specification
and most likely, it will never do as it is too much work.

Also, there are as many extensions to the RFC as there are implementations
of iCalendar creators so it would be impossible to support every existing
property.

This does not mean that ics.py can not read your file:
ics should be able to ready any rfc-compliant file.
ics.py is also able to output a file with the specific property
that you want to use without having knowledge of its meaning.
Please have a look at the :ref:`Advanced guide <custom-property>` to use
the low level API and have access to unsupported properties.


ics.py too is strict when parsing input
***************************************

ics.py was made to output rfc-compliant iCalendar files
and to when possible parse only valid files.
This means that ics.py will throw exceptions when fed malformed
input [#malformed]_ because we trust that failing silently is
not a good practice.

However, we noticed that some widely used clients create some malformed
files. We are planning to add options to ignore those errors [#errors]_ or
transforming them into warnings but at the moment, you will have to
fix those before giving inputting them in ics.py.

.. note:: These problems are not easy to solve in an
  elegant way so they are not best suited for a first contribution
  nor they are expected be addressed by the maintainers in the near future


How to ?
--------

We got some recurrent/interesting questions on GitHub and
by email [#email]_. Here are some answers that might be interesting
to others.

Is there a way to export to format *X* ?
****************************************

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

ics.py does not support the property *Y*, i'm stuck.
****************************************************

Please take a look at :ref:`this section <coverage>`.


Known bugs
----------

Issues with all-day events
**************************

The semantics of all-day events in the pyton API were badly defined
in the early versions of ics.py and this led to incoherence and
bugs. See this
`GitHub thread <https://github.com/C4ptainCrunch/ics.py/issues/155>`_
for more info.

Datetimes are converted to UTC at parsing time
**********************************************

ics.py always uses UTC for internal representation of dates.
This is wrong and leads to many problems. See this
`GitHub thread <https://github.com/C4ptainCrunch/ics.py/issues/188>`_
for more info.

.. rubric:: Footnotes

.. [#email] Please don't send us questions by email, GitHub is much
   more suited for questions
.. [#malformed] An exception to this rule is already made with
   VALARM. ics.py already any type of ``ACTION`` while the rfc only
   accepts a fixed set.
.. [#errors] Known errors are Apple iCloud omitting ``PRODID`` and
   badly other client outputting formatted line splits.
