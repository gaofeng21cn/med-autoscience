from __future__ import annotations

from med_autoscience.controllers.study_runtime_decision.publication_and_submission import (
    _AUTO_RECOVERY_CONTROLLER_STOP_SOURCES,
    _HUMAN_CONFIRMATION_REQUIRED_ACTION,
    _publication_supervisor_current_required_action,
    _publication_supervisor_requests_automated_continuation,
)
from med_autoscience.controllers.study_runtime_decision.runtime_events.human_gates import (
    _publication_supervisor_requires_human_confirmation,
)
from med_autoscience.controllers.study_runtime_decision.runtime_events.ownership_and_continuation import (
    _publication_gate_allows_post_clear_runtime_continuation,
)
from med_autoscience.controllers.study_runtime_types import (
    ProgressProjectionStatus,
    StudyRuntimeQuestStatus,
)


def _controller_stop_source(stop_reason: str | None) -> str | None:
    normalized = str(stop_reason or "").strip()
    if not normalized.startswith("controller_stop:"):
        return None
    source = normalized.split(":", 1)[1].strip()
    return source or None


def _controller_stop_is_auto_recoverable(
    *,
    stop_reason: str | None,
    publication_gate_report: dict[str, object] | None,
) -> bool:
    stop_source = _controller_stop_source(stop_reason)
    if stop_source not in _AUTO_RECOVERY_CONTROLLER_STOP_SOURCES:
        return False
    return _publication_supervisor_requests_automated_continuation(
        publication_gate_report,
        require_blocked_status=True,
    ) or _publication_gate_allows_post_clear_runtime_continuation(publication_gate_report)


def _publication_gate_requests_submission_hardening_continuation(
    publication_gate_report: dict[str, object] | None,
) -> bool:
    if not isinstance(publication_gate_report, dict):
        return False
    if str(publication_gate_report.get("status") or "").strip() in {"", "clear"}:
        return False
    if _publication_supervisor_requires_human_confirmation_from_payload(publication_gate_report):
        return False
    blockers = {
        str(item).strip()
        for item in (publication_gate_report.get("blockers") or [])
        if str(item).strip()
    }
    named_blockers = {
        str(item).strip()
        for item in (publication_gate_report.get("medical_publication_surface_named_blockers") or [])
        if str(item).strip()
    }
    return (
        "submission_hardening_incomplete" in blockers
        or "submission_hardening_incomplete" in named_blockers
    ) and str(publication_gate_report.get("medical_publication_surface_route_back_recommendation") or "").strip() == "return_to_finalize"


def _publication_supervisor_requires_human_confirmation_from_payload(payload: dict[str, object]) -> bool:
    return _publication_supervisor_current_required_action(payload) == _HUMAN_CONFIRMATION_REQUIRED_ACTION


def _stopped_controller_owned_auto_recovery_context(
    *,
    status: ProgressProjectionStatus,
    publication_gate_report: dict[str, object] | None,
) -> dict[str, str | None] | None:
    if status.quest_status is not StudyRuntimeQuestStatus.STOPPED:
        return None
    publication_gate_status = str((publication_gate_report or {}).get("status") or "").strip() or None
    if publication_gate_status is None or _publication_supervisor_requires_human_confirmation(status):
        return None
    try:
        continuation = status.continuation_state
    except KeyError:
        return None
    continuation_policy = continuation.continuation_policy
    continuation_anchor = continuation.continuation_anchor
    continuation_reason = continuation.continuation_reason
    stop_reason = continuation.stop_reason
    if continuation_policy not in {"auto", "wait_for_user_or_resume"}:
        return None
    has_pending_user_message = continuation.pending_user_message_count > 0
    recovery_mode: str | None = None
    controller_stopped_for_submission_hardening = (
        stop_reason is not None
        and stop_reason.startswith("controller_stop:")
        and has_pending_user_message
        and continuation_anchor == "decision"
        and continuation_reason is not None
        and continuation_reason.startswith("decision:")
        and _publication_gate_requests_submission_hardening_continuation(publication_gate_report)
    )
    if controller_stopped_for_submission_hardening:
        recovery_mode = "managed_auto_continuation"
    if stop_reason == "user_stop":
        if (
            continuation_reason is not None
            and continuation_reason.startswith("decision:")
            and has_pending_user_message
        ):
            recovery_mode = "managed_auto_continuation"
        else:
            return None
    elif recovery_mode is not None:
        pass
    elif stop_reason and not stop_reason.startswith("controller_stop:"):
        return None
    elif continuation_anchor == "decision" and continuation_reason is not None and continuation_reason.startswith("decision:"):
        recovery_mode = "decision"
    if recovery_mode is None and _controller_stop_is_auto_recoverable(
        stop_reason=stop_reason,
        publication_gate_report=publication_gate_report,
    ):
        recovery_mode = "controller_guard"
    if recovery_mode is None:
        return None
    return {
        "active_interaction_id": None,
        "stop_reason": stop_reason,
        "continuation_reason": continuation_reason,
        "recovery_mode": recovery_mode,
    }


def _stopped_invalid_blocking_auto_resume_allowed(
    *, stopped_recovery_context: dict[str, str | None] | None
) -> bool:
    if not isinstance(stopped_recovery_context, dict):
        return False
    stop_reason = str(stopped_recovery_context.get("stop_reason") or "").strip() or None
    return stop_reason is None
