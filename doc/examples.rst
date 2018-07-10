Import a calendar from a file
-----------------------------

.. code-block:: python

    from ics import Calendar
    from urllib.request import urlopen
    url = "https://goo.gl/fhhrjN"
    c = Calendar(urlopen(url).read().decode('iso-8859-1'))

    import requests    # Alternative: use requests
    c = Calendar(requests.get(url).text)

    c
    # <Calendar with 42 events>
    c.events
    # [<Event 'SmartMonday #1' begin:2013-12-13 20:00:00 end:2013-12-13 23:00:00>,
    # <Event 'RFID workshop' begin:2013-12-06 12:00:00 end:2013-12-06 19:00:00>,
    #  ...]
    e = c.events[10]
    "Event '{}' started {}".format(e.name, e.begin.humanize())
    # "Event 'Mitch Altman soldering workshop' started 6 days ago"


Create a new calendar and add events
------------------------------------

.. code-block:: python

    from ics import Calendar, Event
    c = Calendar()
    e = Event()
    e.name = "My cool event"
    e.begin = '20140101 00:00:00'
    c.events.add(e)
    c.events
    # [<Event 'My cool event' begin:2014-01-01 00:00:00 end:2014-01-01 00:00:01>]

Export a Calendar to a file
---------------------------

.. code-block:: python

    with open('my.ics', 'w') as f:
        f.writelines(c)
    # And it's done !

iCalendar-formatted data is also available in a string

.. code-block:: python

    str(c)
    # 'BEGIN:VCALENDAR\nPRODID:...
