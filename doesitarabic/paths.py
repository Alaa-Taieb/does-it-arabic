"""Repository locations."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "packages" / "arabic-fixtures" / "fixtures.json"
FONT = ROOT / "fonts" / "DejaVuSans.ttf"
RESULTS = ROOT / "results"
REFERENCE_DIR = RESULTS / "reference"
REGISTRY = ROOT / "adapters" / "registry.json"
DIST = ROOT / "dist"
