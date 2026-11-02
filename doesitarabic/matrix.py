"""Run every adapter, screenshot its output, judge each cell and write results/matrix.json."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from .classify import MATCH_THRESHOLD, SAME_THRESHOLD, classify, discriminating_variants, summarize
from .compare import load_ink
from .fixtures import load_fixtures
from .paths import FONT, REGISTRY, RESULTS, ROOT
from .raster import rasterize
from .reference import SCALE, load_references, render_references
from .variants import VARIANTS

ADAPTER_TIMEOUT = 600


def load_registry(path: Path = REGISTRY) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    ids = [r["id"] for r in data["rows"]]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate adapter ids in registry")
    for r in data["rows"]:
        if r["mode"] not in data["modes"]:
            raise ValueError(f"adapter {r['id']!r} has unknown mode {r['mode']!r}")
    return data


def adapter_command(row: dict, config_path: Path, out_dir: Path) -> list[str]:
    cmd = list(row["command"])
    if cmd[0] == "python":
        cmd[0] = sys.executable
    return cmd[:2] + [str(config_path), str(out_dir)] + cmd[2:]


def run_adapter(row: dict, config_path: Path, out_dir: Path) -> dict:
    """Run one adapter; returns its JSON report, or a crash report covering every fixture."""
    try:
        proc = subprocess.run(adapter_command(row, config_path, out_dir), cwd=ROOT, capture_output=True,
                              text=True, encoding="utf-8", timeout=ADAPTER_TIMEOUT)
    except subprocess.TimeoutExpired:
        return {"crash": f"adapter timed out after {ADAPTER_TIMEOUT}s"}
    lines = [ln for ln in proc.stdout.strip().splitlines() if ln.startswith("{")]
    if proc.returncode != 0 or not lines:
        tail = (proc.stderr or proc.stdout).strip().splitlines()[-5:]
        return {"crash": " | ".join(tail) or f"exit code {proc.returncode}"}
    return json.loads(lines[-1])


def judge_row(row: dict, report: dict, fixtures: list[dict], refs: dict, usable: dict, shots_dir: Path) -> dict:
    cells = {}
    for f in fixtures:
        fid = f["id"]
        if "crash" in report:
            cells[fid] = {"verdict": "error", "error": report["crash"]}
        elif fid in report.get("skipped", {}):
            cells[fid] = {"verdict": "n/a", "reason": report["skipped"][fid]}
        elif fid in report.get("errors", {}):
            cells[fid] = {"verdict": "error", "error": report["errors"][fid]}
        elif fid in report.get("outputs", {}):
            shot = rasterize(report["outputs"][fid], shots_dir / row["id"] / f"{fid}.png")
            cell = classify(load_ink(shot, multiline=bool(f.get("wrap"))), refs[fid], usable[fid]).to_dict()
            cell["shot"] = shot.relative_to(shots_dir.parent).as_posix()
            cell["source"] = Path(report["outputs"][fid]).suffix.lstrip(".")
            cells[fid] = cell
        else:
            cells[fid] = {"verdict": "error", "error": "adapter produced no output for this fixture"}
    verdicts = [c["verdict"] for c in cells.values()]
    judged = [v for v in verdicts if v != "n/a"]
    return {
        **{k: row[k] for k in ("id", "library", "package", "ecosystem", "category", "mode")},
        "adapter": " ".join(row["command"][1:]),
        "version": report.get("version", "unknown"),
        "summary": summarize(verdicts),
        "passed": sum(v == "pass" for v in judged),
        "judged": len(judged),
        "cells": cells,
    }


def apply_reviews(matrix: dict, reviews: list[dict]) -> dict:
    """Attach human reviews to cells. A review overrides the machine verdict and is shown as such."""
    rows = {r["id"]: r for r in matrix["rows"]}
    for rv in reviews:
        cell = rows.get(rv["row"], {}).get("cells", {}).get(rv["fixture"])
        if cell is None:
            raise ValueError(f"review for unknown cell {rv['row']}/{rv['fixture']}")
        if rv["verdict"] not in ("pass", "partial", "fail"):
            raise ValueError(f"invalid review verdict {rv['verdict']!r}")
        cell["machine_verdict"] = cell["verdict"]
        cell["verdict"] = rv["verdict"]
        cell["review"] = {k: rv.get(k) for k in ("reviewer", "date", "note")}
    for row in matrix["rows"]:
        verdicts = [c["verdict"] for c in row["cells"].values()]
        row["summary"] = summarize(verdicts)
        row["passed"] = sum(v == "pass" for v in verdicts)
    return matrix


def load_reviews(path: Path) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else []


def run_matrix(only: list[str] | None = None, results: Path = RESULTS, rerender_reference: bool = True,
               log=print) -> dict:
    fixtures_data = load_fixtures()
    fixtures = fixtures_data["fixtures"]
    ref_dir = results / "reference"
    if rerender_reference or not (ref_dir / "reference.json").exists():
        log("rendering Chromium reference and failure variants ...")
        ref_meta = render_references(fixtures_data, ref_dir)
    else:
        ref_meta = json.loads((ref_dir / "reference.json").read_text(encoding="utf-8"))
    refs = {f["id"]: load_references(f, ref_dir) for f in fixtures}
    usable = {fid: discriminating_variants(r) for fid, r in refs.items()}

    registry = load_registry()
    rows = [r for r in registry["rows"] if not only or r["id"] in only]
    if only and len(rows) != len(set(only)):
        known = {r["id"] for r in registry["rows"]}
        raise KeyError(f"unknown adapter(s): {', '.join(sorted(set(only) - known))}")

    previous = {}
    matrix_path = results / "matrix.json"
    if only and matrix_path.exists():
        previous = {r["id"]: r for r in json.loads(matrix_path.read_text(encoding="utf-8"))["rows"]}

    judged_rows = {}
    with tempfile.TemporaryDirectory() as tmp:
        config_path = Path(tmp) / "config.json"
        config = {"fixtures": fixtures, "fontPath": str(FONT), "fontSize": fixtures_data["fontSize"],
                  "wrapWidth": fixtures_data["wrapWidth"], "scale": SCALE}
        config_path.write_text(json.dumps(config, ensure_ascii=False), encoding="utf-8")
        for row in rows:
            log(f"running {row['id']} ...")
            report = run_adapter(row, config_path, Path(tmp) / "out" / row["id"])
            judged_rows[row["id"]] = judge_row(row, report, fixtures, refs, usable, results / "shots")
            r = judged_rows[row["id"]]
            log(f"  {r['summary']:8s} {r['passed']}/{r['judged']} passed  ({r['version']})")

    ordered = []
    for r in registry["rows"]:
        if r["id"] in judged_rows:
            ordered.append(judged_rows[r["id"]])
        elif r["id"] in previous:
            ordered.append(previous[r["id"]])

    matrix = {
        "schema": 1,
        "generatedAt": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "reference": ref_meta,
        "font": fixtures_data["font"],
        "judging": {"matchThreshold": MATCH_THRESHOLD, "sameThreshold": SAME_THRESHOLD, "method": "automatic"},
        "fixtures": fixtures,
        "variants": {k: {"verdict": v.verdict, "label": v.label, "advice": v.advice} for k, v in VARIANTS.items()},
        "modes": registry["modes"],
        "rows": ordered,
    }
    apply_reviews(matrix, load_reviews(results / "reviews.json"))
    results.mkdir(parents=True, exist_ok=True)
    matrix_path.write_text(json.dumps(matrix, ensure_ascii=False, indent=2), encoding="utf-8")
    append_history(matrix, [judged_rows[k] for k in judged_rows], results / "history.jsonl")
    return matrix


def append_history(matrix: dict, rows: list[dict], path: Path) -> None:
    """One line per adapter run: the dated record of when a library version passed or broke."""
    with path.open("a", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps({"date": matrix["generatedAt"], "row": r["id"], "version": r["version"],
                                 "summary": r["summary"], "passed": r["passed"], "judged": r["judged"],
                                 "verdicts": {k: c["verdict"] for k, c in r["cells"].items()}},
                                ensure_ascii=False) + "\n")

