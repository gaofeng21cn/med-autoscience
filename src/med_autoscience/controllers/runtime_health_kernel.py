from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from med_autoscience.controllers.control_plane_facts import resolve_control_plane_facts
from med_autoscience.controllers.runtime_health_kernel_parts import explicit_resume, run_epoch_budget


SCHEMA_VERSION = 1
EVENT_LOG_RELATIVE_PATH = Path("artifacts") / "runtime" / "health" / "events.jsonl"
SNAPSHOT_RELATIVE_PATH = Path("artifacts") / "runtime" / "health" / "latest.json"
MAX_RECOVERY_ATTEMPTS = 3

RUNTIME_HEALTH_EVENT_TYPES = frozenset(
    {
        "runtime_state_observed",
        "daemon_probe",
        "worker_heartbeat",
        "session_probe",
        "supervisor_tick",
        "launch_attempt",
        "recover_attempt",
        "relaunch_attempt",
        "runtime_event_observed",
        "stale_progress_detected",
        "attempt_released",
        "escalation_opened",
        "escalation_resolved",
    }
)

_ACTIVE_QUEST_STATUSES = frozenset({"active", "running"})
_RECOVERY_DECISIONS = frozenset({"create_and_start", "resume", "relaunch_stopped"})
_ATTEMPT_EVENT_TYPES = frozenset({"launch_attempt", "recover_attempt", "relaunch_attempt"})
_FAILED_ATTEMPT_STATES = frozenset({"failed", "timeout", "lost", "missing_live_session"})
_TERMINAL_ESCALATION_REASONS = frozenset({"manual_runtime_review_required", "recovery_retry_budget_exhausted"})
_ACTIVITY_TIMEOUT_BREACHES = frozenset(
    {
        "read_churn_without_artifact_delta",
        "same_fingerprint_loop",
        "no_meaningful_progress",
    }
)
_BASE_ALLOWED_ACTIONS = (
    "read_runtime_status",
    "refresh_runtime_liveness",
    "recover_runtime",
    "relaunch_runtime",
    "continue_supervising_runtime",
    "open_monitoring_entry",
    "manual_runtime_review",
)
_VOLATILE_SUPERVISOR_KEYS = frozenset(
    {
        "age_seconds",
        "checked_at",
        "generated_at",
        "seconds_since_latest_recorded_at",
        "seconds_since_latest_progress",
    }
)
_STABLE_RUNTIME_AUDIT_KEYS = (
    "ok",
    "status",
    "source",
    "active_run_id",
    "worker_running",
    "worker_pending",
    "stop_requested",
    "runtime_event_contract_error",
    "runtime_event_ref_contract_error",
    "liveness_guard_reason",
)
_STABLE_RUNTIME_LIVENESS_AUDIT_KEYS = (
    "ok",
    "status",
    "source",
    "active_run_id",
    "runner_live",
    "bash_live",
    "stale_progress",
    "liveness_guard_reason",
    "error",
)


def runtime_health_events_path(*, study_root: Path) -> Path:
    return Path(study_root).expanduser().resolve() / EVENT_LOG_RELATIVE_PATH


def runtime_health_snapshot_path(*, study_root: Path) -> Path:
    return Path(study_root).expanduser().resolve() / SNAPSHOT_RELATIVE_PATH


def _stable_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _bool(value: object) -> bool | None:
    return value if isinstance(value, bool) else None


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _read_json(path: Path | None) -> dict[str, Any] | None:
    if path is None or not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object at {path}")
    return payload


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    events: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        text = line.strip()
        if not text:
            continue
        payload = json.loads(text)
        if isinstance(payload, dict):
            events.append(dict(payload))
    return events


def read_runtime_health_events(*, study_root: Path) -> list[dict[str, Any]]:
    return _read_jsonl(runtime_health_events_path(study_root=study_root))


def _event_id_seed(
    *,
    study_id: str,
    quest_id: str,
    event_type: str,
    payload: Mapping[str, Any],
    recorded_at: str,
    sequence: int,
) -> str:
    return _stable_json(
        {
            "study_id": study_id,
            "quest_id": quest_id,
            "event_type": event_type,
            "payload": dict(payload),
            "recorded_at": recorded_at,
            "sequence": sequence,
        }
    )


