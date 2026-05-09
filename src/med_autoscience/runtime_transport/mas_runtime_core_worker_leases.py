from __future__ import annotations

from collections.abc import Callable, Mapping
from datetime import UTC, datetime
import os
from pathlib import Path
import signal
import subprocess
import time
from typing import Any

from med_autoscience.runtime_transport.mas_runtime_core_turn_utils import pid_live, text


def worker_lease_status(
    *,
    lease: Mapping[str, Any],
    run_id: str | None,
    now: Callable[[], datetime],
    parse_time: Callable[[str | None], datetime | None],
    pid_live_check: Callable[[int], bool],
    ttl_seconds: int,
) -> dict[str, Any]:
    if not run_id or lease.get("run_id") != run_id:
        return _lease_status(live=False, monitor_state="unknown", stale_reason="run_id_mismatch")
    monitor_state = text(lease.get("monitor_state")) or "unknown"
    heartbeat_age_seconds = _heartbeat_age_seconds(
        heartbeat=parse_time(text(lease.get("heartbeat_at"))),
        now=now,
    )
    if monitor_state == "exited" or lease.get("child_returncode") is not None:
        return _lease_status(live=False, monitor_state="exited", heartbeat_age_seconds=heartbeat_age_seconds)
    child_status = _child_pid_status(lease=lease, pid_live_check=pid_live_check, heartbeat_age_seconds=heartbeat_age_seconds)
    if child_status is not None:
        return child_status
    monitor_status = _monitor_pid_status(
        lease=lease,
        monitor_state=monitor_state,
        heartbeat_age_seconds=heartbeat_age_seconds,
        ttl_seconds=ttl_seconds,
        pid_live_check=pid_live_check,
    )
    if monitor_status is not None:
        return monitor_status
    pid_status = _direct_pid_status(lease=lease, pid_live_check=pid_live_check, heartbeat_age_seconds=heartbeat_age_seconds)
    if pid_status is not None:
        return pid_status
    return _heartbeat_status(heartbeat_age_seconds=heartbeat_age_seconds, ttl_seconds=ttl_seconds)


def _heartbeat_age_seconds(*, heartbeat: datetime | None, now: Callable[[], datetime]) -> int | None:
    if heartbeat is None:
        return None
    return max(0, int((now().astimezone(UTC) - heartbeat).total_seconds()))


def _lease_status(
    *,
    live: bool,
    monitor_state: str,
    stale_reason: str | None = None,
    heartbeat_age_seconds: int | None = None,
) -> dict[str, Any]:
    return {
        "live": live,
        "monitor_state": monitor_state,
        "stale_reason": stale_reason,
        "heartbeat_age_seconds": heartbeat_age_seconds,
    }


def _child_pid_status(
    *,
    lease: Mapping[str, Any],
    pid_live_check: Callable[[int], bool],
    heartbeat_age_seconds: int | None,
) -> dict[str, Any] | None:
    child_pid = lease.get("child_pid")
    if not isinstance(child_pid, int) or child_pid <= 0:
        return None
    child_live = pid_live_check(child_pid)
    return _lease_status(
        live=child_live,
        monitor_state="live" if child_live else "lost",
        stale_reason=None if child_live else "child_pid_not_live",
        heartbeat_age_seconds=heartbeat_age_seconds,
    )


def _monitor_pid_status(
    *,
    lease: Mapping[str, Any],
    monitor_state: str,
    heartbeat_age_seconds: int | None,
    ttl_seconds: int,
    pid_live_check: Callable[[int], bool],
) -> dict[str, Any] | None:
    monitor_pid = lease.get("monitor_pid")
    if not isinstance(monitor_pid, int) or monitor_pid <= 0:
        return None
    if pid_live_check(monitor_pid):
        return _lease_status(
            live=True,
            monitor_state=monitor_state if monitor_state != "unknown" else "live",
            heartbeat_age_seconds=heartbeat_age_seconds,
        )
    if heartbeat_age_seconds is None or heartbeat_age_seconds > ttl_seconds:
        return _lease_status(
            live=False,
            monitor_state="lost",
            stale_reason="wrapper_pid_not_live",
            heartbeat_age_seconds=heartbeat_age_seconds,
        )
    return _lease_status(live=True, monitor_state="live", heartbeat_age_seconds=heartbeat_age_seconds)


