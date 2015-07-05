The "properties as descriptors" branch brings some subtle changes to the api.

- An Event is considered "all day", when its begin is a `date` (instead of a datetime).
- If a string representation of a date/datetime doesn't contain a time part, it is translated to a `date`
- On all-day-Events 'end' refers to the last day of the Event. If the Event is only one day, then 'event.begin==event.end' (see RFC5545 Section 3.6.1.)
    + If an all-day-event has neither end date nor duration, it is considered to take one day ('event.begin==event.end').
- A UID is generated for an Event when it is accessed, 
- Event.created defaults to arrow.now()

What is the modificator 'inc' in Eventlist.__getitem__ meant for?
