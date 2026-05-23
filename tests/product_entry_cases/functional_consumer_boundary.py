from __future__ import annotations

import importlib
from pathlib import Path

from .shared import make_profile


def test_product_entry_manifest_exposes_functional_consumer_boundary(tmp_path: Path) -> None:
    product_entry = importlib.import_module("med_autoscience.controllers.product_entry")

    profile = make_profile(tmp_path)
    profile_ref = tmp_path / "profile.local.toml"

    manifest = product_entry.build_product_entry_manifest(profile=profile, profile_ref=profile_ref)
    boundary = manifest["functional_consumer_boundary"]

    assert boundary["surface_kind"] == "mas_functional_consumer_boundary"
    assert boundary["status"] == "opl_consumes_generic_surfaces_mas_supplies_domain_authority_pack"
    assert boundary["consumer_role"] == "domain_authority_pack_thin_program_surface"
    assert boundary["generic_surface_owner"] == "one-person-lab"
    assert boundary["no_resurrection_required"] is True
    assert boundary["mas_does_not_own"] == [
        "generic_scheduler",
        "generic_daemon",
        "generic_queue",
        "generic_attempt_ledger",
        "generic_runner",
        "generic_transition_runner",
        "generic_workbench",
        "generic_memory_locator",
        "generic_artifact_lifecycle",
        "generic_observability",
    ]
    assert set(boundary["mas_domain_authority_surfaces"]) == {
        "study_truth",
        "publication_quality_verdict",
        "artifact_authority",
        "publication_route_memory_body",
        "memory_writeback_decision",
        "domain_transition_table",
        "owner_receipt",
        "typed_blocker",
        "safe_action_refs",
    }
    pack_input = boundary["declarative_pack_compiler_input"]
    assert pack_input["surface_kind"] == "mas_declarative_pack_compiler_input"
    assert pack_input["compiler_owner"] == "one-person-lab"
    assert pack_input["pack_id"] == "mas-medical-research-pack"
    assert pack_input["pack_role"] == "domain_authority_pack_input_not_generated_shell_owner"
    assert [item["input_id"] for item in pack_input["input_refs"]] == [
        "domain_descriptor",
        "stage_graph",
        "action_intents",
        "domain_transition_table",
        "publication_route_memory_policy",
        "artifact_authority_policy",
        "source_readiness_policy",
        "receipt_schema",
        "no_forbidden_write_contract",
    ]
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
    assert pack_input["must_not_generate_or_claim_domain_authority"] is True
    handoff = boundary["generated_surface_handoff"]
    assert handoff["surface_kind"] == "mas_generated_surface_handoff"
    assert handoff["generated_surface_owner"] == "one-person-lab"
    assert handoff["current_mas_role"] == "domain_handler_and_refs_projection_source"
    assert handoff["long_term_mas_owner"] is False
    assert handoff["mas_handwritten_shell_expansion_allowed"] is False
    handoff_by_id = {item["surface_id"]: item for item in handoff["handoff_surfaces"]}
    assert set(handoff_by_id) == set(pack_input["compiler_outputs_expected"])
    assert handoff_by_id["cli"]["target_role"] == "opl_generated_command_surface"
    assert handoff_by_id["mcp"]["target_role"] == "opl_generated_mcp_descriptor_surface"
    assert handoff_by_id["skill"]["target_role"] == "opl_generated_skill_descriptor_surface"
    assert handoff_by_id["product_entry"]["target_role"] == "opl_generated_product_entry_surface"
    assert handoff_by_id["sidecar"]["target_role"] == "opl_generated_sidecar_handoff_surface"
    assert handoff_by_id["status"]["target_role"] == "opl_generated_status_wrapper_over_mas_truth_refs"
    assert handoff_by_id["workbench"]["target_role"] == (
        "opl_hosted_workbench_shell_consuming_mas_refs"
    )
    assert handoff_by_id["projection_shell"]["target_role"] == "opl_generated_projection_shell"
    assert handoff_by_id["test_lane_harness"]["target_role"] == (
        "opl_generated_harness_consumer_over_mas_pack"
    )
    generated_default = boundary["generated_default_caller_boundary"]
    assert generated_default["surface_kind"] == "mas_generated_default_caller_boundary"
    assert generated_default["status"] == "opl_generated_hosted_shell_is_default_caller"
    assert generated_default["default_caller_owner"] == "one-person-lab"
    assert generated_default["mas_handwritten_shell_default_caller_allowed"] is False
    assert generated_default["mas_handwritten_shell_expansion_allowed"] is False
    assert generated_default["all_default_surfaces_generated"] is True
    assert generated_default["physical_delete_is_not_implied"] is True
    readiness = generated_default["opl_default_caller_readiness_evidence"]
    assert readiness["surface_kind"] == "mas_opl_default_caller_readiness_evidence"
    assert readiness["source_surface_kind"] == "opl_agent_generated_default_caller_readiness_report"
    assert readiness["status"] == "ready_domain_evidence_required"
    assert readiness["structural_replacement_evidence_ready"] is True
    assert readiness["replacement_parity"] == "ready"
    assert readiness["default_surface_cutover"] == "ready"
    assert readiness["physical_delete_authorized"] is False
    assert readiness["authority_boundary"]["can_claim_domain_ready"] is False
    assert readiness["authority_boundary"]["can_claim_quality_verdict"] is False
    assert readiness["authority_boundary"]["can_authorize_physical_delete"] is False
    assert generated_default["default_caller_surfaces"] == [
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
    generated_surfaces = {
        item["surface_id"]: item for item in generated_default["surface_boundaries"]
    }
    assert set(generated_surfaces) == set(generated_default["default_caller_surfaces"])
    assert generated_surfaces["cli"]["mas_allowed_role"] == "domain_handler_target"
    assert generated_surfaces["mcp"]["parity_ref"] == "mcp_descriptor_parity"
    assert generated_surfaces["product_entry"]["default_caller_owner"] == "one-person-lab"
    assert generated_surfaces["sidecar"]["mas_allowed_role"] == "domain_owner_route_handoff_refs"
    assert generated_surfaces["status"]["mas_allowed_role"] == "domain_truth_status_projection"
    assert generated_surfaces["workbench"]["mas_allowed_role"] == "domain_projection_refs"
    assert all(item["mas_generic_owner_allowed"] is False for item in generated_surfaces.values())
    assert generated_default["allowed_mas_program_roles_after_cutover"] == [
        "direct_skill_target",
        "domain_handler",
        "owner_receipt_signer",
        "typed_blocker",
        "ai_first_validator",
        "diagnostic",
        "domain_authority_refs",
    ]
    authority = boundary["minimal_authority_function_manifest"]
    assert authority["surface_kind"] == "mas_minimal_authority_function_manifest"
    assert authority["status"] == "minimal_authority_functions_only"
    assert authority["semantic_model"] == (
        "ai_first_stage_quality_gate_boundaries_not_script_function_verdicts"
    )
    assert authority["allowed_judgment_modes"] == [
        "ai_first_stage_gate",
        "ai_first_record_validator",
        "mechanical_guard",
    ]
    assert authority["verdict_function_model_retired"] is True
    assert authority["gate_validator_ref"] == (
        "src/med_autoscience/controllers/ai_first_private_authority.py::"
        "validate_ai_first_private_authority_gate"
    )
    assert authority["runtime_enforcement_status"] == "contract_validator_landed"
    assert authority["program_output_policy"] == (
        "programs_validate_ai_first_stage_gate_records_and_emit_receipts_or_typed_blockers_only"
    )
    assert authority["standard_stage_gate_output_model"] == {
        "executor_output": "stage_work_artifact_source_evidence_refs_and_execution_receipt",
        "reviewer_output": "independent_ai_reviewer_or_auditor_gate_record",
        "program_output": "provenance_currentness_schema_receipt_or_typed_blocker",
        "self_review_closes_gate": False,
    }
    assert authority["requires_ai_first_record"] is True
    assert authority["boundary_ids"] == [
        "publication_quality_stage_gate_boundary",
        "ai_reviewer_quality_stage_gate_boundary",
        "artifact_mutation_stage_gate_boundary",
        "publication_route_memory_accept_reject_stage_gate_boundary",
        "source_readiness_stage_gate_boundary",
    ]
    assert authority["forbidden_mechanical_decision_surfaces"] == [
        "script_exit_code_as_publication_quality_verdict",
        "function_return_value_as_ai_reviewer_quality_decision",
        "test_pass_as_artifact_mutation_authorization",
        "queue_completion_as_publication_route_memory_accept_reject",
        "file_presence_as_source_readiness_verdict",
    ]
    independent_policy = authority["independent_executor_reviewer_agent_policy"]
    assert independent_policy["required"] is True
    assert independent_policy["separate_invocation_required"] is True
    assert independent_policy["separate_context_record_required"] is True
    assert independent_policy["separate_task_record_required"] is True
    assert independent_policy["separate_receipt_required"] is True
    assert independent_policy["self_review_closes_quality_gate"] is False
    assert independent_policy["missing_independent_reviewer_record_policy"] == (
        "fail_closed_or_route_back"
    )
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
    assert {item["function_id"] for item in authority["functions"]} == set(authority["function_ids"])
    assert {item["owner"] for item in authority["functions"]} == {"med-autoscience"}
    boundary_by_id = {item["boundary_id"]: item for item in authority["stage_quality_gate_boundaries"]}
    assert set(boundary_by_id) == set(authority["boundary_ids"])
    assert {item["program_role"] for item in boundary_by_id.values()} == {
        "validator",
        "materializer",
        "guard",
    }
    for item in boundary_by_id.values():
        assert item["requires_ai_first_record"] is True
        assert item["route_back_semantics"].startswith("route_back_to_")
        assert item["typed_blocker_semantics"].endswith("_blocker")
        assert item["required_record_refs"]
        assert any(
            "stage_quality_pack:" in ref
            or ref in {"AI reviewer workflow", "AI reviewer-backed publication eval"}
            for ref in item["trace_refs"]
        )
    function_by_id = {item["function_id"]: item for item in authority["functions"]}
    for function_id in [
        "publication_quality_verdict",
        "ai_reviewer_quality_decision",
        "publication_route_memory_accept_reject",
        "source_readiness_verdict",
    ]:
        item = function_by_id[function_id]
        assert item["boundary_id"] in boundary_by_id
        assert item["judgment_mode"] == "ai_first_stage_gate"
        assert item["decision_output_owner"] == "independent_reviewer_auditor_agent"
        assert item["program_may_emit_pass_ready_verdict"] is False
        assert item["missing_ai_first_record_policy"] == "typed_blocker_or_route_back"
        assert item["standard_stage_output"] is True
        assert item["requires_ai_first_record"] is True
        assert item["program_role"] in {"validator", "guard"}
        assert item["route_back_semantics"].startswith("route_back_to_")
        assert item["typed_blocker_semantics"].endswith("_blocker")
        assert set(item["trace_refs"]) <= set(boundary_by_id[item["boundary_id"]]["trace_refs"])
    artifact_auth = function_by_id["artifact_mutation_authorization"]
    assert artifact_auth["judgment_mode"] == "ai_first_record_validator"
    assert artifact_auth["decision_output_owner"] == "independent_reviewer_auditor_agent"
    assert artifact_auth["program_may_emit_pass_ready_verdict"] is False
    assert artifact_auth["requires_ai_first_record"] is True
    assert artifact_auth["program_role"] == "materializer"
    assert function_by_id["owner_receipt_signer"]["judgment_mode"] == "mechanical_guard"
    assert function_by_id["medical_helper_implementation"]["judgment_mode"] == "mechanical_guard"
    assert authority["all_other_program_surfaces"] == "opl_generated_or_domain_refs_projection_source"
    assert authority["forbidden_long_term_mas_shell_owners"] == [
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
    classification = boundary["functional_surface_classification"]
    assert classification["declarative_pack_generated_surface"] == [
        "workspace_source_intake_shell",
        "workbench_portal_generic_shell",
        "owner_route_reconcile_materialize_dispatch_shell",
        "generic_cli_mcp_product_wrappers",
        "generic_daemon_or_scheduler_lifecycle",
        "generic_queue_attempt_retry_dead_letter",
        "generic_transition_runner",
    ]
    assert classification["domain_authority_refs"] == [
        "domain_authority_refs_index",
        "paper_work_unit_outbox_index",
        "runtime_storage_maintenance",
        "publication_route_memory_locator_transport_shell",
        "artifact_lifecycle_storage_audit_shell",
    ]
    assert set(classification["minimal_authority_function"]) == {
        "study_truth",
        "progress_projection",
        "domain_health_diagnostic",
        "publication_quality_verdict",
        "ai_reviewer_workflow",
        "publication_gate",
        "artifact_authority",
        "owner_receipt",
        "domain_transition_table",
        "publication_route_memory_body",
        "memory_writeback_decision",
        "typed_blocker",
        "safe_action_refs",
    }
    assert "legacy_cleanup_no_active_caller_gate" not in classification
    assert set(classification["legacy_cleanup_tombstone_provenance"]) == {
        "mas_generic_workbench_shell",
        "legacy_scheduler_default_aliases",
        "daemonish_terminal_attach_status_as_runtime_owner",
        "scheduler_legacy_residue_tombstone_provenance",
    }
    assert set(classification["legacy_cleanup_physical_retired"]) == {
        "local_launchd_scheduler_install_path",
        "domain_health_diagnostic_loop_shell",
        "workspace_local_watch_service_wrappers",
    }
    inventory = boundary["functional_module_inventory"]
    assert len(inventory) == 18
    by_id = {item["module_id"]: item for item in inventory}
    lifecycle_item = by_id["domain_authority_refs_index"]
    assert lifecycle_item["code_paths"] == [
        "src/med_autoscience/runtime_protocol/domain_authority_refs_index.py",
        "src/med_autoscience/opl_domain_pack/",
        "src/med_autoscience/controllers/owner_route_handoff_parts/substrate_adapter.py",
    ]
    assert lifecycle_item["current_ref_status"] == (
        "domain_authority_refs_index_no_runtime_lifecycle_owner"
    )
    assert lifecycle_item["migration_action"] == (
        "declare_domain_authority_refs_index_and_consume_opl_current_control_state"
    )
    refs_only_retirement_gates = {
        item["module_id"]: item for item in boundary["domain_authority_refs_retirement_gates"]
    }
    assert set(refs_only_retirement_gates) == set(classification["domain_authority_refs"])
    for module_id in classification["domain_authority_refs"]:
        gate = by_id[module_id]["retirement_gate"]
        assert gate == refs_only_retirement_gates[module_id]
        assert gate["classification"] == "domain_authority_refs"
        assert gate["domain_ref_consumer_count"] > 0
        assert gate["domain_ref_consumer_refs"]
        assert gate["generic_owner_claim_allowed"] is False
        assert gate["can_emit_paper_closure_verdict"] is False
        assert gate["can_emit_generic_owner_verdict"] is False
        assert "paper_closure_verdict" in gate["must_not_emit"]
        if module_id == "domain_authority_refs_index":
            assert "domain_authority_refs_replaced_by_opl_generated_ref_index" in gate[
                "delete_or_tombstone_after"
            ]
        else:
            assert gate["delete_or_tombstone_after"]
            assert all("active_caller_count" not in item for item in gate["delete_or_tombstone_after"])
    assert set(lifecycle_item["forbidden_mas_roles"]) == {
        "generic_persistence_engine",
        "generic_lifecycle_engine",
        "generic_runtime_lifecycle_owner",
        "generic_restore_retention_owner",
    }
    assert by_id["owner_route_reconcile_materialize_dispatch_shell"]["migration_action"] == (
        "declare_owner_route_policy_and_consume_opl_runtime_manager_loop"
    )
    wrapper_item = by_id["generic_cli_mcp_product_wrappers"]
    assert wrapper_item["domain_ref_consumers"] == [
        "MAS CLI",
        "MCP tool handlers",
        "skill direct domain entry",
        "product-entry manifest",
    ]
    assert wrapper_item["authority_boundary"] == (
        "opl_generates_wrapper_and_skill_metadata_mas_executes_domain_authority_handlers"
    )
    assert "generated_surface_handoff.skill" in wrapper_item["proof_refs"]
    assert by_id["publication_quality_verdict"]["cannot_absorb_reason"] == (
        "OPL cannot authorize manuscript quality, publication readiness, or medical reviewer verdicts."
    )
    assert by_id["local_launchd_scheduler_install_path"]["default_caller_count"] == 0
    assert by_id["local_launchd_scheduler_install_path"]["install_allowed"] is False
    assert by_id["local_launchd_scheduler_install_path"]["trigger_allowed"] is False
    assert by_id["local_launchd_scheduler_install_path"]["write_install_proof_allowed"] is False
    assert by_id["local_launchd_scheduler_install_path"]["resurrection_allowed"] is False
    assert by_id["local_launchd_scheduler_install_path"]["classification"] == (
        "legacy_cleanup_physical_retired"
    )
    assert by_id["local_launchd_scheduler_install_path"]["no_resurrection_gate"][
        "default_caller_count"
    ] == 0
    assert boundary["functional_module_inventory_summary"]["classification_counts"] == {
        "declarative_pack_generated_surface": 7,
        "domain_authority_refs": 5,
        "minimal_authority_function": 3,
        "legacy_cleanup_physical_retired": 3,
    }
    assert boundary["functional_module_inventory_summary"]["retired_legacy_residue_count"] == 4
    assert boundary["functional_module_inventory_summary"]["legacy_cleanup_items_tombstoned"] == [
        "mas_generic_workbench_shell",
        "legacy_scheduler_default_aliases",
        "daemonish_terminal_attach_status_as_runtime_owner",
        "scheduler_legacy_residue_tombstone_provenance",
    ]
    assert boundary["functional_module_inventory_summary"]["classification_gap_count"] == 0
    assert boundary["functional_module_inventory_summary"]["functional_structure_gap_count"] == 0
    assert boundary["functional_module_inventory_summary"]["active_private_generic_residue_count"] == 0
    assert (
        boundary["functional_module_inventory_summary"]["remaining_gap_classification"]
        == "live_provider_paper_line_evidence_gates"
    )
    assert boundary["functional_module_inventory_summary"]["long_term_opl_owned_replacement_count"] == 0
    assert boundary["functional_module_inventory_summary"]["retire_tombstone_classification_count"] == 0
    followthrough_summary = boundary["functional_followthrough_gap_summary"]
    assert followthrough_summary["surface_kind"] == "mas_functional_followthrough_gap_summary"
    assert followthrough_summary["status"] == "functional_structure_closed_evidence_gates_remaining"
    assert followthrough_summary["classification_gap_count"] == 0
    assert followthrough_summary["functional_structure_gap_count"] == 0
    assert followthrough_summary["active_private_generic_residue_count"] == 0
    assert followthrough_summary["remaining_gap_classification"] == (
        "live_provider_paper_line_evidence_gates"
    )
    assert followthrough_summary["remaining_items_are_evidence_gates"] is True
    assert followthrough_summary["classification_counts"] == boundary["functional_module_inventory_summary"][
        "classification_counts"
    ]
    assert followthrough_summary["legacy_cleanup_items_are_remaining_active_gaps"] is False
    assert followthrough_summary["legacy_cleanup_items_have_default_entry"] is False
    assert followthrough_summary["legacy_cleanup_items_physical_retired"] == [
        "local_launchd_scheduler_install_path",
        "workspace_local_watch_service_wrappers",
        "domain_health_diagnostic_loop_shell",
    ]
    assert followthrough_summary["legacy_cleanup_items_tombstoned"] == [
        "mas_generic_workbench_shell",
        "legacy_scheduler_default_aliases",
        "daemonish_terminal_attach_status_as_runtime_owner",
        "scheduler_legacy_residue_tombstone_provenance",
    ]
    assert followthrough_summary["legacy_cleanup_items_have_standard_template_refs"] is False
    assert followthrough_summary["remaining_functional_followthrough_gate_ids"] == []
    assert followthrough_summary["remaining_functional_followthrough_gates"] == []
    assert followthrough_summary["closed_functional_structure_gate_ids"] == [
        "generated_surface_default_owner_cutover",
        "domain_authority_refs_thinning",
        "legacy_cleanup_physical_retirement",
        "opl_app_workbench_drilldown",
        "lifecycle_locator_retention_restore_ledger_reconciliation",
    ]
    assert followthrough_summary["does_not_clear"] == (
        followthrough_summary["remaining_evidence_gate_ids"]
    )
    assert followthrough_summary["remaining_evidence_gate_ids"] == [
        "live_provider_paper_apply_scaleout",
        "publication_route_memory_receipt_scaleout",
        "artifact_lifecycle_receipt_scaleout",
        "provider_slo_long_soak",
    ]
    assert {item["owner"] for item in followthrough_summary["remaining_evidence_gates"]} == {
        "med-autoscience",
        "one-person-lab",
    }
    assert {item["functional_structure_gap"] for item in followthrough_summary["remaining_evidence_gates"]} == {
        False
    }
    assert "mas_owned_generic_queue" in followthrough_summary["forbidden_remaining_functional_gap_claims"]
    physical_evidence = boundary["physical_thinning_evidence"]
    assert physical_evidence["surface_kind"] == "mas_physical_thinning_evidence"
    assert physical_evidence["status"] == (
        "generic_runtime_residue_closed_as_boundary_evidence_physical_delete_gated"
    )
    assert physical_evidence["body_included"] is False
    assert physical_evidence["does_not_claim_physical_delete"] is True
    assert physical_evidence["does_not_claim_paper_closure"] is True
    assert physical_evidence["evidence_contract_ref"] == (
        "contracts/evidence/mas-evidence-lane.json#/physical_thinning_evidence"
    )
    physical_groups = {item["group_id"]: item for item in physical_evidence["residue_groups"]}
    assert set(physical_groups) == {
        "runner_residue",
        "supervisor_residue",
        "workbench_residue",
        "lifecycle_refs_residue",
    }
    for item in physical_groups.values():
        assert item["generic_owner_claim_allowed"] is False
        assert item["physical_delete_gate"]
        assert item["evidence_refs"]
    assert physical_groups["lifecycle_refs_residue"]["current_role"] == (
        "refs_only_domain_authority_receipt_locator_index"
    )
    assert physical_evidence["active_path_residue_cleanup_gates_ref"] == (
        "functional_consumer_boundary.active_path_residue_cleanup_gates"
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
        "owner_route_handoff_domain_ref_entry",
        "status_projection_domain_truth_refs",
        "legacy_supervisor_scheduler_tombstone",
    }
    physically_retired_residue_ids = {
        "runtime_transport_core_bridge",
        "runtime_turn_runner_closeout_adapter",
        "worker_lease_residency_projection",
        "lifecycle_refs_sqlite_index",
    }
    for residue_id in physically_retired_residue_ids:
        gate = cleanup_gates[residue_id]
        assert gate["current_disposition"] == "physically_retired"
        assert gate["current_role"] == "none_physically_retired_no_alias"
        assert gate["current_paths"] == []
        assert gate["physical_delete_completed"] is True
        assert gate["physical_delete_permitted"] is True
        assert gate["resurrection_alias_or_wrapper_allowed"] is False
        assert gate["archive_permitted"] is False
        assert gate["tombstone_permitted"] is False
        assert "paper_closure_verdict" in gate["must_not_emit"]
    domain_ref_residue_ids = {
        "workbench_shell_domain_projection_refs",
        "owner_route_handoff_domain_ref_entry",
        "status_projection_domain_truth_refs",
    }
    for residue_id in domain_ref_residue_ids:
        gate = cleanup_gates[residue_id]
        assert gate["current_disposition"] == "domain_projection_refs_only_no_runtime_control_alias"
        assert gate["domain_ref_consumer_count"] > 0
        assert gate["stale_surface_scan_clean"] is False
        assert gate["physical_delete_permitted"] is False
        assert gate["archive_permitted"] is False
        assert gate["rename_permitted"] is False
        assert gate["tombstone_permitted"] is False
        assert gate["no_resurrection_alias_or_wrapper_allowed"] is False
        assert gate["delete_or_tombstone_after"] == [
            "stale_surface_scan_clean",
            "opl_replacement_parity_proven",
            "domain_receipt_parity_proven",
            "focused_tests_green",
            "no_forbidden_write_proof",
            "history_tombstone_refs_recorded",
        ]
        assert "paper_closure_verdict" in gate["must_not_emit"]
    tombstone_gate = cleanup_gates["legacy_supervisor_scheduler_tombstone"]
    assert tombstone_gate["current_disposition"] == "tombstone_only"
    assert tombstone_gate["stale_surface_scan_clean"] is True
    assert tombstone_gate["physical_delete_permitted"] is False
    assert tombstone_gate["tombstone_permitted"] is True
    assert "mas_owned_generic_persistence_engine" in physical_evidence["forbidden_claims"]
    assert "resurrection_alias_or_wrapper_for_retired_runtime_path" in physical_evidence[
        "forbidden_claims"
    ]
    assert "physical_delete_claim_without_replacement_proof" in physical_evidence["forbidden_claims"]
    retirement_matrix = boundary["physical_retirement_gate_matrix"]
    assert retirement_matrix["surface_kind"] == "mas_generated_caller_retirement_gate_matrix"
    assert retirement_matrix["status"] == "physical_delete_blocked_until_all_gate_inputs_hold"
    assert retirement_matrix["default_caller_boundary_ref"] == (
        "functional_consumer_boundary.generated_default_caller_boundary"
    )
    assert retirement_matrix["opl_default_caller_readiness_ref"] == (
        "functional_consumer_boundary.generated_default_caller_boundary."
        "opl_default_caller_readiness_evidence"
    )
    assert retirement_matrix["physical_delete_requires_all_gates"] == [
        "stale_surface_scan_clean",
        "opl_replacement_parity",
        "mas_owner_receipt_parity",
        "focused_tests_green",
        "no_forbidden_write_proof",
        "tombstone_refs_landed",
    ]
    candidates = {item["surface_id"]: item for item in retirement_matrix["retirement_candidates"]}
    assert set(candidates) == {
        "runtime_transport",
        "domain_authority_refs_index",
        "workbench_shell",
        "owner_route_handoff",
        "status_projection",
    }
    for surface_id, candidate in candidates.items():
        assert candidate["physical_delete_permitted"] is False
        assert candidate["mas_default_runtime_owner_allowed"] is False
        assert candidate["gate_results"]["opl_default_caller_readiness"]
        assert candidate["gate_results"]["tombstone_refs_landed"] in {
            "required_before_delete",
            "landed_for_retired_legacy_only",
            "not_required_for_no_alias_physical_retirement",
        }
    assert candidates["runtime_transport"]["current_ref_status"] == "physical_retired_no_alias"
    assert "src/med_autoscience/runtime_transport/" in candidates["runtime_transport"]["code_paths"]
    assert candidates["domain_authority_refs_index"]["current_ref_status"] == (
        "domain_authority_refs_index_active_no_runtime_lifecycle_owner"
    )
    assert candidates["workbench_shell"]["gate_results"]["opl_replacement_parity"] == (
        "structural_default_caller_ready_generated_workbench_default_required"
    )
    assert candidates["owner_route_handoff"]["gate_results"]["mas_owner_receipt_parity"] == (
        "pending_real_paper_line_owner_receipt_or_stable_typed_blocker"
    )
    assert candidates["owner_route_handoff"]["deletion_readiness_worklist_ref"] == (
        "functional_consumer_boundary.active_path_residue_cleanup_gates."
        "owner_route_handoff_domain_ref_entry.deletion_readiness_worklist"
    )
    assert (
        "owner_route_handoff_response.forbidden_write_guard_proof"
        in candidates["owner_route_handoff"]["no_forbidden_write_proof_refs"]
    )
    assert candidates["status_projection"]["mas_role"] == "domain_truth_status_projection"
    assert cleanup_gates["workbench_shell_domain_projection_refs"]["current_role"] == (
        "domain_projection_refs_for_opl_workbench"
    )
    assert cleanup_gates["workbench_shell_domain_projection_refs"]["domain_ref_consumer_count"] == 3
    assert cleanup_gates["owner_route_handoff_domain_ref_entry"]["current_role"] == (
        "domain_owner_route_handoff_refs"
    )
    assert cleanup_gates["owner_route_handoff_domain_ref_entry"]["domain_ref_consumer_count"] == 1
    sidecar_worklist = cleanup_gates["owner_route_handoff_domain_ref_entry"]["deletion_readiness_worklist"]
    assert sidecar_worklist["surface_kind"] == "mas_owner_route_handoff_domain_ref_entry_deletion_readiness"
    assert sidecar_worklist["status"] == "blocked_domain_owner_route_handoff_ref_consumer_present_no_runtime_control_owner"
    assert sidecar_worklist["can_delete"] is False
    assert sidecar_worklist["domain_ref_consumer_count"] == 1
    assert {item["gate"] for item in sidecar_worklist["missing_gate_inputs"]} == {
        "opl_generated_sidecar_consumes_domain_refs",
        "opl_replacement_parity_proven",
        "domain_receipt_parity_proven",
        "focused_tests_green",
        "no_forbidden_write_proof",
        "history_tombstone_refs_recorded",
    }
    assert "current_package.zip" in sidecar_worklist["must_not_write"]
    assert "physical_delete_complete" in sidecar_worklist["must_not_claim"]
    assert (
        "tests/test_cli_cases/owner_route_handoff_command_cases/dispatch_cases.py"
        in sidecar_worklist["focused_test_refs"]
    )
    assert cleanup_gates["status_projection_domain_truth_refs"]["current_role"] == (
        "domain_truth_status_projection"
    )
    assert cleanup_gates["status_projection_domain_truth_refs"]["domain_ref_consumer_count"] == 2
    assert retirement_matrix["no_resurrection_summary"] == {
        "all_runtime_control_surfaces_retired_or_opl_owned": True,
        "default_runtime_owner": "one-person-lab",
        "mas_default_runtime_owner_allowed": False,
        "physical_delete_candidate_count": 5,
        "physical_delete_ready_count": 1,
        "physically_retired_surface_ids": ["runtime_transport"],
        "remaining_surfaces_are_domain_refs_not_runtime_control": True,
    }
    tombstones = boundary["retired_legacy_residue_tombstones"]
    assert {item["residue_id"] for item in tombstones} == set(
        classification["legacy_cleanup_tombstone_provenance"]
    )
    for item in tombstones:
        assert item["current_role"] == "history_tombstone_provenance_only"
        assert item["domain_ref_consumer_count"] == 0
        assert item["default_entry_allowed"] is False
        assert item["retirement_gate"] == "no_resurrection_tombstone"
        assert "paper_closure_verdict" in item["must_not_emit"]
    assert by_id["workspace_local_watch_service_wrappers"]["tombstone_required"] is True
    lifecycle_role = boundary["domain_authority_refs_index_role"]
    assert lifecycle_role["classification"] == "domain_authority_refs"
    assert lifecycle_role["current_mas_role"] == "domain_authority_receipt_and_locator_ref_index"
    assert lifecycle_role["authority"] == (
        "refs_only_domain_authority_index_not_generic_runtime_lifecycle_engine"
    )
    assert lifecycle_role["owner"] == "one-person-lab"
    assert lifecycle_role["mas_may_index_domain_receipts"] is True
    assert lifecycle_role["mas_may_claim_generic_persistence_engine"] is False
    assert lifecycle_role["mas_consumes_opl_current_control_state_refs"] is True
    assert lifecycle_role["mas_may_write_domain_truth"] is False
    assert set(lifecycle_role["forbidden_mas_roles"]) == {
        "generic_persistence_engine",
        "generic_lifecycle_engine",
        "generic_runtime_lifecycle_owner",
        "generic_restore_retention_owner",
    }
    assert lifecycle_role["replacement_expectation"]["expected_replacements"] == [
        "opl_runtime_lifecycle_index_contract",
        "opl_artifact_lifecycle_storage_audit_shell",
        "opl_app_workbench_shell",
        "opl_provider_scheduler_lifecycle",
        "opl_queue_attempt_retry_dead_letter",
        "opl_generic_transition_runner",
    ]
    coverage = boundary["opl_functional_harness_consumer_coverage"]
    assert coverage["status"] == "landed_domain_authority_pack_consumer"
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
    assert (
        coverage["refs_only_memory_writeback_chain"]["opl_can_accept_or_reject_writeback"]
        is False
    )
    assert coverage["queue_stage_attempt_typed_closeout"]["queue_completion_is_paper_closure"] is False
    assert (
        coverage["generic_transition_runner"]["runner_completion_can_authorize_publication"]
        is False
    )
    assert (
        coverage["restart_dead_letter_repair_human_gate_state_chain"][
            "state_chain_completion_is_publication_ready"
        ]
        is False
    )
    assert "product_entry_manifest.functional_consumer_boundary" in boundary["proof_surfaces"]
    assert "mas_owned_generic_queue" in boundary["forbidden_regressions"]
    assert boundary["no_resurrection_proof"] == {
        "status": "legacy_local_scheduler_physical_retired",
        "default_caller_count": 0,
        "default_manager": "opl",
        "replacement_owner_surface": "opl_provider_runtime_manager",
        "legacy_local_install_path_role": "physical_retired_tombstone_provenance_only",
        "cleanup_only_commands": [],
        "forbidden_explicit_callers": [
            "runtime-supervision-status --profile <profile> --manager local",
            "runtime-ensure-supervision --profile <profile> --manager local",
            "runtime-remove-supervision --profile <profile> --manager local",
        ],
        "forbidden_default_callers": [
            "cli_default_local_scheduler_install",
            "workspace_bootstrap_local_scheduler_install",
            "product_entry_local_scheduler_install",
            "sidecar_local_scheduler_install",
            "mcp_local_scheduler_install",
        ],
        "proof_items": [
            "cli_default_manager_is_opl",
            "cli_manager_choices_exclude_local",
            "workspace_bootstrap_manager_is_opl",
            "product_entry_consumes_opl_replacement_projection",
            "sidecar_exports_functional_boundary_no_generic_owner",
            "local_scheduler_status_remove_path_returns_tombstone_only",
            "local_scheduler_install_proof_generation_forbidden",
            "local_scheduler_launchagent_adapter_deleted",
        ],
    }
    retirement_proof = boundary["legacy_local_scheduler_physical_retirement_proof"]
    assert retirement_proof["install_allowed"] is False
    assert retirement_proof["status_allowed"] is False
    assert retirement_proof["remove_allowed"] is False
    assert retirement_proof["trigger_allowed"] is False
    assert retirement_proof["write_install_proof_allowed"] is False
    assert retirement_proof["default_cli_exposes_local_install"] is False
    assert retirement_proof["default_bootstrap_exposes_local_install"] is False
    assert retirement_proof["cleanup_status"] == "tombstone_only"
    assert retirement_proof["remaining_physical_delete_blockers"] == []
