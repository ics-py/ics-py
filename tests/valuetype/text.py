import attr
import pytest
from hypothesis import given

from ics.grammar import ContentLine, string_to_container
from ics.valuetype.text import TextConverter
# Text may be comma-separated multi-value but is never quoted, with the characters [\\;,\n] escaped
from tests.grammar import VALUE

TextConv: TextConverter = TextConverter.INST


@pytest.mark.parametrize("inp_esc, out_uesc", [
    (
            "SUMMARY:Project XYZ Final Review\\nConference Room - 3B\\nCome Prepared.",
            ContentLine("SUMMARY", value="Project XYZ Final Review\nConference Room - 3B\nCome Prepared.")
    ),
    (
            "DESCRIPTION;ALTREP=\"cid:part1.0001@example.org\":The Fall'98 Wild Wizards Conference - - Las Vegas\\, NV\\, USA",
            ContentLine("DESCRIPTION", {"ALTREP": ["cid:part1.0001@example.org"]}, value="The Fall'98 Wild Wizards Conference - - Las Vegas, NV, USA")
    ),
    (
            "TEST:abc\\r\\n\\,\\;:\"\t=xyz",
            ContentLine("TEST", value="abc\r\n,;:\"\t=xyz")
    ),
])
def test_example_text_recode(inp_esc, out_uesc):
    par_esc = ContentLine.parse(inp_esc)
    par_uesc = attr.evolve(par_esc, value=TextConv.parse(par_esc.value))
    out_esc = attr.evolve(out_uesc, value=TextConv.serialize(out_uesc.value))
    assert par_uesc == out_uesc
    ser_esc = out_esc.serialize()
    assert inp_esc == ser_esc
    assert string_to_container(inp_esc) == [par_esc]


# TODO list examples ("RESOURCES:EASEL,PROJECTOR,VCR", ContentLine("RESOURCES", value="EASEL,PROJECTOR,VCR"))

def test_trailing_escape_text():
    with pytest.raises(ValueError) as excinfo:
        TextConv.parse("text\\,with\tdangling escape\\")
    assert "not end with an escape sequence" in str(excinfo.value)

    assert TextConv.parse("text\\,with\tdangling escape") == "text,with\tdangling escape"
    assert TextConv.serialize("text,text\\,with\tdangling escape\\") == "text\\,text\\\\\\,with\tdangling escape\\\\"


def test_broken_escape():
    with pytest.raises(ValueError) as e:
        TextConv.unescape_text("\\t")
    assert e.match("can't handle escaped character")
    with pytest.raises(ValueError) as e:
        TextConv.unescape_text("abc;def")
    assert e.match("unescaped character")

def test_trailing_escape_value_list():
    cl1 = ContentLine.parse("TEST:this is,a list \\, with a\\\\,trailing escape\\")
    with pytest.raises(ValueError) as excinfo:
        list(TextConv.split_value_list(cl1.value))
    assert "not end with an escape sequence" in str(excinfo.value)

    cl2 = ContentLine.parse("TEST:this is,a list \\, with a\\\\,trailing escape")
    assert list(TextConv.split_value_list(cl2.value)) == \
           ["this is", "a list \\, with a\\\\", "trailing escape"]
    assert [TextConv.parse(v) for v in TextConv.split_value_list(cl2.value)] == \
           ["this is", "a list , with a\\", "trailing escape"]


@given(value=VALUE)
def test_any_text_value_recode(value):
    esc = TextConv.serialize(value)
    assert TextConv.parse(esc) == value
    cl = ContentLine("TEST", value=esc)
    assert ContentLine.parse(cl.serialize()) == cl
    assert string_to_container(cl.serialize()) == [cl]
    vals = [esc, esc, "test", esc]
    cl2 = ContentLine("TEST", value=TextConv.join_value_list(vals))
    assert list(TextConv.split_value_list(cl2.value)) == vals
    assert ContentLine.parse(cl.serialize()) == cl
    assert string_to_container(cl.serialize()) == [cl]
