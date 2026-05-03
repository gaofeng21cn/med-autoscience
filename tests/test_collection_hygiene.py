from __future__ import annotations

import subprocess
import sys
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


def test_nested_case_collection_ignore_globs_are_declared() -> None:
    assert set(tests_conftest.NESTED_CASE_COLLECTION_IGNORE_GLOBS) == {
        "product_entry_cases/cockpit_status_and_frontdesk_focus_cases/test_*.py",
        "test_runtime_watch_cases/*_cases_cases/test_*.py",
    }
    assert tests_conftest.collect_ignore_glob == list(
        tests_conftest.NESTED_CASE_COLLECTION_IGNORE_GLOBS
    )


def test_submission_minimal_display_surface_uses_write_route_legacy_default() -> None:
    assert (
        "tests/test_submission_minimal_display_surface.py"
        in tests_conftest.WRITE_ROUTE_LEGACY_DEFAULT_FILES
    )


def test_nested_case_modules_are_not_default_collection_surfaces() -> None:
    result = _collect_only(
        "tests/product_entry_cases/cockpit_status_and_frontdesk_focus_cases/test_status_cards.py",
        "tests/test_runtime_watch_cases/work_unit_dispatch_cases_cases/test_work_unit_dedupe.py",
    )

    assert result.returncode == 5, result.stdout + result.stderr
    assert "test_status_cards.py::" not in result.stdout
    assert "test_work_unit_dedupe.py::" not in result.stdout


def test_aggregate_collection_surfaces_still_collect_nested_cases() -> None:
    result = _collect_only(
        "tests/product_entry_cases/cockpit_status_and_frontdesk_focus.py",
        "tests/test_runtime_watch.py",
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "tests/product_entry_cases/cockpit_status_and_frontdesk_focus.py::" in result.stdout
    assert "tests/test_runtime_watch.py::" in result.stdout
    assert "cockpit_status_and_frontdesk_focus_cases/test_" not in result.stdout
    assert "_cases_cases/test_" not in result.stdout
