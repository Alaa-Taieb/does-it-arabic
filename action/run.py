"""Entry point of the GitHub Action: turns INPUT_* variables into a `doesitarabic check` call."""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from doesitarabic.cli import main  # noqa: E402


def build_args(env: dict) -> list[str]:
    checks = env.get("INPUT_CHECKS", "").strip()
    endpoint = env.get("INPUT_ENDPOINT", "").strip()
    if bool(checks) == bool(endpoint):
        raise SystemExit("set exactly one of the 'checks' or 'endpoint' inputs")
    args = ["check"]
    if checks:
        args += ["--spec", checks]
    else:
        args += ["--endpoint", endpoint]
        for fid in env.get("INPUT_FIXTURES", "").split():
            args += ["--fixture", fid]
    if env.get("INPUT_FONT", "").strip():
        args += ["--font", env["INPUT_FONT"].strip()]
    if env.get("INPUT_ALLOW_PARTIAL", "false").strip().lower() == "true":
        args.append("--allow-partial")
    if env.get("GITHUB_STEP_SUMMARY"):
        args += ["--summary", env["GITHUB_STEP_SUMMARY"]]
    return args


if __name__ == "__main__":
    sys.exit(main(build_args(dict(os.environ))))
