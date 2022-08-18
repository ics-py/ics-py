.. _`advanced`:

Advanced usage
==============
This page will present some more advanced usage of ics.py
as well as some parts of the low level API.

.. Low level constructs
.. --------------------

.. _`custom-property`:

Custom properties
-----------------

ics.py does not indeed support the full rfc5545 specification
and most likely, it will never do as it is too much work.
Also, there are as many extensions to the RFC as there are implementations
of iCalendar creators so it would be impossible to support every existing
property.

The way around this limitation is that every :class:`ics.parse.Container`
(:class:`~ics.Event`, :class:`~ics.Todo` and even :class:`~ics.Calendar`
inherit from :class:`~ics.parse.Container`)
has a ``.extra`` attribute.

At parsing time, every property or container that is unknown to ics.py
(and thus not handled) is stored in ``.extra``. The other way, everything
in ``.extra`` is serialized when outputting data.

Let's say that we have an input like this
(indentation is for illustration purposes): ::

  BEGIN:VEVENT
    SUMMARY:Name of the event
    FOO:BAR
  END:VEVENT

It will result in an event that will have the following characteristics:

.. code-block:: python

    e.name == "Name of the event"
    e.extra == [ContentLine(name="FOO", value="BAR")]

In a more complicated situation, you might even have
something like this:  ::

  BEGIN:VEVENT
    SUMMARY:Name of the event
    BEGIN:FOO
      BAR:MISC
    END:FOO
    THX:BYE
  END:VEVENT

It will result in an event that will have a :class:`ics.parse.Container`
in ``.extra``:

.. code-block:: python

    e.name == "Name of the event"
    e.extra == [
        Container(name="FOO", ContentLine(name="BAR", value="MISC")),
        ContentLine(name="THX", value="BYE"),
    ]

``.extra`` is mutable so this means it works in reverse too.

Just add some :class:`~ics.parse.Container` or
:class:`ics.parse.ContentLine` and they will appear in the output too.
(You can even mutate the values of a specific :class:`~ics.parse.ContentLine`
if you desire)

Low level API
-------------

.. autoclass:: ics.parse.Container
    :members:

.. autoclass:: ics.parse.ContentLine
    :members:
