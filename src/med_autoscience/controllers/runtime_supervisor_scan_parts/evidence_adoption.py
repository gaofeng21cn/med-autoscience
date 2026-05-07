from __future__ import annotations

from collections.abc import Mapping
from typing import Any


ADOPTED_REASON = "controller_work_unit_evidence_adopted"
RECHECK_REASON = "publication_gate_recheck_required"


def adopted_controller_work_unit(status: Mapping[str, Any]) -> bool:
    if _text(status.get("reason")) != ADOPTED_REASON:
        return False
    next_route = _mapping(status.get("controller_work_unit_next_route"))
    if _text(next_route.get("owner")) != "publication_gate":
        return False
    if next_route.get("runtime_relaunch_required") is not False:
        return False
    return bool(status.get("controller_work_unit_evidence_adoption"))


def should_suppress_runtime_platform_repair(status: Mapping[str, Any]) -> bool:
    return adopted_controller_work_unit(status)


def platform_repair_required(*, status: Mapping[str, Any], submission_milestone_parked: bool, base_required: bool) -> bool:
    return (
        base_required
        and not submission_milestone_parked
        and not should_suppress_runtime_platform_repair(status)
    )


def resolved_lifecycle(status: Mapping[str, Any], lifecycle: Mapping[str, Any]) -> dict[str, Any]:
    if not adopted_controller_work_unit(status):
        return dict(lifecycle)
    if _text(lifecycle.get("blocked_reason")) in {
        "runtime_recovery_retry_budget_exhausted",
        "runtime_relaunch_no_live_run_started",
        "abnormal_stopped_runtime_resume_required",
        "runtime_controller_redrive_required",
    }:
        return {}
    return dict(lifecycle)


def why_not_applied(status: Mapping[str, Any]) -> str | None:
    if adopted_controller_work_unit(status):
        return RECHECK_REASON
    return None


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "ADOPTED_REASON",
    "RECHECK_REASON",
    "adopted_controller_work_unit",
    "platform_repair_required",
    "resolved_lifecycle",
    "should_suppress_runtime_platform_repair",
    "why_not_applied",
]
