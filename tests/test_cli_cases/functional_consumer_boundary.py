from __future__ import annotations

import importlib
import json
from pathlib import Path

from .shared import write_profile


def test_sidecar_export_projects_functional_consumer_boundary(tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    workspace_root = tmp_path / "workspace"
    profile_path = tmp_path / "profile.local.toml"
    write_profile(profile_path, workspace_root=workspace_root)

    exit_code = cli.main(["sidecar", "export", "--profile", str(profile_path), "--format", "json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    boundary = payload["functional_consumer_boundary"]
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
        "safe_action_refs",
    }
    pack_input = boundary["declarative_pack_compiler_input"]
    assert pack_input["surface_kind"] == "mas_declarative_pack_compiler_input"
    assert pack_input["compiler_owner"] == "one-person-lab"
    assert pack_input["compiler_outputs_expected"] == [
        "cli",
        "mcp",
        "skill",
        "product_entry",
        "sidecar",
        "status",
        "workbench",
        "projection_shell",
        "test_lane_harness",
    ]
    assert pack_input["mas_long_term_code_owner"] == "minimal_authority_functions_only"
    handoff = boundary["generated_surface_handoff"]
    assert handoff["surface_kind"] == "mas_generated_surface_handoff"
    assert handoff["generated_surface_owner"] == "one-person-lab"
    assert handoff["current_mas_role"] == "handwritten_migration_bridge"
    assert handoff["long_term_mas_owner"] is False
    assert handoff["mas_handwritten_shell_expansion_allowed"] is False
    handoff_by_id = {item["surface_id"]: item for item in handoff["handoff_surfaces"]}
    assert set(handoff_by_id) == set(pack_input["compiler_outputs_expected"])
    assert handoff_by_id["sidecar"]["current_role"] == "migration_bridge_export_dispatch_adapter"
    assert handoff_by_id["skill"]["current_role"] == (
        "migration_bridge_domain_skill_target_and_pack_guidance"
    )
    assert handoff_by_id["skill"]["target_role"] == "opl_generated_skill_descriptor_surface"
    assert handoff_by_id["sidecar"]["target_role"] == "opl_generated_sidecar_handoff_surface"
    generated_default = boundary["generated_default_caller_boundary"]
    assert generated_default["status"] == "opl_generated_hosted_shell_is_default_caller"
    assert generated_default["default_caller_owner"] == "one-person-lab"
    assert generated_default["mas_handwritten_shell_default_caller_allowed"] is False
    assert generated_default["all_default_callers_migrated"] is True
    generated_surfaces = {
        item["surface_id"]: item for item in generated_default["surface_boundaries"]
    }
    assert generated_surfaces["sidecar"]["mas_retained_role"] == "domain_owner_route_handoff_adapter"
    assert generated_surfaces["sidecar"]["parity_ref"] == "sidecar_descriptor_parity"
    assert generated_surfaces["workbench"]["default_caller_owner"] == "one-person-lab"
    assert all(item["mas_generic_owner_allowed"] is False for item in generated_surfaces.values())
    authority = boundary["minimal_authority_function_manifest"]
    assert authority["surface_kind"] == "mas_minimal_authority_function_manifest"
    assert authority["function_ids"] == [
        "publication_quality_verdict",
        "ai_reviewer_quality_decision",
        "artifact_mutation_authorization",
        "publication_route_memory_accept_reject",
        "source_readiness_verdict",
        "owner_receipt_signer",
        "medical_helper_implementation",
    ]
    assert authority["function_count"] == 7
    assert authority["all_other_program_surfaces"] == "opl_generated_or_migration_bridge"
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
    assert coverage["refs_only_memory_writeback_chain"]["body_included"] is False
    assert coverage["generic_transition_runner"]["runner_completion_can_authorize_publication"] is False
    inventory = boundary["functional_module_inventory"]
    assert len(inventory) == 19
    inventory_by_id = {item["module_id"]: item for item in inventory}
    assert inventory_by_id["lifecycle_refs_adapter"]["code_paths"] == [
        "src/med_autoscience/runtime_protocol/lifecycle_refs_adapter.py",
        "src/med_autoscience/runtime_protocol/study_runtime.py",
        "src/med_autoscience/cli_parts/runtime_lifecycle_commands.py",
    ]
    assert set(inventory_by_id["lifecycle_refs_adapter"]["forbidden_mas_roles"]) == {
        "generic_persistence_engine",
        "generic_lifecycle_engine",
        "generic_restore_retention_owner",
    }
    assert inventory_by_id["paper_work_unit_outbox_index"]["classification"] == "refs_only_adapter"
    assert inventory_by_id["artifact_authority"]["cannot_absorb_reason"] == (
        "Canonical manuscript/package mutation and submission authority are MAS artifact authority."
    )
    assert inventory_by_id["local_launchd_scheduler_install_path"]["default_caller_count"] == 0
    assert inventory_by_id["local_launchd_scheduler_install_path"]["install_allowed"] is False
    assert boundary["functional_module_inventory_summary"]["classification_gap_count"] == 0
    assert boundary["functional_module_inventory_summary"]["functional_structure_gap_count"] == 0
    assert boundary["functional_followthrough_gap_summary"]["status"] == (
        "functional_structure_closed_evidence_gates_remaining"
    )
    assert boundary["functional_followthrough_gap_summary"]["remaining_gap_classification"] == (
        "live_provider_paper_line_evidence_gates"
    )
    followthrough_summary = boundary["functional_followthrough_gap_summary"]
    assert followthrough_summary["classification_gap_count"] == 0
    assert followthrough_summary["functional_structure_gap_count"] == 0
    assert followthrough_summary["remaining_items_are_evidence_gates"] is True
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
    assert boundary["no_active_caller_proof"]["default_caller_count"] == 0
    assert boundary["no_active_caller_proof"]["default_manager"] == "opl"
    assert "workspace_bootstrap_manager_is_opl" in boundary["no_active_caller_proof"]["proof_items"]
    retirement_proof = boundary["legacy_local_scheduler_physical_retirement_proof"]
    assert retirement_proof["default_bootstrap_exposes_local_install"] is False
    assert retirement_proof["cleanup_status"] == "tombstone_only"
    assert retirement_proof["remaining_physical_delete_blockers"] == []
    thinning = boundary["physical_thinning_evidence"]
    assert thinning["surface_kind"] == "mas_physical_thinning_evidence"
    assert thinning["body_included"] is False
    assert thinning["does_not_claim_physical_delete"] is True
    assert thinning["does_not_claim_paper_closure"] is True
    assert thinning["physical_delete_requires_all_gates"] == [
        "no_active_caller_proof",
        "opl_replacement_parity",
        "domain_receipt_parity",
        "focused_tests",
        "no_forbidden_write_proof",
        "history_tombstone_refs",
    ]
    thinning_groups = {item["group_id"]: item for item in thinning["residue_groups"]}
    assert set(thinning_groups) == {
        "runner_residue",
        "supervisor_residue",
        "workbench_residue",
        "lifecycle_refs_residue",
    }
    assert all(group["physical_delete_permitted"] is False for group in thinning_groups.values())
    assert all(group["generic_owner_claim_allowed"] is False for group in thinning_groups.values())
    assert all(group["tombstone_or_parity_refs_required"] is True for group in thinning_groups.values())
    assert "no_active_caller_proof.default_caller_count=0" in thinning_groups["supervisor_residue"][
        "evidence_refs"
    ]
    assert "retired_legacy_residue_tombstones.scheduler_legacy_residue_without_active_caller" in thinning_groups[
        "supervisor_residue"
    ]["evidence_refs"]
    assert "refs_only_adapter_retirement_gates.lifecycle_refs_adapter" in thinning_groups[
        "lifecycle_refs_residue"
    ]["evidence_refs"]
    retirement_matrix = boundary["physical_retirement_gate_matrix"]
    candidates = {item["surface_id"]: item for item in retirement_matrix["retirement_candidates"]}
    assert set(candidates) == {
        "runtime_transport",
        "lifecycle_refs_sqlite",
        "workbench_shell",
        "owner_route_handoff",
        "status_projection",
    }
    assert retirement_matrix["no_active_caller_summary"]["active_default_caller_count"] == 0
    assert retirement_matrix["no_active_caller_summary"]["full_active_caller_zero_proven"] is False
    assert retirement_matrix["no_active_caller_summary"]["physical_delete_ready_count"] == 0
    assert candidates["runtime_transport"]["physical_delete_permitted"] is False
    assert candidates["lifecycle_refs_sqlite"]["active_caller_status"] == (
        "refs_only_domain_owner_route_handoff_adapter_active"
    )
    assert candidates["owner_route_handoff"]["active_default_caller_zero_proven"] is True
    assert candidates["owner_route_handoff"]["deletion_readiness_worklist_ref"] == (
        "functional_consumer_boundary.active_path_residue_cleanup_gates."
        "owner_route_handoff_adapter.deletion_readiness_worklist"
    )
    assert (
        "owner_route_handoff_response.forbidden_write_guard_proof"
        in candidates["owner_route_handoff"]["no_forbidden_write_proof_refs"]
    )
    assert candidates["workbench_shell"]["retained_as"] == (
        "domain_projection_refs_for_opl_workbench"
    )
    assert candidates["status_projection"]["no_active_caller_proof"]["full_active_caller_status"] == (
        "not_proven_retained_domain_or_diagnostic_adapter"
    )
    cleanup_gates = {
        item["residue_id"]: item for item in boundary["active_path_residue_cleanup_gates"]
    }
    assert set(cleanup_gates) == {
        "runtime_transport_core_bridge",
        "runtime_turn_runner_closeout_adapter",
        "worker_lease_residency_projection",
        "lifecycle_refs_sqlite_index",
        "workbench_shell_domain_projection_refs",
        "owner_route_handoff_adapter",
        "status_projection_domain_truth_refs",
        "legacy_supervisor_scheduler_tombstone",
    }
    retained_gate = cleanup_gates["runtime_transport_core_bridge"]
    assert retained_gate["active_caller_count"] > 0
    assert retained_gate["no_active_caller_proven"] is False
    assert retained_gate["physical_delete_permitted"] is False
    assert retained_gate["archive_permitted"] is False
    assert retained_gate["rename_permitted"] is False
    assert retained_gate["tombstone_permitted"] is False
    assert retained_gate["no_alias_facade_compat_wrapper_allowed"] is True
    assert "active_caller_count=0" in retained_gate["delete_or_tombstone_after"]
    assert "paper_closure_verdict" in retained_gate["must_not_emit"]
    sqlite_gate = cleanup_gates["lifecycle_refs_sqlite_index"]
    assert "tests/test_lifecycle_refs_adapter.py" in sqlite_gate["focused_test_refs"]
    workbench_gate = cleanup_gates["workbench_shell_domain_projection_refs"]
    assert workbench_gate["current_role"] == "domain_projection_refs_for_opl_workbench"
    assert workbench_gate["active_caller_count"] > 0
    assert workbench_gate["physical_delete_permitted"] is False
    sidecar_gate = cleanup_gates["owner_route_handoff_adapter"]
    assert sidecar_gate["current_role"] == "domain_owner_route_handoff_adapter"
    assert sidecar_gate["physical_delete_permitted"] is False
    sidecar_worklist = sidecar_gate["deletion_readiness_worklist"]
    assert sidecar_worklist["status"] == "blocked_active_domain_owner_route_handoff_caller_present"
    assert sidecar_worklist["can_delete"] is False
    assert {item["gate"] for item in sidecar_worklist["missing_gate_inputs"]} == {
        "active_caller_count=0",
        "opl_replacement_parity_proven",
        "domain_receipt_parity_proven",
        "focused_tests_green",
        "no_forbidden_write_proof",
        "history_tombstone_refs_recorded",
    }
    assert "current_package.zip" in sidecar_worklist["must_not_write"]
    assert "physical_delete_complete" in sidecar_worklist["must_not_claim"]
    status_gate = cleanup_gates["status_projection_domain_truth_refs"]
    assert status_gate["current_role"] == "domain_truth_status_projection"
    assert status_gate["no_active_caller_proven"] is False
    tombstone_gate = cleanup_gates["legacy_supervisor_scheduler_tombstone"]
    assert tombstone_gate["active_caller_count"] == 0
    assert tombstone_gate["no_active_caller_proven"] is True
    assert tombstone_gate["physical_delete_permitted"] is False
    assert tombstone_gate["tombstone_permitted"] is True
    assert tombstone_gate["delete_or_tombstone_after"] == []
    assert "physical_delete_already_completed" in thinning["forbidden_claims"]
