from ics.utils import parse_duration
from datetime import timedelta


def test_simple():
    s = "PT30M"
    assert parse_duration(s) == timedelta(minutes=30)


def test_negative():
    s = "-PT30M"
    assert parse_duration(s) == timedelta(minutes=-30)


def test_no_sign():
    s = "P0DT9H0M0S"
    assert parse_duration(s) == timedelta(hours=9)
