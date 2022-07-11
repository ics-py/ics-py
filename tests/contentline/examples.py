from ics import ContentLine
from ics.contentline import QuotedParamValue

CONTENTLINE_EXAMPLES = [
    ("HAHA:", ContentLine(name="HAHA", params={}, value="")),
    ("HAHA:hoho", ContentLine(name="HAHA", params={}, value="hoho")),
    ("HAHA:hoho:hihi", ContentLine(name="HAHA", params={}, value="hoho:hihi")),
    (
        "HAHA;hoho=1:hoho",
        ContentLine(name="HAHA", params={"hoho": ["1"]}, value="hoho"),
    ),
    (
        "RRULE:FREQ=YEARLY;BYMONTH=3;BYDAY=-1SU",
        ContentLine(name="RRULE", params={}, value="FREQ=YEARLY;BYMONTH=3;BYDAY=-1SU"),
    ),
    (
        "SUMMARY:dfqsdfjqkshflqsjdfhqs fqsfhlqs dfkqsldfkqsdfqsfqsfqsfs",
        ContentLine(
            name="SUMMARY",
            params={},
            value="dfqsdfjqkshflqsjdfhqs fqsfhlqs dfkqsldfkqsdfqsfqsfqsfs",
        ),
    ),
    (
        "DTSTART;TZID=Europe/Brussels:20131029T103000",
        ContentLine(
            name="DTSTART",
            params={"TZID": ["Europe/Brussels"]},
            value="20131029T103000",
        ),
    ),
    (
        "haha;p2=v2;p1=v1:",
        ContentLine(name="HAHA", params={"p2": ["v2"], "p1": ["v1"]}, value=""),
    ),
    (
        "haha;hihi=p3,p4,p5;hoho=p1,p2:blabla:blublu",
        ContentLine(
            name="HAHA",
            params={"hihi": ["p3", "p4", "p5"], "hoho": ["p1", "p2"]},
            value="blabla:blublu",
        ),
    ),
    (
        'ATTENDEE;X-A="I&rsquo\\;ll be in NYC":mailto:a@a.com',
        ContentLine(
            name="ATTENDEE",
            params={"X-A": ["I&rsquo\\;ll be in NYC"]},
            value="mailto:a@a.com",
        ),
    ),
    (
        'DTEND;TZID="UTC":20190107T000000',
        ContentLine(
            name="DTEND",
            params={"TZID": [QuotedParamValue("UTC")]},
            value="20190107T000000",
        ),
    ),
    (
        'ATTENDEE;MEMBER="mailto:ietf-calsch@example.org":mailto:jsmith@example.com',
        ContentLine(
            "ATTENDEE",
            {"MEMBER": ["mailto:ietf-calsch@example.org"]},
            "mailto:jsmith@example.com",
        ),
    ),
    (
        'ATTENDEE;MEMBER="mailto:projectA@example.com","mailto:projectB@example.com":mailto:janedoe@example.com',
        ContentLine(
            "ATTENDEE",
            {"MEMBER": ["mailto:projectA@example.com", "mailto:projectB@example.com"]},
            "mailto:janedoe@example.com",
        ),
    ),
    (
        "RESOURCES:EASEL,PROJECTOR,VCR",
        ContentLine("RESOURCES", value="EASEL,PROJECTOR,VCR"),
    ),
    (
        "ATTENDEE;CN=George Herman ^'Babe^' Ruth:mailto:babe@example.com",
        ContentLine(
            "ATTENDEE", {"CN": ['George Herman "Babe" Ruth']}, "mailto:babe@example.com"
        ),
    ),
    (
        "GEO;X-ADDRESS=Pittsburgh Pirates^n115 Federal St^nPittsburgh, PA 15212:40.446816,-80.00566",
        ContentLine(
            "GEO",
            {
                "X-ADDRESS": [
                    "Pittsburgh Pirates\n115 Federal St\nPittsburgh",
                    " PA 15212",
                ]
            },
            "40.446816,-80.00566",
        ),
    ),
    (
        'GEO;X-ADDRESS="Pittsburgh Pirates^n115 Federal St^nPittsburgh, PA 15212":40.446816,-80.00566',
        ContentLine(
            "GEO",
            {"X-ADDRESS": ["Pittsburgh Pirates\n115 Federal St\nPittsburgh, PA 15212"]},
            "40.446816,-80.00566",
        ),
    ),
    (
        "SUMMARY:Project XYZ Final Review\\nConference Room - 3B\\nCome Prepared.",
        ContentLine(
            "SUMMARY",
            value="Project XYZ Final Review\\nConference Room - 3B\\nCome Prepared.",
        ),
    ),
    (
        'DESCRIPTION;ALTREP="cid:part1.0001@example.org":The Fall\'98 Wild Wizards Conference - - Las Vegas\\, NV\\, USA',
        ContentLine(
            "DESCRIPTION",
            {"ALTREP": ["cid:part1.0001@example.org"]},
            value="The Fall'98 Wild Wizards Conference - - Las Vegas\\, NV\\, USA",
        ),
    ),
    (
        "DTSTART;TZID=Mitteleuropäische Sommerzeit:20200401T180000",
        ContentLine(
            "DTSTART",
            {"TZID": ["Mitteleuropäische Sommerzeit"]},
            value="20200401T180000",
        ),
    ),
]
