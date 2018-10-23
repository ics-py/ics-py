Import a calendar from a file
-----------------------------

.. code-block:: python

    from ics import Calendar
    from urllib.request import urlopen
    url = "https://urlab.be/events/urlab.ics"
    c = Calendar(urlopen(url).read().decode())

    import requests    # Alternative: use requests
    c = Calendar(requests.get(url).text)

    c
    # <Calendar with 118 events and 0 todo>
    c.events
    # {<Event 'Visite de "Fab Bike"' begin:2016-06-21T15:00:00+00:00 end:2016-06-21T17:00:00+00:00>,
    # <Event 'Le lundi de l'embarqué: Adventure in Espressif Non OS SDK edition' begin:2018-02-19T17:00:00+00:00 end:2018-02-19T22:00:00+00:00>,
    #  ...}
    e = min(c.events, key=lambda event: event.begin):
    "Event '{}' started {}".format(e.name, e.begin.humanize())
    # "Event 'Workshop Git' started 2 years ago"


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
    # {<Event 'My cool event' begin:2014-01-01 00:00:00 end:2014-01-01 00:00:01>}

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
