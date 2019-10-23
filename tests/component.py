import copy
import unittest

from ics.component import Component
from ics.icalendar import Calendar
from ics.grammar.parse import Container, ContentLine
from ics.parsers.parser import Parser, option
from ics.serializers.serializer import Serializer

from .fixture import cal2

fix1 = "BEGIN:BASETEST\r\nATTR:FOOBAR\r\nEND:BASETEST"

fix2 = "BEGIN:BASETEST\r\nATTR:FOO\r\nATTR2:BAR\r\nEND:BASETEST"


class TestComponent(unittest.TestCase):

    def test_valueerror(self):

        with self.assertRaises(ValueError):
            Calendar(cal2)

    def test_bad_type(self):
        container = Container(name='VINVALID')
        with self.assertRaises(ValueError):
            Calendar._from_container(container)

    def test_base(self):
        assert CT4.Meta.name == "TEST"
        e = CT4.Meta.parser.get_parsers()
        assert len(e) == 1

    def test_parser(self):
        c = CT1()
        c.some_attr = "foobar"
        expected = fix1
        self.assertEqual(str(c), expected)

    def test_2parsers(self):
        c = CT2()
        c.some_attr = "foo"
        c.some_attr2 = "bar"
        expected = fix2
        self.assertEqual(str(c), expected)

    def test_empty_input(self):
        cont = Container("TEST")
        c = CT1._from_container(cont)
        self.assertEqual(c.extra.name, "TEST")
        self.assertEqual(c.some_attr, "biiip")

    def test_no_match_input(self):
        cont = Container("TEST")
        cont.append(ContentLine(name="NOMATCH", value="anything"))
        cont2 = copy.deepcopy(cont)

        c = CT1._from_container(cont)
        self.assertEqual(c.extra.name, "TEST")
        self.assertEqual(c.some_attr, "biiip")
        self.assertEqual(cont2, c.extra)

    def test_input(self):
        cont = Container("TEST")
        cont.append(ContentLine(name="ATTR", value="anything"))

        c = CT1._from_container(cont)
        self.assertEqual(c.extra.name, "TEST")
        self.assertEqual(c.some_attr, "anything")
        self.assertEqual(Container("TEST"), c.extra)

    def test_input_plus_extra(self):
        cont = Container("TEST")
        cont.append(ContentLine(name="ATTR", value="anything"))
        cont.append(ContentLine(name="PLOP", value="plip"))

        unused = Container("TEST")
        unused.append(ContentLine(name="PLOP", value="plip"))

        c = CT1._from_container(cont)
        self.assertEqual(c.extra.name, "TEST")
        self.assertEqual(c.some_attr, "anything")
        self.assertEqual(unused, c.extra)

    def test_required_raises(self):
        cont = Container("TEST")
        cont.append(ContentLine(name="PLOP", value="plip"))

        with self.assertRaises(ValueError):
            CT2._from_container(cont)

    def test_required(self):
        cont = Container("TEST")
        cont.append(ContentLine(name="ATTR", value="anything"))
        cont.append(ContentLine(name="PLOP", value="plip"))

        unused = Container("TEST")
        unused.append(ContentLine(name="PLOP", value="plip"))

        c = CT2._from_container(cont)
        self.assertEqual(c.some_attr, "anything")
        self.assertEqual(unused, c.extra)

    def test_multiple_non_allowed(self):
        cont = Container("TEST")
        cont.append(ContentLine(name="ATTR", value="anything"))
        cont.append(ContentLine(name="ATTR", value="plip"))

        with self.assertRaises(ValueError):
            CT1._from_container(cont)

    def test_multiple(self):
        cont = Container("TEST")
        cont.append(ContentLine(name="ATTR", value="anything"))
        cont.append(ContentLine(name="ATTR", value="plip"))

        c = CT3._from_container(cont)

        self.assertEqual(c.some_attr, "plip, anything")
        self.assertEqual(Container("TEST"), c.extra)

    def test_multiple_fail(self):
        cont = Container("TEST")

        c = CT3._from_container(cont)

        self.assertEqual(c.some_attr, "biiip")
        self.assertEqual(Container("TEST"), c.extra)

    def test_multiple_unique(self):
        cont = Container("TEST")
        cont.append(ContentLine(name="ATTR", value="anything"))

        c = CT3._from_container(cont)

        self.assertEqual(c.some_attr, "anything")
        self.assertEqual(Container("TEST"), c.extra)

    def test_multiple_unique_required(self):
        cont = Container("TEST")
        cont.append(ContentLine(name="OTHER", value="anything"))

        with self.assertRaises(ValueError):
            CT4._from_container(cont)


class ComponentBaseTest(Component):
    class Meta:
        name = "TEST"

    def __init__(self):
        self.some_attr = "biiip"
        self.some_attr2 = "baaaaaaaaaaap"
        self.extra = Container('BASETEST')


# 1
class CT1Parser(Parser):
    def parse_attr(test, line):
        if line:
            test.some_attr = line.value


class CT1Serializer(Serializer):
    def serialize_some_attr(test, container):
        if test.some_attr:
            container.append(ContentLine('ATTR', value=test.some_attr.upper()))


class CT1(ComponentBaseTest):
    class Meta:
        name = "TEST"
        parser = CT1Parser
        serializer = CT1Serializer


# 2
class CT2Parser(Parser):
    @option(required=True)
    def parse_attr(test, line):
        test.some_attr = line.value


class CT2Serializer(Serializer):
    def serialize_some_attr2(test, container):
        if test.some_attr:
            container.append(ContentLine('ATTR', value=test.some_attr.upper()))

    def serialize_some_attr2bis(test, container):
        if test.some_attr2:
            container.append(ContentLine('ATTR2', value=test.some_attr2.upper()))


class CT2(ComponentBaseTest):
    class Meta:
        name = "TEST"
        parser = CT2Parser
        serializer = CT2Serializer


# 3
class CT3Parser(Parser):
    @option(multiple=True)
    def parse_attr(test, line_list):
        if line_list:
            test.some_attr = ", ".join(map(lambda x: x.value, line_list))


class CT3Serializer(Serializer):
    pass


class CT3(ComponentBaseTest):
    class Meta:
        name = "TEST"
        parser = CT3Parser
        serializer = CT3Serializer


# 4
class CT4Parser(Parser):
    @option(required=True, multiple=True)
    def parse_attr(test, line_list):
        test.some_attr = ", ".join(map(lambda x: x.value, line_list))


class CT4Serializer(Serializer):
    pass


class CT4(ComponentBaseTest):
    class Meta:
        name = "TEST"
        parser = CT4Parser
        serializer = CT4Serializer
