#!/usr/bin/env python3
from typing import Union, Type

from ics.contentline.common import *
from ics.contentline.common import __all__ as common_all

__all__ = common_all + ["PARSER", "string_to_containers", "lines_to_containers", "get_parser"]

try:
    import regex
    from ics.contentline.regex_capture import RegexParser

    PARSER = RegexParser(regex)
except ImportError:
    import re
    from ics.contentline.handwritten import HandwrittenParser

    PARSER = HandwrittenParser(re)

string_to_containers = PARSER.string_to_containers
lines_to_containers = PARSER.lines_to_containers


def get_parser_name(name: Union[str, Parser, Type[Parser]]) -> str:
    if isinstance(name, Parser):
        name = type(name)
    if isinstance(name, type):
        name = name.__name__
    name = name.lower()
    if name.endswith("parser"):
        name = name[:-len("parser")]
    return name


def get_parser(name: Union[str, Parser, Type[Parser]], full_regex=False, tatsu_pregen=None) -> Parser:
    if full_regex:
        import regex as regex_impl
    else:
        import re as regex_impl

    name = get_parser_name(name)
    if name == "tatsu":
        from ics.contentline.tatsu_parser import TatsuParser, GRAMMAR

        if tatsu_pregen:
            from ics.contentline.grammar import contentlineParser

            return TatsuParser(regex_impl, contentlineParser())
        else:
            return TatsuParser(regex_impl, GRAMMAR)
    elif name == "regex":
        from ics.contentline.regex_parser import RegexParser

        return RegexParser(regex_impl)
    elif name == "handwritten":
        from ics.contentline.handwritten import HandwrittenParser

        return HandwrittenParser(regex_impl)


if __name__ == "__main__":
    import argparse
    import sys
    import platform
    import time
    import resource
    import json
    from traceback import print_exc

    parser = argparse.ArgumentParser()
    parser.add_argument('--infile', nargs='?', type=argparse.FileType('r'), default=sys.stdin)
    parser.add_argument('--outfile', nargs='?', type=argparse.FileType('w'), default=sys.stdout)
    parser.add_argument('--parser', choices=["tatsu", "regex", "handwritten"], default=get_parser_name(PARSER))
    parser.add_argument('--full-regex', action='store_true')
    parser.add_argument('--tatsu-pregen', action='store_true')
    parser.add_argument('--linewise', action='store_true')
    parser.add_argument('--quiet', action='store_true')
    parser.add_argument('--no-write', action='store_true')
    args = parser.parse_args()

    parser = get_parser(args.parser, args.full_regex, args.tatsu_pregen)

    success = False
    lines = []
    start = (time.perf_counter(), time.process_time())
    try:
        if args.linewise:
            lines = list(parser.lines_to_containers(args.infile))
        else:
            lines = list(parser.string_to_containers(args.infile.read()))
        success = True
    except Exception:
        print_exc()
    end = (time.perf_counter(), time.process_time())

    if not args.quiet:
        name = dict(vars(args))
        name["infile"] = name["infile"].name
        name["outfile"] = name["outfile"].name
        data = {"perf_counter": end[0] - start[0], "process_time": end[1] - start[1]}
        data.update(zip(
            ("utime", "stime", "maxrss", "ixrss", "idrss", "isrss", "minflt", "majflt",
             "nswap", "inblock", "oublock", "msgsnd", "msgrcv", "nsignals", "nvcsw", "nivcsw"),
            resource.getrusage(resource.RUSAGE_SELF)))
        sysinfo = {
            "platform": platform.platform(),
            "pyver": platform.python_version_tuple(),
            "pyimpl": platform.python_implementation()
        }
        print(json.dumps([name, data, sysinfo]), file=sys.stderr)

    if not args.no_write:
        for line in lines:
            for chunk in line.serialize_iter(False):
                args.outfile.write(chunk)
        args.outfile.flush()

    exit(0 if success else 1)