def _build_event_id(
    *,
    study_id: str,
    quest_id: str,
    event_type: str,
    payload: Mapping[str, Any],
    recorded_at: str,
    sequence: int,
) -> str:
    digest = hashlib.sha256(
        _event_id_seed(
            study_id=study_id,
            quest_id=quest_id,
            event_type=event_type,
            payload=payload,
            recorded_at=recorded_at,
            sequence=sequence,
        ).encode("utf-8")
    ).hexdigest()[:16]
    return f"runtime-health-event-{sequence:06d}-{digest}"


def _event_source_signature(event_type: str, payload: Mapping[str, Any]) -> str:
    digest = hashlib.sha256(
        _stable_json(
            {
                "event_type": event_type,
                "payload": _stable_event_payload(event_type, payload),
            }
        ).encode("utf-8")
    ).hexdigest()[:24]
    return f"runtime-health-source::{event_type}::{digest}"


def _stable_event_payload(event_type: str, payload: Mapping[str, Any]) -> dict[str, Any]:
    if event_type != "runtime_state_observed":
        return dict(payload)
    stable = dict(payload)
    runtime_audit = _mapping(stable.get("runtime_audit"))
    if runtime_audit:
        stable["runtime_audit"] = _stable_runtime_audit(runtime_audit)
    liveness_audit = _mapping(stable.get("runtime_liveness_audit"))
    if liveness_audit:
        stable["runtime_liveness_audit"] = _stable_runtime_liveness_audit(liveness_audit)
    return stable


def _source_signature_for_event(event: Mapping[str, Any]) -> str:
    event_type = str(event.get("event_type") or "").strip()
    payload = _mapping(event.get("payload"))
    return _text(event.get("source_signature")) or _event_source_signature(event_type, payload)


def _snapshot_source_signature(events: list[dict[str, Any]]) -> str | None:
    if not events:
        return None
    digest = hashlib.sha256(
        _stable_json(
            [
                {
                    "event_type": event.get("event_type"),
                    "source_signature": _source_signature_for_event(event),
                }
                for event in events
            ]
        ).encode("utf-8")
    ).hexdigest()[:24]
    return f"runtime-health-snapshot::{digest}"


def append_runtime_health_event(
    *,
    study_root: Path,
    study_id: str,
    quest_id: str,
    event_type: str,
    payload: Mapping[str, Any] | None = None,
    recorded_at: str,
    source_signature: str | None = None,
) -> dict[str, Any]:
    event_type_text = str(event_type or "").strip()
    if event_type_text not in RUNTIME_HEALTH_EVENT_TYPES:
        raise ValueError(f"unknown runtime health event type: {event_type}")
    resolved_payload = dict(payload or {})
    path = runtime_health_events_path(study_root=study_root)
    existing = _read_jsonl(path)
    sequence = len(existing) + 1
    event = {
        "schema_version": SCHEMA_VERSION,
        "event_id": _build_event_id(
            study_id=study_id,
            quest_id=quest_id,
            event_type=event_type_text,
            payload=resolved_payload,
            recorded_at=recorded_at,
            sequence=sequence,
        ),
        "sequence": sequence,
        "study_id": study_id,
        "quest_id": quest_id,
        "event_type": event_type_text,
        "recorded_at": recorded_at,
        "payload": resolved_payload,
    }
    normalized_source_signature = _text(source_signature)
    if normalized_source_signature is not None:
        event["source_signature"] = normalized_source_signature
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")
    return event


def _authority_ref(event: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "event_id": _text(event.get("event_id")),
        "event_type": _text(event.get("event_type")),
        "recorded_at": _text(event.get("recorded_at")),
    }


def _latest_event(events: Iterable[dict[str, Any]], event_type: str) -> dict[str, Any] | None:
    for event in reversed(list(events)):
        if event.get("event_type") == event_type:
            return event
    return None


def _events_for(events: Iterable[dict[str, Any]], event_types: frozenset[str]) -> list[dict[str, Any]]:
    return [event for event in events if str(event.get("event_type") or "") in event_types]


def _event_payload(event: Mapping[str, Any] | None) -> dict[str, Any]:
    return _mapping(event.get("payload")) if event is not None else {}


def _first_text(*values: object) -> str | None:
    for value in values:
        text = _text(value)
        if text is not None:
            return text
    return None


