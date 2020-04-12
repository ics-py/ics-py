import re

import pytest
from hypothesis import assume, given
from hypothesis.strategies import characters, text

from ics.grammar import Container, ContentLine, ParseError, QuotedParamValue, escape_param, string_to_container, unfold_lines

CONTROL = [chr(i) for i in range(ord(" ")) if i != ord("\t")] + [chr(0x7F)]
NAME = text(alphabet=(characters(whitelist_categories=["Lu"], whitelist_characters=["-"], max_codepoint=128)), min_size=1)
VALUE = text(characters(blacklist_categories=["Cs"], blacklist_characters=CONTROL))


@pytest.mark.parametrize("inp, out", [
    ('HAHA:', ContentLine(name='HAHA', params={}, value='')),
    ('HAHA:hoho', ContentLine(name='HAHA', params={}, value='hoho')),
    ('HAHA:hoho:hihi', ContentLine(name='HAHA', params={}, value='hoho:hihi')),
    (
            'HAHA;hoho=1:hoho',
            ContentLine(name='HAHA', params={'hoho': ['1']}, value='hoho')
    ), (
            'RRULE:FREQ=YEARLY;BYMONTH=3;BYDAY=-1SU',
            ContentLine(name='RRULE', params={}, value='FREQ=YEARLY;BYMONTH=3;BYDAY=-1SU')
    ), (
            'SUMMARY:dfqsdfjqkshflqsjdfhqs fqsfhlqs dfkqsldfkqsdfqsfqsfqsfs',
            ContentLine(name='SUMMARY', params={}, value='dfqsdfjqkshflqsjdfhqs fqsfhlqs dfkqsldfkqsdfqsfqsfqsfs')
    ), (
            'DTSTART;TZID=Europe/Brussels:20131029T103000',
            ContentLine(name='DTSTART', params={'TZID': ['Europe/Brussels']}, value='20131029T103000')
    ), (
            'haha;p2=v2;p1=v1:',
            ContentLine(name='HAHA', params={'p2': ['v2'], 'p1': ['v1']}, value='')
    ), (
            'haha;hihi=p3,p4,p5;hoho=p1,p2:blabla:blublu',
            ContentLine(name='HAHA', params={'hihi': ['p3', 'p4', 'p5'], 'hoho': ['p1', 'p2']}, value='blabla:blublu')
    ), (
            'ATTENDEE;X-A="I&rsquo\\;ll be in NYC":mailto:a@a.com',
            ContentLine(name='ATTENDEE', params={'X-A': ['I&rsquo\\;ll be in NYC']}, value='mailto:a@a.com')
    ), (
            'DTEND;TZID="UTC":20190107T000000',
            ContentLine(name='DTEND', params={'TZID': [QuotedParamValue('UTC')]}, value='20190107T000000')
    ), (
            "ATTENDEE;MEMBER=\"mailto:ietf-calsch@example.org\":mailto:jsmith@example.com",
            ContentLine("ATTENDEE", {"MEMBER": ["mailto:ietf-calsch@example.org"]}, "mailto:jsmith@example.com")
    ), (
            "ATTENDEE;MEMBER=\"mailto:projectA@example.com\",\"mailto:projectB@example.com\":mailto:janedoe@example.com",
            ContentLine("ATTENDEE", {"MEMBER": ["mailto:projectA@example.com", "mailto:projectB@example.com"]}, "mailto:janedoe@example.com")
    ), (
            "RESOURCES:EASEL,PROJECTOR,VCR",
            ContentLine("RESOURCES", value="EASEL,PROJECTOR,VCR")
    ), (
            "ATTENDEE;CN=George Herman ^'Babe^' Ruth:mailto:babe@example.com",
            ContentLine("ATTENDEE", {"CN": ["George Herman \"Babe\" Ruth"]}, "mailto:babe@example.com")
    ), (
            "GEO;X-ADDRESS=Pittsburgh Pirates^n115 Federal St^nPittsburgh, PA 15212:40.446816,-80.00566",
            ContentLine("GEO", {"X-ADDRESS": ["Pittsburgh Pirates\n115 Federal St\nPittsburgh", " PA 15212"]}, "40.446816,-80.00566")
    ), (
            "GEO;X-ADDRESS=\"Pittsburgh Pirates^n115 Federal St^nPittsburgh, PA 15212\":40.446816,-80.00566",
            ContentLine("GEO", {"X-ADDRESS": ["Pittsburgh Pirates\n115 Federal St\nPittsburgh, PA 15212"]}, "40.446816,-80.00566")
    ), (
            "SUMMARY:Project XYZ Final Review\\nConference Room - 3B\\nCome Prepared.",
            ContentLine("SUMMARY", value="Project XYZ Final Review\\nConference Room - 3B\\nCome Prepared.")
    ), (
            "DESCRIPTION;ALTREP=\"cid:part1.0001@example.org\":The Fall'98 Wild Wizards Conference - - Las Vegas\\, NV\\, USA",
            ContentLine("DESCRIPTION", {"ALTREP": ["cid:part1.0001@example.org"]}, value="The Fall'98 Wild Wizards Conference - - Las Vegas\\, NV\\, USA")
    ),

])
def test_example_recode(inp, out):
    par = ContentLine.parse(inp)
    assert par == out
    ser = out.serialize()
    if inp[0].isupper():
        assert inp == ser
    else:
        assert inp.upper() == ser.upper()
    par_ser = par.serialize()
    if inp[0].isupper():
        assert inp == par_ser
    else:
        assert inp.upper() == par_ser.upper()
    assert string_to_container(inp) == [out]


