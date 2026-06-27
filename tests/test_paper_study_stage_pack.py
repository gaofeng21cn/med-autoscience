from __future__ import annotations

import json
from pathlib import Path


def _json(path: str) -> dict[str, object]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def test_independent_review_stage_has_bounded_repair_and_residual_user_review_contract() -> None:
    contract = _json("contracts/mas-paper-study-stage-pack.json")
    stage = {
        item["stage_id"]: item
        for item in contract["stages"]
    }["07-independent_review_and_revision"]

    policy = stage["bounded_review_repair_policy"]
    assert policy["max_automated_repair_rounds"] == 3
    assert policy["independent_reviewer_context_required"] is True
    assert policy["auto_advance_when_no_clear_actionable_issue"] is True
    assert policy["after_round_budget_without_hard_blocker"] == "advance_to_next_stage_with_residual_user_review"
    assert policy["residual_user_review_language"] == "zh-CN"
    assert policy["residual_user_review_artifact_role"] == "residual_reviewer_issues_user_review"
    assert policy["authority_boundary"] == {
        "residual_user_review_can_authorize_quality": False,
        "residual_user_review_can_authorize_submission": False,
        "residual_user_review_can_block_auto_advance": False,
        "publication_gate_blocks_publication_ready_claim": True,
        "publication_gate_blocks_stage_advance": False,
    }
    assert "publication_gate" not in policy["hard_blockers_still_block"]

    roles = {item["role"]: item["artifact_ref"] for item in stage["stable_artifact_roles"]}
    assert roles["residual_reviewer_issues_user_review"] == (
        "manuscript/inspection_package/residual_reviewer_issues.md"
    )


