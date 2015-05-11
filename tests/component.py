import unittest
from ics.icalendar import Calendar
from ics.component import Component
from ics.parse import Container, ContentLine
from .fixture import cal2
import copy

fix1 = "BEGIN:BASETEST\r\nATTR:FOOBAR\r\nEND:BASETEST"

fix2 = "BEGIN:BASETEST\r\nATTR:FOO\r\nATTR2:BAR\r\nEND:BASETEST"


class TestComponent(unittest.TestCase):

    def test_valueerror(self):

        with self.assertRaises(ValueError):
            Calendar(cal2)

    def test_abstract(self):
        with self.assertRaises(NotImplementedError):
            Component._from_container(Container(name='VCALENDAR'))

    def test_bad_type(self):
        container = Container(name='VINVALID')
        with self.assertRaises(ValueError):
            Calendar._from_container(container)

    def test_no_urepr(self):
        class Dummy(Component):
            pass
        d = Dummy()
        adress = hex(id(d))
        self.assertEqual('<Dummy at {}>'.format(adress), repr(d))

    def test_extractor(self):
        c = CT1()
        c.some_attr = "foobar"
        expected = fix1
        self.assertEqual(str(c), expected)

    def test_2extractors(self):
        c = CT2()
        c.some_attr = "foo"
        c.some_attr2 = "bar"
        expected = fix2
        self.assertEqual(str(c), expected)

    def test_empty_input(self):
        cont = Container("TEST")
        c = CT1._from_container(cont)
        self.assertEqual(c._unused.name, "TEST")
        self.assertEqual(c.some_attr, "biiip")

    def test_no_match_input(self):
        cont = Container("TEST")
        cont.append(ContentLine(name="NOMATCH", value="anything"))
        cont2 = copy.deepcopy(cont)

        c = CT1._from_container(cont)
        self.assertEqual(c._unused.name, "TEST")
        self.assertEqual(c.some_attr, "biiip")
        self.assertEqual(cont2, c._unused)

    def test_input(self):
        cont = Container("TEST")
        cont.append(ContentLine(name="ATTR", value="anything"))

        c = CT1._from_container(cont)
        self.assertEqual(c._unused.name, "TEST")
        self.assertEqual(c.some_attr, "anything")
        self.assertEqual(Container("TEST"), c._unused)

    def test_input_plus_unused(self):
        cont = Container("TEST")
        cont.append(ContentLine(name="ATTR", value="anything"))
        cont.append(ContentLine(name="PLOP", value="plip"))

        unused = Container("TEST")
        unused.append(ContentLine(name="PLOP", value="plip"))

        c = CT1._from_container(cont)
        self.assertEqual(c._unused.name, "TEST")
        self.assertEqual(c.some_attr, "anything")
        self.assertEqual(unused, c._unused)

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
        self.assertEqual(unused, c._unused)

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
        self.assertEqual(Container("TEST"), c._unused)

    def test_multiple_fail(self):
        cont = Container("TEST")

        c = CT3._from_container(cont)

        self.assertEqual(c.some_attr, "biiip")
        self.assertEqual(Container("TEST"), c._unused)

    def test_multiple_unique(self):
        cont = Container("TEST")
        cont.append(ContentLine(name="ATTR", value="anything"))

        c = CT3._from_container(cont)

        self.assertEqual(c.some_attr, "anything")
        self.assertEqual(Container("TEST"), c._unused)

    def test_multiple_unique_required(self):
        cont = Container("TEST")
        cont.append(ContentLine(name="OTHER", value="anything"))

        with self.assertRaises(ValueError):
            CT4._from_container(cont)


class ComponentBaseTest(Component):
    _TYPE = "TEST"

    def __init__(self):
        self.some_attr = "biiip"
        self.some_attr2 = "baaaaaaaaaaap"
        self._unused = Container('BASETEST')


class CT1(ComponentBaseTest):
    _OUTPUTS, _EXTRACTORS = [], []


class CT2(ComponentBaseTest):
    _OUTPUTS, _EXTRACTORS = [], []


class CT3(ComponentBaseTest):
    _OUTPUTS, _EXTRACTORS = [], []


class CT4(ComponentBaseTest):
    _OUTPUTS, _EXTRACTORS = [], []


@CT1._extracts('ATTR')
def attr1(test, line):
    if line:
        test.some_attr = line.value


@CT2._extracts('ATTR', required=True)
def attr2(test, line):
    test.some_attr = line.value


@CT3._extracts('ATTR', multiple=True)
def attr3(test, line_list):
    if line_list:
        test.some_attr = ", ".join(map(lambda x: x.value, line_list))


@CT4._extracts('ATTR', required=True, multiple=True)
def attr4(test, line_list):
    test.some_attr = ", ".join(map(lambda x: x.value, line_list))


@CT1._outputs
def o_some_attr(test, container):
    if test.some_attr:
        container.append(ContentLine('ATTR', value=test.some_attr.upper()))


@CT2._outputs
def o_some_attr2(test, container):
    if test.some_attr:
        container.append(ContentLine('ATTR', value=test.some_attr.upper()))


@CT2._outputs
def o_some_attr2bis(test, container):
    if test.some_attr2:
        container.append(ContentLine('ATTR2', value=test.some_attr2.upper()))
