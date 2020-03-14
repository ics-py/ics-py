import unittest
from datetime import datetime, datetime as dt, timedelta, timezone

from dateutil.tz import UTC as dateutil_tzutc

from ics.alarm.display import DisplayAlarm
from ics.grammar.parse import Container
from ics.icalendar import Calendar
from ics.todo import Todo
from .fixture import cal27, cal28, cal29, cal30, cal31

datetime_tzutc = timezone.utc

CRLF = "\r\n"


class TestTodo(unittest.TestCase):
    maxDiff = None

    def test_init(self):
        t = Todo()
        self.assertIsNotNone(t.uid)
        self.assertIsNotNone(t.dtstamp)
        self.assertIsNone(t.completed)
        self.assertIsNone(t.created)
        self.assertIsNone(t.description)
        self.assertIsNone(t.begin)
        self.assertIsNone(t.location)
        self.assertIsNone(t.percent)
        self.assertIsNone(t.priority)
        self.assertIsNone(t.name)
        self.assertIsNone(t.url)
        self.assertIsNone(t.status)
        self.assertEqual(t.extra, Container(name='VTODO'))

    def test_init_non_exclusive_arguments(self):
        # attributes percent, priority, begin, due, and duration
        # aren't tested here
        dtstamp = datetime(2018, 2, 18, 12, 19, tzinfo=datetime_tzutc)
        completed = dtstamp + timedelta(days=1)
        created = dtstamp + timedelta(seconds=1)
        alarms = [DisplayAlarm]

        t = Todo(
            uid='uid',
            dtstamp=dtstamp,
            completed=completed,
            created=created,
            description='description',
            location='location',
            name='name',
            url='url',
            alarms=alarms)

        self.assertEqual(t.uid, 'uid')
        self.assertEqual(t.dtstamp, dtstamp)
        self.assertEqual(t.completed, completed)
        self.assertEqual(t.created, created)
        self.assertEqual(t.description, 'description')
        self.assertEqual(t.location, 'location')
        self.assertEqual(t.name, 'name')
        self.assertEqual(t.url, 'url')
        self.assertEqual(t.alarms, alarms)

    def test_percent(self):
        t1 = Todo(percent=0)
        self.assertEqual(t1.percent, 0)
        t2 = Todo(percent=100)
        self.assertEqual(t2.percent, 100)
        with self.assertRaises(ValueError):
            Todo(percent=-1)
        with self.assertRaises(ValueError):
            Todo(percent=101)

    def test_priority(self):
        t1 = Todo(priority=0)
        self.assertEqual(t1.priority, 0)
        t2 = Todo(priority=9)
        self.assertEqual(t2.priority, 9)
        with self.assertRaises(ValueError):
            Todo(priority=-1)
        with self.assertRaises(ValueError):
            Todo(priority=10)

    def test_begin(self):
        begin = datetime(2018, 2, 18, 12, 19, tzinfo=datetime_tzutc)
        t = Todo(begin=begin)
        self.assertEqual(t.begin, begin)

        # begin after due
        t = Todo(due=datetime.fromtimestamp(1))
        with self.assertRaises(ValueError):
            t.begin = datetime.fromtimestamp(2)

    def test_duration(self):
        begin = datetime(2018, 2, 18, 12, 19, tzinfo=datetime_tzutc)
        t1 = Todo(begin=begin, duration={'hours': 1})
        self.assertEqual(t1.duration, timedelta(hours=1))
        t2 = Todo(begin=begin, duration=(1,))
        self.assertEqual(t2.duration, timedelta(days=1))
        t3 = Todo(begin=begin, duration=timedelta(minutes=1))
        self.assertEqual(t3.duration, timedelta(minutes=1))

        # Calculate duration from begin and due values
        t4 = Todo(begin=begin, due=begin + timedelta(1))
        self.assertEqual(t4.duration, timedelta(1))

    def test_due(self):
        begin = datetime(2018, 2, 18, 12, 19, tzinfo=datetime_tzutc)
        due = begin + timedelta(1)
        t1 = Todo(due=due)
        self.assertEqual(t1.due, begin + timedelta(1))

        due = begin - timedelta(1)
        with self.assertRaises(ValueError):
            Todo(begin=begin, due=due)

        # Calculate due from begin and duration value
        t2 = Todo(begin=begin, duration=(1,))
        self.assertEqual(t2.due, begin + timedelta(1))

    def test_invalid_time_attributes(self):
        # due and duration must not be set at the same time
        with self.assertRaises(ValueError):
            Todo(begin=datetime.now(), due=datetime.now() + timedelta(1), duration=timedelta(1))

        # duration requires begin
        with self.assertRaises(ValueError):
            Todo(duration=timedelta(1))

    def test_repr(self):
        begin = datetime(2018, 2, 18, 12, 19, tzinfo=datetime_tzutc)

        t1 = Todo()
        self.assertEqual(repr(t1), '<floating Todo>')

        t2 = Todo(name='foo')
        self.assertEqual(repr(t2), "<floating Todo 'foo'>")

        t3 = Todo(name='foo', begin=begin)
        self.assertEqual(repr(t3), "<Todo 'foo' begin: 2018-02-18 12:19:00+00:00>")

        t4 = Todo(name='foo', due=begin)
        self.assertEqual(repr(t4), "<Todo 'foo' fixed due: 2018-02-18 12:19:00+00:00>")

        t4 = Todo(name='foo', begin=begin, due=begin + timedelta(1))
        self.assertEqual(repr(t4),
                         "<Todo 'foo' begin: 2018-02-18 12:19:00+00:00 fixed due: 2018-02-19 12:19:00+00:00 duration: 1 day, 0:00:00>")

    def test_todo_lt(self):
        t1 = Todo()
        t2 = Todo(name='a')
        t3 = Todo(name='b')
        t4 = Todo(due=datetime.fromtimestamp(10))
        t5 = Todo(due=datetime.fromtimestamp(20))

        # Check comparison by name
        self.assertFalse(t1 < t1)
        self.assertTrue(t1 < t2)
        self.assertFalse(t2 < t1)
        self.assertTrue(t2 < t3)
        self.assertFalse(t3 < t2)

        # Check comparison by due time
        self.assertTrue(t4 < t5)
        self.assertFalse(t4 < t4)
        self.assertFalse(t5 < t4)

        # Check invalid call
        with self.assertRaises(TypeError):
            t4 > t4.due
        with self.assertRaises(TypeError):
            t2 < 1

    def test_todo_le(self):
        t1 = Todo()
        t2 = Todo(name='a')
        t3 = Todo(name='b')
        t4 = Todo(due=datetime.fromtimestamp(10))
        t5 = Todo(due=datetime.fromtimestamp(20))

        # Check comparison by name
        self.assertTrue(t1 <= t1)
        self.assertTrue(t1 <= t2)
        self.assertFalse(t2 <= t1)
        self.assertTrue(t2 <= t3)
        self.assertTrue(t2 <= t2)
        self.assertFalse(t3 <= t2)

        # Check comparison by due time
        self.assertTrue(t4 <= t5)
        self.assertTrue(t4 <= t4)
        self.assertFalse(t5 <= t4)

        # Check invalid call
        with self.assertRaises(TypeError):
            t4 > t4.due
        with self.assertRaises(TypeError):
            t2 <= 1

    def test_todo_gt(self):
        t1 = Todo()
        t2 = Todo(name='a')
        t3 = Todo(name='b')
        t4 = Todo(due=datetime.fromtimestamp(10))
        t5 = Todo(due=datetime.fromtimestamp(20))

        # Check comparison by name
        self.assertFalse(t1 > t1)
        self.assertFalse(t1 > t2)
        self.assertTrue(t2 > t1)
        self.assertFalse(t2 > t3)
        self.assertFalse(t2 > t2)
        self.assertTrue(t3 > t2)

        # Check comparison by due time
        self.assertFalse(t4 > t5)
        self.assertFalse(t4 > t4)
        self.assertTrue(t5 > t4)

        # Check invalid call
        with self.assertRaises(TypeError):
            t4 > t4.due
        with self.assertRaises(TypeError):
            t2 > 1

    def test_todo_ge(self):
        t1 = Todo()
        t2 = Todo(name='a')
        t3 = Todo(name='b')
        t4 = Todo(due=datetime.fromtimestamp(10))
        t5 = Todo(due=datetime.fromtimestamp(20))

        # Check comparison by name
        self.assertTrue(t1 >= t1)
        self.assertTrue(t1 <= t2)
        self.assertFalse(t2 <= t1)
        self.assertFalse(t2 >= t3)
        self.assertTrue(t2 >= t2)
        self.assertTrue(t3 >= t2)

        # Check comparison by due time
        self.assertFalse(t4 >= t5)
        self.assertTrue(t4 >= t4)
        self.assertTrue(t5 >= t4)

        # Check invalid call
        with self.assertRaises(TypeError):
            t4 > t4.due
        with self.assertRaises(TypeError):
            t2 >= 1

    def test_todo_eq(self):
        t1 = Todo()
        t2 = Todo()

        self.assertTrue(t1 == t1)
        self.assertFalse(t1 == t2)

    def test_todo_ne(self):
        t1 = Todo()
        t2 = Todo()

        self.assertFalse(t1 != t1)
        self.assertTrue(t1 != t2)

    def test_extract(self):
        c = Calendar(cal27)
        t = next(iter(c.todos))
        self.assertEqual(t.dtstamp, dt(2018, 2, 18, 15, 47, 00, tzinfo=dateutil_tzutc))
        self.assertEqual(t.uid, 'Uid')
        self.assertEqual(t.completed, dt(2018, 4, 18, 15, 00, 00, tzinfo=dateutil_tzutc))
        self.assertEqual(t.created, dt(2018, 2, 18, 15, 48, 00, tzinfo=dateutil_tzutc))
        self.assertEqual(t.description, 'Lorem ipsum dolor sit amet.')
        self.assertEqual(t.begin, dt(2018, 2, 18, 16, 48, 00, tzinfo=dateutil_tzutc))
        self.assertEqual(t.location, 'Earth')
        self.assertEqual(t.percent, 0)
        self.assertEqual(t.priority, 0)
        self.assertEqual(t.name, 'Name')
        self.assertEqual(t.url, 'https://www.example.com/cal.php/todo.ics')
        self.assertEqual(t.duration, timedelta(minutes=10))
        self.assertEqual(len(t.alarms), 1)

    def test_extract_due(self):
        c = Calendar(cal28)
        t = next(iter(c.todos))
        self.assertEqual(t.due, dt(2018, 2, 18, 16, 48, 00, tzinfo=dateutil_tzutc))

    def test_extract_due_error_duration(self):
        with self.assertRaises(ValueError):
            Calendar(cal29)

    def test_extract_duration_error_due(self):
        with self.assertRaises(ValueError):
            Calendar(cal30)

    def test_output(self):
        c = Calendar(cal27)
        t = next(iter(c.todos))

        test_str = CRLF.join(("BEGIN:VTODO",
                              "SEQUENCE:0",
                              "BEGIN:VALARM",
                              "ACTION:DISPLAY",
                              "DESCRIPTION:Event reminder",
                              "TRIGGER:PT1H",
                              "END:VALARM",
                              "COMPLETED:20180418T150000Z",
                              "CREATED:20180218T154800Z",
                              "DESCRIPTION:Lorem ipsum dolor sit amet.",
                              "DTSTAMP:20180218T154700Z",
                              "DURATION:PT10M",
                              "LOCATION:Earth",
                              "PERCENT-COMPLETE:0",
                              "PRIORITY:0",
                              "DTSTART:20180218T164800Z",
                              "SUMMARY:Name",
                              "UID:Uid",
                              "URL:https://www.example.com/cal.php/todo.ics",
                              "END:VTODO"))
        self.assertEqual(str(t), test_str)

    def test_output_due(self):
        dtstamp = datetime(2018, 2, 19, 21, 00, tzinfo=datetime_tzutc)
        due = datetime(2018, 2, 20, 1, 00, tzinfo=datetime_tzutc)
        t = Todo(dtstamp=dtstamp, uid='Uid', due=due)

        test_str = CRLF.join(("BEGIN:VTODO",
                              "DTSTAMP:20180219T210000Z",
                              "DUE:20180220T010000Z",
                              "UID:Uid",
                              "END:VTODO"))
        self.assertEqual(str(t), test_str)

    def test_unescape_texts(self):
        c = Calendar(cal31)
        t = next(iter(c.todos))
        self.assertEqual(t.name, "Hello, \n World; This is a backslash : \\ and another new \n line")
        self.assertEqual(t.location, "In, every text field")
        self.assertEqual(t.description, "Yes, all of them;")

    def test_escape_output(self):
        dtstamp = datetime(2018, 2, 19, 21, 00, tzinfo=datetime_tzutc)
        t = Todo(dtstamp=dtstamp, uid='Uid')

        t.name = "Hello, with \\ special; chars and \n newlines"
        t.location = "Here; too"
        t.description = "Every\nwhere ! Yes, yes !"

        test_str = CRLF.join(("BEGIN:VTODO",
                              "DESCRIPTION:Every\\nwhere ! Yes\\, yes !",
                              "DTSTAMP:20180219T210000Z",
                              "LOCATION:Here\\; too",
                              "SUMMARY:Hello\\, with \\\\ special\\; chars and \\n newlines",
                              "UID:Uid",
                              "END:VTODO"))
        self.assertEqual(str(t), test_str)
