from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from med_autoscience.runtime_transport import mas_runtime_core_delayed_turns as delayed_turns
from med_autoscience.runtime_transport import mas_runtime_core_turn_state as turn_state
from med_autoscience.runtime_transport import mas_runtime_core_turn_timers as turn_timers
from med_autoscience.runtime_transport.mas_runtime_core_turn_liveness import (
    initial_worker_lease_payload,
    lease_payload_live,
    lease_payload_status,
    reconcile_stale_liveness as reconcile_stale_liveness_impl,
    watchdog_projection,
)
from med_autoscience.runtime_transport.mas_runtime_core_turn_paths import delayed_turn_path, worker_lease_path
from med_autoscience.runtime_transport.mas_runtime_core_turn_policy import TERMINAL_STATUSES, WORKER_LEASE_TTL_SECONDS
from med_autoscience.runtime_transport.mas_runtime_core_turn_utils import parse_time, text
from med_autoscience.runtime_transport.mas_runtime_core_worker_leases import (
    terminate_orphan_worker_leases,
    terminate_worker_lease_for_run,
    terminate_worker_leases,
)


def worker_lease_live(*, quest_root: Path, run_id: str, pid_live_check: Callable[[int], bool]) -> bool:
    return lease_payload_live(
        lease=turn_state.read_json(worker_lease_path(quest_root=quest_root, run_id=run_id)),
        run_id=run_id,
        now=turn_state.now,
        parse_time=parse_time,
        pid_live_check=pid_live_check,
        ttl_seconds=WORKER_LEASE_TTL_SECONDS,
    )


def prune_orphan_worker_leases_before_new_turn(*, quest_root: Path, source: str) -> dict[str, Any] | None:
    cleanup = terminate_orphan_worker_leases(
        quest_root=quest_root,
        active_run_id=None,
        source=source,
        reason="orphan_worker_before_new_turn",
        utc_now=turn_state.utc_now,
        read_json=turn_state.read_json,
        write_json=turn_state.write_json,
        append_runtime_event=turn_state.append_runtime_event,
    )
    if cleanup is None:
        return None
    turn_state.persist_state(
        quest_root=quest_root,
        updates={"last_orphan_worker_cleanup": cleanup},
        source=source,
        event_name="orphan_worker_before_new_turn_pruned",
    )
    return cleanup


def inspect_turn_lifecycle(
    *,
    quest_root: Path,
    schedule_turn: Callable[..., dict[str, Any]],
    pid_live_check: Callable[[int], bool],
) -> dict[str, Any]:
    drained_delayed_turn = drain_due_delayed_turn(
        quest_root=quest_root,
        source="mas_runtime_core.inspect_turn_lifecycle",
        schedule_turn=schedule_turn,
    )
    state = turn_state.load_state(quest_root=quest_root)
    active_run_id = text(state.get("active_run_id"))
    lease = turn_state.read_json(worker_lease_path(quest_root=quest_root, run_id=active_run_id)) if active_run_id else {}
    lease_status = lease_payload_status(
        lease=lease,
        run_id=active_run_id,
        now=turn_state.now,
        parse_time=parse_time,
        pid_live_check=pid_live_check,
        ttl_seconds=WORKER_LEASE_TTL_SECONDS,
    )
    lease_live = bool(lease_status.get("live"))
    payload = {
        "ok": True,
        "status": "live" if state.get("worker_running") is True and lease_live else "none",
        "active_run_id": active_run_id if lease_live else None,
        "stale_active_run_id": active_run_id if state.get("worker_running") is True and active_run_id and not lease_live else None,
        "worker_running": state.get("worker_running") is True and lease_live,
        "worker_pending": state.get("worker_pending") is True,
        "stop_requested": state.get("stop_requested") is True,
        "lease": lease if lease else None,
        "worker_watchdog": watchdog_projection(lease=lease, lease_status=lease_status),
        "snapshot": turn_state.snapshot(quest_root=quest_root, state=state),
    }
    if drained_delayed_turn is not None:
        payload["drained_delayed_turn"] = drained_delayed_turn
    return payload


