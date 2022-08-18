from datetime import date, datetime

from ics import Calendar, Event, Timezone, Todo
from ics.event import deterministic_event_data
from ics.timespan import NormalizationAction
from ics.timezone import UTC


@deterministic_event_data()
def test_normalization():
    cal = Calendar()
    start = datetime(2021, 8, 1, 12, 0)
    end = datetime(2021, 8, 1, 18, 0)
    allday = date(2021, 9, 1)
    tzDE = Timezone.from_tzid("Europe/Berlin")
    tzCA = Timezone.from_tzid("America/Toronto")
    tzJP = Timezone.from_tzid("Asia/Tokyo")
    # events
    cal.events.append(Event("Event1 - naive/local", start, end))
    cal.events.append(Event("Event2 - UTC", start.astimezone(UTC), end.astimezone(UTC)))
    cal.events.append(
        Event("Event3 - Europe/Berlin", start.astimezone(tzDE), end.astimezone(tzDE))
    )
    cal.events.append(
        Event("Event4 - America/Toronto", start.astimezone(tzCA), duration=end - start)
    )
    cal.events.append(Event("Event5 - Asia/Tokyo", start.astimezone(tzJP)))
    allday_event = Event("EventA - Allday", allday)
    allday_event.make_all_day()
    cal.events.append(allday_event)
    # todos
    cal.todos.append(
        Todo(
            summary="Todo1 - diverging",
            begin=start.astimezone(tzJP),
            due=end.astimezone(tzCA),
        )
    )
    allday_todo = Todo(summary="TodoA - allday", begin=allday, due=allday)
    allday_todo.make_all_day()
    cal.todos.append(allday_todo)

    cal.normalize(tzCA, normalize_floating=NormalizationAction.REPLACE)

    startCA = start.astimezone(tzCA)
    endCA = end.astimezone(tzCA)
    assert cal.events == [
        Event(
            "Event1 - naive/local", start.replace(tzinfo=tzCA), end.replace(tzinfo=tzCA)
        ),
        Event("Event2 - UTC", startCA, endCA),
        Event("Event3 - Europe/Berlin", startCA, endCA),
        Event("Event4 - America/Toronto", startCA, duration=end - start),
        Event("Event5 - Asia/Tokyo", startCA),
        allday_event,
    ]
    assert cal.todos == [
        Todo(summary="Todo1 - diverging", begin=startCA, due=endCA),
        allday_todo,
    ]
