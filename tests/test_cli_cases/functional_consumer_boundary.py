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
    assert len(inventory) == 18
    inventory_by_id = {item["module_id"]: item for item in inventory}
    assert inventory_by_id["runtime_lifecycle_sqlite_reference_adapter"]["code_paths"] == [
        "src/med_autoscience/runtime_protocol/runtime_lifecycle_store.py",
        "src/med_autoscience/runtime_protocol/study_runtime.py",
        "src/med_autoscience/cli_parts/runtime_lifecycle_commands.py",
    ]
    assert set(inventory_by_id["runtime_lifecycle_sqlite_reference_adapter"]["forbidden_mas_roles"]) == {
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
    assert boundary["functional_module_inventory_summary"]["functional_structure_gap_count"] == 0
    assert boundary["functional_gap_zero_summary"]["status"] == (
        "zero_functional_structure_gaps_remaining_evidence_gated"
    )
    assert boundary["functional_gap_zero_summary"]["remaining_gap_classification"] == (
        "test_evidence_gates_only"
    )
    assert boundary["functional_gap_zero_summary"]["remaining_items_are_evidence_gates"] is True
    assert "live_provider_paper_apply_scaleout" in boundary["functional_gap_zero_summary"][
        "remaining_evidence_gate_ids"
    ]
    assert boundary["no_active_caller_proof"]["default_caller_count"] == 0
    assert boundary["no_active_caller_proof"]["default_manager"] == "opl"
    assert "workspace_bootstrap_manager_is_opl" in boundary["no_active_caller_proof"]["proof_items"]
    assert boundary["legacy_local_scheduler_cleanup_only_proof"]["default_bootstrap_exposes_local_install"] is False
