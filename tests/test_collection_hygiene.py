from __future__ import annotations

import ast
import json
import subprocess
import sys
import fnmatch
from pathlib import Path

from tests import conftest as tests_conftest


REPO_ROOT = Path(__file__).resolve().parents[1]

AGGREGATE_ENTRYPOINT_COLLECTION_COUNT_FLOOR = 132
NESTED_STRUCTURE_PARENT_NAMES = {"cases", "modules", "parts"}
TEST_LANE_MANIFEST_PATH = REPO_ROOT / "contracts" / "test-lane-manifest.json"

AGGREGATE_ENTRYPOINT_NESTED_CASE_MODULES = {
    "tests/product_entry_cases/cockpit_status_and_entry_status_focus.py": {
        "tests/product_entry_cases/cockpit_status_and_entry_status_focus_cases/test_ai_first_operations.py",
        "tests/product_entry_cases/cockpit_status_and_entry_status_focus_cases/test_autonomy_runtime_control.py",
        "tests/product_entry_cases/cockpit_status_and_entry_status_focus_cases/test_cross_study_completion.py",
        "tests/product_entry_cases/cockpit_status_and_entry_status_focus_cases/test_gate_clearing_followthrough.py",
        "tests/product_entry_cases/cockpit_status_and_entry_status_focus_cases/test_medical_paper_ops_health.py",
        "tests/product_entry_cases/cockpit_status_and_entry_status_focus_cases/test_medical_paper_readiness.py",
        "tests/product_entry_cases/cockpit_status_and_entry_status_focus_cases/test_medical_paper_readiness_v2_actions.py",
        "tests/product_entry_cases/cockpit_status_and_entry_status_focus_cases/test_projection_error_isolation.py",
        "tests/product_entry_cases/cockpit_status_and_entry_status_focus_cases/test_quality_lane.py",
        "tests/product_entry_cases/cockpit_status_and_entry_status_focus_cases/test_status_cards.py",
    },
    "tests/test_cli_cases/owner_route_handoff_command.py": {
        "tests/test_cli_cases/owner_route_handoff_command_cases/test_paper_recovery_successor_dispatch_cases.py",
    },
    "tests/test_domain_health_diagnostic.py": {
        "tests/test_domain_health_diagnostic_cases/runtime_status_cases_cases/test_ai_doctor_autonomy_repair.py",
        "tests/test_domain_health_diagnostic_cases/runtime_status_cases_cases/test_ai_doctor_autonomy_repair_lifecycle.py",
        "tests/test_domain_health_diagnostic_cases/runtime_status_cases_cases/test_live_work_unit_autonomy_repair.py",
        "tests/test_domain_health_diagnostic_cases/runtime_status_cases_cases/test_ai_doctor_autonomy_repair_runtime_recovery.py",
        "tests/test_domain_health_diagnostic_cases/runtime_status_cases_cases/test_ai_doctor_autonomy_repair_supervisor_only.py",
        "tests/test_domain_health_diagnostic_cases/runtime_status_cases_cases/test_runtime_activity_projection.py",
        "tests/test_domain_health_diagnostic_cases/runtime_status_cases_cases/test_runtime_protocol_and_efficiency.py",
        "tests/test_domain_health_diagnostic_cases/runtime_status_cases_cases/test_publication_gate_handoff.py",
        "tests/test_domain_health_diagnostic_cases/runtime_status_cases_cases/test_controller_dedup_and_blockers.py",
        "tests/test_domain_health_diagnostic_cases/runtime_status_cases_cases/test_managed_study_projection.py",
        "tests/test_domain_health_diagnostic_cases/supervisor_and_progress_cases_cases/test_alias_and_family_companion.py",
        "tests/test_domain_health_diagnostic_cases/supervisor_and_progress_cases_cases/test_focused_scope.py",
        "tests/test_domain_health_diagnostic_cases/supervisor_and_progress_cases_cases/test_managed_recovery_holds.py",
        "tests/test_domain_health_diagnostic_cases/supervisor_and_progress_cases_cases/test_managed_recovery_redrive.py",
        "tests/test_domain_health_diagnostic_cases/supervisor_and_progress_cases_cases/test_materialized_dispatch_blockers.py",
        "tests/test_domain_health_diagnostic_cases/supervisor_and_progress_cases_cases/test_provider_admission_probe.py",
        "tests/test_domain_health_diagnostic_cases/supervisor_and_progress_cases_cases/test_supervision_escalation.py",
        "tests/test_domain_health_diagnostic_cases/work_unit_dispatch_cases_cases/test_control_plane_dispatch_gate.py",
        "tests/test_domain_health_diagnostic_cases/work_unit_dispatch_cases_cases/test_control_plane_dispatch_runtime_recovery.py",
        "tests/test_domain_health_diagnostic_cases/work_unit_dispatch_cases_cases/test_outer_loop_context.py",
        "tests/test_domain_health_diagnostic_cases/work_unit_dispatch_cases_cases/test_opl_runtime_handoff_delta.py",
        "tests/test_domain_health_diagnostic_cases/work_unit_dispatch_cases_cases/test_redrive_and_platform.py",
        "tests/test_domain_health_diagnostic_cases/work_unit_dispatch_cases_cases/test_specificity_dispatch.py",
        "tests/test_domain_health_diagnostic_cases/work_unit_dispatch_cases_cases/test_specificity_terminal_preensure.py",
        "tests/test_domain_health_diagnostic_cases/work_unit_dispatch_cases_cases/test_user_pause_outer_loop_block.py",
        "tests/test_domain_health_diagnostic_cases/work_unit_dispatch_cases_cases/test_work_unit_dedupe.py",
    },
}

NESTED_CASE_REEXPORT_SURFACES = {
    "tests/product_entry_cases/cockpit_status_and_entry_status_focus.py": (
        AGGREGATE_ENTRYPOINT_NESTED_CASE_MODULES["tests/product_entry_cases/cockpit_status_and_entry_status_focus.py"]
    ),
    "tests/test_cli_cases/owner_route_handoff_command.py": (
        AGGREGATE_ENTRYPOINT_NESTED_CASE_MODULES["tests/test_cli_cases/owner_route_handoff_command.py"]
    ),
    "tests/test_domain_health_diagnostic_cases/runtime_status_cases.py": {
        "tests/test_domain_health_diagnostic_cases/runtime_status_cases_cases/test_ai_doctor_autonomy_repair.py",
        "tests/test_domain_health_diagnostic_cases/runtime_status_cases_cases/test_ai_doctor_autonomy_repair_lifecycle.py",
        "tests/test_domain_health_diagnostic_cases/runtime_status_cases_cases/test_live_work_unit_autonomy_repair.py",
        "tests/test_domain_health_diagnostic_cases/runtime_status_cases_cases/test_ai_doctor_autonomy_repair_runtime_recovery.py",
        "tests/test_domain_health_diagnostic_cases/runtime_status_cases_cases/test_ai_doctor_autonomy_repair_supervisor_only.py",
        "tests/test_domain_health_diagnostic_cases/runtime_status_cases_cases/test_runtime_activity_projection.py",
        "tests/test_domain_health_diagnostic_cases/runtime_status_cases_cases/test_runtime_protocol_and_efficiency.py",
        "tests/test_domain_health_diagnostic_cases/runtime_status_cases_cases/test_publication_gate_handoff.py",
        "tests/test_domain_health_diagnostic_cases/runtime_status_cases_cases/test_controller_dedup_and_blockers.py",
        "tests/test_domain_health_diagnostic_cases/runtime_status_cases_cases/test_managed_study_projection.py",
    },
    "tests/test_domain_health_diagnostic_cases/supervisor_and_progress_cases.py": {
        "tests/test_domain_health_diagnostic_cases/supervisor_and_progress_cases_cases/test_alias_and_family_companion.py",
        "tests/test_domain_health_diagnostic_cases/supervisor_and_progress_cases_cases/test_focused_scope.py",
        "tests/test_domain_health_diagnostic_cases/supervisor_and_progress_cases_cases/test_managed_recovery_holds.py",
        "tests/test_domain_health_diagnostic_cases/supervisor_and_progress_cases_cases/test_managed_recovery_redrive.py",
        "tests/test_domain_health_diagnostic_cases/supervisor_and_progress_cases_cases/test_materialized_dispatch_blockers.py",
        "tests/test_domain_health_diagnostic_cases/supervisor_and_progress_cases_cases/test_provider_admission_probe.py",
        "tests/test_domain_health_diagnostic_cases/supervisor_and_progress_cases_cases/test_supervision_escalation.py",
    },
    "tests/test_domain_health_diagnostic_cases/work_unit_dispatch_cases.py": {
        "tests/test_domain_health_diagnostic_cases/work_unit_dispatch_cases_cases/test_control_plane_dispatch_gate.py",
        "tests/test_domain_health_diagnostic_cases/work_unit_dispatch_cases_cases/test_control_plane_dispatch_runtime_recovery.py",
        "tests/test_domain_health_diagnostic_cases/work_unit_dispatch_cases_cases/test_outer_loop_context.py",
        "tests/test_domain_health_diagnostic_cases/work_unit_dispatch_cases_cases/test_opl_runtime_handoff_delta.py",
        "tests/test_domain_health_diagnostic_cases/work_unit_dispatch_cases_cases/test_redrive_and_platform.py",
        "tests/test_domain_health_diagnostic_cases/work_unit_dispatch_cases_cases/test_specificity_dispatch.py",
        "tests/test_domain_health_diagnostic_cases/work_unit_dispatch_cases_cases/test_specificity_terminal_preensure.py",
        "tests/test_domain_health_diagnostic_cases/work_unit_dispatch_cases_cases/test_user_pause_outer_loop_block.py",
        "tests/test_domain_health_diagnostic_cases/work_unit_dispatch_cases_cases/test_work_unit_dedupe.py",
    },
}

