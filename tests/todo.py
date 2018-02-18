import unittest
import pytest
from datetime import datetime
from datetime import timedelta
from arrow.arrow import Arrow

from ics.utils import get_arrow
from ics.parse import Container
from ics.alarm import AlarmFactory, DisplayAlarm
from ics.icalendar import Calendar
from .fixture import cal27

from ics.todo import Todo


TIME_FORMAT = '%Y-%m-%d %H:%M:%S %z'


class TestTodo(unittest.TestCase):

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
        self.assertEqual(t._unused, Container(name='VTODO'))

    def test_init_non_exclusive_arguments(self):
        # attributes percent, priority, begin, due, and duration
        # aren't tested here
        dtstamp = datetime.strptime('2018-02-18 12:19:00 +0000',
                                    TIME_FORMAT)
        completed = dtstamp + timedelta(days=1)
        created = dtstamp + timedelta(seconds=1)
        alarm = [AlarmFactory().get_type_from_action('DISPLAY')]
        alarms = set()
        alarms.update(alarm)

        t = Todo(
            uid='uid',
            dtstamp=dtstamp,
            completed=completed,
            created=created,
            description='description',
            location='location',
            name='name',
            url='url',
            alarms=alarm)

        self.assertEqual(t.uid, 'uid')
        self.assertEqual(t.dtstamp, get_arrow(dtstamp))
        self.assertEqual(t.completed, get_arrow(completed))
        self.assertEqual(t.created, get_arrow(created))
        self.assertEqual(t.description, 'description')
        self.assertEqual(t.location, 'location')
        self.assertEqual(t.name, 'name')
        self.assertEqual(t.url, 'url')
        self.assertSetEqual(t.alarms, alarms)

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
        begin = datetime.strptime('2018-02-18 12:19:00 +0000',
                                  TIME_FORMAT)
        t = Todo(begin=begin)
        self.assertEqual(t.begin, get_arrow(begin))

        # begin after due
        t = Todo(due=1)
        with self.assertRaises(ValueError):
            t.begin = 2

    def test_duration(self):
        begin = datetime.strptime('2018-02-18 12:19:00 +0000',
                                  TIME_FORMAT)
        t1 = Todo(begin=begin, duration={'hours': 1})
        self.assertEqual(t1.duration, timedelta(hours=1))
        t2 = Todo(begin=begin, duration=1)
        self.assertEqual(t2.duration, timedelta(days=1))
        t3 = Todo(begin=begin, duration=timedelta(minutes=1))
        self.assertEqual(t3.duration, timedelta(minutes=1))

        # Calculate duration from begin and due values
        t4 = Todo(begin=begin, due=begin + timedelta(1))
        self.assertEqual(t4.duration, timedelta(1))

    def test_due(self):
        begin = datetime.strptime('2018-02-18 12:19:00 +0000',
                                  TIME_FORMAT)
        due = begin + timedelta(1)
        t1 = Todo(due=due)
        self.assertEqual(t1.due, begin + timedelta(1))

        due = begin - timedelta(1)
        with self.assertRaises(ValueError):
            Todo(begin=begin, due=due)

        # Calculate due from begin and duration value
        t2 = Todo(begin=begin, duration=1)
        self.assertEqual(t2.due, begin + timedelta(1))

    def test_invalid_time_attributes(self):
        # due and duration must not be set at the same time
        with self.assertRaises(ValueError):
            Todo(begin=1, due=2, duration=1)

        # duration requires begin
        with self.assertRaises(ValueError):
            Todo(duration=1)

    def test_repr(self):
        begin = datetime.strptime('2018-02-18 12:19:00 +0000',
                                  TIME_FORMAT)

        t1 = Todo()
        self.assertEqual(repr(t1), '<Todo>')

        t2 = Todo(name='foo')
        self.assertEqual(repr(t2), "<Todo 'foo'>")

        t3 = Todo(name='foo', begin=begin)
        self.assertEqual(repr(t3), "<Todo 'foo' begin:2018-02-18T12:19:00+00:00>")

        t4 = Todo(name='foo', due=begin)
        self.assertEqual(repr(t4), "<Todo 'foo' due:2018-02-18T12:19:00+00:00>")

        t4 = Todo(name='foo', begin=begin, due=begin + timedelta(1))
        self.assertEqual(repr(t4),
                         "<Todo 'foo' begin:2018-02-18T12:19:00+00:00 due:2018-02-19T12:19:00+00:00>")

    def test_todo_lt(self):
        t1 = Todo()
        t2 = Todo(name='a')
        t3 = Todo(name='b')
        t4 = Todo(due=10)
        t5 = Todo(due=20)
        due_time = datetime.strptime('2018-02-18 12:19:00 +0000',
                                     TIME_FORMAT)
        t6 = Todo(due=Arrow.fromdatetime(due_time))

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

        # Check comparison with datetime
        self.assertTrue(t4 < due_time)
        self.assertFalse(t6 < due_time)

        # Check invalid call
        with self.assertRaises(NotImplementedError):
            t1 < due_time
        with self.assertRaises(NotImplementedError):
            t2 < due_time
        with self.assertRaises(NotImplementedError):
            t2 < 1

    def test_todo_le(self):
        t1 = Todo()
        t2 = Todo(name='a')
        t3 = Todo(name='b')
        t4 = Todo(due=10)
        t5 = Todo(due=20)
        due_time = datetime.strptime('2018-02-18 12:19:00 +0000',
                                     TIME_FORMAT)
        t6 = Todo(due=Arrow.fromdatetime(due_time))
        t7 = Todo(due=Arrow.fromdatetime(due_time + timedelta(days=1)))

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

        # Check comparison with datetime
        self.assertTrue(t4 <= due_time)
        self.assertTrue(t6 <= due_time)
        self.assertFalse(t7 <= due_time)

        # Check invalid call
        with self.assertRaises(NotImplementedError):
            t1 <= due_time
        with self.assertRaises(NotImplementedError):
            t2 <= due_time
        with self.assertRaises(NotImplementedError):
            t2 <= 1

    def test_todo_gt(self):
        t1 = Todo()
        t2 = Todo(name='a')
        t3 = Todo(name='b')
        t4 = Todo(due=10)
        t5 = Todo(due=20)
        due_time = datetime.strptime('2018-02-18 12:19:00 +0000',
                                     TIME_FORMAT)
        t6 = Todo(due=Arrow.fromdatetime(due_time))
        t7 = Todo(due=Arrow.fromdatetime(due_time + timedelta(days=1)))

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

        # Check comparison with datetime
        self.assertFalse(t4 > due_time)
        self.assertFalse(t6 > due_time)
        self.assertTrue(t7 > due_time)

        # Check invalid call
        with self.assertRaises(NotImplementedError):
            t1 > due_time
        with self.assertRaises(NotImplementedError):
            t2 > due_time
        with self.assertRaises(NotImplementedError):
            t2 > 1

    def test_todo_ge(self):
        t1 = Todo()
        t2 = Todo(name='a')
        t3 = Todo(name='b')
        t4 = Todo(due=10)
        t5 = Todo(due=20)
        due_time = datetime.strptime('2018-02-18 12:19:00 +0000',
                                     TIME_FORMAT)
        t6 = Todo(due=Arrow.fromdatetime(due_time))
        t7 = Todo(due=Arrow.fromdatetime(due_time + timedelta(days=1)))

        # Check comparison by name
        self.assertTrue(t1 >= t1)
        self.assertTrue(t1 >= t2)
        self.assertFalse(t2 >= t1)
        self.assertFalse(t2 >= t3)
        self.assertTrue(t2 >= t2)
        self.assertTrue(t3 >= t2)

        # Check comparison by due time
        self.assertFalse(t4 >= t5)
        self.assertTrue(t4 >= t4)
        self.assertTrue(t5 >= t4)

        # Check comparison with datetime
        self.assertFalse(t4 >= due_time)
        self.assertTrue(t6 >= due_time)
        self.assertTrue(t7 >= due_time)

        # Check invalid call
        with self.assertRaises(NotImplementedError):
            t1 >= due_time
        with self.assertRaises(NotImplementedError):
            t2 >= due_time
        with self.assertRaises(NotImplementedError):
            t2 >= 1

    def test_todo_eq(self):
        t1 = Todo()
        t2 = Todo()

        self.assertTrue(t1 == t1)
        self.assertFalse(t1 == t2)

        with self.assertRaises(NotImplementedError):
            t1 == 1

    def test_todo_ne(self):
        t1 = Todo()
        t2 = Todo()

        self.assertFalse(t1 != t1)
        self.assertTrue(t1 != t2)

        with self.assertRaises(NotImplementedError):
            t1 != 1

    def test_extract(self):
        c = Calendar(cal27)
        t = c.todos[0]
        self.assertEqual(t.dtstamp, get_arrow('20180218T154741Z'))
        self.assertEqual(t.uid, 'Uid')
        self.assertEqual(t.completed, get_arrow('20180418T150001Z+00:00'))
        self.assertEqual(t.created, get_arrow('20180218T154800Z+00:00'))
        self.assertEqual(t.description, 'Lorem ipsum dolor sit amet.')
        self.assertEqual(t.begin, get_arrow('20180218T164800Z+00:00'))
        self.assertEqual(t.location, 'Earth')
        self.assertEqual(t.percent, 0)
        self.assertEqual(t.priority, 0)
        self.assertEqual(t.name, 'Name')
        self.assertEqual(t.url, 'Url')
        self.assertEqual(len(t.alarms), 1)
