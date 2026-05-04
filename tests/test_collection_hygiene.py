from __future__ import annotations

import subprocess
import sys
import fnmatch
from pathlib import Path

from tests import conftest as tests_conftest


REPO_ROOT = Path(__file__).resolve().parents[1]

AGGREGATE_ENTRYPOINT_NESTED_CASE_MODULES = {
    "tests/product_entry_cases/cockpit_status_and_frontdesk_focus.py": {
        "tests/product_entry_cases/cockpit_status_and_frontdesk_focus_cases/test_ai_first_operations.py",
        "tests/product_entry_cases/cockpit_status_and_frontdesk_focus_cases/test_autonomy_runtime_control.py",
        "tests/product_entry_cases/cockpit_status_and_frontdesk_focus_cases/test_cross_study_completion.py",
        "tests/product_entry_cases/cockpit_status_and_frontdesk_focus_cases/test_gate_clearing_followthrough.py",
        "tests/product_entry_cases/cockpit_status_and_frontdesk_focus_cases/test_medical_paper_readiness.py",
        "tests/product_entry_cases/cockpit_status_and_frontdesk_focus_cases/test_medical_paper_readiness_v2_actions.py",
        "tests/product_entry_cases/cockpit_status_and_frontdesk_focus_cases/test_quality_lane.py",
        "tests/product_entry_cases/cockpit_status_and_frontdesk_focus_cases/test_status_cards.py",
    },
    "tests/test_runtime_watch.py": {
        "tests/test_runtime_watch_cases/runtime_status_cases_cases/test_runtime_activity_projection.py",
        "tests/test_runtime_watch_cases/work_unit_dispatch_cases_cases/test_control_plane_dispatch_gate.py",
        "tests/test_runtime_watch_cases/work_unit_dispatch_cases_cases/test_outer_loop_context.py",
        "tests/test_runtime_watch_cases/work_unit_dispatch_cases_cases/test_platform_repair_delta.py",
        "tests/test_runtime_watch_cases/work_unit_dispatch_cases_cases/test_redrive_and_platform.py",
        "tests/test_runtime_watch_cases/work_unit_dispatch_cases_cases/test_specificity_dispatch.py",
        "tests/test_runtime_watch_cases/work_unit_dispatch_cases_cases/test_specificity_terminal_preensure.py",
        "tests/test_runtime_watch_cases/work_unit_dispatch_cases_cases/test_work_unit_dedupe.py",
    },
}

NESTED_CASE_REEXPORT_SURFACES = {
    "tests/product_entry_cases/cockpit_status_and_frontdesk_focus.py": (
        AGGREGATE_ENTRYPOINT_NESTED_CASE_MODULES["tests/product_entry_cases/cockpit_status_and_frontdesk_focus.py"]
    ),
    "tests/test_runtime_watch_cases/runtime_status_cases.py": {
        "tests/test_runtime_watch_cases/runtime_status_cases_cases/test_runtime_activity_projection.py",
    },
    "tests/test_runtime_watch_cases/work_unit_dispatch_cases.py": {
        "tests/test_runtime_watch_cases/work_unit_dispatch_cases_cases/test_control_plane_dispatch_gate.py",
        "tests/test_runtime_watch_cases/work_unit_dispatch_cases_cases/test_outer_loop_context.py",
        "tests/test_runtime_watch_cases/work_unit_dispatch_cases_cases/test_platform_repair_delta.py",
        "tests/test_runtime_watch_cases/work_unit_dispatch_cases_cases/test_redrive_and_platform.py",
        "tests/test_runtime_watch_cases/work_unit_dispatch_cases_cases/test_specificity_dispatch.py",
        "tests/test_runtime_watch_cases/work_unit_dispatch_cases_cases/test_specificity_terminal_preensure.py",
        "tests/test_runtime_watch_cases/work_unit_dispatch_cases_cases/test_work_unit_dedupe.py",
    },
}

AGGREGATE_ENTRYPOINT_REEXPORT_SURFACES = {
    "tests/test_runtime_watch.py": {
        "tests/test_runtime_watch_cases/runtime_status_cases.py",
        "tests/test_runtime_watch_cases/work_unit_dispatch_cases.py",
    },
}

