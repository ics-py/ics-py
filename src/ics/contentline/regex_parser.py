from itertools import tee, zip_longest, groupby
from typing import Iterator, Tuple, Union

from ics.contentline.common import *


def pairwise(iterable):
    """[s0, ..., sn] -> (s0,s1), (s1,s2), (s2, s3), ..., (s{n-1}, sn), (sn, None)"""
    a, b = tee(iterable)
    next(b, None)
    return zip_longest(a, b, fillvalue=None)


class RegexParser(Parser):

    def lines_to_contentlines(self, lines: Iterator[Union[Tuple[int, str], str]]) -> Iterator[ContentLine]:
        for line in lines:
            if not isinstance(line, str):
                nr, line = line
            else:
                nr = -1

            match = self.regex_impl.fullmatch(Patterns.LINE, line)
            if not match:
                raise ParseError("doesn't match line regex", nr, line=line)

            cl = ContentLine(name=match.group("name"), value=match.group("value"), line_nr=nr)
            try:
                pname = match.captures("pname")  # list of param names
            except AttributeError:
                raise ValueError("make sure you are using the `regex` module from pypi "
                                 "instead of the built-in `re` module as `regex_impl`")
            pvals = match.captures("pvals")  # list of param values, with one comma-separates string per param
            pval = match.captures("pval")  # individual param values, split at the commas
            assert len(pname) == len(pvals)
            assert len(pval) >= len(pvals)

            if len(pvals) == len(pval):
                # simple case, we have now multi-value params so pval and pvals are equal and directly map to pname
                for n, v in zip(pname, pval):
                    cl.params[n] = [QuotedParamValue.maybe_unquote(v)]

            else:
                # complicated case, for each individual pval we need to find out to which param name it belongs
                groups: Iterator[Tuple[str, int]] = zip(pname, match.end("pvals"))
                # groups is an iterable of (param name, end index of params value list)
                cur_group = next(groups)

                def find_param_section(item: Tuple[str, int]) -> str:
                    """for an item consisting of (single param value, end index of value in line) return the name of
                    the parameter list the value belongs to"""
                    nonlocal cur_group
                    val, val_to = item
                    group, group_to = cur_group
                    # while val ends after the current params value list, advance the current param group
                    while val_to > group_to:
                        cur_group = group, group_to = next(groups)
                    return group

                # this works because pval and groups are linearly sorted with an asceding index in the original string
                for n, vs in groupby(zip(pval, match.ends("pval")), find_param_section):
                    cl.params[n] = [
                        QuotedParamValue.maybe_unquote(v)
                        for v, _ in vs
                    ]

            yield cl
