from __future__ import annotations

import importlib
from pathlib import Path


def test_run_preflight_reports_unclassified_changes_without_running_commands(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.dev_preflight")

    result = module.run_preflight(
        changed_files=["src/med_autoscience/controllers/workspace_init.py"],
        repo_root=tmp_path,
    )

    assert result.ok is False
    assert result.unclassified_changes == ("src/med_autoscience/controllers/workspace_init.py",)
    assert result.results == ()
    assert result.planned_commands == ()


def test_run_preflight_executes_planned_commands(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.dev_preflight")
    calls: list[list[str]] = []

    def fake_run(command, **kwargs):
        calls.append(list(command))

        class Result:
            returncode = 0
            stdout = "ok\n"
            stderr = ""

        return Result()

    monkeypatch.setattr(module.subprocess, "run", fake_run)

    result = module.run_preflight(
        changed_files=["README.md"],
        repo_root=tmp_path,
    )

    assert result.ok is True
    assert result.matched_categories == ("codex_plugin_docs_surface",)
    assert result.unclassified_changes == ()
    assert result.planned_commands == (
        "uv run pytest tests/test_codex_plugin.py -q",
        "uv run pytest tests/test_codex_plugin_installer.py -q",
        "uv run pytest tests/test_codex_plugin_installer_script.py -q",
    )
    assert calls[0] == ["uv", "run", "pytest", "tests/test_codex_plugin.py", "-q"]
    assert result.results[0].stdout == "ok\n"
