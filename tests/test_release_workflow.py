from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tarfile
import tomllib
import zipfile
from pathlib import Path

from packaging.requirements import Requirement


REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_DIR = REPO_ROOT / ".github" / "workflows"
CI_WORKFLOW_PATH = WORKFLOW_DIR / "ci.yml"
ADVISORY_WORKFLOW_PATH = WORKFLOW_DIR / "advisory.yml"
SENTRUX_ADVISORY_WORKFLOW_PATH = WORKFLOW_DIR / "sentrux-advisory.yml"
RELEASE_WORKFLOW_PATH = WORKFLOW_DIR / "release.yml"
WHITEPAPER_WORKFLOW_PATH = WORKFLOW_DIR / "whitepaper.yml"
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
    non_whitepaper_workflow_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted(WORKFLOW_DIR.glob("*.yml"))
        if path != WHITEPAPER_WORKFLOW_PATH
    )

    assert not RELEASE_WORKFLOW_PATH.exists()
    assert "softprops/action-gh-release" not in workflow_text
    assert "contents: write" not in non_whitepaper_workflow_text
    assert "releases/download" not in workflow_text


def test_whitepaper_workflow_limits_write_permission_to_manual_pages_publish() -> None:
    workflow = WHITEPAPER_WORKFLOW_PATH.read_text(encoding="utf-8")

    assert "contents: write" in workflow
    assert "uses: gaofeng21cn/one-person-lab/.github/workflows/reusable-whitepaper.yml@main" in workflow
    assert "profile: contracts/whitepaper_profile.json" in workflow
    assert "output_name: mas-whitepaper" in workflow
    assert "publish: ${{ github.event_name == 'workflow_dispatch' && inputs.publish }}" in workflow
    assert "softprops/action-gh-release" not in workflow


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
    advisory_job = _workflow_job(advisory_workflow, "advisory")

    assert "Install pandoc and BasicTeX" not in ci_workflow
    assert "brew install pandoc" not in ci_workflow
    assert "brew install --cask basictex" not in ci_workflow
    assert 'echo "/Library/TeX/texbin" >> "${GITHUB_PATH}"' not in ci_workflow
    assert "graphviz" not in ci_workflow
    assert "system_dependencies: none" in advisory_job
    assert "system_dependencies: tex" in advisory_job
    assert "system_dependencies: display" in advisory_job
    assert "brew install pandoc" in advisory_job
    assert "brew install --cask basictex" in advisory_job
    assert "brew install pandoc graphviz pkg-config libxml2 r" in advisory_job
    assert 'echo "/Library/TeX/texbin" >> "${GITHUB_PATH}"' in advisory_job
    assert "PKG_CONFIG_PATH=$(brew --prefix libxml2)/lib/pkgconfig:${PKG_CONFIG_PATH:-}" in advisory_job
    assert "XML_CONFIG=$(brew --prefix libxml2)/bin/xml2-config" in advisory_job