def _active_run_from_payload(payload: Mapping[str, Any]) -> str | None:
    return _first_text(
        payload.get("active_run_id"),
        _mapping(payload.get("runtime_audit")).get("active_run_id"),
        _mapping(payload.get("runtime_liveness_audit")).get("active_run_id"),
        _mapping(payload.get("autonomous_runtime_notice")).get("active_run_id"),
    )


def _stable_runtime_audit(payload: Mapping[str, Any]) -> dict[str, Any]:
    return {key: payload[key] for key in _STABLE_RUNTIME_AUDIT_KEYS if key in payload}


def _stable_runtime_liveness_audit(payload: Mapping[str, Any]) -> dict[str, Any]:
    stable = {key: payload[key] for key in _STABLE_RUNTIME_LIVENESS_AUDIT_KEYS if key in payload}
    runtime_audit = _mapping(payload.get("runtime_audit"))
    if runtime_audit:
        stable["runtime_audit"] = _stable_runtime_audit(runtime_audit)
    bash_session_audit = _mapping(payload.get("bash_session_audit"))
    if bash_session_audit:
        stable["bash_session_audit"] = {
            key: bash_session_audit[key]
            for key in ("ok", "status", "session_count", "live_session_count", "live_session_ids")
            if key in bash_session_audit
        }
    return stable


def _last_known_run_id(events: list[dict[str, Any]], *, strict_live: bool, active_run_id: str | None) -> str | None:
    if strict_live:
        return active_run_id
    for event in reversed(events):
        payload = _event_payload(event)
        candidate = _active_run_from_payload(payload)
        if candidate is not None:
            return candidate
    return None


def _latest_runtime_observation(events: list[dict[str, Any]]) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    event = _latest_event(events, "runtime_state_observed")
    return event, _event_payload(event)


def _latest_supervisor_state(events: list[dict[str, Any]]) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    event = _latest_event(events, "supervisor_tick")
    payload = _event_payload(event)
    status = _first_text(payload.get("supervisor_tick_status"), payload.get("status"))
    stable_payload = {
        key: item
        for key, item in payload.items()
        if key not in _VOLATILE_SUPERVISOR_KEYS
    }
    return event, {
        "status": status or "unknown",
        "required": _bool(payload.get("required")),
        "latest_recorded_at": _first_text(payload.get("latest_recorded_at"), payload.get("recorded_at")),
        "source_signature": _event_source_signature("supervisor_tick", stable_payload),
    }


def _events_for_budget(
    events: list[dict[str, Any]],
    event_types: Iterable[str],
    *,
    active_run_id: str | None,
) -> list[dict[str, Any]]:
    return run_epoch_budget.events_for_budget(
        events,
        event_types,
        active_run_id=active_run_id,
        event_payload=_event_payload,
        active_run_from_payload=_active_run_from_payload,
    )


def _attempt_events_for_budget(events: list[dict[str, Any]], *, active_run_id: str | None) -> list[dict[str, Any]]:
    return _events_for_budget(events, _ATTEMPT_EVENT_TYPES, active_run_id=active_run_id)


def _attempt_count(
    events: list[dict[str, Any]],
    runtime_payload: Mapping[str, Any],
    *,
    active_run_id: str | None = None,
) -> int:
    attempts = len(_attempt_events_for_budget(events, active_run_id=active_run_id))
    decision = _text(runtime_payload.get("decision"))
    if decision in _RECOVERY_DECISIONS and attempts == 0:
        attempts = 1
    return attempts


def _failed_attempt_count(events: list[dict[str, Any]], *, active_run_id: str | None = None) -> int:
    failed = 0
    for event in _attempt_events_for_budget(events, active_run_id=active_run_id):
        state = _text(_event_payload(event).get("attempt_state"))
        if state in _FAILED_ATTEMPT_STATES:
            failed += 1
    return failed


def _latest_escalation_event(events: list[dict[str, Any]], *, active_run_id: str | None) -> dict[str, Any] | None:
    selected = _events_for_budget(events, ("escalation_opened",), active_run_id=active_run_id)
    return selected[-1] if selected else None


def _latest_failure_reason(
    events: list[dict[str, Any]],
    runtime_payload: Mapping[str, Any],
    *,
    active_run_id: str | None = None,
) -> str | None:
    for event in reversed(
        _events_for_budget(
            events,
            _ATTEMPT_EVENT_TYPES | frozenset({"escalation_opened"}),
            active_run_id=active_run_id,
        )
    ):
        payload = _event_payload(event)
        reason = _first_text(payload.get("failure_reason"), payload.get("reason"))
        if reason is not None:
            return reason
    return _first_text(runtime_payload.get("liveness_guard_reason"), runtime_payload.get("reason"))


