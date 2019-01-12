from arrow import Arrow
from .utils import arrow_to_iso


class Repeatable:
    """Represents a recurrence rule."""

    _TYPE = "RRULE"
    _FREQ_POSSIBLES = {"DAILY": "days",
                       "WEEKLY": "weeks",
                       "MONTHLY": "months",
                       "YEARLY": "years"}

    _WEEKDAY_POSSIBLES = {"SU": "Sunday",
                          "MO": "Monday",
                          "TU": "Tuesday",
                          "WE": "Wednesday",
                          "TH": "Thursday",
                          "FR": "Friday",
                          "SA": "Saturday"}
    def __init__(self,
                 freq="DAILY",
                 until=None,
                 count=None,
                 interval=1,
                 byday=None,
                 bymonthday=None,
                 byyearday=None,
                 byweekno=None,
                 bymonth=None):
        """Instantiate a new Repeatable rule.

        :param freq: str
        :param until: Arrow-compatible
        :param count: int
        :param interval: int
        :param bysecond: list
        :param byminute: list
        :param byhour: list
        :param byday: list
        :param bymonthday: list
        :param byyearday: list
        :param byweekno: list
        :param bymonth: list
        """
        self._freq = None
        self._until = None
        self._count = None
        self._interval = None
        self._byday = None
        self._bymonthday = None
        self._byyearday = None
        self._byweekno = None
        self._bymonth = None

        self.freq = freq
        self.until = until
        self.count = count
        self.interval = interval
        self.byday = byday
        self.bymonthday = bymonthday
        self.byyearday = byyearday
        self.byweekno = byweekno
        self.bymonth = bymonth

    @property
    def freq(self):
        """Get/set frequency value.

        Frequency should be one of the keys of _FREQ_POSSIBLES, i.e.,
        ["SECONDLY", "MINUTELY", "HOURLY", "DAILY", "WEEKLY", "MONTHLY", "YEARLY"]

        :return str
        """
        return self._freq

    @freq.setter
    def freq(self, value):
        if not value:
            return

        value = value.upper()

        if value not in self._FREQ_POSSIBLES:
            raise ValueError("Frequency should be in {}".format(list(self._FREQ_POSSIBLES.keys())))

        self._freq = value

    @property
    def until(self):
        """Get/set until.

        :return Arrow-compatible
        """
        return self._until

    @until.setter
    def until(self, value):
        if not value:
            return

        if not isinstance(value, Arrow):
            raise ValueError("Until should be an instance of Arrow.")

        self._until = value

    @property
    def count(self):
        """Get/set count.

        :return: int
        """
        return self._count

    @count.setter
    def count(self, value):
        if not value:
            return

        self._count = int(value)

    @property
    def interval(self):
        """Get/set interval.

        :return: int
        """
        return self._interval

    @interval.setter
    def interval(self, value):
        if not value:
            return

        self._interval = int(value)

    @property
    def byday(self):
        """Get/set byday list.

        :return: list
        """
        return self._byday

    @byday.setter
    def byday(self, values):
        if not values:
            return

        if type(values) is str:
            values = values.split(',')

        values = list(values)
        new_values = []

        for v in values:
            digit = [c for c in v if c in ['+', '-'] or c.isdigit()]

            digit = ''.join(digit)
            digit = 0 if len(digit) == 0 else int(digit)

            value = v.replace(str(digit), '')

            if value not in self._WEEKDAY_POSSIBLES or digit not in range(1, 54):
                raise ValueError("{} is not a possible value for byday.".format(v))

            day = eval('relativedelta.{}({})'.format(value, digit))
            new_values.append(day)

        self._byday = new_values

    @property
    def bymonthday(self):
        """Get/set bymonthday list.

        :return: list
        """
        return self._bymonthday

    @bymonthday.setter
    def bymonthday(self, values):
        if not values:
            return

        if type(values) is str:
            values = values.split(',')

        values = [int(v) for v in list(values)]

        for v in values:
            if abs(v) not in range(1, 31):
                raise ValueError("{} is out of range +/- 1-31.".format(v))

        self._bymonthday = values

    @property
    def byyearday(self):
        """Get/set byyearday list.

        :return: list
        """
        return self._bymonthday

    @byyearday.setter
    def byyearday(self, values):
        if not values:
            return

        if type(values) is str:
            values = values.split(',')

        values = [int(v) for v in list(values)]

        for v in values:
            if abs(v) not in range(1, 367):
                raise ValueError("{} is out of range +/- 1-366.".format(v))

        self._byyearday = values

    @property
    def byweekno(self):
        """Get/set byweekno list.

        :return: list
        """
        return self._byweekno

    @byweekno.setter
    def byweekno(self, values):
        if not values:
            return

        if type(values) is str:
            values = values.split(',')

        values = [int(v) for v in list(values)]

        for v in values:
            if abs(v) not in range(1, 54):
                raise ValueError("{} is out of range +/- 1-53.".format(v))

        self._byweekno = values

    @property
    def bymonth(self):
        """Get/set bymonth list.

        :return: list
        """
        return self._bymonth

    @bymonth.setter
    def bymonth(self, values):
        if not values:
            return

        if type(values) is str:
            values = values.split(',')

        values = [int(v) for v in list(values)]

        for v in values:
            if v not in range(1, 13):
                raise ValueError("{} is out of range 1-12.".format(v))

        self._bymonth = values

    @property
    def delta_index(self):
        """According to frequency, determines the timedelta parameter.

        :return: str
        """
        return self._FREQ_POSSIBLES[self.freq]

    @classmethod
    def from_line(cls, line):
        """Parse RRULE values.

        :param line: RRULE values
        :return: Repeatable
        """
        repeatable = cls()
        contents = line.split(';')

        for content in contents:
            properties = content.split('=')
            name = properties[0].lower()
            value = properties[1]

            try:
                exec('repeatable.{} = {}'.format(name, value))
            except AttributeError:
                continue

        return repeatable

    def __str__(self):
        res = []

        if self.freq:
            res.append("FREQ={}".format(self.freq))

        if self.until:
            res.append("UNTIL={}".format(arrow_to_iso(self.until)))

        if self.count:
            res.append("COUNT={}".format(self.count))

        if self.interval:
            res.append("INTERVAL={}".format(self.interval))

        if self.bysecond:
            values = str(self.bysecond).replace('[', '').replace(']', '').replace(' ', '')
            res.append("BYSECOND={}".format(values))

        if self.byminute:
            values = ','.join(self.byminute)
            res.append("BYMINUTE={}".format(values))

        if self.byhour:
            values = str(self.byhour).replace('[', '').replace(']', '').replace(' ', '')
            res.append("BYHOUR={}".format(values))

        if self.byday:
            values = []
            for day in self.byday:
                value = str(day).split('(')[0]
                digit = '' if day.n == 0 else str(day.n)
                values.append(digit + value)

            values = ','.join(values)
            res.append("BYDAY={}".format(values))

        if self.bymonthday:
            values = str(self.bymonthday).replace('[', '').replace(']', '').replace(' ', '')
            res.append("BYMONTHDAY={}".format(values))

        if self.byyearday:
            values = str(self.byyearday).replace('[', '').replace(']', '').replace(' ', '')
            res.append("BYYEARDAY={}".format(values))

        if self.byweekno:
            values = str(self.byweekno).replace('[', '').replace(']', '').replace(' ', '')
            res.append("BYWEEKNO={}".format(values))

        if self.bymonth:
            values = str(self.bymonth).replace('[', '').replace(']', '').replace(' ', '')
            res.append("BYMONTH={}".format(values))

        return ';'.join(res)
