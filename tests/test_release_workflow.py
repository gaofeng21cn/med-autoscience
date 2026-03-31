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


def test_release_workflows_use_supported_setup_python_action_version() -> None:
    ci_workflow = (REPO_ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    release_workflow = RELEASE_WORKFLOW_PATH.read_text(encoding="utf-8")

    assert "actions/setup-python@v5" in ci_workflow
    assert "actions/setup-python@v5" in release_workflow


def test_release_workflow_uses_explicit_prerelease_tag_patterns() -> None:
    workflow = RELEASE_WORKFLOW_PATH.read_text(encoding="utf-8")

    assert "[[:alpha:]]" not in workflow
    assert "a[0-9]+" in workflow
    assert "b[0-9]+" in workflow
    assert "rc[0-9]+" in workflow


def test_release_workflows_install_pandoc_before_running_pytest() -> None:
    ci_workflow = (REPO_ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    release_workflow = RELEASE_WORKFLOW_PATH.read_text(encoding="utf-8")

    assert "brew install pandoc" in ci_workflow
    assert "brew install pandoc" in release_workflow


def test_release_workflows_use_uv_managed_test_environment() -> None:
    ci_workflow = (REPO_ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    release_workflow = RELEASE_WORKFLOW_PATH.read_text(encoding="utf-8")

    assert "uv sync --frozen --group dev" in ci_workflow
    assert "uv sync --frozen --group dev" in release_workflow
    assert "uv run pytest" in ci_workflow
    assert "uv run pytest" in release_workflow
    assert "uv run python -m build --sdist --wheel" in ci_workflow
    assert "uv run python -m build --sdist --wheel" in release_workflow
    assert "python -m pytest" not in ci_workflow
    assert "python -m pytest" not in release_workflow
    assert "python -m pip install pytest build python-docx ." not in ci_workflow
    assert "python -m pip install pytest build python-docx ." not in release_workflow


def test_release_workflow_dev_group_matches_uv_sync_contract() -> None:
    pyproject = tomllib.loads(PYPROJECT_PATH.read_text(encoding="utf-8"))

    dependency_groups = pyproject.get("dependency-groups")
    assert isinstance(dependency_groups, dict)

    dev_group = dependency_groups.get("dev")
    assert isinstance(dev_group, list)

    dev_names = {Requirement(item).name for item in dev_group}
    assert {"pytest", "build", "python-docx"}.issubset(dev_names)
