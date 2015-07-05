import unittest
from ics.parse import unfold_lines
from .fixture import (
    cal1,
    calendar_without_prodid,
    empty_calendar,
    cal6,
    empty_calendar_with_blank_line1,
    empty_calendar_with_blank_line2,
    empty_calendar_with_blank_line3,
    unfolded_cal1,
    unfolded_calendar_without_prodid,
    unfolded_cal6,
)


class TestUnfoldLines(unittest.TestCase):

    def test_no_folded_lines(self):
        self.assertEqual(list(unfold_lines(calendar_without_prodid.split('\n'))),
                         unfolded_calendar_without_prodid)

    def test_simple_folded_lines(self):
        self.assertEqual(list(unfold_lines(cal1.split('\n'))), unfolded_cal1)

    def test_last_line_folded(self):
        self.assertEqual(list(unfold_lines(cal6.split('\n'))), unfolded_cal6)

    def test_simple(self):
        dataset = {
            'a': ('a',),
            'ab': ('ab',),
            'a\nb': ('a', 'b',),
            'a\n b': ('ab',),
            'a \n b': ('a b',),
            'a\n b\nc': ('ab', 'c',),
            'a\nb\n c': ('a', 'bc',),
            'a\nb\nc': ('a', 'b', 'c',),
            'a\n b\n c': ('abc',),
            'a \n b \n c': ('a b c',),
        }
        for line in dataset:
            expected = dataset[line]
            got = tuple(unfold_lines(line.split('\n')))
            self.assertEqual(expected, got)

    def test_empty(self):
        self.assertEqual(list(unfold_lines([])), [])

    def test_one_line(self):
        self.assertEqual(list(unfold_lines(cal6.split('\n'))), unfolded_cal6)

    def test_two_lines(self):
        self.assertEqual(list(unfold_lines(empty_calendar.split('\n'))),
                         ['BEGIN:VCALENDAR', 'END:VCALENDAR'])

    def test_no_empty_lines(self):
        self.assertEqual(list(unfold_lines(empty_calendar_with_blank_line1.split('\n'))),
                         ['BEGIN:VCALENDAR', 'END:VCALENDAR'])

    def test_no_whitespace_lines(self):
        self.assertEqual(list(unfold_lines(empty_calendar_with_blank_line2.split('\n'))),
                         ['BEGIN:VCALENDAR', 'END:VCALENDAR'])

    def test_first_line_empty(self):
        self.assertEqual(list(unfold_lines(empty_calendar_with_blank_line3.split('\n'))),
                         ['BEGIN:VCALENDAR', 'END:VCALENDAR'])
