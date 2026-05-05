from __future__ import annotations

import importlib
from pathlib import Path

import pytest

pytestmark = pytest.mark.family


def test_run_preflight_treats_docs_as_review_only_without_running_commands(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.dev_preflight")

    result = module.run_preflight(
        changed_files=["docs/program/untracked_runtime_contract.md"],
        repo_root=tmp_path,
    )

    assert result.ok is True
    assert result.matched_categories == ("documentation_review_only",)
    assert result.unclassified_changes == ()
    assert result.results == ()
    assert result.planned_commands == ()


def test_run_preflight_routes_unknown_python_changes_to_regression(monkeypatch, tmp_path: Path) -> None:
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
        changed_files=["src/med_autoscience/controllers/new_controller.py"],
        repo_root=tmp_path,
    )

    assert result.ok is True
    assert result.matched_categories == ("generic_python_regression_surface",)
    assert result.unclassified_changes == ()
    assert result.planned_commands == ("make test-regression",)
    assert calls == [["make", "test-regression"]]


def test_run_preflight_routes_unknown_test_changes_to_regression(monkeypatch, tmp_path: Path) -> None:
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
        changed_files=["tests/test_new_controller.py"],
        repo_root=tmp_path,
    )

    assert result.ok is True
    assert result.matched_categories == ("generic_python_regression_surface",)
    assert result.unclassified_changes == ()
    assert result.planned_commands == ("make test-regression",)
    assert calls == [["make", "test-regression"]]


def test_run_preflight_keeps_unknown_workflow_config_fail_closed(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.dev_preflight")
    calls: list[list[str]] = []

    def fake_run(command, **kwargs):
        calls.append(list(command))
        raise AssertionError("unclassified workflow/config changes must not run commands")

    monkeypatch.setattr(module.subprocess, "run", fake_run)

    result = module.run_preflight(
        changed_files=[".github/workflows/new-release.yml", "tox.ini"],
        repo_root=tmp_path,
    )

    assert result.ok is False
    assert result.matched_categories == ()
    assert result.unclassified_changes == (".github/workflows/new-release.yml", "tox.ini")
    assert result.planned_commands == ()
    assert result.results == ()
    assert calls == []


def test_run_ci_preflight_runs_smoke_for_empty_diff(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.dev_preflight")
    calls: list[list[str]] = []

    monkeypatch.setattr(module, "collect_changed_files", lambda **kwargs: [])

    def fake_run(command, **kwargs):
        calls.append(list(command))

        class Result:
            returncode = 0
            stdout = "ok\n"
            stderr = ""

        return Result()

    monkeypatch.setattr(module.subprocess, "run", fake_run)

    result = module.run_ci_preflight(base_ref="HEAD~1", repo_root=tmp_path)

    assert result.ok is True
    assert result.input_mode == "ci-empty"
    assert result.changed_files == ()
    assert result.matched_categories == ("smoke_surface",)
    assert result.planned_commands == ("make test-smoke",)
    assert calls == [["make", "test-smoke"]]


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
    assert result.matched_categories == ("documentation_review_only",)
    assert result.unclassified_changes == ()
    assert result.planned_commands == ()
    assert result.results == ()
    assert calls == []


def test_render_preflight_text_includes_failed_command_output_tail() -> None:
    module = importlib.import_module("med_autoscience.dev_preflight")

    result = module.PreflightResult(
        input_mode="ci-base_ref",
        changed_files=("src/med_autoscience/controllers/example.py",),
        matched_categories=("generic_python_regression_surface",),
        unclassified_changes=(),
        planned_commands=("make test-regression",),
        results=(
            module.CommandResult(
                command="make test-regression",
                returncode=2,
                stdout="collected 2 items\nFAILED tests/test_example.py::test_contract\n",
                stderr="pytest: error: unknown config option\n",
            ),
        ),
        ok=False,
    )

    text = module.render_preflight_text(result)

    assert "  - command: make test-regression" in text
    assert "    returncode: 2" in text
    assert "    stdout_tail:" in text
    assert "      FAILED tests/test_example.py::test_contract" in text
    assert "    stderr_tail:" in text
    assert "      pytest: error: unknown config option" in text


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
    assert result.matched_categories == ("documentation_review_only",)
    assert result.unclassified_changes == ()
    assert result.planned_commands == ()
    assert result.results == ()
    assert calls == []


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
    assert result.matched_categories == ("documentation_review_only",)
    assert result.unclassified_changes == ()
    assert result.planned_commands == ()
    assert result.results == ()
    assert calls == []


def test_run_preflight_executes_family_shared_lane(monkeypatch, tmp_path: Path) -> None:
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
        changed_files=["src/med_autoscience/editable_shared_bootstrap.py"],
        repo_root=tmp_path,
    )

    assert result.ok is True
    assert result.matched_categories == ("family_shared_surface",)
    assert result.unclassified_changes == ()
    assert result.planned_commands == ("make test-family",)
    assert calls == [["make", "test-family"]]


def test_family_verify_lane_is_exposed_from_makefile_and_verify_script() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    makefile = (repo_root / "Makefile").read_text(encoding="utf-8")
    verify_script = (repo_root / "scripts" / "verify.sh").read_text(encoding="utf-8")

    phony_line = next(line for line in makefile.splitlines() if line.startswith(".PHONY:"))
    phony_targets = set(phony_line.split()[1:])
    for target in (
        "test",
        "test-smoke",
        "test-regression",
        "test-ci-preflight",
        "test-fast",
        "test-meta",
        "test-display",
        "test-submission",
        "test-full",
        "test-family",
        "test-structure",
        "test-control-plane",
    ):
        assert target in phony_targets
    assert "test-control-plane:" in makefile
    assert (
        'if [[ "${lane}" == "control-plane" ]]; then\n'
        '  run_with_optional_summary "control-plane" "make test-control-plane" make test-control-plane\n'
        "  exit 0\n"
        "fi\n"
    ) in verify_script
    assert "test-smoke:" in makefile
    assert "test-regression:" in makefile
    assert "test-ci-preflight:" in makefile
    assert (
        "test-family:\n"
        "\tuv run pytest tests/test_family_shared_release.py "
        "tests/test_editable_shared_bootstrap.py tests/test_dev_preflight_contract.py "
        "tests/test_dev_preflight.py -q\n"
    ) in makefile
    assert (
        'if [[ "${lane}" == "family" ]]; then\n'
        '  run_with_optional_summary "family" "make test-family" make test-family\n'
        "  exit 0\n"
        "fi\n"
    ) in verify_script
    assert 'if [[ "${lane}" == "ci-preflight" ]]; then' in verify_script


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
