import unittest

from ics.grammar.parse import ContentLine, ParseError
from ics.utils import iso_to_arrow


class TestContentLine(unittest.TestCase):

    dataset = {
        'HAHA:': ContentLine('haha'),
        'HAHA:hoho': ContentLine('haha', {}, 'hoho'),
        'HAHA:hoho:hihi': ContentLine('haha', {}, 'hoho:hihi'),
        'HAHA;hoho=1:hoho': ContentLine('haha', {'hoho': ['1']}, 'hoho'),
        'RRULE:FREQ=YEARLY;BYMONTH=3;BYDAY=-1SU':
        ContentLine(
            'RRULE',
            {},
            'FREQ=YEARLY;BYMONTH=3;BYDAY=-1SU'
        ),
        'SUMMARY:dfqsdfjqkshflqsjdfhqs fqsfhlqs dfkqsldfkqsdfqsfqsfqsfs':
        ContentLine(
            'SUMMARY',
            {},
            'dfqsdfjqkshflqsjdfhqs fqsfhlqs dfkqsldfkqsdfqsfqsfqsfs'
        ),
        'DTSTART;TZID=Europe/Brussels:20131029T103000':
        ContentLine(
            'DTSTART',
            {'TZID': ['Europe/Brussels']},
            '20131029T103000'
        ),
    }

    dataset2 = {
        'haha;p2=v2;p1=v1:':
        ContentLine(
            'haha',
            {'p1': ['v1'], 'p2': ['v2']},
            ''
        ),
        'haha;hihi=p3,p4,p5;hoho=p1,p2:blabla:blublu':
        ContentLine(
            'haha',
            {'hoho': ['p1', 'p2'], 'hihi': ['p3', 'p4', 'p5']},
            'blabla:blublu'
        ),
        r'ATTENDEE;X-A="I&rsquo\;ll be in NYC":mailto:a@a.com':
        ContentLine(
            'ATTENDEE',
            {'X-A': [r"I&rsquo\;ll be in NYC"]},
            'mailto:a@a.com',
        ),
        'DTEND;TZID="UTC":20190107T000000':
        ContentLine(
            "DTEND",
            {'TZID': ['UTC']},
            "20190107T000000"
        )
    }

    def test_errors(self):
        self.assertRaises(ParseError, ContentLine.parse, 'haha;p1=v1')
        self.assertRaises(ParseError, ContentLine.parse, 'haha;p1:')

    def test_str(self):
        for test in self.dataset:
            expected = test
            got = str(self.dataset[test])
            self.assertEqual(expected, got)

    def test_parse(self):
        self.dataset2.update(self.dataset)
        for test in self.dataset2:
            expected = self.dataset2[test]
            got = ContentLine.parse(test)
            self.assertEqual(expected, got)


    # https://github.com/C4ptainCrunch/ics.py/issues/68
    def test_timezone_not_dropped(self):
        line = ContentLine.parse("DTSTART;TZID=Europe/Berlin:20151104T190000")
        arrow = iso_to_arrow(line)
        self.assertIn("Europe/Berlin", str(arrow.tzinfo))
