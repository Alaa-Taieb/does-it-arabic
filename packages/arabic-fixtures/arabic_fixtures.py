"""arabic-fixtures: RTL test strings for Arabic, Persian and Hebrew document rendering."""

import json
from pathlib import Path

_DATA = json.loads((Path(__file__).with_name("fixtures.json")).read_text(encoding="utf-8"))

fixtures = _DATA["fixtures"]
font_size = _DATA["fontSize"]
wrap_width = _DATA["wrapWidth"]
version = _DATA["version"]


def ids():
    """Fixture ids in canonical order."""
    return [f["id"] for f in fixtures]


def get(fixture_id):
    """One fixture by id; raises KeyError on an unknown id."""
    for f in fixtures:
        if f["id"] == fixture_id:
            return f
    raise KeyError(f"unknown fixture {fixture_id!r}; known: {', '.join(ids())}")
