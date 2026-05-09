from __future__ import annotations

from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

from med_autoscience.runtime_transport.mas_runtime_core_turn_completion import (
    inspect_logical_turn_completion,
)
from med_autoscience.runtime_transport.mas_runtime_core_worker_leases import worker_lease_status


def lease_payload_status(
    *,
    lease: Mapping[str, Any],
    run_id: str | None,
    now: Callable[[], Any],
    parse_time: Callable[[str | None], Any],
    pid_live_check: Callable[[int], bool],
    ttl_seconds: int,
) -> dict[str, Any]:
    return worker_lease_status(
        lease=lease,
        run_id=run_id,
        now=now,
        parse_time=parse_time,
        pid_live_check=pid_live_check,
        ttl_seconds=ttl_seconds,
    )


def lease_payload_live(
    *,
    lease: Mapping[str, Any],
    run_id: str | None,
    now: Callable[[], Any],
    parse_time: Callable[[str | None], Any],
    pid_live_check: Callable[[int], bool],
    ttl_seconds: int,
) -> bool:
    return bool(
        lease_payload_status(
            lease=lease,
            run_id=run_id,
            now=now,
            parse_time=parse_time,
            pid_live_check=pid_live_check,
            ttl_seconds=ttl_seconds,
        ).get("live")
    )


def watchdog_projection(*, lease: Mapping[str, Any], lease_status: Mapping[str, Any]) -> dict[str, Any] | None:
    if not lease:
        return None
    keys = (
        "monitor_kind",
        "monitor_pid",
        "child_pid",
        "last_seen_at",
        "last_output_at",
        "stdout_cursor",
        "stderr_cursor",
        "last_stdout_ref",
        "last_stderr_ref",
        "child_returncode",
        "runner_status",
    )
    projection = {key: lease.get(key) for key in keys if lease.get(key) is not None}
    projection["monitor_state"] = lease_status.get("monitor_state")
    projection["stale_reason"] = lease_status.get("stale_reason")
    projection["heartbeat_age_seconds"] = lease_status.get("heartbeat_age_seconds")
    projection["live"] = bool(lease_status.get("live"))
    return projection


def initial_worker_lease_payload(
    *,
    quest_id: str,
    run_id: str,
    reason: str,
    source: str,
    started_at: str,
    runner_receipt: Mapping[str, Any],
    text: Callable[[object], str | None],
) -> dict[str, Any]:
    lease: dict[str, Any] = {
        "schema_version": 1,
        "quest_id": quest_id,
        "run_id": run_id,
        "reason": reason,
        "source": source,
        "started_at": started_at,
        "heartbeat_at": started_at,
        "runner_kind": "mas_turn_runner",
        "monitor_kind": text(runner_receipt.get("monitor_kind")) or "in_process_runner_monitor",
        "monitor_state": "live",
        "last_seen_at": started_at,
        "last_output_at": started_at,
        "last_stdout_ref": text(runner_receipt.get("stdout_path")),
        "last_stderr_ref": text(runner_receipt.get("stderr_path")),
        "stdout_cursor": 0,
        "stderr_cursor": 0,
        "stale_reason": None,
    }
    for key in ("pid", "monitor_pid", "child_pid"):
        value = runner_receipt.get(key)
        if isinstance(value, int):
            lease[key] = value
    return lease


