from __future__ import annotations

import subprocess
import sys
import fnmatch
from pathlib import Path

from tests import conftest as tests_conftest


REPO_ROOT = Path(__file__).resolve().parents[1]


def _collect_only(*paths: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q", *paths],
        check=False,
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
    )


def _current_nested_case_module_paths() -> set[str]:
    product_entry_case_dir = (
        REPO_ROOT
        / "tests"
        / "product_entry_cases"
        / "cockpit_status_and_frontdesk_focus_cases"
    )
    runtime_watch_case_dir = REPO_ROOT / "tests" / "test_runtime_watch_cases"
    nested_paths = [
        *product_entry_case_dir.glob("test_*.py"),
        *runtime_watch_case_dir.glob("*_cases_cases/test_*.py"),
    ]
    return {path.relative_to(REPO_ROOT / "tests").as_posix() for path in nested_paths}


def _is_covered_by_nested_case_ignore(path: str) -> bool:
    return any(
        fnmatch.fnmatch(path, pattern)
        for pattern in tests_conftest.NESTED_CASE_COLLECTION_IGNORE_GLOBS
    )


def test_nested_case_collection_ignore_globs_are_declared() -> None:
    assert set(tests_conftest.NESTED_CASE_COLLECTION_IGNORE_GLOBS) == {
        "product_entry_cases/cockpit_status_and_frontdesk_focus_cases/test_*.py",
        "test_runtime_watch_cases/*_cases_cases/test_*.py",
    }
    assert tests_conftest.collect_ignore_glob == list(
        tests_conftest.NESTED_CASE_COLLECTION_IGNORE_GLOBS
    )


def test_declared_nested_case_families_cover_current_case_module_paths() -> None:
    nested_case_files = _current_nested_case_module_paths()
    uncovered_paths = {path for path in nested_case_files if not _is_covered_by_nested_case_ignore(path)}

    assert nested_case_files
    assert uncovered_paths == set()


def test_submission_minimal_display_surface_uses_write_route_legacy_default() -> None:
    assert (
        "tests/test_submission_minimal_display_surface.py"
        in tests_conftest.WRITE_ROUTE_LEGACY_DEFAULT_FILES
    )


def test_nested_case_modules_are_not_default_collection_surfaces() -> None:
    result = _collect_only(
        "tests/product_entry_cases/cockpit_status_and_frontdesk_focus_cases/test_status_cards.py",
        "tests/test_runtime_watch_cases/runtime_status_cases_cases/test_runtime_activity_projection.py",
        "tests/test_runtime_watch_cases/work_unit_dispatch_cases_cases/test_work_unit_dedupe.py",
    )

    assert result.returncode == 5, result.stdout + result.stderr
    assert "test_status_cards.py::" not in result.stdout
    assert "test_runtime_activity_projection.py::" not in result.stdout
    assert "test_work_unit_dedupe.py::" not in result.stdout


def test_aggregate_collection_surfaces_still_collect_nested_cases() -> None:
    result = _collect_only(
        "tests/product_entry_cases/cockpit_status_and_frontdesk_focus.py",
        "tests/test_runtime_watch.py",
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "tests/product_entry_cases/cockpit_status_and_frontdesk_focus.py::" in result.stdout
    assert "tests/test_runtime_watch.py::" in result.stdout
    assert "::test_workspace_cockpit_markdown_prefers_human_facing_labels" in result.stdout
    assert "::test_watch_runtime_projects_live_worker_stale_artifact_delta_as_recovering" in result.stdout
    assert "::test_work_unit_dedupe_accepts_closed_attempt_result" in result.stdout
    assert "cockpit_status_and_frontdesk_focus_cases/test_" not in result.stdout
    assert "_cases_cases/test_" not in result.stdout


def test_aggregate_collection_surfaces_hold_expected_collection_count() -> None:
    result = _collect_only(
        "tests/product_entry_cases/cockpit_status_and_frontdesk_focus.py",
        "tests/test_runtime_watch.py",
    )

    collected_lines = [line for line in result.stdout.splitlines() if "::" in line]

    assert result.returncode == 0, result.stdout + result.stderr
    assert len(collected_lines) == 126
