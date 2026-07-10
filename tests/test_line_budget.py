from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest


def _load_line_budget_script():
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "line_budget.py"
    spec = importlib.util.spec_from_file_location("mas_line_budget_script", script_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_line_budget_script_accepts_current_locked_baseline(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _load_line_budget_script()
    monkeypatch.setattr(sys, "argv", ["scripts/line_budget.py"])

    assert module.main() == 0


@pytest.mark.parametrize("extra_args", [[], ["--strict"]])
def test_line_budget_script_reports_findings_as_advisory(
    extra_args: list[str],
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    module = _load_line_budget_script()
    finding = SimpleNamespace(
        line_count=1200,
        path="src/med_autoscience/example.py",
        message="exceeds the preferred line budget",
        recommendation="split along the owner boundary",
    )
    report = SimpleNamespace(oversized_findings=(finding,))
    monkeypatch.setattr(module, "audit_boundary_fitness", lambda *args, **kwargs: report)
    monkeypatch.setattr(sys, "argv", ["scripts/line_budget.py", *extra_args])

    assert module.main() == 0
    output = capsys.readouterr().out
    assert "line budget advisory found 1 issue" in output
    assert finding.path in output


def test_verify_runs_line_budget_before_default_smoke() -> None:
    verify = (Path(__file__).resolve().parents[1] / "scripts" / "verify.sh").read_text(encoding="utf-8")
    assert verify.index('"${clean_python_runner}" scripts/line_budget.py') < verify.index("make test-smoke")
