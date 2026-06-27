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
    } <= set(signature["semantic_delta_fields"])
    assert {
        "queue_id",
        "stage_attempt_id",
        "active_run_id",
        "worker_readiness",
        "provider_liveness",
        "focused_test_result",
        "docs_or_contract_commit",
    } <= set(signature["transport_only_fields_do_not_change_signature"])
    assert signature["repeated_signature_without_semantic_delta_is_non_advancing"] is True

    budget = policy["budget_and_escalation_policy"]
    assert budget["second_same_signature_route_back_without_semantic_delta"] == (
        "escalate_to_mas_owned_codex_executor_stage"
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
    } <= set(budget["allowed_escalation_outcomes"])

    executor_stage = policy["mas_owned_codex_executor_stage"]
    assert executor_stage == {
        "stage_type": "paper_mission_semantic_progress_executor",
        "owner": "MedAutoScience",
        "executor": "Codex CLI",
        "entry_condition": (
            "same semantic_progress_signature repeats through route_back/domain_gate "
            "without a new semantic_delta_fields value"
        ),
        "required_output": (
            "one of semantic artifact delta, owner receipt, stable typed blocker, human gate, "
            "route-back evidence with successor work unit, or repair-lane proposal"
        ),
        "opl_role": "transport_refs_attempts_queue_and_stage_run_lifecycle_only",
    }

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
    } <= set(policy["completion_and_readiness_forbidden_claims"])
    assert policy["authority_boundary"] == {
        "mas_owns_semantic_progress_detection": True,
        "mas_owns_executor_stage_type": True,
        "opl_can_transport_route_back_refs": True,
        "opl_can_decide_semantic_progress": False,
        "opl_transport_or_worker_ready_counts_as_semantic_progress": False,
        "policy_can_write_authority_surfaces": False,
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
        "after_threshold_next_owner": "MedAutoScience.paper_mission_semantic_progress_executor",
        "opl_redrive_after_worker_ready_allowed": False,
        "queue_or_worker_readiness_can_reset_budget": False,
        "budget_exhausted_can_claim_completion": False,
    }
    assert {
        "domain_ready",
        "runtime_ready",
        "publication_ready",
        "submission_ready",
        "provider_running",
        "DM002_ready",
        "DM003_ready",
    } <= set(policy["forbidden_public_or_readiness_claims"])
    assert policy["authority_boundary"] == {
        "domain_owns_semantic_progress_signature": True,
        "domain_owns_non_advancing_escalation": True,
        "opl_owns_transport_lifecycle": True,
        "opl_can_write_domain_truth": False,
        "opl_can_claim_domain_readiness_from_transport": False,
    }