AGGREGATE_ENTRYPOINT_REEXPORT_SURFACES = {
    "tests/test_domain_health_diagnostic.py": {
        "tests/test_domain_health_diagnostic_cases/runtime_status_cases.py",
        "tests/test_domain_health_diagnostic_cases/supervisor_and_progress_cases.py",
        "tests/test_domain_health_diagnostic_cases/work_unit_dispatch_cases.py",
    },
}

REPRESENTATIVE_NESTED_CASES = {
    "tests/product_entry_cases/cockpit_status_and_entry_status_focus_cases/test_status_cards.py": (
        "test_workspace_cockpit_markdown_prefers_human_facing_labels"
    ),
    "tests/test_domain_health_diagnostic_cases/runtime_status_cases_cases/test_runtime_activity_projection.py": (
        "test_watch_runtime_projects_live_worker_stale_artifact_delta_as_recovering"
    ),
    "tests/test_domain_health_diagnostic_cases/work_unit_dispatch_cases_cases/test_work_unit_dedupe.py": (
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


def _current_nested_structure_module_paths() -> set[str]:
    return {
        path.relative_to(REPO_ROOT / "tests").as_posix()
        for path in (REPO_ROOT / "tests").rglob("test_*.py")
        if _is_nested_structure_module_path(path.relative_to(REPO_ROOT / "tests"))
    }


def _current_nested_case_module_paths() -> set[str]:
    return {
        path
        for path in _current_nested_structure_module_paths()
        if _is_covered_by_nested_case_ignore(path)
    }


def _read(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


def _test_lane_manifest() -> dict[str, object]:
    return json.loads(TEST_LANE_MANIFEST_PATH.read_text(encoding="utf-8"))


def _is_nested_structure_module_path(relative_path: Path) -> bool:
    structural_parent_count = sum(
        part.endswith("_cases")
        or part.endswith("_cases_cases")
        or part in NESTED_STRUCTURE_PARENT_NAMES
        for part in relative_path.parts[:-1]
    )
    return structural_parent_count >= 2


def _entrypoint_import_token(entrypoint: str, nested_module: str) -> str:
    entrypoint_parent = Path(entrypoint).parent
    nested_module_path = Path(nested_module).with_suffix("")
    return "." + nested_module_path.relative_to(entrypoint_parent).as_posix().replace("/", ".")


def _is_covered_by_nested_case_ignore(path: str) -> bool:
    return any(
        fnmatch.fnmatch(path, pattern)
        for pattern in tests_conftest.NESTED_CASE_COLLECTION_IGNORE_GLOBS
    )


def _is_marker_managed_nested_path(path: str) -> bool:
    relative_test_path = "tests/" + path
    return (
        relative_test_path in tests_conftest.META_FILES
        or relative_test_path in tests_conftest.DISPLAY_HEAVY_FILES
        or relative_test_path in tests_conftest.FAMILY_FILES
        or relative_test_path in tests_conftest.WRITE_ROUTE_LEGACY_DEFAULT_FILES
        or relative_test_path.startswith(tests_conftest.WRITE_ROUTE_LEGACY_DEFAULT_PREFIXES)
        or "pytestmark = pytest.mark." in _read(relative_test_path)
    )


def _test_function_names(relative_path: str) -> set[str]:
    tree = ast.parse(_read(relative_path), filename=relative_path)
    return {
        node.name
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name.startswith("test_")
    }


def _collected_test_function_names(collected_ids: set[str]) -> set[str]:
    return {
        collected_id.rsplit("::", maxsplit=1)[-1].split("[", maxsplit=1)[0]
        for collected_id in collected_ids
    }


def _format_paths(paths: set[str]) -> str:
    if not paths:
        return "  - <none>"
    return "\n".join(f"  - {path}" for path in sorted(paths))


def _nested_case_ignore_failure_message(uncovered_paths: set[str]) -> str:
    configured_globs = "\n".join(
        f"  - {pattern}" for pattern in tests_conftest.NESTED_CASE_COLLECTION_IGNORE_GLOBS
    )
    return (
        "Nested case modules must stay out of default pytest collection.\n"
        "Uncovered nested case module paths:\n"
        f"{_format_paths(uncovered_paths)}\n"
        "Current tests/conftest.py NESTED_CASE_COLLECTION_IGNORE_GLOBS:\n"
        f"{configured_globs}\n"
        "If these paths are a new aggregate-managed family, add a precise family glob to "
        "tests/conftest.py and add the modules to AGGREGATE_ENTRYPOINT_NESTED_CASE_MODULES plus "
        "NESTED_CASE_REEXPORT_SURFACES in tests/test_collection_hygiene.py. If they should be "
        "default-collected tests, keep them outside nested case directories and rely on normal marker "
        "management instead."
    )


def _nested_structure_classification_failure_message(unclassified_paths: set[str]) -> str:
    configured_globs = "\n".join(
        f"  - {pattern}" for pattern in tests_conftest.NESTED_CASE_COLLECTION_IGNORE_GLOBS
    )
    return (
        "Nested structure test modules must be explicitly classified.\n"
        "Unclassified nested module paths:\n"
        f"{_format_paths(unclassified_paths)}\n"
        "Current nested ignore surface:\n"
        f"{configured_globs}\n"
        "Aggregate-managed nested families must add a precise family glob to "
        "tests/conftest.py and declare aggregate/re-export coverage here. "
        "Default-collected nested families must be marker-managed through tests/conftest.py "
        "or module-level pytestmark."
    )


def _coverage_failure_message(
    *,
    surface_name: str,
    missing_paths: set[str],
    stale_paths: set[str],
    instruction: str,
) -> str:
    return (
        f"Nested case module {surface_name} coverage is out of sync.\n"
        "Missing nested case module paths:\n"
        f"{_format_paths(missing_paths)}\n"
        "Stale declared paths:\n"
        f"{_format_paths(stale_paths)}\n"
        f"{instruction}"
    )


def _missing_imports_failure_message(
    *,
    surface_kind: str,
    surface: str,
    missing_imports: set[str],
) -> str:
    missing_tokens = {
        f"{path} -> {_entrypoint_import_token(surface, path)}"
        for path in missing_imports
    }
    return (
        f"{surface_kind} is missing explicit nested-case imports: {surface}\n"
        "Missing module paths and expected import tokens:\n"
        f"{_format_paths(missing_tokens)}\n"
        "Add explicit re-export imports for these paths, or remove the path from the declared "
        "surface if the module is no longer part of that family."
    )


def _aggregate_collection_failure_message(
    *,
    entrypoint: str,
    missing_test_names: set[str],
) -> str:
    return (
        f"Aggregate entrypoint coverage shrank for {entrypoint}.\n"
        "Missing nested case test names:\n"
        f"{_format_paths(missing_test_names)}\n"
        "Keep the aggregate entrypoint importing every declared nested case module, or update "
        "AGGREGATE_ENTRYPOINT_NESTED_CASE_MODULES after deleting/moving the module."
    )


def test_nested_case_collection_ignore_globs_are_declared() -> None:
    assert set(tests_conftest.NESTED_CASE_COLLECTION_IGNORE_GLOBS) == {
        "product_entry_cases/cockpit_status_and_entry_status_focus_cases/test_*.py",
        "test_cli_cases/owner_route_handoff_command_cases/test_*.py",
        "test_domain_health_diagnostic_cases/*_cases_cases/test_*.py",
    }
    assert tests_conftest.collect_ignore_glob == list(
        tests_conftest.NESTED_CASE_COLLECTION_IGNORE_GLOBS
    )


def test_test_lane_manifest_declares_known_overlap_policy() -> None:
    manifest = _test_lane_manifest()

    assert manifest["schema_version"] == 1
    assert manifest["focused_lanes"]["control-plane"] == {
        "kind": "focused_owner_surface_gate",
        "overlap_policy": "allowed_with_regression",
    }
    assert manifest["lanes"]["smoke"]["overlap_policy"] == "entry_contract_only"


def test_family_files_are_not_meta_owned() -> None:
    family_files = {
        "tests/test_dev_preflight.py",
        "tests/test_dev_preflight_contract.py",
        "tests/test_editable_shared_bootstrap.py",
        "tests/test_family_shared_release.py",
    }

    assert family_files.isdisjoint(tests_conftest.META_FILES)


def test_nested_structure_modules_are_explicitly_classified() -> None:
    nested_structure_files = _current_nested_structure_module_paths()
    unclassified_paths = {
        path
        for path in nested_structure_files
        if not _is_covered_by_nested_case_ignore(path) and not _is_marker_managed_nested_path(path)
    }

    assert nested_structure_files
    assert unclassified_paths == set(), _nested_structure_classification_failure_message(unclassified_paths)


def test_declared_nested_case_modules_have_aggregate_entrypoint_coverage() -> None:
    nested_case_files = {"tests/" + path for path in _current_nested_case_module_paths()}
    aggregate_coverage = set().union(*AGGREGATE_ENTRYPOINT_NESTED_CASE_MODULES.values())
    reexport_coverage = set().union(*NESTED_CASE_REEXPORT_SURFACES.values())

    assert nested_case_files == aggregate_coverage, _coverage_failure_message(
        surface_name="aggregate entrypoint",
        missing_paths=nested_case_files - aggregate_coverage,
        stale_paths=aggregate_coverage - nested_case_files,
        instruction=(
            "Add missing paths to AGGREGATE_ENTRYPOINT_NESTED_CASE_MODULES under the aggregate "
            "entrypoint that owns the family, or remove stale paths after deleting/moving modules."
        ),
    )
    assert nested_case_files == reexport_coverage, _coverage_failure_message(
        surface_name="re-export surface",
        missing_paths=nested_case_files - reexport_coverage,
        stale_paths=reexport_coverage - nested_case_files,
        instruction=(
            "Add missing paths to NESTED_CASE_REEXPORT_SURFACES under the re-export module that "
            "should import them, then add the matching explicit import in that module."
        ),
        )


def test_aggregate_entrypoints_collect_all_declared_nested_case_tests() -> None:
    for entrypoint, nested_modules in AGGREGATE_ENTRYPOINT_NESTED_CASE_MODULES.items():
        expected_test_names = set().union(*(_test_function_names(module) for module in nested_modules))
        collected_names = _collected_test_function_names(_collectable_test_ids(entrypoint))
        missing_test_names = expected_test_names - collected_names

        assert expected_test_names
        assert missing_test_names == set(), _aggregate_collection_failure_message(
            entrypoint=entrypoint,
            missing_test_names=missing_test_names,
        )


def test_nested_case_reexport_surfaces_explicitly_import_declared_nested_modules() -> None:
    for reexport_surface, nested_modules in NESTED_CASE_REEXPORT_SURFACES.items():
        surface_source = _read(reexport_surface)
        missing_imports = {
            module
            for module in nested_modules
            if _entrypoint_import_token(reexport_surface, module) not in surface_source
        }

        assert missing_imports == set(), _missing_imports_failure_message(
            surface_kind="Nested case re-export surface",
            surface=reexport_surface,
            missing_imports=missing_imports,
        )


def test_aggregate_entrypoints_explicitly_import_nested_case_reexport_surfaces() -> None:
    for entrypoint, reexport_surfaces in AGGREGATE_ENTRYPOINT_REEXPORT_SURFACES.items():
        entrypoint_source = _read(entrypoint)
        missing_imports = {
            surface
            for surface in reexport_surfaces
            if _entrypoint_import_token(entrypoint, surface) not in entrypoint_source
        }

        assert missing_imports == set(), _missing_imports_failure_message(
            surface_kind="Aggregate entrypoint",
            surface=entrypoint,
            missing_imports=missing_imports,
        )


def test_submission_minimal_display_surface_uses_write_route_legacy_default() -> None:
    assert (
        "tests/test_submission_minimal_display_surface.py"
        in tests_conftest.WRITE_ROUTE_LEGACY_DEFAULT_FILES
    )


def test_nested_case_modules_are_not_default_collection_surfaces() -> None:
    nested_case_modules = {"tests/" + path for path in _current_nested_case_module_paths()}
    result = _collect_only(*sorted(nested_case_modules))

    assert nested_case_modules
    assert result.returncode == 5, result.stdout + result.stderr
    for nested_case_module in nested_case_modules:
        assert f"{nested_case_module}::" not in result.stdout


def test_aggregate_collection_surfaces_still_collect_nested_cases() -> None:
    collected_ids = _collectable_test_ids(
        "tests/product_entry_cases/cockpit_status_and_entry_status_focus.py",
        "tests/test_domain_health_diagnostic.py",
    )
    collected_output = "\n".join(collected_ids)

    for test_name in REPRESENTATIVE_NESTED_CASES.values():
        assert f"::{test_name}" in collected_output
    assert "tests/product_entry_cases/cockpit_status_and_entry_status_focus.py::" in collected_output
    assert "tests/test_domain_health_diagnostic.py::" in collected_output
    assert "cockpit_status_and_entry_status_focus_cases/test_" not in collected_output
    assert "_cases_cases/test_" not in collected_output


def test_representative_nested_case_modules_only_collect_through_aggregate_entrypoints() -> None:
    direct_result = _collect_only(*REPRESENTATIVE_NESTED_CASES)
    aggregate_collected_ids = _collectable_test_ids(
        "tests/product_entry_cases/cockpit_status_and_entry_status_focus.py",
        "tests/test_domain_health_diagnostic.py",
    )
    aggregate_output = "\n".join(aggregate_collected_ids)

    assert direct_result.returncode == 5, direct_result.stdout + direct_result.stderr
    for nested_module, test_name in REPRESENTATIVE_NESTED_CASES.items():
        assert f"{nested_module}::" not in direct_result.stdout
        assert f"::{test_name}" not in direct_result.stdout
        assert f"::{test_name}" in aggregate_output


def test_aggregate_collection_surfaces_keep_collection_count_above_known_coverage_floor() -> None:
    collected_lines = _collectable_test_ids(
        "tests/product_entry_cases/cockpit_status_and_entry_status_focus.py",
        "tests/test_domain_health_diagnostic.py",
    )

    assert len(collected_lines) >= AGGREGATE_ENTRYPOINT_COLLECTION_COUNT_FLOOR
