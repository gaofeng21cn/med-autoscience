from __future__ import annotations

import tomllib
from pathlib import Path

from packaging.requirements import Requirement


REPO_ROOT = Path(__file__).resolve().parents[1]
CI_WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "ci.yml"
ADVISORY_WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "advisory.yml"
RELEASE_WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "release.yml"
PYPROJECT_PATH = REPO_ROOT / "pyproject.toml"


def test_release_workflow_grants_contents_write_permission() -> None:
    workflow = RELEASE_WORKFLOW_PATH.read_text(encoding="utf-8")

    assert "permissions:" in workflow
    assert "contents: write" in workflow


def test_release_workflows_use_node24_ready_action_versions() -> None:
    ci_workflow = CI_WORKFLOW_PATH.read_text(encoding="utf-8")
    advisory_workflow = ADVISORY_WORKFLOW_PATH.read_text(encoding="utf-8")
    release_workflow = RELEASE_WORKFLOW_PATH.read_text(encoding="utf-8")

    assert "actions/checkout@v6" in ci_workflow
    assert "actions/checkout@v6" in advisory_workflow
    assert "actions/checkout@v6" in release_workflow
    assert "actions/setup-python@v6" in ci_workflow
    assert "actions/setup-python@v6" in advisory_workflow
    assert "actions/setup-python@v6" in release_workflow


def test_release_workflows_track_python_312_minor_instead_of_exact_patch_file() -> None:
    ci_workflow = CI_WORKFLOW_PATH.read_text(encoding="utf-8")
    advisory_workflow = ADVISORY_WORKFLOW_PATH.read_text(encoding="utf-8")
    release_workflow = RELEASE_WORKFLOW_PATH.read_text(encoding="utf-8")

    assert "python-version: '3.12'" in ci_workflow
    assert "python-version: '3.12'" in advisory_workflow
    assert "python-version: '3.12'" in release_workflow
    assert "python-version-file: .python-version" not in ci_workflow
    assert "python-version-file: .python-version" not in advisory_workflow
    assert "python-version-file: .python-version" not in release_workflow


def test_release_workflow_uses_explicit_prerelease_tag_patterns() -> None:
    workflow = RELEASE_WORKFLOW_PATH.read_text(encoding="utf-8")

    assert "[[:alpha:]]" not in workflow
    assert "a[0-9]+" in workflow
    assert "b[0-9]+" in workflow
    assert "rc[0-9]+" in workflow


def test_release_workflows_split_system_dependencies_by_lane() -> None:
    ci_workflow = CI_WORKFLOW_PATH.read_text(encoding="utf-8")
    advisory_workflow = ADVISORY_WORKFLOW_PATH.read_text(encoding="utf-8")
    release_workflow = RELEASE_WORKFLOW_PATH.read_text(encoding="utf-8")
    family_workflow, display_workflow = advisory_workflow.split("display-surface:", maxsplit=1)

    assert "Install pandoc and BasicTeX" in ci_workflow
    assert "brew install pandoc" in ci_workflow
    assert "brew install --cask basictex" in ci_workflow
    assert 'echo "/Library/TeX/texbin" >> "${GITHUB_PATH}"' in ci_workflow
    assert "graphviz" not in ci_workflow
    assert "brew install pandoc graphviz pkg-config libxml2 r" not in family_workflow
    assert "brew install pandoc graphviz pkg-config libxml2 r" in display_workflow
    assert "brew install --cask basictex" in display_workflow
    assert 'echo "/Library/TeX/texbin" >> "${GITHUB_PATH}"' in display_workflow
    assert "brew install pandoc graphviz pkg-config libxml2 r" in release_workflow
    assert "brew install --cask basictex" in release_workflow
    assert 'echo "/Library/TeX/texbin" >> "${GITHUB_PATH}"' in release_workflow
    assert "PKG_CONFIG_PATH=$(brew --prefix libxml2)/lib/pkgconfig:${PKG_CONFIG_PATH:-}" in display_workflow
    assert "XML_CONFIG=$(brew --prefix libxml2)/bin/xml2-config" in display_workflow
    assert "PKG_CONFIG_PATH=$(brew --prefix libxml2)/lib/pkgconfig:${PKG_CONFIG_PATH:-}" in release_workflow
    assert "XML_CONFIG=$(brew --prefix libxml2)/bin/xml2-config" in release_workflow


def test_release_workflows_use_uv_managed_test_environment() -> None:
    ci_workflow = CI_WORKFLOW_PATH.read_text(encoding="utf-8")
    advisory_workflow = ADVISORY_WORKFLOW_PATH.read_text(encoding="utf-8")
    release_workflow = RELEASE_WORKFLOW_PATH.read_text(encoding="utf-8")

    assert "uv sync --frozen --group dev" in ci_workflow
    assert "uv sync --frozen --group dev" in advisory_workflow
    assert "uv sync --frozen --group dev" in release_workflow
    assert "scripts/verify.sh meta" in ci_workflow
    assert "scripts/verify.sh" in ci_workflow
    assert "scripts/verify.sh family" in advisory_workflow
    assert "scripts/verify.sh display" in advisory_workflow
    assert "scripts/verify.sh family" not in ci_workflow
    assert "scripts/verify.sh display" not in ci_workflow
    assert "scripts/verify.sh full" in release_workflow
    assert "uv run python -m build --sdist --wheel" in ci_workflow
    assert "uv run python -m build --sdist --wheel" in release_workflow
    assert "python -m pytest" not in ci_workflow
    assert "python -m pytest" not in advisory_workflow
    assert "python -m pytest" not in release_workflow
    assert "python -m pip install pytest build python-docx ." not in ci_workflow
    assert "python -m pip install pytest build python-docx ." not in advisory_workflow
    assert "python -m pip install pytest build python-docx ." not in release_workflow
    assert "uv run pytest" not in ci_workflow
    assert "uv run pytest" not in advisory_workflow
    assert "uv run pytest" not in release_workflow
    assert "make test-meta" not in ci_workflow
    assert "make test-fast" not in ci_workflow
    assert "make test-display" not in ci_workflow
    assert "make test-family" not in advisory_workflow
    assert "make test-display" not in advisory_workflow
    assert "make test-full" not in release_workflow


