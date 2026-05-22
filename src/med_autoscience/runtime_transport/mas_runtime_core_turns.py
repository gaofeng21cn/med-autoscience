from __future__ import annotations

from collections.abc import Callable, Mapping
from datetime import datetime
from pathlib import Path
from typing import Any

from med_autoscience.runtime_transport import mas_runtime_core_turn_monitor as turn_monitor
from med_autoscience.runtime_transport import mas_runtime_core_turn_blocks as turn_blocks
from med_autoscience.runtime_transport import mas_runtime_core_turn_messages as turn_messages
from med_autoscience.runtime_transport import mas_runtime_core_turn_residency as turn_residency
from med_autoscience.runtime_transport import mas_runtime_core_turn_state as turn_state
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
from med_autoscience.runtime_transport import mas_runtime_core_turn_timers as turn_timers
from med_autoscience.runtime_transport.mas_runtime_core_pause_resume import release_paused_explicit_resume
from med_autoscience.runtime_transport.mas_runtime_core_turn_paths import (
    delayed_turn_path,
    run_root as _run_root,
    turn_receipts_path,
    worker_lease_path,
)
from med_autoscience.runtime_transport.mas_runtime_core_turn_utils import (
    idempotency_key as make_idempotency_key,
    pid_live,
    runner_unavailable,
    text,
)
from med_autoscience.runtime_transport.mas_runtime_core_turn_policy import (
    AUTO_CONTINUE_DELAY_SECONDS,
    BACKEND_ID,
    ENGINE_ID,
    MAX_RETRY_ATTEMPTS,
    RETRY_BACKOFF_BASE_SECONDS,
    SAME_FINGERPRINT_AUTO_TURN_THRESHOLD,
    TERMINAL_STATUSES,
)


_TURN_RUNNER: MasTurnRunner = CodexExecTurnRunner()
def set_turn_runner_for_tests(runner: MasTurnRunner) -> None:
    global _TURN_RUNNER
    _TURN_RUNNER = runner


def reset_turn_runner_for_tests() -> None:
    global _TURN_RUNNER
    _TURN_RUNNER = CodexExecTurnRunner()


def set_clock_for_tests(clock: Callable[[], datetime]) -> None:
    turn_state.set_clock_for_tests(clock)


def reset_clock_for_tests() -> None:
    turn_state.reset_clock_for_tests()


def set_delayed_timers_enabled_for_tests(enabled: bool) -> None:
    turn_timers.set_delayed_timers_enabled_for_tests(enabled)


def utc_now() -> str:
    return turn_state.utc_now()


def run_id(*, quest_id: str) -> str:
    slug = turn_state.now().strftime("%Y%m%dT%H%M%S%fZ")
    safe_quest_id = "".join(ch if ch.isalnum() or ch in "-_." else "-" for ch in quest_id).strip("-") or "quest"
    return f"mas-run-{safe_quest_id}-{slug}"


def read_json(path: Path) -> dict[str, Any]:
    return turn_state.read_json(path)


def write_json(path: Path, payload: Mapping[str, Any]) -> None:
    turn_state.write_json(path, payload)


def append_jsonl(path: Path, payload: Mapping[str, Any]) -> None:
    turn_state.append_jsonl(path, payload)


def load_state(*, quest_root: Path) -> dict[str, Any]:
    return turn_state.load_state(quest_root=quest_root)


def persist_state(
    *,
    quest_root: Path,
    updates: Mapping[str, Any],
    source: str,
    event_name: str,
    delete_keys: list[str] | tuple[str, ...] | None = None,
) -> dict[str, Any]:
    return turn_state.persist_state(
        quest_root=quest_root,
        updates=updates,
        source=source,
        event_name=event_name,
        delete_keys=delete_keys,
    )


def append_runtime_event(*, quest_root: Path, event: Mapping[str, Any]) -> None:
    turn_state.append_runtime_event(quest_root=quest_root, event=event)


def load_message_queue(*, quest_root: Path) -> dict[str, Any]:
    return turn_messages.load_message_queue(quest_root=quest_root)


def write_message_queue(*, quest_root: Path, queue: Mapping[str, Any]) -> None:
    turn_messages.write_message_queue(quest_root=quest_root, queue=queue)


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
    message, pending_count = turn_messages.queue_user_message(
        quest_root=quest_root,
        quest_id=quest_id,
        content=text,
        source=source,
        recorded_at=now,
        reply_to_interaction_id=reply_to_interaction_id,
        decision_response=decision_response,
    )
    persist_state(
        quest_root=quest_root,
        updates={"pending_user_message_count": pending_count},
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
    allow_paused_explicit_resume: bool = False,
) -> dict[str, Any]:
    state = load_state(quest_root=quest_root)
    runtime_status = text(state.get("status"))
    released_state = release_paused_explicit_resume(
        quest_root=quest_root,
        state=state,
        reason=reason,
        source=source,
        allow_paused_explicit_resume=allow_paused_explicit_resume,
        text=text,
        utc_now=utc_now,
        persist_state=persist_state,
    )
    if released_state is not None:
        state = released_state
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
    return turn_residency.prune_orphan_worker_leases_before_new_turn(quest_root=quest_root, source=source)


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
    lease = turn_residency.initial_worker_lease_payload(
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
    return turn_messages.claim_pending_user_messages(
        quest_root=quest_root,
        run_id=run_id,
        claimed_at=utc_now(),
    )


def restore_claimed_user_messages(*, quest_root: Path, run_id: str) -> None:
    turn_messages.restore_claimed_user_messages(quest_root=quest_root, run_id=run_id)


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
    return turn_residency.inspect_turn_lifecycle(
        quest_root=quest_root,
        schedule_turn=schedule_turn,
        pid_live_check=pid_live,
    )


def drain_due_delayed_turn(*, quest_root: Path, source: str) -> dict[str, Any] | None:
    return turn_residency.drain_due_delayed_turn(quest_root=quest_root, source=source, schedule_turn=schedule_turn)


def _arm_delayed_turn_timer(*, quest_root: Path, delay_seconds: float, source: str) -> None:
    turn_residency.arm_delayed_turn_timer(
        quest_root=quest_root,
        delay_seconds=delay_seconds,
        source=source,
        schedule_turn=schedule_turn,
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
    return turn_residency.reconcile_stale_liveness(
        quest_root=quest_root,
        source=source,
        inspect_turn_lifecycle=inspect_turn_lifecycle,
        turn_receipt=_turn_receipt,
        make_idempotency_key=make_idempotency_key,
    )


def snapshot(*, quest_root: Path, state: Mapping[str, Any] | None = None) -> dict[str, Any]:
    return turn_state.snapshot(quest_root=quest_root, state=state)


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
        from med_autoscience.runtime_protocol import lifecycle_refs_adapter

        payload["runtime_lifecycle_index"] = lifecycle_refs_adapter.record_turn_receipt(
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
    return turn_residency.worker_lease_live(quest_root=quest_root, run_id=run_id, pid_live_check=pid_live)