def test_mission_first_non_advancing_route_back_policy_escalates_to_mas_codex_stage() -> None:
    contract = _json("contracts/mas-paper-study-stage-pack.json")

    policy = contract["mission_first_non_advancing_route_back_policy"]

    assert policy["surface_kind"] == "mas_mission_first_non_advancing_route_back_policy"
    assert policy["policy_id"] == "mas.paper_mission.non_advancing_route_back_escalation.v1"
    assert {
        "route_back",
        "domain_gate",
        "non_advancing_apply",
        "owner_answer_shape=route_back_evidence_ref",
        "paper_mission_stage_route_domain_gate_pending",
    } <= set(policy["applies_to_terminal_shapes"])

    signature = policy["semantic_progress_signature"]
    assert {
        "study_id",
        "paper_mission_run_id",
        "stage_id",
        "current_owner",
        "action_type",
        "work_unit_id",
        "work_unit_fingerprint",
        "route_identity_key",
        "attempt_idempotency_key",
        "required_output_surface",
        "accepted_answer_shape",
        "canonical_mission_id",
        "candidate_semantic_fingerprint",
        "normalized_route_back_reason",
        "normalized_repair_scope",
    } <= set(signature["identity_fields"])
    assert {
        "owner_receipt_ref",
        "stable_typed_blocker_ref",
        "human_gate_ref",
        "route_back_evidence_ref",
        "canonical_paper_or_artifact_delta_ref",
        "ai_reviewer_or_publication_gate_delta_ref",
        "successor_work_unit_ref",
        "carry_forward_risk_receipt_ref",
        "owner_decision_packet_ref",
        "claim_decision_ref",
        "scope_decision_ref",
        "evidence_decision_ref",
        "pivot_decision_ref",
        "carry_forward_decision_ref",
        "mission_executor_continuation_ref",
    } <= set(signature["semantic_delta_fields"])
    assert {
        "queue_id",
        "stage_attempt_id",
        "active_run_id",
        "worker_readiness",
        "provider_liveness",
        "focused_test_result",
        "docs_or_contract_commit",
        "run_id",
        "quest_id",
        "temporal_workflow_id",
    } <= set(signature["transport_only_fields_do_not_change_signature"])
    assert signature["repeated_signature_without_semantic_delta_is_non_advancing"] is True

    ledger = policy["synonymous_route_back_budget_ledger"]
    assert ledger["ledger_scope"] == "cross_run_same_study_mission_signature"
    assert {
        "study_id",
        "canonical_mission_id",
        "paper_mission_run_id",
        "candidate_semantic_fingerprint",
        "normalized_route_back_reason",
        "normalized_repair_scope",
    } <= set(ledger["ledger_key_fields"])
    assert {
        "run_id",
        "quest_id",
        "queue_id",
        "stage_attempt_id",
        "active_run_id",
        "temporal_workflow_id",
        "docs_or_contract_commit",
    } <= set(ledger["fields_that_do_not_reset_budget"])
    assert {
        "owner_decision_packet_ref",
        "claim_decision_ref",
        "scope_decision_ref",
        "evidence_decision_ref",
        "pivot_decision_ref",
        "carry_forward_decision_ref",
        "mission_executor_continuation_ref",
    } <= set(ledger["budget_reset_requires_one_of"])
    assert ledger["second_synonymous_route_back_without_reset"] == (
        "enter_mas_mission_executor_fallback"
    )
    assert ledger["budget_exhaustion_can_claim_completion"] is False

    budget = policy["budget_and_escalation_policy"]
    assert budget["second_same_signature_route_back_without_semantic_delta"] == (
        "escalate_to_mas_owned_codex_executor_stage"
    )
    assert budget["mas_mission_executor_fallback_auto_continue"] is True
    assert budget["fallback_entry_after_synonymous_budget"] == (
        "mission_executor_continue_same_stage_until_semantic_delta_or_narrow_gate"
    )
    assert budget["same_signature_opl_redrive_budget_after_escalation"] == 0
    assert budget["transport_repair_budget_after_worker_ready"] == 0
    assert budget["budget_exhaustion_is_not_completion"] is True
    assert {
        "canonical_paper_or_artifact_delta",
        "owner_receipt_ref",
        "stable_typed_blocker_ref",
        "human_gate_ref",
        "route_back_evidence_ref_with_successor_work_unit",
        "carry_forward_risk_receipt_ref",
        "open_repair_lane_proposal",
        "owner_decision_packet_ref",
        "claim_decision_ref",
        "scope_decision_ref",
        "evidence_decision_ref",
        "pivot_decision_ref",
        "carry_forward_decision_ref",
        "mission_executor_continuation_ref",
    } <= set(budget["allowed_escalation_outcomes"])

    owner_decisions = policy["ai_owner_decision_product_refs"]
    assert owner_decisions["required_when_fallback_selects_owner_decision"] is True
    assert owner_decisions["ref_families"] == [
        "claim_decision_ref",
        "scope_decision_ref",
        "evidence_decision_ref",
        "pivot_decision_ref",
        "carry_forward_decision_ref",
    ]
    assert owner_decisions["decision_kind_to_ref"] == {
        "claim_strength_adjustment": "claim_decision_ref",
        "scope_reduction": "scope_decision_ref",
        "evidence_substitution": "evidence_decision_ref",
        "research_pivot": "pivot_decision_ref",
        "carry_forward_with_residual_risk": "carry_forward_decision_ref",
    }
    assert owner_decisions["can_authorize_submission_or_publication_ready"] is False
    assert owner_decisions["can_replace_owner_receipt_or_quality_gate"] is False

    narrowing = policy["typed_blocker_and_human_gate_narrowing_policy"]
    assert narrowing["typed_blocker_requires_failed_fallback_attempts"] == [
        "claim_strength_adjustment",
        "scope_reduction",
        "evidence_substitution",
        "carry_forward_risk_receipt",
        "research_pivot_decision",
    ]
    assert narrowing["human_gate_requires_decision_owner_question"] is True
    assert narrowing["typed_blocker_must_name_smallest_owner_surface"] is True
    assert {
        "queue_empty",
        "focused_tests_only",
        "docs_or_contract_only",
        "repeated_route_back_budget_exhausted_only",
    } <= set(narrowing["forbidden_blocker_reasons"])

    executor_stage = policy["mas_owned_codex_executor_stage"]
    assert executor_stage["stage_type"] == "paper_mission_semantic_progress_executor"
    assert executor_stage["owner"] == "MedAutoScience"
    assert executor_stage["executor"] == "Codex CLI"
    assert executor_stage["auto_continue_after_synonymous_budget"] is True
    assert executor_stage["fallback_stop_condition"] == (
        "semantic_delta_owner_decision_narrow_typed_blocker_human_gate_or_repair_lane_proposal"
    )
    assert {
        "owner_decision_packet_ref",
        "claim_decision_ref",
        "scope_decision_ref",
        "evidence_decision_ref",
        "pivot_decision_ref",
        "carry_forward_decision_ref",
        "mission_executor_continuation_ref",
    } <= set(executor_stage["required_product_refs"])

    canary = policy["dm002_dm003_canary_acceptance"]
    assert canary["applies_to_studies"] == [
        "002-dm-china-us-mortality-attribution",
        "003-dpcc-primary-care-phenotype-treatment-gap",
    ]
    assert {
        "paper_mission_inspect_exposes_mas_owner_fallback_semantic_ref",
        "synonymous_route_back_budget_ledger_enters_mission_executor_fallback",
        "mission_executor_outputs_ai_owner_decision_product_ref",
        "opl_stale_running_rows_rejected_as_running_proof",
    } <= set(canary["success_requires_fresh_readback_one_of"])
    assert {
        "tests_only",
        "queue_empty_only",
        "docs_or_contract_only",
        "route_back_packet_without_changed_owner_answer_shape",
        "stale_opl_running_row_counted_as_provider_running",
    } <= set(canary["failure_cases"])
    assert canary["canary_can_claim_submission_ready"] is False
    assert canary["canary_can_claim_publication_ready"] is False
    assert canary["canary_can_claim_runtime_ready"] is False

    assert {
        "DM002_ready",
        "DM003_ready",
        "submission_ready",
        "publication_ready",
        "runtime_ready",
        "provider_running",
        "paper_progress_from_repeated_route_back",
        "paper_progress_from_domain_gate_only",
        "paper_progress_from_focused_tests_or_docs",
        "paper_progress_from_canary_contract_only",
        "paper_progress_from_queue_empty",
        "paper_progress_from_opl_hydrate_only",
    } <= set(policy["completion_and_readiness_forbidden_claims"])
    assert policy["authority_boundary"] == {
        "mas_owns_semantic_progress_detection": True,
        "mas_owns_executor_stage_type": True,
        "opl_can_transport_route_back_refs": True,
        "opl_can_decide_semantic_progress": False,
        "opl_transport_or_worker_ready_counts_as_semantic_progress": False,
        "policy_can_write_authority_surfaces": False,
        "canary_contract_can_write_runtime_or_authority": False,
        "fallback_contract_can_write_owner_receipt_or_gate": False,
    }


