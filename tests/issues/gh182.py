from datetime import datetime

import pytest
from dateutil.tz import gettz

from ics import Todo
from ics.contentline import ContentLine, lines_to_container


def test_issue_182_seconds_ignored():
    todo = Todo.from_container(
        lines_to_container(
            [
                "BEGIN:VTODO",
                "DTSTART;TZID=Europe/Berlin:20180219T120005",
                "COMPLETED;TZID=Europe/Brussels:20180418T150001",
                "END:VTODO",
            ]
        )
    )
    assert todo.begin == datetime(2018, 2, 19, 12, 0, 5, tzinfo=gettz("Europe/Berlin"))
    assert todo.completed == datetime(
        2018, 4, 18, 15, 0, 1, tzinfo=gettz("Europe/Brussels")
    )

    with pytest.raises(ValueError):
        Todo.from_container(
            lines_to_container(
                [
                    "BEGIN:VTODO",
                    "DTSTART;TZID=Europe/Berlin:2018-02-19 12:00:05",
                    "END:VTODO",
                ]
            )
        )

    container = lines_to_container(
        [
            "BEGIN:VTODO",
            "COMPLETED:;TZID=Europe/Brussels:20180418T150001",
            #         ^ this : breaks parsing
            "END:VTODO",
        ]
    )
    assert container[0] == ContentLine(
        "COMPLETED", value=";TZID=Europe/Brussels:20180418T150001"
    )
    pytest.raises(ValueError, Todo.from_container, container)
