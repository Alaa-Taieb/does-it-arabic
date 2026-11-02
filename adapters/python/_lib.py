"""Shared adapter plumbing (Python twin of adapters/node/_lib.mjs)."""

from __future__ import annotations

import json
import sys
import traceback
from importlib import metadata
from pathlib import Path


def pkg_version(name: str) -> str:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return "unknown"


def read_config() -> dict:
    if len(sys.argv) < 3:
        print("usage: <adapter> <config.json> <outdir>", file=sys.stderr)
        sys.exit(2)
    config = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    out = Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    config["outDir"] = out
    return config


def geometry(config: dict, fixture: dict) -> dict:
    pad = 20
    if fixture.get("wrap"):
        return {"width": config["wrapWidth"] + 2 * pad, "height": 360, "pad": pad}
    return {"width": 1000, "height": 90, "pad": pad}


class Skip(Exception):
    """Raised by a render function when the library has no API for a fixture."""


def run_fixtures(config: dict, version: str, render) -> None:
    """render(fixture, path_without_ext) -> extension written ('pdf' or 'png')."""
    outputs, errors, skipped = {}, {}, {}
    for fixture in config["fixtures"]:
        stem = config["outDir"] / fixture["id"]
        try:
            ext = render(fixture, stem)
            outputs[fixture["id"]] = str(stem.with_suffix("." + ext))
        except Skip as s:
            skipped[fixture["id"]] = str(s)
        except Exception:  # noqa: BLE001 - every library failure is a result, not a crash
            errors[fixture["id"]] = " | ".join(traceback.format_exc().strip().splitlines()[-3:])
    print(json.dumps({"version": version, "outputs": outputs, "errors": errors, "skipped": skipped}))
