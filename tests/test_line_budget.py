from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_line_budget_script_accepts_current_locked_baseline() -> None:
    repo_root = Path(__file__).resolve().parents[1]

    result = subprocess.run(
        [sys.executable, "scripts/line_budget.py"],
        cwd=repo_root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    assert result.returncode == 0, result.stdout


def test_verify_runs_line_budget_as_intentional_sanity_gate_before_default_smoke_tests() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    verify_script = (repo_root / "scripts" / "verify.sh").read_text(encoding="utf-8")
    line_budget_command = 'PYTHONPATH="${repo_root}/src${PYTHONPATH:+:${PYTHONPATH}}" python scripts/line_budget.py'

    assert line_budget_command in verify_script
    assert verify_script.index(line_budget_command) < verify_script.index("make test-smoke")
