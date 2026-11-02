"""Generate the static site and the agent-facing files from results/matrix.json.

Everything here is derived from matrix.json: no verdict is typed by hand.
"""

from __future__ import annotations

import html
import json
import shutil
from pathlib import Path

from .paths import DIST, RESULTS, ROOT

ICON = {"pass": "✓", "partial": "◐", "fail": "✗", "mismatch": "≠", "error": "!", "n/a": "–"}
WORD = {"pass": "pass", "partial": "partial", "fail": "fail", "mismatch": "mismatch (needs review)",
        "error": "error", "n/a": "not applicable"}
CATEGORY = {"pdf": "PDF", "og-image": "OG / image", "chart": "Chart"}


def e(s) -> str:
    return html.escape(str(s), quote=True)


def load_matrix(results: Path = RESULTS) -> dict:
    path = results / "matrix.json"
    if not path.exists():
        raise FileNotFoundError(f"{path} not found; run `npm run matrix` first")
    return json.loads(path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------- derived facts

def alternatives(matrix: dict, row: dict) -> list[dict]:
    """Rows that pass every fixture, same ecosystem first, then same category."""
    passing = [r for r in matrix["rows"] if r["summary"] == "pass" and r["id"] != row["id"]]
    same_eco = [r for r in passing if r["ecosystem"] == row["ecosystem"]]
    same_cat = [r for r in same_eco if r["category"] == row["category"]]
    rest = [r for r in same_eco if r not in same_cat]
    return same_cat + rest


def related(matrix: dict, row: dict) -> list[dict]:
    """Other tested configurations of the same package (built-in options, workarounds)."""
    return [r for r in matrix["rows"] if r["package"] == row["package"] and r["id"] != row["id"]]


def stats(matrix: dict) -> dict:
    rows = matrix["rows"]
    inv = [r["cells"].get("invoice-line", {}).get("verdict") for r in rows]
    cells = [c for r in rows for c in r["cells"].values()]
    return {
        "rows": len(rows),
        "all_pass": sum(r["summary"] == "pass" for r in rows),
        "invoice_judged": sum(v not in (None, "n/a", "error") for v in inv),
        "invoice_broken": sum(v in ("fail", "partial", "mismatch") for v in inv),
        "reviewed": sum(1 for c in cells if c.get("review")),
        "cells": len(cells),
    }


def worse_workarounds(matrix: dict) -> list[str]:
    """Workaround rows that pass fewer fixtures than the plain library they were meant to fix."""
    out = []
    for w in matrix["rows"]:
        if w["mode"] != "workaround":
            continue
        base = next((r for r in matrix["rows"] if r["package"] == w["package"] and r["mode"] == "default"), None)
        if base and w["passed"] < base["passed"]:
            out.append(f"{w['library']} passes {w['passed']}/{w['judged']} fixtures, plain {base['library']} "
                       f"passes {base['passed']}/{base['judged']}: the workaround makes it worse.")
    return out


def failing_fixtures(row: dict, fixtures: list[dict]) -> list[str]:
    titles = {f["id"]: f["title"] for f in fixtures}
    return [titles[fid] for fid, c in row["cells"].items() if c["verdict"] not in ("pass", "n/a")]


# ---------------------------------------------------------------- HTML

CSS = """
:root { --pass:#1a7f37; --partial:#9a6700; --fail:#cf222e; --mismatch:#bc4c00; --error:#57606a; --na:#8c959f;
        --bg:#fff; --fg:#1f2328; --muted:#59636e; --line:#d1d9e0; --soft:#f6f8fa; }
@media (prefers-color-scheme: dark) { :root { --bg:#0d1117; --fg:#e6edf3; --muted:#9198a1; --line:#3d444d; --soft:#151b23;
  --pass:#3fb950; --partial:#d29922; --fail:#f85149; --mismatch:#db6d28; } }
* { box-sizing: border-box; }
body { margin:0; font:15px/1.5 system-ui,-apple-system,"Segoe UI",sans-serif; background:var(--bg); color:var(--fg); }
main { max-width: 1180px; margin: 0 auto; padding: 24px 20px 64px; }
a { color: inherit; }
h1 { font-size: 30px; margin: 8px 0 4px; } h2 { margin-top: 40px; font-size: 21px; }
.muted { color: var(--muted); } .small { font-size: 13px; }
.notice { border:1px solid var(--line); background:var(--soft); padding:10px 14px; border-radius:8px; margin:16px 0; }
table { border-collapse: collapse; width: 100%; }
th, td { border-bottom: 1px solid var(--line); padding: 6px 8px; text-align: left; vertical-align: middle; }
th { font-size: 12px; font-weight: 600; color: var(--muted); }
.grid td.c { text-align: center; width: 76px; }
.v { display:inline-block; min-width: 30px; padding: 1px 6px; border-radius: 6px; font-weight: 700; color:#fff; text-align:center; text-decoration:none; }
.v.pass{background:var(--pass)} .v.partial{background:var(--partial)} .v.fail{background:var(--fail)}
.v.mismatch{background:var(--mismatch)} .v.error{background:var(--error)} .v.na{background:transparent;color:var(--na)}
.tag { font-size: 12px; border:1px solid var(--line); border-radius: 10px; padding: 0 7px; color: var(--muted); white-space:nowrap; }
.strip { display:grid; grid-template-columns: 220px 1fr 110px; gap: 6px 14px; align-items:center; }
.pair img { height: 72px; width: auto; object-fit: contain; object-position: left center; }
.fixture.wrap .pair img { height: 140px; }
.strip img, .pair img { max-width:100%; background:#fff; border:1px solid var(--line); border-radius:4px; }
.strip .lib { font-weight: 600; }
.strip img { height: 56px; width: auto; object-fit: contain; object-position: left center; }
.pair { display:grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.fixture { border:1px solid var(--line); border-radius: 10px; padding: 14px; margin: 16px 0; }
.fixture h3 { margin: 0 0 6px; font-size: 17px; }
pre { background: var(--soft); border:1px solid var(--line); padding: 12px; border-radius: 8px; overflow:auto; font-size: 13px; }
.rtl { direction: rtl; unicode-bidi: isolate; font-size: 18px; }
nav a { margin-right: 14px; }
.legend span { margin-right: 14px; white-space: nowrap; }
"""


def page(title: str, body: str, depth: int = 0) -> str:
    up = "../" * depth
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(title)}</title><link rel="icon" href="data:,"><link rel="stylesheet" href="{up}style.css">
<link rel="alternate" type="application/json" href="{up}matrix.json"></head>
<body><main>
<nav class="small"><a href="{up}index.html">Matrix</a><a href="{up}fixtures.html">Fixtures</a><a href="{up}method.html">How it is judged</a><a href="{up}matrix.json">matrix.json</a><a href="{up}llms.txt">llms.txt</a><a href="{up}skill/SKILL.md">Agent skill</a></nav>
{body}
</main></body></html>
"""


def badge(cell: dict, href: str | None = None) -> str:
    v = cell["verdict"]
    cls = "na" if v == "n/a" else v
    title = cell.get("label") or cell.get("reason") or cell.get("error") or WORD[v]
    if cell.get("review"):
        title = f"Human review: {WORD[v]} (machine said {cell.get('machine_verdict')}). " + (cell["review"].get("note") or "")
    mark = ICON[v] + ("*" if cell.get("review") else "")
    inner = f'<span class="v {cls}" title="{e(title)}">{mark}</span>'
    return f'<a href="{href}" style="text-decoration:none">{inner}</a>' if href else inner


def legend() -> str:
    items = [("pass", "matches the correct rendering"), ("partial", "correct shaping, wrong base direction"),
             ("fail", "matches a known failure pattern"), ("mismatch", "matches nothing known: broken or unusual, needs review"),
             ("error", "the library crashed"), ("n/a", "the library has no API for this case")]
    return '<p class="legend small">' + "".join(
        f'<span>{badge({"verdict": v})} {e(t)}</span>' for v, t in items) + "</p>"


def render_index(matrix: dict) -> str:
    s = stats(matrix)
    fixtures = matrix["fixtures"]
    head = "".join(f'<th title="{e(f["title"])}">{e(f["id"])}</th>' for f in fixtures)
    rows_html = []
    for r in matrix["rows"]:
        cells = "".join(f'<td class="c">{badge(r["cells"][f["id"]], f"lib/{r["id"]}.html#{f["id"]}")}</td>' for f in fixtures)
        rows_html.append(
            f'<tr><td><a href="lib/{e(r["id"])}.html"><b>{e(r["library"])}</b></a><br>'
            f'<span class="muted small">{e(r["version"])}</span></td>'
            f'<td><span class="tag">{e(CATEGORY.get(r["category"], r["category"]))}</span> '
            f'<span class="tag">{e(r["ecosystem"])}</span> <span class="tag">{e(r["mode"])}</span></td>'
            f'{cells}<td class="c">{badge({"verdict": r["summary"]})}<br><span class="small muted">{r["passed"]}/{r["judged"]}</span></td></tr>')
    inv = next(f for f in fixtures if f["id"] == "invoice-line")
    strip = ['<div class="strip">',
             f'<div class="lib">Correct (Chromium reference)</div><a href="img/reference/invoice-line__ok.png"><img src="img/crop/reference/invoice-line__ok.png" alt="reference rendering"></a><div>{badge({"verdict": "pass"})}</div>']
    for r in matrix["rows"]:
        c = r["cells"]["invoice-line"]
        img = f'<a href="img/{e(c["shot"])}"><img loading="lazy" src="img/crop/{e(c["shot"])}" alt="{e(r["library"])} output"></a>' if c.get("shot") else f'<div class="muted small">{e(c.get("reason") or c.get("error") or "")}</div>'
        strip.append(f'<div class="lib"><a href="lib/{e(r["id"])}.html">{e(r["library"])}</a></div>{img}'
                     f'<div>{badge(c)} <span class="small muted">{e(c.get("variant") or "")}</span></div>')
    strip.append("</div>")
    reviewed = (f'{s["reviewed"]} of {s["cells"]} cells have a human review.' if s["reviewed"]
                else "No cell has been reviewed by a native speaker yet.")
    body = f"""
