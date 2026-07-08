from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .shared import _mapping_copy, _non_empty_text, _read_json_object

_CLOSEOUT_ROOT = Path("artifacts/supervision/consumer/stage_attempt_closeouts")
_INVALIDATING_BLOCKED_REASONS = frozenset(
    {
        "no_selected_dispatch_for_requested_action_types",
    }
)


def status_with_invalidated_closed_runtime_attempt(
    *,
    status: dict[str, Any],
    study_root: Path,
) -> dict[str, Any]:
    active_run_id = _active_run_id(status)
    if active_run_id is None:
        return status
    attempt_id = _stage_attempt_id(active_run_id)
    if attempt_id is None:
        return status
    closeout = _read_json_object(Path(study_root).expanduser().resolve() / _CLOSEOUT_ROOT / f"{attempt_id}.json")
    if not _closeout_invalidates_live_attempt(closeout, attempt_id=attempt_id):
        return status
    invalidated = dict(status)
    _clear_runtime_liveness(invalidated)
    invalidated["runtime_liveness_status"] = "none"
    invalidated["active_run_id"] = None
    invalidated["worker_running"] = False
    invalidated["reason"] = (
        _non_empty_text(invalidated.get("reason"))
        or _non_empty_text(closeout.get("blocked_reason"))
        or "provider_attempt_closed_without_dispatch"
    )
    invalidated["runtime_closeout_invalidation"] = {
        "surface_kind": "study_progress_runtime_closeout_invalidation",
        "stage_attempt_id": attempt_id,
        "closeout_status": _non_empty_text(closeout.get("status")),
        "blocked_reason": _non_empty_text(closeout.get("blocked_reason")),
        "source_path": str(
            Path(study_root).expanduser().resolve() / _CLOSEOUT_ROOT / f"{attempt_id}.json"
        ),
    }
    return invalidated


def _active_run_id(status: Mapping[str, Any]) -> str | None:
    liveness = _mapping_copy(status.get("runtime_liveness_audit"))
    runtime_audit = _mapping_copy(liveness.get("runtime_audit"))
    execution_owner_guard = _mapping_copy(status.get("execution_owner_guard"))
    autonomous_runtime_notice = _mapping_copy(status.get("autonomous_runtime_notice"))
    continuation_state = _mapping_copy(status.get("continuation_state"))
    return (
        _non_empty_text(status.get("active_run_id"))
        or _non_empty_text(liveness.get("active_run_id"))
        or _non_empty_text(runtime_audit.get("active_run_id"))
        or _non_empty_text(execution_owner_guard.get("active_run_id"))
        or _non_empty_text(autonomous_runtime_notice.get("active_run_id"))
        or _non_empty_text(continuation_state.get("active_run_id"))
    )


def _stage_attempt_id(active_run_id: str) -> str | None:
    prefix = "opl-stage-attempt://"
    if not active_run_id.startswith(prefix):
        return None
    attempt_id = active_run_id[len(prefix) :].strip()
    return attempt_id or None


def _closeout_invalidates_live_attempt(closeout: Mapping[str, Any] | None, *, attempt_id: str) -> bool:
    if not isinstance(closeout, Mapping):
        return False
    if _non_empty_text(closeout.get("stage_attempt_id")) != attempt_id:
        return False
    if _non_empty_text(closeout.get("status")) != "blocked":
        return False
    if _non_empty_text(closeout.get("blocked_reason")) not in _INVALIDATING_BLOCKED_REASONS:
        return False
    if _mapping_copy(closeout.get("paper_stage_log")):
        return False
    if _mapping_copy(closeout.get("user_stage_log")):
        return False
    if _mapping_copy(closeout.get("stage_log_summary")):
        return False
    return True


def _clear_runtime_liveness(status: dict[str, Any]) -> None:
    liveness = _mapping_copy(status.get("runtime_liveness_audit"))
    if liveness:
        runtime_audit = _mapping_copy(liveness.get("runtime_audit"))
        runtime_audit["status"] = "none"
        runtime_audit["active_run_id"] = None
        runtime_audit["worker_running"] = False
        liveness["status"] = "none"
        liveness["active_run_id"] = None
        liveness["worker_running"] = False
        liveness["running_provider_attempt"] = False
        liveness["runtime_audit"] = runtime_audit
        status["runtime_liveness_audit"] = liveness
    for key in ("execution_owner_guard", "autonomous_runtime_notice", "continuation_state"):
        payload = _mapping_copy(status.get(key))
        if payload:
            payload["active_run_id"] = None
            status[key] = payload
    runtime_health = _mapping_copy(status.get("runtime_health_snapshot"))
    if runtime_health:
        worker_liveness = _mapping_copy(runtime_health.get("worker_liveness_state"))
        if worker_liveness:
            worker_liveness["state"] = "not_live"
            worker_liveness["runtime_liveness_status"] = "none"
            worker_liveness["worker_running"] = False
            worker_liveness["active_run_id"] = None
            runtime_health["worker_liveness_state"] = worker_liveness
        runtime_health["active_run_id"] = None
        if _non_empty_text(runtime_health.get("attempt_state")) == "live":
            runtime_health["attempt_state"] = "idle"
        status["runtime_health_snapshot"] = runtime_health
