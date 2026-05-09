from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.controllers.runtime_supervisor_scan_parts import abnormal_stopped_runtime
from med_autoscience.controllers.runtime_supervisor_scan_parts import current_truth_owner


PARKED_REASONS = {
    "publishability_stop_loss_recommended",
    "quest_parked_on_unchanged_finalize_state",
    "quest_waiting_for_explicit_wakeup_after_manual_hold",
    "quest_waiting_for_submission_metadata",
}


def current_truth(status: Mapping[str, Any], progress: Mapping[str, Any]) -> bool:
    if _has_live_worker(status, progress):
        return False
    if abnormal_stopped_runtime.repair_kind(status, progress) == "failed_non_resumable_relaunch":
        return False
    if _current_controller_route_available(status, progress):
        return False
    macro_state = _mapping(status.get("study_macro_state")) or _mapping(progress.get("study_macro_state"))
    if _text(macro_state.get("writer_state")) == "parked" and _text(macro_state.get("reason")) in {
        "external_info",
        "stop_loss",
        "user_stop",
    }:
        return True
    auto_parked = _mapping(status.get("auto_runtime_parked")) or _mapping(progress.get("auto_runtime_parked"))
    if auto_parked.get("parked") is True:
        if _owner_route_pending(auto_parked):
            return False
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


def _owner_route_pending(auto_parked: Mapping[str, Any]) -> bool:
    if auto_parked.get("awaiting_explicit_wakeup") is True:
        return False
    return _text(auto_parked.get("parked_state")) == "ai_reviewer_pending" or _text(auto_parked.get("parked_owner")) == "ai_reviewer"


def _current_controller_route_available(status: Mapping[str, Any], progress: Mapping[str, Any]) -> bool:
    study_root = _text(status.get("study_root")) or _text(progress.get("study_root"))
    if study_root is None:
        return False
    publication_eval = _mapping(status.get("publication_eval")) or _mapping(progress.get("publication_eval"))
    if not publication_eval:
        return False
    return (
        current_truth_owner.current_controller_runtime_route(
            study_root=Path(study_root),
            publication_eval_payload=publication_eval,
        )
        is not None
    )


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = ["block_state", "current_truth"]
