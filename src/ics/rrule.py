import dateutil.rrule

from ics.contentline.parser import ContentLineParser

__all__ = [
    "rrule_to_dict",
    "rrule_to_ContentLine",
    "rrule_eq",
    "rrule_hash",
    "rrule_repr",
    "rruleset_eq",
    "rruleset_str",
    "rruleset_repr",
    "rruleset_hash",
]


def rrule_to_dict(self: dateutil.rrule.rrule):
    return {
        "interval": self._interval,  # type: ignore[attr-defined]
        "count": self._count,  # type: ignore[attr-defined]
        "dtstart": self._dtstart,  # type: ignore[attr-defined]
        "freq": self._freq,  # type: ignore[attr-defined]
        "until": self._until,  # type: ignore[attr-defined]
        "wkst": self._wkst,  # type: ignore[attr-defined]
        **self._original_rule,  # type: ignore[attr-defined]
    }


def rrule_to_ContentLine(self: dateutil.rrule.rrule):
    val = str(self).splitlines()
    while val[0].startswith("DTSTART"):
        val = val[1:]
    assert len(val) == 1
    return ContentLineParser().parse(val[0])


def rrule_eq(self: dateutil.rrule.rrule, other: dateutil.rrule.rrule):
    if not isinstance(other, dateutil.rrule.rrule):
        return False
    return rrule_to_dict(self) == rrule_to_dict(other)


def rrule_hash(self: dateutil.rrule.rrule):
    return hash(tuple(rrule_to_dict(self).items()))


def rrule_repr(self: dateutil.rrule.rrule):
    return f"rrule({', '.join(f'{k}={v!r}' for k, v in rrule_to_dict(self).items())})"


def rruleset_eq(self: dateutil.rrule.rruleset, other: dateutil.rrule.rruleset):
    if not isinstance(other, dateutil.rrule.rruleset):
        return False
    return self._rrule == other._rrule and self._rdate == other._rdate and self._exrule == other._exrule and self._exdate == other._exdate  # type: ignore[attr-defined]


def rruleset_str(self: dateutil.rrule.rruleset):
    out = ""
    for rrule in self._rrule:  # type: ignore[attr-defined]
        out += str(rrule) + "\n"
    for exrule in self._exrule:  # type: ignore[attr-defined]
        out += "EX" + str(exrule)[1:] + "\n"  # replace the R-RULE by an EX-RULE
    for rdate in self._rdate:  # type: ignore[attr-defined]
        out += str(rdate) + "\n"
    for exdate in self._exdate:  # type: ignore[attr-defined]
        out += str(exdate) + "\n"
    return out


def rruleset_repr(self: dateutil.rrule.rruleset):
    return "rruleset(rrule={}, exrule={}, rdate={!r}, exdate={!r})".format(
        self._rrule,  # type: ignore[attr-defined]
        self._exrule,  # type: ignore[attr-defined]
        self._rdate,  # type: ignore[attr-defined]
        self._exdate,  # type: ignore[attr-defined]
    )


def rruleset_hash(self: dateutil.rrule.rruleset):
    return hash(
        (
            tuple(self._rrule),  # type: ignore[attr-defined]
            tuple(self._rdate),  # type: ignore[attr-defined]
            tuple(self._exrule),  # type: ignore[attr-defined]
            tuple(self._exdate),  # type: ignore[attr-defined]
        )
    )


dateutil.rrule.rrule.__eq__ = rrule_eq  # type: ignore[assignment]
dateutil.rrule.rrule.__hash__ = rrule_hash  # type: ignore[assignment]
dateutil.rrule.rrule.__repr__ = rrule_repr  # type: ignore[assignment]
dateutil.rrule.rruleset.__eq__ = rruleset_eq  # type: ignore[assignment]
dateutil.rrule.rruleset.__hash__ = rruleset_hash  # type: ignore[assignment]
dateutil.rrule.rruleset.__str__ = rruleset_str  # type: ignore[assignment]
dateutil.rrule.rruleset.__repr__ = rruleset_repr  # type: ignore[assignment]