def reconcile_stale_liveness(
    *,
    quest_root: Path,
    source: str,
    inspect_turn_lifecycle: Callable[..., dict[str, Any]],
    text: Callable[[object], str | None],
    load_state: Callable[..., dict[str, Any]],
    persist_state: Callable[..., dict[str, Any]],
    snapshot: Callable[..., dict[str, Any]],
    turn_receipt: Callable[..., dict[str, Any]],
    make_idempotency_key: Callable[..., str],
    terminate_worker_leases: Callable[..., dict[str, Any]],
    utc_now: Callable[[], str],
    read_json: Callable[[Path], dict[str, Any]],
    write_json: Callable[[Path, Mapping[str, Any]], None],
    append_runtime_event: Callable[..., None],
) -> dict[str, Any] | None:
    lifecycle = inspect_turn_lifecycle(quest_root=quest_root)
    stale_run_id = text(lifecycle.get("stale_active_run_id"))
    stale_reason = "worker_lease_not_live"
    logical_completion = inspect_logical_turn_completion(
        quest_root=quest_root,
        run_id=text(lifecycle.get("active_run_id")) or stale_run_id,
    )
    if stale_run_id is None and logical_completion is not None:
        stale_run_id = logical_completion["run_id"]
        stale_reason = logical_completion["reason"]
        if not logical_completion["latest_receipt_terminal"]:
            _write_missed_completion_receipt(
                quest_root=quest_root,
                source=source,
                stale_run_id=stale_run_id,
                logical_completion=logical_completion,
                load_state=load_state,
                turn_receipt=turn_receipt,
                make_idempotency_key=make_idempotency_key,
            )
    if stale_run_id is None:
        return None
    worker_cleanup = _terminate_stuck_worker(
        quest_root=quest_root,
        source=source,
        stale_reason=stale_reason,
        terminate_worker_leases=terminate_worker_leases,
        utc_now=utc_now,
        read_json=read_json,
        write_json=write_json,
        append_runtime_event=append_runtime_event,
    )
    repaired = _persist_reconciled_state(
        quest_root=quest_root,
        source=source,
        stale_run_id=stale_run_id,
        stale_reason=stale_reason,
        worker_cleanup=worker_cleanup,
        load_state=load_state,
        persist_state=persist_state,
    )
    result = _reconcile_result(
        quest_root=quest_root,
        stale_run_id=stale_run_id,
        stale_reason=stale_reason,
        repaired=repaired,
        snapshot=snapshot,
    )
    if worker_cleanup is not None:
        result["worker_cleanup"] = worker_cleanup
    if logical_completion is not None:
        result["logical_completion"] = logical_completion
    return result


def _write_missed_completion_receipt(
    *,
    quest_root: Path,
    source: str,
    stale_run_id: str,
    logical_completion: Mapping[str, Any],
    load_state: Callable[..., dict[str, Any]],
    turn_receipt: Callable[..., dict[str, Any]],
    make_idempotency_key: Callable[..., str],
) -> None:
    state = load_state(quest_root=quest_root)
    turn_receipt(
        quest_root=quest_root,
        run_id=stale_run_id,
        reason=str(state.get("turn_reason") or "unknown"),
        source=source,
        status="finished",
        started=False,
        queued=False,
        idempotency_key=make_idempotency_key(
            quest_id=quest_root.name,
            reason="missed_completion_reconcile",
            source=source,
            active_run_id=stale_run_id,
        ),
        extra={
            "runner_status": "succeeded",
            "normalized_status": "active",
            "reconciled_from": dict(logical_completion),
        },
    )


def _terminate_stuck_worker(
    *,
    quest_root: Path,
    source: str,
    stale_reason: str,
    terminate_worker_leases: Callable[..., dict[str, Any]],
    utc_now: Callable[[], str],
    read_json: Callable[[Path], dict[str, Any]],
    write_json: Callable[[Path, Mapping[str, Any]], None],
    append_runtime_event: Callable[..., None],
) -> dict[str, Any] | None:
    if stale_reason != "logical_turn_completed":
        return None
    return terminate_worker_leases(
        quest_root=quest_root,
        source=source,
        reason=stale_reason,
        utc_now=utc_now,
        read_json=read_json,
        write_json=write_json,
        append_runtime_event=append_runtime_event,
    )


def _persist_reconciled_state(
    *,
    quest_root: Path,
    source: str,
    stale_run_id: str,
    stale_reason: str,
    worker_cleanup: dict[str, Any] | None,
    load_state: Callable[..., dict[str, Any]],
    persist_state: Callable[..., dict[str, Any]],
) -> dict[str, Any]:
    state = load_state(quest_root=quest_root)
    last_completed_run_id = (
        stale_run_id if stale_reason == "logical_turn_completed" else state.get("last_completed_run_id")
    )
    return persist_state(
        quest_root=quest_root,
        updates={
            "status": "active",
            "active_run_id": None,
            "last_known_run_id": stale_run_id,
            "last_completed_run_id": last_completed_run_id,
            "worker_running": False,
            "worker_pending": False,
            "continuation_policy": state.get("continuation_policy") or "auto",
            "last_liveness_reconcile_reason": stale_reason,
            "last_worker_cleanup": worker_cleanup,
        },
        source=source,
        event_name="stale_turn_reconciled",
    )


def _reconcile_result(
    *,
    quest_root: Path,
    stale_run_id: str,
    stale_reason: str,
    repaired: Mapping[str, Any],
    snapshot: Callable[..., dict[str, Any]],
) -> dict[str, Any]:
    return {
        "ok": True,
        "status": "stale",
        "active_run_id": None,
        "stale_active_run_id": stale_run_id,
        "stale_reason": stale_reason,
        "worker_running": False,
        "worker_pending": False,
        "stop_requested": repaired.get("stop_requested") is True,
        "snapshot": snapshot(quest_root=quest_root, state=repaired),
    }
