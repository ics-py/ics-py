import unittest

from ics.icalendar import Calendar
from ics.grammar.parse import (Container, ContentLine, ParseError, lines_to_container,
                               string_to_container)

from .fixture import cal1, cal5, cal11


class TestParse(unittest.TestCase):

    def test_parse(self):
        content = string_to_container(cal5)
        self.assertEqual(1, len(content))

        cal = content.pop()
        self.assertEqual('VCALENDAR', cal.name)
        self.assertTrue(isinstance(cal, Container))
        self.assertEqual('VERSION', cal[0].name)
        self.assertEqual('2.0', cal[0].value)
        self.assertEqual(cal5.strip().splitlines(), str(cal).strip().splitlines())

    def test_one_line(self):
        ics = 'DTSTART;TZID=Europe/Brussels:20131029T103000'
        reader = lines_to_container([ics])
        self.assertEqual(next(iter(reader)), ContentLine(
            'DTSTART',
            {'TZID': ['Europe/Brussels']},
            '20131029T103000'
        ))

    def test_many_lines(self):
        i = 0
        for line in string_to_container(cal1)[0]:
            self.assertNotEqual('', line.name)
            if isinstance(line, ContentLine):
                self.assertNotEqual('', line.value)
            if line.name == 'DESCRIPTION':
                self.assertEqual('Lorem ipsum dolor sit amet, \
                    consectetur adipiscing elit. \
                    Sed vitae facilisis enim. \
                    Morbi blandit et lectus venenatis tristique. \
                    Donec sit amet egestas lacus. \
                    Donec ullamcorper, mi vitae congue dictum, \
                    quam dolor luctus augue, id cursus purus justo vel lorem. \
                    Ut feugiat enim ipsum, quis porta nibh ultricies congue. \
                    Pellentesque nisl mi, molestie id sem vel, \
                    vehicula nullam.', line.value)
            i += 1

    def test_end_different(self):

        with self.assertRaises(ParseError):
            Calendar(cal11)


class TestContainer(unittest.TestCase):

    def test_repr(self):

        e = ContentLine(name="VTEST", value="cocu !")
        c = Container("test", e)

        self.assertEqual("<Container 'test' with 1 element>", repr(c))


class TestLine(unittest.TestCase):

    def test_repr(self):

        c = ContentLine(name="VTEST", value="cocu !")
        self.assertEqual("<ContentLine 'VTEST' with 0 parameter. Value='cocu !'>", repr(c))

    def test_get_item(self):
        l = ContentLine(name="VTEST", value="cocu !", params={"plop": "plip"})
        self.assertEqual(l['plop'], "plip")