def _direct_pid_status(
    *,
    lease: Mapping[str, Any],
    pid_live_check: Callable[[int], bool],
    heartbeat_age_seconds: int | None,
) -> dict[str, Any] | None:
    pid = lease.get("pid")
    if not isinstance(pid, int) or pid <= 0:
        return None
    pid_is_live = pid_live_check(pid)
    return _lease_status(
        live=pid_is_live,
        monitor_state="live" if pid_is_live else "lost",
        stale_reason=None if pid_is_live else "pid_not_live",
        heartbeat_age_seconds=heartbeat_age_seconds,
    )


def _heartbeat_status(*, heartbeat_age_seconds: int | None, ttl_seconds: int) -> dict[str, Any]:
    if heartbeat_age_seconds is None:
        return _lease_status(live=False, monitor_state="unknown", stale_reason="heartbeat_missing")
    if heartbeat_age_seconds > ttl_seconds:
        return _lease_status(
            live=False,
            monitor_state="stale",
            stale_reason="heartbeat_ttl_exceeded",
            heartbeat_age_seconds=heartbeat_age_seconds,
        )
    return _lease_status(live=True, monitor_state="live", heartbeat_age_seconds=heartbeat_age_seconds)


def worker_lease_live(
    *,
    lease: Mapping[str, Any],
    run_id: str | None,
    now: Callable[[], datetime],
    parse_time: Callable[[str | None], datetime | None],
    pid_live_check: Callable[[int], bool],
    ttl_seconds: int,
) -> bool:
    return bool(
        worker_lease_status(
            lease=lease,
            run_id=run_id,
            now=now,
            parse_time=parse_time,
            pid_live_check=pid_live_check,
            ttl_seconds=ttl_seconds,
        )["live"]
    )


def terminate_worker_leases(
    *,
    quest_root: Path,
    source: str,
    reason: str,
    utc_now: Callable[[], str],
    read_json: Callable[[Path], dict[str, Any]],
    write_json: Callable[[Path, Mapping[str, Any]], None],
    append_runtime_event: Callable[..., None],
) -> dict[str, Any]:
    leases = _worker_leases(quest_root=quest_root, read_json=read_json)
    return _terminate_leases(
        quest_root=quest_root,
        leases=leases,
        source=source,
        reason=reason,
        utc_now=utc_now,
        write_json=write_json,
        append_runtime_event=append_runtime_event,
    )


def terminate_orphan_worker_leases(
    *,
    quest_root: Path,
    active_run_id: str | None,
    source: str,
    reason: str,
    utc_now: Callable[[], str],
    read_json: Callable[[Path], dict[str, Any]],
    write_json: Callable[[Path, Mapping[str, Any]], None],
    append_runtime_event: Callable[..., None],
) -> dict[str, Any] | None:
    leases = [
        (lease_path, lease)
        for lease_path, lease in _worker_leases(quest_root=quest_root, read_json=read_json)
        if (text(lease.get("run_id")) or lease_path.parent.name) != active_run_id
    ]
    if not leases:
        return None
    return _terminate_leases(
        quest_root=quest_root,
        leases=tuple(leases),
        source=source,
        reason=reason,
        utc_now=utc_now,
        write_json=write_json,
        append_runtime_event=append_runtime_event,
    )


