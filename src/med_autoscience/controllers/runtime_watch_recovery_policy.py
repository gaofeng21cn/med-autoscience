from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from med_autoscience.controllers.study_runtime_types import StudyRuntimeStatus


def _non_empty_text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    text = value.strip()
    return text or None


def _read_json_object(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else None


def _status_payload(value: dict[str, Any] | StudyRuntimeStatus) -> dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    return value.to_dict()


def _mapping_value(payload: dict[str, Any], key: str) -> dict[str, Any]:
    value = payload.get(key)
    return dict(value) if isinstance(value, dict) else {}


def _bool_value(value: object) -> bool | None:
    return value if isinstance(value, bool) else None


def _liveness_probe_payload(payload: dict[str, Any]) -> dict[str, Any]:
    runtime_liveness_audit = _mapping_value(payload, "runtime_liveness_audit")
    runtime_audit = _mapping_value(runtime_liveness_audit, "runtime_audit")
    return {
        "status": _non_empty_text(runtime_liveness_audit.get("status")) or _non_empty_text(runtime_audit.get("status")),
        "active_run_id": _non_empty_text(runtime_liveness_audit.get("active_run_id"))
        or _non_empty_text(runtime_audit.get("active_run_id")),
        "worker_running": _bool_value(runtime_audit.get("worker_running")),
        "worker_pending": _bool_value(runtime_audit.get("worker_pending")),
        "stop_requested": _bool_value(runtime_audit.get("stop_requested")),
    }


def _probe_has_live_worker(liveness: dict[str, Any]) -> bool:
    return (
        liveness.get("status") == "live"
        and liveness.get("worker_running") is True
        and _non_empty_text(liveness.get("active_run_id")) is not None
    )


def _probe_id(*, study_id: str | None, quest_id: str | None, episode_count: int) -> str:
    return (
        "recovery-probe::"
        f"{study_id or 'unknown-study'}::"
        f"{quest_id or 'unknown-quest'}::"
        f"flapping-circuit-breaker::{episode_count}"
    )


def _build_recovery_probe(
    *,
    payload: dict[str, Any],
    flapping_report: dict[str, Any],
    episode_count: int,
) -> dict[str, Any]:
    study_id = _non_empty_text(payload.get("study_id")) or _non_empty_text(flapping_report.get("study_id"))
    quest_id = _non_empty_text(payload.get("quest_id")) or _non_empty_text(flapping_report.get("quest_id"))
    liveness = _liveness_probe_payload(payload)
    has_live_worker = _probe_has_live_worker(liveness)
    escalated = _non_empty_text(flapping_report.get("health_status")) == "escalated" or bool(
        flapping_report.get("needs_human_intervention")
    )
    if has_live_worker:
        status = "clear_hold"
        recommended_action = "ready_to_resume"
        reason = "runtime_liveness_confirmed_live"
        next_probe_id = None
    elif escalated:
        status = "escalate"
        recommended_action = "escalate"
        reason = "flapping_circuit_breaker_escalated"
        next_probe_id = _probe_id(study_id=study_id, quest_id=quest_id, episode_count=episode_count + 1)
    else:
        status = "hold_active"
        recommended_action = "hold"
        reason = "flapping_circuit_breaker_active"
        next_probe_id = _probe_id(study_id=study_id, quest_id=quest_id, episode_count=episode_count + 1)
    return {
        "probe_id": _probe_id(study_id=study_id, quest_id=quest_id, episode_count=episode_count),
        "status": status,
        "recommended_action": recommended_action,
        "reason": reason,
        "next_probe_id": next_probe_id,
        "liveness": liveness,
        "current_status": {
            "quest_status": _non_empty_text(payload.get("quest_status")),
            "decision": _non_empty_text(payload.get("decision")),
            "reason": _non_empty_text(payload.get("reason")),
            "runtime_stability_status": "live" if has_live_worker else _non_empty_text(flapping_report.get("runtime_stability_status")),
            "flapping_circuit_breaker": False if has_live_worker else bool(flapping_report.get("flapping_circuit_breaker")),
            "flapping_episode_count": episode_count,
        },
    }


def _flapping_circuit_breaker_report(*, study_root: Path) -> dict[str, Any] | None:
    latest_path = (
        Path(study_root).expanduser().resolve()
        / "artifacts"
        / "runtime"
        / "runtime_supervision"
        / "latest.json"
    )
    latest = _read_json_object(latest_path)
    if not latest:
        return None
    if latest.get("flapping_circuit_breaker") is not True:
        return None
    if _non_empty_text(latest.get("runtime_stability_status")) != "flapping":
        return None
    return latest


def hold_for_flapping_circuit_breaker(
    *,
    study_root: Path,
    status_payload: dict[str, Any] | StudyRuntimeStatus,
) -> dict[str, Any] | None:
    flapping_report = _flapping_circuit_breaker_report(study_root=study_root)
    if flapping_report is None:
        return None
    payload = _status_payload(status_payload)
    episode_count = int(flapping_report.get("flapping_episode_count") or 0)
    return {
        "study_id": _non_empty_text(payload.get("study_id")),
        "quest_id": _non_empty_text(payload.get("quest_id")),
        "decision": _non_empty_text(payload.get("decision")),
        "reason": _non_empty_text(payload.get("reason")),
        "hold_reason": "flapping_circuit_breaker_active",
        "recommended_probe": "refresh_runtime_liveness_before_resume",
        "flapping_episode_count": episode_count,
        "recovery_probe": _build_recovery_probe(
            payload=payload,
            flapping_report=flapping_report,
            episode_count=episode_count,
        ),
    }


def write_recovery_probe(*, study_root: Path, recovery_hold: dict[str, Any]) -> Path | None:
    recovery_probe = recovery_hold.get("recovery_probe")
    if not isinstance(recovery_probe, dict):
        return None
    latest_path = Path(study_root).expanduser().resolve() / "artifacts" / "runtime" / "recovery_probe" / "latest.json"
    latest_path.parent.mkdir(parents=True, exist_ok=True)
    latest_path.write_text(json.dumps(recovery_probe, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return latest_path