def test_ci_and_advisory_workflows_use_uv_managed_test_environment() -> None:
    ci_workflow = CI_WORKFLOW_PATH.read_text(encoding="utf-8")
    advisory_workflow = ADVISORY_WORKFLOW_PATH.read_text(encoding="utf-8")
    isolated_requirement_jobs = [
        _workflow_job(ci_workflow, "quick-checks"),
        _workflow_job(advisory_workflow, "advisory"),
    ]

    for workflow_job in isolated_requirement_jobs:
        assert (
            'uv export --quiet --frozen --no-emit-project --group dev --format requirements-txt '
            '> "${RUNNER_TEMP}/mas-requirements.txt"'
        ) in workflow_job
        assert "uv sync --frozen --group dev" not in workflow_job
        assert "UV_PROJECT_ENVIRONMENT" not in workflow_job
        assert 'UV_NO_SYNC: "1"' not in workflow_job
    assert "PYTHONPATH: src" in _workflow_job(advisory_workflow, "advisory")
    assert (
        'uv run --isolated --frozen --no-project --with-requirements '
        '"${RUNNER_TEMP}/mas-requirements.txt" python - <<\'PY\''
    ) in advisory_workflow
    assert "enable-cache: true" in ci_workflow
    assert "enable-cache: true" in advisory_workflow
    assert ci_workflow.count("cache-dependency-glob: |") == 1
    assert advisory_workflow.count("cache-dependency-glob: |") == 1
    for workflow in (ci_workflow, advisory_workflow):
        assert "uv.lock" in workflow
        assert "pyproject.toml" in workflow
    assert "pull_request:" in ci_workflow
    assert "github.event.pull_request.base.sha" in ci_workflow
    assert "github.event.before" in ci_workflow
    assert "scripts/verify.sh ci-preflight" in ci_workflow
    assert "scripts/verify.sh meta" not in ci_workflow
    assert re.search(r"run: scripts/verify\.sh\s*$", ci_workflow, flags=re.MULTILINE) is None
    assert "scripts/verify.sh ${{ matrix.lane }}" in advisory_workflow
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
        "ensure-supervision",
        "prepare-external-research",
        "provider live refresh",
        "live literature refresh",
        "artifacts/medical_paper/literature_provider_runtime.json",
        "artifacts/controller_decisions/latest.json",
        "paper/submission_minimal",
    )
    for fragment in forbidden_live_workspace_fragments:
        assert fragment not in ci_workflow


def test_ci_boundary_guards_mas_and_declared_scholarskills_pack_contract_regression() -> None:
    ci_workflow = CI_WORKFLOW_PATH.read_text(encoding="utf-8")
    quick_checks = _workflow_job(ci_workflow, "quick-checks")
    advisory_workflow = ADVISORY_WORKFLOW_PATH.read_text(encoding="utf-8")
    advisory_job = _workflow_job(advisory_workflow, "advisory")

    assert quick_checks.count("actions/checkout@v6") == 2
    assert quick_checks.count("repository:") == 1
    assert "repository: gaofeng21cn/mas-scholar-skills" in quick_checks
    assert "path: .ci/mas-scholar-skills" in quick_checks
    for workflow_job in (quick_checks, advisory_job):
        assert "git clone --depth=1 --filter=blob:none https://github.com/gaofeng21cn/one-person-lab.git ../one-person-lab" in workflow_job
        assert "npm ci --prefix ../one-person-lab --ignore-scripts" in workflow_job
        assert "npm run --prefix ../one-person-lab build" in workflow_job
        assert 'echo "OPL_BIN=$GITHUB_WORKSPACE/../one-person-lab/bin/opl" >> "$GITHUB_ENV"' in workflow_job
        assert 'packages link-framework --agent-root "$GITHUB_WORKSPACE" --json' in workflow_job
        assert workflow_job.index("Checkout and build OPL Framework") < workflow_job.index("Link OPL Framework")
    assert "gaofeng21cn/med-deepscientist" not in ci_workflow
    assert ".ci/med-deepscientist" not in ci_workflow

    forbidden_fragments = (
        "prepare-external-research",
        "provider live refresh",
        "live literature refresh",
        "workspace-cockpit --profile",
        "product-entry-status --profile",
        "study-progress --profile",
        "ensure-supervision",
        "runtime watch",
        "artifacts/controller_decisions/latest.json",
        "paper/submission_minimal",
    )
    for fragment in forbidden_fragments:
        assert fragment not in quick_checks

    assert "scripts/verify.sh ci-preflight" in quick_checks
    assert "make test-medical-paper-ops" in quick_checks
    assert 'scripts/run-build-clean.sh --outdir "${RUNNER_TEMP}/mas-dist"' in quick_checks


def _archive_names(path: Path) -> set[str]:
    if path.suffix == ".whl":
        with zipfile.ZipFile(path) as archive:
            return set(archive.namelist())
    with tarfile.open(path) as archive:
        return set(archive.getnames())


