from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

from packaging.requirements import Requirement


REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_DIR = REPO_ROOT / ".github" / "workflows"
CI_WORKFLOW_PATH = WORKFLOW_DIR / "ci.yml"
ADVISORY_WORKFLOW_PATH = WORKFLOW_DIR / "advisory.yml"
SENTRUX_ADVISORY_WORKFLOW_PATH = WORKFLOW_DIR / "sentrux-advisory.yml"
RELEASE_WORKFLOW_PATH = WORKFLOW_DIR / "release.yml"
PYPROJECT_PATH = REPO_ROOT / "pyproject.toml"


def _workflow_texts() -> list[str]:
    return [path.read_text(encoding="utf-8") for path in sorted(WORKFLOW_DIR.glob("*.yml"))]


def _workflow_job(workflow: str, job_id: str) -> str:
    match = re.search(rf"(?ms)^  {re.escape(job_id)}:\n.*?(?=^  [A-Za-z0-9_-]+:\n|\Z)", workflow)
    assert match is not None, f"missing workflow job: {job_id}"
    return match.group(0)


def _workflow_step(workflow_job: str, step_name: str) -> str:
    match = re.search(rf"(?ms)^      - name: {re.escape(step_name)}\n.*?(?=^      - name: |\Z)", workflow_job)
    assert match is not None, f"missing workflow step: {step_name}"
    return match.group(0)


def test_domain_repo_does_not_publish_github_releases() -> None:
    workflow_text = "\n".join(_workflow_texts())

    assert not RELEASE_WORKFLOW_PATH.exists()
    assert "softprops/action-gh-release" not in workflow_text
    assert "contents: write" not in workflow_text
    assert "releases/download" not in workflow_text


def test_ci_and_advisory_workflows_use_node24_ready_action_versions() -> None:
    ci_workflow = CI_WORKFLOW_PATH.read_text(encoding="utf-8")
    advisory_workflow = ADVISORY_WORKFLOW_PATH.read_text(encoding="utf-8")
    sentrux_advisory_workflow = SENTRUX_ADVISORY_WORKFLOW_PATH.read_text(encoding="utf-8")

    assert "actions/checkout@v6" in ci_workflow
    assert "actions/checkout@v6" in advisory_workflow
    assert "actions/checkout@v6" in sentrux_advisory_workflow
    assert "actions/setup-python@v6" in ci_workflow
    assert "actions/setup-python@v6" in advisory_workflow


def test_ci_and_advisory_workflows_cancel_superseded_same_ref_runs() -> None:
    ci_workflow = CI_WORKFLOW_PATH.read_text(encoding="utf-8")
    advisory_workflow = ADVISORY_WORKFLOW_PATH.read_text(encoding="utf-8")

    for workflow in (ci_workflow, advisory_workflow):
        assert "concurrency:" in workflow
        assert "group: ${{ github.workflow }}-${{ github.ref }}" in workflow
        assert "cancel-in-progress: true" in workflow


def test_sentrux_advisory_workflow_fetches_main_and_passes_opl_compare_ref() -> None:
    workflow = SENTRUX_ADVISORY_WORKFLOW_PATH.read_text(encoding="utf-8")
    structural_gate_job = _workflow_job(workflow, "structural-gate")
    checkout_step = _workflow_step(structural_gate_job, "Checkout repository")
    quality_details_step = _workflow_step(structural_gate_job, "Run OPL quality details")

    assert "fetch-depth: 0" in checkout_step
    assert "git fetch --no-tags --prune origin main:refs/remotes/origin/main" in structural_gate_job
    assert "uses: gaofeng21cn/one-person-lab/.github/actions/quality-details@main" in quality_details_step
    assert "compare-ref: origin/main" in quality_details_step


def test_ci_and_advisory_workflows_track_python_312_minor_instead_of_exact_patch_file() -> None:
    ci_workflow = CI_WORKFLOW_PATH.read_text(encoding="utf-8")
    advisory_workflow = ADVISORY_WORKFLOW_PATH.read_text(encoding="utf-8")

    assert "python-version: '3.12'" in ci_workflow
    assert "python-version: '3.12'" in advisory_workflow
    assert "python-version-file: .python-version" not in ci_workflow
    assert "python-version-file: .python-version" not in advisory_workflow


