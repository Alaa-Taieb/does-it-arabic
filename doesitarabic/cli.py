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


def cmd_build(args) -> int:
    from .site import build_site

    info = build_site()
    print(f"built {info['pages']} pages into {info['out']}")
    return 0


def cmd_serve(args) -> int:
    import functools
    import http.server

    from .paths import DIST
    from .site import build_site

    if not args.no_build:
        build_site()
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(DIST))
    with http.server.ThreadingHTTPServer((args.host, args.port), handler) as httpd:
        print(f"Does It Arabic? is running at http://{args.host}:{args.port}/  (Ctrl+C to stop)", flush=True)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass
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

    sub.add_parser("build", help="generate the static site and agent files into dist/").set_defaults(func=cmd_build)
    sv = sub.add_parser("serve", help="build the site and serve it locally")
    sv.add_argument("--port", type=int, default=8000)
    sv.add_argument("--host", default="127.0.0.1")
    sv.add_argument("--no-build", action="store_true")
    sv.set_defaults(func=cmd_serve)
    return p


def main(argv: list[str] | None = None) -> int:
    _utf8_stdout()
    args = build_parser().parse_args(argv)
    return args.func(args)
