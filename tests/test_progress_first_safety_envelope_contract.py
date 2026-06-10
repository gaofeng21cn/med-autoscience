from __future__ import annotations

import json
from pathlib import Path

import pytest


pytestmark = pytest.mark.meta

REPO_ROOT = Path(__file__).resolve().parents[1]


def _envelope() -> dict[str, object]:
    return json.loads(
        (REPO_ROOT / "contracts" / "progress_first_safety_envelope.json").read_text(
            encoding="utf-8"
        )
    )


def _stage_run_profile() -> dict[str, object]:
    return json.loads(
        (REPO_ROOT / "contracts" / "stage_run_kernel_profile.json").read_text(
            encoding="utf-8"
        )
    )


def _evo_contract() -> dict[str, object]:
    return json.loads(
        (REPO_ROOT / "contracts" / "evo_scientist_progress_accelerator.json").read_text(
            encoding="utf-8"
        )
    )


def test_safety_envelope_declares_progress_first_scope_without_authority_claims() -> None:
    envelope = _envelope()

    assert envelope["surface_kind"] == "mas_progress_first_safety_envelope"
    assert envelope["version"] == "progress-first-safety-envelope.v1"
    assert envelope["state"] == "active_contract"
    assert "current_owner_delta" in envelope["ordinary_progress_spine"]
    assert "ProgressDeltaReceipt_or_OwnerReceipt_or_TypedBlocker" in envelope[
        "ordinary_progress_spine"
    ]
    assert {
        "provider_completion",
        "zero_open_worklist",
        "ranking_or_tournament_win",
        "sidecar_observation_memory_written",
        "same_invocation_self_review",
    } <= set(envelope["global_non_authority_signals"])

    closeout = envelope["closeout_authority"]
    assert {
        "OwnerReceipt",
        "TypedBlocker",
        "independent_reviewer_or_auditor_record_ref",
        "canonical_paper_or_artifact_delta_ref",
    } <= set(closeout["accepted_progress_outputs"])
    assert {
        "mas_owner_receipt_or_stable_typed_blocker",
        "same_work_unit_identity",
        "currentness_basis",
        "required_output_surface",
        "forbidden_write_boundary",
    } <= set(closeout["domain_closeout_requires"])
    assert {
        "domain_ready",
        "publication_ready",
        "submission_ready",
        "artifact_mutation",
        "memory_accept_reject",
        "current_package_update",
        "production_ready",
    } <= set(closeout["cannot_authorize"])


def test_external_learning_adoption_closure_requires_functional_landing_status() -> None:
    policy = _envelope()["external_learning_adoption_closure_policy"]

    assert policy["surface_kind"] == "mas_external_learning_adoption_closure_policy"
    assert policy["role"] == "landing_status_contract_for_external_research_agent_intake"
    assert policy["default_posture"] == "contract_intake_is_not_functional_landing"
    assert {
        "Co-Scientist",
        "Nature-skills",
        "Academic Research Skills",
        "AutoSci/OmegaWiki",
        "EvoScientist/EvoSkills",
        "ARK",
        "ARIS",
        "PaperSpine",
        "Open Auto Research",
        "Light0305/Light",
    } <= set(policy["applies_to_source_families"])
    assert policy["accepted_landing_statuses"] == [
        "owner_surface_landed",
        "read_model_landed",
        "sidecar_or_worker_landed",
        "contract_projection_landed",
    ]
    assert policy["gap_statuses"] == [
        "contract_only_gap",
        "projection_only_gap",
        "history_only_gap",
        "not_landed_gap",
    ]
    assert {
        "adopt_contract",
        "reference_intake_recorded",
        "design_doc_recorded",
        "read_model_projection_without_owner_or_worker_consumption",
    } <= set(policy["non_landing_signals"])
    assert {
        "mas_owner_surface_consumes_pattern",
        "generated_or_read_model_projection_is_consumed_by_owner",
        "worker_or_sidecar_execution_slot_declared",
        "callable_or_action_catalog_entry_declared",
        "quality_pack_consumer_declared",
        "controller_authorized_soak_declared",
    } <= set(policy["functional_landing_requires_one_of"])
    assert {
        "required_inputs",
        "allowed_writes",
        "forbidden_authority",
        "output_refs",
        "nonblocking_or_fail_open_policy",
        "verification_gate",
    } <= set(policy["worker_or_sidecar_boundary_requires"])
    assert {
        "landing_status",
        "missing_landing_surface",
        "next_safe_landing_path",
        "verification_gate",
    } <= set(policy["gap_reporting_requires"])

    ordinary = policy["ordinary_progress_policy"]
    assert ordinary["external_learning_is_admission_layer"] is False
    assert ordinary["missing_external_advisory_blocks_current_owner_action"] is False
    assert ordinary["missing_worker_or_projection_blocks_current_owner_action"] is False
    assert ordinary["hard_gate_escalation_requires_current_delta_route_required_ref"] is True
    assert {
        "source_data_or_evidence",
        "owner_route_identity",
        "forbidden_write_boundary",
        "irreversible_mutation_authorization",
        "independent_reviewer_record",
        "publication_gate",
        "human_gate",
        "mas_hard_gate",
    } <= set(ordinary["hard_gate_ref_families"])


