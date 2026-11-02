import json
import shutil
import sys
from pathlib import Path

import pytest

from conftest import DATA
from doesitarabic import matrix as mx
from doesitarabic.compare import load_ink
from doesitarabic.fixtures import load_fixtures
from doesitarabic.variants import VARIANTS


def test_registry_is_valid_and_points_at_existing_adapters():
    reg = mx.load_registry()
    assert len(reg["rows"]) >= 15
    for row in reg["rows"]:
        assert (mx.ROOT / row["command"][1]).exists(), row["id"]


def test_adapter_command_inserts_config_and_outdir_before_flags():
    row = {"command": ["python", "adapters/python/fpdf2_adapter.py", "--shaping"]}
    cmd = mx.adapter_command(row, Path("c.json"), Path("out"))
    assert cmd == [sys.executable, "adapters/python/fpdf2_adapter.py", "c.json", "out", "--shaping"]


ROW = {"id": "demo", "library": "Demo", "package": "demo", "ecosystem": "npm", "category": "pdf",
       "mode": "default", "command": ["node", "adapters/node/demo.mjs"]}


def _refs():
    fx = [f for f in load_fixtures()["fixtures"] if f["id"] in ("invoice-line", "connected")]
    refs = {f["id"]: {v: load_ink(DATA / "ref" / f"{f['id']}__{v}.png") for v in VARIANTS} for f in fx}
    usable = {k: mx.discriminating_variants(r) for k, r in refs.items()}
    return fx, refs, usable


def test_judge_row_records_outputs_skips_and_errors(tmp_path):
    fx, refs, usable = _refs()
    report = {"version": "1.0", "outputs": {"invoice-line": str(DATA / "out" / "pillow-invoice-line.png")},
              "errors": {"connected": "TypeError: boom"}, "skipped": {}}
    row = mx.judge_row(ROW, report, fx, refs, usable, tmp_path / "shots")
    assert row["cells"]["invoice-line"]["verdict"] == "pass"
    assert row["cells"]["invoice-line"]["shot"] == "shots/demo/invoice-line.png"
    assert (tmp_path / "shots" / "demo" / "invoice-line.png").exists()
    assert row["cells"]["connected"] == {"verdict": "error", "error": "TypeError: boom"}
    assert row["summary"] == "partial" and row["passed"] == 1 and row["judged"] == 2


def test_judge_row_crash_marks_every_cell_error(tmp_path):
    fx, refs, usable = _refs()
    row = mx.judge_row(ROW, {"crash": "Cannot find module"}, fx, refs, usable, tmp_path)
    assert {c["verdict"] for c in row["cells"].values()} == {"error"}
    assert row["summary"] == "fail"


def test_judge_row_skipped_is_not_applicable(tmp_path):
    fx, refs, usable = _refs()
    report = {"version": "1", "outputs": {"invoice-line": str(DATA / "out" / "pillow-invoice-line.png")},
              "errors": {}, "skipped": {"connected": "no API"}}
    row = mx.judge_row(ROW, report, fx, refs, usable, tmp_path)
    assert row["cells"]["connected"] == {"verdict": "n/a", "reason": "no API"}
    assert row["summary"] == "pass" and row["judged"] == 1


def _tiny_matrix():
    return {"rows": [{"id": "a", "cells": {"x": {"verdict": "mismatch"}, "y": {"verdict": "pass"}}}]}


def test_review_overrides_machine_verdict_visibly():
    m = mx.apply_reviews(_tiny_matrix(), [{"row": "a", "fixture": "x", "verdict": "pass", "reviewer": "native speaker",
                                           "date": "2026-11-02", "note": "marks differ but read correctly"}])
    cell = m["rows"][0]["cells"]["x"]
    assert cell["verdict"] == "pass" and cell["machine_verdict"] == "mismatch"
    assert cell["review"]["reviewer"] == "native speaker"
    assert m["rows"][0]["summary"] == "pass"


@pytest.mark.parametrize("bad", [{"row": "zz", "fixture": "x", "verdict": "pass"},
                                 {"row": "a", "fixture": "x", "verdict": "great"}])
def test_invalid_reviews_are_rejected(bad):
    with pytest.raises(ValueError):
        mx.apply_reviews(_tiny_matrix(), [bad])


def test_history_appends_one_line_per_row(tmp_path):
    rows = [{"id": "a", "version": "1", "summary": "pass", "passed": 1, "judged": 1, "cells": {"x": {"verdict": "pass"}}}]
    path = tmp_path / "h.jsonl"
    mx.append_history({"generatedAt": "2026-11-02T00:00:00+00:00"}, rows, path)
    mx.append_history({"generatedAt": "2026-11-09T00:00:00+00:00"}, rows, path)
    lines = [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines()]
    assert [x["date"][:10] for x in lines] == ["2026-11-02", "2026-11-09"]
    assert lines[0]["verdicts"] == {"x": "pass"}


@pytest.mark.skipif(shutil.which("node") is None, reason="needs Node.js and Chrome for the real end-to-end run")
def test_end_to_end_run_with_real_adapters(tmp_path):
    """Render the Chromium reference, run two real adapters, judge them, write matrix.json."""
    m = mx.run_matrix(only=["pillow", "fpdf2"], results=tmp_path, log=lambda *_: None)
    rows = {r["id"]: r for r in m["rows"]}
    assert rows["pillow"]["cells"]["invoice-line"]["verdict"] == "pass"
    assert rows["fpdf2"]["cells"]["invoice-line"]["variant"] == "naive"
    assert rows["pillow"]["cells"]["wrapping"]["verdict"] == "n/a"
    saved = json.loads((tmp_path / "matrix.json").read_text(encoding="utf-8"))
    assert saved["reference"]["renderer"] == "chromium" and saved["judging"]["method"] == "automatic"
    assert (tmp_path / "shots" / "fpdf2" / "invoice-line.png").exists()
    assert len((tmp_path / "history.jsonl").read_text(encoding="utf-8").splitlines()) == 2
