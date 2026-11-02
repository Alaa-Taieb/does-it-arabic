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


def cmd_check(args) -> int:
    import json
    from pathlib import Path

    from .check import check_endpoint, judge_file, markdown_report, parse_spec, reference_dir_for

    try:
        ref_dir = reference_dir_for(Path(args.font) if args.font else None)
        if args.endpoint:
            ids = args.fixture or [f["id"] for f in load_fixtures()["fixtures"]]
            results = check_endpoint(args.endpoint, ids, ref_dir, args.method)
        else:
            if args.spec or args.spec_file:
                spec = args.spec if args.spec else Path(args.spec_file).read_text(encoding="utf-8")
                pairs = parse_spec(spec)
            elif args.file and args.fixture and len(args.fixture) == 1:
                pairs = [(args.fixture[0], args.file)]
            else:
                print("give FILE --fixture ID, --spec, --spec-file or --endpoint", file=sys.stderr)
                return 2
            results = [judge_file(path, fid, ref_dir) for fid, path in pairs]
    except (ValueError, KeyError, FileNotFoundError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps([r.to_dict() for r in results], ensure_ascii=False, indent=2))
    else:
        for r in results:
            mark = "PASS" if r.verdict == "pass" else r.verdict.upper()
            print(f"{mark:8s} {r.fixture:13s} {r.label}")
            if r.verdict != "pass" and r.advice:
                print(f"         fix: {r.advice}")
    if args.summary:
        with open(args.summary, "a", encoding="utf-8") as fh:
            fh.write(markdown_report(results, args.allow_partial))
    return 0 if all(r.ok(args.allow_partial) for r in results) else 1


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

    c = sub.add_parser("check", help="judge your own PDF/PNG output (or an endpoint) against the fixtures")
    c.add_argument("file", nargs="?", help="PDF, PNG, JPEG or WebP containing only the fixture text")
    c.add_argument("--fixture", action="append", help="fixture id (repeat for several with --endpoint)")
    c.add_argument("--spec", help="lines of '<fixture-id> <path>'")
    c.add_argument("--spec-file", help="file with lines of '<fixture-id> <path>'")
    c.add_argument("--endpoint", help="URL that renders a fixture: POST JSON {id,text,dir,lang}, or GET with {text}")
    c.add_argument("--method", default="POST", choices=["POST", "GET"])
    c.add_argument("--font", help="the TTF/OTF your output uses (references are rendered with it)")
    c.add_argument("--allow-partial", action="store_true", help="treat 'partial' (LTR base direction) as passing")
    c.add_argument("--json", action="store_true")
    c.add_argument("--summary", help="append a Markdown report to this file (e.g. $GITHUB_STEP_SUMMARY)")
    c.set_defaults(func=cmd_check)
    return p


def main(argv: list[str] | None = None) -> int:
    _utf8_stdout()
    args = build_parser().parse_args(argv)
    return args.func(args)