def test_safety_envelope_covers_all_false_completion_and_drift_risk_classes() -> None:
    risks = {risk["risk_id"]: risk for risk in _envelope()["risk_classes"]}

    assert set(risks) == {
        "false_completion",
        "pseudo_evidence",
        "stale_read_model",
        "duplicate_receipt",
        "artifact_authority_drift",
    }

    false_completion = risks["false_completion"]
    assert false_completion["fail_policy"] == (
        "fail_closed_to_typed_blocker_or_route_back_without_claiming_ready"
    )
    assert {
        "script_success",
        "test_pass",
        "queue_completion",
        "provider_completion",
        "same_invocation_self_review",
    } <= set(false_completion["forbidden_completion_signals"])

    pseudo = risks["pseudo_evidence"]
    assert pseudo["primary_guard"] == "body_free_ref_authority_boundary"
    assert pseudo["fail_policy"] == (
        "missing_route_required_evidence_returns_named_ref_family_typed_blocker"
    )
    assert pseudo["ordinary_progress_policy"] == (
        "missing_non_required_advisory_is_observability_not_blocker"
    )

    stale = risks["stale_read_model"]
    assert stale["canonical_current_source"] == "current_work_unit"
    assert stale["valid_current_statuses"] == [
        "executable_owner_action",
        "running_provider_attempt",
        "typed_blocker",
        "blocked_current_work_unit",
    ]
    assert "legacy_control_next_action_without_binding" in stale[
        "stale_sources_must_be_diagnostic_only"
    ]

    duplicate = risks["duplicate_receipt"]
    assert {
        "work_unit_id",
        "work_unit_fingerprint",
        "action_type",
        "source_fingerprint",
        "idempotency_key",
    } <= set(duplicate["required_identity_fields"])
    assert duplicate["fail_policy"] == (
        "do_not_redrive_same_work_unit_without_new_target_surface_or_typed_blocker"
    )

    artifact = risks["artifact_authority_drift"]
    assert "owner_authorized_artifact_mutation_receipt" in artifact[
        "allowed_artifact_authority_shapes"
    ]
    assert {
        "file_presence",
        "stage_folder_manifest_only",
        "locator_index_entry",
        "lifecycle_report",
        "current_package_path_exists",
    } <= set(artifact["forbidden_artifact_authority_substitutes"])
    assert artifact["ordinary_progress_policy"] == (
        "artifact_locator_updates_are_platform_repair_unless_owner_authorized_delta_ref_exists"
    )