<h1>Does It Arabic?</h1>
<p class="muted">Which PDF, OG-image and chart libraries render Arabic, Persian and Hebrew correctly — screenshots, not opinions.</p>
<p style="font-size:19px"><b>Same Arabic invoice line, {s["invoice_judged"]} library configurations, {s["invoice_broken"]} broke it.</b>
{s["all_pass"]} of {s["rows"]} configurations pass all fixtures.</p>
<div class="notice small"><b>Automatic verdicts.</b> Every cell is a real screenshot of the library's output, judged by
comparing it with a Chromium/HarfBuzz reference and with known failure patterns (<a href="method.html">method</a>).
{reviewed} Run on {e(matrix["generatedAt"][:10])} with font {e(matrix["font"])} and reference {e(matrix["reference"]["renderer"])} {e(matrix["reference"]["version"])}.</div>
<h2>The invoice line</h2>
<p><span class="rtl" lang="ar" dir="rtl">{e(inv["text"])}</span> <span class="muted">— {e(inv["meaning"])}</span></p>
{"".join(strip)}
<h2>All fixtures</h2>
{legend()}
<div style="overflow-x:auto"><table class="grid"><tr><th>Library</th><th>Kind</th>{head}<th>Overall</th></tr>
{"".join(rows_html)}</table></div>
<p class="small muted">For coding agents: <a href="llms.txt">llms.txt</a>, <a href="matrix.json">matrix.json</a> and an installable
<a href="skill/SKILL.md">skill file</a>. Fixtures: <a href="fixtures.html">arabic-fixtures</a>.</p>
"""
    return page("Does It Arabic? — RTL rendering test matrix", body)


def render_library(matrix: dict, row: dict, adapter_source: str) -> str:
    fixtures = matrix["fixtures"]
    sections = []
    for f in fixtures:
        c = row["cells"][f["id"]]
        if c.get("shot"):
            got = (f'<a href="../img/{e(c["shot"])}" title="full screenshot"><img loading="lazy" src="../img/crop/{e(c["shot"])}" '
                   f'alt="{e(row["library"])} output"></a>')
        else:
            got = f'<pre>{e(c.get("reason") or c.get("error") or "")}</pre>'
        detail = e(c.get("label") or WORD[c["verdict"]])
        if c["verdict"] == "mismatch" and c.get("nearest"):
            detail += f' <span class="muted">(closest known pattern: {e(c["nearest"])})</span>'
        advice = f'<p class="small"><b>Usual fix:</b> {e(c["advice"])}</p>' if c.get("advice") else ""
        review = ""
        if c.get("review"):
            rv = c["review"]
            review = (f'<p class="small"><b>Human review</b> by {e(rv.get("reviewer"))} on {e(rv.get("date"))}: '
                      f'{e(WORD[c["verdict"]])} (machine verdict: {e(c.get("machine_verdict"))}). {e(rv.get("note") or "")}</p>')
        dist = ""
        if c.get("distances"):
            dist = '<p class="small muted">Distances: ' + ", ".join(f"{k} {v:.3f}" for k, v in c["distances"].items()) + "</p>"
        sections.append(f"""<div class="fixture{' wrap' if f.get('wrap') else ''}" id="{e(f["id"])}">
