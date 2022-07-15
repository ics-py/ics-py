import re
import sys
from datetime import timedelta

import lipsum
import pytest
from hypothesis import assume, example, given, settings
from hypothesis.core import Example
from hypothesis.strategies import characters, text

from ics.contentline import *
from ics.contentline.container import DEFAULT_LINE_WRAP, Patterns, escape_param
from ics.contentline.parser import ContentLineParser
from tests.contentline.examples import CONTENTLINE_EXAMPLES

CONTROL = [chr(i) for i in range(ord(" ")) if i != ord("\t")] + [chr(0x7F)]
NAME = text(
    alphabet=(
        characters(
            whitelist_categories=["Lu"], whitelist_characters=["-"], max_codepoint=128
        )
    ),
    min_size=1,
)
VALUE = text(characters(blacklist_categories=["Cs"], blacklist_characters=CONTROL))
VALUE_NONEMPTY = text(
    characters(blacklist_categories=["Cs"], blacklist_characters=CONTROL), min_size=1
)
ContentLineParser.always_check = True


@pytest.fixture(params=[5, 10, 13, 70, 74, 75, 76, 80, 100, sys.maxsize])
def contentline_any_wrap(request):
    oldwidth = DEFAULT_LINE_WRAP.width
    DEFAULT_LINE_WRAP.width = request.param
    try:
        yield
    finally:
        DEFAULT_LINE_WRAP.width = oldwidth


def parse_contentline(line: str) -> ContentLine:
    (cl,) = Parser.lines_to_contentlines(
        Parser.unfold_lines(Parser.string_to_lines(line))
    )
    return cl


def unfold_str(lines: str) -> str:
    return "".join(
        line for nr, line in Parser.unfold_lines(Parser.string_to_lines(lines))
    )


@pytest.mark.parametrize("inp, out", CONTENTLINE_EXAMPLES)
def test_example_recode(inp, out):
    par = parse_contentline(inp)
    assert par == out

    ser = out.serialize(wrap=None)
    if inp[0].isupper():
        assert inp == ser
    else:
        assert inp.upper() == ser.upper()

    par_ser = par.serialize(wrap=None)
    if inp[0].isupper():
        assert inp == par_ser
    else:
        assert inp.upper() == par_ser.upper()

    ser_par = parse_contentline(ser)
    assert ser_par == out


@pytest.mark.parametrize("inp, out", CONTENTLINE_EXAMPLES)
@pytest.mark.usefixtures("contentline_any_wrap")
def test_example_linewrap(inp, out):
    ser = out.serialize()
    if inp[0].isupper():
        assert inp == unfold_str(ser)
    else:
        assert inp.upper() == unfold_str(ser).upper()

    for line in Parser.string_to_lines(ser):
        assert len(line) <= DEFAULT_LINE_WRAP.width

    ser_par = parse_contentline(ser)
    assert ser_par == out


def test_param_quoting():
    inp = 'TEST;P1="A";P2=B;P3=C,"D",E,"F":"VAL"'
    out = ContentLine(
        "TEST",
        {
            "P1": [QuotedParamValue("A")],
            "P2": ["B"],
            "P3": ["C", QuotedParamValue("D"), "E", QuotedParamValue("F")],
        },
        '"VAL"',
    )
    par = parse_contentline(inp)
    assert par == out
    ser = out.serialize(wrap=None)
    assert inp == ser
    par_ser = par.serialize(wrap=None)
    assert inp == par_ser
    assert parse_contentline(inp) == out

    for param in out.params.keys():
        for o_val, p_val in zip(out[param], par[param]):
            assert type(o_val) == type(p_val)


