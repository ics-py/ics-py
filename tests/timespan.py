import itertools
from datetime import datetime as dt, timedelta as td

import dateutil
import pytest

from ics.timespan import EventTimespan
from ics.utils import floor_datetime_to_midnight


class TestEventTimespan(object):
    data = []

    def assert_end_eq_duration(self, by_dur: EventTimespan, by_end: EventTimespan):

        assert by_dur.get_begin() == by_end.get_begin()
        assert by_dur.get_effective_end() == by_end.get_effective_end()
        assert by_dur.get_effective_duration() == by_end.get_effective_duration()
        assert by_dur.get_precision() == by_end.get_precision()
        assert by_dur == by_end.convert_end("duration")
        assert by_end == by_dur.convert_end("end")

    def assert_make_all_day_valid(self, ts_secs: EventTimespan, ts_days: EventTimespan):
        # check resolution for all_day
        assert ts_days.get_effective_duration() % td(days=1) == td(0)
        assert floor_datetime_to_midnight(ts_days.get_begin()) == ts_days.get_begin()
        assert floor_datetime_to_midnight(ts_days.get_effective_end()) == ts_days.get_effective_end()

        # minimum duration is 0s / 1d
        assert ts_secs.get_effective_duration() >= td()
        assert ts_days.get_effective_duration() >= td(days=1)

        # test inclusion and boundaries
        ts_days_begin_wtz = ts_days.get_begin().replace(tzinfo=ts_secs.get_begin().tzinfo)
        ts_days_eff_end_wtz = ts_days.get_effective_end().replace(tzinfo=ts_secs.get_effective_end().tzinfo)
        assert ts_days_begin_wtz <= ts_secs.get_begin()
        assert ts_days_eff_end_wtz >= ts_secs.get_effective_end()
        assert ts_days.get_effective_duration() >= ts_secs.get_effective_duration()

        # test that we didn't decrease anything
        begin_earlier = ts_secs.get_begin() - ts_days_begin_wtz
        end_later = ts_days_eff_end_wtz - ts_secs.get_effective_end()
        duration_bigger = ts_days.get_effective_duration() - ts_secs.get_effective_duration()
        assert begin_earlier >= td()
        assert end_later >= td()
        assert duration_bigger >= td()

        # test that we didn't drift too far
        assert begin_earlier < td(hours=24)
        instant_to_one_day = (ts_secs.get_begin().hour == 0 and ts_secs.get_effective_duration() == td())
        if instant_to_one_day:
            assert end_later == td(hours=24)
        else:
            assert end_later < td(hours=24)
        # NOTICE: duration might grow by 48h, not only 24, as we floor the begin time (which might be 23:59)
        # and ceil the end time (which might be 00:01)
        assert duration_bigger < td(hours=24 * 2)

        # test that we made no unnecessary modification
        if ts_secs.get_begin() == floor_datetime_to_midnight(ts_secs.get_begin()):
            assert ts_days.get_begin() == ts_secs.get_begin().replace(tzinfo=None)
        if ts_secs.get_effective_end() == floor_datetime_to_midnight(ts_secs.get_effective_end()):
            if instant_to_one_day:
                # here we need to convert duration=0 to duration=1d
                assert ts_days.get_effective_end() == ts_secs.get_effective_end().replace(tzinfo=None) + td(days=1)
            else:
                assert ts_days.get_effective_end() == ts_secs.get_effective_end().replace(tzinfo=None)

        # the following won't hold for events that don't start at 00:00, compare NOTICE above
        if ts_secs.get_begin().hour == 0:
            if instant_to_one_day:
                # here we need to convert duration=0 to duration=1d
                assert duration_bigger == td(hours=24)
            else:
                # if we start at midnight, only the end time is ceiled, which can only add up to 24h instead of 48h
                assert duration_bigger < td(hours=24)

            mod_duration = (ts_secs.get_effective_duration() % td(days=1))
            if ts_secs.get_effective_duration() <= td(days=1):
                # here we need to convert duration<1d to duration=1d
                assert ts_days.get_effective_duration() == td(days=1)
            elif mod_duration == td():
                assert ts_days.get_effective_duration() == ts_secs.get_effective_duration()
            else:
                assert ts_days.get_effective_duration() == ts_secs.get_effective_duration() + td(days=1) - mod_duration

        # log data
        if self.data is not None:
            self.data.append((
                str(ts_secs), ts_secs.get_effective_duration().days * 24 + ts_secs.get_effective_duration().seconds / 3600,
                str(ts_days), ts_days.get_effective_duration().days * 24 + ts_days.get_effective_duration().seconds / 3600,
                begin_earlier, end_later, duration_bigger,
            ))

    # this generates quite a lot of different dates, but make_all_day is hard, so better test more corner cases than less
    @pytest.mark.parametrize(["begin_tz", "begin_hour", "dur_hours"], [
        (begin_tz, begin_hour, dur_hours)
        for begin_tz in range(-3, 3)
        for begin_hour in range(-3, 3)
        for dur_hours in itertools.chain(range(0, 5), range(24 - 4, 24 + 5), range(48 - 4, 48 + 5))
    ])
    def test(self, begin_tz, begin_hour, dur_hours):
        tzoffset = dateutil.tz.tzoffset("%+03d:00" % begin_tz, td(hours=begin_tz))
        start = dt(2019, 5, 29, tzinfo=tzoffset) + td(hours=begin_hour)
        timespan_seconds = EventTimespan(begin_time=start, duration=td(hours=dur_hours))
        timespan_all_day = timespan_seconds.make_all_day()

        timespan_seconds_end = EventTimespan(begin_time=start, end_time=start + td(hours=dur_hours))
        timespan_all_day_end = timespan_seconds_end.make_all_day()

        # TODO none of the following will hold if begin_tz and end_tz differ - e.g. for plane flights
        self.assert_end_eq_duration(timespan_seconds, timespan_seconds_end)
        self.assert_end_eq_duration(timespan_all_day, timespan_all_day_end)
        self.assert_make_all_day_valid(timespan_seconds, timespan_all_day)

        # for end_tz in range(-3, 3):

        # from tabulate import tabulate
        # if self.data:
        #     print(tabulate(self.data, headers=("hourly event", "hourly duration", "all-day event", "all-day duration",
        #                                        "begins earlier by", "ends later by", "duration bigger by")))
