import importlib.util
import os
import subprocess
import sys

import pytest

from conftest import DATA
from doesitarabic.paths import ROOT

spec = importlib.util.spec_from_file_location("action_run", ROOT / "action" / "run.py")
action_run = importlib.util.module_from_spec(spec)
spec.loader.exec_module(action_run)


def test_action_yml_inputs_match_the_runner():
    yaml = pytest.importorskip("yaml")
    action = yaml.safe_load((ROOT / "action.yml").read_text(encoding="utf-8"))
    assert action["runs"]["using"] == "composite"
    assert set(action["inputs"]) == {"checks", "endpoint", "fixtures", "font", "allow-partial"}
    env = action["runs"]["steps"][-1]["env"]
    for name in action["inputs"]:
        assert f"INPUT_{name.upper().replace('-', '_')}" in env
    assert "action/run.py" in action["runs"]["steps"][-1]["run"]


def test_build_args_for_files_and_endpoint():
    assert action_run.build_args({"INPUT_CHECKS": "invoice-line a.pdf", "INPUT_ALLOW_PARTIAL": "true",
                                  "GITHUB_STEP_SUMMARY": "s.md"}) == [
        "check", "--spec", "invoice-line a.pdf", "--allow-partial", "--summary", "s.md"]
    assert action_run.build_args({"INPUT_ENDPOINT": "http://x/r", "INPUT_FIXTURES": "connected hebrew",
                                  "INPUT_FONT": "f.ttf"}) == [
        "check", "--endpoint", "http://x/r", "--fixture", "connected", "--fixture", "hebrew", "--font", "f.ttf"]


@pytest.mark.parametrize("env", [{}, {"INPUT_CHECKS": "a b", "INPUT_ENDPOINT": "http://x"}])
def test_build_args_requires_exactly_one_source(env):
    with pytest.raises(SystemExit):
        action_run.build_args(env)


def _run_action(checks, tmp_path):
    summary = tmp_path / "summary.md"
    env = {**os.environ, "INPUT_CHECKS": checks, "GITHUB_STEP_SUMMARY": str(summary), "PYTHONPATH": str(ROOT)}
    proc = subprocess.run([sys.executable, str(ROOT / "action" / "run.py")], env=env, cwd=tmp_path,
                          capture_output=True, text=True, encoding="utf-8")
    return proc, summary.read_text(encoding="utf-8")


def test_action_passes_good_output(tmp_path):
    proc, summary = _run_action(f"invoice-line {DATA / 'out' / 'pillow-invoice-line.png'}", tmp_path)
    assert proc.returncode == 0, proc.stderr
    assert "**1/1 passed.**" in summary


def test_action_fails_broken_output(tmp_path):
    proc, summary = _run_action(f"invoice-line {DATA / 'out' / 'fpdf2-invoice-line.pdf'}", tmp_path)
    assert proc.returncode == 1
    assert "❌ fail" in summary
