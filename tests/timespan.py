import itertools
import unittest
from datetime import timedelta as td

import arrow

from ics.timespan import Timespan
from ics.utils import floor_datetime_to_midnight


class TestTimespan(unittest.TestCase):
    def setUp(self) -> None:
        super().setUp()
        self.data = []

    def assert_end_eq_duration(self, by_dur: Timespan, by_end: Timespan):
        self.assertEqual(by_dur.get_begin(), by_end.get_begin())
        self.assertEqual(by_dur.get_effective_end(), by_end.get_effective_end())
        self.assertEqual(by_dur.get_effective_duration(), by_end.get_effective_duration())
        self.assertEqual(by_dur.get_precision(), by_end.get_precision())
        self.assertEqual(by_dur, by_end.convert_end("duration"))
        self.assertEqual(by_end, by_dur.convert_end("end"))

    def assert_make_all_day_valid(self, ts_secs: Timespan, ts_days: Timespan):
        # check resolution for all_day
        self.assertEqual(ts_days.get_effective_duration() % td(days=1), td(0))
        self.assertEqual(floor_datetime_to_midnight(ts_days.get_begin()), ts_days.get_begin())
        self.assertEqual(floor_datetime_to_midnight(ts_days.get_effective_end()), ts_days.get_effective_end())

        # minimum duration is 0s / 1d
        self.assertGreaterEqual(ts_secs.get_effective_duration(), td())
        self.assertGreaterEqual(ts_days.get_effective_duration(), td(days=1))

        # test inclusion and boundaries
        ts_days_begin_wtz = ts_days.get_begin().replace(tzinfo=ts_secs.get_begin().tzinfo)
        ts_days_eff_end_wtz = ts_days.get_effective_end().replace(tzinfo=ts_secs.get_effective_end().tzinfo)
        self.assertLessEqual(ts_days_begin_wtz, ts_secs.get_begin())
        self.assertGreaterEqual(ts_days_eff_end_wtz, ts_secs.get_effective_end())
        self.assertGreaterEqual(ts_days.get_effective_duration(), ts_secs.get_effective_duration())

        # test that we didn't decrease anything
        begin_earlier = ts_secs.get_begin() - ts_days_begin_wtz
        end_later = ts_days_eff_end_wtz - ts_secs.get_effective_end()
        duration_bigger = ts_days.get_effective_duration() - ts_secs.get_effective_duration()
        self.assertGreaterEqual(begin_earlier, td())
        self.assertGreaterEqual(end_later, td())
        self.assertGreaterEqual(duration_bigger, td())

        # test that we didn't drift too far
        self.assertLess(begin_earlier, td(hours=24))
        instant_to_one_day = (ts_secs.get_begin().hour == 0 and ts_secs.get_effective_duration() == td())
        if instant_to_one_day:
            self.assertEqual(end_later, td(hours=24))
        else:
            self.assertLess(end_later, td(hours=24))
        # NOTICE: duration might grow by 48h, not only 24, as we floor the begin time (which might be 23:59)
        # and ceil the end time (which might be 00:01)
        self.assertLess(duration_bigger, td(hours=24 * 2))

        # test that we made no unnecessary modification
        if ts_secs.get_begin() == floor_datetime_to_midnight(ts_secs.get_begin()):
            self.assertEqual(ts_days.get_begin(), ts_secs.get_begin().replace(tzinfo=None))
        if ts_secs.get_effective_end() == floor_datetime_to_midnight(ts_secs.get_effective_end()):
            if instant_to_one_day:
                # here we need to convert duration=0 to duration=1d
                self.assertEqual(ts_days.get_effective_end(),
                                 ts_secs.get_effective_end().replace(tzinfo=None) + td(days=1))
            else:
                self.assertEqual(ts_days.get_effective_end(),
                                 ts_secs.get_effective_end().replace(tzinfo=None))

        # the following won't hold for events that don't start at 00:00, compare NOTICE above
        if ts_secs.get_begin().hour == 0:
            if instant_to_one_day:
                # here we need to convert duration=0 to duration=1d
                self.assertEqual(duration_bigger, td(hours=24))
            else:
                # if we start at midnight, only the end time is ceiled, which can only add up to 24h instead of 48h
                self.assertLess(duration_bigger, td(hours=24))

            mod_duration = (ts_secs.get_effective_duration() % td(days=1))
            if ts_secs.get_effective_duration() <= td(days=1):
                # here we need to convert duration<1d to duration=1d
                self.assertEqual(ts_days.get_effective_duration(), td(days=1))
            elif mod_duration == td():
                self.assertEqual(ts_days.get_effective_duration(), ts_secs.get_effective_duration())
            else:
                self.assertEqual(ts_days.get_effective_duration(), ts_secs.get_effective_duration() + td(days=1) - mod_duration)

        # log data
        if self.data is not None:
            self.data.append((
                str(ts_secs), ts_secs.get_effective_duration().days * 24 + ts_secs.get_effective_duration().seconds / 3600,
                str(ts_days), ts_days.get_effective_duration().days * 24 + ts_days.get_effective_duration().seconds / 3600,
                begin_earlier, end_later, duration_bigger,
            ))

    def test(self):
        # this generates quite a lot of different dates, but make_all_day is hard, so better test more corner cases than less
        for begin_tz in range(-3, 3):
            for begin_hour in range(-3, 3):
                for dur_hours in itertools.chain(range(0, 5), range(24 - 4, 24 + 5), range(48 - 4, 48 + 5)):
                    start = arrow.Arrow(2019, 5, 29, tzinfo="%+03d:00" % begin_tz).shift(hours=begin_hour)
                    timespan_seconds = Timespan(begin_time=start.datetime, duration=td(hours=dur_hours))
                    timespan_all_day = timespan_seconds.make_all_day()

                    timespan_seconds_end = Timespan(begin_time=start.datetime, end_time=start.shift(hours=dur_hours).datetime)
                    timespan_all_day_end = timespan_seconds_end.make_all_day()

                    # TODO none of the following will hold if begin_tz and end_tz differ - e.g. for plane flights
                    self.assert_end_eq_duration(timespan_seconds, timespan_seconds_end)
                    self.assert_end_eq_duration(timespan_all_day, timespan_all_day_end)
                    self.assert_make_all_day_valid(timespan_seconds, timespan_all_day)

                    # for end_tz in range(-3, 3):

        from tabulate import tabulate
        if self.data:
            print(tabulate(self.data, headers=("hourly event", "hourly duration", "all-day event", "all-day duration",
                                               "begins earlier by", "ends later by", "duration bigger by")))
