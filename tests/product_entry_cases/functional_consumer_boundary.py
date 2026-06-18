from __future__ import annotations

import importlib
from pathlib import Path

from tests.standard_agent_purity_helpers import assert_standard_agent_purity_boundary

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
    assert boundary["standard_agent_purity_guard"]["status"] == "standard_agent_purity_cutover_guard"
    assert_standard_agent_purity_boundary(boundary)

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
    assert pack_input["compiler_outputs_expected"] == [
        "cli",
        "mcp",
        "skill",
        "product_entry",
        "product_status",
        "product_session",
        "domain_handler",
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
    assert set(handoff_by_id) == {
        "cli",
        "mcp",
        "skill",
        "product_entry",
        "domain_handler",
        "status",
        "workbench",
        "projection_shell",
        "test_lane_harness",
    }
    assert handoff_by_id["cli"]["target_role"] == "opl_generated_command_surface"
    assert handoff_by_id["mcp"]["target_role"] == "opl_generated_mcp_descriptor_surface"
    assert handoff_by_id["skill"]["target_role"] == "opl_generated_skill_descriptor_surface"
    assert handoff_by_id["product_entry"]["target_role"] == "opl_generated_product_entry_surface"
    assert handoff_by_id["domain_handler"]["target_role"] == "opl_generated_domain_handler_handoff_surface"
    assert handoff_by_id["status"]["target_role"] == "opl_generated_status_wrapper_over_mas_truth_refs"
    assert handoff_by_id["workbench"]["target_role"] == (
        "opl_hosted_workbench_shell_consuming_mas_refs"
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
        "product_status",
        "product_session",
        "domain_handler",
        "workbench",
    ]
    generated_surfaces = {
        item["surface_id"]: item for item in generated_default["surface_boundaries"]
    }
    assert set(generated_surfaces) == set(generated_default["default_caller_surfaces"])
    assert generated_surfaces["mcp"]["parity_ref"] == "mcp_descriptor_parity"
    assert generated_surfaces["product_entry"]["default_caller_owner"] == "one-person-lab"
    assert generated_surfaces["product_status"]["mas_allowed_role"] == (
        "domain_truth_status_projection"
    )
    assert generated_surfaces["product_session"]["mas_allowed_role"] == "domain_handler_target"
    assert generated_surfaces["domain_handler"]["mas_allowed_role"] == "domain_handler_target"
    assert generated_surfaces["domain_handler"]["parity_ref"] == "domain_handler_descriptor_parity"
    assert generated_surfaces["workbench"]["mas_allowed_role"] == "domain_projection_refs"
    assert all(item["mas_generic_owner_allowed"] is False for item in generated_surfaces.values())

    authority = boundary["minimal_authority_function_manifest"]
    assert authority["surface_kind"] == "mas_minimal_authority_function_manifest"
    assert authority["status"] == "minimal_authority_functions_only"
    assert authority["semantic_model"] == (
        "ai_first_stage_quality_gate_boundaries_not_script_function_verdicts"
    )
    assert authority["requires_ai_first_record"] is True
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
    assert authority["all_other_program_surfaces"] == "opl_generated_or_domain_refs_projection_source"
    assert authority["forbidden_long_term_mas_shell_owners"] == [
        "cli",
        "mcp",
        "skill",
        "product_entry",
        "product_status",
        "product_session",
        "domain_handler",
        "status",
        "workbench",
        "projection_shell",
        "test_lane_harness",
    ]
    classification = boundary["functional_surface_classification"]
    assert set(classification) == {
        "declarative_pack_generated_surface",
        "domain_authority_refs",
        "minimal_authority_function",
    }
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
        "paper_progress_transition_refs",
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

    inventory = boundary["functional_module_inventory"]
    assert len(inventory) == 15
    by_id = {item["module_id"]: item for item in inventory}
    assert "local_launchd_scheduler_install_path" not in by_id
    assert "workspace_local_watch_service_wrappers" not in by_id
    assert "domain_health_diagnostic_loop_shell" not in by_id
    assert by_id["domain_authority_refs_index"]["code_paths"] == [
        "src/med_autoscience/runtime_protocol/opl_state_index_source_adapter.py",
        "src/med_autoscience/runtime_protocol/domain_authority_refs_index.py",
        "src/med_autoscience/opl_domain_pack/",
        "src/med_autoscience/controllers/owner_route_handoff_parts/substrate_adapter.py",
    ]
    assert by_id["paper_progress_transition_refs"]["classification"] == "domain_authority_refs"
    assert by_id["publication_quality_verdict"]["classification"] == "minimal_authority_function"
    assert by_id["publication_quality_verdict"]["cannot_absorb_reason"] == (
        "OPL cannot authorize manuscript quality, publication readiness, or medical reviewer verdicts."
    )
    assert by_id["artifact_authority"]["migration_action"] == "authority_stays_in_mas"
    owner_dispatch_thinning = by_id["owner_route_reconcile_materialize_dispatch_shell"][
        "latest_thinning_evidence"
    ]
    assert owner_dispatch_thinning["status"] == (
        "default_executor_action_policy_single_source_landed"
    )
    assert owner_dispatch_thinning["policy_module"] == (
        "src/med_autoscience/controllers/default_executor_action_policy.py"
    )
    assert owner_dispatch_thinning["domain_repo_physical_delete_authorized"] is False
    assert "publication_eval/latest.json" in owner_dispatch_thinning["does_not_write"]
    assert "owner_chain_closed" in owner_dispatch_thinning["does_not_claim"]
    workbench_thinning = by_id["workbench_portal_generic_shell"]["latest_thinning_evidence"]
    assert workbench_thinning["status"] == (
        "opl_hosted_workbench_projection_and_read_model_materializer_landed"
    )
    materializer_boundary = workbench_thinning["read_model_materializer_boundary"]
    assert materializer_boundary["status"] == "domain_owned_read_model_materializer_no_active_workspace_helper"
    assert materializer_boundary["hosted_package_role"] == "read_model_projection_package"
    assert materializer_boundary["hosted_package_truth_role"] == "projection_only_no_workspace_runtime_truth"
    assert materializer_boundary["physical_module"] == (
        "src/med_autoscience/controllers/progress_portal_parts/read_model_materializer.py"
    )
    assert materializer_boundary["materializer_scope"] == (
        "domain_owned_payload_html_and_hosted_package_projection"
    )
    assert materializer_boundary["active_callers"] == []
    assert materializer_boundary["domain_repo_physical_delete_authorized"] is False
    assert "local_http_service_owner" in materializer_boundary["does_not_claim"]
    assert "runtime_control_owner" in materializer_boundary["does_not_claim"]
    assert "publication_eval/latest.json" in materializer_boundary["does_not_write"]
    assert "workspace_carrier_boundary" not in workbench_thinning

    followthrough = boundary["functional_followthrough_gap_summary"]
    assert followthrough["surface_kind"] == "mas_functional_followthrough_gap_summary"
    assert followthrough["status"] == "functional_structure_closed_evidence_gates_remaining"
    assert followthrough["classification_gap_count"] == 0
    assert followthrough["functional_structure_gap_count"] == 0
    assert followthrough["active_private_generic_residue_count"] == 0
    assert followthrough["remaining_items_are_evidence_gates"] is True
    assert followthrough["remaining_functional_followthrough_gate_ids"] == []
    assert "standard_agent_purity_guard" in followthrough["closed_functional_structure_gate_ids"]
    assert set(followthrough["remaining_evidence_gate_ids"]) == {
        "live_provider_paper_apply_scaleout",
        "publication_route_memory_receipt_scaleout",
        "artifact_lifecycle_receipt_scaleout",
        "provider_slo_long_soak",
    }
    owner_followthrough = followthrough["owner_followthrough_evidence"][0]
    assert owner_followthrough["surface_kind"] == (
        "mas_memory_artifact_lifecycle_owner_followthrough"
    )
    assert owner_followthrough["status"] == "typed_blocker_followthrough_recorded_not_ready"
    assert owner_followthrough["typed_blocker_ref_count"] == 25
    assert owner_followthrough["closes_work_order_followthrough"] is True
    assert owner_followthrough["closes_artifact_lifecycle_receipt_scaleout"] is False
    assert owner_followthrough["ready_claim_authorized"] is False

    lifecycle_role = boundary["domain_authority_refs_index_role"]
    assert lifecycle_role["classification"] == "domain_authority_refs"
    assert lifecycle_role["current_mas_role"] == "domain_authority_receipt_and_locator_ref_index"
    assert lifecycle_role["mas_may_claim_generic_persistence_engine"] is False
    assert lifecycle_role["mas_consumes_opl_current_control_state_refs"] is True
    assert lifecycle_role["mas_may_write_domain_truth"] is False

    coverage = boundary["opl_functional_harness_consumer_coverage"]
    assert coverage["status"] == "landed_domain_authority_pack_consumer"
    assert coverage["opl_harness_pass_is_paper_closure"] is False
    assert coverage["opl_harness_pass_is_publication_ready"] is False
    assert coverage["mas_owns_generic_runtime"] is False
    assert coverage["refs_only_memory_writeback_chain"]["body_included"] is False
    assert coverage["generic_transition_runner"]["runner_completion_can_authorize_publication"] is False