<h3>{badge(c)} {e(f["title"])}</h3>
<p><span class="rtl" lang="{e(f["lang"])}" dir="{e(f["dir"])}">{e(f["text"])}</span> <span class="muted small">— {e(f["meaning"])}</span></p>
<div class="pair"><div><div class="small muted">Correct (Chromium)</div><a href="../img/reference/{e(f["id"])}__ok.png"><img loading="lazy" src="../img/crop/reference/{e(f["id"])}__ok.png" alt="reference"></a></div>
<div><div class="small muted">{e(row["library"])}</div>{got}</div></div>
<p><b>{e(WORD[c["verdict"]])}:</b> {detail}</p>{advice}{review}{dist}</div>""")

    alt = alternatives(matrix, row)
    rel = related(matrix, row)
    extra = ""
    if rel:
        extra += "<h2>Other tested configurations of this library</h2><ul>" + "".join(
            f'<li><a href="{e(r["id"])}.html">{e(r["library"])}</a> ({e(r["mode"])}): {badge({"verdict": r["summary"]})} '
            f'{r["passed"]}/{r["judged"]} fixtures pass</li>' for r in rel) + "</ul>"
    if row["summary"] != "pass" and alt:
        extra += "<h2>Use instead</h2><p class=\"small muted\">Configurations in this matrix that pass every fixture.</p><ul>" + "".join(
            f'<li><a href="{e(r["id"])}.html">{e(r["library"])}</a> <span class="tag">{e(r["ecosystem"])}</span> '
            f'<span class="tag">{e(CATEGORY.get(r["category"], r["category"]))}</span></li>' for r in alt) + "</ul>"
    body = f"""
