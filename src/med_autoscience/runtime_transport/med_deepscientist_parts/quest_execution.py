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


def _probe_error_message(*audits: dict[str, Any]) -> str | None:
    errors = [str(audit.get("error")) for audit in audits if audit.get("error")]
    return " | ".join(errors) if errors else None


def _runtime_audit_boolean(runtime_audit: dict[str, Any], key: str) -> bool | None:
    return bool(runtime_audit.get(key)) if key in runtime_audit else None


def _runtime_event_fields(payload: dict[str, Any]) -> dict[str, Any]:
    event_fields: dict[str, Any] = {}
    runtime_event_contract_error = str(payload.get("runtime_event_contract_error") or "").strip() or None
    if runtime_event_contract_error is not None:
        event_fields["runtime_event_contract_error"] = runtime_event_contract_error
    runtime_event_ref_contract_error = str(payload.get("runtime_event_ref_contract_error") or "").strip() or None
    if runtime_event_ref_contract_error is not None:
        event_fields["runtime_event_ref_contract_error"] = runtime_event_ref_contract_error
    runtime_event_ref_payload = payload.get("runtime_event_ref")
    if isinstance(runtime_event_ref_payload, dict):
        event_fields["runtime_event_ref"] = dict(runtime_event_ref_payload)
    runtime_event_payload = payload.get("runtime_event")
    if isinstance(runtime_event_payload, dict):
        event_fields["runtime_event"] = dict(runtime_event_payload)
    return event_fields


def _runtime_audit_result(
    *,
    runtime_audit: dict[str, Any],
    payload: dict[str, Any],
    status: str,
    active_run_id: str | None,
    interaction_watchdog: dict[str, Any] | None,
    stale_progress: bool,
) -> dict[str, Any]:
    result = {
        "ok": bool(runtime_audit.get("ok", True)),
        "status": status,
        "source": str(runtime_audit.get("source") or "quest_session_runtime_audit"),
        "active_run_id": active_run_id,
        "worker_running": _runtime_audit_boolean(runtime_audit, "worker_running"),
        "worker_pending": _runtime_audit_boolean(runtime_audit, "worker_pending"),
        "stop_requested": _runtime_audit_boolean(runtime_audit, "stop_requested"),
    }
    result.update(_runtime_event_fields(payload))
    if interaction_watchdog is not None:
        result["interaction_watchdog"] = interaction_watchdog
    if stale_progress:
        result["stale_progress"] = True
        result["liveness_guard_reason"] = "stale_progress_watchdog"
    return result


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
    return _runtime_audit_result(
        runtime_audit=runtime_audit,
        payload=payload,
        status=status,
        active_run_id=active_run_id,
        interaction_watchdog=interaction_watchdog,
        stale_progress=stale_progress,
    )


def _local_runtime_state_payload(
    *,
    runtime_audit: dict[str, Any],
    bash_session_audit: dict[str, Any],
    local_runtime_liveness: dict[str, Any],
) -> dict[str, Any]:
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
    probe_error = _probe_error_message(runtime_audit, bash_session_audit)
    if probe_error is not None:
        payload["probe_error"] = probe_error
    return payload


def _combined_liveness_status(
    *,
    runtime_live: bool,
    runtime_live_missing_active_run_id: bool,
    bash_live: bool,
    runtime_known: bool,
    bash_known: bool,
    stale_progress: bool,
) -> tuple[str, bool, str | None]:
    if stale_progress:
        return "unknown", False, None
    if runtime_live_missing_active_run_id and not bash_live:
        return "unknown", False, "live_runtime_missing_active_run_id"
    if runtime_live or bash_live:
        return "live", True, None
    if runtime_known and bash_known:
        return "none", True, None
    return "unknown", False, None


def _combined_execution_errors(
    *,
    runtime_audit: dict[str, Any],
    bash_session_audit: dict[str, Any],
    stale_progress: bool,
    runtime_live_missing_active_run_id: bool,
) -> str | None:
    errors: list[str] = []
    if stale_progress:
        errors.append("Live managed runtime exceeded the artifact interaction silence threshold.")
    if runtime_live_missing_active_run_id:
        errors.append("Live managed runtime reported worker activity without an active_run_id.")
    probe_error = _probe_error_message(runtime_audit, bash_session_audit)
    if probe_error is not None:
        errors.append(probe_error)
    return " | ".join(errors) if errors else None


def _combined_execution_payload(
    *,
    ok: bool,
    status: str,
    runtime_active_run_id: str | None,
    runtime_live: bool,
    bash_live: bool,
    runtime_audit: dict[str, Any],
    bash_session_audit: dict[str, Any],
    stale_progress: bool,
    runtime_live_missing_active_run_id: bool,
    liveness_guard_reason: str | None,
) -> dict[str, Any]:
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
    payload.update(_runtime_event_fields(runtime_audit))
    if stale_progress:
        payload["stale_progress"] = True
    if liveness_guard_reason is not None:
        payload["liveness_guard_reason"] = liveness_guard_reason
    error = _combined_execution_errors(
        runtime_audit=runtime_audit,
        bash_session_audit=bash_session_audit,
        stale_progress=stale_progress,
        runtime_live_missing_active_run_id=runtime_live_missing_active_run_id,
    )
    if error is not None:
        payload["error"] = error
    return payload


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
    status, ok, guard_override = _combined_liveness_status(
        runtime_live=runtime_live,
        runtime_live_missing_active_run_id=runtime_live_missing_active_run_id,
        bash_live=bash_live,
        runtime_known=runtime_known,
        bash_known=bash_known,
        stale_progress=stale_progress,
    )
    if guard_override is not None:
        liveness_guard_reason = guard_override
    if status == "unknown" and not stale_progress and guard_override is None and not (runtime_live or bash_live):
        local_runtime_liveness = (
            infer_local_runtime_liveness_fn(runtime_root=runtime_root, quest_id=quest_id)
            if runtime_root is not None
            else None
        )
        if local_runtime_liveness is not None:
            return _local_runtime_state_payload(
                runtime_audit=runtime_audit,
                bash_session_audit=bash_session_audit,
                local_runtime_liveness=local_runtime_liveness,
            )
    return _combined_execution_payload(
        ok=ok,
        status=status,
        runtime_active_run_id=runtime_active_run_id,
        runtime_live=runtime_live,
        bash_live=bash_live,
        runtime_audit=runtime_audit,
        bash_session_audit=bash_session_audit,
        stale_progress=stale_progress,
        runtime_live_missing_active_run_id=runtime_live_missing_active_run_id,
        liveness_guard_reason=liveness_guard_reason,
    )


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
