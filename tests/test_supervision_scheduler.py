from __future__ import annotations

import importlib
from pathlib import Path

from tests.study_runtime_test_helpers import make_profile


def test_default_scheduler_status_uses_opl_replacement_without_launchagent(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.supervision_scheduler")
    profile = make_profile(tmp_path)
    launch_agents = tmp_path / "LaunchAgents"

    result = module.read_supervision_status(profile=profile)

    assert result["scheduler_owner"] == "opl_provider_runtime_manager"
    assert result["adapter_id"] == "opl_family_runtime_provider"
    assert result["manager"] == "opl"
    assert result["status"] == "replacement_owner_active"
    assert result["loaded"] is True
    assert result["adapter_status"]["migration_state"] == "replacement_owner_active"
    assert result["opl_replacement"]["provider_slo_tick_command"] == (
        "opl family-runtime provider-slo tick --provider temporal"
    )
    assert result["legacy_adapter"]["manager"] == "local"
    assert result["legacy_adapter"]["scheduler_owner"] == "mas_supervision_scheduler"
    assert result["legacy_adapter"]["adapter_id"] == "local_launchd_retired_tombstone"
    assert result["legacy_adapter"]["status"] == "retired_physical_tombstone"
    assert result["legacy_adapter"]["callable"] is False
    assert result["legacy_adapter"]["diagnostic_status_command"] is None
    assert result["legacy_adapter"]["cleanup_command"] is None
    assert result["authority_boundary"]["can_install_domain_daemon"] is False
    assert result["authority_boundary"]["can_own_generic_scheduler"] is False
    assert result["authority_boundary"]["can_own_generic_daemon"] is False
    assert result["authority_boundary"]["can_own_generic_queue"] is False
    assert result["authority_boundary"]["can_own_generic_attempt_ledger"] is False
    assert result["authority_boundary"]["can_own_generic_runner"] is False
    assert result["authority_boundary"]["can_own_generic_workbench"] is False
    assert result["outer_supervision_slo"]["supervision_owner"] == "opl_provider_runtime_manager"
    boundary = result["consumer_migration"]["functional_consumer_boundary"]
    assert boundary["surface_kind"] == "mas_functional_consumer_boundary"
    assert boundary["generic_surface_owner"] == "one-person-lab"
    assert set(boundary["mas_does_not_own"]) >= {
        "generic_scheduler",
        "generic_daemon",
        "generic_queue",
        "generic_attempt_ledger",
        "generic_runner",
        "generic_workbench",
    }
    assert set(boundary["mas_retains"]) >= {
        "study_truth",
        "publication_quality_verdict",
        "artifact_authority",
        "publication_route_memory_body",
        "owner_receipt",
        "typed_blocker",
    }
    assert boundary["declarative_pack_compiler_input"]["compiler_owner"] == "one-person-lab"
    assert boundary["declarative_pack_compiler_input"]["pack_id"] == "mas-medical-research-pack"
    assert boundary["generated_surface_handoff"]["current_mas_role"] == (
        "handwritten_migration_bridge"
    )
    assert boundary["generated_surface_handoff"]["mas_handwritten_shell_expansion_allowed"] is False
    assert boundary["minimal_authority_function_manifest"]["function_ids"] == [
        "publication_quality_verdict",
        "ai_reviewer_quality_decision",
        "artifact_mutation_authorization",
        "publication_route_memory_accept_reject",
        "source_readiness_verdict",
        "owner_receipt_signer",
        "medical_helper_implementation",
    ]
    assert boundary["functional_module_inventory_summary"]["classification_gap_count"] == 0
    assert boundary["functional_module_inventory_summary"]["functional_structure_gap_count"] == 0
    assert boundary["functional_module_inventory_summary"]["active_private_generic_residue_count"] == 0
    assert (
        boundary["functional_module_inventory_summary"]["remaining_gap_classification"]
        == "live_provider_paper_line_evidence_gates"
    )
    followthrough_summary = boundary["functional_followthrough_gap_summary"]
    assert followthrough_summary["status"] == "functional_structure_closed_evidence_gates_remaining"
    assert followthrough_summary["classification_gap_count"] == 0
    assert followthrough_summary["functional_structure_gap_count"] == 0
    assert followthrough_summary["remaining_items_are_evidence_gates"] is True
    assert followthrough_summary["legacy_cleanup_items_are_remaining_active_gaps"] is False
    assert followthrough_summary["legacy_cleanup_items_have_default_entry"] is False
    assert followthrough_summary["legacy_cleanup_items_have_standard_template_refs"] is True
    assert followthrough_summary["remaining_functional_followthrough_gate_ids"] == []
    assert followthrough_summary["remaining_functional_followthrough_gates"] == []
    assert set(followthrough_summary["closed_functional_structure_gate_ids"]) == {
        "generated_surface_active_caller_cutover",
        "refs_only_adapter_thinning",
        "legacy_cleanup_physical_retirement",
        "opl_app_workbench_drilldown",
        "lifecycle_locator_retention_restore_ledger_reconciliation",
    }
    assert followthrough_summary["does_not_clear"] == (
        followthrough_summary["remaining_evidence_gate_ids"]
    )
    assert set(followthrough_summary["remaining_evidence_gate_ids"]) == {
        "live_provider_paper_apply_scaleout",
        "publication_route_memory_receipt_scaleout",
        "artifact_lifecycle_receipt_scaleout",
        "provider_slo_long_soak",
    }
    coverage = boundary["opl_functional_harness_consumer_coverage"]
    assert coverage["coverage_items"] == [
        "refs_only_memory_writeback_chain",
        "queue_stage_attempt_typed_closeout",
        "generic_transition_runner",
        "restart_dead_letter_repair_human_gate_state_chain",
    ]
    assert coverage["opl_harness_pass_is_paper_closure"] is False
    assert coverage["opl_harness_pass_is_publication_ready"] is False
    assert coverage["mas_owns_generic_runtime"] is False
    inventory = boundary["functional_module_inventory"]
    assert len(inventory) == 18
    inventory_by_id = {item["module_id"]: item for item in inventory}
    assert inventory_by_id["runtime_lifecycle_sqlite_reference_adapter"]["active_caller_status"] == (
        "refs_only_domain_sidecar_adapter_active"
    )
    assert set(inventory_by_id["runtime_lifecycle_sqlite_reference_adapter"]["forbidden_mas_roles"]) == {
        "generic_persistence_engine",
        "generic_lifecycle_engine",
        "generic_restore_retention_owner",
    }
    assert inventory_by_id["runtime_supervisor_scan_consume_dispatch_shell"]["migration_action"] == (
        "declare_runtime_supervisor_policy_and_consume_opl_runtime_manager_loop"
    )
    assert inventory_by_id["local_launchd_scheduler_install_path"]["active_caller_allowed"] is False
    assert inventory_by_id["local_launchd_scheduler_install_path"]["default_caller_count"] == 0
    assert inventory_by_id["local_launchd_scheduler_install_path"]["install_allowed"] is False
    assert inventory_by_id["local_launchd_scheduler_install_path"]["physical_retired"] is True
    assert inventory_by_id["local_launchd_scheduler_install_path"]["active_callers"] == []
    assert boundary["no_active_caller_proof"]["default_caller_count"] == 0
    assert boundary["no_active_caller_proof"]["status"] == "legacy_local_scheduler_physical_retired"
    assert boundary["no_active_caller_proof"]["cleanup_only_commands"] == []
    assert boundary["no_active_caller_proof"]["forbidden_explicit_callers"] == [
        "runtime-supervision-status --profile <profile> --manager local",
        "runtime-ensure-supervision --profile <profile> --manager local",
        "runtime-remove-supervision --profile <profile> --manager local",
    ]
    assert boundary["no_active_caller_proof"]["forbidden_default_callers"] == [
        "cli_default_local_scheduler_install",
        "workspace_bootstrap_local_scheduler_install",
        "product_entry_local_scheduler_install",
        "sidecar_local_scheduler_install",
        "mcp_local_scheduler_install",
    ]
    retirement_proof = boundary["legacy_local_scheduler_physical_retirement_proof"]
    assert retirement_proof["status"] == "physical_retired_tombstone_provenance_only"
    assert retirement_proof["status_allowed"] is False
    assert retirement_proof["remove_allowed"] is False
    assert retirement_proof["trigger_allowed"] is False
    assert retirement_proof["write_install_proof_allowed"] is False
    assert retirement_proof["remaining_physical_delete_blockers"] == []
    assert not launch_agents.exists()


def test_default_scheduler_ensure_delegates_to_opl_replacement_without_launchagent(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.supervision_scheduler")
    profile = make_profile(tmp_path)
    launch_agents = tmp_path / "LaunchAgents"

    result = module.ensure_supervision(profile=profile, trigger_now=True, write_install_proof=True)

    assert result["action"] == "delegated_to_opl_provider_scheduler"
    assert result["scheduler_owner"] == "opl_provider_runtime_manager"
    assert result["manager"] == "opl"
    assert result["dry_run"] is False
    assert result["write_install_proof"] is False
    assert result["after"]["status"] == "replacement_owner_active"
    assert result["legacy_local_tombstone"]["manager"] == "local"
    assert result["legacy_local_tombstone"]["status"] == "retired_physical_tombstone"
    assert result["legacy_local_tombstone"]["cleanup_command"] is None
    assert result["authority_boundary"]["can_install_domain_daemon"] is False
    assert not launch_agents.exists()


def test_default_scheduler_remove_delegates_to_opl_and_keeps_local_tombstone(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.supervision_scheduler")
    profile = make_profile(tmp_path)

    result = module.remove_supervision(profile=profile)

    assert result["action"] == "delegated_to_opl_provider_scheduler"
    assert result["scheduler_owner"] == "opl_provider_runtime_manager"
    assert result["manager"] == "opl"
    assert result["removed_job_ids"] == []
    assert result["legacy_local_cleanup_command"] is None
    assert result["legacy_local_tombstone"]["status"] == "retired_physical_tombstone"


def test_local_scheduler_direct_call_returns_physical_tombstone(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.supervision_scheduler")
    profile = make_profile(tmp_path)

    result = module.ensure_supervision(
        profile=profile,
        manager="local",
        trigger_now=False,
        dry_run=True,
    )

    assert result["scheduler_owner"] == "mas_supervision_scheduler"
    assert result["adapter_id"] == "local_launchd_retired_tombstone"
    assert result["active_path_role"] == "physical_retired_tombstone_provenance_only"
    assert result["consumer_migration"]["replacement_owner"] == "one-person-lab"
    assert result["consumer_migration"]["replacement_owner_surface"] == "opl_provider_runtime_manager"
    assert result["consumer_migration"]["replacement_required_before_retirement"] is False
    assert result["consumer_migration"]["retirement_state"] == "local_legacy_physical_retired_tombstone"
    assert result["dry_run"] is True
    assert result["write_install_proof"] is False
    assert result["install_allowed"] is False
    assert result["status_allowed"] is False
    assert result["remove_allowed"] is False
    assert result["cleanup_command"] is None
    assert result["diagnostic_status_command"] is None
    assert result["tombstone_ref"].startswith("contracts/runtime/legacy-active-path-tombstones.json")
    assert result["command_outputs"] == []


def test_local_scheduler_status_and_remove_are_tombstone_only(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.supervision_scheduler")
    profile = make_profile(tmp_path)

    status = module.read_supervision_status(profile=profile, manager="local")
    removed = module.remove_supervision(profile=profile, manager="local")

    assert status["status"] == "retired_physical_tombstone"
    assert status["requested_action"] == "status"
    assert status["job_exists"] is False
    assert status["retired_artifacts"] == {}
    assert removed["status"] == "retired_physical_tombstone"
    assert removed["requested_action"] == "remove"
    assert removed["removed_job_ids"] == []
    assert removed["remove_allowed"] is False


def test_explicit_hermes_adapter_is_projected_under_mas_scheduler_owner(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.supervision_scheduler")
    profile = make_profile(tmp_path)

    monkeypatch.setattr(
        module.hermes_supervision,
        "read_supervision_status",
        lambda **_: {
            "schema_version": 1,
            "surface_kind": "workspace_runtime_supervision",
            "owner": "hermes_gateway_cron",
            "status": "loaded",
            "loaded": True,
            "job_name": "medautoscience-supervision-diabetes-abc12345",
            "watch_command": ["watch-runtime", "--interval-seconds", "300"],
        },
    )

    result = module.read_supervision_status(profile=profile, manager="hermes")

    assert result["scheduler_owner"] == "mas_supervision_scheduler"
    assert result["adapter_id"] == "hermes_gateway_cron"
    assert result["active_path_role"] == "explicit_optional_executor_adapter_provenance_only"
    assert result["consumer_migration"]["replacement_owner"] == "one-person-lab"
    assert result["owner"] == "hermes_gateway_cron"
    assert result["workspace_key"] == "diabetes-abc12345"
    assert result["outer_supervision_slo"]["supervision_owner"] == "mas_supervision_scheduler"
    assert result["outer_supervision_slo"]["adapter_id"] == "hermes_gateway_cron"
    assert result["outer_supervision_slo"]["handoff"]["replacement_owner"] == "one-person-lab"
    assert result["outer_supervision_slo"]["consumer_migration"]["retirement_proof_required"] == [
        "opl_replacement_contract_available",
        "replacement_proof",
        "no_active_caller_proof",
        "no_forbidden_write",
        "focused_cli_status_tests",
        "git_diff_check",
    ]
