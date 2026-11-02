import json
import subprocess
import sys

import pytest

from doesitarabic.fixtures import fixture_by_id, load_fixtures
from doesitarabic.paths import ROOT


def test_fixture_set_has_the_eight_brief_cases():
    data = load_fixtures()
    assert [f["id"] for f in data["fixtures"]] == [
        "connected", "lam-alef", "harakat", "invoice-line", "digits", "persian", "hebrew", "wrapping",
    ]
    assert fixture_by_id(data, "invoice-line")["text"] == "Order #1234 للعميل محمد – 250 TND"


def test_unknown_fixture_raises():
    with pytest.raises(KeyError):
        fixture_by_id(load_fixtures(), "nope")


def test_invalid_fixture_file_is_rejected(tmp_path):
    p = tmp_path / "f.json"
    p.write_text(json.dumps({"fixtures": [{"id": "a", "title": "t", "text": "x", "dir": "up", "lang": "ar"}]}))
    with pytest.raises(ValueError):
        load_fixtures(p)


def test_js_loader_reads_the_same_fixtures():
    out = subprocess.run(
        ["node", "-e", "const f=require('./packages/arabic-fixtures'); console.log(JSON.stringify(f.ids()))"],
        cwd=ROOT, capture_output=True, text=True, check=True,
    )
    assert json.loads(out.stdout) == [f["id"] for f in load_fixtures()["fixtures"]]


def test_python_loader_reads_the_same_fixtures():
    code = "import arabic_fixtures as a; print(a.get('hebrew')['lang'])"
    out = subprocess.run([sys.executable, "-c", code], cwd=ROOT / "packages" / "arabic-fixtures",
                         capture_output=True, text=True, check=True)
    assert out.stdout.strip() == "he"
