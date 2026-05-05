from __future__ import annotations

from collections.abc import Mapping
from typing import Any


ABNORMAL_STOPPED_RUNTIME_REASONS = {
    "quest_stopped_by_controller_guard",
}

RESUME_REQUIRED_DECISIONS = {
    "resume",
    "continue",
    "relaunch",
}

REPAIR_REASON = "abnormal_stopped_runtime_resume_required"


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _active_run_id(status: Mapping[str, Any], progress: Mapping[str, Any]) -> str | None:
    supervision = _mapping(progress.get("supervision"))
    runtime_liveness = _mapping(status.get("runtime_liveness_audit"))
    runtime_audit = _mapping(runtime_liveness.get("runtime_audit"))
    for value in (
        supervision.get("active_run_id"),
        status.get("active_run_id"),
        runtime_liveness.get("active_run_id"),
        runtime_audit.get("active_run_id"),
    ):
        if text := _text(value):
            return text
    return None


def _worker_running(status: Mapping[str, Any]) -> bool:
    runtime_liveness = _mapping(status.get("runtime_liveness_audit"))
    runtime_audit = _mapping(runtime_liveness.get("runtime_audit"))
    if runtime_audit.get("worker_running") is False:
        return False
    if runtime_liveness.get("worker_running") is False:
        return False
    return bool(runtime_audit.get("worker_running") or runtime_liveness.get("worker_running"))


def repair_required(status: Mapping[str, Any], progress: Mapping[str, Any]) -> bool:
    if _text(status.get("quest_status")) != "stopped":
        return False
    if _active_run_id(status, progress) or _worker_running(status):
        return False
    auto_runtime_parked = _mapping(progress.get("auto_runtime_parked"))
    if auto_runtime_parked.get("parked") is True:
        return False
    if auto_runtime_parked.get("auto_execution_complete") is True:
        return False
    decision = _text(status.get("decision")) or _text(status.get("runtime_decision"))
    reason = _text(status.get("reason")) or _text(status.get("runtime_reason"))
    current_stage = _text(progress.get("current_stage"))
    runtime_health = _mapping(status.get("runtime_health_snapshot"))
    attempt_state = _text(runtime_health.get("attempt_state"))
    canonical_runtime_action = _text(runtime_health.get("canonical_runtime_action"))
    return bool(
        decision in RESUME_REQUIRED_DECISIONS
        or reason in ABNORMAL_STOPPED_RUNTIME_REASONS
        or current_stage in {"managed_runtime_recovering", "managed_runtime_degraded", "managed_runtime_escalated"}
        or attempt_state in {"recovering", "retrying", "probing", "relaunching", "escalated"}
        or canonical_runtime_action in {"recover_runtime", "probe_runtime", "relaunch_runtime"}
    )

