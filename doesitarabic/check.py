"""Judge your own rendering pipeline: a PDF/PNG file, or an HTTP endpoint that returns one.

Contract: the file (first page) must contain only the fixture text, black on white, in one block.
References are rendered in *your* font (``--font``) so a different typeface does not count as a failure.
"""

from __future__ import annotations

import hashlib
import json
import tempfile
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from .classify import classify, discriminating_variants
from .compare import load_ink
from .fixtures import fixture_by_id, load_fixtures
from .paths import FONT, REFERENCE_DIR, RESULTS
from .raster import rasterize
from .reference import load_references, render_references

CACHE = RESULTS / ".cache"


@dataclass
class CheckResult:
    fixture: str
    source: str
    verdict: str
    variant: str | None
    label: str
    advice: str
    distance: float | None

    def ok(self, allow_partial: bool = False) -> bool:
        return self.verdict == "pass" or (allow_partial and self.verdict == "partial")

    def to_dict(self) -> dict:
        return self.__dict__.copy()


def reference_dir_for(font: Path | None) -> Path:
    """Reference renders for a font: the committed ones for the default font, a cache otherwise."""
    fixtures = load_fixtures()
    if font is None or Path(font).resolve() == FONT.resolve():
        if not (REFERENCE_DIR / "reference.json").exists():
            render_references(fixtures, REFERENCE_DIR)
        return REFERENCE_DIR
    font = Path(font)
    if not font.exists():
        raise FileNotFoundError(f"font not found: {font}")
    digest = hashlib.sha256(font.read_bytes() + json.dumps(fixtures, sort_keys=True).encode()).hexdigest()[:16]
    out = CACHE / f"reference-{digest}"
    if not (out / "reference.json").exists():
        render_references(fixtures, out, font=font)
    return out


def sniff(data: bytes) -> str:
    if data[:5] == b"%PDF-":
        return "pdf"
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "png"
    if data[:3] == b"\xff\xd8\xff":
        return "jpg"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp"
    raise ValueError("not a PDF, PNG, JPEG or WebP file")


def judge_file(path: str | Path, fixture_id: str, ref_dir: Path) -> CheckResult:
    path = Path(path)
    fixture = fixture_by_id(load_fixtures(), fixture_id)
    kind = sniff(path.read_bytes()[:16])
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / f"input.{kind}"
        src.write_bytes(path.read_bytes())
        png = rasterize(src, Path(tmp) / "page.png")
        ink = load_ink(png, multiline=bool(fixture.get("wrap")))
    refs = load_references(fixture, ref_dir)
    j = classify(ink, refs, discriminating_variants(refs))
    return CheckResult(fixture_id, str(path), j.verdict, j.variant, j.label, j.advice, j.distance)


def fetch_endpoint(url: str, fixture: dict, method: str = "POST", timeout: float = 60) -> bytes:
    """Ask the user's endpoint to render a fixture.

    GET: ``{text}``, ``{dir}``, ``{lang}`` and ``{id}`` in the URL are replaced (URL-encoded).
    POST: JSON body ``{"id", "text", "dir", "lang"}``.
    """
    fields = {k: fixture[k] for k in ("id", "text", "dir", "lang")}
    if method.upper() == "GET":
        for k, v in fields.items():
            url = url.replace("{" + k + "}", urllib.parse.quote(v))
        req = urllib.request.Request(url, method="GET")
    else:
        req = urllib.request.Request(url, data=json.dumps(fields, ensure_ascii=False).encode("utf-8"),
                                     headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def check_endpoint(url: str, fixture_ids: list[str], ref_dir: Path, method: str = "POST") -> list[CheckResult]:
    fixtures = load_fixtures()
    results = []
    with tempfile.TemporaryDirectory() as tmp:
        for fid in fixture_ids:
            fixture = fixture_by_id(fixtures, fid)
            try:
                data = fetch_endpoint(url, fixture, method)
                out = Path(tmp) / f"{fid}.{sniff(data[:16])}"
                out.write_bytes(data)
                r = judge_file(out, fid, ref_dir)
                r.source = url
            except Exception as exc:  # noqa: BLE001 - an endpoint failure is a failed check, not a crash
                r = CheckResult(fid, url, "error", None, f"endpoint failed: {exc}", "", None)
            results.append(r)
    return results


def parse_spec(spec: str) -> list[tuple[str, str]]:
    """Lines of ``<fixture-id> <path>``; blank lines and # comments ignored."""
    pairs = []
    known = {f["id"] for f in load_fixtures()["fixtures"]}
    for n, line in enumerate(spec.splitlines(), 1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(None, 1)
        if len(parts) != 2:
            raise ValueError(f"line {n}: expected '<fixture-id> <path>', got {line!r}")
        if parts[0] not in known:
            raise ValueError(f"line {n}: unknown fixture {parts[0]!r}")
        pairs.append((parts[0], parts[1].strip()))
    if not pairs:
        raise ValueError("no checks given")
    return pairs


def markdown_report(results: list[CheckResult], allow_partial: bool = False) -> str:
    icon = {"pass": "✅", "partial": "🟡", "fail": "❌", "mismatch": "❌", "error": "⚠️"}
    lines = ["## Does It Arabic? check", "", "| Fixture | Source | Verdict | What it looks like |", "|---|---|---|---|"]
    for r in results:
        lines.append(f"| `{r.fixture}` | `{r.source}` | {icon.get(r.verdict, '')} {r.verdict} | {r.label} |")
    failed = [r for r in results if not r.ok(allow_partial)]
    lines += ["", f"**{len(results) - len(failed)}/{len(results)} passed.**"]
    advice = sorted({r.advice for r in failed if r.advice})
    if advice:
        lines += ["", "Usual fixes:", *[f"- {a}" for a in advice]]
    return "\n".join(lines) + "\n"
