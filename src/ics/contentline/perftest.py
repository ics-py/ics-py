import argparse
import json
import shutil
import sys
from operator import itemgetter

import sh

try:
    import regex
except ImportError:
    MODES = [
        ["--parser", "tatsu"],
        ["--parser", "tatsu", "--linewise"],
        ["--parser", "tatsu", "--tatsu-pregen"],
        ["--parser", "tatsu", "--tatsu-pregen", "--linewise"],
        ["--parser", "handwritten"],
        ["--parser", "handwritten", "--linewise"],
    ]
else:
    MODES = [
        ["--parser", "tatsu", "--full-regex"],
        ["--parser", "tatsu", "--full-regex", "--linewise"],
        ["--parser", "tatsu", "--full-regex", "--tatsu-pregen"],
        ["--parser", "tatsu", "--full-regex", "--tatsu-pregen", "--linewise"],
        ["--parser", "regex", "--full-regex"],
        ["--parser", "regex", "--full-regex", "--linewise"],
        ["--parser", "handwritten", "--full-regex"],
        ["--parser", "handwritten", "--full-regex", "--linewise"],
    ]


def flatten_dict(inp):
    out = {}
    for key, val in inp.items():
        if isinstance(val, dict):
            out.update(val)
        else:
            out[key] = val
    return out


def cmp_file(f1, f2):
    bufsize = 8 * 1024
    with open(f1, 'rb') as fp1, open(f2, 'rb') as fp2:
        while True:
            b1 = fp1.read(bufsize)
            b2 = fp2.read(bufsize)
            if b1 != b2:
                return False
            if not b1:
                return True


if __name__ == "__main__":
    #  tox -e py38-re-contentline-perftest,py38-regex-contentline-perftest,pypy3-re-contentline-perftest,pypy3-regex-contentline-perftest
    #  -- holidays.ics --repeat=3 --full-json=perftest.json --filter-table=perftest.md
    parser = argparse.ArgumentParser()
    parser.add_argument('infile')
    parser.add_argument('--no-inmem', action="store_true")
    parser.add_argument('--repeat', type=int, default=10)
    parser.add_argument('--table-fmt', default="github")
    parser.add_argument('--reference', default="[infile]")
    parser.add_argument('--full-table', nargs='?', type=argparse.FileType('a'))
    parser.add_argument('--full-json', nargs='?', type=argparse.FileType('a'))
    # parser.add_argument('--filter', choices=["med"], default="med")
    parser.add_argument('--filter-table', nargs='?', type=argparse.FileType('a'), default=sys.stdout)
    parser.add_argument('--filter-json', nargs='?', type=argparse.FileType('a'))
    args = parser.parse_args()

    if args.reference == "[infile]":
        args.reference = args.infile

    outfile = "/tmp/icspy-perftest-outfile"
    # Path(__file__).parent.absolute().joinpath("__init__.py")
    perftest = sh.Command(sys.executable).bake("-m", "ics.contentline.__init__", outfile=outfile)
    variants = [perftest.bake(infile=args.infile, *mode) for mode in MODES]

    if not args.no_inmem:
        infile_mem = "/dev/shm/icspy-perftest-infile"
        shutil.copyfile(args.infile, infile_mem)
        variants.extend(perftest.bake(infile=infile_mem, *mode) for mode in MODES)

    full_table = []
    filter_table = []

    for variant in variants:
        variant_table = []
        for i in range(args.repeat):
            print(i, variant)
            success = False
            try:
                p = variant()
                success = True
            except sh.ErrorReturnCode as e:
                p = e  # pypy doesn't preserve the `except ... as` variable after of the block
                success = False
            stderr = p.stderr.decode().splitlines()
            errs = stderr[:-1]
            if errs:
                success = False
                print("\n".join(errs), file=sys.stderr)
            if success and args.reference and not cmp_file(args.reference, outfile):
                success = False
                print("Files differ", file=sys.stderr)
            stats = json.loads(stderr[-1])
            print(stats)
            variant_table.append(dict(success=success, run=i, key=stats[0], stats=stats[1], platform=stats[2]))

        filtered = sorted(filter(itemgetter("success"), variant_table), key=lambda d: d["stats"]["perf_counter"])
        if len(filtered) > 0:
            entry = dict(filtered[(len(filtered) // 2)])
        else:
            entry = dict(variant_table[0])
        del entry["success"]
        entry["successes"] = len(filtered)
        filter_table.append(entry)

        full_table.extend(variant_table)

    if args.full_json:
        json.dump(full_table, args.full_json)
    if args.filter_json:
        json.dump(filter_table, args.filter_json)
    if args.full_table:
        import tabulate

        print(tabulate.tabulate(map(flatten_dict, full_table), headers="keys", tablefmt=args.table_fmt), file=args.full_table)
    if args.filter_table:
        import tabulate

        print(tabulate.tabulate(map(flatten_dict, filter_table), headers="keys", tablefmt=args.table_fmt), file=args.filter_table)