def test_trailing_escape_param():
    with pytest.raises(ParseError) as excinfo:
        (
            parse_contentline(
                "TEST;PARAM=this ^^ is a ^'param^',with a ^^trailing escape^:value"
            )
        )
    assert "not end with an escape sequence" in str(excinfo.value)
    with pytest.raises(ParseError) as excinfo:
        (
            parse_contentline(
                "TEST;PARAM=this ^^ is a ^'param^',with an ^invalid escape:value"
            )
        )
    assert "invalid escape sequence" in str(excinfo.value)
    assert (
        parse_contentline(
            "TEST;PARAM=this ^^ is a ^'param^',without a ^^trailing escape:value"
        )
    ) == ContentLine(
        "TEST",
        {"PARAM": ['this ^ is a "param"', "without a ^trailing escape"]},
        "value",
    )


def assert_parses_to(raw, cl):
    assert parse_contentline(raw).serialize(wrap=None) == raw
    assert unfold_str(parse_contentline(raw).serialize()) == raw
    assert parse_contentline(raw).serialize() == "\r\n".join(
        DEFAULT_LINE_WRAP.wrap(raw)
    )

    assert parse_contentline(cl.serialize(wrap=None)) == cl
    assert parse_contentline(cl.serialize()) == cl

    assert parse_contentline(raw) == cl
    assert cl.serialize(wrap=None) == raw

    for line in Parser.string_to_lines(cl.serialize()):
        assert len(line) <= DEFAULT_LINE_WRAP.width


@given(name=NAME, value=VALUE)
@example(name="A", value="abc\x85abc")
@pytest.mark.usefixtures("contentline_any_wrap")
def test_any_name_value_recode(name, value):
    raw = f"{name}:{value}"
    cl = ContentLine(name, value=value)
    assert_parses_to(raw, cl)


def quote_escape_param(pval):
    if re.search("[:;,]", pval):
        return f'"{escape_param(pval)}"'
    else:
        return escape_param(pval)


@given(param=NAME, value=VALUE_NONEMPTY)
@pytest.mark.usefixtures("contentline_any_wrap")
def test_any_param_value_recode(param, value):
    raw = f"TEST;{param}={quote_escape_param(value)}:VALUE"
    cl = ContentLine("TEST", {param: [value]}, "VALUE")
    assert_parses_to(raw, cl)


@given(
    name=NAME,
    value=VALUE,
    param1=NAME,
    p1value=VALUE_NONEMPTY,
    param2=NAME,
    p2value1=VALUE_NONEMPTY,
    p2value2=VALUE_NONEMPTY,
)
@pytest.mark.usefixtures("contentline_any_wrap")
def test_any_name_params_value_recode(
    name, value, param1, p1value, param2, p2value1, p2value2
):
    assume(param1 != param2)
    raw = "{};{}={};{}={},{}:{}".format(
        name,
        param1,
        quote_escape_param(p1value),
        param2,
        quote_escape_param(p2value1),
        quote_escape_param(p2value2),
        value,
    )
    cl = ContentLine(name, {param1: [p1value], param2: [p2value1, p2value2]}, value)
    assert_parses_to(raw, cl)


def test_contentline_parse_error():
    with pytest.raises(ParseError):
        (parse_contentline("haha;p1=v1"))
    with pytest.raises(ParseError):
        (parse_contentline("haha;p1:"))