def _strict_live(runtime_payload: Mapping[str, Any]) -> tuple[bool, str, bool | None, str | None]:
    runtime_liveness_status = (
        _text(runtime_payload.get("runtime_liveness_status"))
        or _text(runtime_payload.get("status"))
        or _text(_mapping(runtime_payload.get("runtime_liveness_audit")).get("status"))
        or "unknown"
    )
    runtime_audit = _mapping(runtime_payload.get("runtime_audit"))
    liveness_audit = _mapping(runtime_payload.get("runtime_liveness_audit"))
    worker_running = _bool(runtime_payload.get("worker_running"))
    if worker_running is None:
        worker_running = _bool(runtime_audit.get("worker_running"))
    if worker_running is None:
        worker_running = _bool(_mapping(liveness_audit.get("runtime_audit")).get("worker_running"))
    active_run_id = _active_run_from_payload(runtime_payload)
    return runtime_liveness_status == "live" and worker_running is True and active_run_id is not None, runtime_liveness_status, worker_running, active_run_id


def _activity_timeout_from_runtime_payload(runtime_payload: Mapping[str, Any]) -> tuple[bool, list[str]]:
    autonomy_slo = _mapping(runtime_payload.get("autonomy_slo"))
    progress_freshness = _mapping(runtime_payload.get("progress_freshness"))
    activity_timeout = _mapping(progress_freshness.get("activity_timeout"))
    if _text(activity_timeout.get("state")) == "timed_out":
        return True, ["live_worker_meaningful_artifact_delta_timeout"]
    breach_types = {
        text
        for item in autonomy_slo.get("breach_types") or []
        if (text := _text(item)) is not None
    }
    timeout_breaches = sorted(breach_types & _ACTIVITY_TIMEOUT_BREACHES)
    if not timeout_breaches:
        return False, []
    state = _text(autonomy_slo.get("state"))
    if state not in {"breach", "blocked_external"}:
        return False, []
    return True, ["live_worker_meaningful_artifact_delta_timeout", *timeout_breaches]


def _worker_liveness_state(
    *,
    runtime_liveness_status: str,
    worker_running: bool | None,
    active_run_id: str | None,
    strict_live: bool,
    activity_timeout: bool,
    activity_timeout_reasons: list[str],
    quest_status: str | None,
    reason: str | None,
    supervisor_status: str | None,
) -> tuple[dict[str, Any], list[str]]:
    blocking_reasons: list[str] = []
    if strict_live and activity_timeout:
        state = "activity_timeout"
        blocking_reasons.extend(activity_timeout_reasons)
    elif strict_live:
        state = "live"
    elif runtime_liveness_status == "live" and active_run_id is None:
        state = "unknown"
        blocking_reasons.append("live_worker_requires_active_run_id")
    elif runtime_liveness_status == "live" and worker_running is not True:
        state = "unknown"
        blocking_reasons.append("live_worker_requires_worker_running")
    elif (
        quest_status in _ACTIVE_QUEST_STATUSES
        and (
            runtime_liveness_status == "none"
            or reason == "quest_marked_running_but_no_live_session"
            or supervisor_status in {"missing", "stale", "invalid"}
        )
    ):
        state = "missing_live_session"
        blocking_reasons.append("quest_marked_running_but_no_live_session")
    elif quest_status not in _ACTIVE_QUEST_STATUSES:
        state = "not_live"
    elif runtime_liveness_status == "unknown":
        state = "unknown"
        blocking_reasons.append("runtime_liveness_unknown")
    else:
        state = "not_live"
    return {
        "state": state,
        "runtime_liveness_status": runtime_liveness_status,
        "worker_running": worker_running,
        "active_run_id": active_run_id if strict_live else None,
    }, blocking_reasons


def _dominant_event(
    *,
    events: list[dict[str, Any]],
    strict_live: bool,
    missing_live_session: bool,
    failed_attempt_count: int,
    runtime_event: dict[str, Any] | None,
    active_run_id: str | None,
) -> dict[str, Any] | None:
    escalation = _latest_escalation_event(events, active_run_id=active_run_id)
    if escalation is not None:
        return escalation
    if failed_attempt_count >= MAX_RECOVERY_ATTEMPTS:
        attempts = _attempt_events_for_budget(events, active_run_id=active_run_id)
        return attempts[-1] if attempts else None
    if missing_live_session and runtime_event is not None:
        return runtime_event
    if strict_live and runtime_event is not None:
        return runtime_event
    return events[-1] if events else None


