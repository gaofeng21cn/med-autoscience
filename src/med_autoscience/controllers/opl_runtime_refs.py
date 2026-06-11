from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Mapping


_ACTIVE_QUEST_STATUSES = frozenset({"active", "running"})
_NO_LIVE_REASONS = frozenset(
    {
        "quest_marked_running_but_no_live_session",
        "running_quest_live_session_audit_failed",
    }
)
_PARKED_CLOSEOUT_REASONS = frozenset(
    {
        "blocked_turn_closeout_waiting_for_owner",
        "completed_parked_auto_continue_no_new_message",
        "parked_after_checkpoint_no_new_message",
    }
)
_OPL_STAGE_ATTEMPT_PREFIX = "opl-stage-attempt://"


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _is_opl_stage_attempt_run_id(value: str | None) -> bool:
    return bool(value and value.startswith(_OPL_STAGE_ATTEMPT_PREFIX))


def _opl_control_disproves_running_attempt(
    *,
    opl_control_present: bool,
    opl_control: Mapping[str, Any],
    runtime_liveness_status: str,
    active_run_id: str | None,
) -> bool:
    if not opl_control_present or not _is_opl_stage_attempt_run_id(active_run_id):
        return False
    if opl_control.get("running_provider_attempt") is True:
        return False
    return runtime_liveness_status not in {
        "attempt_running",
        "provider_admitted",
        "running",
        "live",
    }


def _trusted_continuation_stage_attempt(
    *,
    active_run_id: str | None,
    active_run_id_source: str | None,
    continuation_state: Mapping[str, Any],
) -> bool:
    return (
        active_run_id_source == "continuation_state.active_run_id"
        and _is_opl_stage_attempt_run_id(active_run_id)
        and _text(continuation_state.get("continuation_policy")) == "auto"
        and _text(continuation_state.get("continuation_anchor")) == "decision"
        and _text(continuation_state.get("continuation_reason")) == "controller_work_unit_pending"
    )


def _bool(value: object) -> bool | None:
    return value if isinstance(value, bool) else None


def _first_text_source(*candidates: tuple[str, object]) -> tuple[str | None, str | None]:
    for source, value in candidates:
        text = _text(value)
        if text is not None:
            return text, source
    return None, None


