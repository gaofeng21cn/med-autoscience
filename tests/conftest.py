from __future__ import annotations

import fnmatch
from pathlib import Path

import pytest

from tests.control_plane_route_helpers import writable_route_context


REPO_ROOT = Path(__file__).resolve().parents[1]

NESTED_CASE_COLLECTION_IGNORE_GLOBS = (
    "product_entry_cases/cockpit_status_and_entry_status_focus_cases/test_*.py",
    "domain_action_request_materializer_cases/test_paper_recovery_owner_callable_cases/test_*.py",
    "test_cli_cases/ai_reviewer_publication_eval_command_cases/test_*.py",
    "test_adapter_retirement_boundary_cases/runtime_surface_no_authority_violation_guards_cases/test_*.py",
)

collect_ignore_glob = list(NESTED_CASE_COLLECTION_IGNORE_GLOBS)

META_FILES = {
    "tests/controller_charter/test_controller_charter_module_contract.py",
    "tests/eval_hygiene/test_eval_hygiene_module_contract.py",
    "tests/integration/test_monorepo_scaffold_boundaries.py",
    "tests/runtime/test_runtime_module_contract.py",
    "tests/test_stage_route_assets.py",
    "tests/test_codex_plugin.py",
    "tests/test_codex_plugin_installer.py",
    "tests/test_codex_plugin_installer_script.py",
    "tests/test_codex_plugin_scaffold.py",
    "tests/test_med_deepscientist_repo_manifest.py",
    "tests/test_python_environment_contract.py",
    "tests/test_release_installer.py",
    "tests/test_release_metadata.py",
    "tests/test_release_workflow.py",
    "tests/test_workspace_contracts.py",
}

DISPLAY_HEAVY_FILES = {
    "tests/test_display_ab_golden_regression.py",
    "tests/test_display_abh_golden_regression.py",
    "tests/test_display_ch_golden_regression.py",
    "tests/test_display_deg_golden_regression.py",
    "tests/test_display_f_golden_regression.py",
    "tests/test_display_layout_qc.py",
    "tests/test_display_surface_materialization.py",
    "tests/test_display_surface_materialization_cli.py",
    "tests/test_medical_startup_contract_support.py",
    "tests/test_submission_minimal_display_surface.py",
}

FAMILY_FILES = {
    "tests/test_dev_preflight.py",
    "tests/test_dev_preflight_contract.py",
    "tests/test_editable_shared_bootstrap.py",
    "tests/test_family_shared_release.py",
    "tests/test_opl_agent_lab_longline_migration.py",
}

MATERIALIZATION_HEAVY_FILES = {
    "tests/test_fast_lane_executor.py",
    "tests/test_gate_clearing_batch.py",
    "tests/test_journal_package_controller.py",
    "tests/test_publication_gate.py",
    "tests/test_quality_repair_batch.py",
    "tests/test_study_delivery_sync.py",
}

SOAK_OR_GOLDEN_FILES = {
    "tests/test_control_plane_generalization_cases/test_study_soak_replay_cases.py",
    "tests/test_mas_mds_longitudinal_soak.py",
    "tests/test_medical_paper_v2_final_soak_proof.py",
    "tests/test_multistudy_soak_proof.py",
    "tests/test_open_auto_research_soak.py",
    "tests/test_real_paper_ai_first_soak.py",
    "tests/test_real_paper_autonomy_soak_inventory.py",
    "tests/test_real_workspace_soak_monitor.py",
    "tests/test_storage_governance_read_only_soak.py",
    "tests/test_study_truth_kernel_golden_fixtures.py",
}


def _relative_test_path(item: pytest.Item) -> str:
    path = Path(str(item.fspath)).resolve()
    return path.relative_to(REPO_ROOT).as_posix()


def _is_nested_case_collection_path(relative_test_path: str) -> bool:
    relative_to_tests = relative_test_path.removeprefix("tests/")
    return any(fnmatch.fnmatch(relative_to_tests, pattern) for pattern in NESTED_CASE_COLLECTION_IGNORE_GLOBS)


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    del config
    nested_case_items = [item for item in items if _is_nested_case_collection_path(_relative_test_path(item))]
    if nested_case_items:
        items[:] = [item for item in items if item not in nested_case_items]
    for item in items:
        relative_path = _relative_test_path(item)
        if relative_path in META_FILES:
            item.add_marker(pytest.mark.meta)
        if relative_path in DISPLAY_HEAVY_FILES:
            item.add_marker(pytest.mark.display_heavy)
        if relative_path in FAMILY_FILES:
            item.add_marker(pytest.mark.family)
        if relative_path in MATERIALIZATION_HEAVY_FILES:
            item.add_marker(pytest.mark.materialization_heavy)
        if relative_path in SOAK_OR_GOLDEN_FILES:
            item.add_marker(pytest.mark.soak_or_golden)


@pytest.fixture
def writable_authority_route_context() -> dict[str, object]:
    return writable_route_context()
