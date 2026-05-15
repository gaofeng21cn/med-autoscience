from __future__ import annotations

from collections.abc import Callable, Mapping
from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any

from med_autoscience.runtime_transport import mas_runtime_core_turn_monitor as turn_monitor
from med_autoscience.runtime_transport import mas_runtime_core_turn_blocks as turn_blocks
from med_autoscience.runtime_transport.mas_runtime_core_turn_completion import (
    BLOCKED_CLOSEOUT_RUNNER_STATUS,
    INCOMPLETE_RUNNER_STATUS,
    blocked_closeout_wait_state,
    inspect_runner_completion,
    next_retry_state,
    stale_runner_completion_result,
    status_after_runner,
)
from med_autoscience.runtime_transport.mas_runtime_core_turn_runner import (
    CodexExecTurnRunner,
    MasTurnRunner,
    pop_running_process,
)
from med_autoscience.runtime_transport.mas_runtime_core_turn_receipts import (
    launch_fields,
    record_post_turn_storage_maintenance_hook,
    schedule_result,
    turn_receipt_payload,
)
from med_autoscience.runtime_transport.mas_runtime_core_turn_liveness import (
    initial_worker_lease_payload,
    lease_payload_live as _lease_payload_live,
    lease_payload_status as _lease_payload_status,
    reconcile_stale_liveness as reconcile_stale_liveness_impl,
    watchdog_projection as _watchdog_projection,
)
from med_autoscience.runtime_transport import mas_runtime_core_turn_timers as turn_timers
from med_autoscience.runtime_transport import mas_runtime_core_delayed_turns as delayed_turns
from med_autoscience.runtime_transport.mas_runtime_core_turn_utils import (
    idempotency_key as make_idempotency_key,
    message_id as make_message_id,
    parse_time,
    pid_live,
    runner_unavailable,
    text,
)
from med_autoscience.runtime_transport.mas_runtime_core_worker_leases import (
    terminate_orphan_worker_leases,
    terminate_worker_lease_for_run,
    terminate_worker_leases,
)
from med_autoscience.runtime_transport.mas_runtime_core_turn_policy import (
    AUTO_CONTINUE_DELAY_SECONDS,
    BACKEND_ID,
    ENGINE_ID,
    MAX_RETRY_ATTEMPTS,
    RETRY_BACKOFF_BASE_SECONDS,
    SAME_FINGERPRINT_AUTO_TURN_THRESHOLD,
    TERMINAL_STATUSES,
    WORKER_LEASE_TTL_SECONDS,
)


_TURN_RUNNER: MasTurnRunner = CodexExecTurnRunner()
_NOW: Callable[[], datetime] = lambda: datetime.now(UTC)
def set_turn_runner_for_tests(runner: MasTurnRunner) -> None:
    global _TURN_RUNNER
    _TURN_RUNNER = runner


def reset_turn_runner_for_tests() -> None:
    global _TURN_RUNNER
    _TURN_RUNNER = CodexExecTurnRunner()


def set_clock_for_tests(clock: Callable[[], datetime]) -> None:
    global _NOW
    _NOW = clock


def reset_clock_for_tests() -> None:
    global _NOW
    _NOW = lambda: datetime.now(UTC)


def set_delayed_timers_enabled_for_tests(enabled: bool) -> None:
    turn_timers.set_delayed_timers_enabled_for_tests(enabled)


def utc_now() -> str:
    return _NOW().astimezone(UTC).replace(microsecond=0).isoformat()


