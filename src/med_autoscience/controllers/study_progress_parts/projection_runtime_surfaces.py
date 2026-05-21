from __future__ import annotations

from typing import Any, Mapping

from med_autoscience.controllers import control_plane_facts

from .shared import _mapping_copy, _non_empty_text


def supervision_health_status(
    *,
    publication_gate_stationary: bool,
    auto_runtime_parked: Mapping[str, Any],
    runtime_facts: Any,
    runtime_health_status: str | None,
) -> str | None:
    if publication_gate_stationary:
        return "publication_gate_blocked"
    if bool(auto_runtime_parked.get("parked")):
        return "parked"
    if runtime_facts.recovery_pending or runtime_facts.missing_live_session:
        return "recovering"
    if runtime_facts.strict_live:
        return runtime_health_status or "live"
    return runtime_health_status


def status_absorbing_live_runtime_surfaces(
    *,
    status: dict[str, Any],
    study_id: str,
    runtime_supervision_payload: Mapping[str, Any] | None,
    launch_report_payload: Mapping[str, Any] | None,
) -> dict[str, Any]:
    quest_status = _non_empty_text(status.get("quest_status"))
    if quest_status not in {"active", "running"}:
        return status
    if _mapping_copy(status.get("domain_transition")):
        return status
    live = _live_runtime_supervision_facts(runtime_supervision_payload, study_id=study_id)
    if live is None:
        return status
    updated = dict(status)
    active_run_id = live["active_run_id"]
    updated["active_run_id"] = active_run_id
    updated["worker_running"] = True
    updated["runtime_liveness_status"] = "live"
    if live.get("quest_status") is not None:
        updated["quest_status"] = live["quest_status"]
    if live.get("runtime_reason") is not None:
        updated["reason"] = live["runtime_reason"]
        updated["runtime_reason"] = live["runtime_reason"]
    if live.get("runtime_health_snapshot"):
        updated["runtime_health_snapshot"] = live["runtime_health_snapshot"]
    updated["runtime_liveness_audit"] = {
        "status": "live",
        "active_run_id": active_run_id,
        "runtime_audit": {
            "status": "live",
            "worker_running": True,
            "active_run_id": active_run_id,
        },
    }
    launch = _mapping_copy(launch_report_payload)
    for key in ("autonomous_runtime_notice", "execution_owner_guard", "continuation_state"):
        value = _mapping_copy(launch.get(key))
        if not value:
            continue
        value_active_run_id = _non_empty_text(value.get("active_run_id"))
        if value_active_run_id is None or value_active_run_id == active_run_id:
            updated[key] = value
    return updated


def _live_runtime_supervision_facts(
    payload: Mapping[str, Any] | None,
    *,
    study_id: str,
) -> dict[str, Any] | None:
    supervision = _mapping_copy(payload)
    if not supervision:
        return None
    payload_study_id = _non_empty_text(supervision.get("study_id"))
    if payload_study_id is not None and payload_study_id != study_id:
        return None
    runtime_health = _mapping_copy(supervision.get("runtime_health_snapshot"))
    worker_liveness = _mapping_copy(runtime_health.get("worker_liveness_state"))
    facts = control_plane_facts.resolve_control_plane_facts(
        {
            "active_run_id": (
                _non_empty_text(supervision.get("active_run_id"))
                or _non_empty_text(runtime_health.get("active_run_id"))
                or _non_empty_text(worker_liveness.get("active_run_id"))
            ),
            "runtime_liveness_status": (
                _non_empty_text(supervision.get("runtime_liveness_status"))
                or _non_empty_text(worker_liveness.get("runtime_liveness_status"))
                or _non_empty_text(supervision.get("health_status"))
                or _non_empty_text(worker_liveness.get("state"))
            ),
            "worker_running": (
                supervision.get("worker_running")
                if isinstance(supervision.get("worker_running"), bool)
                else worker_liveness.get("worker_running")
            ),
            "quest_status": _non_empty_text(supervision.get("quest_status")),
            "reason": _non_empty_text(supervision.get("runtime_reason")),
        }
    )
    if not facts.strict_live or facts.active_run_id is None:
        return None
    return {
        "active_run_id": facts.active_run_id,
        "quest_status": facts.quest_status,
        "runtime_reason": facts.reason,
        "runtime_health_snapshot": runtime_health,
    }
