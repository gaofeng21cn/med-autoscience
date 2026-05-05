from __future__ import annotations

from collections.abc import Mapping
from typing import Any


PARKED_REASONS = {
    "publishability_stop_loss_recommended",
    "quest_parked_on_unchanged_finalize_state",
    "quest_waiting_for_explicit_wakeup_after_manual_hold",
    "quest_waiting_for_submission_metadata",
}


def current_truth(status: Mapping[str, Any], progress: Mapping[str, Any]) -> bool:
    if _has_live_worker(status, progress):
        return False
    auto_parked = _mapping(status.get("auto_runtime_parked")) or _mapping(progress.get("auto_runtime_parked"))
    if auto_parked.get("parked") is True:
        return True
    runtime_health = _mapping(status.get("runtime_health_snapshot")) or _mapping(progress.get("runtime_health_snapshot"))
    if _text(runtime_health.get("canonical_runtime_action")) == "await_explicit_resume":
        return True
    return _text(status.get("reason")) in PARKED_REASONS


def block_state(status: Mapping[str, Any], progress: Mapping[str, Any]) -> dict[str, Any] | None:
    if not current_truth(status, progress):
        return None
    return {
        "blocked_reason": None,
        "next_owner": None,
        "external_supervisor_required": False,
    }


def _has_live_worker(status: Mapping[str, Any], progress: Mapping[str, Any]) -> bool:
    if _text(status.get("active_run_id")) or _text(progress.get("active_run_id")):
        return True
    supervision = _mapping(progress.get("supervision"))
    if _text(supervision.get("active_run_id")):
        return True
    liveness = _mapping(status.get("runtime_liveness_audit"))
    runtime_audit = _mapping(liveness.get("runtime_audit"))
    if _text(liveness.get("active_run_id")) or _text(runtime_audit.get("active_run_id")):
        return True
    return runtime_audit.get("worker_running") is True


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = ["block_state", "current_truth"]