def _terminate_leases(
    *,
    quest_root: Path,
    leases: tuple[tuple[Path, dict[str, Any]], ...],
    source: str,
    reason: str,
    utc_now: Callable[[], str],
    write_json: Callable[[Path, Mapping[str, Any]], None],
    append_runtime_event: Callable[..., None],
) -> dict[str, Any]:
    terminations: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    for lease_path, lease in leases:
        run_id = text(lease.get("run_id")) or lease_path.parent.name
        pid = lease.get("child_pid") or lease.get("monitor_pid") or lease.get("pid")
        if not isinstance(pid, int) or pid <= 0:
            skipped.append({"run_id": run_id, "lease_path": str(lease_path), "reason": "missing_pid"})
            continue
        result = _terminate_leased_pid(pid=pid)
        record = {
            "run_id": run_id,
            "pid": pid,
            "lease_path": str(lease_path),
            **result,
        }
        terminations.append(record)
        updated_lease = {
            **lease,
            "termination_requested_at": utc_now(),
            "termination_reason": reason,
            "termination_source": source,
            "termination_result": result,
        }
        write_json(lease_path, updated_lease)
    payload = {
        "schema_version": 1,
        "event": "worker_lease_termination",
        "source": source,
        "reason": reason,
        "recorded_at": utc_now(),
        "quest_id": quest_root.name,
        "lease_count": len(leases),
        "termination_count": len(terminations),
        "terminations": terminations,
        "skipped": skipped,
    }
    append_runtime_event(quest_root=quest_root, event=payload)
    return payload


def _worker_leases(
    *,
    quest_root: Path,
    read_json: Callable[[Path], dict[str, Any]],
) -> tuple[tuple[Path, dict[str, Any]], ...]:
    runs_root = quest_root / ".ds" / "runs"
    leases: list[tuple[Path, dict[str, Any]]] = []
    for lease_path in sorted(runs_root.glob("*/worker_lease.json")):
        lease = read_json(lease_path)
        if not lease:
            continue
        run_id = text(lease.get("run_id")) or lease_path.parent.name
        lease_quest_id = text(lease.get("quest_id"))
        if lease_quest_id and lease_quest_id != quest_root.name:
            continue
        if run_id != lease_path.parent.name:
            continue
        leases.append((lease_path, lease))
    return tuple(leases)


def _terminate_leased_pid(*, pid: int) -> dict[str, Any]:
    if pid == os.getpid():
        return {"status": "skipped", "reason": "current_process_pid"}
    if not _pid_active(pid=pid):
        return {"status": "already_exited", "live_before": False}
    target: tuple[str, int] = ("pid", pid)
    try:
        pgid = os.getpgid(pid)
    except OSError:
        pgid = None
    try:
        current_pgid = os.getpgid(0)
    except OSError:
        current_pgid = None
    if pgid is not None and pgid == pid and pgid != current_pgid:
        target = ("pgid", pgid)
    term_error = _send_signal(target=target, sig=signal.SIGTERM)
    if term_error is not None and target[0] == "pgid":
        target = ("pid", pid)
        term_error = _send_signal(target=target, sig=signal.SIGTERM)
    if _wait_pid_not_live(pid=pid, timeout_seconds=2.0):
        payload = {"status": "terminated", "live_before": True, "signal": "SIGTERM", "target": target[0]}
        if term_error is not None:
            payload["signal_error"] = term_error
        return payload
    kill_error = _send_signal(target=target, sig=signal.SIGKILL)
    if _wait_pid_not_live(pid=pid, timeout_seconds=1.0):
        payload = {"status": "killed", "live_before": True, "signal": "SIGKILL", "target": target[0]}
        if kill_error is not None:
            payload["signal_error"] = kill_error
        return payload
    payload = {"status": "kill_timeout", "live_before": True, "target": target[0]}
    if kill_error is not None:
        payload["signal_error"] = kill_error
    return payload


def _send_signal(*, target: tuple[str, int], sig: signal.Signals) -> str | None:
    target_type, target_id = target
    try:
        if target_type == "pgid":
            os.killpg(target_id, sig)
        else:
            os.kill(target_id, sig)
    except ProcessLookupError:
        return None
    except PermissionError as exc:
        return f"{type(exc).__name__}: {exc}"
    return None


def _wait_pid_not_live(*, pid: int, timeout_seconds: float) -> bool:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if not _pid_active(pid=pid):
            return True
        time.sleep(0.02)
    return not _pid_active(pid=pid)


def _pid_active(*, pid: int) -> bool:
    if not pid_live(pid):
        return False
    try:
        result = subprocess.run(
            ["ps", "-o", "stat=", "-p", str(pid)],
            text=True,
            capture_output=True,
            check=False,
            timeout=0.5,
        )
    except (OSError, subprocess.TimeoutExpired):
        return True
    if result.returncode != 0:
        return False
    status = result.stdout.strip()
    return not status.startswith("Z")