def test_advisory_and_release_workflows_only_prepare_study_runtime_analysis_bundle_for_display_and_release_bound_lanes() -> None:
    ci_workflow = CI_WORKFLOW_PATH.read_text(encoding="utf-8")
    advisory_workflow = ADVISORY_WORKFLOW_PATH.read_text(encoding="utf-8")
    release_workflow = RELEASE_WORKFLOW_PATH.read_text(encoding="utf-8")
    family_workflow, display_workflow = advisory_workflow.split("display-surface:", maxsplit=1)

    assert ci_workflow.count("Ensure study runtime analysis bundle") == 0
    assert advisory_workflow.count("Ensure study runtime analysis bundle") == 1
    assert "Ensure study runtime analysis bundle" not in family_workflow
    assert "Ensure study runtime analysis bundle" in display_workflow
    assert "Run display-heavy advisory tests" in advisory_workflow
    assert "continue-on-error: true" not in ci_workflow
    assert "continue-on-error: true" in family_workflow
    assert "continue-on-error: true" in display_workflow
    assert "brew install pandoc graphviz pkg-config libxml2 r" in release_workflow
    assert "Ensure study runtime analysis bundle" in release_workflow
    assert "continue-on-error: true" not in release_workflow
    assert "scripts/verify.sh full" in release_workflow


def test_ci_docs_keep_public_readmes_focused_on_user_entry() -> None:
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    readme_zh = (REPO_ROOT / "README.zh-CN.md").read_text(encoding="utf-8")
    preflight_doc = (REPO_ROOT / "docs" / "program" / "repository_ci_preflight.md").read_text(encoding="utf-8")

    assert "Docs Guide" in readme
    assert "Project" in readme
    assert "product-frontdesk" not in readme
    assert "workspace-cockpit" not in readme
    assert "Repository CI preflight" not in readme
    assert "repository_ci_preflight.md" not in readme
    assert "Development Verification" not in readme
    assert "Codex Plugin Integration" not in readme
    assert "submission-facing DOCX/PDF coverage" not in readme
    assert "`pandoc` plus `BasicTeX`" not in readme
    assert "advisory on push" not in readme
    assert "文档索引" in readme_zh
    assert "项目概览" in readme_zh
    assert "product-frontdesk" not in readme_zh
    assert "workspace-cockpit" not in readme_zh
    assert "仓库 CI 预检" not in readme_zh
    assert "repository_ci_preflight.md" not in readme_zh
    assert "开发验证" not in readme_zh
    assert "Codex 接入说明" not in readme_zh
    assert "submission-facing DOCX/PDF 覆盖" not in readme_zh
    assert "`pandoc` 与 `BasicTeX`" not in readme_zh
    assert "push 上保持 advisory 告警" not in readme_zh
    assert "submission-facing DOCX/PDF" in preflight_doc
    assert "`pandoc` 与 `BasicTeX`" in preflight_doc
    assert "display-heavy` 与 `family` lane 迁入 `macOS Advisory`" in preflight_doc


def test_release_workflows_split_stable_push_and_advisory_jobs() -> None:
    ci_workflow = CI_WORKFLOW_PATH.read_text(encoding="utf-8")
    advisory_workflow = ADVISORY_WORKFLOW_PATH.read_text(encoding="utf-8")

    assert "quick-checks:" in ci_workflow
    assert "display-surface:" not in ci_workflow
    assert "Run stable core tests and build" in ci_workflow
    assert "family-shared:" in advisory_workflow
    assert "display-surface:" in advisory_workflow
    assert "Run family shared advisory tests" in advisory_workflow
    assert "Run display-heavy advisory tests" in advisory_workflow


def test_release_workflow_dev_group_matches_uv_sync_contract() -> None:
    pyproject = tomllib.loads(PYPROJECT_PATH.read_text(encoding="utf-8"))

    dependency_groups = pyproject.get("dependency-groups")
    assert isinstance(dependency_groups, dict)

    dev_group = dependency_groups.get("dev")
    assert isinstance(dev_group, list)

    dev_names = {Requirement(item).name for item in dev_group}
    assert {"pytest", "build", "python-docx"}.issubset(dev_names)


def test_ci_workflow_only_triggers_on_push_main_and_development() -> None:
    ci_workflow = CI_WORKFLOW_PATH.read_text(encoding="utf-8")

    assert "pull_request:" not in ci_workflow
    assert "push:" in ci_workflow
    assert "- main" in ci_workflow
    assert "- development" in ci_workflow


def test_advisory_workflow_only_triggers_on_manual_or_daily_schedule() -> None:
    advisory_workflow = ADVISORY_WORKFLOW_PATH.read_text(encoding="utf-8")

    assert "push:" not in advisory_workflow
    assert "pull_request:" not in advisory_workflow
    assert "workflow_dispatch:" in advisory_workflow
    assert "schedule:" in advisory_workflow
    assert "cron: '0 20 * * *'" in advisory_workflow
