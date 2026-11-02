"""Command line interface."""

from __future__ import annotations

import argparse
import sys

from .fixtures import load_fixtures


def _utf8_stdout() -> None:
    # Windows consoles default to a legacy code page; fixture text is Arabic/Hebrew.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")


def cmd_fixtures(args) -> int:
    for f in load_fixtures()["fixtures"]:
        print(f"{f['id']:13s} {f['dir']}  {f['title']}")
    return 0


def cmd_references(args) -> int:
    from .reference import render_references

    meta = render_references(load_fixtures())
    print(f"rendered reference variants with {meta['renderer']} {meta['version']}")
    return 0


def cmd_matrix(args) -> int:
    from .matrix import run_matrix

    m = run_matrix(only=args.only or None, rerender_reference=not args.keep_reference)
    rows = m["rows"]
    print(f"\n{sum(r['summary'] == 'pass' for r in rows)}/{len(rows)} configurations pass every fixture; "
          f"results/matrix.json written")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="doesitarabic", description="Does It Arabic? RTL test matrix")
    sub = p.add_subparsers(dest="command", required=True)

    sub.add_parser("fixtures", help="list the fixtures").set_defaults(func=cmd_fixtures)
    sub.add_parser("references", help="render the Chromium reference and failure variants").set_defaults(
        func=cmd_references)

    m = sub.add_parser("matrix", help="run every adapter and judge the outputs")
    m.add_argument("--only", nargs="*", help="adapter ids to run (others keep their previous results)")
    m.add_argument("--keep-reference", action="store_true", help="reuse the existing reference renders")
    m.set_defaults(func=cmd_matrix)
    return p


def main(argv: list[str] | None = None) -> int:
    _utf8_stdout()
    args = build_parser().parse_args(argv)
    return args.func(args)
