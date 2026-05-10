from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any


PUBLIC_STATES = frozenset(
    {
        "progressing",
        "awaiting_controller_redrive",
        "blocked_controller_route",
        "awaiting_callable_owner",
        "awaiting_human",
        "downstream_only",
        "terminal_delivered",
    }
)

PAPER_PROGRESS_STATE_SURFACE = "paper_progress_state"
PAPER_PROGRESS_STATE_READ_MODEL = "paper_progress_state_read_model"

_RUNTIME_RETRY_EXHAUSTED = "runtime_recovery_retry_budget_exhausted"
_DOWNSTREAM_ONLY = "publication_supervisor_state.bundle_tasks_downstream_only"


def build_paper_progress_state(payload: Mapping[str, Any]) -> dict[str, Any]:
    details = _mapping(_mapping(payload.get("study_macro_state")).get("details"))
    actual_write_active = _actual_write_active(payload)
    package_delivered = _package_delivered(payload, details)
    meaningful_artifact_delta = _meaningful_artifact_delta(payload)
    next_owner = _next_owner(payload, details)
    requires_user_input = _requires_user_input(payload)
    blocking_reasons = _blocking_reasons(payload)
    state = _paper_state(
        payload=payload,
        actual_write_active=actual_write_active,
        package_delivered=package_delivered,
        meaningful_artifact_delta=meaningful_artifact_delta,
        next_owner=next_owner,
        requires_user_input=requires_user_input,
        blocking_reasons=blocking_reasons,
    )
    why_not_progressing = _why_not_progressing(
        state=state,
        payload=payload,
        actual_write_active=actual_write_active,
        package_delivered=package_delivered,
        meaningful_artifact_delta=meaningful_artifact_delta,
        next_owner=next_owner,
        blocking_reasons=blocking_reasons,
    )
    return {
        "surface": PAPER_PROGRESS_STATE_SURFACE,
        "read_model": PAPER_PROGRESS_STATE_READ_MODEL,
        "schema_version": 1,
        "study_id": _text(payload.get("study_id")),
        "quest_id": _text(payload.get("quest_id")),
        "state": state,
        "actual_write_active": actual_write_active,
        "package_delivered": package_delivered,
        "meaningful_artifact_delta": meaningful_artifact_delta,
        "next_owner": next_owner,
        "requires_user_input": requires_user_input,
        "why_not_progressing": why_not_progressing,
        "safe_reconcile_command": _safe_reconcile_command(payload),
    }


def _paper_state(
    *,
    payload: Mapping[str, Any],
    actual_write_active: bool,
    package_delivered: bool,
    meaningful_artifact_delta: bool,
    next_owner: str | None,
    requires_user_input: bool,
    blocking_reasons: list[str],
) -> str:
    if package_delivered:
        return "terminal_delivered"
    if requires_user_input:
        return "awaiting_human"
    if _is_downstream_only(payload, blocking_reasons):
        return "downstream_only"
    if _RUNTIME_RETRY_EXHAUSTED in blocking_reasons and next_owner == "MAS/controller":
        return "awaiting_controller_redrive"
    if _owner_callable_surface_missing(payload, next_owner):
        return "awaiting_callable_owner"
    if _controller_route_blocked(payload, blocking_reasons):
        return "blocked_controller_route"
    if actual_write_active and meaningful_artifact_delta:
        return "progressing"
    if next_owner:
        return "awaiting_callable_owner"
    return "blocked_controller_route"


def _actual_write_active(payload: Mapping[str, Any]) -> bool:
    macro_state = _mapping(payload.get("study_macro_state"))
    writer_state = _text(macro_state.get("writer_state"))
    if writer_state != "live":
        return False
    if not _fresh_artifact_delta_present(payload):
        return False
    return bool(
        _text(_mapping(macro_state.get("details")).get("active_run_id"))
        or _text(payload.get("active_run_id"))
        or _text(_mapping(payload.get("supervision")).get("active_run_id"))
    )


def _package_delivered(payload: Mapping[str, Any], details: Mapping[str, Any]) -> bool:
    if details.get("package_delivered") is True:
        return True
    delivery = _mapping(payload.get("delivery_inspection"))
    if delivery.get("package_delivered") is True:
        return True
    submission_hygiene = _mapping(payload.get("submission_hygiene_truth"))
    if submission_hygiene.get("package_delivered") is True:
        return True
    package_state = _text(submission_hygiene.get("package_state"))
    return package_state in {"delivered", "current_package_delivered", "terminal_delivered"}


def _meaningful_artifact_delta(payload: Mapping[str, Any]) -> bool:
    if _fresh_artifact_delta_present(payload):
        return True
    for key in ("paper_progress_stall", "portable_supervisor_dashboard", "runtime_health_snapshot"):
        value = _mapping(payload.get(key))
        if value.get("meaningful_artifact_delta") is True:
            return True
        artifact_delta = _mapping(value.get("artifact_delta"))
        if _text(artifact_delta.get("status")) == "fresh":
            return True
    return False


def _fresh_artifact_delta_present(payload: Mapping[str, Any]) -> bool:
    progress_freshness = _mapping(payload.get("progress_freshness"))
    artifact_delta = _mapping(progress_freshness.get("meaningful_artifact_delta_freshness"))
    return _text(artifact_delta.get("status")) == "fresh" and _text(artifact_delta.get("latest_progress_at")) is not None