<h1>{e(row["library"])}</h1>
<p>{badge({"verdict": row["summary"]})} <b>{row["passed"]}/{row["judged"]}</b> fixtures pass · version {e(row["version"])} ·
<span class="tag">{e(CATEGORY.get(row["category"], row["category"]))}</span> <span class="tag">{e(row["ecosystem"])}</span>
<span class="tag" title="{e(matrix["modes"].get(row["mode"], ""))}">{e(row["mode"])}</span></p>
<p class="small muted">{e(matrix["modes"].get(row["mode"], ""))} Verdicts are automatic unless marked as reviewed.</p>
{"".join(sections)}
{extra}
<h2>The exact code that produced these screenshots</h2>
<p class="small muted"><code>{e(row["adapter"])}</code></p>
<pre>{e(adapter_source)}</pre>
"""
    return page(f"{row['library']} — Does It Arabic?", body, depth=1)


def render_fixtures(matrix: dict) -> str:
    rows = "".join(
        f'<tr><td><b>{e(f["id"])}</b><br><span class="small muted">{e(f["title"])}</span></td>'
        f'<td><span class="rtl" lang="{e(f["lang"])}" dir="{e(f["dir"])}">{e(f["text"])}</span><br><span class="small muted">{e(f["meaning"])}</span></td>'
        f'<td class="small">{e(f["checks"])}</td><td><img loading="lazy" style="max-width:260px" src="img/reference/{e(f["id"])}__ok.png" alt=""></td></tr>'
        for f in matrix["fixtures"])
    body = f"""<h1>Fixtures</h1>
<p>Eight RTL test strings, available as the <code>arabic-fixtures</code> package (JSON with a JS and a Python loader,
CC0). Rendered with {e(matrix["font"])} at the same size by every library.</p>
<table><tr><th>Fixture</th><th>Text</th><th>What correct looks like</th><th>Reference</th></tr>{rows}</table>"""
    return page("Fixtures — Does It Arabic?", body)


def render_method(matrix: dict) -> str:
    variants = "".join(f'<tr><td><b>{e(k)}</b></td><td>{badge({"verdict": v["verdict"]})}</td><td>{e(v["label"])}</td>'
                       f'<td class="small">{e(v["advice"])}</td></tr>' for k, v in matrix["variants"].items())
    j = matrix["judging"]
    body = f"""<h1>How it is judged</h1>
