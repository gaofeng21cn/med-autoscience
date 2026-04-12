from __future__ import annotations

import tomllib
from pathlib import Path

from packaging.requirements import Requirement


REPO_ROOT = Path(__file__).resolve().parents[1]
RELEASE_WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "release.yml"
PYPROJECT_PATH = REPO_ROOT / "pyproject.toml"


def test_release_workflow_grants_contents_write_permission() -> None:
    workflow = RELEASE_WORKFLOW_PATH.read_text(encoding="utf-8")

    assert "permissions:" in workflow
    assert "contents: write" in workflow


def test_release_workflows_use_node24_ready_action_versions() -> None:
    ci_workflow = (REPO_ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    release_workflow = RELEASE_WORKFLOW_PATH.read_text(encoding="utf-8")

    assert "actions/checkout@v6" in ci_workflow
    assert "actions/checkout@v6" in release_workflow
    assert "actions/setup-python@v6" in ci_workflow
    assert "actions/setup-python@v6" in release_workflow


def test_release_workflows_track_python_312_minor_instead_of_exact_patch_file() -> None:
    ci_workflow = (REPO_ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    release_workflow = RELEASE_WORKFLOW_PATH.read_text(encoding="utf-8")

    assert "python-version: '3.12'" in ci_workflow
    assert "python-version: '3.12'" in release_workflow
    assert "python-version-file: .python-version" not in ci_workflow
    assert "python-version-file: .python-version" not in release_workflow


def test_release_workflow_uses_explicit_prerelease_tag_patterns() -> None:
    workflow = RELEASE_WORKFLOW_PATH.read_text(encoding="utf-8")

    assert "[[:alpha:]]" not in workflow
    assert "a[0-9]+" in workflow
    assert "b[0-9]+" in workflow
    assert "rc[0-9]+" in workflow


def test_release_workflows_install_pandoc_and_graphviz_before_running_pytest() -> None:
    ci_workflow = (REPO_ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    release_workflow = RELEASE_WORKFLOW_PATH.read_text(encoding="utf-8")

    assert "brew install pandoc graphviz" in ci_workflow
    assert "brew install pandoc graphviz" in release_workflow


def test_release_workflows_use_uv_managed_test_environment() -> None:
    ci_workflow = (REPO_ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    release_workflow = RELEASE_WORKFLOW_PATH.read_text(encoding="utf-8")

    assert "uv sync --frozen --group dev" in ci_workflow
    assert "uv sync --frozen --group dev" in release_workflow
    assert "scripts/verify.sh meta" in ci_workflow
    assert "scripts/verify.sh" in ci_workflow
    assert "scripts/verify.sh display" in ci_workflow
    assert "scripts/verify.sh full" in release_workflow
    assert "uv run python -m build --sdist --wheel" in ci_workflow
    assert "uv run python -m build --sdist --wheel" in release_workflow
    assert "python -m pytest" not in ci_workflow
    assert "python -m pytest" not in release_workflow
    assert "python -m pip install pytest build python-docx ." not in ci_workflow
    assert "python -m pip install pytest build python-docx ." not in release_workflow
    assert "uv run pytest" not in ci_workflow
    assert "uv run pytest" not in release_workflow
    assert "make test-meta" not in ci_workflow
    assert "make test-fast" not in ci_workflow
    assert "make test-display" not in ci_workflow
    assert "make test-full" not in release_workflow


def test_ci_and_release_workflows_prepare_study_runtime_analysis_bundle_before_display_bound_lanes() -> None:
    ci_workflow = (REPO_ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    release_workflow = RELEASE_WORKFLOW_PATH.read_text(encoding="utf-8")

    assert ci_workflow.count("Ensure study runtime analysis bundle") == 2
    assert "Run display-heavy tests" in ci_workflow
    assert "brew install pandoc graphviz r" in release_workflow
    assert "Ensure study runtime analysis bundle" in release_workflow
    assert "scripts/verify.sh full" in release_workflow


def test_release_workflows_split_ci_fast_and_display_jobs() -> None:
    ci_workflow = (REPO_ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")

    assert "quick-checks:" in ci_workflow
    assert "display-surface:" in ci_workflow
    assert "Run fast/meta tests and build" in ci_workflow
    assert "Run display-heavy tests" in ci_workflow


def test_release_workflow_dev_group_matches_uv_sync_contract() -> None:
    pyproject = tomllib.loads(PYPROJECT_PATH.read_text(encoding="utf-8"))

    dependency_groups = pyproject.get("dependency-groups")
    assert isinstance(dependency_groups, dict)

    dev_group = dependency_groups.get("dev")
    assert isinstance(dev_group, list)

    dev_names = {Requirement(item).name for item in dev_group}
    assert {"pytest", "build", "python-docx"}.issubset(dev_names)


def test_ci_workflow_only_triggers_on_push_main_and_development() -> None:
    ci_workflow = (REPO_ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")

    assert "pull_request:" not in ci_workflow
    assert "push:" in ci_workflow
    assert "- main" in ci_workflow
    assert "- development" in ci_workflow
