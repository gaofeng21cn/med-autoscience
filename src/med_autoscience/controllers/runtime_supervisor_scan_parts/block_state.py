from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.controllers.runtime_supervisor_scan_parts import completion_evidence
from med_autoscience.controllers.runtime_supervisor_scan_parts import current_truth_owner
from med_autoscience.controllers.runtime_supervisor_scan_parts import parked_truth


def projection_block_state(
    *,
    status: Mapping[str, Any],
    progress: Mapping[str, Any],
    lifecycle: Mapping[str, Any],
    actions: list[dict[str, Any]],
    why_not_applied: str | None,
) -> dict[str, Any]:
    if completion_evidence.completed_current_truth(status, progress):
        return _clear_block_state()
    parked_state = parked_truth.block_state(status, progress)
    if parked_state is not None:
        return parked_state
    completion_state = completion_evidence.block_state(status, progress)
    if completion_state is not None:
        return completion_state
    blocked_reason = _text(lifecycle.get("blocked_reason"))
    if why_not_applied is not None and any(_text(action.get("reason")) == why_not_applied for action in actions):
        blocked_reason = why_not_applied
    next_owner = next_owner_for_blocked_reason(blocked_reason) if blocked_reason else _text(lifecycle.get("next_owner"))
    external_supervisor_required = bool(
        lifecycle.get("external_supervisor_required")
        or any(_text(action.get("authority")) == "external_supervisor" for action in actions)
    )
    if next_owner is not None and next_owner != "external_supervisor":
        external_supervisor_required = any(
            _text(action.get("authority")) == "external_supervisor"
            and _text(action.get("reason")) == blocked_reason
            for action in actions
        )
    return {
        "blocked_reason": blocked_reason,
        "next_owner": next_owner,
        "external_supervisor_required": external_supervisor_required,
    }


def next_owner_for_blocked_reason(blocked_reason: str | None) -> str:
    if owner := current_truth_owner.next_owner_for_reason(blocked_reason):
        return owner
    if blocked_reason == "study_completion_contract_not_ready":
        return "completion_evidence"
    if blocked_reason == "publication_gate_specificity_required":
        return "publication_gate"
    if blocked_reason == "current_package_freshness_required":
        return "artifact_os"
    if blocked_reason == "display_surface_materialization_failed":
        return "artifact_os"
    if blocked_reason == "ai_reviewer_assessment_required":
        return "ai_reviewer"
    return "external_supervisor"


def _clear_block_state() -> dict[str, Any]:
    return {
        "blocked_reason": None,
        "next_owner": None,
        "external_supervisor_required": False,
    }


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = ["next_owner_for_blocked_reason", "projection_block_state"]
