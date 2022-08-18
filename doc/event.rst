First, let’s import the latest version of ics.py :date:

::

   >>> import ics
   >>> ics.__version__
   '0.8.0-dev0'

We’re also going to create a lot of ``datetime`` and ``timedelta``
objects, so we import them as short-hand aliases ``dt`` and ``td``:

::

   >>> from datetime import datetime as dt, timedelta as td

Now, we are ready to create our first event :tada:

::

   >>> e = ics.Event(begin=dt(2020, 2, 20,  20, 20))
   >>> str(e)
   '<floating Event begin: 2020-02-20 20:20:00 end: 2020-02-20 20:20:00>'

We specified no end time or duration for the event, so the event
defaults to ending at the same instant it begins. The event is also
considered “floating”, as datetime objects by default contain no
timezone information and we didn’t specify any ``tzinfo``, so the begin
time of the event is timezone-naive. We will see how to handle timezones
correctly later. Instead of using the default end time, we can update
the event to set the end time explicitly:

::

   >>> e.end = dt(2020, 2, 22,  20, 20)
   >>> str(e)
   '<floating Event begin: 2020-02-20 20:20:00 fixed end: 2020-02-22 20:20:00 duration: 2 days, 0:00:00>'

Now, the duration of the event explicitly shows up and the end time is
also marked as being set or “fixed” to a certain instant. If we now set
the duration of the event to a different value, the end time will change
correspondingly:

::

   >>> e.duration=td(days=2)
   >>> str(e)
   '<floating Event begin: 2020-02-20 20:20:00 end: 2020-02-22 20:20:00 fixed duration: 2 days, 0:00:00>'

As we now specified the duration explicitly, the duration is now fixed
instead of the end time. This actually makes a big difference when you
now change the start time of the event:

::

   >>> e1 = ics.Event(begin=dt(2020, 2, 20,  20, 20), end=dt(2020, 2, 22,  20, 20))
   >>> e2 = ics.Event(begin=dt(2020, 2, 20,  20, 20), duration=td(days=2))
   >>> str(e1)
   '<floating Event begin: 2020-02-20 20:20:00 fixed end: 2020-02-22 20:20:00 duration: 2 days, 0:00:00>'
   >>> str(e2)
   '<floating Event begin: 2020-02-20 20:20:00 end: 2020-02-22 20:20:00 fixed duration: 2 days, 0:00:00>'
   >>> e1.begin = e2.begin = dt(2020, 1, 10,  10, 10)
   >>> str(e1)
   '<floating Event begin: 2020-01-10 10:10:00 fixed end: 2020-02-22 20:20:00 duration: 43 days, 10:10:00>'
   >>> str(e2)
   '<floating Event begin: 2020-01-10 10:10:00 end: 2020-01-12 10:10:00 fixed duration: 2 days, 0:00:00>'

As we just saw, duration and end can also be passed to the constructor,
but both are only allowed when a begin time for the event is specified,
and both can’t be set at the same time:

::

   >>> ics.Event(end=dt(2020, 2, 22,  20, 20))
   Traceback (most recent call last):
     ...
   ValueError: event timespan without begin time can't have end time
   >>> ics.Event(duration=td(2))
   Traceback (most recent call last):
     ...
   ValueError: timespan without begin time can't have duration
   >>> ics.Event(begin=dt(2020, 2, 20,  20, 20), end=dt(2020, 2, 22,  20, 20), duration=td(2))
   Traceback (most recent call last):
     ...
   ValueError: can't set duration together with end time

Similarly, when you created an event that hasn’t a begin time yet, you
won’t be able to set its duration or end:

::

   >>> ics.Event().end = dt(2020, 2, 22,  20, 20)
   Traceback (most recent call last):
     ...
   ValueError: event timespan without begin time can't have end time
   >>> ics.Event().duration = td(2)
   Traceback (most recent call last):
     ...
   ValueError: timespan without begin time can't have duration