def test_param_quoting():
    inp = 'TEST;P1="A";P2=B;P3=C,"D",E,"F":"VAL"'
    out = ContentLine("TEST", {
        "P1": [QuotedParamValue("A")],
        "P2": ["B"],
        "P3": ["C", QuotedParamValue("D"), "E", QuotedParamValue("F")],
    }, '"VAL"')
    par = ContentLine.parse(inp)
    assert par == out
    ser = out.serialize()
    assert inp == ser
    par_ser = par.serialize()
    assert inp == par_ser
    assert string_to_container(inp) == [out]

    for param in out.params.keys():
        for o_val, p_val in zip(out[param], par[param]):
            assert type(o_val) == type(p_val)


def test_trailing_escape_param():
    with pytest.raises(ValueError) as excinfo:
        ContentLine.parse("TEST;PARAM=this ^^ is a ^'param^',with a ^trailing escape^:value")
    assert "not end with an escape sequence" in str(excinfo.value)
    assert ContentLine.parse("TEST;PARAM=this ^^ is a ^'param^',with a ^trailing escape:value").params["PARAM"] == \
           ["this ^ is a \"param\"", "with a ^trailing escape"]


@given(name=NAME, value=VALUE)
def test_any_name_value_recode(name, value):
    raw = "%s:%s" % (name, value)
    assert ContentLine.parse(raw).serialize() == raw
    cl = ContentLine(name, value=value)
    assert ContentLine.parse(cl.serialize()) == cl
    assert string_to_container(raw) == [cl]


def quote_escape_param(pval):
    if re.search("[:;,]", pval):
        return '"%s"' % escape_param(pval)
    else:
        return escape_param(pval)


@given(param=NAME, value=VALUE)
def test_any_param_value_recode(param, value):
    raw = "TEST;%s=%s:VALUE" % (param, quote_escape_param(value))
    assert ContentLine.parse(raw).serialize() == raw
    cl = ContentLine("TEST", {param: [value]}, "VALUE")
    assert ContentLine.parse(cl.serialize()) == cl
    assert string_to_container(raw) == [cl]


@given(name=NAME, value=VALUE,
       param1=NAME, p1value=VALUE,
       param2=NAME, p2value1=VALUE, p2value2=VALUE)
def test_any_name_params_value_recode(name, value, param1, p1value, param2, p2value1, p2value2):
    assume(param1 != param2)
    raw = "%s;%s=%s;%s=%s,%s:%s" % (name, param1, quote_escape_param(p1value),
                                    param2, quote_escape_param(p2value1), quote_escape_param(p2value2), value)
    assert ContentLine.parse(raw).serialize() == raw
    cl = ContentLine(name, {param1: [p1value], param2: [p2value1, p2value2]}, value)
    assert ContentLine.parse(cl.serialize()) == cl
    assert string_to_container(raw) == [cl]


def test_contentline_parse_error():
    pytest.raises(ParseError, ContentLine.parse, 'haha;p1=v1')
    pytest.raises(ParseError, ContentLine.parse, 'haha;p1:')


