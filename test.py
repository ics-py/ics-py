import unittest
from parser import ParseError, ContentLine, Container, ICSReader
from fixture import cal1, cal2, cal3, cal4, cal5
from urllib import urlopen


class TestContentLine(unittest.TestCase):
    dataset = {
        'haha:': ContentLine('haha'),
        ':hoho': ContentLine('',  {}, 'hoho'),
        'haha:hoho': ContentLine('haha', {}, 'hoho'),
        'haha:hoho:hihi': ContentLine('haha', {}, 'hoho:hihi'),
        'haha;hoho=1:hoho': ContentLine('haha', {'hoho': ['1']}, 'hoho'),
        'haha;p2=v2;p1=v1:': ContentLine('haha', {'p1': ['v1'], 'p2': ['v2']}, ''),
        'haha;hihi=p3,p4,p5;hoho=p1,p2:blabla:blublu': ContentLine('haha', {'hoho': ['p1', 'p2'], 'hihi': ['p3', 'p4', 'p5']}, 'blabla:blublu'),
        'RRULE:FREQ=YEARLY;BYMONTH=3;BYDAY=-1SU': ContentLine('RRULE', {}, 'FREQ=YEARLY;BYMONTH=3;BYDAY=-1SU'),
        'SUMMARY:dfqsdfjqkshflqsjdfhqs fqsfhlqs dfkqsldfkqsdfqsfqsfqsfs': ContentLine('SUMMARY', {}, 'dfqsdfjqkshflqsjdfhqs fqsfhlqs dfkqsldfkqsdfqsfqsfqsfs'),
        'DTSTART;TZID=Europe/Brussels:20131029T103000': ContentLine('DTSTART', {'TZID': ['Europe/Brussels']}, '20131029T103000'),
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

    def test_parse(self):
        content = ICSReader(cal5.split('\n')).parse()
        self.assertEqual(1, len(content))
        
        cal = content.pop()
        self.assertEqual('VCALENDAR', cal.name)
        self.assertTrue(isinstance(cal, Container))
        self.assertEqual('VERSION', cal[0].name)
        self.assertEqual('2.0', cal[0].value)
        self.assertEqual(cal5.strip(), str(cal).strip())

    def test_one_line(self):
        ics = 'DTSTART;TZID=Europe/Brussels:20131029T103000'
        reader = ICSReader([ics])
        self.assertEqual(iter(reader).next(), TestContentLine.dataset[ics])
    
    def test_gehol(self):
        url = "http://scientia-web.ulb.ac.be/gehol/index.php?Student/Calendar/%23SPLUS35F0F0/1-14.ics"
        ics = ICSReader(urlopen(url)).parse()
        self.assertTrue(ics)
        
    
    def test_many_lines(self):
        i = 0
        for line in ICSReader(cal1.split('\n')):
            self.assertNotEqual('', line.name)
            self.assertNotEqual('', line.value)
            if line.name == 'DESCRIPTION':
                self.assertEqual('Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed vitae facilisis enim. Morbi blandit et lectus venenatis tristique. Donec sit amet egestas lacus. Donec ullamcorper, mi vitae congue dictum, quam dolor luctus augue, id cursus purus justo vel lorem. Ut feugiat enim ipsum, quis porta nibh ultricies congue. Pellentesque nisl mi, molestie id sem vel, vehicula nullam.', line.value)
            i += 1
    
    def test_multiline_string(self):
        i = 0
        for line in ICSReader(cal1):
            self.assertNotEqual('', line.name)
            self.assertNotEqual('', line.value)
            if line.name == 'DESCRIPTION':
                self.assertEqual('Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed vitae facilisis enim. Morbi blandit et lectus venenatis tristique. Donec sit amet egestas lacus. Donec ullamcorper, mi vitae congue dictum, quam dolor luctus augue, id cursus purus justo vel lorem. Ut feugiat enim ipsum, quis porta nibh ultricies congue. Pellentesque nisl mi, molestie id sem vel, vehicula nullam.', line.value)
            i += 1


if __name__ == '__main__':
    unittest.main()