def test_foundry_agent_series_projects_non_advancing_policy_without_claiming_readiness() -> None:
    series_contract = _json("contracts/foundry_agent_series.json")

    policy = series_contract["mission_first_non_advancing_escalation_policy"]

    assert policy["surface_kind"] == "opl_foundry_agent_mission_first_non_advancing_escalation_policy"
    assert policy["domain_policy_ref"] == (
        "contracts/mas-paper-study-stage-pack.json#/mission_first_non_advancing_route_back_policy"
    )
    assert policy["applies_to_agents"] == ["MAS"]
    assert policy["stage_type_projection"] == {
        "mas_owned_stage_type": "paper_mission_semantic_progress_executor",
        "opl_runtime_stage_role": "provider_backing_transport_for_domain_refs",
        "codex_executor_is_first_class_stage_executor": True,
        "generic_provider_completion_counts_as_domain_progress": False,
    }
    assert policy["semantic_progress_signature_projection"][
        "same_signature_without_domain_delta_counts_as_non_advancing"
    ] is True
    assert policy["semantic_progress_signature_projection"][
        "transport_only_fields_are_observability"
    ] is True
    assert policy["route_back_budget_policy"] == {
        "same_signature_repeat_threshold": 2,
        "ledger_scope": "cross_run_same_study_mission_signature",
        "after_threshold_next_owner": "MedAutoScience.paper_mission_semantic_progress_executor",
        "after_threshold_action": (
            "mission_executor_continue_same_stage_until_semantic_delta_or_narrow_gate"
        ),
        "opl_redrive_after_worker_ready_allowed": False,
        "queue_or_worker_readiness_can_reset_budget": False,
        "transport_or_observability_fields_can_reset_budget": False,
        "budget_exhausted_can_claim_completion": False,
    }
    fallback = policy["mas_mission_executor_fallback_projection"]
    assert fallback["auto_continue_after_synonymous_budget"] is True
    assert {
        "owner_decision_packet_ref",
        "claim_decision_ref",
        "scope_decision_ref",
        "evidence_decision_ref",
        "pivot_decision_ref",
        "carry_forward_decision_ref",
        "mission_executor_continuation_ref",
    } <= set(fallback["required_product_refs"])
    assert policy["ai_owner_decision_product_refs_projection"] == {
        "domain_policy_section_ref": (
            "contracts/mas-paper-study-stage-pack.json"
            "#/mission_first_non_advancing_route_back_policy/"
            "ai_owner_decision_product_refs"
        ),
        "ref_families": [
            "claim_decision_ref",
            "scope_decision_ref",
            "evidence_decision_ref",
            "pivot_decision_ref",
            "carry_forward_decision_ref",
        ],
        "can_authorize_submission_or_publication_ready": False,
        "can_replace_owner_receipt_or_quality_gate": False,
    }
    assert policy["dm002_dm003_canary_acceptance_projection"] == {
        "domain_policy_section_ref": (
            "contracts/mas-paper-study-stage-pack.json"
            "#/mission_first_non_advancing_route_back_policy/"
            "dm002_dm003_canary_acceptance"
        ),
        "success_requires_fresh_readback": True,
        "contract_or_tests_only_can_pass": False,
        "stale_opl_running_row_can_count_as_running_proof": False,
    }
    assert {
        "domain_ready",
        "runtime_ready",
        "publication_ready",
        "submission_ready",
        "provider_running",
        "DM002_ready",
        "DM003_ready",
        "paper_progress_from_canary_contract_only",
    } <= set(policy["forbidden_public_or_readiness_claims"])
    assert policy["authority_boundary"] == {
        "domain_owns_semantic_progress_signature": True,
        "domain_owns_non_advancing_escalation": True,
        "opl_owns_transport_lifecycle": True,
        "opl_can_write_domain_truth": False,
        "opl_can_claim_domain_readiness_from_transport": False,
        "opl_can_reset_synonymous_route_back_budget_from_transport": False,
    }
