from __future__ import annotations

from pathlib import Path
from typing import Any

from med_autoscience.controllers.owner_route_reconcile_parts import domain_authority_handoff


PROJECTION_CONTRACT_ERROR_REASON = "study_projection_contract_error"


def projection_error_study(
    *,
    study_id: str,
    study_root: Path,
    developer_mode_payload: dict[str, Any],
    safe_actions_enabled: bool,
    generated_at: str,
    error: Exception,
    why_not_applied_timeline: list[dict[str, Any]],
) -> dict[str, Any]:
    reason = PROJECTION_CONTRACT_ERROR_REASON
    return {
        "study_id": study_id,
        "study_root": str(study_root),
        "quest_id": None,
        "quest_root": None,
        "quest_status": None,
        "current_stage": "projection_blocked",
        "active_run_id": None,
        "supervision_url": None,
        "paper_stage": None,
        "runtime_health": {},
        "meaningful_artifact_delta": False,
        "artifact_delta": {
            "status": "not_observed",
            "summary": "Study projection failed before artifact freshness could be evaluated.",
        },
        "gate_specificity": {
            "required": False,
            "status": "not_evaluated",
            "missing_target_kinds": [],
            "covered_target_kinds": [],
            "specificity_targets": [],
        },
        "ai_reviewer_assessment": {
            "present": False,
            "owner": "projection_error",
            "required": False,
            "missing": False,
        },
        "ai_reviewer_status": {
            "status": "not_evaluated",
            "owner": "projection_error",
            "trace_complete": False,
            "blocked_reason": reason,
        },
        "ai_repair_lifecycle": None,
        "action_queue": [],
        "submission_milestone_parked_refresh": None,
        "domain_authority_handoff": domain_authority_handoff.projection_error_handoff(
            study_id=study_id,
            study_root=study_root,
            generated_at=generated_at,
            reason=reason,
            error=error,
        ),
        "paper_progress_stall": {
            "schema_version": 1,
            "surface_kind": "paper_progress_stall",
            "stalled": True,
            "stall_reasons": [reason],
            "terminal": False,
            "safe_reconcile_candidate": False,
            "will_start_llm": False,
            "codex_dispatch_count": 0,
        },
        "owner_route": {},
        "repeat_suppression": {"repeat_suppressed": False, "why_not_applied": None},
        "why_not_applied": reason,
        "why_not_applied_timeline": why_not_applied_timeline,
        "escalation_reason": reason,
        "next_owner": "repo_controller_repair",
        "blocked_reason": reason,
        "external_supervisor_required": False,
        "supervisor_only": False,
        "paper_package_mutated": False,
        "apply_safe_actions": safe_actions_enabled,
        "developer_supervisor_mode": developer_mode_payload,
        "projection_error": {
            "error_type": type(error).__name__,
            "message": str(error),
            "handled_as": reason,
        },
        "refs": {},
    }


__all__ = ["PROJECTION_CONTRACT_ERROR_REASON", "projection_error_study"]
