from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def resolve_why_not_applied(
    *,
    default_why_not_applied: str | None,
    actions: list[dict[str, Any]],
    lifecycle: Mapping[str, Any],
    runtime_platform_repair_apply: Mapping[str, Any] | None,
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
        }:
            return top_action_reason
    if runtime_platform_repair_apply is not None and _text(runtime_platform_repair_apply.get("dispatch_status")) == "applied":
        if actions:
            return _text(actions[0].get("reason")) or _text(actions[0].get("action_type"))
        return None
    if runtime_platform_repair_apply is not None:
        apply_reason = _text(runtime_platform_repair_apply.get("reason"))
        if apply_reason in {"publication_gate_specificity_required", "current_package_freshness_required"}:
            return apply_reason
    if submission_milestone_parked:
        return None
    if default_why_not_applied is None and lifecycle:
        return _text(lifecycle.get("blocked_reason"))
    return default_why_not_applied


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None
