from __future__ import annotations

from typing import Any


PROGRESS_DELTA_POLICY: dict[str, Any] = {
    "surface_kind": "opl_stage_progress_delta_policy",
    "version": "progress-delta-policy.v1",
    "owner": "one-person-lab",
    "standard_agent_requirement": (
        "stage_closeout_must_classify_deliverable_progress_vs_platform_repair_or_return_typed_blocker"
    ),
    "projection_surface": "stage_progress_log.user_stage_log",
    "required_fields": [
        "progress_delta_classification",
        "deliverable_progress_delta",
        "platform_repair_delta",
        "next_forced_delta",
    ],
    "classification_values": [
        "deliverable_progress",
        "platform_repair",
        "mixed",
        "typed_blocker",
        "human_gate",
        "stop_loss",
    ],
    "deliverable_delta_aliases": {
        "paper_progress_delta": "deliverable_progress_delta",
        "paper_work_progress": "deliverable_progress_delta",
    },
    "platform_delta_aliases": {
        "platform_repair_delta": "platform_repair_delta",
    },
    "platform_only_is_not_deliverable_progress": True,
    "missing_delta_policy": "emit_zero_deliverable_delta_and_next_forced_delta_without_inventing_paper_work",
    "authority_boundary": {
        "opl_can_infer_domain_work": False,
        "opl_can_read_artifact_body": False,
        "opl_can_write_domain_truth": False,
        "opl_can_authorize_quality_or_export": False,
        "mas_retains_publication_quality_authority": True,
    },
}

TYPED_BLOCKER_LINEAGE_POLICY: dict[str, Any] = {
    "surface_kind": "family-stall-lineage.v1",
    "version": "family-stall-lineage.v1",
    "owner": "one-person-lab",
    "standard_agent_requirement": (
        "typed_blockers_must_include_repeat_budget_lineage_next_forced_delta_and_escalation_owner"
    ),
    "required_fields": [
        "blocker_family",
        "study_id_or_domain_identity",
        "work_unit_id",
        "eval_id_or_review_ref",
        "source_fingerprint",
        "repeat_count",
        "first_seen",
        "last_seen",
        "last_deliverable_delta",
        "next_forced_delta",
        "escalation_owner",
        "terminal",
    ],
    "repeat_budget": {
        "mechanism_repair_after_repeat_count": 2,
        "human_gate_or_stop_loss_after_repeat_count": 3,
    },
    "platform_only_delta_policy": "does_not_reset_deliverable_stall_budget",
    "authority_boundary": {
        "opl_can_generate_domain_blocker": False,
        "opl_can_escalate_without_domain_or_human_gate_ref": False,
        "opl_can_claim_deliverable_progress_from_platform_repair": False,
        "mas_retains_typed_blocker_authority": True,
    },
}
