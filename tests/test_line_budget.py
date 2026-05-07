from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def _load_line_budget_script():
    repo_root = Path(__file__).resolve().parents[1]
    script_path = repo_root / "scripts" / "line_budget.py"
    spec = importlib.util.spec_from_file_location("mas_line_budget_script", script_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_line_budget_script_accepts_current_locked_baseline() -> None:
    module = _load_line_budget_script()
    original_argv = sys.argv
    sys.argv = ["scripts/line_budget.py"]
    try:
        exit_code = module.main()
    finally:
        sys.argv = original_argv

    assert exit_code == 0


def test_verify_runs_line_budget_as_intentional_sanity_gate_before_default_smoke_tests() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    verify_script = (repo_root / "scripts" / "verify.sh").read_text(encoding="utf-8")
    line_budget_command = 'PYTHONPATH="${repo_root}/src${PYTHONPATH:+:${PYTHONPATH}}" python scripts/line_budget.py'

    assert line_budget_command in verify_script
    assert verify_script.index(line_budget_command) < verify_script.index("make test-smoke")