def test_hybrid_policy_is_owner_native_jit_affordance_not_budgeted_sidecar() -> None:
    policy = _envelope()["hybrid_progress_accelerator_policy"]

    assert policy["surface_kind"] == "mas_light_coscientist_progress_first_hybrid_policy"
    assert policy["role"] == "current_owner_native_jit_affordance"
    assert policy["ordinary_path_root"] == "current_owner_delta"
    assert (
        policy["default_posture"]
        == "affordance_available_no_standing_sidecar_no_default_scan_current_delta_declares_or_implies_affordance_need"
    )
    assert policy["default_design"] == "ordinary_progress_has_no_extra_advisory_stage"
    assert policy["standing_sidecar_enabled"] is False
    assert policy["standing_advisory_scan_each_attempt"] is False
    assert policy["affordance_invocation_default"] == "none"
    assert policy["affordance_invocation_trigger"] == (
        "current_delta_declares_or_implies_affordance_need"
    )
    assert policy["affordance_invocation_only_when"] == [
        "current_owner_action_declares_named_ref_family_or_briefing_need",
        "current_delta_shape_implies_named_ref_family_or_briefing_need",
        "owner_route_requires_named_ref_family_for_current_delta",
        "owner_route_shape_implies_repair_context_or_arbitration_need_for_current_delta",
        "typed_blocker_or_route_back_requests_specific_repair_context",
        "independent_reviewer_or_publication_gate_requests_specific_brief",
        "stop_loss_or_repeated_failure_requires_route_arbitration",
    ]
    assert {
        "current_work_unit_identity",
        "target_surface",
        "requested_ref_family_or_question",
        "owner_policy",
        "bounded_output_shape",
        "no_new_default_next_action",
    } <= set(policy["affordance_invocation_must_bind"])
    assert {
        "always_generate_micro_candidates",
        "always_run_next_delta_tournament",
        "always_run_meta_review",
        "always_prefetch_context",
        "always_scan_memory",
        "always_score_routes",
        "build_complete_external_skill_map_before_dispatch",
    } <= set(policy["forbidden_default_motions"])
    assert policy["can_generate_default_next_action"] is False
    assert policy["can_block_current_owner_action"] is False
    assert policy["missing_sidecar_blocks_dispatch"] is False
    assert policy["full_research_lifecycle_preflight_each_delta"] is False
    assert policy["full_readiness_inventory_each_delta"] is False
    assert policy["mainline_waits_for_sidecar"] is False
    assert policy["platform_repair_or_prefetch_counts_as_paper_progress"] is False

    cap = policy["secondary_invocation_cap"]
    assert cap["role"] == "last_resort_sprawl_cap_after_jit_invocation_not_design_driver"
    assert cap["cap_applies_only_after_affordance_is_invoked"] is True
    assert cap["max_micro_candidates_per_attempt"] == 3
    assert cap["max_next_delta_tournaments_per_attempt"] == 1
    assert cap["max_reviewer_repair_hints_per_attempt"] == 3
    assert cap["max_reusable_lesson_refs_per_attempt"] == 1
    assert cap["meta_review_runs_every_attempt"] is False
    assert cap["opportunistic_prefetch_mainline_waits"] is False
    assert cap["missing_advisory_scan_blocks_owner_action"] is False

    assert policy["hard_gate_escalation_only_when"] == [
        "route_required_ref_missing_for_current_delta",
        "source_data_or_evidence_missing_for_current_delta",
        "owner_route_identity_missing_or_invalid",
        "forbidden_write_boundary_unclear",
        "irreversible_mutation_requires_authorization",
        "independent_reviewer_or_publication_gate_required_for_claimed_quality",
    ]
    assert {
        "named_missing_ref_family",
        "route_back_owner",
        "current_work_unit_identity",
        "repair_condition",
        "forbidden_shortcut_avoided",
    } <= set(policy["hard_gate_output_requires"])


