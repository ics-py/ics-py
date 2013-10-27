import unittest
from parser import ParseError, ContentLine, ICSReader
from fixture import cal1, cal2, cal3, cal4

class TestContentLine(unittest.TestCase):
	dataset = {
		'haha:': ContentLine('haha'),
		':hoho': ContentLine('',  {}, 'hoho'),
		'haha:hoho': ContentLine('haha', {}, 'hoho'),
		'haha:hoho:hihi': ContentLine('haha', {}, 'hoho:hihi'),
		'haha;hoho=1:hoho': ContentLine('haha', {'hoho': ['1']}, 'hoho'),
		'haha;p2=v2;p1=v1:': ContentLine('haha', {'p1':['v1'], 'p2':['v2']}, ''),
		'haha;hihi=p3,p4,p5;hoho=p1,p2:blabla:blublu':ContentLine('haha', {'hoho':['p1','p2'], 'hihi':['p3','p4','p5']}, 'blabla:blublu'),
		'RRULE:FREQ=YEARLY;BYMONTH=3;BYDAY=-1SU': ContentLine('RRULE', {}, 'FREQ=YEARLY;BYMONTH=3;BYDAY=-1SU'),
		'SUMMARY:dfqsdfjqkshflqsjdfhqs fqsfhlqs dfkqsldfkqsdfqsfqsfqsfs': ContentLine('SUMMARY', {}, 'dfqsdfjqkshflqsjdfhqs fqsfhlqs dfkqsldfkqsdfqsfqsfqsfs'),
		'DTSTART;TZID=Europe/Brussels:20131029T103000': ContentLine('DTSTART', {'TZID':['Europe/Brussels']}, '20131029T103000'),
	}
	
	def test_errors(self):
		self.assertRaises(ParseError, ContentLine.parse, 'haha;p1=v1')
		self.assertRaises(ParseError, ContentLine.parse, 'haha;p1:')
	
	def test_parse(self):
		for test in self.dataset:
			expected = self.dataset[test]
			got = ContentLine.parse(test)
			self.assertEqual(expected, got, "Parse")
	
	def test_str(self):
		for test in self.dataset:
			expected = test
			got = str(self.dataset[test])
			self.assertEqual(expected, got, "To string")

class TestICSReader(unittest.TestCase):
	def test_one_line(self):
		ics = 'DTSTART;TZID=Europe/Brussels:20131029T103000'
		reader = ICSReader([ics])
		self.assertEqual(iter(reader).next(), TestContentLine.dataset[ics])

if __name__ == '__main__':
	unittest.main()