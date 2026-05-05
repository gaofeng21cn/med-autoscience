from __future__ import annotations

from typing import Any


STARTUP_FRESHNESS_CONTINUATION_REASONS = frozenset({"current_package_freshness_required"})


def continuation_reason(payload: dict[str, Any]) -> str | None:
    continuation_state = payload.get("continuation_state")
    if isinstance(continuation_state, dict):
        reason = str(continuation_state.get("continuation_reason") or "").strip()
        if reason:
            return reason
    reason = str(payload.get("continuation_reason") or "").strip()
    return reason or None


def gate_clearing_preempts_task_intake(
    *,
    status_payload: dict[str, Any],
    batch_action: dict[str, Any] | None,
) -> bool:
    if not isinstance(batch_action, dict):
        return False
    if str(batch_action.get("controller_action_type") or "").strip() != "run_gate_clearing_batch":
        return False
    return continuation_reason(status_payload) in STARTUP_FRESHNESS_CONTINUATION_REASONS


def startup_freshness_requires_gate_clearing(status_payload: dict[str, Any]) -> bool:
    return continuation_reason(status_payload) in STARTUP_FRESHNESS_CONTINUATION_REASONS