def test_hybrid_policy_keeps_external_sources_as_advisory_patterns_only() -> None:
    sources = {
        item["source_id"]: item
        for item in _envelope()["hybrid_progress_accelerator_policy"]["source_patterns"]
    }

    light = sources["Light0305/Light"]
    assert light["source_role"] == "external_pattern_ref_library_invoked_by_current_owner_need"
    assert light["allowed_ref_families"] == [
        "verified_asset_ref",
        "collision_check_ref",
        "refusal_rehearsal_ref",
        "fresh_evidence_gate_ref",
    ]
    assert {
        "runtime_owner",
        "skill_router_owner",
        "knowledge_truth_owner",
        "quality_gate_owner",
        "artifact_authority_owner",
    } <= set(light["forbidden_roles"])
    assert light["missing_advisory_default"] == "no_lookup_continue_current_owner_action"

    coscientist = sources["Co-Scientist"]
    assert coscientist["source_role"] == "jit_within_stage_strategy_affordance"
    assert "ranking_ref" in coscientist["allowed_ref_families"]
    assert {
        "route_authority_by_ranking",
        "quality_gate_owner",
        "publication_ready_authority",
        "stage_promotion_authority",
    } <= set(coscientist["forbidden_roles"])
    assert coscientist["missing_advisory_default"] == "do_not_invoke_continue_current_owner_delta"

    evo = sources["EvoScientist/EvoSkills"]
    assert evo["source_role"] == "jit_learning_and_tool_affordance_pattern"
    assert "tool_affordance_ref" in evo["allowed_ref_families"]
    assert {
        "default_runtime_owner",
        "tool_authority",
        "memory_body_authority",
        "admission_gate",
        "quality_owner",
    } <= set(evo["forbidden_roles"])
    assert evo["missing_advisory_default"] == "no_op_fail_open"


def test_safety_envelope_matches_existing_stage_and_learning_sidecar_boundaries() -> None:
    envelope = _envelope()
    profile = _stage_run_profile()
    evo = _evo_contract()

    handoff = profile["ordinary_progress_handoff"]
    assert handoff["default_progress_root"] == "current_owner_delta"
    assert handoff["audit_sidecar_policy"]["can_generate_default_next_action"] is False
    assert handoff["audit_sidecar_policy"]["can_close_stage"] is False
    assert handoff["audit_sidecar_policy"]["can_claim_domain_ready"] is False
    assert handoff["progress_delta_receipt"]["cannot_authorize"] == [
        "domain_ready",
        "publication_ready",
        "submission_ready",
        "quality_or_export_ready",
        "artifact_body_mutation",
        "artifact_authority",
        "memory_accept_reject",
        "production_ready",
        "physical_delete",
    ]

    coscientist = profile["coscientist_stage_strategy_boundary"]
    assert coscientist["strategy_refs_are_advisory"] is True
    assert coscientist["strategy_refs_can_close_quality_gate"] is False
    assert coscientist["progress_jit_affordance_can_block_attempt_when_missing"] is False
    assert coscientist["opportunistic_prefetch_mainline_waits"] is False

    evo_progress = evo["ordinary_progress_policy"]
    assert evo_progress["ordinary_progress_spine"] == [
        "current_owner_delta",
        "concrete_delta",
        "ProgressDeltaReceipt_or_OwnerReceipt_or_TypedBlocker",
        "next_current_owner_delta",
    ]
    assert evo_progress["can_block_current_owner_action"] is False
    assert evo_progress["missing_learning_sidecar_blocks_dispatch"] is False
    assert evo["quality_gate_policy"]["same_attempt_review_can_close_quality_gate"] is False

    audit = envelope["audit_policy"]
    assert audit["live_path_runs_full_audit_each_delta"] is False
    assert audit["ordinary_delta_runs_jit_checks_only"] is True
    assert audit[
        "audit_findings_do_not_block_current_owner_action_unless_hard_gate_escalation_applies"
    ] is True
