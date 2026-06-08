from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.controllers.owner_route_reconcile_parts import ai_reviewer_actions


def resolve_why_not_applied(
    *,
    default_why_not_applied: str | None,
    actions: list[dict[str, Any]],
    lifecycle: Mapping[str, Any],
    submission_milestone_parked: bool,
) -> str | None:
    if actions:
        top_action_reason = _text(actions[0].get("reason")) or _text(actions[0].get("action_type"))
        if top_action_reason in {
            "publication_gate_specificity_required",
            "publication_gate_recheck_required",
            "paper_authority_clean_migration_required",
            "current_package_freshness_required",
            "display_surface_materialization_failed",
            "ai_reviewer_assessment_required",
            "ai_reviewer_assessment_stale_after_reviewer_revision",
            ai_reviewer_actions.RECORD_STALE_AFTER_CURRENT_MANUSCRIPT_REASON,
            ai_reviewer_actions.RECORD_STALE_AFTER_CURRENT_INPUTS_REASON,
            ai_reviewer_actions.RECORD_STALE_AFTER_UNIT_HARMONIZED_RERUN_REASON,
            ai_reviewer_actions.ANALYSIS_HARMONIZATION_COMPLETED_REVIEW_REASON,
            "repair_progress_ai_reviewer_recheck_required",
            "repair_progress_gate_replay_required",
        }:
            return top_action_reason
    if submission_milestone_parked:
        return None
    if default_why_not_applied is None and lifecycle:
        return _text(lifecycle.get("blocked_reason"))
    return default_why_not_applied


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None