def test_ci_and_advisory_workflows_split_system_dependencies_by_lane() -> None:
    ci_workflow = CI_WORKFLOW_PATH.read_text(encoding="utf-8")
    advisory_workflow = ADVISORY_WORKFLOW_PATH.read_text(encoding="utf-8")
    regression_workflow = _workflow_job(advisory_workflow, "regression")
    meta_workflow = _workflow_job(advisory_workflow, "meta-contracts")
    family_workflow = _workflow_job(advisory_workflow, "family-shared")
    submission_workflow = _workflow_job(advisory_workflow, "submission-surface")
    display_workflow = _workflow_job(advisory_workflow, "display-surface")

    assert "Install pandoc and BasicTeX" not in ci_workflow
    assert "brew install pandoc" not in ci_workflow
    assert "brew install --cask basictex" not in ci_workflow
    assert 'echo "/Library/TeX/texbin" >> "${GITHUB_PATH}"' not in ci_workflow
    assert "graphviz" not in ci_workflow
    assert "brew install pandoc graphviz pkg-config libxml2 r" not in regression_workflow
    assert "brew install pandoc graphviz pkg-config libxml2 r" not in meta_workflow
    assert "brew install pandoc graphviz pkg-config libxml2 r" not in family_workflow
    assert "brew install pandoc" in submission_workflow
    assert "brew install --cask basictex" in submission_workflow
    assert 'echo "/Library/TeX/texbin" >> "${GITHUB_PATH}"' in submission_workflow
    assert "graphviz" not in submission_workflow
    assert "brew install pandoc graphviz pkg-config libxml2 r" in display_workflow
    assert "brew install --cask basictex" in display_workflow
    assert 'echo "/Library/TeX/texbin" >> "${GITHUB_PATH}"' in display_workflow
    assert "PKG_CONFIG_PATH=$(brew --prefix libxml2)/lib/pkgconfig:${PKG_CONFIG_PATH:-}" in display_workflow
    assert "XML_CONFIG=$(brew --prefix libxml2)/bin/xml2-config" in display_workflow


def test_ci_and_advisory_workflows_use_uv_managed_test_environment() -> None:
    ci_workflow = CI_WORKFLOW_PATH.read_text(encoding="utf-8")
    advisory_workflow = ADVISORY_WORKFLOW_PATH.read_text(encoding="utf-8")
    uv_no_project_jobs = [
        _workflow_job(ci_workflow, "quick-checks"),
        _workflow_job(advisory_workflow, "regression"),
        _workflow_job(advisory_workflow, "meta-contracts"),
        _workflow_job(advisory_workflow, "family-shared"),
        _workflow_job(advisory_workflow, "submission-surface"),
        _workflow_job(advisory_workflow, "display-surface"),
    ]

    assert "uv sync --frozen --group dev" in ci_workflow
    assert "uv sync --frozen --group dev" in advisory_workflow
    for workflow_job in uv_no_project_jobs:
        assert "uv sync --frozen --group dev --no-install-project" in workflow_job
        assert "PYTHONPATH: src" in workflow_job
        assert 'UV_NO_SYNC: "1"' in workflow_job
    assert "enable-cache: true" in ci_workflow
    assert "enable-cache: true" in advisory_workflow
    assert ci_workflow.count("cache-dependency-glob: |") == 1
    assert advisory_workflow.count("cache-dependency-glob: |") == 6
    for workflow in (ci_workflow, advisory_workflow):
        assert "uv.lock" in workflow
        assert "pyproject.toml" in workflow
    assert 'scripts/verify.sh ci-preflight "${{ github.event.before }}"' in ci_workflow
    assert "scripts/verify.sh meta" not in ci_workflow
    assert re.search(r"run: scripts/verify\.sh\s*$", ci_workflow, flags=re.MULTILINE) is None
    assert "scripts/verify.sh regression" in advisory_workflow
    assert "scripts/verify.sh meta" in advisory_workflow
    assert "scripts/verify.sh family" in advisory_workflow
    assert "scripts/verify.sh display" in advisory_workflow
    assert "scripts/verify.sh submission" in advisory_workflow
    assert "scripts/verify.sh regression" not in ci_workflow
    assert "scripts/verify.sh family" not in ci_workflow
    assert "scripts/verify.sh display" not in ci_workflow
    assert "scripts/verify.sh submission" not in ci_workflow
    assert 'scripts/run-build-clean.sh --outdir "${RUNNER_TEMP}/mas-dist"' in ci_workflow
    assert "path: ${{ runner.temp }}/mas-dist" in ci_workflow
    assert "python -m pytest" not in ci_workflow
    assert "python -m pytest" not in advisory_workflow
    assert "python -m pip install pytest build python-docx ." not in ci_workflow
    assert "python -m pip install pytest build python-docx ." not in advisory_workflow
    assert "uv run pytest" not in ci_workflow
    assert "uv run pytest" not in advisory_workflow
    assert "make test-meta" not in ci_workflow
    assert "make test-fast" not in ci_workflow
    assert "make test-display" not in ci_workflow
    assert "make test-regression" not in advisory_workflow
    assert "make test-meta" not in advisory_workflow
    assert "make test-family" not in advisory_workflow
    assert "make test-submission" not in advisory_workflow
    assert "make test-display" not in advisory_workflow


