import unittest
from datetime import datetime, timedelta

import arrow

from ics.alarm.base import BaseAlarm
from ics.alarm.none import NoneAlarm
from ics.alarm.custom import CustomAlarm
from ics.alarm import AudioAlarm, DisplayAlarm
from ics.icalendar import Calendar
from ics.alarm.email import EmailAlarm
from ics.grammar.parse import ContentLine

from .fixture import cal21, cal22, cal23, cal24, cal25, cal35, cal36

CRLF = "\r\n"


class FakeAlarm(BaseAlarm):
    @property
    def action(self):
        return "FAKE"


class TestAlarm(unittest.TestCase):
    def test_alarm_timedelta_trigger(self):
        a = FakeAlarm(trigger=timedelta(minutes=15))
        self.assertEqual(15 * 60, a.trigger.total_seconds())

    def test_alarm_datetime_trigger(self):
        alarm_time = datetime(year=2016, month=1, day=1, hour=0, minute=0, second=0)
        a = FakeAlarm(trigger=alarm_time)
        self.assertEqual(arrow.get(alarm_time), a.trigger)

    def test_alarm_repeat(self):
        a = FakeAlarm(
            trigger=timedelta(minutes=15), repeat=2, duration=timedelta(minutes=10)
        )
        self.assertEqual(15 * 60, a.trigger.total_seconds())
        self.assertEqual(2, a.repeat)
        self.assertEqual(10 * 60, a.duration.total_seconds())

    def test_alarm_invalid_repeat(self):
        with self.assertRaises(ValueError):
            FakeAlarm(
                trigger=timedelta(minutes=15), repeat=-2, duration=timedelta(minutes=10)
            )

    def test_alarm_invalid_duration(self):
        with self.assertRaises(ValueError):
            FakeAlarm(
                trigger=timedelta(minutes=15), repeat=2, duration=timedelta(minutes=-10)
            )

    def test_alarm_missing_duration(self):
        with self.assertRaises(ValueError):
            FakeAlarm(trigger=timedelta(minutes=15), repeat=2)

    def test_alarm_timedelta_trigger_output(self):
        a = FakeAlarm(trigger=timedelta(minutes=15))

        desired_output = CRLF.join(
            ["BEGIN:VALARM", "ACTION:FAKE", "TRIGGER:PT15M", "END:VALARM"]
        )

        self.assertEqual(desired_output, str(a))

    def test_alarm_datetime_trigger_output(self):
        alarm_time = datetime(year=2016, month=1, day=1, hour=0, minute=0, second=0)
        a = FakeAlarm(trigger=alarm_time)

        desired_output = CRLF.join(
            [
                "BEGIN:VALARM",
                "ACTION:FAKE",
                "TRIGGER;VALUE=DATE-TIME:20160101T000000Z",
                "END:VALARM",
            ]
        )

        self.assertEqual(desired_output, str(a))

    def test_alarm_repeat_duration_output(self):
        a = FakeAlarm(
            trigger=timedelta(minutes=15), repeat=2, duration=timedelta(minutes=10)
        )

        desired_output = CRLF.join(
            [
                "BEGIN:VALARM",
                "ACTION:FAKE",
                "DURATION:PT10M",
                "REPEAT:2",
                "TRIGGER:PT15M",
                "END:VALARM",
            ]
        )

        self.assertEqual(desired_output, str(a))