def test_container():
    inp = """BEGIN:TEST
VAL1:The-Val
VAL2;PARAM1=P1;PARAM2=P2A,P2B;PARAM3="P3:A","P3:B,C":The-Val2
END:TEST"""
    out = Container(
        "TEST",
        [
            ContentLine(name="VAL1", params={}, value="The-Val"),
            ContentLine(
                name="VAL2",
                params={
                    "PARAM1": ["P1"],
                    "PARAM2": ["P2A", "P2B"],
                    "PARAM3": ["P3:A", "P3:B,C"],
                },
                value="The-Val2",
            ),
        ],
    )

    assert list(string_to_containers(inp)) == [out]
    assert out.serialize(wrap=None) == inp.replace("\n", "\r\n")
    assert (
        str(out)
        == "TEST[VAL1='The-Val', VAL2{'PARAM1': ['P1'], 'PARAM2': ['P2A', 'P2B'], 'PARAM3': ['P3:A', 'P3:B,C']}='The-Val2']"
    )
    assert (
        repr(out) == "Container('TEST', ["
        "ContentLine(name='VAL1', params={}, value='The-Val', line_nr=-1), "
        "ContentLine(name='VAL2', params={'PARAM1': ['P1'], 'PARAM2': ['P2A', 'P2B'], "
        "'PARAM3': ['P3:A', 'P3:B,C']}, value='The-Val2', line_nr=-1)])"
    )

    out_shallow = out.clone(deep=False)
    out_deep = out.clone(deep=True)
    assert out == out_shallow == out_deep
    assert all(a == b for a, b in zip(out, out_shallow))
    assert all(a == b for a, b in zip(out, out_deep))
    assert all(a is b for a, b in zip(out, out_shallow))
    assert all(a is not b for a, b in zip(out, out_deep))
    out_deep.append(ContentLine("LAST"))
    assert out != out_deep
    out[0].params["NEW"] = "SOMETHING"
    assert out == out_shallow
    out_shallow.name = "DIFFERENT"
    assert out != out_shallow

    with pytest.raises(TypeError):
        out_shallow[0] = ["CONTENT:Line"]
    with pytest.raises(TypeError):
        out_shallow[:] = ["CONTENT:Line"]
    pytest.raises(TypeError, out_shallow.append, "CONTENT:Line")
    pytest.raises(TypeError, out_shallow.append, ["CONTENT:Line"])
    pytest.raises(TypeError, out_shallow.extend, ["CONTENT:Line"])
    out_shallow[:] = [out[0]]
    assert out_shallow == Container("DIFFERENT", [out[0]])
    out_shallow[:] = []
    assert out_shallow == Container("DIFFERENT")
    out_shallow.append(ContentLine("CL1"))
    out_shallow.extend([ContentLine("CL3")])
    out_shallow.insert(1, ContentLine("CL2"))
    out_shallow += [ContentLine("CL4")]
    assert out_shallow[1:3] == Container(
        "DIFFERENT", [ContentLine("CL2"), ContentLine("CL3")]
    )
    assert out_shallow == Container(
        "DIFFERENT",
        [
            ContentLine("CL1"),
            ContentLine("CL2"),
            ContentLine("CL3"),
            ContentLine("CL4"),
        ],
    )

    with pytest.warns(UserWarning, match="not all-uppercase"):
        assert list(string_to_containers("BEGIN:test\nEND:TeSt")) == [
            Container("TEST", [])
        ]


def test_container_nested():
    inp = """BEGIN:TEST1
VAL1:The-Val
BEGIN:TEST2
VAL2:The-Val
BEGIN:TEST3
VAL3:The-Val
END:TEST3
END:TEST2
VAL4:The-Val
BEGIN:TEST2
VAL5:The-Val
END:TEST2
BEGIN:TEST2
VAL5:The-Val
END:TEST2
VAL6:The-Val
END:TEST1"""
    out = Container(
        "TEST1",
        [
            ContentLine(name="VAL1", params={}, value="The-Val"),
            Container(
                "TEST2",
                [
                    ContentLine(name="VAL2", params={}, value="The-Val"),
                    Container(
                        "TEST3", [ContentLine(name="VAL3", params={}, value="The-Val")]
                    ),
                ],
            ),
            ContentLine(name="VAL4", params={}, value="The-Val"),
            Container("TEST2", [ContentLine(name="VAL5", params={}, value="The-Val")]),
            Container("TEST2", [ContentLine(name="VAL5", params={}, value="The-Val")]),
            ContentLine(name="VAL6", params={}, value="The-Val"),
        ],
    )

    assert list(string_to_containers(inp)) == [out]
    assert out.serialize(wrap=None) == inp.replace("\n", "\r\n")


