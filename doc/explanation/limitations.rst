.. _`misc`:

Known Limitations
=================


ics.py has some known limitations due to the complexity of some parts
of the rfc5545 specification or the lack of time for the developers.
Here is a non-exhaustive list of the most notable limitations.

Missing support for recurrent events
------------------------------------

Events in the iCalendar specification may have a ``RRULE`` property that
defines a rule or repeating pattern (Todos may have these too).
At the moment, ics.py does not have support for the parsing of this
property nor for its usage in the :class:`ics.timeline.Timeline` class
as designing a Pythonic API proved challenging.

Support of ``RRULE`` is expected to be implemented before version 1.0.

.. _`coverage`:

Coverage of the rfc5545 is not 100%
-----------------------------------

ics.py does not actually support the full rfc5545 specification
and most likely, it will never do as it is too much work.

Also, there are as many extensions to the RFC as there are implementations
of iCalendar creators, so it would be impossible to support every existing
property.

This does not mean that ics.py can not read your file:
ics should be able to ready any rfc-compliant file.
ics.py is also able to output a file with the specific property
that you want to use without having knowledge of its meaning.
Please have a look at the :ref:`Advanced guide <custom-property>` to use
the low level API and have access to unsupported properties.


ics.py too is strict when parsing input
---------------------------------------

ics.py was made to output rfc-compliant iCalendar files
and to when possible parse only valid files.
This means that ics.py will throw exceptions when fed malformed
input because we trust that failing silently is
not a good practice.

However, we noticed that some widely used clients create some malformed
files. We are planning to add options to ignore those errors or
to transform them into warnings but at the moment, you will have to
fix those before inputting them in ics.py.

.. note:: These problems are not easy to solve in an
  elegant way so they are not best suited for a first contribution
  nor are they expected to be addressed by the maintainers in the near future.