def _next_owner(payload: Mapping[str, Any], details: Mapping[str, Any]) -> str | None:
    interaction = _mapping(payload.get("interaction_arbitration"))
    owner_route = _mapping(payload.get("owner_route"))
    production_impact = _mapping(payload.get("production_blocker_impact"))
    paper_progress_stall = _mapping(payload.get("paper_progress_stall"))
    portable_supervisor = _mapping(payload.get("portable_supervisor_dashboard"))
    ai_repair_lifecycle = _mapping(payload.get("ai_repair_lifecycle"))
    control_plane = _mapping(payload.get("control_plane_snapshot"))
    return (
        _text(interaction.get("next_owner"))
        or _text(owner_route.get("next_owner"))
        or _text(production_impact.get("next_owner"))
        or _text(details.get("decision_owner"))
        or _text(paper_progress_stall.get("next_owner"))
        or _text(portable_supervisor.get("next_owner"))
        or _text(ai_repair_lifecycle.get("next_owner"))
        or _text(control_plane.get("next_owner"))
    )


def _requires_user_input(payload: Mapping[str, Any]) -> bool:
    interaction = _mapping(payload.get("interaction_arbitration"))
    if isinstance(interaction.get("requires_user_input"), bool):
        return bool(interaction.get("requires_user_input"))
    if payload.get("needs_user_decision") is True or payload.get("needs_physician_decision") is True:
        return True
    macro_state = _mapping(payload.get("study_macro_state"))
    return _text(macro_state.get("user_next")) in {"submit_info", "revise"}


def _why_not_progressing(
    *,
    state: str,
    payload: Mapping[str, Any],
    actual_write_active: bool,
    package_delivered: bool,
    meaningful_artifact_delta: bool,
    next_owner: str | None,
    blocking_reasons: list[str],
) -> str | None:
    if state == "progressing" and actual_write_active and meaningful_artifact_delta:
        return None
    if package_delivered:
        return "package_delivered"
    if state == "downstream_only":
        return _DOWNSTREAM_ONLY
    if state == "awaiting_controller_redrive":
        return _RUNTIME_RETRY_EXHAUSTED
    interaction = _mapping(payload.get("interaction_arbitration"))
    for value in (
        interaction.get("blocked_reason"),
        _mapping(payload.get("production_blocker_impact")).get("why_not_running"),
        _mapping(payload.get("paper_progress_stall")).get("why_not_running"),
        _mapping(payload.get("paper_progress_stall")).get("summary"),
        _mapping(_mapping(payload.get("progress_freshness")).get("activity_timeout")).get("summary"),
        _mapping(_mapping(payload.get("progress_freshness")).get("meaningful_artifact_delta_freshness")).get("summary"),
    ):
        text = _text(value)
        if text:
            return text
    if blocking_reasons:
        return blocking_reasons[0]
    if next_owner:
        return f"awaiting {next_owner}"
    if not meaningful_artifact_delta:
        return "meaningful_artifact_delta_missing"
    if not actual_write_active:
        return "actual_write_inactive"
    return "blocked_controller_route"


def _safe_reconcile_command(payload: Mapping[str, Any]) -> str | None:
    trigger = _mapping(payload.get("runtime_reconcile_trigger"))
    if trigger.get("safe_to_request") is False:
        return None
    return _text(trigger.get("recommended_command")) or _text(
        trigger.get("canonical_one_shot_supervisor_reconcile_command")
    )


def _controller_route_blocked(payload: Mapping[str, Any], blocking_reasons: list[str]) -> bool:
    control_plane = _mapping(payload.get("control_plane_snapshot"))
    dispatch_gate = _mapping(control_plane.get("dispatch_gate"))
    if _text(dispatch_gate.get("state")) == "blocked":
        return True
    if _text(control_plane.get("control_state")) in {"blocked_controller_decision", "blocked_ledger", "needs_reconcile"}:
        return True
    return any(reason.startswith("controller_") or reason.startswith("ledger.") for reason in blocking_reasons)


def _is_downstream_only(payload: Mapping[str, Any], blocking_reasons: list[str]) -> bool:
    supervisor = _mapping(payload.get("publication_supervisor_state"))
    return supervisor.get("bundle_tasks_downstream_only") is True or _DOWNSTREAM_ONLY in blocking_reasons


def _owner_callable_surface_missing(payload: Mapping[str, Any], next_owner: str | None) -> bool:
    interaction = _mapping(payload.get("interaction_arbitration"))
    if _text(interaction.get("blocked_reason")) == "owner_callable_surface_missing":
        return True
    if next_owner and next_owner not in _registered_callable_owners():
        return True
    return "owner_callable_surface_missing" in _blocking_reasons(payload)


def _registered_callable_owners() -> set[str]:
    try:
        from med_autoscience.runtime_control.owner_callable_registry import callable_owner_names
    except ImportError:
        return set()
    return set(callable_owner_names())


def _blocking_reasons(payload: Mapping[str, Any]) -> list[str]:
    control_plane = _mapping(payload.get("control_plane_snapshot"))
    dispatch_gate = _mapping(control_plane.get("dispatch_gate"))
    health = _mapping(payload.get("runtime_health_snapshot"))
    truth = _mapping(payload.get("study_truth_snapshot"))
    return _dedupe(
        [
            *_string_items(payload.get("current_blockers")),
            *_string_items(control_plane.get("blocking_reasons")),
            *_string_items(dispatch_gate.get("blocking_reasons")),
            *_string_items(health.get("blocking_reasons")),
            *_string_items(truth.get("blocking_reasons")),
        ]
    )


def _dedupe(items: Iterable[str]) -> list[str]:
    return list(dict.fromkeys(item for item in items if item))


def _string_items(value: object) -> list[str]:
    if isinstance(value, Mapping) or isinstance(value, str | bytes):
        text = _text(value)
        return [text] if text is not None else []
    if not isinstance(value, Iterable):
        return []
    return [text for item in value if (text := _text(item)) is not None]


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "PAPER_PROGRESS_STATE_READ_MODEL",
    "PAPER_PROGRESS_STATE_SURFACE",
    "PUBLIC_STATES",
    "build_paper_progress_state",
]
