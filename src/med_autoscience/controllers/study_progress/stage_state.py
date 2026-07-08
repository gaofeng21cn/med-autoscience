from __future__ import annotations


def progress_freshness_required(current_stage: str) -> bool:
    return current_stage not in {
        "study_completed",
        "manual_finishing",
        "waiting_physician_decision",
        "waiting_user_decision",
        "auto_runtime_parked",
    }


def current_stage_from_runtime_attempt_state(attempt_state: str | None) -> str | None:
    if attempt_state == "degraded":
        return "managed_runtime_degraded"
    if attempt_state == "escalated":
        return "managed_runtime_escalated"
    return None

