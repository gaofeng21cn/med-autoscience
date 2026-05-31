from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def minimum_forward_delta_contract(stage: Mapping[str, Any]) -> dict[str, Any]:
    stage_id = str(stage["stage_id"])
    domain_stage_refs = list(stage["domain_stage_refs"])
    return {
        "surface_kind": "mas_stage_minimum_forward_delta_contract",
        "schema_version": 1,
        "stage_id": stage_id,
        "domain_stage_refs": domain_stage_refs,
        "progress_first_priority": "produce_reviewable_deliverable_delta_before_control_plane_explanation",
        "valid_non_terminal_results": [
            "deliverable_progress_delta",
            "typed_blocker_with_next_forced_delta",
            "human_gate_with_last_attempted_delta",
            "stop_loss_candidate",
        ],
        "restricted_results": [
            "no_op_with_currentness_proof",
            "record_only_reviewer_loop",
            "provider_completed_without_typed_closeout",
            "platform_repair_counted_as_deliverable_progress",
        ],
        "no_op_budget_ref": "stage_contract.progress_delta_policy.no_op_currentness_budget",
        "target_surface": {
            "ref_kind": "route_obligation",
            "stage_id": stage_id,
            "domain_stage_refs": domain_stage_refs,
            "deliverable_delta_ref": "stage_contract.progress_delta_policy.deliverable_progress_delta",
            "next_forced_delta_ref": "study_progress.next_forced_delta",
        },
        "acceptance_refs": [
            "stage_contract.user_stage_log_contract",
            "stage_contract.progress_delta_policy",
            "stage_contract.typed_blocker_lineage_policy",
            "stage_contract.human_gate_progress_evidence",
        ],
        "owner_action": {
            "next_owner": "MedAutoScience",
            "allowed_action_refs": list(stage["allowed_action_refs"]),
            "owner_receipt_required": True,
        },
        "authority_boundary": {
            "can_write_domain_truth": False,
            "can_authorize_publication_quality": False,
            "can_authorize_submission_readiness": False,
            "mas_retains_stage_closeout_authority": True,
        },
    }


def route_obligation_lens(stage: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "surface_kind": "mas_stage_route_obligation_lens",
        "schema_version": 1,
        "stage_id": str(stage["stage_id"]),
        "domain_stage_refs": list(stage["domain_stage_refs"]),
        "active_route_obligation_policy": "project_current_blocking_route_obligation_before_generic_stage_status",
        "target_surface_ref": "stage_contract.minimum_forward_delta.target_surface",
        "route_obligation_progress_delta": {
            "deliverable_progress_delta_ref": "stage_contract.minimum_forward_delta",
            "next_forced_delta_ref": "study_progress.next_forced_delta",
            "typed_blocker_lineage_ref": "stage_contract.typed_blocker_lineage_policy",
        },
    }


def human_gate_progress_evidence_contract() -> dict[str, Any]:
    return {
        "surface_kind": "mas_stage_human_gate_progress_evidence_contract",
        "schema_version": 1,
        "required_fields": [
            "last_attempted_deliverable_delta",
            "why_ai_cannot_progress_one_more_delta",
            "next_forced_delta",
            "human_decision_owner",
        ],
        "missing_evidence_policy": "return_to_ai_executor_for_minimum_forward_delta_or_typed_blocker",
        "authority_boundary": {
            "can_authorize_publication_quality": False,
            "can_replace_ai_reviewer_gate": False,
            "mas_retains_human_gate_receipt_authority": True,
        },
    }


__all__ = [
    "human_gate_progress_evidence_contract",
    "minimum_forward_delta_contract",
    "route_obligation_lens",
]