def test_ci_runs_medical_paper_ops_contract_guard_without_touching_live_workspaces() -> None:
    ci_workflow = CI_WORKFLOW_PATH.read_text(encoding="utf-8")
    quick_checks = _workflow_job(ci_workflow, "quick-checks")
    ops_guard_step = _workflow_step(quick_checks, "Run medical paper ops contract guard")

    assert "make test-medical-paper-ops" in ops_guard_step
    assert "scripts/verify.sh ci-preflight" in quick_checks
    assert quick_checks.index("Run change-aware CI preflight") < quick_checks.index(
        "Run medical paper ops contract guard"
    )
    assert quick_checks.index("Run medical paper ops contract guard") < quick_checks.index(
        "Build sdist and wheel"
    )

    forbidden_live_workspace_fragments = (
        "/Users/gaofeng/workspace/Yang/",
        "workspace-cockpit --profile",
        "product-entry-status --profile",
        "study-progress --profile",
        "runtime watch",
        "ensure-study-runtime",
        "prepare-external-research",
        "provider live refresh",
        "live literature refresh",
        "artifacts/medical_paper/literature_provider_runtime.json",
        "artifacts/controller_decisions/latest.json",
        "paper/submission_minimal",
    )
    for fragment in forbidden_live_workspace_fragments:
        assert fragment not in ci_workflow


def test_ci_boundary_guards_mas_repo_only_contract_regression() -> None:
    ci_workflow = CI_WORKFLOW_PATH.read_text(encoding="utf-8")
    quick_checks = _workflow_job(ci_workflow, "quick-checks")

    assert quick_checks.count("actions/checkout@v6") == 1
    assert "repository:" not in quick_checks
    assert "gaofeng21cn/med-deepscientist" not in ci_workflow
    assert ".ci/med-deepscientist" not in ci_workflow

    forbidden_fragments = (
        "prepare-external-research",
        "provider live refresh",
        "live literature refresh",
        "workspace-cockpit --profile",
        "product-entry-status --profile",
        "study-progress --profile",
        "ensure-study-runtime",
        "runtime watch",
        "artifacts/controller_decisions/latest.json",
        "paper/submission_minimal",
    )
    for fragment in forbidden_fragments:
        assert fragment not in quick_checks

    assert "scripts/verify.sh ci-preflight" in quick_checks
    assert "make test-medical-paper-ops" in quick_checks
    assert 'scripts/run-build-clean.sh --outdir "${RUNNER_TEMP}/mas-dist"' in quick_checks


