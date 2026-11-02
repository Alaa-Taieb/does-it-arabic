"""Render the Chromium reference and failure variants for every fixture."""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path

from .compare import Ink, load_ink
from .paths import FONT, REFERENCE_DIR, ROOT
from .variants import variant_jobs

SCALE = 2


def node_bin() -> str:
    node = shutil.which("node")
    if not node:
        raise RuntimeError("Node.js is required to render the Chromium reference (node not found on PATH)")
    return node


def render_references(fixtures: dict, out_dir: Path = REFERENCE_DIR, font: Path = FONT) -> dict:
    """Render all variants with Chromium into out_dir; returns {'renderer', 'version'}."""
    jobs = [j for f in fixtures["fixtures"] for j in variant_jobs(f)]
    payload = {"fontSize": fixtures["fontSize"], "wrapWidth": fixtures["wrapWidth"], "scale": SCALE, "jobs": jobs}
    out_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        jobs_path = Path(tmp) / "jobs.json"
        jobs_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        proc = subprocess.run(
            [node_bin(), str(ROOT / "reference" / "render-chromium.mjs"), str(jobs_path), str(font), str(out_dir)],
            capture_output=True, text=True, encoding="utf-8", cwd=ROOT,
        )
    if proc.returncode != 0:
        raise RuntimeError(f"reference renderer failed:\n{proc.stderr.strip()}")
    info = json.loads(proc.stdout.strip().splitlines()[-1])
    meta = {"renderer": info["renderer"], "version": info["version"]}
    (out_dir / "reference.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return meta


def reference_path(fixture_id: str, variant: str, ref_dir: Path = REFERENCE_DIR) -> Path:
    return ref_dir / f"{fixture_id}__{variant}.png"


def load_references(fixture: dict, ref_dir: Path = REFERENCE_DIR) -> dict[str, Ink | None]:
    refs = {}
    for job in variant_jobs(fixture):
        p = reference_path(fixture["id"], job["variant"], ref_dir)
        if not p.exists():
            raise FileNotFoundError(f"missing reference {p}; run `python -m doesitarabic references` first")
        refs[job["variant"]] = load_ink(p, multiline=bool(fixture.get("wrap")))
    return refs