<ol>
<li>Each adapter renders the eight fixtures with one library, using that library's documented API and the same font
({e(matrix["font"])}). PDFs are rasterised with PDFium, which draws exactly the glyphs the library placed.</li>
<li>Chromium (HarfBuzz shaping, full Unicode Bidi Algorithm) renders the correct output <b>and</b> each known way of
getting it wrong, listed below. Those failure renders are made by the same engine, so the only difference is the bug.</li>
<li>Every screenshot is cropped to its ink, resampled to a common grid, blurred slightly and compared with each variant
(1 − cosine similarity plus an aspect-ratio penalty). For wrapped text the lines are re-stacked with equal spacing first,
so line height does not count but line order and alignment do.</li>
<li>The nearest variant within {j["matchThreshold"]} decides the verdict. Nothing that close → <b>mismatch</b>: the
output is neither correct nor a known pattern (for example misplaced harakat or scrambled words) and needs a human look.</li>
</ol>
<p>Variants closer than {j["sameThreshold"]} to the correct render (e.g. "unshaped" Hebrew) cannot tell anything apart and are ignored for that fixture.</p>
<table><tr><th>Variant</th><th>Verdict</th><th>What it looks like</th><th>Usual fix</th></tr>{variants}</table>
<h2>Limits</h2>
<ul><li>Verdicts are automatic. A native-speaker review can override a cell; reviewed cells are marked with *.</li>
<li>One font for everything, so font fallback problems are out of scope.</li>
<li>"mismatch" can, rarely, be a correct rendering that differs in detail (e.g. a different but valid mark position).</li></ul>"""
    return page("Method — Does It Arabic?", body)


# ---------------------------------------------------------------- agent files

def render_llms_txt(matrix: dict) -> str:
    s = stats(matrix)
    lines = [
        "# Does It Arabic?",
        "",
        "> Screenshot-backed test matrix of which PDF, OG-image and chart libraries render Arabic, Persian and Hebrew "
        "correctly. Verdicts are automatic comparisons with a Chromium/HarfBuzz reference "
        f"(run {matrix['generatedAt'][:10]}, font {matrix['font']}).",
        "",
        f"Same Arabic invoice line, {s['invoice_judged']} configurations, {s['invoice_broken']} broke it. "
        f"{s['all_pass']} of {s['rows']} pass every fixture.",
        "",
        "## Results",
        "",
    ]
    for r in matrix["rows"]:
        bad = failing_fixtures(r, matrix["fixtures"])
        tail = f" — fails: {', '.join(bad)}" if bad else ""
        lines.append(f"- [{r['library']}](lib/{r['id']}.html) ({r['ecosystem']}, {r['category']}, {r['mode']}, "
                     f"{r['version']}): {r['summary'].upper()} {r['passed']}/{r['judged']}{tail}")
    lines += ["", "## Files", "",
              "- [matrix.json](matrix.json): every cell with verdict, diagnosis and screenshot path",
              "- [Agent skill](skill/SKILL.md): rules for coding agents generating RTL documents",
              "- [Fixtures](fixtures.html): the eight test strings",
              "- [Method](method.html): how verdicts are computed", ""]
    return "\n".join(lines)


def render_skill(matrix: dict) -> str:
    passing = [r for r in matrix["rows"] if r["summary"] == "pass"]
    avoid = [r for r in matrix["rows"] if r["summary"] == "fail"]
    partial = [r for r in matrix["rows"] if r["summary"] == "partial"]

    def item(r):
        bad = failing_fixtures(r, matrix["fixtures"])
        return (f"- **{r['library']}** ({r['ecosystem']}, {r['category']}, {r['version']}): "
                f"{r['passed']}/{r['judged']} pass" + (f"; broken: {', '.join(bad)}" if bad else ""))

    return "\n".join([
        "---",
        "name: does-it-arabic",
        "description: Use when generating PDFs, invoices, receipts, certificates, OG/social images or charts that contain "
        "Arabic, Persian, Urdu or Hebrew text, or when choosing a library for that. Gives tested library verdicts so the "
        "output does not ship with disconnected letters, reversed words or misplaced numbers.",
        "---",
        "",
        "# Does It Arabic? — RTL output rules",
        "",
        f"Tested {matrix['generatedAt'][:10]} by rendering the same RTL fixtures with each library and comparing the "
        "screenshots with a Chromium/HarfBuzz reference. Verdicts are automatic; see matrix.json for every cell.",
        "",
        "## Before you write code",
        "",
        "1. Pick a library configuration from **Works** below. Do not default to one from **Avoid**.",
        "2. Embed a font that covers every script in the text (Arabic *and* Latin digits/letters), e.g. DejaVu Sans or "
        "Noto Sans Arabic + a Latin font with fallback. Many Arabic fonts contain no Latin glyphs.",
        "3. Set the paragraph/base direction to RTL where the API allows it (`dir=\"rtl\"`, `direction: 'rtl'`, "
        "`ctx.direction = 'rtl'`, `set_text_shaping(True, direction=\"rtl\")`).",
        "4. Do not reverse strings yourself, and do not pre-shape text for a library that already shapes it.",
        "5. Keep harakat: `arabic_reshaper` removes them by default.",
        *[f"6. Measured here: {w}" for w in worse_workarounds(matrix)][:1],
        *[f"   {w}" for w in worse_workarounds(matrix)][1:],
        "",
        "## Works (passes every fixture)",
        "",
        *[item(r) for r in passing],
        "",
        "## Partly works",
        "",
        *[item(r) for r in partial],
        "",
        "## Avoid for RTL text",
        "",
        *[item(r) for r in avoid],
        "",
        "## Check your output",
        "",
        "Render the fixture text with your code, then judge the PDF or PNG:",
        "",
        "```",
        "python -m doesitarabic check invoice.pdf --fixture invoice-line",
        "```",
        "",
        "Exit code 0 means it matches the correct rendering. Fixture texts are in "
        "`packages/arabic-fixtures/fixtures.json` (the invoice line is `Order #1234 للعميل محمد – 250 TND`).",
        "",
    ])


# ---------------------------------------------------------------- build

CROP_PAD = 24


def crop_for_display(src: Path, dest: Path, pad: int = CROP_PAD) -> None:
    """Copy of a screenshot cropped to its text (plus padding) so every image shows the text at one scale.
    The full, uncropped screenshot is published next to it and linked."""
    from PIL import Image

    from .compare import INK_THRESHOLD, ink_from_image

    dest.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(src) as img:
        img = img.convert("RGB")
        mask = ink_from_image(img) > INK_THRESHOLD
        if mask.any():
            rows, cols = mask.any(axis=1).nonzero()[0], mask.any(axis=0).nonzero()[0]
            box = (max(0, cols[0] - pad), max(0, rows[0] - pad), min(img.width, cols[-1] + pad + 1),
                   min(img.height, rows[-1] + pad + 1))
            img = img.crop(box)
        img.save(dest)


def site_matrix(matrix: dict) -> dict:
    """matrix.json as published: screenshot paths relative to the site root."""
    m = json.loads(json.dumps(matrix))
    for r in m["rows"]:
        for c in r["cells"].values():
            if c.get("shot"):
                c["shot"] = "img/" + c["shot"]
    m["referenceImages"] = {f["id"]: f"img/reference/{f['id']}__ok.png" for f in m["fixtures"]}
    return m


def build_site(results: Path = RESULTS, out: Path = DIST, skill_dir: Path | None = ROOT / "skill" / "does-it-arabic") -> dict:
    matrix = load_matrix(results)
    if out.exists():
        shutil.rmtree(out)
    (out / "lib").mkdir(parents=True)
    (out / "skill").mkdir()
    shutil.copytree(results / "shots", out / "img" / "shots")
    for shot in (results / "shots").rglob("*.png"):
        crop_for_display(shot, out / "img" / "crop" / shot.relative_to(results))
    (out / "img" / "reference").mkdir(parents=True)
    for f in matrix["fixtures"]:
        ref = results / "reference" / f"{f['id']}__ok.png"
        shutil.copy(ref, out / "img" / "reference")
        crop_for_display(ref, out / "img" / "crop" / "reference" / ref.name)

    def write(rel: str, text: str) -> None:
        (out / rel).write_text(text, encoding="utf-8")

    write("style.css", CSS)
    write("index.html", render_index(matrix))
    write("fixtures.html", render_fixtures(matrix))
    write("method.html", render_method(matrix))
    for r in matrix["rows"]:
        src_path = ROOT / r["adapter"].split()[0]
        source = src_path.read_text(encoding="utf-8") if src_path.exists() else "(adapter source not found)"
        write(f"lib/{r['id']}.html", render_library(matrix, r, source))
    write("matrix.json", json.dumps(site_matrix(matrix), ensure_ascii=False, indent=2))
    write("llms.txt", render_llms_txt(matrix))
    skill = render_skill(matrix)
    write("skill/SKILL.md", skill)
    if skill_dir is not None:
        skill_dir.mkdir(parents=True, exist_ok=True)
        (skill_dir / "SKILL.md").write_text(skill, encoding="utf-8")
    return {"pages": 3 + len(matrix["rows"]), "out": str(out)}