def test_container_parse_error():
    pytest.raises(ParseError, list, string_to_containers("BEGIN:TEST"))
    assert list(string_to_containers("END:TEST")) == [
        ContentLine(name="END", value="TEST")
    ]
    pytest.raises(ParseError, list, string_to_containers("BEGIN:TEST1\nEND:TEST2"))
    pytest.raises(
        ParseError, list, string_to_containers("BEGIN:TEST1\nEND:TEST2\nEND:TEST1")
    )
    assert list(string_to_containers("BEGIN:TEST1\nEND:TEST1\nEND:TEST1")) == [
        Container("TEST1"),
        ContentLine(name="END", value="TEST1"),
    ]
    pytest.raises(
        ParseError, list, string_to_containers("BEGIN:TEST1\nBEGIN:TEST1\nEND:TEST1")
    )


def test_unfold():
    val1 = "DESCRIPTION:This is a long description that exists on a long line."
    val2 = "DESCRIPTION:This is a lo\n ng description\n  that exists on a long line."
    assert unfold_str(val2) == val1
    assert parse_contentline(val1) == parse_contentline(val2)


@pytest.mark.usefixtures("contentline_any_wrap")
def test_value_characters():
    chars = (
        "abcABC0123456789"
        "-=_+!$%&*()[]{}<>'@#~/?|`¬€¨ÄÄää´ÁÁááßæÆ \t\\n😜🇪🇺👩🏾‍💻👨🏻‍👩🏻‍👧🏻‍👦🏻xyzXYZ"
    )
    special_chars = ';:,"^'
    inp = 'TEST;P1={chars};P2={chars},{chars},"{chars}",{chars}:{chars}:{chars}{special}'.format(
        chars=chars, special=special_chars
    )
    out = ContentLine(
        "TEST",
        {"P1": [chars], "P2": [chars, chars, QuotedParamValue(chars), chars]},
        chars + ":" + chars + special_chars,
    )
    assert_parses_to(inp, out)


def test_contentline_funcs():
    cl = ContentLine("TEST", {"PARAM": ["VAL"]}, "VALUE")
    assert cl["PARAM"] == ["VAL"]
    cl["PARAM2"] = ["VALA", "VALB"]
    assert cl.params == {"PARAM": ["VAL"], "PARAM2": ["VALA", "VALB"]}
    cl_clone = cl.clone()
    assert cl == cl_clone and cl is not cl_clone
    assert cl.params == cl_clone.params and cl.params is not cl_clone.params
    assert (
        cl.params["PARAM2"] == cl_clone.params["PARAM2"]
        and cl.params["PARAM2"] is not cl_clone.params["PARAM2"]
    )
    cl_clone["PARAM2"].append("VALC")
    assert cl != cl_clone
    assert str(cl) == "TEST{'PARAM': ['VAL'], 'PARAM2': ['VALA', 'VALB']}='VALUE'"
    assert (
        str(cl_clone)
        == "TEST{'PARAM': ['VAL'], 'PARAM2': ['VALA', 'VALB', 'VALC']}='VALUE'"
    )


# https://emojipedia.org/couple-with-heart-woman-man-light-skin-tone-dark-skin-tone/
EMOJI = "\U0001f469\U0001f3fb\u200d\u2764\ufe0f\u200d\U0001f468\U0001f3ff"


@given(inp=VALUE)
@example(inp=lipsum.generate_sentences(2))
@example(inp=lipsum.generate_paragraphs(1))
@example(inp=lipsum.generate_paragraphs(2))
@example(inp=lipsum.generate_paragraphs(10))
@example(inp=lipsum.generate_paragraphs(100))
@pytest.mark.usefixtures("contentline_any_wrap")
@settings(deadline=timedelta(seconds=10))  # the long lipsum texts take some time
def test_linefold(inp):
    inp = re.sub(Patterns.LINEBREAK, "\\\\n", inp)
    raw = f"TEST:{inp}"
    cl = ContentLine("TEST", value=inp)
    assert_parses_to(raw, cl)


for i in range(20):
    test_linefold.hypothesis_explicit_examples.append(
        Example(tuple(), dict(inp=EMOJI + " " * i + EMOJI * 100))
    )
