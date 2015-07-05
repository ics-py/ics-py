import unittest
from datetime import date, datetime, timedelta, tzinfo
from dateutil.tz import tzstr
from ics.parse import ParseError, ContentLine, string_to_container
from ics.utils import (tzutc, parse_duration, timedelta_to_duration, remove_x, iso_to_arrow,
                       get_date_or_datetime, parse_date_or_datetime, parse_date,
                       parse_cal_date, parse_cal_datetime)

from tests.fixture import cal1, calendar_without_prodid


class TestParseDuration(unittest.TestCase):
    dataset_simple = {
        'P1W': (7, 0), 'P1D': (1, 0), '-P1D': (-1, 0),
        'P1H': (0, 3600), 'P1M': (0, 60), 'P1S': (0, 1),
        'PT1H': (0, 3600), 'PT1M': (0, 60), 'PT1S': (0, 1),
        'PT': (0, 0)
    }

    dataset_combined = {
        "P1D1WT1H": (8, 3600), "P1DT1H1W": (8, 3600), "P1DT1H1M1W": (8, 3660),
        "P1DT1H1M1S1W": (8, 3661), "P1DT1H": (1, 3600), "P1DT1H1M": (1, 3660),
        "PT1S1M": (0, 61)
    }

    def run_on_dataset(self, dataset):
        for test in dataset:
            expected = dataset[test]
            self.assertEqual(parse_duration(test), timedelta(*expected))

    def test_simple(self):
        self.run_on_dataset(self.dataset_simple)

    def test_combined(self):
        self.run_on_dataset(self.dataset_combined)

    def test_no_p(self):
        self.assertRaises(ParseError, parse_duration, 'caca')

    def test_two_letters(self):
        self.assertRaises(ParseError, parse_duration, 'P1DF')

    def test_two_occurences(self):
        self.assertRaises(ParseError, parse_duration, 'P1D1D')


class TestTimedeltaToDuration(unittest.TestCase):
    dataset_simple = {
        (0, 0): 'P',
        (0, 1): 'PT1S', (0, 60): 'PT1M', (0, 3600): 'PT1H',
        (1, 0): 'P1D', (7, 0): 'P1W',
    }

    dataset_combined = {
        (1, 1): 'P1DT1S', (8, 3661): 'P1W1DT1H1M1S', (15, 18020): 'P2W1DT5H20S',
    }

    def run_on_dataset(self, dataset):
        for test in dataset:
            expected = dataset[test]
            self.assertEqual(timedelta_to_duration(timedelta(*test)), expected)

    def test_simple(self):
        self.run_on_dataset(self.dataset_simple)

    def test_combined(self):
        self.run_on_dataset(self.dataset_combined)


class TestRemoveX(unittest.TestCase):

    def test_with_x(self):
        c = string_to_container(cal1)[0]
        remove_x(c)
        for line in c:
            self.assertFalse(line.name.startswith('X-'))

    def test_without_x(self):
        c = string_to_container(calendar_without_prodid)[0]
        c2 = string_to_container(calendar_without_prodid)[0]
        remove_x(c)
        self.assertSequenceEqual(c, c2)


class TestIso_to_arrow(unittest.TestCase):

    def test_none(self):
        self.assertIs(None, iso_to_arrow(None))

    # TODO: Test with data


