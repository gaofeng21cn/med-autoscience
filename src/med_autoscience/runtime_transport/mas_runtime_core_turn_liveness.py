from __future__ import annotations

from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

from med_autoscience.runtime_transport.mas_runtime_core_turn_completion import (
    read_blocked_closeout_payload,
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
    terminal_attach_capable = runner_receipt.get("terminal_attach_capable") is True
    lease.update(
        {
            "terminal_attach_capable": terminal_attach_capable,
            "terminal_bridge_status": text(runner_receipt.get("terminal_bridge_status"))
            or ("enabled" if terminal_attach_capable else "disabled_by_run_capability"),
            "terminal_bridge_kind": text(runner_receipt.get("terminal_bridge_kind")),
            "terminal_input_owner": text(runner_receipt.get("terminal_input_owner")),
            "chat_quest_input_allowed": runner_receipt.get("chat_quest_input_allowed") is True,
        }
    )
    for key in ("terminal_bridge_path", "terminal_transcript_path"):
        value = text(runner_receipt.get(key))
        if value:
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
    terminate_worker_lease_for_run: Callable[..., dict[str, Any] | None] | None = None,
    utc_now: Callable[[], str],
    read_json: Callable[[Path], dict[str, Any]],
    write_json: Callable[[Path, Mapping[str, Any]], None],
    append_runtime_event: Callable[..., None],
) -> dict[str, Any] | None:
    lifecycle = inspect_turn_lifecycle(quest_root=quest_root)
    _clear_stale_blocked_closeout_for_live_run(
        quest_root=quest_root,
        lifecycle=lifecycle,
        source=source,
        text=text,
        load_state=load_state,
        persist_state=persist_state,
    )
    stale_run_id = text(lifecycle.get("stale_active_run_id"))
    stale_reason = "worker_lease_not_live"
    logical_completion = inspect_logical_turn_completion(
        quest_root=quest_root,
        run_id=text(lifecycle.get("active_run_id")) or stale_run_id,
    )
    if logical_completion is not None and (
        stale_run_id is None or stale_run_id == logical_completion["run_id"]
    ):
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
        parked = _reconcile_latest_blocked_closeout_without_live_run(
            quest_root=quest_root,
            source=source,
            lifecycle=lifecycle,
            load_state=load_state,
            persist_state=persist_state,
            snapshot=snapshot,
        )
        if parked is not None:
            return parked
        completed = _reconcile_latest_completed_closeout_without_live_run(
            quest_root=quest_root,
            source=source,
            lifecycle=lifecycle,
            load_state=load_state,
            persist_state=persist_state,
            snapshot=snapshot,
            turn_receipt=turn_receipt,
            make_idempotency_key=make_idempotency_key,
            terminate_worker_leases=terminate_worker_leases,
            terminate_worker_lease_for_run=terminate_worker_lease_for_run,
            utc_now=utc_now,
            read_json=read_json,
            write_json=write_json,
            append_runtime_event=append_runtime_event,
        )
        if completed is not None:
            return completed
        return None
    worker_cleanup = _terminate_stuck_worker(
        quest_root=quest_root,
        source=source,
        stale_reason=stale_reason,
        stale_run_id=stale_run_id,
        terminate_worker_leases=terminate_worker_leases,
        terminate_worker_lease_for_run=terminate_worker_lease_for_run,
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
        logical_completion=logical_completion,
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


def _reconcile_latest_completed_closeout_without_live_run(
    *,
    quest_root: Path,
    source: str,
    lifecycle: Mapping[str, Any],
    load_state: Callable[..., dict[str, Any]],
    persist_state: Callable[..., dict[str, Any]],
    snapshot: Callable[..., dict[str, Any]],
    turn_receipt: Callable[..., dict[str, Any]],
    make_idempotency_key: Callable[..., str],
    terminate_worker_leases: Callable[..., dict[str, Any]],
    terminate_worker_lease_for_run: Callable[..., dict[str, Any] | None] | None,
    utc_now: Callable[[], str],
    read_json: Callable[[Path], dict[str, Any]],
    write_json: Callable[[Path, Mapping[str, Any]], None],
    append_runtime_event: Callable[..., None],
) -> dict[str, Any] | None:
    state = load_state(quest_root=quest_root)
    if str(state.get("status") or "").strip() not in {"active", "running"}:
        return None
    if state.get("worker_running") is True or state.get("worker_pending") is True:
        return None
    if str(state.get("active_run_id") or "").strip():
        return None
    logical_completion = _latest_completed_closeout(quest_root=quest_root)
    if logical_completion is None:
        return None
    stale_run_id = str(logical_completion["run_id"])
    if (
        str(state.get("last_completed_run_id") or "").strip() == stale_run_id
        and logical_completion.get("latest_receipt_terminal") is True
    ):
        return None
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
    stale_reason = "logical_turn_completed"
    worker_cleanup = _terminate_stuck_worker(
        quest_root=quest_root,
        source=source,
        stale_reason=stale_reason,
        stale_run_id=stale_run_id,
        terminate_worker_leases=terminate_worker_leases,
        terminate_worker_lease_for_run=terminate_worker_lease_for_run,
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
        logical_completion=logical_completion,
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
    result["logical_completion"] = logical_completion
    result["previous_lifecycle"] = dict(lifecycle)
    return result


def _latest_completed_closeout(*, quest_root: Path) -> dict[str, Any] | None:
    closeout_root = quest_root / "artifacts" / "runtime" / "turn_closeouts"
    if not closeout_root.is_dir():
        return None
    for path in sorted(closeout_root.glob("*.json"), key=lambda item: item.stat().st_mtime, reverse=True):
        logical_completion = inspect_logical_turn_completion(quest_root=quest_root, run_id=path.stem)
        if logical_completion is None:
            continue
        if logical_completion.get("reason") == "blocked_turn_closeout_waiting_for_owner":
            continue
        return logical_completion
    return None


def _reconcile_latest_blocked_closeout_without_live_run(
    *,
    quest_root: Path,
    source: str,
    lifecycle: Mapping[str, Any],
    load_state: Callable[..., dict[str, Any]],
    persist_state: Callable[..., dict[str, Any]],
    snapshot: Callable[..., dict[str, Any]],
) -> dict[str, Any] | None:
    state = load_state(quest_root=quest_root)
    if str(state.get("status") or "").strip() not in {"active", "running"}:
        return None
    if state.get("worker_running") is True or state.get("worker_pending") is True:
        return None
    if str(state.get("active_run_id") or "").strip():
        return None
    blocked_closeout = _latest_blocked_closeout(quest_root=quest_root)
    if blocked_closeout is None:
        return None
    latest_run_id = str(blocked_closeout["run_id"])
    latest_known = str(state.get("last_completed_run_id") or state.get("last_known_run_id") or "").strip()
    if latest_known and latest_known != latest_run_id:
        return None
    repaired = persist_state(
        quest_root=quest_root,
        updates={
            **_blocked_closeout_updates(
                run_id=latest_run_id,
                closeout=blocked_closeout,
            ),
            "active_run_id": None,
            "last_known_run_id": latest_run_id,
            "last_completed_run_id": latest_run_id,
            "worker_running": False,
            "worker_pending": False,
            "last_liveness_reconcile_reason": "blocked_turn_closeout_waiting_for_owner",
        },
        source=source,
        event_name="blocked_turn_closeout_reconciled",
    )
    return {
        "ok": True,
        "status": "parked",
        "active_run_id": None,
        "stale_active_run_id": latest_run_id,
        "stale_reason": "blocked_turn_closeout_waiting_for_owner",
        "worker_running": False,
        "worker_pending": False,
        "stop_requested": repaired.get("stop_requested") is True,
        "snapshot": snapshot(quest_root=quest_root, state=repaired),
        "blocked_turn_closeout": dict(blocked_closeout),
        "previous_lifecycle": dict(lifecycle),
    }


def _latest_blocked_closeout(*, quest_root: Path) -> dict[str, Any] | None:
    closeout_root = quest_root / "artifacts" / "runtime" / "turn_closeouts"
    if not closeout_root.is_dir():
        return None
    for path in sorted(closeout_root.glob("*.json"), key=lambda item: item.stat().st_mtime, reverse=True):
        payload = read_blocked_closeout_payload(path)
        if payload is not None:
            return payload
    return None


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
    runner_status = str(logical_completion.get("completion_runner_status") or "succeeded")
    target_status = str(logical_completion.get("target_status") or "active")
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
            "runner_status": runner_status,
            "normalized_status": target_status,
            "reconciled_from": dict(logical_completion),
        },
    )