def run_id(*, quest_id: str) -> str:
    slug = _NOW().astimezone(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    safe_quest_id = "".join(ch if ch.isalnum() or ch in "-_." else "-" for ch in quest_id).strip("-") or "quest"
    return f"mas-run-{safe_quest_id}-{slug}"


def state_path(quest_root: Path) -> Path:
    return quest_root / ".ds" / "runtime_state.json"


def event_log_path(quest_root: Path) -> Path:
    return quest_root / "artifacts" / "runtime" / "mas_runtime_events.jsonl"


def queue_path(quest_root: Path) -> Path:
    return quest_root / "artifacts" / "runtime" / "user_message_queue.json"


def turn_receipts_path(quest_root: Path) -> Path:
    return quest_root / "artifacts" / "runtime" / "turn_receipts.jsonl"


def delayed_turn_path(quest_root: Path) -> Path:
    return quest_root / "artifacts" / "runtime" / "delayed_turns.json"


def _run_root(*, quest_root: Path, run_id: str) -> Path:
    return quest_root / ".ds" / "runs" / run_id


def worker_lease_path(*, quest_root: Path, run_id: str) -> Path:
    return _run_root(quest_root=quest_root, run_id=run_id) / "worker_lease.json"


def read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(payload), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def append_jsonl(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(dict(payload), ensure_ascii=False, sort_keys=True) + "\n")


def load_state(*, quest_root: Path) -> dict[str, Any]:
    state = read_json(state_path(quest_root))
    state.setdefault("quest_id", quest_root.name)
    state.setdefault("runtime_backend_id", BACKEND_ID)
    state.setdefault("runtime_engine_id", ENGINE_ID)
    state.setdefault("external_mds_required", False)
    state.setdefault("continuation_policy", "auto")
    state["pending_user_message_count"] = int(state.get("pending_user_message_count") or 0)
    return state


def persist_state(
    *,
    quest_root: Path,
    updates: Mapping[str, Any],
    source: str,
    event_name: str,
    delete_keys: list[str] | tuple[str, ...] | None = None,
) -> dict[str, Any]:
    now = utc_now()
    previous = load_state(quest_root=quest_root)
    for key in delete_keys or ():
        previous.pop(key, None)
    payload = {
        **previous,
        **dict(updates),
        "quest_id": quest_root.name,
        "runtime_backend_id": BACKEND_ID,
        "runtime_engine_id": ENGINE_ID,
        "external_mds_required": False,
        "source": source,
        "updated_at": now,
    }
    payload.setdefault("continuation_policy", "auto")
    payload["pending_user_message_count"] = int(payload.get("pending_user_message_count") or 0)
    write_json(state_path(quest_root), payload)
    append_runtime_event(quest_root=quest_root, event={"event": event_name, "source": source, "recorded_at": now, "snapshot": payload})
    return payload


def append_runtime_event(*, quest_root: Path, event: Mapping[str, Any]) -> None:
    append_jsonl(event_log_path(quest_root), event)


def load_message_queue(*, quest_root: Path) -> dict[str, Any]:
    payload = read_json(queue_path(quest_root))
    pending = payload.get("pending") if isinstance(payload.get("pending"), list) else []
    completed = payload.get("completed") if isinstance(payload.get("completed"), list) else []
    return {"schema_version": 1, "pending": list(pending), "completed": list(completed)}


def write_message_queue(*, quest_root: Path, queue: Mapping[str, Any]) -> None:
    write_json(queue_path(quest_root), queue)


def submit_user_message(
    *,
    runtime_root: Path,
    quest_root: Path,
    quest_id: str,
    text: str,
    source: str,
    reply_to_interaction_id: str | None = None,
    decision_response: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    now = utc_now()
    queue = load_message_queue(quest_root=quest_root)
    message_id = make_message_id(quest_id=quest_id, text=text, source=source, recorded_at=now)
    message = {
        "message_id": message_id,
        "content": text,
        "source": source,
        "reply_to_interaction_id": reply_to_interaction_id,
        "decision_response": dict(decision_response) if isinstance(decision_response, Mapping) else None,
        "recorded_at": now,
        "status": "pending",
    }
    queue["pending"].append(message)
    write_message_queue(quest_root=quest_root, queue=queue)
    persist_state(
        quest_root=quest_root,
        updates={"pending_user_message_count": len(queue["pending"])},
        source=source,
        event_name="user_message_queued",
    )
    scheduled = schedule_turn(
        runtime_root=runtime_root,
        quest_root=quest_root,
        quest_id=quest_id,
        reason="user_message",
        source=source,
    )
    return {
        "ok": True,
        "status": "scheduled",
        "source": BACKEND_ID,
        "message": message,
        "turn_reason": "user_message",
        **_launch_fields(scheduled),
        "snapshot": scheduled.get("snapshot"),
    }


def schedule_turn(
    *,
    runtime_root: Path,
    quest_root: Path,
    quest_id: str,
    reason: str,
    source: str,
    delay_seconds: float | None = None,
    terminal_attach_capable: bool = False,
) -> dict[str, Any]:
    state = load_state(quest_root=quest_root)
    runtime_status = text(state.get("status"))
    if runtime_status in TERMINAL_STATUSES:
        return turn_blocks.terminal_runtime_schedule_block(
            quest_root=quest_root,
            quest_id=quest_id,
            reason=reason,
            state=state,
            runtime_status=runtime_status,
            backend_id=BACKEND_ID,
            text=text,
            snapshot=snapshot,
        )
    active_run_id = text(state.get("active_run_id"))
    if state.get("worker_running") is True and active_run_id:
        if not _worker_lease_live(quest_root=quest_root, run_id=active_run_id):
            reconcile_stale_liveness(quest_root=quest_root, source=f"{source}:schedule_turn")
            state = load_state(quest_root=quest_root)
            active_run_id = text(state.get("active_run_id"))
        else:
            updated = persist_state(
                quest_root=quest_root,
                updates={
                    "status": state.get("status") or "running",
                    "active_run_id": active_run_id,
                    "worker_running": True,
                    "worker_pending": True,
                    "pending_turn_reason": reason,
                    "pending_turn_source": source,
                },
                source=source,
                event_name="turn_queued_worker_active",
            )
            receipt = _turn_receipt(
                quest_root=quest_root,
                run_id=active_run_id,
                reason=reason,
                source=source,
                status="queued",
                started=False,
                queued=True,
                idempotency_key=make_idempotency_key(quest_id=quest_id, reason=reason, source=source, active_run_id=active_run_id),
            )
            return schedule_result(
                quest_root=quest_root,
                status="queued",
                backend_id=BACKEND_ID,
                active_run_id=active_run_id,
                started=False,
                queued=True,
                scheduled=True,
                reason=reason,
                receipt=receipt,
                snapshot_payload=snapshot(quest_root=quest_root, state=updated),
            )
    if active_run_id is None:
        _prune_orphan_worker_leases_before_new_turn(quest_root=quest_root, source=source)
    if delay_seconds is not None and delay_seconds > 0:
        payload = {
            "schema_version": 1,
            "quest_id": quest_id,
            "reason": reason,
            "source": source,
            "delay_seconds": delay_seconds,
            "scheduled_at": utc_now(),
            "idempotency_key": make_idempotency_key(quest_id=quest_id, reason=reason, source=source, active_run_id=None),
        }
        write_json(delayed_turn_path(quest_root), payload)
        _arm_delayed_turn_timer(quest_root=quest_root, delay_seconds=delay_seconds, source=source)
        updated = persist_state(
            quest_root=quest_root,
            updates={
                "status": state.get("status") or "active",
                "active_run_id": None,
                "worker_running": False,
                "worker_pending": True,
                "pending_turn_reason": reason,
                "pending_turn_source": source,
                "pending_turn_delay_seconds": delay_seconds,
            },
            source=source,
            event_name="turn_scheduled_delayed",
        )
        return {
            "ok": True,
            "status": "scheduled",
            "source": BACKEND_ID,
            "quest_id": quest_id,
            "reason": reason,
            "scheduled": True,
            "started": False,
            "queued": False,
            "delay_seconds": delay_seconds,
            "idempotency_key": payload["idempotency_key"],
            "snapshot": snapshot(quest_root=quest_root, state=updated),
        }
    return start_turn(
        runtime_root=runtime_root, quest_root=quest_root, quest_id=quest_id, reason=reason, source=source,
        terminal_attach_capable=terminal_attach_capable,
    )


def _prune_orphan_worker_leases_before_new_turn(*, quest_root: Path, source: str) -> dict[str, Any] | None:
    cleanup = terminate_orphan_worker_leases(
        quest_root=quest_root,
        active_run_id=None,
        source=source,
        reason="orphan_worker_before_new_turn",
        utc_now=utc_now,
        read_json=read_json,
        write_json=write_json,
        append_runtime_event=append_runtime_event,
    )
    if cleanup is None:
        return None
    persist_state(
        quest_root=quest_root,
        updates={"last_orphan_worker_cleanup": cleanup},
        source=source,
        event_name="orphan_worker_before_new_turn_pruned",
    )
    return cleanup


def start_turn(
    *,
    runtime_root: Path,
    quest_root: Path,
    quest_id: str,
    reason: str,
    source: str,
    terminal_attach_capable: bool = False,
) -> dict[str, Any]:
    state = load_state(quest_root=quest_root)
    runtime_status = text(state.get("status"))
    if runtime_status in TERMINAL_STATUSES:
        return turn_blocks.terminal_runtime_schedule_block(
            quest_root=quest_root,
            quest_id=quest_id,
            reason=reason,
            state=state,
            runtime_status=runtime_status,
            backend_id=BACKEND_ID,
            text=text,
            snapshot=snapshot,
        )
    new_run_id = run_id(quest_id=quest_id)
    claimed_messages = claim_pending_user_messages(quest_root=quest_root, run_id=new_run_id)
    now = utc_now()
    try:
        runner_receipt = _TURN_RUNNER.start_turn(
            runtime_root=runtime_root,
            quest_root=quest_root,
            quest_id=quest_id,
            run_id=new_run_id,
            reason=reason,
            claimed_user_messages=claimed_messages,
            terminal_attach_capable=terminal_attach_capable,
        )
    except Exception as exc:  # pragma: no cover - exercised through fake runner tests when needed.
        runner_receipt = {
            "runner_kind": "mas_turn_runner",
            "available": False,
            "fail_closed": True,
            "error": f"{type(exc).__name__}: {exc}",
        }
    if runner_unavailable(runner_receipt):
        restore_claimed_user_messages(quest_root=quest_root, run_id=new_run_id)
        queue = load_message_queue(quest_root=quest_root)
        updated = persist_state(
            quest_root=quest_root,
            updates={
                "status": state.get("status") or "active",
                "active_run_id": None,
                "worker_running": False,
                "worker_pending": False,
                "pending_turn_reason": reason,
                "pending_turn_source": source,
                "pending_user_message_count": len(queue["pending"]),
                "last_runner_start_error": runner_receipt.get("error"),
            },
            source=source,
            event_name="turn_runner_unavailable",
        )
        receipt = _turn_receipt(
            quest_root=quest_root,
            run_id=new_run_id,
            reason=reason,
            source=source,
            status="runner_unavailable",
            started=False,
            queued=False,
            idempotency_key=make_idempotency_key(quest_id=quest_id, reason=reason, source=source, active_run_id=new_run_id),
            extra={
                "claimed_user_message_count": len(claimed_messages),
                "runner_receipt": runner_receipt,
            },
        )
        return {
            "ok": False,
            "status": "runner_unavailable",
            "source": BACKEND_ID,
            "quest_id": quest_id,
            "active_run_id": None,
            "scheduled": False,
            "started": False,
            "queued": False,
            "reason": reason,
            "turn_reason": reason,
            "idempotency_key": receipt.get("idempotency_key"),
            "turn_receipt": receipt,
            "snapshot": snapshot(quest_root=quest_root, state=updated),
        }
    lease = initial_worker_lease_payload(
        quest_id=quest_id,
        run_id=new_run_id,
        reason=reason,
        source=source,
        started_at=now,
        runner_receipt=runner_receipt,
        text=text,
    )
    write_json(worker_lease_path(quest_root=quest_root, run_id=new_run_id), lease)
    pending_count = len(load_message_queue(quest_root=quest_root)["pending"])
    updated = persist_state(
        quest_root=quest_root,
        updates={
            "status": "running",
            "active_run_id": new_run_id,
            "worker_running": True,
            "worker_pending": False,
            "stop_requested": False,
            "pending_turn_reason": None,
            "pending_turn_source": None,
            "turn_reason": reason,
            "pending_user_message_count": pending_count,
            "continuation_policy": state.get("continuation_policy") or "auto",
            "last_turn_started_at": now,
        },
        source=source,
        event_name="turn_started",
    )
    receipt = _turn_receipt(
        quest_root=quest_root,
        run_id=new_run_id,
        reason=reason,
        source=source,
        status="started",
        started=True,
        queued=False,
        idempotency_key=make_idempotency_key(quest_id=quest_id, reason=reason, source=source, active_run_id=new_run_id),
        extra={
            "claimed_user_message_count": len(claimed_messages),
            "claimed_user_messages": list(claimed_messages),
            "runner_receipt": runner_receipt,
        },
    )
    _arm_runner_monitor(runtime_root=runtime_root, quest_root=quest_root, quest_id=quest_id, run_id=new_run_id, source=source)
    result = schedule_result(
        quest_root=quest_root, status="running", backend_id=BACKEND_ID, active_run_id=new_run_id,
        started=True, queued=False, scheduled=True, reason=reason, receipt=receipt,
        snapshot_payload=snapshot(quest_root=quest_root, state=updated),
    )
    if terminal_attach_capable:
        result["terminal_attach_capable"] = True
        result["terminal_bridge_status"] = runner_receipt.get("terminal_bridge_status")
    return result


def claim_pending_user_messages(*, quest_root: Path, run_id: str) -> tuple[dict[str, Any], ...]:
    queue = load_message_queue(quest_root=quest_root)
    pending = [item for item in queue["pending"] if isinstance(item, dict)]
    if not pending:
        write_message_queue(quest_root=quest_root, queue=queue)
        return ()
    claimed: list[dict[str, Any]] = []
    now = utc_now()
    for item in pending:
        claimed_item = {**item, "status": "completed", "claimed_by_run_id": run_id, "claimed_at": now}
        claimed.append(claimed_item)
    queue["pending"] = []
    queue["completed"].extend(claimed)
    write_message_queue(quest_root=quest_root, queue=queue)
    return tuple(claimed)


def restore_claimed_user_messages(*, quest_root: Path, run_id: str) -> None:
    queue = load_message_queue(quest_root=quest_root)
    restored: list[dict[str, Any]] = []
    remaining_completed: list[dict[str, Any]] = []
    for item in queue["completed"]:
        if isinstance(item, dict) and item.get("claimed_by_run_id") == run_id:
            restored_item = dict(item)
            restored_item["status"] = "pending"
            restored_item.pop("claimed_by_run_id", None)
            restored_item.pop("claimed_at", None)
            restored.append(restored_item)
        else:
            remaining_completed.append(item)
    if restored:
        queue["pending"] = restored + [item for item in queue["pending"] if isinstance(item, dict)]
        queue["completed"] = remaining_completed
        write_message_queue(quest_root=quest_root, queue=queue)


def complete_turn_and_normalize(
    *,
    runtime_root: Path,
    quest_root: Path,
    quest_id: str,
    run_id: str,
    runner_status: str,
    source: str,
    blocking_decision_request: Mapping[str, Any] | None = None,
    same_fingerprint: bool = False,
) -> dict[str, Any]:
    previous = load_state(quest_root=quest_root)
    stale_completion = _stale_completion_result(
        previous=previous,
        quest_root=quest_root,
        quest_id=quest_id,
        run_id=run_id,
        runner_status=runner_status,
        source=source,
    )
    if stale_completion is not None:
        return stale_completion
    completion = inspect_runner_completion(
        quest_root=quest_root,
        run_id=run_id,
        runner_status=text(runner_status) or "succeeded",
    )
    normalized_runner_status = text(completion.get("normalized_runner_status")) or text(runner_status) or "succeeded"
    target_status = status_after_runner(normalized_runner_status)
    retry_state = next_retry_state(
        previous=previous,
        runner_status=normalized_runner_status,
        max_attempts=MAX_RETRY_ATTEMPTS,
        backoff_base_seconds=RETRY_BACKOFF_BASE_SECONDS,
    )
    if retry_state is not None:
        target_status = "active" if retry_state["attempt"] < retry_state["max_attempts"] else "failed"
    same_fingerprint_count = (
        int(previous.get("same_fingerprint_auto_turn_count") or 0) + 1 if same_fingerprint else 0
    )
    updates: dict[str, Any] = {
        "status": target_status,
        "active_run_id": None,
        "worker_running": False,
        "worker_pending": False,
        "retry_state": retry_state if retry_state is not None and target_status == "active" else None,
        "last_completed_run_id": (
            previous.get("last_completed_run_id") if normalized_runner_status == INCOMPLETE_RUNNER_STATUS else run_id
        ),
        "last_incomplete_run_id": run_id if normalized_runner_status == INCOMPLETE_RUNNER_STATUS else None,
        "last_runner_status": normalized_runner_status,
        "last_runner_completion": completion,
        "last_turn_finished_at": utc_now(),
    }
    updates["same_fingerprint_auto_turn_count"] = same_fingerprint_count
    if same_fingerprint_count >= SAME_FINGERPRINT_AUTO_TURN_THRESHOLD:
        updates["control_intent_lifecycle"] = {
            "state": "await_artifact_delta_or_gate_replay",
            "block_reason": "same_fingerprint_no_artifact_delta",
            "same_fingerprint_auto_turn_count": same_fingerprint_count,
        }
    if target_status == "waiting_for_user" and isinstance(blocking_decision_request, Mapping):
        updates["waiting_interaction_id"] = text(blocking_decision_request.get("interaction_id"))
        updates["blocking_decision_request"] = dict(blocking_decision_request)
    else:
        updates["continuation_policy"] = previous.get("continuation_policy") or "auto"
    if normalized_runner_status == BLOCKED_CLOSEOUT_RUNNER_STATUS:
        updates.update(blocked_closeout_wait_state(completion=completion, run_id=run_id))
    queue = load_message_queue(quest_root=quest_root)
    updates["pending_user_message_count"] = len(queue["pending"])
    updated = persist_state(quest_root=quest_root, updates=updates, source=source, event_name="turn_finished")
    _turn_receipt(
        quest_root=quest_root,
        run_id=run_id,
        reason=str(previous.get("turn_reason") or "unknown"),
        source=source,
        status=INCOMPLETE_RUNNER_STATUS if normalized_runner_status == INCOMPLETE_RUNNER_STATUS else "finished",
        started=False,
        queued=False,
        idempotency_key=make_idempotency_key(quest_id=quest_id, reason="complete", source=source, active_run_id=run_id),
        extra={
            "runner_status": normalized_runner_status,
            "raw_runner_status": text(runner_status) or "succeeded",
            "runner_completion": completion,
            "normalized_status": target_status,
        },
    )
    _record_post_turn_storage_maintenance_hook(quest_root=quest_root, quest_id=quest_id, run_id=run_id, source=source)
    try:
        next_turn = _next_turn_after_normalization(
            runtime_root=runtime_root,
            quest_root=quest_root,
            quest_id=quest_id,
            state=updated,
            source=source,
        )
    except Exception as exc:
        repaired = persist_state(
            quest_root=quest_root,
            updates={
                "status": "active",
                "active_run_id": None,
                "worker_running": False,
                "worker_pending": False,
                "normalization_error": f"{type(exc).__name__}: {exc}",
            },
            source=source,
            event_name="turn_normalization_failed",
        )
        _turn_receipt(
            quest_root=quest_root,
            run_id=run_id,
            reason=str(previous.get("turn_reason") or "unknown"),
            source=source,
            status="normalization_failed",
            started=False,
            queued=False,
            idempotency_key=make_idempotency_key(
                quest_id=quest_id,
                reason="normalization_failed",
                source=source,
                active_run_id=run_id,
            ),
            extra={"error": f"{type(exc).__name__}: {exc}"},
        )
        return {
            "ok": False,
            "status": "normalization_failed",
            "source": BACKEND_ID,
            "quest_id": quest_id,
            "run_id": run_id,
            "snapshot": snapshot(quest_root=quest_root, state=repaired),
            "next_turn": None,
            "error": f"{type(exc).__name__}: {exc}",
        }
    final_state = load_state(quest_root=quest_root)
    return {
        "ok": True,
        "status": final_state.get("status") or target_status,
        "source": BACKEND_ID,
        "quest_id": quest_id,
        "run_id": run_id,
        "snapshot": snapshot(quest_root=quest_root, state=final_state),
        "next_turn": next_turn,
    }


def inspect_turn_lifecycle(*, quest_root: Path) -> dict[str, Any]:
    drained_delayed_turn = drain_due_delayed_turn(quest_root=quest_root, source="mas_runtime_core.inspect_turn_lifecycle")
    state = load_state(quest_root=quest_root)
    active_run_id = text(state.get("active_run_id"))
    lease = read_json(worker_lease_path(quest_root=quest_root, run_id=active_run_id)) if active_run_id else {}
    lease_status = _lease_payload_status(
        lease=lease,
        run_id=active_run_id,
        now=_NOW,
        parse_time=parse_time,
        pid_live_check=pid_live,
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
        "worker_watchdog": _watchdog_projection(lease=lease, lease_status=lease_status),
        "snapshot": snapshot(quest_root=quest_root, state=state),
    }
    if drained_delayed_turn is not None:
        payload["drained_delayed_turn"] = drained_delayed_turn
    return payload


def drain_due_delayed_turn(*, quest_root: Path, source: str) -> dict[str, Any] | None:
    delayed = read_json(delayed_turn_path(quest_root))
    if not delayed:
        return None
    state = load_state(quest_root=quest_root)
    if text(state.get("status")) in TERMINAL_STATUSES:
        delayed_turns.cancel_delayed_turn(
            quest_root=quest_root, source=source, reason="terminal_state", delayed_turn_path=delayed_turn_path,
            read_json=read_json, text=text, utc_now=utc_now, append_runtime_event=append_runtime_event,
        )
        return None
    scheduled_at = parse_time(text(delayed.get("scheduled_at")))
    delay_seconds = float(delayed.get("delay_seconds") or 0)
    if scheduled_at is None or (_NOW().astimezone(UTC) - scheduled_at).total_seconds() < delay_seconds:
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


def _arm_delayed_turn_timer(*, quest_root: Path, delay_seconds: float, source: str) -> None:
    turn_timers.arm_delayed_turn_timer(
        quest_root=quest_root,
        delay_seconds=delay_seconds,
        source=source,
        drain_due_delayed_turn=drain_due_delayed_turn,
    )


def _arm_runner_monitor(*, runtime_root: Path, quest_root: Path, quest_id: str, run_id: str, source: str) -> None:
    turn_monitor.arm_runner_monitor(
        runtime_root=runtime_root,
        quest_root=quest_root,
        quest_id=quest_id,
        run_id=run_id,
        source=source,
        process=pop_running_process(quest_root=quest_root, run_id=run_id),
        load_state=load_state,
        text=text,
        append_runtime_event=append_runtime_event,
        write_json=write_json,
        run_root=_run_root,
        utc_now=utc_now,
        complete_turn_and_normalize=complete_turn_and_normalize,
        persist_state=persist_state,
    )


def reconcile_stale_liveness(*, quest_root: Path, source: str) -> dict[str, Any] | None:
    return reconcile_stale_liveness_impl(
        quest_root=quest_root,
        source=source,
        inspect_turn_lifecycle=inspect_turn_lifecycle,
        text=text,
        load_state=load_state,
        persist_state=persist_state,
        snapshot=snapshot,
        turn_receipt=_turn_receipt,
        make_idempotency_key=make_idempotency_key,
        terminate_worker_leases=terminate_worker_leases,
        terminate_worker_lease_for_run=terminate_worker_lease_for_run,
        utc_now=utc_now,
        read_json=read_json,
        write_json=write_json,
        append_runtime_event=append_runtime_event,
    )


def snapshot(*, quest_root: Path, state: Mapping[str, Any] | None = None) -> dict[str, Any]:
    runtime_state = dict(state or load_state(quest_root=quest_root))
    active_run_id = text(runtime_state.get("active_run_id"))
    return {
        "quest_id": str(runtime_state.get("quest_id") or quest_root.name),
        "status": text(runtime_state.get("status")),
        "active_run_id": active_run_id,
        "runtime_backend_id": str(runtime_state.get("runtime_backend_id") or BACKEND_ID),
        "runtime_engine_id": str(runtime_state.get("runtime_engine_id") or ENGINE_ID),
        "worker_running": runtime_state.get("worker_running") if isinstance(runtime_state.get("worker_running"), bool) else None,
        "worker_pending": runtime_state.get("worker_pending") if isinstance(runtime_state.get("worker_pending"), bool) else None,
        "stop_requested": runtime_state.get("stop_requested") if isinstance(runtime_state.get("stop_requested"), bool) else None,
        "pending_user_message_count": int(runtime_state.get("pending_user_message_count") or 0),
        "continuation_policy": text(runtime_state.get("continuation_policy")) or "auto",
        "updated_at": text(runtime_state.get("updated_at")),
    }


def _next_turn_after_normalization(
    *,
    runtime_root: Path,
    quest_root: Path,
    quest_id: str,
    state: Mapping[str, Any],
    source: str,
) -> dict[str, Any] | None:
    status = text(state.get("status")) or "active"
    if status in TERMINAL_STATUSES:
        return None
    if status == "waiting_for_user":
        return None
    queue = load_message_queue(quest_root=quest_root)
    if queue["pending"]:
        return schedule_turn(
            runtime_root=runtime_root,
            quest_root=quest_root,
            quest_id=quest_id,
            reason="queued_user_messages",
            source=source,
        )
    pending_reason = text(state.get("pending_turn_reason"))
    if pending_reason and pending_reason != "auto_continue":
        return schedule_turn(
            runtime_root=runtime_root,
            quest_root=quest_root,
            quest_id=quest_id,
            reason=pending_reason,
            source=text(state.get("pending_turn_source")) or source,
        )
    retry_state = state.get("retry_state") if isinstance(state.get("retry_state"), Mapping) else None
    if retry_state and int(retry_state.get("attempt") or 0) < int(retry_state.get("max_attempts") or 0):
        return schedule_turn(
            runtime_root=runtime_root,
            quest_root=quest_root,
            quest_id=quest_id,
            reason="retry_backoff",
            source=source,
            delay_seconds=float(retry_state.get("next_delay_seconds") or RETRY_BACKOFF_BASE_SECONDS),
        )
    if int(state.get("same_fingerprint_auto_turn_count") or 0) >= SAME_FINGERPRINT_AUTO_TURN_THRESHOLD:
        return None
    continuation_policy = (text(state.get("continuation_policy")) or "auto").lower()
    if continuation_policy in {"none", "wait_for_user_or_resume"}:
        return None
    if continuation_policy == "when_external_progress" and not state.get("external_progress_observed"):
        return None
    return schedule_turn(
        runtime_root=runtime_root,
        quest_root=quest_root,
        quest_id=quest_id,
        reason="auto_continue",
        source=source,
        delay_seconds=AUTO_CONTINUE_DELAY_SECONDS,
    )


def _stale_completion_result(
    *,
    previous: Mapping[str, Any],
    quest_root: Path,
    quest_id: str,
    run_id: str,
    runner_status: str,
    source: str,
) -> dict[str, Any] | None:
    result = stale_runner_completion_result(
        previous=previous,
        quest_id=quest_id,
        run_id=run_id,
        runner_status=runner_status,
        source=source,
        recorded_at=utc_now(),
        backend_id=BACKEND_ID,
        snapshot_payload=snapshot(quest_root=quest_root, state=previous),
    )
    if result is not None:
        append_runtime_event(quest_root=quest_root, event=result["ignored_completion"])
    return result


def _launch_fields(payload: Mapping[str, Any]) -> dict[str, Any]:
    return launch_fields(payload, text=text)


def _turn_receipt(
    *,
    quest_root: Path,
    run_id: str,
    reason: str,
    source: str,
    status: str,
    started: bool,
    queued: bool,
    idempotency_key: str,
    extra: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    payload = turn_receipt_payload(
        quest_root=quest_root,
        run_id=run_id,
        reason=reason,
        source=source,
        status=status,
        started=started,
        queued=queued,
        idempotency_key=idempotency_key,
        recorded_at=utc_now(),
        extra=extra,
    )
    append_jsonl(turn_receipts_path(quest_root), payload)
    latest_path = quest_root / "artifacts" / "runtime" / "latest_turn_receipt.json"
    write_json(latest_path, payload)
    try:
        from med_autoscience.runtime_protocol import runtime_lifecycle_store

        payload["runtime_lifecycle_index"] = runtime_lifecycle_store.record_turn_receipt(
            quest_root=quest_root,
            receipt=payload,
            receipt_path=latest_path,
        )
        write_json(latest_path, payload)
    except Exception as exc:  # SQLite is an index/read-model; keep the file receipt authoritative.
        payload["runtime_lifecycle_index_error"] = f"{type(exc).__name__}: {exc}"
        write_json(latest_path, payload)
    return payload


def _record_post_turn_storage_maintenance_hook(*, quest_root: Path, quest_id: str, run_id: str, source: str) -> None:
    record_post_turn_storage_maintenance_hook(
        quest_root=quest_root,
        quest_id=quest_id,
        run_id=run_id,
        source=source,
        recorded_at=utc_now(),
        write_json=write_json,
        append_runtime_event=append_runtime_event,
    )


def _worker_lease_live(*, quest_root: Path, run_id: str) -> bool:
    return _lease_payload_live(
        lease=read_json(worker_lease_path(quest_root=quest_root, run_id=run_id)),
        run_id=run_id,
        now=_NOW,
        parse_time=parse_time,
        pid_live_check=pid_live,
        ttl_seconds=WORKER_LEASE_TTL_SECONDS,
    )