def _projection_invalidations(
    *,
    events: list[dict[str, Any]],
    dominant: dict[str, Any] | None,
    strict_live: bool,
    last_known_run_id: str | None,
) -> list[dict[str, Any]]:
    if dominant is None or strict_live or last_known_run_id is None:
        return []
    dominant_id = _text(dominant.get("event_id"))
    invalidations: list[dict[str, Any]] = []
    for event in events:
        if event.get("event_type") not in {"launch_attempt", "recover_attempt", "relaunch_attempt"}:
            continue
        payload = _event_payload(event)
        if _active_run_from_payload(payload) != last_known_run_id:
            continue
        invalidations.append(
            {
                "invalidated_surface": "last_launch_report",
                "invalidated_event_id": _text(event.get("event_id")),
                "invalidated_by_event_id": dominant_id,
                "reason": "runtime_liveness_observation_dominates_stale_run_handle",
            }
        )
        break
    return invalidations


def _allowed_controller_actions(*, canonical_runtime_action: str) -> list[str]:
    if canonical_runtime_action in {"recover_runtime", "relaunch_runtime", "probe_runtime_liveness"}:
        return [
            "read_runtime_status",
            "refresh_runtime_liveness",
            "recover_runtime",
            "relaunch_runtime",
            "open_monitoring_entry",
        ]
    if canonical_runtime_action in {"escalate_runtime", "external_supervisor_required"}:
        return ["read_runtime_status", "open_monitoring_entry", "manual_runtime_review"]
    return list(_BASE_ALLOWED_ACTIONS)