class TestGet_date_or_datetime(unittest.TestCase):

    def test_get_date_or_datetime(self):
        self.assertEqual(None, get_date_or_datetime(None))
        d = date(2015, 7, 1)
        dt = datetime(2015, 7, 1, 10, 30)
        self.assertEqual(d, get_date_or_datetime(d))
        self.assertEqual(dt, get_date_or_datetime(dt))
        self.assertEqual(d, get_date_or_datetime('20150701'))
        self.assertEqual(dt, get_date_or_datetime('2015-07-01 10:30:00'))
        self.assertEqual(dt, get_date_or_datetime((2015, 07, 01, 10, 30)))
        self.assertEqual(dt, get_date_or_datetime(dict(year=2015, month=07,
            day=01, hour=10, minute=30)))
        self.assertEqual(datetime.fromtimestamp(1, tz=tzutc),
                         get_date_or_datetime(1))
        self.assertEqual(datetime.fromtimestamp(1.1, tz=tzutc),
                         get_date_or_datetime(1.1))
        self.assertEqual(None, parse_date_or_datetime('Test'))

    def test_get_date_or_datetime_with_zimezone(self):
        class CET(tzinfo):
            """minimal Timezone for Central European Time (no dst)"""
            def utcoffset(self, dt):
                return timedelta(hours=1)
            def dst(self, dt):
                return timedelta(0)
            def tzname(self, dt):
                return 'CET'

        cet = CET()
        self.assertEqual(None, get_date_or_datetime(None, cet))
        dt = datetime(2015, 7, 1, 10, 30, tzinfo=cet)
        self.assertEqual(dt, get_date_or_datetime('2015-07-01 10:30:00', cet))
        self.assertEqual(dt, get_date_or_datetime((2015, 07, 01, 10, 30), cet))
        self.assertEqual(dt, get_date_or_datetime(dict(year=2015, month=07,
            day=01, hour=10, minute=30, tzinfo=cet)))
        self.assertEqual(datetime(1970, 1, 1, 1, 0, 1, tzinfo=cet),
                         get_date_or_datetime(1, cet))
        self.assertEqual(datetime(1970, 1, 1, 1, 0, 1, 100000, tzinfo=cet),
                         get_date_or_datetime(1.1, cet))
        self.assertEqual(None, parse_date_or_datetime('Test', cet))


class TestParse_date_or_datetime(unittest.TestCase):

    def test_parse_date_or_datetime(self):
        d = date(2015, 7, 1)
        dt = datetime(2015, 7, 1, 10, 30)
        self.assertEqual(d, parse_date_or_datetime('20150701'))
        self.assertEqual(d, parse_date_or_datetime('2015/07/01'))
        self.assertEqual(d, parse_date_or_datetime('2015-07-01'))
        self.assertEqual(dt, parse_date_or_datetime('2015-07-01 10:30:00'))
        self.assertEqual(dt, parse_date_or_datetime('2015-07-01T10:30:00'))
        self.assertEqual(dt, parse_date_or_datetime('20150701T103000'))
        self.assertRaises(ValueError, parse_date_or_datetime, None)
        self.assertRaises(ValueError, parse_date_or_datetime, 17)
        self.assertRaises(ValueError, parse_date_or_datetime, d)
        self.assertEqual(None, parse_date_or_datetime('Test'))


class TestParse_date(unittest.TestCase):

    def test_parse_date(self):
        d = date(2015, 7, 1)
        self.assertEqual(d, parse_date('20150701'))
        self.assertEqual(d, parse_date('2015/07/01'))
        self.assertEqual(d, parse_date('2015-07-01'))
        self.assertEqual(None, parse_date(None))
        self.assertEqual(17, parse_date(17))
        self.assertEqual(d, parse_date(d))
        self.assertEqual('Test', parse_date('Test'))


class TestParse_cal_date(unittest.TestCase):

    def test_parse_cal_date(self):
        self.assertEqual(date(2015, 7, 1), parse_cal_date('20150701'))


class TestParse_cal_datetime(unittest.TestCase):

    def test_parse_cal_datetime(self):
        cl = ContentLine.parse('DTSTART:20150701T060000')
        self.assertEqual(datetime(2015, 7, 1, 6), parse_cal_datetime(cl))
        cl = ContentLine.parse('DTSTART:20150701T060000Z')
        self.assertEqual(datetime(2015, 7, 1, 6, tzinfo=tzutc),
                         parse_cal_datetime(cl))
        cl = ContentLine.parse('DTSTART;TZID=America/New_York:20150701T060000Z')
        self.assertEqual(datetime(2015, 7, 1, 6, tzinfo=tzstr('America/New_York')),
                         parse_cal_datetime(cl))