def test_sdist_build_projects_stage_route_contract_resource(tmp_path: Path) -> None:
    fixture_root = tmp_path / "sdist-fixture"
    ignored_roots = {".git", ".venv", ".worktrees", "dist", "build", ".pytest_cache", "__pycache__"}

    def ignore(_dir: str, names: list[str]) -> set[str]:
        return set(names) & ignored_roots

    shutil.copytree(REPO_ROOT, fixture_root, ignore=ignore)

    result = subprocess.run(
        [sys.executable, "-m", "build", "--sdist", "--outdir", str(tmp_path / "dist")],
        cwd=fixture_root,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr


def test_advisory_workflow_only_prepares_study_runtime_analysis_bundle_for_display_lane() -> None:
    ci_workflow = CI_WORKFLOW_PATH.read_text(encoding="utf-8")
    advisory_workflow = ADVISORY_WORKFLOW_PATH.read_text(encoding="utf-8")
    regression_workflow = _workflow_job(advisory_workflow, "regression")
    meta_workflow = _workflow_job(advisory_workflow, "meta-contracts")
    family_workflow = _workflow_job(advisory_workflow, "family-shared")
    submission_workflow = _workflow_job(advisory_workflow, "submission-surface")
    display_workflow = _workflow_job(advisory_workflow, "display-surface")

    assert ci_workflow.count("Ensure study runtime analysis bundle") == 0
    assert advisory_workflow.count("Ensure study runtime analysis bundle") == 1
    assert "Ensure study runtime analysis bundle" not in regression_workflow
    assert "Ensure study runtime analysis bundle" not in meta_workflow
    assert "Ensure study runtime analysis bundle" not in family_workflow
    assert "Ensure study runtime analysis bundle" not in submission_workflow
    assert "Ensure study runtime analysis bundle" in display_workflow
    ensure_bundle_step = _workflow_step(display_workflow, "Ensure study runtime analysis bundle")
    assert 'PYTHONDONTWRITEBYTECODE: "1"' in ensure_bundle_step
    assert "Run regression advisory tests" in advisory_workflow
    assert "Run submission-heavy advisory tests" in advisory_workflow
    assert "Run display-heavy advisory tests" in advisory_workflow
    assert "continue-on-error: true" not in ci_workflow
    for workflow_job in (
        regression_workflow,
        meta_workflow,
        family_workflow,
        submission_workflow,
        display_workflow,
    ):
        assert "continue-on-error: true" in workflow_job


def test_advisory_workflow_uploads_non_blocking_lane_summaries() -> None:
    ci_workflow = CI_WORKFLOW_PATH.read_text(encoding="utf-8")
    advisory_workflow = ADVISORY_WORKFLOW_PATH.read_text(encoding="utf-8")
    history_workflow = _workflow_job(advisory_workflow, "duration-history")

    assert "MAS_TEST_LANE_SUMMARY_PATH" not in ci_workflow
    assert "mas-test-lane-summary-" not in ci_workflow
    assert "duration-history:" in advisory_workflow
    assert "needs:" in history_workflow
    assert "regression" in history_workflow
    assert "meta-contracts" in history_workflow
    assert "family-shared" in history_workflow
    assert "submission-surface" in history_workflow
    assert "display-surface" in history_workflow
    assert "if: always()" in history_workflow
    assert "continue-on-error: true" in history_workflow
    assert "actions/download-artifact@v7" in history_workflow
    assert "pattern: mas-test-lane-summary-*" in history_workflow
    assert "path: artifacts/mas-test-lane-summary-history" in history_workflow
    assert "merge-multiple: true" in history_workflow
    assert "artifacts/mas-test-lane-baseline.json" in history_workflow
    assert "--baseline artifacts/mas-test-lane-baseline.json" in history_workflow
    assert "uv run python scripts/summarize-test-lane-history.py \\" in history_workflow
    assert "uv run python scripts/summarize-test-lane-history.py artifacts/mas-test-lane-summary-history" in history_workflow

    for job_id, lane in (
        ("regression", "regression"),
        ("meta-contracts", "meta"),
        ("family-shared", "family"),
        ("submission-surface", "submission"),
        ("display-surface", "display"),
    ):
        workflow_job = _workflow_job(advisory_workflow, job_id)
        summarize_step = _workflow_step(workflow_job, f"Summarize {lane} lane duration")
        upload_step = _workflow_step(workflow_job, f"Upload {lane} lane summary")

        assert (
            f"MAS_TEST_LANE_SUMMARY_PATH: artifacts/mas-test-lane-summaries/{lane}.json"
            in workflow_job
        )
        assert "if: always()" in summarize_step
        assert "continue-on-error: true" in summarize_step
        assert 'uv run python scripts/summarize-test-lane-durations.py "${MAS_TEST_LANE_SUMMARY_PATH}"' in summarize_step
        assert "if: always()" in upload_step
        assert "uses: actions/upload-artifact@v7" in upload_step
        assert "continue-on-error: true" in upload_step
        assert f"name: mas-test-lane-summary-{lane}" in upload_step
        assert "path: ${{ env.MAS_TEST_LANE_SUMMARY_PATH }}" in upload_step
        assert "if-no-files-found: warn" in upload_step
        assert "retention-days: 14" in upload_step


def test_advisory_workflow_uploads_history_markdown_and_json_summaries() -> None:
    advisory_workflow = ADVISORY_WORKFLOW_PATH.read_text(encoding="utf-8")
    history_workflow = _workflow_job(advisory_workflow, "duration-history")
    history_step = _workflow_step(history_workflow, "Summarize advisory lane duration history")
    upload_step = _workflow_step(history_workflow, "Upload advisory lane duration history")

    assert "mkdir -p artifacts/mas-test-lane-summary-history-summary" in history_step
    assert "history_text=artifacts/mas-test-lane-summary-history-summary/history.txt" in history_step
    assert "history_json=artifacts/mas-test-lane-summary-history-summary/history.json" in history_step
    assert "history_markdown=artifacts/mas-test-lane-summary-history-summary/history.md" in history_step
    assert "uv run python scripts/summarize-test-lane-history.py \\" in history_step
    assert "--format json >\"${history_json}\"" in history_step
    assert "cat \"${history_text}\"" in history_step
    assert "## Advisory lane duration history" in history_step
    assert "median/max/slowest/delta" in history_step
    assert "cat \"${history_markdown}\" >> \"${GITHUB_STEP_SUMMARY}\"" in history_step
    assert "uses: actions/upload-artifact@v7" in upload_step
    assert "name: mas-test-lane-history-summary" in upload_step
    assert "path: artifacts/mas-test-lane-summary-history-summary" in upload_step
    assert "if-no-files-found: warn" in upload_step
    assert "retention-days: 14" in upload_step


def test_ci_and_advisory_workflows_split_stable_push_and_advisory_jobs() -> None:
    ci_workflow = CI_WORKFLOW_PATH.read_text(encoding="utf-8")
    advisory_workflow = ADVISORY_WORKFLOW_PATH.read_text(encoding="utf-8")

    assert "quick-checks:" in ci_workflow
    assert "Run change-aware CI preflight and build" in ci_workflow
    assert 'scripts/verify.sh ci-preflight "${{ github.event.before }}"' in ci_workflow
    assert "Run stable core tests and build" not in ci_workflow
    assert "display-surface:" not in ci_workflow
    assert "submission-surface:" not in ci_workflow
    assert "regression:" not in ci_workflow
    assert "meta-contracts:" not in ci_workflow
    assert "regression:" in advisory_workflow
    assert "meta-contracts:" in advisory_workflow
    assert "family-shared:" in advisory_workflow
    assert "submission-surface:" in advisory_workflow
    assert "display-surface:" in advisory_workflow
    assert "Run regression advisory tests" in advisory_workflow
    assert "Run meta advisory tests" in advisory_workflow
    assert "Run family shared advisory tests" in advisory_workflow
    assert "Run submission-heavy advisory tests" in advisory_workflow
    assert "Run display-heavy advisory tests" in advisory_workflow


def test_workflow_dev_group_matches_uv_sync_contract() -> None:
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
