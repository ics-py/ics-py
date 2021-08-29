from datetime import datetime

from ics import Calendar, Event, Timezone, Todo
from ics.timespan import NormalizationAction
from ics.timezone import UTC


def test_normalization():
    cal = Calendar()
    start = datetime(2021, 8, 1, 12, 0)
    end = datetime(2021, 8, 1, 18, 0)
    tzDE = Timezone.from_tzid("Europe/Berlin")
    tzCA = Timezone.from_tzid("America/Toronto")
    tzJP = Timezone.from_tzid("Asia/Tokyo")
    kwargs = {"uid": "test@example.com", "dtstamp": start.replace(tzinfo=UTC)}
    cal.events.append(Event("Event1 - naive/local", start, end, **kwargs))
    cal.events.append(Event("Event2 - UTC", start.astimezone(UTC), end.astimezone(UTC), **kwargs))
    cal.events.append(Event("Event3 - Europe/Berlin", start.astimezone(tzDE), end.astimezone(tzDE), **kwargs))
    cal.events.append(Event("Event4 - America/Toronto", start.astimezone(tzCA), duration=end - start, **kwargs))
    cal.events.append(Event("Event5 - Asia/Tokyo", start.astimezone(tzJP), **kwargs))
    cal.todos.append(
        Todo(summary="Todo1 - diverging", begin=start.astimezone(tzJP), due=end.astimezone(tzCA), **kwargs))

    cal.normalize(tzCA, normalize_floating=NormalizationAction.REPLACE)

    startCA = start.astimezone(tzCA)
    endCA = end.astimezone(tzCA)
    assert cal.events == [
        Event("Event1 - naive/local", start.replace(tzinfo=tzCA), end.replace(tzinfo=tzCA), **kwargs),
        Event("Event2 - UTC", startCA, endCA, **kwargs),
        Event("Event3 - Europe/Berlin", startCA, endCA, **kwargs),
        Event("Event4 - America/Toronto", startCA, duration=end - start, **kwargs),
        Event("Event5 - Asia/Tokyo", startCA, **kwargs),
    ]
    assert cal.todos == [
        Todo(summary="Todo1 - diverging", begin=startCA, due=endCA, **kwargs)
    ]
