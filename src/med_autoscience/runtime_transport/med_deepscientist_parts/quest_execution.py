from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from med_autoscience.runtime_transport.med_deepscientist_parts.quest_sessions import (
    GetQuestSession,
)
from med_autoscience.runtime_transport.med_deepscientist_parts.quest_watchdogs import (
    _interaction_watchdog_payload,
    _stale_progress_watchdog,
)
from med_autoscience.runtime_transport.med_deepscientist_parts.storage import _load_json_dict, _load_yaml_dict


InspectQuestLiveRuntime = Callable[..., dict[str, Any]]
InspectQuestLiveBashSessions = Callable[..., dict[str, Any]]
InferLocalRuntimeLiveness = Callable[..., dict[str, Any] | None]


def inspect_quest_live_runtime(
    *,
    quest_id: str,
    get_quest_session_fn: GetQuestSession,
    daemon_url: str | None = None,
    runtime_root: Path | None = None,
    timeout: int,
) -> dict[str, Any]:
    try:
        payload = get_quest_session_fn(
            quest_id=quest_id,
            daemon_url=daemon_url,
            runtime_root=runtime_root,
            timeout=timeout,
        )
    except RuntimeError as exc:
        return {
            "ok": False,
            "status": "unknown",
            "source": "quest_session_runtime_audit",
            "active_run_id": None,
            "worker_running": None,
            "worker_pending": None,
            "stop_requested": None,
            "error": str(exc),
        }

    runtime_audit = payload.get("runtime_audit") if isinstance(payload.get("runtime_audit"), dict) else None
    snapshot = payload.get("snapshot") if isinstance(payload.get("snapshot"), dict) else {}
    active_run_id = str((runtime_audit or {}).get("active_run_id") or snapshot.get("active_run_id") or "").strip() or None
    if runtime_audit is None:
        return {
            "ok": False,
            "status": "unknown",
            "source": "quest_session_runtime_audit",
            "active_run_id": active_run_id,
            "worker_running": None,
            "worker_pending": None,
            "stop_requested": None,
            "error": "Quest session probe returned no runtime_audit payload.",
        }

    status = str(runtime_audit.get("status") or "").strip().lower()
    if status not in {"live", "none"}:
        return {
            "ok": False,
            "status": "unknown",
            "source": str(runtime_audit.get("source") or "quest_session_runtime_audit"),
            "active_run_id": active_run_id,
            "worker_running": None,
            "worker_pending": None,
            "stop_requested": None,
            "error": f"Unsupported runtime audit status: {status or 'empty'}",
        }

    interaction_watchdog = _interaction_watchdog_payload(snapshot)
    stale_progress = status == "live" and _stale_progress_watchdog(
        interaction_watchdog,
        snapshot=snapshot,
        runtime_root=runtime_root,
        quest_id=quest_id,
    )
    result = {
        "ok": bool(runtime_audit.get("ok", True)),
        "status": status,
        "source": str(runtime_audit.get("source") or "quest_session_runtime_audit"),
        "active_run_id": active_run_id,
        "worker_running": bool(runtime_audit.get("worker_running")) if "worker_running" in runtime_audit else None,
        "worker_pending": bool(runtime_audit.get("worker_pending")) if "worker_pending" in runtime_audit else None,
        "stop_requested": bool(runtime_audit.get("stop_requested")) if "stop_requested" in runtime_audit else None,
    }
    runtime_event_contract_error = str(payload.get("runtime_event_contract_error") or "").strip() or None
    if runtime_event_contract_error is not None:
        result["runtime_event_contract_error"] = runtime_event_contract_error
    runtime_event_ref_contract_error = str(payload.get("runtime_event_ref_contract_error") or "").strip() or None
    if runtime_event_ref_contract_error is not None:
        result["runtime_event_ref_contract_error"] = runtime_event_ref_contract_error
    runtime_event_ref_payload = payload.get("runtime_event_ref")
    if isinstance(runtime_event_ref_payload, dict):
        result["runtime_event_ref"] = dict(runtime_event_ref_payload)
    runtime_event_payload = payload.get("runtime_event")
    if isinstance(runtime_event_payload, dict):
        result["runtime_event"] = dict(runtime_event_payload)
    if interaction_watchdog is not None:
        result["interaction_watchdog"] = interaction_watchdog
    if stale_progress:
        result["stale_progress"] = True
        result["liveness_guard_reason"] = "stale_progress_watchdog"
    return result


