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
                 byday=[],
                 bymonthday=[],
                 bymonth=[]):
        """Instantiate a new Repeatable rule.

        :param freq: str
        :param until: Arrow-compatible
        :param count: int
        :param interval: int
        :param byday: list
        :param bymonthday: list
        :param bymonth: list
        """
        self._freq = None
        self._until = None
        self._count = None
        self._interval = None
        self._byday = None
        self._bymonthday = None
        self._bymonth = None

        self.freq = freq
        self.until = until
        self.count = count
        self.interval = interval
        self.byday = byday
        self.bymonthday = bymonthday
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
        if type(values) not in [str, list]:
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

            if value not in self._WEEKDAY_POSSIBLES or abs(digit) not in range(0, 54):
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
        if type(values) not in [str, list]:
            return

        if type(values) is str:
            values = values.split(',')

        values = [int(v) for v in list(values)]

        for v in values:
            if abs(v) not in range(1, 31):
                raise ValueError("{} is out of range +/- 1-31.".format(v))

        self._bymonthday = values

    @property
    def bymonth(self):
        """Get/set bymonth list.

        :return: list
        """
        return self._bymonth

    @bymonth.setter
    def bymonth(self, values):
        if type(values) not in [str, list]:
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
        contents = line.value.split(';')

        for content in contents:
            properties = content.split('=')
            name = properties[0].lower()
            value = properties[1]

            try:
                exec('repeatable.{} = "{}"'.format(name, value))
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

        if self.byday:
            values = []
            for day in self.byday:
                value = str(day).split('(')[0]
                digit = '' if day.n == 0 else str(day.n)
                values.append(digit + value)

            values = ','.join(values)
            res.append("BYDAY={}".format(values))

        if self.bymonthday:
            values = str(self.bymonthday).replace('[', '')\
                .replace(']', '').replace(' ', '')
            res.append("BYMONTHDAY={}".format(values))

        if self.bymonth:
            values = str(self.bymonth).replace('[', '')\
                .replace(']', '').replace(' ', '')
            res.append("BYMONTH={}".format(values))

        return ';'.join(res)
