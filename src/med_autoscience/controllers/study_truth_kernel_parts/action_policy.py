from __future__ import annotations

from collections.abc import Mapping
from typing import Any


BASE_ALLOWED_ACTIONS = (
    "read_opl_current_control_state",
    "open_monitoring_entry",
    "stop_runtime",
    "request_opl_handoff_hydration",
    "record_user_decision",
    "direct_study_execution",
    "direct_paper_line_write",
    "direct_bundle_build",
    "direct_compiled_bundle_proofing",
)

SUPERVISOR_ONLY_FORBIDDEN_ACTIONS = frozenset(
    {
        "direct_study_execution",
        "direct_paper_line_write",
        "direct_bundle_build",
        "direct_compiled_bundle_proofing",
    }
)

DOWNSTREAM_BUNDLE_FORBIDDEN_ACTIONS = frozenset(
    {
        "direct_bundle_build",
        "direct_compiled_bundle_proofing",
    }
)


def canonical_next_action(dominant_event: Mapping[str, Any] | None) -> str:
    if dominant_event is None:
        return "observe"
    event_type = dominant_event.get("event_type")
    payload = _mapping(dominant_event.get("payload"))
    if event_type == "stop_loss":
        return "stop_runtime"
    closure = _mapping(payload.get("quality_closure_truth"))
    if event_type == "task_intake" and _text(closure.get("state")) == "stop_loss_recommended":
        return "stop_runtime"
    if event_type in {"task_intake", "explicit_resume"}:
        return _text(payload.get("current_required_action")) or "resume_same_study_line"
    if event_type == "opl_runtime_owner_handoff":
        guard = _mapping(payload.get("execution_owner_guard"))
        if guard.get("supervisor_only") is True:
            return "request_opl_handoff_hydration"
    if event_type == "publication_gate_eval":
        provenance = _mapping(payload.get("assessment_provenance"))
        owner = _text(provenance.get("owner"))
        action = _text(payload.get("current_required_action"))
        if owner != "ai_reviewer" and action in {
            "reviewer_ready",
            "bundle_only_remaining",
            "finalize",
            "finalize_ready",
            "submission_ready",
        }:
            return "review_required"
    return _text(payload.get("current_required_action")) or "observe"


def blocking_reasons(events: list[dict[str, Any]]) -> list[str]:
    reasons: list[str] = []
    supervision = _last_payload(events, "opl_runtime_owner_handoff")
    guard = _mapping(supervision.get("execution_owner_guard"))
    supervisor = _mapping(supervision.get("publication_supervisor_state"))
    if guard.get("supervisor_only") is True:
        reasons.append("opl_current_control_state.handoff_required")
    if supervisor.get("bundle_tasks_downstream_only") is True:
        reasons.append("publication_supervisor_state.bundle_tasks_downstream_only")
    if _latest_event(events, "stop_loss") is not None:
        reasons.append("publishability_stop_loss_recommended")
    publication = _last_payload(events, "publication_gate_eval")
    provenance = _mapping(publication.get("assessment_provenance"))
    action = _text(publication.get("current_required_action"))
    if _text(provenance.get("owner")) != "ai_reviewer" and action in {
        "reviewer_ready",
        "bundle_only_remaining",
        "finalize",
        "finalize_ready",
        "submission_ready",
    }:
        reasons.append("publication_eval.ai_reviewer_required")
    return reasons


def allowed_controller_actions(events: list[dict[str, Any]]) -> list[str]:
    allowed = list(BASE_ALLOWED_ACTIONS)
    supervision = _last_payload(events, "opl_runtime_owner_handoff")
    guard = _mapping(supervision.get("execution_owner_guard"))
    supervisor = _mapping(supervision.get("publication_supervisor_state"))
    forbidden: set[str] = set()
    if guard.get("supervisor_only") is True:
        forbidden.update(SUPERVISOR_ONLY_FORBIDDEN_ACTIONS)
    if supervisor.get("bundle_tasks_downstream_only") is True:
        forbidden.update(DOWNSTREAM_BUNDLE_FORBIDDEN_ACTIONS)
    return [action for action in allowed if action not in forbidden]


def _latest_event(events: list[dict[str, Any]], event_type: str) -> dict[str, Any] | None:
    for event in reversed(events):
        if event.get("event_type") == event_type:
            return event
    return None


def _last_payload(events: list[dict[str, Any]], event_type: str) -> dict[str, Any]:
    event = _latest_event(events, event_type)
    return _mapping(event.get("payload")) if event is not None else {}


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "allowed_controller_actions",
    "blocking_reasons",
    "canonical_next_action",
]
