from __future__ import annotations

from typing import Any


_PROGRESS_FIRST_STATUS_KEYS = (
    "current_stage",
    "current_stage_summary",
    "current_stage_label",
    "status_summary",
    "paper_stage",
    "paper_stage_summary",
    "current_blockers",
    "latest_events",
    "next_system_action",
    "next_step",
    "needs_user_decision",
    "needs_physician_decision",
    "progress_freshness",
    "paper_progress_delta",
    "platform_repair_delta",
    "intervention_lane",
    "operator_verdict",
    "operator_status_card",
    "quality_closure_truth",
    "quality_execution_lane",
    "quality_review_loop",
    "supervision",
    "continuation_state",
    "study_macro_state",
    "ai_repair_lifecycle",
)

_LEGACY_DEFAULT_COMPLETION_KEYS = (
    "current_executable_owner_action",
    "current_work_unit",
    "paper_recovery_state",
    "progress_first_monitoring_summary",
    "provider_attempt_blocked_by_supervisor_decision",
    "provider_attempt_candidates",
    "provider_attempt_pending_count",
    "provider_attempt_running_proof_consumed",
    "provider_attempt_terminal_closeout_consumed",
    "transition_request_candidates",
    "transition_request_pending_count",
)

_USER_VISIBLE_STATUS_KEYS = (
    "state",
    "writer_state",
    "user_next",
    "reason",
    "conflict_reason",
    "package_delivered",
    "actual_write_active",
    "meaningful_artifact_delta",
    "next_owner",
    "why_not_progressing",
    "user_action_required",
    "state_label",
    "state_summary",
    "current_stage",
    "current_stage_label",
    "current_stage_summary",
    "status_summary",
    "paper_stage",
    "paper_stage_summary",
    "current_blockers",
    "next_system_action",
    "next_step",
    "needs_user_decision",
    "needs_physician_decision",
)


def progress_first_status_payload(
    payload: dict[str, Any],
    *,
    preserve_runtime_reason: bool = False,
) -> dict[str, Any]:
    progress_projection = payload.get("progress_projection")
    source_payload = progress_projection if isinstance(progress_projection, dict) else payload
    user_visible = source_payload.get("user_visible_projection")
    if not isinstance(progress_projection, dict) and not _is_current_user_visible_projection(user_visible):
        return _without_legacy_default_completion_surfaces(payload)
    updated = dict(payload)
    for key in _PROGRESS_FIRST_STATUS_KEYS:
        if key in source_payload:
            updated[key] = source_payload[key]
    if _is_current_user_visible_projection(user_visible):
        updated["user_visible_projection"] = dict(user_visible)
        for key in _USER_VISIBLE_STATUS_KEYS:
            if preserve_runtime_reason and key == "reason":
                continue
            if key in user_visible:
                updated[key] = user_visible[key]
    updated["progress_first_projection"] = {
        "surface_kind": "domain_progress_projection_progress_first_view",
        "source": (
            "progress_projection.user_visible_projection"
            if isinstance(progress_projection, dict)
            else "user_visible_projection"
        ),
        "runtime_decision_field": "decision",
        "runtime_reason_field": "reason",
    }
    return _without_legacy_default_completion_surfaces(updated)


def _without_legacy_default_completion_surfaces(payload: dict[str, Any]) -> dict[str, Any]:
    updated = dict(payload)
    retained_current_action = _retained_current_executable_owner_action(
        updated.get("current_executable_owner_action")
    )
    for key in _LEGACY_DEFAULT_COMPLETION_KEYS:
        updated.pop(key, None)
    if retained_current_action:
        updated["current_executable_owner_action"] = retained_current_action
    return updated


def _retained_current_executable_owner_action(value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    if str(value.get("surface_kind") or "").strip() != "current_executable_owner_action":
        return {}
    authority = str(value.get("authority") or "").strip()
    if authority in {
        "study_progress.canonical_owner_action_projection",
        "study_progress.current_executable_owner_action",
    }:
        return dict(value)
    if (
        str(value.get("source") or "").strip() == "paper_mission_typed_blocker_resolution"
        and str(value.get("required_delta_kind") or "").strip()
        == "typed_blocker_resolution_owner_action"
        and str(value.get("work_unit_id") or "").strip()
        and str(value.get("work_unit_fingerprint") or "").strip()
    ):
        return dict(value)
    return {}


def _is_current_user_visible_projection(value: object) -> bool:
    return (
        isinstance(value, dict)
        and value.get("schema_version") == 2
        and all(
            key in value
            for key in ("writer_state", "user_next", "reason", "state_label", "state_summary")
        )
    )


__all__ = ["progress_first_status_payload"]