class TestDisplayAlarm(unittest.TestCase):
    def test_alarm(self):
        test_description = "Test description"
        a = DisplayAlarm(trigger=timedelta(minutes=15), display_text=test_description)
        self.assertEqual(test_description, a.display_text)

    def test_alarm_output(self):
        a = DisplayAlarm(trigger=timedelta(minutes=15), display_text="Test description")

        desired_output = CRLF.join(
            [
                "BEGIN:VALARM",
                "ACTION:DISPLAY",
                "DESCRIPTION:Test description",
                "TRIGGER:PT15M",
                "END:VALARM",
            ]
        )

        self.assertEqual(desired_output, str(a))

    def test_alarm_without_repeat_extraction(self):
        c = Calendar(cal21)
        e = next(iter(c.events))
        assert isinstance(e.alarms, list)
        a = e.alarms[0]
        self.assertEqual(a.trigger, timedelta(hours=1))
        self.assertIsNone(a.repeat)
        self.assertIsNone(a.duration)
        self.assertEqual(a.display_text, "Event reminder")

    def test_alarm_with_repeat_extraction(self):
        c = Calendar(cal22)
        a = next(iter(c.events)).alarms[0]
        self.assertEqual(a.trigger, timedelta(hours=1))
        self.assertEqual(a.repeat, 2)
        self.assertEqual(a.duration, timedelta(minutes=10))
        self.assertEqual(a.display_text, "Event reminder")

    def test_alarm_without_repeat_datetime_trigger_extraction(self):
        c = Calendar(cal23)
        a = next(iter(c.events)).alarms[0]

        alarm_time = datetime(year=2016, month=1, day=1, hour=0, minute=0, second=0)
        self.assertEqual(a.trigger, arrow.get(alarm_time))
        self.assertIsNone(a.repeat)
        self.assertIsNone(a.duration)
        self.assertEqual(a.display_text, "Event reminder")


class TestAudioAlarm(unittest.TestCase):
    def test_alarm(self):
        a = AudioAlarm(trigger=timedelta(minutes=15))
        self.assertEqual("AUDIO", a.action)

    def test_plain_repr(self):
        a = AudioAlarm(trigger=timedelta(minutes=15))
        self.assertEqual(repr(a), "<AudioAlarm trigger:0:15:00>")

    def test_alarm_output(self):
        attach = "ftp://example.com/pub/sounds/bell-01.aud"
        attach_params = {"FMTTYPE": ["audio/basic"]}
        a = AudioAlarm(trigger=timedelta(minutes=15))
        a.sound = ContentLine("ATTACH", value=attach, params=attach_params)

        desired_output = CRLF.join(
            [
                "BEGIN:VALARM",
                "ACTION:AUDIO",
                "ATTACH;FMTTYPE=audio/basic:{0}".format(attach),
                "TRIGGER:PT15M",
                "END:VALARM",
            ]
        )

        self.assertEqual(desired_output, str(a))

    def test_alarm_without_attach_extraction(self):
        c = Calendar(cal24)
        a = next(iter(c.events)).alarms[0]
        alarm_time = datetime(year=2016, month=1, day=1, hour=0, minute=0, second=0)

        self.assertEqual(a.action, "AUDIO")
        self.assertEqual(a.trigger, arrow.get(alarm_time))
        self.assertIsNone(a.repeat)
        self.assertIsNone(a.duration)
        self.assertIsNone(a.sound)

    def test_alarm_with_attach_extraction(self):
        c = Calendar(cal25)
        a = next(iter(c.events)).alarms[0]
        alarm_time = datetime(year=2016, month=1, day=1, hour=0, minute=0, second=0)

        self.assertEqual(a.action, "AUDIO")
        self.assertEqual(a.trigger, arrow.get(alarm_time))
        self.assertIsNone(a.repeat)
        self.assertIsNone(a.duration)
        self.assertEqual(a.sound.value, "ftp://example.com/pub/sounds/bell-01.aud")
        self.assertIn("FMTTYPE", a.sound.params.keys())
        self.assertEqual(1, len(a.sound.params["FMTTYPE"]))
        self.assertEqual("audio/basic", a.sound.params["FMTTYPE"][0])


def test_none():
    c = Calendar(cal35)
    a = next(iter(c.events)).alarms[0]
    assert isinstance(a, NoneAlarm)


def test_custom():
    c = Calendar(cal36)
    a = next(iter(c.events)).alarms[0]
    assert isinstance(a, CustomAlarm)
    assert a.action == "YOLO"


def test_custom_back_forth():
    c = Calendar(cal36)
    c1 = Calendar(str(c))
    assert c == c1


class TestEmailAlarm(unittest.TestCase):
    def test_alarm(self):
        a = EmailAlarm(trigger=timedelta(minutes=15))
        self.assertEqual("EMAIL", a.action)