def _terminate_stuck_worker(
    *,
    quest_root: Path,
    source: str,
    stale_reason: str,
    stale_run_id: str,
    terminate_worker_leases: Callable[..., dict[str, Any]],
    terminate_worker_lease_for_run: Callable[..., dict[str, Any] | None] | None,
    utc_now: Callable[[], str],
    read_json: Callable[[Path], dict[str, Any]],
    write_json: Callable[[Path, Mapping[str, Any]], None],
    append_runtime_event: Callable[..., None],
) -> dict[str, Any] | None:
    if stale_reason != "logical_turn_completed":
        return None
    if terminate_worker_lease_for_run is not None:
        return terminate_worker_lease_for_run(
            quest_root=quest_root,
            run_id=stale_run_id,
            source=source,
            reason=stale_reason,
            utc_now=utc_now,
            read_json=read_json,
            write_json=write_json,
            append_runtime_event=append_runtime_event,
        )
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
    logical_completion: Mapping[str, Any] | None,
    load_state: Callable[..., dict[str, Any]],
    persist_state: Callable[..., dict[str, Any]],
) -> dict[str, Any]:
    state = load_state(quest_root=quest_root)
    blocked_closeout = _blocked_closeout_state(
        stale_run_id=stale_run_id,
        stale_reason=stale_reason,
        state=state,
        logical_completion=logical_completion,
    )
    if blocked_closeout is not None:
        updates = blocked_closeout
    else:
        updates = {
            "status": "active",
            "continuation_policy": state.get("continuation_policy") or "auto",
        }
    last_completed_run_id = stale_run_id if stale_reason in {
        "logical_turn_completed",
        "blocked_turn_closeout_waiting_for_owner",
    } else state.get("last_completed_run_id")
    updates.update(
        {
            "active_run_id": None,
            "last_known_run_id": stale_run_id,
            "last_completed_run_id": last_completed_run_id,
            "worker_running": False,
            "worker_pending": False,
            "last_liveness_reconcile_reason": stale_reason,
            "last_worker_cleanup": worker_cleanup,
        }
    )
    return persist_state(
        quest_root=quest_root,
        updates=updates,
        source=source,
        event_name="stale_turn_reconciled",
    )


