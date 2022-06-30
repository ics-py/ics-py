import os
import unittest
from datetime import datetime as dt
from datetime import timedelta as td

import arrow
import pytest

from ics.attendee import Attendee, Organizer
from ics.event import Event
from ics.icalendar import Calendar
from ics.grammar.parse import Container

from .fixture import (cal12, cal13, cal15, cal16, cal17, cal18, cal19,
                      cal19bis, cal20, cal32, cal33_1, cal33_2, cal33_3,
                      cal33_4, cal33_5)

CRLF = "\r\n"


class TestEvent(unittest.TestCase):

    def test_event(self):
        e = Event(begin=0, end=20)
        self.assertEqual(e.begin.int_timestamp, 0)
        self.assertEqual(e.end.int_timestamp, 20)
        self.assertTrue(e.has_end())
        self.assertFalse(e.all_day)

        f = Event(begin=10, end=30)
        self.assertTrue(e < f)
        self.assertTrue(e <= f)
        self.assertTrue(f > e)
        self.assertTrue(f >= e)

    def test_event_with_duration(self):
        c = Calendar(cal12)
        e = next(iter(c.events))
        self.assertEqual(e._duration, td(1, 3600))
        self.assertEqual(e.end - e.begin, td(1, 3600))

    def test_event_with_geo(self):
        c = Calendar(cal12)
        e = list(c.events)[0]
        self.assertEqual(e.geo, (40.779897,-73.968565))

    def test_not_duration_and_end(self):
        with self.assertRaises(ValueError):
            Calendar(cal13)

    def test_duration_output(self):
        e = Event(begin=0, duration=td(1, 23))
        lines = str(e).splitlines()
        self.assertIn('DTSTART:19700101T000000Z', lines)
        self.assertIn('DURATION:P1DT23S', lines)

    def test_geo_output(self):
        e = Event(geo=(40.779897, -73.968565))
        lines = str(e).splitlines()
        self.assertIn('GEO:40.779897;-73.968565', lines)

    def test_make_all_day(self):
        e = Event(begin=0, end=20)
        begin = e.begin
        e.make_all_day()
        self.assertEqual(e.begin, begin)
        self.assertEqual(e._end_time, None)
        self.assertEqual(e._duration, None)

    def test_make_all_day2(self):
        e = Event(begin="1993/05/24")
        begin = arrow.get("1993/05/24")

        self.assertEqual(e._begin, begin)
        self.assertEqual(e.begin, begin)

        self.assertEqual(e._end_time, None)
        self.assertEqual(e.end, begin)

        e.make_all_day()

        self.assertEqual(e._begin, begin)
        self.assertEqual(e.begin, begin)
        self.assertEqual(e._begin_precision, "day")

        self.assertEqual(e._end_time, None)
        self.assertEqual(e.end, arrow.get("1993/05/25"))

    def test_init_duration_end(self):
        with self.assertRaises(ValueError):
            Event(name="plop", begin=0, end=10, duration=1)

    def test_end_before_begin(self):
        e = Event(begin="2013/10/10")
        with self.assertRaises(ValueError):
            e.end = "1999/10/10"

    def test_begin_after_end(self):
        e = Event(end="19991010")
        with self.assertRaises(ValueError):
            e.begin = "2013/10/10"

    def test_end_with_prescision(self):
        e = Event(begin="1999/10/10")
        e._begin_precision = "day"
        self.assertEqual(e.end, arrow.get("1999/10/11"))

    def test_plain_repr(self):
        self.assertEqual(repr(Event()), "<Event>")

    def test_all_day_repr(self):
        e = Event(name='plop', begin="1999/10/10")
        e.make_all_day()
        self.assertEqual(repr(e), "<all-day Event 'plop' 1999-10-10>")

    def test_name_repr(self):
        e = Event(name='plop')
        self.assertEqual(repr(e), "<Event 'plop'>")

    def test_repr(self):
        e = Event(name='plop', begin="1999/10/10")
        self.assertEqual(repr(e), "<Event 'plop' begin:1999-10-10T00:00:00+00:00 end:1999-10-10T00:00:00+00:00>")

    def test_init(self):
        e = Event()

        self.assertEqual(e._duration, None)
        self.assertEqual(e._end_time, None)
        self.assertEqual(e._begin, None)
        self.assertEqual(e._begin_precision, 'second')
        self.assertNotEqual(e.uid, None)
        self.assertEqual(e.description, None)
        self.assertEqual(e.created, None)
        self.assertEqual(e.last_modified, None)
        self.assertEqual(e.location, None)
        self.assertEqual(e.geo, None)
        self.assertEqual(e.url, None)
        self.assertEqual(e.extra, Container(name='VEVENT'))
        self.assertEqual(e.status, None)
        self.assertEqual(e.organizer, None)

    def test_has_end(self):
        e = Event()
        self.assertFalse(e.has_end())
        e = Event(begin="1993/05/24", duration=10)
        self.assertTrue(e.has_end())
        e = Event(begin="1993/05/24", end="1999/10/11")
        self.assertTrue(e.has_end())
        e = Event(begin="1993/05/24")
        e.make_all_day()
        self.assertFalse(e.has_end())

    def test_duration(self):
        e = Event()
        self.assertIsNone(e.duration)

        e1 = Event(begin="1993/05/24")
        e1.make_all_day()
        self.assertEqual(e1.duration, td(days=1))

        e2 = Event(begin="1993/05/24", end="1993/05/30")
        self.assertEqual(e2.duration, td(days=6))

        e3 = Event(begin="1993/05/24", duration=td(minutes=1))
        self.assertEqual(e3.duration, td(minutes=1))

        e4 = Event(begin="1993/05/24")
        self.assertEqual(e4.duration, td(0))

        e5 = Event(begin="1993/05/24")
        e5.duration = {'days': 6, 'hours': 2}
        self.assertEqual(e5.end, arrow.get("1993-05-30T02:00"))
        self.assertEqual(e5.duration, td(hours=146))

    def test_geo(self):
        e = Event()
        self.assertIsNone(e.geo)

        e1 = Event(geo=(40.779897, -73.968565))
        self.assertEqual(e1.geo, (40.779897, -73.968565))

        e2 = Event(geo={'latitude': 40.779897, 'longitude': -73.968565})
        self.assertEqual(e2.geo, (40.779897, -73.968565))

    def test_attendee(self):
        a = Attendee(email='email@email.com')
        line = str(a)
        self.assertIn("ATTENDEE;CN=email@email.com:mailto:email@email.com", line)

        a2 = Attendee(email='email@email.com', common_name='Email')
        line = str(a2)
        self.assertIn("ATTENDEE;CN=Email:mailto:email@email.com", line)

        a3 = Attendee(
            email="email@email.com",
            common_name="Email",
            partstat="ACCEPTED",
            role="CHAIR",
        )
        line = str(a3)
        self.assertIn(
            "ATTENDEE;CN=Email;PARTSTAT=ACCEPTED;ROLE=CHAIR:mailto:email@email.com",
            line,
        )

    def test_add_attendees(self):
        e = Event()
        a = Attendee(email='email@email.com')
        e.add_attendee(a)
        lines = str(e).splitlines()
        self.assertIn("ATTENDEE;CN=email@email.com:mailto:email@email.com", lines)

    def test_organizer(self):
        e = Event()
        e.organizer = Organizer(email='email@email.com', common_name='Mister Email')
        lines = str(e).splitlines()
        self.assertIn("ORGANIZER;CN=Mister Email:mailto:email@email.com", lines)

    def test_always_uid(self):
        e = Event()
        e.uid = None
        self.assertIn('UID:', str(e))

    def test_cmp_other(self):
        with self.assertRaises(NotImplementedError):
            Event() < 1
        with self.assertRaises(NotImplementedError):
            Event() > 1
        with self.assertRaises(NotImplementedError):
            Event() <= 1
        with self.assertRaises(NotImplementedError):
            Event() >= 1

    def test_cmp_by_name(self):
        self.assertGreater(Event(name="z"), Event(name="a"))
        self.assertGreaterEqual(Event(name="z"), Event(name="a"))
        self.assertGreaterEqual(Event(name="m"), Event(name="m"))

        self.assertLess(Event(name="a"), Event(name="z"))
        self.assertLessEqual(Event(name="a"), Event(name="z"))
        self.assertLessEqual(Event(name="m"), Event(name="m"))

    def test_cmp_by_name_fail(self):
        self.assertFalse(Event(name="a") > Event(name="z"))
        self.assertFalse(Event(name="a") >= Event(name="z"))

        self.assertFalse(Event(name="z") < Event(name="a"))
        self.assertFalse(Event(name="z") <= Event(name="a"))

    def test_cmp_by_name_fail_not_equal(self):
        self.assertFalse(Event(name="a") > Event(name="a"))
        self.assertFalse(Event(name="b") < Event(name="b"))

    def test_cmp_by_start_time(self):
        ev1 = Event(begin=dt(2018, 6, 29, 6))
        ev2 = Event(begin=dt(2018, 6, 29, 7))
        self.assertLess(ev1, ev2)
        self.assertGreaterEqual(ev2, ev1)
        self.assertLessEqual(ev1, ev2)
        self.assertGreater(ev2, ev1)

    def test_cmp_by_start_time_with_end_time(self):
        ev1 = Event(begin=dt(2018, 6, 29, 5), end=dt(2018, 6, 29, 7))
        ev2 = Event(begin=dt(2018, 6, 29, 6), end=dt(2018, 6, 29, 8))
        ev3 = Event(begin=dt(2018, 6, 29, 6))
        self.assertLess(ev1, ev2)
        self.assertGreaterEqual(ev2, ev1)
        self.assertLessEqual(ev1, ev2)
        self.assertGreater(ev2, ev1)
        self.assertLess(ev3, ev2)
        self.assertGreaterEqual(ev2, ev3)
        self.assertLessEqual(ev3, ev2)
        self.assertGreater(ev2, ev3)

    def test_cmp_by_end_time(self):
        ev1 = Event(begin=dt(2018, 6, 29, 6), end=dt(2018, 6, 29, 7))
        ev2 = Event(begin=dt(2018, 6, 29, 6), end=dt(2018, 6, 29, 8))
        self.assertLess(ev1, ev2)
        self.assertGreaterEqual(ev2, ev1)
        self.assertLessEqual(ev1, ev2)
        self.assertGreater(ev2, ev1)

    def test_unescape_summary(self):
        c = Calendar(cal15)
        e = next(iter(c.events))
        self.assertEqual(e.name, "Hello, \n World; This is a backslash : \\ and another new \n line")

    def test_unescapte_texts(self):
        c = Calendar(cal17)
        e = next(iter(c.events))
        self.assertEqual(e.name, "Some special ; chars")
        self.assertEqual(e.location, "In, every text field")
        self.assertEqual(e.description, "Yes, all of them;")

    def test_escape_output(self):
        e = Event()

        e.name = "Hello, with \\ special; chars and \n newlines"
        e.location = "Here; too"
        e.description = "Every\nwhere ! Yes, yes !"
        e.created = arrow.Arrow(2013, 1, 1)
        e.uid = "empty-uid"

        eq = CRLF.join(("BEGIN:VEVENT",
                "DTSTAMP:20130101T000000Z",
                "DESCRIPTION:Every\\nwhere ! Yes\\, yes !",
                "LOCATION:Here\\; too",
                "SUMMARY:Hello\\, with \\\\ special\\; chars and \\n newlines",
                "UID:empty-uid",
                "END:VEVENT"))
        self.assertEqual(str(e), eq)

    def test_url_input(self):
        c = Calendar(cal16)
        e = next(iter(c.events))
        self.assertEqual(e.url, "http://example.com/pub/calendars/jsmith/mytime.ics")

    def test_url_output(self):
        URL = "http://example.com/pub/calendars/jsmith/mytime.ics"
        e = Event(name="Name", url=URL)
        self.assertIn("URL:" + URL, str(e).splitlines())

    def test_status_input(self):
        c = Calendar(cal16)
        e = next(iter(c.events))
        self.assertEqual(e.status, "CONFIRMED")

    def test_status_output(self):
        STATUS = "CONFIRMED"
        e = Event(name="Name", status=STATUS)
        self.assertIn("STATUS:" + STATUS, str(e).splitlines())

    def test_category_input(self):
        c = Calendar(cal16)
        e = next(iter(c.events))
        self.assertIn("Simple Category", e.categories)
        self.assertIn("My \"Quoted\" Category", e.categories)
        self.assertIn("Category, with comma", e.categories)

    def test_category_output(self):
        cat = "Simple category"
        e = Event(name="Name", categories={cat})
        self.assertIn("CATEGORIES:" + cat, str(e).splitlines())

    def test_all_day_with_end(self):
        c = Calendar(cal20)
        e = next(iter(c.events))
        self.assertTrue(e.all_day)

    def test_not_all_day(self):
        c = Calendar(cal16)
        e = next(iter(c.events))
        self.assertFalse(e.all_day)

    def test_all_day_duration(self):
        c = Calendar(cal20)
        e = next(iter(c.events))
        self.assertTrue(e.all_day)
        self.assertEqual(e.duration, td(days=2))

    def test_make_all_day_idempotence(self):
        c = Calendar(cal18)
        e = next(iter(c.events))
        self.assertFalse(e.all_day)
        e2 = e.clone()
        e2.make_all_day()
        self.assertTrue(e2.all_day)
        self.assertNotEqual(e.begin, e2.begin)
        self.assertNotEqual(e.end, e2.end)
        e3 = e2.clone()
        e3.make_all_day()
        self.assertEqual(e2.begin, e3.begin)
        self.assertEqual(e2.end, e3.end)

    def test_all_day_outputs_dtstart_value_date(self):
        """All day events should output DTSTART using VALUE=DATE without
        time and timezone in order to assume the user's current timezone

        refs http://www.kanzaki.com/docs/ical/dtstart.html
             http://www.kanzaki.com/docs/ical/date.html
        """
        e = Event(begin="2015/12/21")
        e.make_all_day()
        # no time or tz specifier
        self.assertIn('DTSTART;VALUE=DATE:20151221', str(e).splitlines())

    def test_transparent_input(self):
        c = Calendar(cal19)
        e1 = list(c.events)[0]
        self.assertEqual(e1.transparent, False)

        c2 = Calendar(cal19bis)
        e2 = list(c2.events)[0]
        self.assertEqual(e2.transparent, True)

    def test_default_transparent_input(self):
        c = Calendar(cal18)
        e = next(iter(c.events))
        self.assertEqual(e.transparent, None)

    def test_default_transparent_output(self):
        e = Event(name="Name")
        self.assertNotIn("TRANSP:OPAQUE", str(e).splitlines())

    def test_transparent_output(self):
        e = Event(name="Name", transparent=True)
        self.assertIn("TRANSP:TRANSPARENT", str(e).splitlines())

        e = Event(name="Name", transparent=False)
        self.assertIn("TRANSP:OPAQUE", str(e).splitlines())

    def test_includes_disjoined(self):
        # disjoined events
        event_a = Event(name='Test #1', begin=dt(2016, 6, 10, 20, 10), duration=td(minutes=20))
        event_b = Event(name='Test #2', begin=dt(2016, 6, 10, 20, 50), duration=td(minutes=20))
        assert not event_a.includes(event_b)
        assert not event_b.includes(event_a)

    def test_includes_intersected(self):
        # intersected events
        event_a = Event(name='Test #1', begin=dt(2016, 6, 10, 20, 10), duration=td(minutes=30))
        event_b = Event(name='Test #2', begin=dt(2016, 6, 10, 20, 30), duration=td(minutes=30))
        assert not event_a.includes(event_b)
        assert not event_b.includes(event_a)

        event_a = Event(name='Test #1', begin=dt(2016, 6, 10, 20, 30), duration=td(minutes=30))
        event_b = Event(name='Test #2', begin=dt(2016, 6, 10, 20, 10), duration=td(minutes=30))
        assert not event_a.includes(event_b)
        assert not event_b.includes(event_a)

    def test_includes_included(self):
        # included events
        event_a = Event(name='Test #1', begin=dt(2016, 6, 10, 20, 00), duration=td(minutes=60))
        event_b = Event(name='Test #2', begin=dt(2016, 6, 10, 20, 10), duration=td(minutes=30))
        assert event_a.includes(event_b)
        assert not event_b.includes(event_a)

        event_a = Event(name='Test #1', begin=dt(2016, 6, 10, 20, 10), duration=td(minutes=30))
        event_b = Event(name='Test #2', begin=dt(2016, 6, 10, 20, 00), duration=td(minutes=60))
        assert not event_a.includes(event_b)
        assert event_b.includes(event_a)

    def test_intersects_disjoined(self):
        # disjoined events
        event_a = Event(name='Test #1', begin=dt(2016, 6, 10, 20, 10), duration=td(minutes=20))
        event_b = Event(name='Test #2', begin=dt(2016, 6, 10, 20, 50), duration=td(minutes=20))
        assert not event_a.intersects(event_b)
        assert not event_b.intersects(event_a)

    def test_intersects_intersected(self):
        # intersected events
        event_a = Event(name='Test #1', begin=dt(2016, 6, 10, 20, 10), duration=td(minutes=30))
        event_b = Event(name='Test #2', begin=dt(2016, 6, 10, 20, 30), duration=td(minutes=30))
        assert event_a.intersects(event_b)
        assert event_b.intersects(event_a)

        event_a = Event(name='Test #1', begin=dt(2016, 6, 10, 20, 30), duration=td(minutes=30))
        event_b = Event(name='Test #2', begin=dt(2016, 6, 10, 20, 10), duration=td(minutes=30))
        assert event_a.intersects(event_b)
        assert event_b.intersects(event_a)

    def test_intersects_included(self):
        # included events
        event_a = Event(name='Test #1', begin=dt(2016, 6, 10, 20, 00), duration=td(minutes=60))
        event_b = Event(name='Test #2', begin=dt(2016, 6, 10, 20, 10), duration=td(minutes=30))
        assert event_a.intersects(event_b)
        assert event_b.intersects(event_a)

        event_a = Event(name='Test #1', begin=dt(2016, 6, 10, 20, 10), duration=td(minutes=30))
        event_b = Event(name='Test #2', begin=dt(2016, 6, 10, 20, 00), duration=td(minutes=60))
        assert event_a.intersects(event_b)
        assert event_b.intersects(event_a)

    def test_join_disjoined(self):
        # disjoined events
        event_a = Event(name='Test #1', begin=dt(2016, 6, 10, 20, 10), duration=td(minutes=20))
        event_b = Event(name='Test #2', begin=dt(2016, 6, 10, 20, 50), duration=td(minutes=20))
        with pytest.raises(ValueError):
            event_a.join(event_b)
        with pytest.raises(ValueError):
            event_b.join(event_a)

    def test_join_intersected(self):
        # intersected events
        event_a = Event(name='Test #1', begin=dt(2016, 6, 10, 20, 10), duration=td(minutes=30))
        event_b = Event(name='Test #2', begin=dt(2016, 6, 10, 20, 30), duration=td(minutes=30))
        assert event_a.join(event_b).time_equals(Event(name=None, begin=event_a.begin, end=event_b.end))
        assert event_b.join(event_a).time_equals(Event(name=None, begin=event_a.begin, end=event_b.end))

        event_a = Event(name='Test #1', begin=dt(2016, 6, 10, 20, 30), duration=td(minutes=30))
        event_b = Event(name='Test #2', begin=dt(2016, 6, 10, 20, 10), duration=td(minutes=30))
        assert event_a.join(event_b).time_equals(Event(name=None, begin=event_b.begin, end=event_a.end))
        assert event_b.join(event_a).time_equals(Event(name=None, begin=event_b.begin, end=event_a.end))

    def test_join_included(self):
        # included events
        event_a = Event(name='Test #1', begin=dt(2016, 6, 10, 20, 00), duration=td(minutes=60))
        event_b = Event(name='Test #2', begin=dt(2016, 6, 10, 20, 10), duration=td(minutes=30))
        assert event_a.join(event_b).time_equals(Event(name=None, begin=event_a.begin, end=event_a.end))
        assert event_b.join(event_a).time_equals(Event(name=None, begin=event_a.begin, end=event_a.end))

        event_a = Event(name='Test #1', begin=dt(2016, 6, 10, 20, 10), duration=td(minutes=30))
        event_b = Event(name='Test #2', begin=dt(2016, 6, 10, 20, 00), duration=td(minutes=60))
        assert event_a.join(event_b).time_equals(Event(name=None, begin=event_b.begin, end=event_b.end))
        assert event_b.join(event_a).time_equals(Event(name=None, begin=event_b.begin, end=event_b.end))

        event = Event(uid='0', name='Test #1', begin=dt(2016, 6, 10, 20, 10), duration=td(minutes=30))
        event.join(event)
        assert event == Event(uid='0', name='Test #1', begin=dt(2016, 6, 10, 20, 10), duration=td(minutes=30))

    def test_issue_92(self):
        c = Calendar(cal32)
        e = list(c.events)[0]

        assert e.begin == arrow.get('2016-10-04')
        assert e.end == arrow.get('2016-10-05')

    def test_classification_input(self):
        c = Calendar(cal12)
        e = next(iter(c.events))
        self.assertEqual(None, e.classification)

        c = Calendar(cal33_1)
        e = next(iter(c.events))
        self.assertEqual('PUBLIC', e.classification)

        c = Calendar(cal33_2)
        e = next(iter(c.events))
        self.assertEqual('PRIVATE', e.classification)

        c = Calendar(cal33_3)
        e = next(iter(c.events))
        self.assertEqual('CONFIDENTIAL', e.classification)

        c = Calendar(cal33_4)
        e = next(iter(c.events))
        self.assertEqual('iana-token', e.classification)

        c = Calendar(cal33_5)
        e = next(iter(c.events))
        self.assertEqual('x-name', e.classification)

    def test_classification_output(self):
        e = Event(name="Name")
        self.assertNotIn("CLASS:PUBLIC", str(e).splitlines())

        e = Event(name="Name", classification='PUBLIC')
        self.assertIn("CLASS:PUBLIC", str(e).splitlines())

        e = Event(name="Name", classification='PRIVATE')
        self.assertIn("CLASS:PRIVATE", str(e).splitlines())

        e = Event(name="Name", classification='CONFIDENTIAL')
        self.assertIn("CLASS:CONFIDENTIAL", str(e).splitlines())

        e = Event(name="Name", classification='iana-token')
        self.assertIn("CLASS:iana-token", str(e).splitlines())

        e = Event(name="Name", classification='x-name')
        self.assertIn("CLASS:x-name", str(e).splitlines())

    def test_classification_bool(self):
        with pytest.raises(ValueError):
            Event(name="Name", classification=True)

    def test_last_modified(self):
        c = Calendar(cal18)
        e = list(c.events)[0]

        assert e.last_modified == arrow.get('2015-11-13 00:48:09')

    def equality(self):
        ev1 = Event(begin=dt(2018, 6, 29, 5), end=dt(2018, 6, 29, 7), name="my name")
        ev2 = ev1.clone()

        assert ev1 == ev2

        ev2.uid = "something else"
        assert ev1 == ev2

        ev2.name = "other name"
        assert ev1 != ev2

    def test_attendee_parse(self):
        with open(
            os.path.join(os.path.dirname(__file__), "fixtures/groupscheduled.ics")
        ) as f:
            c = Calendar(f.read())
            e = list(c.events)[0]
            assert len(e.attendees) == 1
