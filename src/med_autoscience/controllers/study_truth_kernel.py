from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from med_autoscience.controllers.study_truth_kernel_parts import action_policy

SCHEMA_VERSION = 1
EVENT_LOG_RELATIVE_PATH = Path("artifacts") / "truth" / "events.jsonl"
SNAPSHOT_RELATIVE_PATH = Path("artifacts") / "truth" / "latest.json"

TRUTH_EVENT_TYPES = frozenset(
    {
        "task_intake",
        "controller_decision",
        "runtime_native_event",
        "opl_runtime_owner_handoff",
        "publication_gate_eval",
        "quality_review_eval",
        "package_authority_eval",
        "delivery_sync",
        "human_gate",
        "stop_loss",
        "explicit_resume",
        "writer_lock_acquired",
        "writer_lock_released",
    }
)

_VOLATILE_OPL_HANDOFF_AUDIT_KEYS = frozenset(
    {
        "age_seconds",
        "checked_at",
        "generated_at",
        "recorded_at",
        "seconds_since_latest_recorded_at",
        "seconds_since_latest_progress",
    }
)


def truth_events_path(*, study_root: Path) -> Path:
    return Path(study_root).expanduser().resolve() / EVENT_LOG_RELATIVE_PATH


def truth_snapshot_path(*, study_root: Path) -> Path:
    return Path(study_root).expanduser().resolve() / SNAPSHOT_RELATIVE_PATH


def _stable_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _event_id_seed(
    *,
    study_id: str,
    event_type: str,
    payload: Mapping[str, Any],
    recorded_at: str,
    sequence: int,
) -> str:
    return _stable_json(
        {
            "study_id": study_id,
            "event_type": event_type,
            "payload": dict(payload),
            "recorded_at": recorded_at,
            "sequence": sequence,
        }
    )


def _build_event_id(
    *,
    study_id: str,
    event_type: str,
    payload: Mapping[str, Any],
    recorded_at: str,
    sequence: int,
) -> str:
    digest = hashlib.sha256(
        _event_id_seed(
            study_id=study_id,
            event_type=event_type,
            payload=payload,
            recorded_at=recorded_at,
            sequence=sequence,
        ).encode("utf-8")
    ).hexdigest()[:16]
    return f"truth-event-{sequence:06d}-{digest}"


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


def read_truth_events(*, study_root: Path) -> list[dict[str, Any]]:
    return _read_jsonl(truth_events_path(study_root=study_root))


