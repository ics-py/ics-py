import unittest
from ics.parse import ParseError, ContentLine


class TestContentLine(unittest.TestCase):

    dataset = {
        'haha:': ContentLine('haha'),
        ':hoho': ContentLine('', {}, 'hoho'),
        'haha:hoho': ContentLine('haha', {}, 'hoho'),
        'haha:hoho:hihi': ContentLine('haha', {}, 'hoho:hihi'),
        'haha;hoho=1:hoho': ContentLine('haha', {'hoho': ['1']}, 'hoho'),
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
    }

    def test_errors(self):
        self.assertRaises(ParseError, ContentLine.parse, 'haha;p1=v1')
        self.assertRaises(ParseError, ContentLine.parse, 'haha;p1:')

    def test_str(self):
        for test in self.dataset:
            expected = test
            got = str(self.dataset[test])
            self.assertEqual(expected, got, "To string")

    def test_parse(self):
        self.dataset2.update(self.dataset)
        for test in self.dataset2:
            expected = self.dataset2[test]
            got = ContentLine.parse(test)
            self.assertEqual(expected, got, "Parse")
