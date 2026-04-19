from __future__ import annotations

import importlib
from pathlib import Path


def test_run_preflight_reports_unclassified_changes_without_running_commands(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.dev_preflight")

    result = module.run_preflight(
        changed_files=["src/med_autoscience/controllers/untracked_controller.py"],
        repo_root=tmp_path,
    )

    assert result.ok is False
    assert result.unclassified_changes == ("src/med_autoscience/controllers/untracked_controller.py",)
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
    assert result.matched_categories == ("public_doc_surface",)
    assert result.unclassified_changes == ()
    assert result.planned_commands == (
        "uv run pytest tests/test_dev_preflight_contract.py -q",
        "uv run pytest tests/test_dev_preflight.py -q",
        "make test-meta",
    )
    assert calls[0] == ["uv", "run", "pytest", "tests/test_dev_preflight_contract.py", "-q"]
    assert result.results[0].stdout == "ok\n"


def test_run_preflight_executes_external_runtime_dependency_commands(monkeypatch, tmp_path: Path) -> None:
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
        changed_files=["docs/program/external_runtime_dependency_gate.md"],
        repo_root=tmp_path,
    )

    assert result.ok is True
    assert result.matched_categories == ("external_runtime_dependency_surface",)
    assert result.unclassified_changes == ()
    assert "uv run pytest tests/test_external_runtime_dependency_gate.py -q" in result.planned_commands
    assert calls[0] == ["uv", "run", "pytest", "tests/test_med_deepscientist_repo_manifest.py", "-q"]


def test_run_preflight_executes_integration_harness_commands(monkeypatch, tmp_path: Path) -> None:
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
        changed_files=["docs/program/integration_harness_activation_package.md"],
        repo_root=tmp_path,
    )

    assert result.ok is True
    assert result.matched_categories == ("integration_harness_surface",)
    assert result.unclassified_changes == ()
    assert "uv run pytest tests/test_integration_harness_activation_package.py -q" in result.planned_commands
    assert "uv run pytest tests/test_workspace_init.py -q" in result.planned_commands
    assert "uv run pytest tests/test_runtime_watch.py tests/test_study_delivery_sync.py tests/test_publication_gate.py -q" not in result.planned_commands
    assert calls[0] == ["uv", "run", "pytest", "tests/test_dev_preflight_contract.py", "-q"]


def test_collect_changed_files_from_staged_diff(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.dev_preflight")

    monkeypatch.setattr(
        module,
        "_git_diff_name_only",
        lambda **kwargs: ["README.md", "docs/references/codex_plugin.md"],
    )

    changed_files = module.collect_changed_files(repo_root=tmp_path, staged=True)

    assert changed_files == ["README.md", "docs/references/codex_plugin.md"]


def test_collect_changed_files_from_base_ref_diff(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.dev_preflight")

    monkeypatch.setattr(
        module,
        "_git_diff_name_only",
        lambda **kwargs: ["src/med_autoscience/controllers/study_runtime_router.py"],
    )

    changed_files = module.collect_changed_files(repo_root=tmp_path, base_ref="origin/main")

    assert changed_files == ["src/med_autoscience/controllers/study_runtime_router.py"]
