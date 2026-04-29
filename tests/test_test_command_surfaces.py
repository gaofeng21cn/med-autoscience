from __future__ import annotations

import inspect
import re
import tomllib
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
REQUIRED_OPL_SHARED_RUNTIME_CONTINUITY_COMMIT = "9b02ce03bf079db0257959c3219a1fd2b1ad1364"


def _read(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


def test_makefile_exposes_layered_test_entrypoints() -> None:
    makefile = _read("Makefile")

    assert "test-fast:" in makefile
    assert 'uv run pytest -q -m "not meta and not display_heavy and not submission_heavy and not family"' in makefile
    assert "test-meta:" in makefile
    assert "uv run pytest -q -m meta" in makefile
    assert "test-display:" in makefile
    assert "uv run pytest -q -m display_heavy" in makefile
    assert "test-submission:" in makefile
    assert "uv run pytest -q -m submission_heavy" in makefile
    assert "test-family:" in makefile
    assert (
        "uv run pytest tests/test_family_shared_release.py tests/test_editable_shared_bootstrap.py "
        "tests/test_dev_preflight_contract.py tests/test_dev_preflight.py -q"
    ) in makefile
    assert "test-full:" in makefile
    assert "./scripts/run-parallel-test-lanes.sh full" in makefile


def test_pyproject_registers_meta_display_and_submission_markers() -> None:
    pyproject = tomllib.loads(_read("pyproject.toml"))
    markers = pyproject["tool"]["pytest"]["ini_options"]["markers"]

    assert "meta: repo-tracked docs, workflow, packaging, and command-surface checks" in markers
    assert "display_heavy: display materialization and golden-regression tests that dominate wall-clock time" in markers
    assert "submission_heavy: submission package materialization tests that dominate fast-lane wall-clock time" in markers
    assert "family: family shared boundary tests that depend on cross-repo shared-module topology" in markers


def test_pyproject_pins_opl_harness_shared_to_a_full_commit() -> None:
    pyproject = tomllib.loads(_read("pyproject.toml"))
    dependency = next(
        item
        for item in pyproject["project"]["dependencies"]
        if item.startswith("opl-harness-shared @ ")
    )

    assert re.fullmatch(
        r"opl-harness-shared @ git\+https://github\.com/gaofeng21cn/one-person-lab\.git@[0-9a-f]{40}#subdirectory=python/opl-harness-shared",
        dependency,
    )


@pytest.mark.meta
def test_locked_opl_harness_shared_exports_runtime_continuity_contracts() -> None:
    pyproject = tomllib.loads(_read("pyproject.toml"))
    dependency = next(
        item
        for item in pyproject["project"]["dependencies"]
        if item.startswith("opl-harness-shared @ ")
    )
    lockfile = _read("uv.lock")

    assert REQUIRED_OPL_SHARED_RUNTIME_CONTINUITY_COMMIT in dependency
    assert f"rev={REQUIRED_OPL_SHARED_RUNTIME_CONTINUITY_COMMIT}" in lockfile
    assert f"#{REQUIRED_OPL_SHARED_RUNTIME_CONTINUITY_COMMIT}" in lockfile

    from opl_harness_shared import product_entry_companions, runtime_task_companions

    for helper_name in (
        "build_session_continuity",
        "build_progress_projection",
        "build_artifact_inventory",
    ):
        assert callable(getattr(runtime_task_companions, helper_name))

    manifest_parameters = inspect.signature(
        product_entry_companions.build_family_product_entry_manifest
    ).parameters
    assert {
        "session_continuity",
        "progress_projection",
        "artifact_inventory",
    }.issubset(manifest_parameters)


def test_verify_script_exposes_named_lanes_for_ci_workflows() -> None:
    verify_script = _read("scripts/verify.sh")

    assert 'repo_root="$(git rev-parse --show-toplevel)"' in verify_script
    assert 'cd "${repo_root}"' in verify_script
    assert "run_sanity_checks() {" in verify_script
    assert "git grep -n -I -E '^(<<<<<<< |=======|>>>>>>> |\\|\\|\\|\\|\\|\\|\\| )' -- ." in verify_script
    assert "while IFS= read -r python_file; do" in verify_script
    assert "python_files+=(\"${python_file}\")" in verify_script
    assert "done < <(git ls-files '*.py')" in verify_script
    assert "mapfile" not in verify_script
    assert 'uv run python -m py_compile "${python_files[@]}"' in verify_script
    assert "run_sanity_checks" in verify_script
    assert 'if [[ -z "${lane}" ]]; then' in verify_script
    assert 'if [[ "${lane}" == "meta" ]]; then' in verify_script
    assert 'if [[ "${lane}" == "display" ]]; then' in verify_script
    assert 'if [[ "${lane}" == "submission" ]]; then' in verify_script
    assert 'if [[ "${lane}" == "full" ]]; then' in verify_script
    assert "make test-fast" in verify_script
    assert "make test-meta" in verify_script
    assert "make test-display" in verify_script
    assert "make test-submission" in verify_script
    assert "make test-full" in verify_script


def test_verify_script_runs_sanity_checks_before_default_dispatch() -> None:
    verify_script = _read("scripts/verify.sh")

    assert 'run_sanity_checks\n\nif [[ -z "${lane}" ]]; then' in verify_script


def test_parallel_full_lane_script_covers_all_marker_groups() -> None:
    script = _read("scripts/run-parallel-test-lanes.sh")

    assert 'Usage: $0 full' in script
    assert '"test-fast"' in script
    assert '"test-meta"' in script
    assert '"test-display"' in script
    assert '"test-submission"' in script
    assert '"test-family"' in script
    assert 'make "${lane}"' in script


def test_family_lane_test_files_are_marker_scoped_to_avoid_full_lane_overlap() -> None:
    family_release = _read("tests/test_family_shared_release.py")
    editable_bootstrap = _read("tests/test_editable_shared_bootstrap.py")
    dev_preflight_contract = _read("tests/test_dev_preflight_contract.py")
    dev_preflight = _read("tests/test_dev_preflight.py")

    assert "pytestmark = pytest.mark.family" in family_release
    assert "pytestmark = pytest.mark.family" in editable_bootstrap
    assert "pytestmark = pytest.mark.family" in dev_preflight_contract
    assert "pytestmark = pytest.mark.family" in dev_preflight
