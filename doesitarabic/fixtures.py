"""Load the fixture set."""

from __future__ import annotations

import json
from pathlib import Path

from .paths import FIXTURES


def load_fixtures(path: str | Path = FIXTURES) -> dict:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    ids = [f["id"] for f in data["fixtures"]]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate fixture ids")
    for f in data["fixtures"]:
        for key in ("id", "title", "text", "dir", "lang"):
            if not f.get(key):
                raise ValueError(f"fixture {f.get('id')!r} is missing {key!r}")
        if f["dir"] not in ("rtl", "ltr"):
            raise ValueError(f"fixture {f['id']!r} has invalid dir {f['dir']!r}")
    return data


def fixture_by_id(data: dict, fixture_id: str) -> dict:
    for f in data["fixtures"]:
        if f["id"] == fixture_id:
            return f
    raise KeyError(f"unknown fixture {fixture_id!r}; known: {', '.join(f['id'] for f in data['fixtures'])}")
