from __future__ import annotations

from pathlib import Path

import pytest

from tests.control_plane_route_helpers import writable_route_context


REPO_ROOT = Path(__file__).resolve().parents[1]

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
    "tests/display_ch_golden_regression_cases/test_clinical_baseline_and_transportability_golden.py",
    "tests/display_deg_golden_regression_cases/test_atlas_spatial_trajectory_golden.py",
    "tests/display_deg_golden_regression_cases/test_deg_omics_and_genomic_golden.py",
    "tests/display_deg_golden_regression_cases/test_multiomic_spatial_and_trajectory_golden.py",
    "tests/test_display_layout_qc.py",
    "tests/test_display_surface_materialization.py",
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
    "tests/test_journal_package_controller.py",
    "tests/test_study_delivery_sync.py",
    "tests/test_gate_clearing_batch_cases/test_display_materialization_failures.py",
    "tests/test_gate_clearing_batch_cases/test_outer_loop_controller_action.py",
    "tests/test_gate_clearing_batch_cases/test_planning_and_replay_primitives.py",
    "tests/test_gate_clearing_batch_cases/test_planning_and_replay_recommendations.py",
    "tests/test_gate_clearing_batch_cases/test_planning_and_replay_submission_refresh.py",
    "tests/test_gate_clearing_batch_cases/test_startup_freshness_priority.py",
    "tests/test_gate_clearing_batch_cases/test_transport_sync_normalization.py",
    "tests/test_publication_gate_cases/test_blocker_payload_cases.py",
    "tests/test_publication_gate_cases/test_deterministic_quality_gate_cases.py",
    "tests/test_publication_gate_cases/test_drift_and_state_cases.py",
    "tests/test_publication_gate_cases/test_journal_and_anchor_cases.py",
    "tests/test_publication_gate_cases/test_paper_root_authority_cases.py",
    "tests/test_publication_gate_cases/test_render_and_cli_cases.py",
    "tests/test_publication_gate_cases/test_submission_manifest_paths.py",
    "tests/test_publication_gate_cases/test_supervisor_cases.py",
}

SOAK_OR_GOLDEN_FILES = {
    "tests/test_control_plane_generalization_cases/test_study_soak_replay_cases.py",
    "tests/test_medical_paper_v2_final_soak_proof.py",
    "tests/test_study_truth_kernel_golden_fixtures.py",
}


def _relative_test_path(item: pytest.Item) -> str:
    path = Path(str(item.fspath)).resolve()
    return path.relative_to(REPO_ROOT).as_posix()


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    del config
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