def _clear_stale_blocked_closeout_for_live_run(
    *,
    quest_root: Path,
    lifecycle: Mapping[str, Any],
    source: str,
    text: Callable[[object], str | None],
    load_state: Callable[..., dict[str, Any]],
    persist_state: Callable[..., dict[str, Any]],
) -> dict[str, Any] | None:
    active_run_id = text(lifecycle.get("active_run_id"))
    if active_run_id is None:
        return None
    if lifecycle.get("worker_running") is not True:
        return None
    state = load_state(quest_root=quest_root)
    blocked_closeout = state.get("blocked_turn_closeout")
    if not isinstance(blocked_closeout, Mapping):
        return None
    blocked_run_id = text(blocked_closeout.get("run_id"))
    if blocked_run_id is None or blocked_run_id == active_run_id:
        return None
    cleared_keys = [
        key
        for key in (
            "blocked_turn_closeout",
            "last_liveness_reconcile_reason",
        )
        if key in state
    ]
    if not cleared_keys:
        return None
    repaired = persist_state(
        quest_root=quest_root,
        updates={
            "status": "running",
            "active_run_id": active_run_id,
            "worker_running": True,
            "continuation_policy": "auto",
            "continuation_anchor": "live_run",
            "continuation_reason": "stale_blocked_turn_closeout_superseded_by_live_run",
            "last_stale_blocked_closeout_clear": {
                "active_run_id": active_run_id,
                "cleared_run_id": blocked_run_id,
                "cleared_keys": cleared_keys,
                "source": source,
            },
        },
        source=source,
        event_name="stale_blocked_turn_closeout_cleared",
        delete_keys=cleared_keys,
    )
    return {
        "cleared": True,
        "active_run_id": active_run_id,
        "cleared_run_id": blocked_run_id,
        "cleared_keys": cleared_keys,
        "state": repaired,
    }


def _blocked_closeout_state(
    *,
    stale_run_id: str,
    stale_reason: str,
    state: Mapping[str, Any],
    logical_completion: Mapping[str, Any] | None,
) -> dict[str, Any] | None:
    if stale_reason != "blocked_turn_closeout_waiting_for_owner":
        return None
    return {
        **_blocked_closeout_updates(
            run_id=stale_run_id,
            closeout=_blocked_closeout_payload(
                stale_run_id=stale_run_id,
                state=state,
                logical_completion=logical_completion,
            ),
        ),
    }


def _blocked_closeout_updates(*, run_id: str, closeout: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "status": "waiting_for_user",
        "continuation_policy": "wait_for_user_or_resume",
        "continuation_anchor": "turn_closeout",
        "continuation_reason": "blocked_turn_closeout_waiting_for_owner",
        "blocked_turn_closeout": {
            "run_id": run_id,
            "closeout_path": closeout.get("closeout_path"),
            "blocked_reason": closeout.get("blocked_reason"),
            "next_owner": closeout.get("next_owner"),
        },
    }


def _blocked_closeout_payload(
    *,
    stale_run_id: str,
    state: Mapping[str, Any],
    logical_completion: Mapping[str, Any] | None,
) -> dict[str, Any]:
    completion = state.get("last_runner_completion")
    if not isinstance(completion, Mapping):
        completion = {}
    logical = logical_completion if isinstance(logical_completion, Mapping) else {}
    return {
        "run_id": stale_run_id,
        "closeout_path": logical.get("closeout_path") or completion.get("closeout_path"),
        "blocked_reason": logical.get("blocked_reason") or completion.get("blocked_reason"),
        "next_owner": logical.get("next_owner") or completion.get("next_owner"),
    }


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