def _snapshot_from_events(
    *,
    study_root: Path,
    study_id: str,
    quest_id: str,
    events: list[dict[str, Any]],
) -> dict[str, Any]:
    runtime_event, runtime_payload = _latest_runtime_observation(events)
    supervisor_event, supervisor_state = _latest_supervisor_state(events)
    quest_status = _first_text(runtime_payload.get("quest_status"), runtime_payload.get("observed_quest_status"))
    decision = _text(runtime_payload.get("decision"))
    reason = _first_text(runtime_payload.get("reason"), runtime_payload.get("runtime_reason"))
    strict_live, runtime_liveness_status, worker_running, observed_active_run_id = _strict_live(runtime_payload)
    activity_timeout, activity_timeout_reasons = _activity_timeout_from_runtime_payload(runtime_payload)
    worker_state, blocking_reasons = _worker_liveness_state(
        runtime_liveness_status=runtime_liveness_status,
        worker_running=worker_running,
        active_run_id=observed_active_run_id,
        strict_live=strict_live,
        activity_timeout=activity_timeout,
        activity_timeout_reasons=activity_timeout_reasons,
        quest_status=quest_status,
        reason=reason,
        supervisor_status=_text(supervisor_state.get("status")),
    )
    active_budget_run_id = observed_active_run_id if strict_live else None
    failed_attempts = _failed_attempt_count(events, active_run_id=active_budget_run_id)
    attempt_count = _attempt_count(events, runtime_payload, active_run_id=active_budget_run_id)
    escalation_event = _latest_escalation_event(events, active_run_id=active_budget_run_id)
    missing_live_session = worker_state["state"] == "missing_live_session"
    live_activity_timeout = worker_state["state"] == "activity_timeout"
    retry_budget_remaining = max(MAX_RECOVERY_ATTEMPTS - max(attempt_count, failed_attempts), 0)
    recovery_path_requested = decision in _RECOVERY_DECISIONS or bool(_events_for(events, _ATTEMPT_EVENT_TYPES))
    awaiting_explicit_resume_reason = explicit_resume.reason_requires_explicit_resume(reason)
    retry_budget_exhausted = (
        retry_budget_remaining == 0
        and max(attempt_count, failed_attempts) >= MAX_RECOVERY_ATTEMPTS
        and (
            recovery_path_requested
            or missing_live_session
            or live_activity_timeout
            or worker_state["state"] == "unknown"
        )
    )

    if awaiting_explicit_resume_reason:
        attempt_state = "awaiting_explicit_resume"
        canonical_runtime_action = "await_explicit_resume"
        blocking_reasons = []
    elif escalation_event is not None or failed_attempts >= MAX_RECOVERY_ATTEMPTS or retry_budget_exhausted:
        attempt_state = "escalated"
        canonical_runtime_action = "external_supervisor_required"
        retry_budget_remaining = 0
        blocking_reasons.append("runtime_recovery_retry_budget_exhausted")
    elif live_activity_timeout:
        attempt_state = "recovering"
        canonical_runtime_action = "recover_runtime"
    elif strict_live:
        attempt_state = "live"
        canonical_runtime_action = "continue_supervising_runtime"
        retry_budget_remaining = MAX_RECOVERY_ATTEMPTS
    elif missing_live_session:
        attempt_state = "recovering"
        canonical_runtime_action = "recover_runtime"
    elif worker_state["state"] == "unknown":
        attempt_state = "probe_required"
        canonical_runtime_action = "probe_runtime_liveness"
    else:
        attempt_state = "idle"
        canonical_runtime_action = "continue_supervising_runtime"

    dominant = _dominant_event(
        events=events,
        strict_live=strict_live,
        missing_live_session=missing_live_session,
        failed_attempt_count=failed_attempts,
        runtime_event=runtime_event,
        active_run_id=active_budget_run_id,
    )
    latest_event = events[-1] if events else None
    runtime_health_epoch = _text(dominant.get("event_id")) if dominant is not None else None
    active_run_id = observed_active_run_id if strict_live else None
    last_known_run_id = _last_known_run_id(events, strict_live=strict_live, active_run_id=observed_active_run_id)
    failure_reason = _latest_failure_reason(events, runtime_payload, active_run_id=active_budget_run_id)
    blocking_reasons = list(dict.fromkeys(reason for reason in blocking_reasons if reason))
    return {
        "schema_version": SCHEMA_VERSION,
        "surface": "runtime_health_snapshot",
        "study_id": study_id,
        "quest_id": quest_id,
        "study_root": str(Path(study_root).expanduser().resolve()),
        "generated_at": _text(latest_event.get("recorded_at")) if latest_event is not None else None,
        "runtime_health_epoch": runtime_health_epoch,
        "desired_runtime_state": {
            "state": "running" if quest_status in _ACTIVE_QUEST_STATUSES else "inactive",
            "reason": "managed_study_runtime_contract",
        },
        "observed_quest_state": {
            "quest_status": quest_status,
            "decision": decision,
            "reason": reason,
        },
        "supervisor_state": supervisor_state,
        "worker_liveness_state": worker_state,
        "active_run_id": active_run_id,
        "last_known_run_id": last_known_run_id,
        "session_ref": _text(runtime_payload.get("session_ref")),
        "attempt_state": attempt_state,
        "attempt_count": attempt_count,
        "run_attempt_phase": _text(runtime_payload.get("run_attempt_phase")) or attempt_state,
        "failure_reason": failure_reason,
        "backoff_until": _text(runtime_payload.get("backoff_until")),
        "retry_budget_remaining": retry_budget_remaining,
        "canonical_runtime_action": canonical_runtime_action,
        "blocking_reasons": blocking_reasons,
        "allowed_controller_actions": _allowed_controller_actions(canonical_runtime_action=canonical_runtime_action),
        "dominant_runtime_refs": [_authority_ref(dominant)] if dominant is not None else [],
        "projection_invalidations": _projection_invalidations(
            events=events,
            dominant=dominant,
            strict_live=strict_live,
            last_known_run_id=last_known_run_id,
        ),
        "source_signature": _snapshot_source_signature(events),
        "writer_epoch": _text(runtime_payload.get("writer_epoch")) or (
            f"writer::{active_run_id}" if active_run_id is not None else None
        ),
        "event_count": len(events),
        "event_log_path": str(runtime_health_events_path(study_root=study_root)),
    }


def rebuild_runtime_health_snapshot(*, study_root: Path, study_id: str, quest_id: str) -> dict[str, Any]:
    events = [
        event
        for event in read_runtime_health_events(study_root=study_root)
        if event.get("study_id") == study_id and event.get("quest_id") == quest_id
    ]
    return _snapshot_from_events(study_root=study_root, study_id=study_id, quest_id=quest_id, events=events)


