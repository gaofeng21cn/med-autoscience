from __future__ import annotations

from collections.abc import Callable, Mapping
from datetime import UTC, datetime
import json
from pathlib import Path
import subprocess
from typing import Any

from med_autoscience.runtime_transport.med_deepscientist_parts.storage import _load_json_dict


RunLauncher = Callable[..., subprocess.CompletedProcess[str]]


def release_idle_workspace_daemon(
    *,
    runtime_root: Path,
    run_launcher: RunLauncher,
    parse_launcher_status: Callable[..., dict[str, Any]],
    idle_ttl_seconds: int = 300,
    pending_lease_seconds: int = 3600,
) -> dict[str, Any]:
    resolved_runtime_root = Path(runtime_root).expanduser().resolve()
    status_result = run_launcher(runtime_root=resolved_runtime_root, args=("--status",))
    status_payload = parse_launcher_status(result=status_result, runtime_root=resolved_runtime_root)
    lifecycle = workspace_daemon_lifecycle(
        runtime_root=resolved_runtime_root,
        status_payload=status_payload,
        pending_lease_seconds=pending_lease_seconds,
    )
    if not _healthy_managed_daemon(status_payload):
        return _result(
            released=False,
            reason="workspace_daemon_not_healthy",
            runtime_root=resolved_runtime_root,
            daemon_lifecycle=lifecycle,
        )
    if lifecycle["active_lease_count"]:
        return _result(
            released=False,
            reason="active_quest_lease_present",
            runtime_root=resolved_runtime_root,
            daemon_lifecycle=lifecycle,
        )
    if int(idle_ttl_seconds) > 0 and lifecycle["idle_seconds"] < int(idle_ttl_seconds):
        return _result(
            released=False,
            reason="idle_ttl_not_elapsed",
            runtime_root=resolved_runtime_root,
            daemon_lifecycle=lifecycle,
        )
    stop_result = run_launcher(runtime_root=resolved_runtime_root, args=("--stop",))
    return {
        **_result(
            released=stop_result.returncode == 0,
            reason="idle_workspace_daemon_released" if stop_result.returncode == 0 else "workspace_daemon_stop_failed",
            runtime_root=resolved_runtime_root,
            daemon_lifecycle=lifecycle,
        ),
        "stop_result": {
            "returncode": stop_result.returncode,
            "stdout": str(stop_result.stdout or "").strip(),
            "stderr": str(stop_result.stderr or "").strip(),
        },
    }


def workspace_daemon_lifecycle(
    *,
    runtime_root: Path,
    status_payload: Mapping[str, Any],
    pending_lease_seconds: int,
) -> dict[str, Any]:
    resolved_runtime_root = Path(runtime_root).expanduser().resolve()
    leases = _active_quest_leases(
        runtime_root=resolved_runtime_root,
        pending_lease_seconds=pending_lease_seconds,
    )
    daemon = _mapping(status_payload.get("daemon"))
    started_at = _text(daemon.get("started_at"))
    return {
        "status": "active" if leases else "idle",
        "runtime_root": str(resolved_runtime_root),
        "daemon_id": _text(daemon.get("daemon_id")),
        "daemon_started_at": started_at,
        "idle_seconds": _idle_seconds(started_at),
        "active_lease_count": len(leases),
        "active_leases": leases,
    }


def _active_quest_leases(*, runtime_root: Path, pending_lease_seconds: int) -> list[dict[str, Any]]:
    quests_root = runtime_root / "quests"
    if not quests_root.is_dir():
        return []
    leases: list[dict[str, Any]] = []
    for quest_dir in sorted(quests_root.iterdir(), key=lambda item: item.name):
        if not quest_dir.is_dir():
            continue
        state = _load_json_dict(quest_dir / ".ds" / "runtime_state.json")
        yaml_state = _quest_yaml_state(quest_dir / "quest.yaml")
        quest_id = _text(state.get("quest_id")) or _text(yaml_state.get("quest_id")) or quest_dir.name
        status = _text(state.get("status")) or _text(yaml_state.get("status"))
        active_run_id = _text(state.get("active_run_id")) or _text(yaml_state.get("active_run_id"))
        worker_running = state.get("worker_running") is True
        if active_run_id or worker_running or status == "running":
            leases.append(
                {
                    "quest_id": quest_id,
                    "lease_kind": "live_run",
                    "status": status,
                    "active_run_id": active_run_id,
                    "worker_running": worker_running,
                }
            )
            continue
        if _recent_recovery_lease(state=state, pending_lease_seconds=pending_lease_seconds):
            leases.append(
                {
                    "quest_id": quest_id,
                    "lease_kind": "pending_recovery",
                    "status": status,
                    "active_run_id": active_run_id,
                    "worker_running": worker_running,
                    "continuation_reason": _text(state.get("continuation_reason")),
                }
            )
    return leases


def _recent_recovery_lease(*, state: Mapping[str, Any], pending_lease_seconds: int) -> bool:
    if _text(state.get("continuation_reason")) != "runtime_platform_repair_redrive":
        return False
    updated_at = _parse_time(_text(state.get("continuation_updated_at")) or _text(state.get("updated_at")))
    if updated_at is None:
        return False
    return (datetime.now(UTC) - updated_at).total_seconds() <= int(pending_lease_seconds)


def _healthy_managed_daemon(payload: Mapping[str, Any]) -> bool:
    return payload.get("healthy") is True and payload.get("identity_match") is True and payload.get("managed") is True


def _quest_yaml_state(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    result: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        key, sep, value = line.partition(":")
        if sep:
            result[key.strip()] = value.strip()
    return result


def _idle_seconds(started_at: str | None) -> int:
    parsed = _parse_time(started_at)
    if parsed is None:
        return 0
    return max(0, int((datetime.now(UTC) - parsed).total_seconds()))


def _parse_time(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _result(*, released: bool, reason: str, runtime_root: Path, daemon_lifecycle: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "surface": "workspace_daemon_lifecycle",
        "released": released,
        "reason": reason,
        "runtime_root": str(runtime_root),
        "daemon_lifecycle": dict(daemon_lifecycle),
    }


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = ["release_idle_workspace_daemon", "workspace_daemon_lifecycle"]
