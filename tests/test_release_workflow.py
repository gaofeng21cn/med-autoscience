from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
RELEASE_WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "release.yml"


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