def test_container():
    inp = """BEGIN:TEST
VAL1:The-Val
VAL2;PARAM1=P1;PARAM2=P2A,P2B;PARAM3="P3:A","P3:B,C":The-Val2
END:TEST"""
    out = Container('TEST', [
        ContentLine(name='VAL1', params={}, value='The-Val'),
        ContentLine(name='VAL2', params={'PARAM1': ['P1'], 'PARAM2': ['P2A', 'P2B'], 'PARAM3': ['P3:A', 'P3:B,C']}, value='The-Val2')])

    assert string_to_container(inp) == [out]
    assert out.serialize() == inp.replace("\n", "\r\n")
    assert str(out) == "TEST[VAL1='The-Val', VAL2{'PARAM1': ['P1'], 'PARAM2': ['P2A', 'P2B'], 'PARAM3': ['P3:A', 'P3:B,C']}='The-Val2']"
    assert repr(out) == "Container('TEST', [ContentLine(name='VAL1', params={}, value='The-Val'), ContentLine(name='VAL2', params={'PARAM1': ['P1'], 'PARAM2': ['P2A', 'P2B'], 'PARAM3': ['P3:A', 'P3:B,C']}, value='The-Val2')])"

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
        out_shallow[0] = ['CONTENT:Line']
    with pytest.raises(TypeError):
        out_shallow[:] = ['CONTENT:Line']
    pytest.raises(TypeError, out_shallow.append, 'CONTENT:Line')
    pytest.raises(TypeError, out_shallow.append, ['CONTENT:Line'])
    pytest.raises(TypeError, out_shallow.extend, ['CONTENT:Line'])
    out_shallow[:] = [out[0]]
    assert out_shallow == Container("DIFFERENT", [out[0]])
    out_shallow[:] = []
    assert out_shallow == Container("DIFFERENT")
    out_shallow.append(ContentLine("CL1"))
    out_shallow.extend([ContentLine("CL3")])
    out_shallow.insert(1, ContentLine("CL2"))
    out_shallow += [ContentLine("CL4")]
    assert out_shallow[1:3] == Container("DIFFERENT", [ContentLine("CL2"), ContentLine("CL3")])
    assert out_shallow == Container("DIFFERENT", [ContentLine("CL1"), ContentLine("CL2"), ContentLine("CL3"), ContentLine("CL4")])

    with pytest.warns(UserWarning, match="not all-uppercase"):
        assert string_to_container("BEGIN:test\nEND:TeSt") == [Container("TEST", [])]


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
    out = Container('TEST1', [
        ContentLine(name='VAL1', params={}, value='The-Val'),
        Container('TEST2', [
            ContentLine(name='VAL2', params={}, value='The-Val'),
            Container('TEST3', [
                ContentLine(name='VAL3', params={}, value='The-Val')
            ])
        ]),
        ContentLine(name='VAL4', params={}, value='The-Val'),
        Container('TEST2', [
            ContentLine(name='VAL5', params={}, value='The-Val')]),
        Container('TEST2', [
            ContentLine(name='VAL5', params={}, value='The-Val')]),
        ContentLine(name='VAL6', params={}, value='The-Val')])

    assert string_to_container(inp) == [out]
    assert out.serialize() == inp.replace("\n", "\r\n")


def test_container_parse_error():
    pytest.raises(ParseError, string_to_container, "BEGIN:TEST")
    assert string_to_container("END:TEST") == [ContentLine(name="END", value="TEST")]
    pytest.raises(ParseError, string_to_container, "BEGIN:TEST1\nEND:TEST2")
    pytest.raises(ParseError, string_to_container, "BEGIN:TEST1\nEND:TEST2\nEND:TEST1")
    assert string_to_container("BEGIN:TEST1\nEND:TEST1\nEND:TEST1") == [Container("TEST1"), ContentLine(name="END", value="TEST1")]
    pytest.raises(ParseError, string_to_container, "BEGIN:TEST1\nBEGIN:TEST1\nEND:TEST1")


def test_unfold():
    val1 = "DESCRIPTION:This is a long description that exists on a long line."
    val2 = "DESCRIPTION:This is a lo\n ng description\n  that exists on a long line."
    assert "".join(unfold_lines(val2.splitlines())) == val1
    assert string_to_container(val1) == string_to_container(val2) == [ContentLine.parse(val1)]
    pytest.raises(ValueError, ContentLine.parse, val2)


def test_value_characters():
    chars = "abcABC0123456789"  "-=_+!$%&*()[]{}<>'@#~/?|`¬€¨ÄÄää´ÁÁááßæÆ \t\\n😜🇪🇺👩🏾‍💻👨🏻‍👩🏻‍👧🏻‍👦🏻xyzXYZ"
    special_chars = ";:,\"^"
    inp = "TEST;P1={chars};P2={chars},{chars},\"{chars}\",{chars}:{chars}:{chars}{special}".format(
        chars=chars, special=special_chars)
    out = ContentLine("TEST", {"P1": [chars], "P2": [chars, chars, QuotedParamValue(chars), chars]},
                      chars + ":" + chars + special_chars)
    par = ContentLine.parse(inp)
    assert par == out
    ser = out.serialize()
    assert inp == ser
    par_ser = par.serialize()
    assert inp == par_ser
    assert string_to_container(inp) == [out]


def test_contentline_funcs():
    cl = ContentLine("TEST", {"PARAM": ["VAL"]}, "VALUE")
    assert cl["PARAM"] == ["VAL"]
    cl["PARAM2"] = ["VALA", "VALB"]
    assert cl.params == {"PARAM": ["VAL"], "PARAM2": ["VALA", "VALB"]}
    cl_clone = cl.clone()
    assert cl == cl_clone and cl is not cl_clone
    assert cl.params == cl_clone.params and cl.params is not cl_clone.params
    assert cl.params["PARAM2"] == cl_clone.params["PARAM2"] and cl.params["PARAM2"] is not cl_clone.params["PARAM2"]
    cl_clone["PARAM2"].append("VALC")
    assert cl != cl_clone
    assert str(cl) == "TEST{'PARAM': ['VAL'], 'PARAM2': ['VALA', 'VALB']}='VALUE'"
    assert str(cl_clone) == "TEST{'PARAM': ['VAL'], 'PARAM2': ['VALA', 'VALB', 'VALC']}='VALUE'"