def _read_json_object(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _completed_parked_auto_continue_run(status_payload: Mapping[str, Any], active_run_id: str | None) -> bool:
    if active_run_id is None:
        return False
    quest_root_text = _text(status_payload.get("quest_root"))
    if quest_root_text is None:
        return False
    run_root = Path(quest_root_text).expanduser() / ".ds" / "runs" / active_run_id
    command_payload = _read_json_object(run_root / "command.json")
    result_payload = _read_json_object(run_root / "result.json")
    if command_payload is None or result_payload is None:
        return False
    return (
        _text(command_payload.get("turn_reason")) == "auto_continue"
        and _text(command_payload.get("turn_mode")) == "parked"
        and result_payload.get("exit_code") == 0
    )


def _parked_closeout_continuation(continuation_state: Mapping[str, Any]) -> str | None:
    continuation_reason = _text(continuation_state.get("continuation_reason"))
    if continuation_reason not in _PARKED_CLOSEOUT_REASONS:
        return None
    if _text(continuation_state.get("continuation_policy")) != "wait_for_user_or_resume":
        return None
    if _text(continuation_state.get("active_run_id")) is not None:
        return None
    return continuation_reason


@dataclass(frozen=True)
class OplRuntimeRefs:
    quest_status: str | None
    decision: str | None
    reason: str | None
    runtime_liveness_status: str
    worker_running: bool | None
    worker_pending: bool | None
    stop_requested: bool | None
    active_run_id: str | None
    active_run_id_source: str | None
    strict_live: bool
    missing_live_session: bool
    recovery_pending: bool
    monitoring_url: str | None

    def to_runtime_refs_dict(self) -> dict[str, Any]:
        return {
            "runtime_liveness_status": self.runtime_liveness_status,
            "worker_running": self.worker_running,
            "worker_pending": self.worker_pending,
            "stop_requested": self.stop_requested,
            "active_run_id": self.active_run_id,
            "active_run_id_source": self.active_run_id_source,
            "strict_live": self.strict_live,
            "missing_live_session": self.missing_live_session,
            "recovery_pending": self.recovery_pending,
        }

    def to_domain_activity_ref(self) -> dict[str, Any]:
        if self.strict_live:
            activity_state = "running"
            heartbeat_state = self.runtime_liveness_status or "live"
        elif self.runtime_liveness_status == "parked":
            activity_state = "parked"
            heartbeat_state = "parked"
        elif self.recovery_pending:
            activity_state = "recovering"
            heartbeat_state = "missing_live_session" if self.missing_live_session else self.runtime_liveness_status
        elif self.quest_status in {"stopped", "completed"}:
            activity_state = "stopped"
            heartbeat_state = "inactive"
        else:
            activity_state = "unknown"
            heartbeat_state = self.runtime_liveness_status or "unknown"
        return {
            "provider_owner": "one-person-lab",
            "source": "opl_runtime_refs",
            "activity_state": activity_state,
            "heartbeat_state": heartbeat_state,
            "quest_status": self.quest_status,
            "active_run_id": self.active_run_id,
            "monitoring_url": self.monitoring_url,
            "reason": self.reason,
        }


def resolve_opl_runtime_refs(
    status_payload: Mapping[str, Any],
    *,
    supervisor_tick_audit: Mapping[str, Any] | None = None,
) -> OplRuntimeRefs:
    opl_control = _mapping(status_payload.get("opl_current_control_state")) or _mapping(
        status_payload.get("current_control_state")
    )
    runtime_liveness_audit = _mapping(status_payload.get("runtime_liveness_audit"))
    runtime_audit = _mapping(runtime_liveness_audit.get("runtime_audit"))
    autonomous_runtime_notice = _mapping(status_payload.get("autonomous_runtime_notice"))
    execution_owner_guard = _mapping(status_payload.get("execution_owner_guard"))
    continuation_state = _mapping(status_payload.get("continuation_state"))
    execution = _mapping(status_payload.get("execution"))
    supervisor_tick = _mapping(supervisor_tick_audit)

    active_run_id, active_run_id_source = _first_text_source(
        ("opl_current_control_state.active_run_id", opl_control.get("active_run_id")),
        ("status.active_run_id", status_payload.get("active_run_id")),
        ("execution_owner_guard.active_run_id", execution_owner_guard.get("active_run_id")),
        ("autonomous_runtime_notice.active_run_id", autonomous_runtime_notice.get("active_run_id")),
        ("runtime_liveness_audit.active_run_id", runtime_liveness_audit.get("active_run_id")),
        ("runtime_audit.active_run_id", runtime_audit.get("active_run_id")),
        ("continuation_state.active_run_id", continuation_state.get("active_run_id")),
        ("execution.active_run_id", execution.get("active_run_id")),
    )
    runtime_liveness_status = (
        _text(opl_control.get("status"))
        or _text(opl_control.get("state"))
        or _text(status_payload.get("runtime_liveness_status"))
        or _text(runtime_liveness_audit.get("status"))
        or _text(runtime_audit.get("status"))
        or "unknown"
    )
    worker_running = _bool(status_payload.get("worker_running"))
    if worker_running is None:
        worker_running = _bool(runtime_audit.get("worker_running"))
    if (
        worker_running is None
        and _text(runtime_liveness_audit.get("source")) == "opl_current_control_state_provider_attempt"
        and runtime_liveness_audit.get("running_provider_attempt") is True
    ):
        worker_running = True
    worker_pending = _bool(runtime_audit.get("worker_pending"))
    stop_requested = _bool(runtime_audit.get("stop_requested"))
    quest_status = _text(status_payload.get("quest_status")) or _text(continuation_state.get("quest_status"))
    decision = _text(status_payload.get("decision"))
    reason = _text(status_payload.get("reason")) or _text(status_payload.get("runtime_reason"))
    opl_control_present = bool(opl_control)
    liveness_source_present = bool(runtime_liveness_audit)
    if _opl_control_disproves_running_attempt(
        opl_control_present=opl_control_present,
        opl_control=opl_control,
        runtime_liveness_status=runtime_liveness_status,
        active_run_id=active_run_id,
    ):
        active_run_id = None
        active_run_id_source = "invalidated_no_running_provider_attempt"
    if (
        not opl_control_present
        and
        liveness_source_present
        and active_run_id is not None
        and not _trusted_continuation_stage_attempt(
            active_run_id=active_run_id,
            active_run_id_source=active_run_id_source,
            continuation_state=continuation_state,
        )
        and (runtime_liveness_status != "live" or worker_running is not True)
    ):
        active_run_id = None
        active_run_id_source = "invalidated_no_live_worker"
    if _completed_parked_auto_continue_run(status_payload, active_run_id):
        runtime_liveness_status = "parked"
        worker_running = False
        worker_pending = False
        stop_requested = False
        active_run_id = None
        active_run_id_source = "completed_parked_auto_continue"
        reason = "completed_parked_auto_continue_no_new_message"
    parked_closeout_reason = _parked_closeout_continuation(continuation_state)
    if parked_closeout_reason is not None and (
        reason not in _NO_LIVE_REASONS
        or parked_closeout_reason == "blocked_turn_closeout_waiting_for_owner"
    ):
        runtime_liveness_status = "parked"
        worker_running = False
        worker_pending = False
        stop_requested = False
        active_run_id = None
        active_run_id_source = "continuation_state.parked_closeout"
        reason = parked_closeout_reason
    strict_live = (
        active_run_id is not None
        and (
            (
                opl_control_present
                and runtime_liveness_status in {"attempt_running", "provider_admitted", "running", "live"}
            )
            or (
                not opl_control_present
                and runtime_liveness_status == "live"
                and worker_running is True
            )
        )
    )
    supervisor_tick_status = _text(opl_control.get("supervisor_tick_status")) or _text(supervisor_tick.get("status"))
    trusted_active_run_for_recovery = active_run_id_source in {
        "status.active_run_id",
        "execution_owner_guard.active_run_id",
        "autonomous_runtime_notice.active_run_id",
        "runtime_liveness_audit.active_run_id",
        "runtime_audit.active_run_id",
    } or _trusted_continuation_stage_attempt(
        active_run_id=active_run_id,
        active_run_id_source=active_run_id_source,
        continuation_state=continuation_state,
    )
    missing_live_session = runtime_liveness_status != "parked" and (
        (reason in _NO_LIVE_REASONS and not trusted_active_run_for_recovery)
        or (quest_status in _ACTIVE_QUEST_STATUSES and runtime_liveness_status == "none")
        or (quest_status in _ACTIVE_QUEST_STATUSES and supervisor_tick_status in {"missing", "stale", "invalid"})
    )
    recovery_pending = bool(quest_status in _ACTIVE_QUEST_STATUSES and not strict_live and missing_live_session)
    return OplRuntimeRefs(
        quest_status=quest_status,
        decision=decision,
        reason=reason,
        runtime_liveness_status=runtime_liveness_status,
        worker_running=worker_running,
        worker_pending=worker_pending,
        stop_requested=stop_requested,
        active_run_id=active_run_id,
        active_run_id_source=active_run_id_source,
        strict_live=strict_live,
        missing_live_session=missing_live_session,
        recovery_pending=recovery_pending,
        monitoring_url=_text(autonomous_runtime_notice.get("browser_url")),
    )


def active_run_id(status_payload: Mapping[str, Any]) -> str | None:
    return resolve_opl_runtime_refs(status_payload).active_run_id


def runtime_liveness_status(status_payload: Mapping[str, Any]) -> str:
    return resolve_opl_runtime_refs(status_payload).runtime_liveness_status


def strict_live(status_payload: Mapping[str, Any]) -> bool:
    return resolve_opl_runtime_refs(status_payload).strict_live