REPRESENTATIVE_NESTED_CASES = {
    "tests/product_entry_cases/cockpit_status_and_frontdesk_focus_cases/test_status_cards.py": (
        "test_workspace_cockpit_markdown_prefers_human_facing_labels"
    ),
    "tests/test_runtime_watch_cases/runtime_status_cases_cases/test_runtime_activity_projection.py": (
        "test_watch_runtime_projects_live_worker_stale_artifact_delta_as_recovering"
    ),
    "tests/test_runtime_watch_cases/work_unit_dispatch_cases_cases/test_work_unit_dedupe.py": (
        "test_work_unit_dedupe_accepts_closed_attempt_result"
    ),
}


def _collect_only(*paths: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q", *paths],
        check=False,
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
    )


def _collectable_test_ids(*paths: str) -> set[str]:
    result = _collect_only(*paths)

    assert result.returncode == 0, result.stdout + result.stderr
    return {line for line in result.stdout.splitlines() if "::" in line}


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


def _read(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


def _entrypoint_import_token(entrypoint: str, nested_module: str) -> str:
    entrypoint_parent = Path(entrypoint).parent
    nested_module_path = Path(nested_module).with_suffix("")
    return "." + nested_module_path.relative_to(entrypoint_parent).as_posix().replace("/", ".")


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


def test_declared_nested_case_modules_have_aggregate_entrypoint_coverage() -> None:
    nested_case_files = {"tests/" + path for path in _current_nested_case_module_paths()}
    aggregate_coverage = set().union(*AGGREGATE_ENTRYPOINT_NESTED_CASE_MODULES.values())
    reexport_coverage = set().union(*NESTED_CASE_REEXPORT_SURFACES.values())

    assert nested_case_files == aggregate_coverage
    assert nested_case_files == reexport_coverage


def test_nested_case_reexport_surfaces_explicitly_import_declared_nested_modules() -> None:
    for reexport_surface, nested_modules in NESTED_CASE_REEXPORT_SURFACES.items():
        surface_source = _read(reexport_surface)
        missing_imports = {
            module
            for module in nested_modules
            if _entrypoint_import_token(reexport_surface, module) not in surface_source
        }

        assert missing_imports == set()


def test_aggregate_entrypoints_explicitly_import_nested_case_reexport_surfaces() -> None:
    for entrypoint, reexport_surfaces in AGGREGATE_ENTRYPOINT_REEXPORT_SURFACES.items():
        entrypoint_source = _read(entrypoint)
        missing_imports = {
            surface
            for surface in reexport_surfaces
            if _entrypoint_import_token(entrypoint, surface) not in entrypoint_source
        }

        assert missing_imports == set()


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
    collected_ids = _collectable_test_ids(
        "tests/product_entry_cases/cockpit_status_and_frontdesk_focus.py",
        "tests/test_runtime_watch.py",
    )
    collected_output = "\n".join(collected_ids)

    for test_name in REPRESENTATIVE_NESTED_CASES.values():
        assert f"::{test_name}" in collected_output
    assert "tests/product_entry_cases/cockpit_status_and_frontdesk_focus.py::" in collected_output
    assert "tests/test_runtime_watch.py::" in collected_output
    assert "cockpit_status_and_frontdesk_focus_cases/test_" not in collected_output
    assert "_cases_cases/test_" not in collected_output


def test_representative_nested_case_modules_only_collect_through_aggregate_entrypoints() -> None:
    direct_result = _collect_only(*REPRESENTATIVE_NESTED_CASES)
    aggregate_collected_ids = _collectable_test_ids(
        "tests/product_entry_cases/cockpit_status_and_frontdesk_focus.py",
        "tests/test_runtime_watch.py",
    )
    aggregate_output = "\n".join(aggregate_collected_ids)

    assert direct_result.returncode == 5, direct_result.stdout + direct_result.stderr
    for nested_module, test_name in REPRESENTATIVE_NESTED_CASES.items():
        assert f"{nested_module}::" not in direct_result.stdout
        assert f"::{test_name}" not in direct_result.stdout
        assert f"::{test_name}" in aggregate_output


def test_aggregate_collection_surfaces_hold_expected_collection_count() -> None:
    collected_lines = _collectable_test_ids(
        "tests/product_entry_cases/cockpit_status_and_frontdesk_focus.py",
        "tests/test_runtime_watch.py",
    )

    assert len(collected_lines) == 127