def append_truth_event(
    *,
    study_root: Path,
    study_id: str,
    event_type: str,
    payload: Mapping[str, Any] | None = None,
    recorded_at: str,
    source_signature: str | None = None,
) -> dict[str, Any]:
    event_type_text = str(event_type or "").strip()
    if event_type_text not in TRUTH_EVENT_TYPES:
        raise ValueError(f"unknown study truth event type: {event_type}")
    resolved_payload = dict(payload or {})
    path = truth_events_path(study_root=study_root)
    existing = _read_jsonl(path)
    sequence = len(existing) + 1
    event = {
        "schema_version": SCHEMA_VERSION,
        "event_id": _build_event_id(
            study_id=study_id,
            event_type=event_type_text,
            payload=resolved_payload,
            recorded_at=recorded_at,
            sequence=sequence,
        ),
        "sequence": sequence,
        "study_id": study_id,
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


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _stable_opl_handoff_audit(value: object) -> dict[str, Any]:
    return {
        key: item
        for key, item in _mapping(value).items()
        if key not in _VOLATILE_OPL_HANDOFF_AUDIT_KEYS
    }


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


def _last_payload(events: Iterable[dict[str, Any]], event_type: str) -> dict[str, Any]:
    event = _latest_event(events, event_type)
    return _mapping(event.get("payload")) if event is not None else {}


def _event_summary(event: Mapping[str, Any]) -> str | None:
    payload = _mapping(event.get("payload"))
    return (
        _text(payload.get("summary"))
        or _text(payload.get("controller_stage_note"))
        or _text(payload.get("current_required_action"))
    )


def _event_source_signature(event_type: str, payload: Mapping[str, Any]) -> str:
    digest = hashlib.sha256(
        _stable_json(
            {
                "event_type": event_type,
                "payload": dict(payload),
            }
        ).encode("utf-8")
    ).hexdigest()[:24]
    return f"truth-source::{event_type}::{digest}"


def _source_signature_for_event(event: Mapping[str, Any]) -> str:
    event_type = str(event.get("event_type") or "").strip()
    payload = _mapping(event.get("payload"))
    return _text(event.get("source_signature")) or _event_source_signature(event_type, payload)


def _event_dedupe_keys(event: Mapping[str, Any]) -> set[tuple[str, str]]:
    event_type = str(event.get("event_type") or "").strip()
    keys = {(event_type, _source_signature_for_event(event))}
    payload = _mapping(event.get("payload"))
    if event_type == "task_intake":
        if task_id := _text(payload.get("task_id")):
            keys.add(("task_intake_id", task_id))
        if intervention_event_id := _text(payload.get("intervention_event_id")):
            keys.add(("intervention_event_id", intervention_event_id))
    return keys


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
    return f"truth-snapshot::{digest}"


def _quality_state(events: list[dict[str, Any]], dominant_event: dict[str, Any] | None) -> dict[str, Any]:
    if dominant_event is not None and dominant_event.get("event_type") == "stop_loss":
        return {
            "state": "stop_loss_recommended",
            "summary": _event_summary(dominant_event),
        }
    task = _latest_event(events, "task_intake")
    task_payload = _mapping(task.get("payload")) if task is not None else {}
    closure = _mapping(task_payload.get("quality_closure_truth"))
    if _text(closure.get("state")) == "stop_loss_recommended":
        return {"state": "stop_loss_recommended", "summary": _text(closure.get("summary"))}
    review = _last_payload(events, "quality_review_eval")
    if review:
        return {
            "state": _text(review.get("state")) or _text(review.get("verdict")) or "review_observed",
            "summary": _text(review.get("summary")),
        }
    publication = _last_payload(events, "publication_gate_eval")
    publication_closure = _mapping(publication.get("quality_closure_truth"))
    if publication_closure:
        return {
            "state": _text(publication_closure.get("state")) or "publication_gate_observed",
            "route_target": _text(publication_closure.get("route_target")),
            "summary": _text(publication_closure.get("summary")),
        }
    return {"state": "unknown", "summary": None}


def _publication_gate_state(events: list[dict[str, Any]]) -> dict[str, Any]:
    payload = _last_payload(events, "publication_gate_eval")
    if not payload:
        return {"state": "not_observed", "current_required_action": None}
    return {
        "state": _text(payload.get("status")) or "observed",
        "current_required_action": _text(payload.get("current_required_action")),
        "same_line_route_truth": _mapping(payload.get("same_line_route_truth")) or None,
    }


def _delivery_state(events: list[dict[str, Any]]) -> dict[str, Any]:
    payload = _last_payload(events, "delivery_sync")
    if not payload:
        return {"state": "not_observed"}
    return {
        "state": _text(payload.get("state")) or _text(payload.get("delivery_state")) or "observed",
        "source_signature": _text(payload.get("source_signature")),
    }


def _writer_state(events: list[dict[str, Any]]) -> dict[str, Any]:
    writer_epoch: str | None = None
    active_run_id: str | None = None
    locked = False
    for event in events:
        payload = _mapping(event.get("payload"))
        if event.get("event_type") == "writer_lock_acquired":
            writer_epoch = _text(payload.get("writer_epoch")) or _text(event.get("event_id"))
            active_run_id = _text(payload.get("active_run_id"))
            locked = True
        elif event.get("event_type") == "writer_lock_released":
            release_epoch = _text(payload.get("writer_epoch"))
            if release_epoch is None or release_epoch == writer_epoch:
                writer_epoch = None
                active_run_id = None
                locked = False
    return {
        "locked": locked,
        "writer_epoch": writer_epoch,
        "active_run_id": active_run_id,
    }


def _package_state(events: list[dict[str, Any]], writer_state: Mapping[str, Any]) -> dict[str, Any]:
    payload = _last_payload(events, "package_authority_eval")
    if not payload:
        return {
            "authority_state": "not_observed",
            "writer_epoch": _text(writer_state.get("writer_epoch")),
            "source_signature": None,
        }
    status = (
        _text(payload.get("submission_minimal_authority_status"))
        or _text(payload.get("current_package_status"))
        or _text(payload.get("authority_state"))
        or "observed"
    )
    if writer_state.get("locked") and status in {"current", "fresh"}:
        authority_state = "provisionally_current_for_epoch"
    else:
        authority_state = "current" if status == "fresh" else status
    return {
        "authority_state": authority_state,
        "submission_minimal_authority_status": _text(payload.get("submission_minimal_authority_status")),
        "current_package_status": _text(payload.get("current_package_status")),
        "writer_epoch": _text(writer_state.get("writer_epoch")),
        "source_signature": _text(payload.get("source_signature"))
        or _text(payload.get("submission_minimal_evaluated_source_signature")),
    }


def _execution_owner_and_state(
    events: list[dict[str, Any]],
    *,
    dominant_event: Mapping[str, Any] | None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    owner = {"owner": "mas", "runtime_control_owner": "one-person-lab", "active_run_id": None}
    state = {"state": "unknown", "quest_status": None, "reason": None}
    for event in events:
        payload = _mapping(event.get("payload"))
        if event.get("event_type") == "runtime_native_event":
            state = {
                "state": _text(payload.get("state")) or _text(payload.get("quest_status")) or "runtime_observed",
                "quest_status": _text(payload.get("quest_status")),
                "reason": _text(payload.get("reason")),
            }
        elif event.get("event_type") == "opl_runtime_owner_handoff":
            guard = _mapping(payload.get("execution_owner_guard"))
            supervisor_state = _mapping(payload.get("publication_supervisor_state"))
            if guard.get("supervisor_only") is True:
                owner = {
                    "owner": "one-person-lab",
                    "runtime_control_owner": "one-person-lab",
                    "stage_attempt_owner": "one-person-lab",
                    "mas_role": "domain_authority_refs_only",
                    "active_run_id": _text(guard.get("active_run_id")) or _text(payload.get("active_run_id")),
                }
                state = {
                    "state": "opl_handoff_required",
                    "quest_status": _text(payload.get("quest_status")) or "running",
                    "reason": _text(supervisor_state.get("current_required_action")),
                }
        elif event.get("event_type") in {"task_intake", "explicit_resume"}:
            action = _text(payload.get("current_required_action"))
            if action in {
                "resume_same_study_line",
                "resume_runtime",
                "relaunch_same_study_line",
                "authorize_clean_reproducible_model_rebuild",
            }:
                state = {
                    "state": "reactivation_requested",
                    "quest_status": state.get("quest_status"),
                    "reason": _event_summary(event),
                }
    if dominant_event is not None and dominant_event.get("event_type") in {"task_intake", "explicit_resume"}:
        payload = _mapping(dominant_event.get("payload"))
        action = _text(payload.get("current_required_action"))
        if action in {
            "resume_same_study_line",
            "resume_runtime",
            "relaunch_same_study_line",
            "authorize_clean_reproducible_model_rebuild",
        }:
            state = {
                "state": "reactivation_requested",
                "quest_status": state.get("quest_status"),
                "reason": _event_summary(dominant_event),
            }
    return owner, state


def _parsed_recorded_at(value: object) -> datetime:
    text = _text(value)
    if text is None:
        return datetime.min.replace(tzinfo=timezone.utc)
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return datetime.min.replace(tzinfo=timezone.utc)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _sequence_number(event: Mapping[str, Any], fallback: int) -> int:
    try:
        return int(event.get("sequence") or fallback)
    except (TypeError, ValueError):
        return fallback


def _latest_authority_candidate(events: Iterable[dict[str, Any]]) -> dict[str, Any] | None:
    candidates = list(events)
    if not candidates:
        return None
    return max(
        enumerate(candidates),
        key=lambda item: (
            _parsed_recorded_at(item[1].get("recorded_at")),
            _sequence_number(item[1], item[0]),
            item[0],
        ),
    )[1]


def _dominant_event(events: list[dict[str, Any]]) -> dict[str, Any] | None:
    stop_loss_candidates: list[dict[str, Any]] = []
    for event in events:
        if event.get("event_type") == "stop_loss":
            stop_loss_candidates.append(event)
            continue
        payload = _mapping(event.get("payload"))
        closure = _mapping(payload.get("quality_closure_truth"))
        if event.get("event_type") == "task_intake" and _text(closure.get("state")) == "stop_loss_recommended":
            stop_loss_candidates.append(event)
    if stop_loss := _latest_authority_candidate(stop_loss_candidates):
        return stop_loss
    reactivation_candidates: list[dict[str, Any]] = []
    for event in events:
        payload = _mapping(event.get("payload"))
        if event.get("event_type") in {"task_intake", "explicit_resume"}:
            action = _text(payload.get("current_required_action"))
            task_intake_kind = _text(payload.get("task_intake_kind"))
            reactivation = _mapping(payload.get("reactivation_policy"))
            revision = _mapping(payload.get("revision_intake"))
            if (
                action in {"resume_same_study_line", "resume_runtime", "relaunch_same_study_line"}
                or action == "authorize_clean_reproducible_model_rebuild"
                or task_intake_kind == "methodology_rebuild_authorization"
                or reactivation.get("same_study_line") is True
                or _text(revision.get("kind")) == "reviewer_revision"
            ):
                reactivation_candidates.append(event)
    if reactivation := _latest_authority_candidate(reactivation_candidates):
        return reactivation
    handoff_candidates: list[dict[str, Any]] = []
    for event in events:
        payload = _mapping(event.get("payload"))
        guard = _mapping(payload.get("execution_owner_guard"))
        supervisor = _mapping(payload.get("publication_supervisor_state"))
        if (
            event.get("event_type") == "opl_runtime_owner_handoff"
            and (guard.get("supervisor_only") is True or supervisor.get("bundle_tasks_downstream_only") is True)
        ):
            handoff_candidates.append(event)
    if handoff := _latest_authority_candidate(handoff_candidates):
        return handoff
    eval_candidates: list[dict[str, Any]] = []
    for event in events:
        if event.get("event_type") in {"publication_gate_eval", "quality_review_eval", "package_authority_eval"}:
            eval_candidates.append(event)
    if eval_event := _latest_authority_candidate(eval_candidates):
        return eval_event
    return events[-1] if events else None


def _projection_invalidations(events: list[dict[str, Any]], dominant_event: dict[str, Any] | None) -> list[dict[str, Any]]:
    if dominant_event is None:
        return []
    dominant_type = str(dominant_event.get("event_type") or "")
    dominant_id = _text(dominant_event.get("event_id"))
    weaker_by_dominance = {
        "stop_loss": {
            "publication_gate_eval",
            "quality_review_eval",
            "package_authority_eval",
            "delivery_sync",
            "runtime_native_event",
        },
        "task_intake": {
            "publication_gate_eval",
            "package_authority_eval",
            "delivery_sync",
            "runtime_native_event",
        },
        "explicit_resume": {
            "publication_gate_eval",
            "package_authority_eval",
            "delivery_sync",
            "runtime_native_event",
        },
        "opl_runtime_owner_handoff": {
            "package_authority_eval",
            "delivery_sync",
        },
    }.get(dominant_type, set())
    invalidations: list[dict[str, Any]] = []
    seen: set[str] = set()
    for event in events:
        event_type = str(event.get("event_type") or "")
        event_id = _text(event.get("event_id"))
        if event_id == dominant_id or event_type not in weaker_by_dominance or event_type in seen:
            continue
        invalidations.append(
            {
                "invalidated_surface": event_type,
                "invalidated_event_id": event_id,
                "invalidated_by_event_id": dominant_id,
                "reason": f"{dominant_type}_dominates_{event_type}",
            }
        )
        seen.add(event_type)
    return invalidations


def _snapshot_from_events(*, study_root: Path, study_id: str, events: list[dict[str, Any]]) -> dict[str, Any]:
    dominant = _dominant_event(events)
    writer_state = _writer_state(events)
    owner, execution_state = _execution_owner_and_state(events, dominant_event=dominant)
    latest_event = events[-1] if events else None
    authority_epoch = _text(dominant.get("event_id")) if dominant is not None else None
    generated_at = _text(latest_event.get("recorded_at")) if latest_event is not None else None
    snapshot = {
        "schema_version": SCHEMA_VERSION,
        "surface": "study_truth_snapshot",
        "study_id": study_id,
        "study_root": str(Path(study_root).expanduser().resolve()),
        "generated_at": generated_at,
        "truth_epoch": authority_epoch,
        "authority_epoch": authority_epoch,
        "execution_state": execution_state,
        "execution_owner": owner,
        "active_run_id": owner.get("active_run_id") or writer_state.get("active_run_id"),
        "quality_state": _quality_state(events, dominant),
        "publication_gate_state": _publication_gate_state(events),
        "package_state": _package_state(events, writer_state),
        "delivery_state": _delivery_state(events),
        "writer_epoch": _text(writer_state.get("writer_epoch")),
        "source_signature": _snapshot_source_signature(events),
        "canonical_next_action": action_policy.canonical_next_action(dominant),
        "blocking_reasons": action_policy.blocking_reasons(events),
        "dominant_authority_refs": [_authority_ref(dominant)] if dominant is not None else [],
        "projection_invalidations": _projection_invalidations(events, dominant),
        "allowed_controller_actions": action_policy.allowed_controller_actions(events),
        "event_count": len(events),
        "event_log_path": str(truth_events_path(study_root=study_root)),
    }
    return snapshot


def rebuild_truth_snapshot(*, study_root: Path, study_id: str) -> dict[str, Any]:
    events = [event for event in read_truth_events(study_root=study_root) if event.get("study_id") == study_id]
    return _snapshot_from_events(study_root=study_root, study_id=study_id, events=events)


def _transient_event(
    *,
    study_id: str,
    event_type: str,
    payload: Mapping[str, Any],
    recorded_at: str,
    sequence: int,
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "event_id": _build_event_id(
            study_id=study_id,
            event_type=event_type,
            payload=payload,
            recorded_at=recorded_at,
            sequence=sequence,
        ),
        "sequence": sequence,
        "study_id": study_id,
        "event_type": event_type,
        "recorded_at": recorded_at,
        "payload": dict(payload),
        "source_signature": _event_source_signature(event_type, payload),
        "transient": True,
    }


def _status_payload_truth_events(
    *,
    study_id: str,
    status_payload: Mapping[str, Any],
    recorded_at: str,
    first_sequence: int,
) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    sequence = first_sequence
    quest_status = _text(status_payload.get("quest_status"))
    decision = _text(status_payload.get("decision"))
    reason = _text(status_payload.get("reason"))
    active_run_id = _text(status_payload.get("active_run_id"))
    if quest_status is not None or decision is not None or reason is not None:
        sequence += 1
        events.append(
            _transient_event(
                study_id=study_id,
                event_type="runtime_native_event",
                payload={
                    "quest_status": quest_status,
                    "decision": decision,
                    "reason": reason,
                    "active_run_id": active_run_id,
                },
                recorded_at=recorded_at,
                sequence=sequence,
            )
        )
    execution_owner_guard = _mapping(status_payload.get("execution_owner_guard"))
    publication_supervisor_state = _mapping(status_payload.get("publication_supervisor_state"))
    opl_handoff_audit = _stable_opl_handoff_audit(
        status_payload.get("opl_runtime_owner_handoff")
        or status_payload.get("opl_current_control_state_handoff")
        or status_payload.get("supervisor_tick_audit")
    )
    active_run_id = active_run_id or _text(execution_owner_guard.get("active_run_id"))
    if execution_owner_guard or publication_supervisor_state or opl_handoff_audit:
        sequence += 1
        events.append(
            _transient_event(
                study_id=study_id,
                event_type="opl_runtime_owner_handoff",
                payload={
                    "execution_owner_guard": execution_owner_guard,
                    "publication_supervisor_state": publication_supervisor_state,
                    "opl_handoff_audit": opl_handoff_audit,
                    "quest_status": quest_status,
                },
                recorded_at=recorded_at,
                sequence=sequence,
            )
        )
    if execution_owner_guard.get("supervisor_only") is True and active_run_id is not None:
        sequence += 1
        events.append(
            _transient_event(
                study_id=study_id,
                event_type="writer_lock_acquired",
                payload={
                    "writer_epoch": _text(status_payload.get("writer_epoch")) or f"writer::{active_run_id}",
                    "active_run_id": active_run_id,
                    "source": "execution_owner_guard",
                },
                recorded_at=recorded_at,
                sequence=sequence,
            )
        )
    package_payload = _package_authority_event_payload(status_payload)
    if package_payload:
        sequence += 1
        events.append(
            _transient_event(
                study_id=study_id,
                event_type="package_authority_eval",
                payload=package_payload,
                recorded_at=recorded_at,
                sequence=sequence,
            )
        )
    task_intake_payload = _latest_task_intake_payload(study_root=Path(status_payload.get("study_root") or ""))
    task_intake_event_payload = _task_intake_event_payload(task_intake_payload)
    if task_intake_event_payload:
        sequence += 1
        events.append(
            _transient_event(
                study_id=study_id,
                event_type="task_intake",
                payload=task_intake_event_payload,
                recorded_at=_text(task_intake_payload.get("emitted_at")) or recorded_at,
                sequence=sequence,
            )
        )
    supervisor_phase = _text(publication_supervisor_state.get("supervisor_phase"))
    supervisor_action = _text(publication_supervisor_state.get("current_required_action"))
    if reason == "publishability_stop_loss_recommended" or supervisor_phase == "stop_loss" or supervisor_action == "stop_runtime":
        sequence += 1
        events.append(
            _transient_event(
                study_id=study_id,
                event_type="stop_loss",
                payload={
                    "summary": _text(publication_supervisor_state.get("controller_stage_note"))
                    or "publishability stop-loss recommended",
                    "controller_action": "stop_runtime",
                    "reason": reason,
                },
                recorded_at=recorded_at,
                sequence=sequence,
            )
        )
    return events


def _package_authority_event_payload(status_payload: Mapping[str, Any]) -> dict[str, Any]:
    package_state = _mapping(status_payload.get("package_state"))
    payload = {
        "submission_minimal_authority_status": _text(
            status_payload.get("submission_minimal_authority_status")
            or package_state.get("submission_minimal_authority_status")
        ),
        "submission_minimal_evaluated_source_signature": _text(
            status_payload.get("submission_minimal_evaluated_source_signature")
            or package_state.get("submission_minimal_evaluated_source_signature")
        ),
        "submission_minimal_authority_source_signature": _text(
            status_payload.get("submission_minimal_authority_source_signature")
            or package_state.get("submission_minimal_authority_source_signature")
        ),
        "current_package_status": _text(status_payload.get("current_package_status") or package_state.get("current_package_status")),
        "current_package_source_signature": _text(
            status_payload.get("current_package_source_signature") or package_state.get("current_package_source_signature")
        ),
        "current_package_authority_source_signature": _text(
            status_payload.get("current_package_authority_source_signature")
            or package_state.get("current_package_authority_source_signature")
        ),
        "authority_state": _text(status_payload.get("authority_state") or package_state.get("authority_state")),
        "source_signature": _text(
            status_payload.get("source_signature")
            or status_payload.get("current_package_source_signature")
            or status_payload.get("submission_minimal_evaluated_source_signature")
            or package_state.get("source_signature")
            or package_state.get("current_package_source_signature")
            or package_state.get("submission_minimal_evaluated_source_signature")
        ),
    }
    return {key: value for key, value in payload.items() if value is not None}


def _latest_task_intake_payload(*, study_root: Path) -> dict[str, Any]:
    if not str(study_root).strip():
        return {}
    path = Path(study_root).expanduser() / "artifacts" / "controller" / "task_intake" / "latest.json"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return dict(payload) if isinstance(payload, Mapping) else {}


def _task_intake_event_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    if not payload:
        return {}
    revision_intake = _mapping(payload.get("revision_intake"))
    reactivation_policy = _mapping(payload.get("reactivation_policy"))
    task_intake_kind = _text(payload.get("task_intake_kind")) or _text(payload.get("intake_kind"))
    task_intent = _text(payload.get("task_intent")) or ""
    text = " ".join(
        item
        for item in (
            task_intent,
            _text(payload.get("summary")) or "",
            " ".join(str(item) for item in payload.get("constraints", []) if item is not None)
            if isinstance(payload.get("constraints"), list)
            else "",
        )
        if item
    ).lower()
    legacy_reviewer_revision = (
        "reviewer_revision" in text
        or "reviewer revision" in text
        or ("reviewer" in text and "revision" in text)
        or "审稿" in text
        or "返修" in text
    )
    if task_intake_kind == "methodology_rebuild_authorization":
        current_required_action = "authorize_clean_reproducible_model_rebuild"
        quality_closure_truth = None
        if not reactivation_policy:
            reactivation_policy = {
                "same_study_line": True,
                "route_target": "analysis-campaign",
                "next_owner": "provenance_limited_harmonization_owner",
                "next_work_unit": "provenance_limited_harmonization_audit",
            }
    elif "stop-loss" in text or "stop loss" in text or "止损" in text:
        current_required_action = "stop_runtime"
        quality_closure_truth = {"state": "stop_loss_recommended", "summary": _text(payload.get("task_intent"))}
    elif (
        _text(revision_intake.get("kind")) == "reviewer_revision"
        or reactivation_policy.get("same_study_line") is True
        or legacy_reviewer_revision
    ):
        current_required_action = "resume_same_study_line"
        quality_closure_truth = None
    else:
        current_required_action = _text(payload.get("current_required_action"))
        quality_closure_truth = None
    if current_required_action is None and not revision_intake and not reactivation_policy:
        return {}
    event_payload = {
        "task_id": _text(payload.get("task_id")),
        "task_intake_kind": task_intake_kind,
        "revision_intake": revision_intake or None,
        "reactivation_policy": reactivation_policy or {"same_study_line": True}
        if current_required_action == "resume_same_study_line"
        else reactivation_policy or None,
        "current_required_action": current_required_action,
        "summary": _text(payload.get("task_intent")) or _text(payload.get("summary")),
    }
    if quality_closure_truth is not None:
        event_payload["quality_closure_truth"] = quality_closure_truth
    return event_payload


def derive_truth_snapshot_from_status_payload(
    *,
    study_root: Path,
    study_id: str,
    status_payload: Mapping[str, Any],
    recorded_at: str,
) -> dict[str, Any]:
    persisted_events = [
        event for event in read_truth_events(study_root=study_root) if event.get("study_id") == study_id
    ]
    seen = set().union(*(_event_dedupe_keys(event) for event in persisted_events)) if persisted_events else set()
    transient_events = _status_payload_truth_events(
        study_id=study_id,
        status_payload=status_payload,
        recorded_at=recorded_at,
        first_sequence=len(persisted_events),
    )
    deduped_transient_events: list[dict[str, Any]] = []
    for event in transient_events:
        keys = _event_dedupe_keys(event)
        if keys & seen:
            continue
        deduped_transient_events.append(event)
        seen.update(keys)
    return _snapshot_from_events(
        study_root=study_root,
        study_id=study_id,
        events=[*persisted_events, *deduped_transient_events],
    )


def materialize_truth_snapshot(*, study_root: Path, study_id: str) -> Path:
    snapshot = rebuild_truth_snapshot(study_root=study_root, study_id=study_id)
    path = truth_snapshot_path(study_root=study_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def reconcile_truth_snapshot_from_status_payload(
    *,
    study_root: Path,
    study_id: str,
    status_payload: Mapping[str, Any],
    recorded_at: str,
) -> dict[str, Any]:
    path = truth_events_path(study_root=study_root)
    persisted_events = _read_jsonl(path)
    persisted_for_study = [event for event in persisted_events if event.get("study_id") == study_id]
    seen = set().union(*(_event_dedupe_keys(event) for event in persisted_for_study)) if persisted_for_study else set()
    transient_events = _status_payload_truth_events(
        study_id=study_id,
        status_payload=status_payload,
        recorded_at=recorded_at,
        first_sequence=len(persisted_events),
    )
    appended: list[dict[str, Any]] = []
    for event in transient_events:
        event_type = str(event.get("event_type") or "").strip()
        payload = _mapping(event.get("payload"))
        source_signature = _source_signature_for_event(event)
        keys = _event_dedupe_keys(event)
        if keys & seen:
            continue
        appended.append(
            append_truth_event(
                study_root=study_root,
                study_id=study_id,
                event_type=event_type,
                payload=payload,
                recorded_at=_text(event.get("recorded_at")) or recorded_at,
                source_signature=source_signature,
            )
        )
        seen.update(keys)
    snapshot_path = materialize_truth_snapshot(study_root=study_root, study_id=study_id)
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    return {
        "surface": "study_truth_reconcile_result",
        "study_id": study_id,
        "snapshot_path": str(snapshot_path),
        "truth_epoch": _text(snapshot.get("truth_epoch")),
        "source_signature": _text(snapshot.get("source_signature")),
        "writer_epoch": _text(snapshot.get("writer_epoch")),
        "appended_event_count": len(appended),
        "appended_event_ids": [event["event_id"] for event in appended],
        "snapshot": snapshot,
    }