def _transient_event(
    *,
    study_id: str,
    quest_id: str,
    event_type: str,
    payload: Mapping[str, Any],
    recorded_at: str,
    sequence: int,
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "event_id": _build_event_id(
            study_id=study_id,
            quest_id=quest_id,
            event_type=event_type,
            payload=payload,
            recorded_at=recorded_at,
            sequence=sequence,
        ),
        "sequence": sequence,
        "study_id": study_id,
        "quest_id": quest_id,
        "event_type": event_type,
        "recorded_at": recorded_at,
        "payload": dict(payload),
        "source_signature": _event_source_signature(event_type, payload),
        "transient": True,
    }


def _candidate_path(value: object) -> Path | None:
    text = _text(value)
    if text is None:
        return None
    return Path(text).expanduser().resolve()


def _launch_report_event_payload(status_payload: Mapping[str, Any]) -> dict[str, Any]:
    direct_report = _mapping(status_payload.get("last_launch_report"))
    launch_report_path = _candidate_path(status_payload.get("launch_report_path"))
    file_report = _read_json(launch_report_path) if launch_report_path is not None else None
    report = direct_report or _mapping(file_report)
    if not report:
        return {}
    active_run_id = _first_text(
        report.get("active_run_id"),
        _mapping(report.get("autonomous_runtime_notice")).get("active_run_id"),
        _mapping(report.get("runtime_liveness_audit")).get("active_run_id"),
    )
    if active_run_id is None and _text(report.get("last_action")) is None:
        return {}
    return {
        "attempt_state": _text(report.get("dispatch_status")) or _text(report.get("status")) or "observed",
        "active_run_id": active_run_id,
        "last_action": _text(report.get("last_action")),
        "summary_ref": str(launch_report_path) if launch_report_path is not None else None,
    }


def _status_payload_runtime_health_events(
    *,
    study_id: str,
    quest_id: str,
    status_payload: Mapping[str, Any],
    recorded_at: str,
    first_sequence: int,
) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    sequence = first_sequence
    facts = resolve_control_plane_facts(status_payload)
    runtime_liveness_audit = _mapping(status_payload.get("runtime_liveness_audit"))
    runtime_audit = _mapping(runtime_liveness_audit.get("runtime_audit"))
    stable_runtime_audit = _stable_runtime_audit(runtime_audit)
    stable_runtime_liveness_audit = _stable_runtime_liveness_audit(runtime_liveness_audit)
    runtime_payload = {
        "quest_status": _text(status_payload.get("quest_status")),
        "decision": _text(status_payload.get("decision")),
        "reason": _text(status_payload.get("reason")),
        "runtime_liveness_status": facts.runtime_liveness_status,
        "worker_running": facts.worker_running,
        "worker_pending": facts.worker_pending,
        "stop_requested": facts.stop_requested,
        "active_run_id": facts.active_run_id if facts.strict_live else None,
        "runtime_audit": stable_runtime_audit or None,
        "runtime_liveness_audit": stable_runtime_liveness_audit or None,
        "liveness_guard_reason": _text(runtime_liveness_audit.get("liveness_guard_reason")),
        "autonomy_slo": _mapping(status_payload.get("autonomy_slo")) or None,
        "progress_freshness": _mapping(status_payload.get("progress_freshness")) or None,
    }
    runtime_payload = {key: value for key, value in runtime_payload.items() if value is not None}
    if runtime_payload:
        sequence += 1
        events.append(
            _transient_event(
                study_id=study_id,
                quest_id=quest_id,
                event_type="runtime_state_observed",
                payload=runtime_payload,
                recorded_at=recorded_at,
                sequence=sequence,
            )
        )

    supervisor_tick_audit = _mapping(status_payload.get("supervisor_tick_audit"))
    if supervisor_tick_audit:
        supervisor_payload = {
            key: value
            for key, value in supervisor_tick_audit.items()
            if key not in _VOLATILE_SUPERVISOR_KEYS
        }
        supervisor_payload["supervisor_tick_status"] = _text(supervisor_tick_audit.get("status"))
        sequence += 1
        events.append(
            _transient_event(
                study_id=study_id,
                quest_id=quest_id,
                event_type="supervisor_tick",
                payload=supervisor_payload,
                recorded_at=recorded_at,
                sequence=sequence,
            )
        )

    launch_payload = _launch_report_event_payload(status_payload)
    if launch_payload:
        sequence += 1
        events.append(
            _transient_event(
                study_id=study_id,
                quest_id=quest_id,
                event_type="launch_attempt",
                payload=launch_payload,
                recorded_at=recorded_at,
                sequence=sequence,
            )
        )

    decision = _text(status_payload.get("decision"))
    if decision in _RECOVERY_DECISIONS:
        event_type = "relaunch_attempt" if decision == "relaunch_stopped" else "recover_attempt"
        sequence += 1
        events.append(
            _transient_event(
                study_id=study_id,
                quest_id=quest_id,
                event_type=event_type,
                payload={
                    "attempt_state": "requested",
                    "decision": decision,
                    "reason": _text(status_payload.get("reason")),
                    "active_run_id": facts.active_run_id if facts.strict_live else None,
                },
                recorded_at=recorded_at,
                sequence=sequence,
            )
        )
    return events


