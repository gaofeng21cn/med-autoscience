from __future__ import annotations

import importlib


def test_plan_commands_for_categories_deduplicates_results() -> None:
    module = importlib.import_module("med_autoscience.dev_preflight_contract")

    commands = module.plan_commands_for_categories(
        ("workflow_surface", "workflow_surface", "codex_plugin_surface")
    )

    assert commands.count("scripts/run-pytest-clean.sh tests/test_release_workflow.py -q") == 1
    assert "scripts/run-pytest-clean.sh tests/test_codex_plugin.py -q" in commands
    assert "scripts/run-pytest-clean.sh tests/test_codex_plugin_scaffold.py -q" in commands


def test_plan_commands_for_documentation_review_only_do_not_run_pytest() -> None:
    module = importlib.import_module("med_autoscience.dev_preflight_contract")

    commands = module.plan_commands_for_categories((module.DOCUMENTATION_REVIEW_CATEGORY,))

    assert commands == []


def test_plan_commands_for_optional_provider_archive_audit_surface_include_gate_proofs() -> None:
    module = importlib.import_module("med_autoscience.dev_preflight_contract")

    commands = module.plan_commands_for_categories(("optional_provider_archive_audit_surface",))

    assert "scripts/run-pytest-clean.sh tests/test_med_deepscientist_repo_manifest.py -q" in commands
    assert "scripts/run-pytest-clean.sh tests/test_workspace_contracts.py -q" in commands
    assert "scripts/run-pytest-clean.sh tests/test_backend_audit.py -q" in commands


def test_plan_commands_for_integration_harness_surface_include_runtime_eval_proofs() -> None:
    module = importlib.import_module("med_autoscience.dev_preflight_contract")

    commands = module.plan_commands_for_categories(("integration_harness_surface",))

    assert "scripts/run-pytest-clean.sh tests/test_dev_preflight_contract.py -q" in commands
    assert "scripts/run-pytest-clean.sh tests/test_dev_preflight.py -q" in commands
    assert "scripts/run-pytest-clean.sh tests/test_workspace_init.py -q" in commands
    assert "make test-meta" in commands
    assert "scripts/run-pytest-clean.sh tests/test_work_unit_runtime_contract.py -q" not in commands
    assert "scripts/run-pytest-clean.sh tests/test_domain_health_diagnostic.py tests/test_study_delivery_sync.py tests/test_publication_gate.py -q" not in commands


def test_plan_commands_for_runtime_contract_surface_include_mas_runtime_proofs() -> None:
    module = importlib.import_module("med_autoscience.dev_preflight_contract")

    commands = module.plan_commands_for_categories(("runtime_contract_surface",))

    assert "scripts/run-pytest-clean.sh tests/test_opl_runtime_contract.py -q" in commands
    assert "scripts/run-pytest-clean.sh tests/test_profiles.py -q" in commands
    assert "scripts/run-pytest-clean.sh tests/test_runtime_protocol_layout.py -q" in commands
    assert "scripts/run-pytest-clean.sh tests/test_runtime_transport_hermes.py -q" not in commands
    assert "scripts/run-pytest-clean.sh tests/test_work_unit_runtime_contract.py -q" not in commands
    assert "make test-meta" in commands


def test_plan_commands_for_family_shared_surface_use_focused_family_lane() -> None:
    module = importlib.import_module("med_autoscience.dev_preflight_contract")

    commands = module.plan_commands_for_categories(("family_shared_surface",))

    assert commands == ["make test-family"]


def test_plan_commands_for_structure_quality_surface_use_structure_lane() -> None:
    module = importlib.import_module("med_autoscience.dev_preflight_contract")

    commands = module.plan_commands_for_categories(("structure_quality_surface",))

    assert commands == ["make test-structure"]


def test_plan_commands_for_root_governance_contract_surface_use_focused_contract_lanes() -> None:
    module = importlib.import_module("med_autoscience.dev_preflight_contract")

    commands = module.plan_commands_for_categories(("root_governance_contract_surface",))

    assert commands == [
        (
            "scripts/run-pytest-clean.sh "
            "tests/controller_charter/test_controller_charter_module_contract.py "
            "tests/runtime/test_runtime_module_contract.py "
            "tests/eval_hygiene/test_eval_hygiene_module_contract.py "
            "tests/integration/test_monorepo_scaffold_boundaries.py -q"
        ),
        "scripts/run-pytest-clean.sh tests/test_opl_family_contract_adoption.py -q",
        "scripts/run-pytest-clean.sh tests/test_opl_family_persistence_adapter.py -q",
        "scripts/run-pytest-clean.sh tests/test_test_command_surfaces.py -q",
    ]


def test_plan_commands_for_control_plane_surface_use_focused_lane() -> None:
    module = importlib.import_module("med_autoscience.dev_preflight_contract")

    commands = module.plan_commands_for_categories(("control_plane_surface",))

    assert commands == ["make test-control-plane"]