def drain_due_delayed_turn(
    *,
    quest_root: Path,
    source: str,
    schedule_turn: Callable[..., dict[str, Any]],
) -> dict[str, Any] | None:
    delayed = turn_state.read_json(delayed_turn_path(quest_root))
    if not delayed:
        return None
    state = turn_state.load_state(quest_root=quest_root)
    if text(state.get("status")) in TERMINAL_STATUSES:
        delayed_turns.cancel_delayed_turn(
            quest_root=quest_root,
            source=source,
            reason="terminal_state",
            delayed_turn_path=delayed_turn_path,
            read_json=turn_state.read_json,
            text=text,
            utc_now=turn_state.utc_now,
            append_runtime_event=turn_state.append_runtime_event,
        )
        return None
    scheduled_at = parse_time(text(delayed.get("scheduled_at")))
    delay_seconds = float(delayed.get("delay_seconds") or 0)
    if scheduled_at is None or (turn_state.now() - scheduled_at).total_seconds() < delay_seconds:
        return None
    if state.get("worker_running") is True and text(state.get("active_run_id")):
        return None
    try:
        delayed_turn_path(quest_root).unlink()
    except FileNotFoundError:
        pass
    result = schedule_turn(
        runtime_root=quest_root.parent.parent,
        quest_root=quest_root,
        quest_id=text(delayed.get("quest_id")) or quest_root.name,
        reason=text(delayed.get("reason")) or "auto_continue",
        source=text(delayed.get("source")) or source,
    )
    return {
        "quest_id": text(delayed.get("quest_id")) or quest_root.name,
        "reason": text(delayed.get("reason")) or "auto_continue",
        "source": text(delayed.get("source")) or source,
        "delay_seconds": delay_seconds,
        "scheduled_at": text(delayed.get("scheduled_at")),
        "started": bool(result.get("started")),
        "active_run_id": text(result.get("active_run_id")),
    }


def arm_delayed_turn_timer(
    *,
    quest_root: Path,
    delay_seconds: float,
    source: str,
    schedule_turn: Callable[..., dict[str, Any]],
) -> None:
    def _drain_due_delayed_turn(*, quest_root: Path, source: str) -> dict[str, Any] | None:
        return drain_due_delayed_turn(quest_root=quest_root, source=source, schedule_turn=schedule_turn)

    turn_timers.arm_delayed_turn_timer(
        quest_root=quest_root,
        delay_seconds=delay_seconds,
        source=source,
        drain_due_delayed_turn=_drain_due_delayed_turn,
    )


def reconcile_stale_liveness(
    *,
    quest_root: Path,
    source: str,
    inspect_turn_lifecycle: Callable[..., dict[str, Any]],
    turn_receipt: Callable[..., dict[str, Any]],
    make_idempotency_key: Callable[..., str],
) -> dict[str, Any] | None:
    return reconcile_stale_liveness_impl(
        quest_root=quest_root,
        source=source,
        inspect_turn_lifecycle=inspect_turn_lifecycle,
        text=text,
        load_state=turn_state.load_state,
        persist_state=turn_state.persist_state,
        snapshot=turn_state.snapshot,
        turn_receipt=turn_receipt,
        make_idempotency_key=make_idempotency_key,
        terminate_worker_leases=terminate_worker_leases,
        terminate_worker_lease_for_run=terminate_worker_lease_for_run,
        utc_now=turn_state.utc_now,
        read_json=turn_state.read_json,
        write_json=turn_state.write_json,
        append_runtime_event=turn_state.append_runtime_event,
    )


__all__ = [
    "arm_delayed_turn_timer",
    "drain_due_delayed_turn",
    "initial_worker_lease_payload",
    "inspect_turn_lifecycle",
    "prune_orphan_worker_leases_before_new_turn",
    "reconcile_stale_liveness",
    "worker_lease_live",
]
