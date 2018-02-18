import unittest
import pytest
from datetime import datetime
from datetime import timedelta
from arrow.arrow import Arrow

from ics.parse import Container
from ics.todo import Todo


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

    def test_todo_lt(self):
        t1 = Todo()
        t2 = Todo(name='a')
        t3 = Todo(name='b')
        t4 = Todo(due=10)
        t5 = Todo(due=20)
        due_time = datetime.strptime('2018-02-18 12:19:00 +0000',
                                     '%Y-%m-%d %H:%M:%S %z')
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
                                     '%Y-%m-%d %H:%M:%S %z')
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
                                     '%Y-%m-%d %H:%M:%S %z')
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
                                     '%Y-%m-%d %H:%M:%S %z')
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