def derive_runtime_health_snapshot_from_status_payload(
    *,
    study_root: Path,
    study_id: str,
    quest_id: str,
    status_payload: Mapping[str, Any],
    recorded_at: str,
) -> dict[str, Any]:
    persisted_events = [
        event
        for event in read_runtime_health_events(study_root=study_root)
        if event.get("study_id") == study_id and event.get("quest_id") == quest_id
    ]
    seen = {
        (str(event.get("event_type") or ""), _source_signature_for_event(event))
        for event in persisted_events
    }
    transient_events = _status_payload_runtime_health_events(
        study_id=study_id,
        quest_id=quest_id,
        status_payload=status_payload,
        recorded_at=recorded_at,
        first_sequence=len(persisted_events),
    )
    deduped_transient_events: list[dict[str, Any]] = []
    for event in transient_events:
        key = (str(event.get("event_type") or "").strip(), _source_signature_for_event(event))
        if key in seen:
            continue
        deduped_transient_events.append(event)
        seen.add(key)
    return _snapshot_from_events(
        study_root=study_root,
        study_id=study_id,
        quest_id=quest_id,
        events=[*persisted_events, *deduped_transient_events],
    )


def materialize_runtime_health_snapshot(*, study_root: Path, study_id: str, quest_id: str) -> Path:
    snapshot = rebuild_runtime_health_snapshot(study_root=study_root, study_id=study_id, quest_id=quest_id)
    path = runtime_health_snapshot_path(study_root=study_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def reconcile_runtime_health_snapshot_from_status_payload(
    *,
    study_root: Path,
    study_id: str,
    quest_id: str,
    status_payload: Mapping[str, Any],
    recorded_at: str,
) -> dict[str, Any]:
    path = runtime_health_events_path(study_root=study_root)
    persisted_events = _read_jsonl(path)
    persisted_for_quest = [
        event
        for event in persisted_events
        if event.get("study_id") == study_id and event.get("quest_id") == quest_id
    ]
    seen = {
        (str(event.get("event_type") or ""), _source_signature_for_event(event))
        for event in persisted_for_quest
    }
    transient_events = _status_payload_runtime_health_events(
        study_id=study_id,
        quest_id=quest_id,
        status_payload=status_payload,
        recorded_at=recorded_at,
        first_sequence=len(persisted_events),
    )
    appended: list[dict[str, Any]] = []
    for event in transient_events:
        event_type = str(event.get("event_type") or "").strip()
        payload = _mapping(event.get("payload"))
        source_signature = _source_signature_for_event(event)
        key = (event_type, source_signature)
        if key in seen:
            continue
        appended.append(
            append_runtime_health_event(
                study_root=study_root,
                study_id=study_id,
                quest_id=quest_id,
                event_type=event_type,
                payload=payload,
                recorded_at=_text(event.get("recorded_at")) or recorded_at,
                source_signature=source_signature,
            )
        )
        seen.add(key)
    snapshot_path = materialize_runtime_health_snapshot(
        study_root=study_root,
        study_id=study_id,
        quest_id=quest_id,
    )
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    return {
        "surface": "runtime_health_reconcile_result",
        "study_id": study_id,
        "quest_id": quest_id,
        "snapshot_path": str(snapshot_path),
        "runtime_health_epoch": _text(snapshot.get("runtime_health_epoch")),
        "source_signature": _text(snapshot.get("source_signature")),
        "writer_epoch": _text(snapshot.get("writer_epoch")),
        "appended_event_count": len(appended),
        "appended_event_ids": [event["event_id"] for event in appended],
        "snapshot": snapshot,
    }