def test_build_packages_tracked_stage_route_contract_without_setup_hook(tmp_path: Path) -> None:
    fixture_root = tmp_path / "sdist-fixture"
    ignored_roots = {
        ".codegraph",
        ".git",
        ".venv",
        ".worktrees",
        "dist",
        "build",
        ".pytest_cache",
        "__pycache__",
    }

    def ignore(_dir: str, names: list[str]) -> set[str]:
        return set(names) & ignored_roots

    shutil.copytree(REPO_ROOT, fixture_root, ignore=ignore)
    assert not (fixture_root / "setup.py").exists()

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "build",
            "--no-isolation",
            "--sdist",
            "--wheel",
            "--outdir",
            str(tmp_path / "dist"),
        ],
        cwd=fixture_root,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    archives = sorted((tmp_path / "dist").iterdir())
    assert {item.suffix for item in archives} == {".gz", ".whl"}
    for archive_path in archives:
        names = _archive_names(archive_path)
        assert any(name.endswith("med_autoscience/resources/stage_route_contract.yaml") for name in names)
        assert not any(name.endswith("/setup.py") or name == "setup.py" for name in names)
        assert not any("/display_pack_repo/" in name or name.endswith("/display_pack_repo") for name in names)


def test_advisory_workflow_only_prepares_study_runtime_analysis_bundle_for_display_lane() -> None:
    ci_workflow = CI_WORKFLOW_PATH.read_text(encoding="utf-8")
    advisory_workflow = ADVISORY_WORKFLOW_PATH.read_text(encoding="utf-8")
    advisory_job = _workflow_job(advisory_workflow, "advisory")

    assert ci_workflow.count("Ensure study runtime analysis bundle") == 0
    assert advisory_workflow.count("Ensure study runtime analysis bundle") == 1
    assert "prepare_analysis_bundle: true" in advisory_job
    assert "prepare_analysis_bundle: false" in advisory_job
    ensure_bundle_step = _workflow_step(advisory_job, "Ensure study runtime analysis bundle")
    assert "if: matrix.prepare_analysis_bundle" in ensure_bundle_step
    assert 'PYTHONDONTWRITEBYTECODE: "1"' in ensure_bundle_step
    assert "Run regression advisory tests" in advisory_workflow
    assert "Run submission-heavy advisory tests" in advisory_workflow
    assert "Run display-heavy advisory tests" in advisory_workflow
    assert "continue-on-error: true" not in ci_workflow
    assert "continue-on-error: true" in advisory_job


def test_advisory_workflow_uses_one_non_blocking_matrix_without_duration_artifacts() -> None:
    advisory_workflow = ADVISORY_WORKFLOW_PATH.read_text(encoding="utf-8")
    advisory_job = _workflow_job(advisory_workflow, "advisory")

    assert "strategy:" in advisory_job
    assert "fail-fast: false" in advisory_job
    assert advisory_workflow.count("lane:") == 5
    assert "duration-history:" not in advisory_workflow
    assert "MAS_TEST_LANE_SUMMARY_PATH" not in advisory_workflow
    assert "summarize-test-lane" not in advisory_workflow
    assert "actions/download-artifact" not in advisory_workflow
    assert "actions/upload-artifact" not in advisory_workflow


def test_ci_and_advisory_workflows_split_stable_push_and_advisory_jobs() -> None:
    ci_workflow = CI_WORKFLOW_PATH.read_text(encoding="utf-8")
    advisory_workflow = ADVISORY_WORKFLOW_PATH.read_text(encoding="utf-8")

    assert "quick-checks:" in ci_workflow
    assert "Run change-aware CI preflight and build" in ci_workflow
    assert "github.event.pull_request.base.sha" in ci_workflow
    assert "github.event.before" in ci_workflow
    assert "scripts/verify.sh ci-preflight" in ci_workflow
    assert "Run stable core tests and build" not in ci_workflow
    assert "advisory:" in advisory_workflow
    assert "display-surface:" not in ci_workflow
    assert "submission-surface:" not in ci_workflow
    assert "regression:" not in ci_workflow
    assert "meta-contracts:" not in ci_workflow
    assert "Run regression advisory tests" in advisory_workflow
    assert "Run meta advisory tests" in advisory_workflow
    assert "Run OPL Framework advisory tests" in advisory_workflow
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


def test_ci_workflow_triggers_on_pull_request_and_push_main_and_development() -> None:
    ci_workflow = CI_WORKFLOW_PATH.read_text(encoding="utf-8")

    assert "pull_request:" in ci_workflow
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
