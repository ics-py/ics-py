import arrow
import unittest

from datetime import datetime, timedelta
from ics.alarm import DisplayAlarm
from ics.icalendar import Calendar

from .fixture import cal21, cal22

CRLF = "\r\n"


class TestAlarm(unittest.TestCase):
    """
    Tests many of the base cases for Alarms, using the DisplayAlarm class (since instantiating the Alarm class
    directly is not allowed).
    """

    def test_alarm_timedelta_trigger(self):
        a = DisplayAlarm(trigger=timedelta(minutes=15))
        self.assertEqual(15 * 60, a.trigger.total_seconds())

    def test_alarm_datetime_trigger(self):
        alarm_time = datetime(year=2016, month=1, day=1, hour=0, minute=0, second=0)
        a = DisplayAlarm(trigger=alarm_time)
        self.assertEqual(arrow.get(alarm_time), a.trigger)

    def test_alarm_repeat(self):
        a = DisplayAlarm(trigger=timedelta(minutes=15),
                         repeat=2,
                         duration=timedelta(minutes=10))
        self.assertEqual(15 * 60, a.trigger.total_seconds())
        self.assertEqual(2, a.repeat)
        self.assertEqual(10 * 60, a.duration.total_seconds())

    def test_alarm_invalid_repeat(self):
        with self.assertRaises(ValueError):
            DisplayAlarm(trigger=timedelta(minutes=15),
                         repeat=-2,
                         duration=timedelta(minutes=10))

    def test_alarm_invalid_duration(self):
        with self.assertRaises(ValueError):
            DisplayAlarm(trigger=timedelta(minutes=15),
                         repeat=2,
                         duration=timedelta(minutes=-10))

    def test_alarm_missing_duration(self):
        with self.assertRaises(ValueError):
            DisplayAlarm(trigger=timedelta(minutes=15), repeat=2)

    def test_alarm_timedelta_trigger_output(self):
        a = DisplayAlarm(trigger=timedelta(minutes=15))

        desired_output = CRLF.join(['BEGIN:VALARM',
                                    'TRIGGER:-PT15M',
                                    'ACTION:DISPLAY',
                                    'DESCRIPTION:',
                                    'END:VALARM'])

        self.assertEqual(desired_output, str(a))

    def test_alarm_datetime_trigger_output(self):
        alarm_time = datetime(year=2016, month=1, day=1, hour=0, minute=0, second=0)
        a = DisplayAlarm(trigger=alarm_time)

        desired_output = CRLF.join(['BEGIN:VALARM',
                                    'TRIGGER;VALUE=DATE-TIME:20160101T000000Z',
                                    'ACTION:DISPLAY',
                                    'DESCRIPTION:',
                                    'END:VALARM'])

        self.assertEqual(desired_output, str(a))

    def test_alarm_repeat_duration_output(self):
        a = DisplayAlarm(trigger=timedelta(minutes=15),
                         repeat=2,
                         duration=timedelta(minutes=10))

        desired_output = CRLF.join(['BEGIN:VALARM',
                                    'TRIGGER:-PT15M',
                                    'DURATION:PT10M',
                                    'REPEAT:2',
                                    'ACTION:DISPLAY',
                                    'DESCRIPTION:',
                                    'END:VALARM'])

        self.assertEqual(desired_output, str(a))


class TestDisplayAlarm(unittest.TestCase):

    def test_alarm(self):
        test_description = 'Test description'
        a = DisplayAlarm(trigger=timedelta(minutes=15),
                         description=test_description)
        self.assertEqual(test_description, a.description)

    def test_plain_repr(self):
        test_description = 'Test description'
        a = DisplayAlarm(trigger=timedelta(minutes=15),
                         description=test_description)
        self.assertEqual(repr(a), "<<class 'ics.alarm.DisplayAlarm'> trigger:0:15:00 description:Test description>")

    def test_repeat_repr(self):
        test_description = 'Test description'
        a = DisplayAlarm(trigger=timedelta(minutes=15),
                         repeat=2,
                         duration=timedelta(minutes=10),
                         description=test_description)
        self.assertEqual(repr(a), "<<class 'ics.alarm.DisplayAlarm'> trigger:0:15:00 repeat:2 "
                                  "duration:0:10:00 description:Test description>")

    def test_alarm_output(self):
        a = DisplayAlarm(trigger=timedelta(minutes=15),
                         description='Test description')

        desired_output = CRLF.join(['BEGIN:VALARM',
                                    'TRIGGER:-PT15M',
                                    'ACTION:DISPLAY',
                                    'DESCRIPTION:Test description',
                                    'END:VALARM'])

        self.assertEqual(desired_output, str(a))

    def test_alarm_without_repeat_extraction(self):
        c = Calendar(cal21)
        a = c.events[0].alarms[0]
        self.assertEqual(a.trigger, timedelta(hours=1))
        self.assertIsNone(a.repeat)
        self.assertIsNone(a.duration)
        self.assertEqual(a.description, 'Event reminder')

    def test_alarm_with_repeat_extraction(self):
        c = Calendar(cal22)
        a = c.events[0].alarms[0]
        self.assertEqual(a.trigger, timedelta(hours=1))
        self.assertEqual(a.repeat, 2)
        self.assertEqual(a.duration, timedelta(minutes=10))
        self.assertEqual(a.description, 'Event reminder')