def inspect_quest_live_execution(
    *,
    quest_id: str,
    inspect_quest_live_runtime_fn: InspectQuestLiveRuntime,
    inspect_quest_live_bash_sessions_fn: InspectQuestLiveBashSessions,
    infer_local_runtime_liveness_fn: InferLocalRuntimeLiveness,
    daemon_url: str | None = None,
    runtime_root: Path | None = None,
    timeout: int,
) -> dict[str, Any]:
    runtime_audit = inspect_quest_live_runtime_fn(
        quest_id=quest_id,
        daemon_url=daemon_url,
        runtime_root=runtime_root,
        timeout=timeout,
    )
    bash_session_audit = inspect_quest_live_bash_sessions_fn(
        quest_id=quest_id,
        daemon_url=daemon_url,
        runtime_root=runtime_root,
        timeout=timeout,
    )
    runtime_audit_status = str(runtime_audit.get("status") or "").strip()
    runtime_active_run_id = str(runtime_audit.get("active_run_id") or "").strip() or None
    runtime_live_missing_active_run_id = runtime_audit_status == "live" and runtime_active_run_id is None
    runtime_live = runtime_audit_status == "live" and runtime_active_run_id is not None
    bash_live = str(bash_session_audit.get("status") or "").strip() == "live"
    runtime_known = runtime_audit_status in {"live", "none"}
    bash_known = str(bash_session_audit.get("status") or "").strip() in {"live", "none"}
    stale_progress = bool(runtime_audit.get("stale_progress"))
    liveness_guard_reason = str(runtime_audit.get("liveness_guard_reason") or "").strip() or None
    if stale_progress:
        status = "unknown"
        ok = False
    elif runtime_live_missing_active_run_id and not bash_live:
        status = "unknown"
        ok = False
        liveness_guard_reason = "live_runtime_missing_active_run_id"
    elif runtime_live or bash_live:
        status = "live"
        ok = True
    elif runtime_known and bash_known:
        status = "none"
        ok = True
    else:
        local_runtime_liveness = (
            infer_local_runtime_liveness_fn(runtime_root=runtime_root, quest_id=quest_id)
            if runtime_root is not None
            else None
        )
        if local_runtime_liveness is not None:
            payload = {
                "ok": True,
                "status": "none",
                "source": "local_runtime_state_contract",
                "active_run_id": local_runtime_liveness.get("active_run_id"),
                "runner_live": False,
                "bash_live": False,
                "runtime_audit": runtime_audit,
                "bash_session_audit": bash_session_audit,
                "local_runtime_state": local_runtime_liveness,
            }
            errors = [str(item) for item in [runtime_audit.get("error"), bash_session_audit.get("error")] if item]
            if errors:
                payload["probe_error"] = " | ".join(errors)
            return payload
        status = "unknown"
        ok = False
    payload = {
        "ok": ok,
        "status": status,
        "source": "combined_runner_or_bash_session",
        "active_run_id": runtime_active_run_id,
        "runner_live": runtime_live,
        "bash_live": bash_live,
        "runtime_audit": runtime_audit,
        "bash_session_audit": bash_session_audit,
    }
    if isinstance(runtime_audit.get("runtime_event_ref"), dict):
        payload["runtime_event_ref"] = dict(runtime_audit.get("runtime_event_ref") or {})
    if isinstance(runtime_audit.get("runtime_event"), dict):
        payload["runtime_event"] = dict(runtime_audit.get("runtime_event") or {})
    if stale_progress:
        payload["stale_progress"] = True
    if liveness_guard_reason is not None:
        payload["liveness_guard_reason"] = liveness_guard_reason
    errors: list[str] = []
    if stale_progress:
        errors.append("Live managed runtime exceeded the artifact interaction silence threshold.")
    if runtime_live_missing_active_run_id:
        errors.append("Live managed runtime reported worker activity without an active_run_id.")
    errors.extend(str(item) for item in [runtime_audit.get("error"), bash_session_audit.get("error")] if item)
    if errors:
        payload["error"] = " | ".join(errors)
    return payload


def _infer_local_runtime_liveness(*, runtime_root: Path, quest_id: str) -> dict[str, Any] | None:
    quest_root = Path(runtime_root).expanduser().resolve() / "quests" / quest_id
    quest_yaml_path = quest_root / "quest.yaml"
    runtime_state_path = quest_root / ".ds" / "runtime_state.json"
    if not quest_yaml_path.exists():
        return None
    quest_data = _load_yaml_dict(quest_yaml_path)
    runtime_state = _load_json_dict(runtime_state_path)
    status = str(runtime_state.get("status") or quest_data.get("status") or "").strip()
    active_run_id = str(runtime_state.get("active_run_id") or quest_data.get("active_run_id") or "").strip() or None
    if active_run_id or status == "running":
        return None
    return {
        "status": status or None,
        "active_run_id": active_run_id,
        "continuation_policy": str(runtime_state.get("continuation_policy") or "").strip() or None,
        "continuation_anchor": str(runtime_state.get("continuation_anchor") or "").strip() or None,
        "continuation_reason": str(runtime_state.get("continuation_reason") or "").strip() or None,
    }
