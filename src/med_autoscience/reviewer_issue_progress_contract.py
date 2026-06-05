from __future__ import annotations

from typing import Any


SURFACE_KIND = "mas_reviewer_issue_progress_contract"
VERSION = "mas-reviewer-issue-progress-contract.v1"
OWNER = "MedAutoScience"
ARK_SOURCE_COMMIT = "01cab1048cc78fa4d33e8274e4f963a44d70dc48"

REQUIRED_ISSUE_LEDGER_FIELDS: tuple[str, ...] = (
    "issue_id",
    "title",
    "severity",
    "issue_kind",
    "reviewer_record_ref",
    "canonical_artifact_digest",
    "refined_work_unit_ref",
    "status",
    "repeat_count",
    "attempted_fix_refs",
    "resolution_evidence_refs",
    "currentness",
)


def build_reviewer_issue_progress_contract() -> dict[str, Any]:
    return {
        "surface_kind": SURFACE_KIND,
        "version": VERSION,
        "owner": OWNER,
        "contract_ref": "med_autoscience.reviewer_issue_progress_contract.build_reviewer_issue_progress_contract",
        "clean_room_absorption": {
            "source_project": "kaust-ark/ARK",
            "source_commit": ARK_SOURCE_COMMIT,
            "absorbed_as": "mas_native_contract_pattern",
            "runtime_dependency": False,
            "vendor_dependency": False,
            "foreign_authority": False,
        },
        "authority_boundary": {
            "surface_role": "reviewer_issue_ledger_and_progress_router_input",
            "truth_owner": OWNER,
            "publication_readiness_authority": False,
            "quality_verdict_authority": False,
            "artifact_mutation_authority": False,
            "source_readiness_authority": False,
            "memory_accept_reject_authority": False,
            "score_threshold_authority": False,
            "stagnation_authority": "advisory_route_signal_only",
            "opl_role": "descriptor_ref_freshness_locator_consumer",
            "opl_can_write_mas_truth": False,
        },
        "issue_ledger": {
            "role": "reviewer_issue_progress_and_repair_memory",
            "required_fields": list(REQUIRED_ISSUE_LEDGER_FIELDS),
            "allowed_statuses": [
                "open",
                "repair_work_unit_created",
                "route_back_requested",
                "resolved_with_evidence",
                "blocked_by_hard_gate",
                "superseded_by_current_reviewer_record",
            ],
            "repeat_key_basis": [
                "issue_id",
                "normalized_title",
                "reviewer_record_ref",
                "canonical_artifact_digest",
            ],
            "repair_validation_required_refs": [
                "attempted_fix_refs",
                "resolution_evidence_refs",
                "current_reviewer_record_ref",
            ],
            "may_authorize_publication_readiness": False,
            "may_authorize_quality_verdict": False,
        },
        "goal_anchor_currentness": {
            "required_fields": [
                "study_charter_ref",
                "goal_anchor_ref",
                "anchor_digest",
                "canonical_artifact_ref",
                "canonical_artifact_digest",
                "checked_at",
            ],
            "stale_if_digest_mismatch": True,
            "stale_behavior": "typed_anchor_refresh_work_unit_or_reviewer_route_back",
            "may_authorize_publication_readiness": False,
        },
        "progress_first_policy": {
            "repeat_issue_behavior": "typed_repair_work_unit_or_reviewer_route_back",
            "score_delta_behavior": "advisory_progress_signal_only",
            "stagnation_behavior": "route_bias_not_publication_verdict",
            "may_block_all_agent_progress": False,
            "hard_gate_blockers": [
                "source_readiness_gate",
                "publication_gate",
                "artifact_mutation_authority_gate",
                "human_or_expert_gate",
                "forbidden_write_guard",
            ],
        },
        "forbidden_authority": [
            "score_threshold_as_publication_acceptance",
            "stagnation_as_global_stop",
            "executor_self_review_as_quality_gate_closure",
            "foreign_runtime_state_as_mas_truth",
        ],
        "outputs": [
            "reviewer_issue_ref",
            "typed_repair_work_unit_ref",
            "reviewer_route_back_ref",
            "anchor_refresh_work_unit_ref",
            "hard_gate_blocker_ref",
            "owner_receipt_ref",
        ],
    }


__all__ = [
    "ARK_SOURCE_COMMIT",
    "OWNER",
    "REQUIRED_ISSUE_LEDGER_FIELDS",
    "SURFACE_KIND",
    "VERSION",
    "build_reviewer_issue_progress_contract",
]
