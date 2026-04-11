from __future__ import annotations

from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]

META_FILES = {
    "tests/controller_charter/test_controller_charter_module_contract.py",
    "tests/eval_hygiene/test_eval_hygiene_module_contract.py",
    "tests/integration/test_monorepo_scaffold_boundaries.py",
    "tests/runtime/test_runtime_module_contract.py",
    "tests/test_agent_entry_assets.py",
    "tests/test_codex_plugin.py",
    "tests/test_codex_plugin_installer.py",
    "tests/test_codex_plugin_installer_script.py",
    "tests/test_codex_plugin_scaffold.py",
    "tests/test_dev_preflight.py",
    "tests/test_dev_preflight_contract.py",
    "tests/test_integration_harness_activation_package.py",
    "tests/test_manual_runtime_stabilization_docs.py",
    "tests/test_med_deepscientist_repo_manifest.py",
    "tests/test_python_environment_contract.py",
    "tests/test_release_installer.py",
    "tests/test_release_metadata.py",
    "tests/test_release_workflow.py",
    "tests/test_runtime_contract_docs.py",
    "tests/test_runtime_supervision_docs.py",
    "tests/test_study_progress_docs.py",
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
