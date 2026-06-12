from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest


def _load_line_budget_script():
    repo_root = Path(__file__).resolve().parents[1]
    script_path = repo_root / "scripts" / "line_budget.py"
    spec = importlib.util.spec_from_file_location("mas_line_budget_script", script_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _install_line_budget_report(module, monkeypatch: pytest.MonkeyPatch) -> None:
    finding = SimpleNamespace(
        line_count=1200,
        path="src/med_autoscience/example.py",
        message="exceeds the preferred line budget",
        recommendation="split along the owner boundary",
    )
    report = SimpleNamespace(
        oversized_findings=(finding,),
        blocking_findings=(finding,),
    )
    monkeypatch.setattr(module, "audit_boundary_fitness", lambda *args, **kwargs: report)


def _install_oversized_advisory_report(module, monkeypatch: pytest.MonkeyPatch) -> None:
    finding = SimpleNamespace(
        line_count=1200,
        path="src/med_autoscience/example.py",
        message="exceeds the preferred line budget",
        recommendation="split along the owner boundary",
    )
    report = SimpleNamespace(
        oversized_findings=(finding,),
        blocking_findings=(),
    )
    monkeypatch.setattr(module, "audit_boundary_fitness", lambda *args, **kwargs: report)


def test_line_budget_script_accepts_current_locked_baseline() -> None:
    module = _load_line_budget_script()
    original_argv = sys.argv
    sys.argv = ["scripts/line_budget.py"]
    try:
        exit_code = module.main()
    finally:
        sys.argv = original_argv

    assert exit_code == 0


def test_line_budget_script_reports_all_line_budget_findings_as_advisory_by_default(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    module = _load_line_budget_script()
    _install_line_budget_report(module, monkeypatch)
    monkeypatch.delenv("MAS_LINE_BUDGET_STRICT", raising=False)
    original_argv = sys.argv
    sys.argv = ["scripts/line_budget.py"]
    try:
        exit_code = module.main()
    finally:
        sys.argv = original_argv

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "line budget advisory found 1 issue" in output
    assert "src/med_autoscience/example.py" in output


def test_line_budget_script_reports_oversized_advisories_by_default(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    module = _load_line_budget_script()
    _install_oversized_advisory_report(module, monkeypatch)
    monkeypatch.delenv("MAS_LINE_BUDGET_STRICT", raising=False)
    original_argv = sys.argv
    sys.argv = ["scripts/line_budget.py"]
    try:
        exit_code = module.main()
    finally:
        sys.argv = original_argv

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "line budget advisory found 1 issue" in output
    assert "src/med_autoscience/example.py" in output


def test_line_budget_script_strict_flag_keeps_line_budget_advisory(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    module = _load_line_budget_script()
    _install_oversized_advisory_report(module, monkeypatch)
    original_argv = sys.argv
    sys.argv = ["scripts/line_budget.py", "--strict"]
    try:
        exit_code = module.main()
    finally:
        sys.argv = original_argv

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "line budget advisory found 1 issue" in output


def test_line_budget_script_strict_environment_keeps_line_budget_advisory(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    module = _load_line_budget_script()
    _install_oversized_advisory_report(module, monkeypatch)
    monkeypatch.setenv("MAS_LINE_BUDGET_STRICT", "1")
    original_argv = sys.argv
    sys.argv = ["scripts/line_budget.py"]
    try:
        exit_code = module.main()
    finally:
        sys.argv = original_argv

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "line budget advisory found 1 issue" in output


def test_verify_runs_line_budget_as_advisory_sanity_check_before_default_smoke_tests() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    verify_script = (repo_root / "scripts" / "verify.sh").read_text(encoding="utf-8")
    line_budget_command = '"${clean_python_runner}" scripts/line_budget.py'

    assert line_budget_command in verify_script
    assert verify_script.index(line_budget_command) < verify_script.index("make test-smoke")
