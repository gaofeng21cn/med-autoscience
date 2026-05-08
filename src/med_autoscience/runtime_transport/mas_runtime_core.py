from __future__ import annotations

from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any

import yaml

BACKEND_ID = "mas_runtime_core"
ENGINE_ID = "mas-runtime-core"
CONTROLLED_RESEARCH_BACKEND_ID = BACKEND_ID
CONTROLLED_RESEARCH_ENGINE_ID = ENGINE_ID
DEFAULT_DAEMON_TIMEOUT_SECONDS = 10


def _resolved_runtime_root(runtime_root: Path) -> Path:
    return Path(runtime_root).expanduser().resolve()


def _quest_root(*, runtime_root: Path, quest_id: str) -> Path:
    normalized_quest_id = str(quest_id or "").strip()
    if not normalized_quest_id:
        raise ValueError("quest_id is required")
    quest_path = Path(normalized_quest_id)
    if quest_path.is_absolute() or ".." in quest_path.parts or len(quest_path.parts) != 1:
        raise ValueError("quest_id must be a single relative path segment")
    return _resolved_runtime_root(runtime_root) / "quests" / normalized_quest_id


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def _run_id(*, quest_id: str) -> str:
    slug = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    safe_quest_id = "".join(ch if ch.isalnum() or ch in "-_." else "-" for ch in quest_id).strip("-") or "quest"
    return f"mas-run-{safe_quest_id}-{slug}"


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _read_yaml(path: Path) -> dict[str, Any]:
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except FileNotFoundError:
        return {}
    return payload if isinstance(payload, dict) else {}


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_yaml(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rendered = yaml.safe_dump(payload, allow_unicode=True, sort_keys=False)
    path.write_text(rendered if rendered.endswith("\n") else f"{rendered}\n", encoding="utf-8")


def _state_path(quest_root: Path) -> Path:
    return quest_root / ".ds" / "runtime_state.json"


def _event_log_path(quest_root: Path) -> Path:
    return quest_root / "artifacts" / "runtime" / "mas_runtime_events.jsonl"


def _snapshot(*, quest_root: Path) -> dict[str, Any]:
    quest_payload = _read_yaml(quest_root / "quest.yaml")
    state = _read_json(_state_path(quest_root))
    quest_id = str(state.get("quest_id") or quest_payload.get("quest_id") or quest_root.name).strip() or quest_root.name
    status = str(state.get("status") or quest_payload.get("status") or "").strip() or None
    active_run_id = str(state.get("active_run_id") or quest_payload.get("active_run_id") or "").strip() or None
    return {
        "quest_id": quest_id,
        "status": status,
        "active_run_id": active_run_id,
        "runtime_backend_id": str(state.get("runtime_backend_id") or BACKEND_ID),
        "runtime_engine_id": str(state.get("runtime_engine_id") or ENGINE_ID),
        "worker_running": state.get("worker_running") if isinstance(state.get("worker_running"), bool) else None,
        "worker_pending": state.get("worker_pending") if isinstance(state.get("worker_pending"), bool) else None,
        "stop_requested": state.get("stop_requested") if isinstance(state.get("stop_requested"), bool) else None,
        "updated_at": str(state.get("updated_at") or "").strip() or None,
    }


def _persist_state(
    *,
    quest_root: Path,
    status: str,
    source: str,
    active_run_id: str | None = None,
    worker_running: bool | None = None,
    worker_pending: bool | None = None,
    stop_requested: bool | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    now = _utc_now()
    previous = _read_json(_state_path(quest_root))
    payload: dict[str, Any] = {
        **previous,
        "quest_id": quest_root.name,
        "status": status,
        "active_run_id": active_run_id,
        "worker_running": worker_running,
        "worker_pending": worker_pending,
        "stop_requested": stop_requested,
        "runtime_backend_id": BACKEND_ID,
        "runtime_engine_id": ENGINE_ID,
        "external_mds_required": False,
        "source": source,
        "updated_at": now,
    }
    if extra:
        payload.update(extra)
    _write_json(_state_path(quest_root), payload)
    _append_event(quest_root=quest_root, event={"event": status, "source": source, "recorded_at": now, "snapshot": payload})
    return payload


def _append_event(*, quest_root: Path, event: dict[str, Any]) -> None:
    path = _event_log_path(quest_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")


def _result(*, quest_root: Path, status: str, source: str, **extra: Any) -> dict[str, Any]:
    snapshot = _snapshot(quest_root=quest_root)
    return {
        "ok": True,
        "status": status,
        "source": source,
        "quest_id": quest_root.name,
        "snapshot": snapshot,
        **extra,
    }


def resolve_daemon_url(*, runtime_root: Path) -> str:
    return _resolved_runtime_root(runtime_root).as_uri()


def create_quest(*, runtime_root: Path, payload: dict[str, Any]) -> dict[str, Any]:
    quest_id = str(payload.get("quest_id") or payload.get("study_id") or "").strip()
    quest_root = _quest_root(runtime_root=runtime_root, quest_id=quest_id)
    quest_root.mkdir(parents=True, exist_ok=True)
    quest_payload = {
        "quest_id": quest_id,
        "study_id": str(payload.get("study_id") or quest_id),
        "status": "created",
        "runtime_backend_id": BACKEND_ID,
        "runtime_engine_id": ENGINE_ID,
    }
    _write_yaml(quest_root / "quest.yaml", quest_payload)
    _write_json(quest_root / "artifacts" / "runtime" / "create_payload.json", dict(payload))
    _persist_state(quest_root=quest_root, status="created", source="mas_runtime_core.create_quest")
    return _result(quest_root=quest_root, status="created", source="mas_runtime_core")


def resume_quest(*, runtime_root: Path, quest_id: str, source: str) -> dict[str, Any]:
    quest_root = _quest_root(runtime_root=runtime_root, quest_id=quest_id)
    if not (quest_root / "quest.yaml").is_file():
        raise RuntimeError(f"MAS runtime quest is missing: {quest_root}")
    active_run_id = _run_id(quest_id=quest_root.name)
    _persist_state(
        quest_root=quest_root,
        status="running",
        source=source,
        active_run_id=active_run_id,
        worker_running=True,
        worker_pending=False,
        stop_requested=False,
    )
    return _result(
        quest_root=quest_root,
        status="running",
        source="mas_runtime_core",
        active_run_id=active_run_id,
        started=True,
        queued=False,
        scheduled=False,
    )


def pause_quest(*, runtime_root: Path, quest_id: str, source: str) -> dict[str, Any]:
    quest_root = _quest_root(runtime_root=runtime_root, quest_id=quest_id)
    if not (quest_root / "quest.yaml").is_file():
        raise RuntimeError(f"MAS runtime quest is missing: {quest_root}")
    _persist_state(
        quest_root=quest_root,
        status="paused",
        source=source,
        active_run_id=None,
        worker_running=False,
        worker_pending=False,
        stop_requested=False,
    )
    return _result(quest_root=quest_root, status="paused", source="mas_runtime_core")


def stop_quest(
    *,
    daemon_url: str | None = None,
    runtime_root: Path | None = None,
    quest_id: str,
    source: str,
) -> dict[str, Any]:
    if runtime_root is None:
        raise ValueError("runtime_root is required for MAS runtime core stop_quest")
    quest_root = _quest_root(runtime_root=runtime_root, quest_id=quest_id)
    if not (quest_root / "quest.yaml").is_file():
        raise RuntimeError(f"MAS runtime quest is missing: {quest_root}")
    _persist_state(
        quest_root=quest_root,
        status="stopped",
        source=source,
        active_run_id=None,
        worker_running=False,
        worker_pending=False,
        stop_requested=True,
        extra={"daemon_url": daemon_url},
    )
    return _result(quest_root=quest_root, status="stopped", source="mas_runtime_core")


def get_quest_session(
    *,
    quest_id: str,
    daemon_url: str | None = None,
    runtime_root: Path | None = None,
    timeout: int | None = None,
) -> dict[str, Any]:
    if runtime_root is None:
        raise ValueError("runtime_root is required for MAS runtime core get_quest_session")
    quest_root = _quest_root(runtime_root=runtime_root, quest_id=quest_id)
    snapshot = _snapshot(quest_root=quest_root)
    runtime_audit = inspect_quest_live_runtime(
        quest_id=quest_id,
        daemon_url=daemon_url,
        runtime_root=runtime_root,
        timeout=timeout,
    )
    return {
        "ok": True,
        "status": snapshot["status"],
        "source": "mas_runtime_core",
        "snapshot": snapshot,
        "runtime_audit": runtime_audit,
    }


def inspect_quest_live_runtime(
    *,
    quest_id: str,
    daemon_url: str | None = None,
    runtime_root: Path | None = None,
    timeout: int | None = None,
) -> dict[str, Any]:
    if runtime_root is None:
        raise ValueError("runtime_root is required for MAS runtime core inspect_quest_live_runtime")
    snapshot = _snapshot(quest_root=_quest_root(runtime_root=runtime_root, quest_id=quest_id))
    live = snapshot["status"] == "running" and bool(snapshot["active_run_id"]) and snapshot["worker_running"] is True
    return {
        "ok": True,
        "status": "live" if live else "none",
        "source": "mas_runtime_core_local_state",
        "active_run_id": snapshot["active_run_id"],
        "worker_running": snapshot["worker_running"] is True,
        "worker_pending": snapshot["worker_pending"] is True,
        "stop_requested": snapshot["stop_requested"] is True,
    }


def inspect_quest_live_bash_sessions(
    *,
    quest_id: str,
    daemon_url: str | None = None,
    runtime_root: Path | None = None,
    timeout: int | None = None,
) -> dict[str, Any]:
    if runtime_root is None:
        raise ValueError("runtime_root is required for MAS runtime core inspect_quest_live_bash_sessions")
    _snapshot(quest_root=_quest_root(runtime_root=runtime_root, quest_id=quest_id))
    return {
        "ok": True,
        "status": "none",
        "source": "mas_runtime_core_no_external_bash_session",
        "session_count": 0,
        "live_session_count": 0,
        "live_session_ids": [],
    }


def inspect_quest_live_execution(
    *,
    quest_id: str,
    daemon_url: str | None = None,
    runtime_root: Path | None = None,
    timeout: int | None = None,
) -> dict[str, Any]:
    runtime_audit = inspect_quest_live_runtime(
        quest_id=quest_id,
        daemon_url=daemon_url,
        runtime_root=runtime_root,
        timeout=timeout,
    )
    live = runtime_audit["status"] == "live"
    return {
        "ok": True,
        "status": "live" if live else "none",
        "source": "mas_runtime_core_local_state",
        "active_run_id": runtime_audit["active_run_id"],
        "runner_live": live,
        "bash_live": False,
        "runtime_audit": runtime_audit,
        "bash_session_audit": inspect_quest_live_bash_sessions(
            quest_id=quest_id,
            daemon_url=daemon_url,
            runtime_root=runtime_root,
            timeout=timeout,
        ),
    }


def update_quest_startup_context(
    *,
    runtime_root: Path,
    quest_id: str,
    startup_contract: dict[str, Any] | None = None,
    requested_baseline_ref: dict[str, Any] | None = None,
) -> dict[str, Any]:
    quest_root = _quest_root(runtime_root=runtime_root, quest_id=quest_id)
    if not (quest_root / "quest.yaml").is_file():
        raise RuntimeError(f"MAS runtime quest is missing: {quest_root}")
    payload = {
        "quest_id": quest_root.name,
        "startup_contract": startup_contract,
        "requested_baseline_ref": requested_baseline_ref,
        "updated_at": _utc_now(),
        "runtime_backend_id": BACKEND_ID,
    }
    _write_json(quest_root / "artifacts" / "runtime" / "startup_context.json", payload)
    return {
        "ok": True,
        "status": "updated",
        "source": "mas_runtime_core",
        "quest_id": quest_root.name,
        "snapshot": payload,
    }


def chat_quest(
    *,
    runtime_root: Path,
    quest_id: str,
    text: str,
    source: str,
    reply_to_interaction_id: str | None = None,
    decision_response: dict[str, Any] | None = None,
) -> dict[str, Any]:
    quest_root = _quest_root(runtime_root=runtime_root, quest_id=quest_id)
    if not (quest_root / "quest.yaml").is_file():
        raise RuntimeError(f"MAS runtime quest is missing: {quest_root}")
    payload = {
        "text": text,
        "source": source,
        "reply_to_interaction_id": reply_to_interaction_id,
        "decision_response": decision_response,
        "recorded_at": _utc_now(),
    }
    _append_event(quest_root=quest_root, event={"event": "chat", **payload})
    return {"ok": True, "status": "queued", "source": "mas_runtime_core", "message": payload}


def artifact_complete_quest(*, runtime_root: Path, quest_id: str, summary: str) -> dict[str, Any]:
    quest_root = _quest_root(runtime_root=runtime_root, quest_id=quest_id)
    if not (quest_root / "quest.yaml").is_file():
        raise RuntimeError(f"MAS runtime quest is missing: {quest_root}")
    _persist_state(
        quest_root=quest_root,
        status="completed",
        source="mas_runtime_core.artifact_complete",
        active_run_id=None,
        worker_running=False,
        worker_pending=False,
        stop_requested=False,
        extra={"completion_summary": summary},
    )
    return _result(quest_root=quest_root, status="completed", source="mas_runtime_core")


def artifact_interact(*, runtime_root: Path, quest_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    quest_root = _quest_root(runtime_root=runtime_root, quest_id=quest_id)
    if not (quest_root / "quest.yaml").is_file():
        raise RuntimeError(f"MAS runtime quest is missing: {quest_root}")
    _append_event(quest_root=quest_root, event={"event": "artifact_interact", "payload": payload, "recorded_at": _utc_now()})
    return {"ok": True, "status": "queued", "source": "mas_runtime_core", "snapshot": _snapshot(quest_root=quest_root)}


def release_idle_workspace_daemon(
    *,
    runtime_root: Path,
    idle_ttl_seconds: int = 300,
    pending_lease_seconds: int = 3600,
) -> dict[str, Any]:
    resolved_runtime_root = _resolved_runtime_root(runtime_root)
    live_leases: list[dict[str, Any]] = []
    quests_root = resolved_runtime_root / "quests"
    if quests_root.is_dir():
        for quest_dir in sorted(quests_root.iterdir(), key=lambda item: item.name):
            if not quest_dir.is_dir():
                continue
            snapshot = _snapshot(quest_root=quest_dir)
            if snapshot["status"] == "running" and snapshot["active_run_id"]:
                live_leases.append(
                    {
                        "quest_id": quest_dir.name,
                        "lease_kind": "mas_runtime_core_run",
                        "status": snapshot["status"],
                        "active_run_id": snapshot["active_run_id"],
                        "worker_running": snapshot["worker_running"] is True,
                    }
                )
    return {
        "surface": "workspace_daemon_lifecycle",
        "released": False,
        "reason": "no_external_workspace_daemon_in_mas_runtime_core",
        "runtime_root": str(resolved_runtime_root),
        "daemon_lifecycle": {
            "status": "active" if live_leases else "idle",
            "active_lease_count": len(live_leases),
            "active_leases": live_leases,
            "idle_seconds": 0,
        },
    }
