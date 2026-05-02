from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.controllers.control_identity import ControlWorkUnitIdentity
from med_autoscience.controllers import work_unit_ledger


_UPSTREAM_REPAIR_UNITS = frozenset(
    {
        "analysis_claim_evidence_repair",
        "manuscript_story_repair",
        "figure_results_trace_repair",
        "treatment_gap_reporting_repair",
    }
)
_OUTER_LOOP_WAKEUP_SOURCE = "runtime_watch_outer_loop_wakeup"
_LEDGER_EXECUTED_EVENT_TYPES = frozenset({"closed"})
_SPECIFICITY_UNIT_ID = "gate_needs_specificity"
_SPECIFICITY_ACTION_TYPE = "request_gate_specificity"
MAX_OPEN_REDRIVE_ATTEMPTS = 3
_MEANINGFUL_RESULT_ARTIFACT_KEYS = (
    "publication_eval_latest",
    "publication_gate_latest",
)


def _non_empty_text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    text = value.strip()
    return text or None


def _read_json_object(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else None


def _wakeup_latest_path(study_root: Path) -> Path:
    return Path(study_root).expanduser().resolve() / "artifacts" / "runtime" / "runtime_watch_wakeup" / "latest.json"


def dispatch_key(tick_request: Mapping[str, Any]) -> str | None:
    work_unit_fingerprint = _non_empty_text(tick_request.get("work_unit_fingerprint"))
    next_work_unit = tick_request.get("next_work_unit")
    unit_id = (
        _non_empty_text(next_work_unit.get("unit_id"))
        if isinstance(next_work_unit, Mapping)
        else None
    )
    controller_actions = tick_request.get("controller_actions")
    first_controller_action = (
        controller_actions[0]
        if isinstance(controller_actions, list) and controller_actions and isinstance(controller_actions[0], Mapping)
        else {}
    )
    action_type = _non_empty_text(first_controller_action.get("action_type"))
    if action_type is None and unit_id == _SPECIFICITY_UNIT_ID:
        action_type = _SPECIFICITY_ACTION_TYPE
    if work_unit_fingerprint is None or unit_id is None or action_type is None:
        return None
    return f"{work_unit_fingerprint}::{unit_id}::{action_type}"


def identity_from_tick_request(
    *,
    study_id: str,
    quest_id: str | None,
    tick_request: Mapping[str, Any],
) -> ControlWorkUnitIdentity | None:
    work_unit_fingerprint = _non_empty_text(tick_request.get("work_unit_fingerprint"))
    next_work_unit = tick_request.get("next_work_unit")
    unit_id = (
        _non_empty_text(next_work_unit.get("unit_id"))
        if isinstance(next_work_unit, Mapping)
        else None
    )
    lane = (
        _non_empty_text(next_work_unit.get("lane"))
        if isinstance(next_work_unit, Mapping)
        else None
    )
    controller_actions = tick_request.get("controller_actions")
    first_controller_action = (
        controller_actions[0]
        if isinstance(controller_actions, list) and controller_actions and isinstance(controller_actions[0], Mapping)
        else {}
    )
    action_type = _non_empty_text(first_controller_action.get("action_type"))
    if action_type is None and unit_id == _SPECIFICITY_UNIT_ID:
        action_type = _SPECIFICITY_ACTION_TYPE
    if work_unit_fingerprint is None or unit_id is None or lane is None or action_type is None:
        return None
    return ControlWorkUnitIdentity(
        domain="publication-work-unit",
        study_id=study_id,
        quest_id=quest_id,
        lane=lane,
        unit_id=unit_id,
        action_type=action_type,
        effective_blockers=(work_unit_fingerprint,),
        fingerprint_override=work_unit_fingerprint,
    )


def outer_loop_wakeup_inputs_unchanged(audit: Mapping[str, Any]) -> bool:
    if _non_empty_text(audit.get("dispatch_cause")) != "input_unchanged":
        return False
    return _non_empty_text(audit.get("previous_outcome")) in {
        "no_request",
        "skipped_matching_decision",
        "skipped_unchanged_inputs",
    }


def append_ledger_event(
    *,
    study_root: Path,
    status_payload: Mapping[str, Any],
    tick_request: Mapping[str, Any],
    event_type: str,
    wakeup_audit: Mapping[str, Any],
    default_recorded_at: str,
) -> None:
    identity = identity_from_tick_request(
        study_id=_non_empty_text(status_payload.get("study_id")) or Path(study_root).name,
        quest_id=_non_empty_text(status_payload.get("quest_id")),
        tick_request=tick_request,
    )
    if identity is None:
        return
    recorded_at = _non_empty_text(wakeup_audit.get("recorded_at")) or default_recorded_at
    work_unit_ledger.append_event(
        study_root=study_root,
        identity=identity,
        event_type=event_type,
        payload={
            "source": _OUTER_LOOP_WAKEUP_SOURCE,
            "wakeup_outcome": _non_empty_text(wakeup_audit.get("outcome")),
            "wakeup_reason": _non_empty_text(wakeup_audit.get("reason")),
            **(
                {"specificity_questions": list(wakeup_audit.get("specificity_questions") or [])}
                if isinstance(wakeup_audit.get("specificity_questions"), list)
                else {}
            ),
        },
        recorded_at=recorded_at,
    )


def _unit_dispatch_suffix(tick_request: Mapping[str, Any]) -> tuple[str | None, str | None]:
    next_work_unit = tick_request.get("next_work_unit")
    unit_id = (
        _non_empty_text(next_work_unit.get("unit_id"))
        if isinstance(next_work_unit, Mapping)
        else None
    )
    controller_actions = tick_request.get("controller_actions")
    first_controller_action = (
        controller_actions[0]
        if isinstance(controller_actions, list) and controller_actions and isinstance(controller_actions[0], Mapping)
        else {}
    )
    action_type = _non_empty_text(first_controller_action.get("action_type"))
    if action_type is None and unit_id == _SPECIFICITY_UNIT_ID:
        action_type = _SPECIFICITY_ACTION_TYPE
    if unit_id is None or action_type is None:
        return None, None
    return unit_id, f"::{unit_id}::{action_type}"


def needs_specificity_request(tick_request: Mapping[str, Any]) -> bool:
    next_work_unit = tick_request.get("next_work_unit")
    if not isinstance(next_work_unit, Mapping):
        return False
    return _non_empty_text(next_work_unit.get("unit_id")) == _SPECIFICITY_UNIT_ID


def _ledger_has_executed_dispatch(
    *,
    study_root: Path,
    dispatch_key_value: str,
    unit_id: str | None,
    suffix: str | None,
) -> bool:
    exact_event = work_unit_ledger.latest_event(study_root=study_root, dispatch_key=dispatch_key_value)
    if (
        isinstance(exact_event, Mapping)
        and _non_empty_text(exact_event.get("event_type")) in _LEDGER_EXECUTED_EVENT_TYPES
        and _closed_event_has_result_evidence(exact_event)
    ):
        return True
    return False


def active_platform_repair_required(
    *,
    study_root: Path,
    tick_request: Mapping[str, Any],
) -> tuple[bool, str | None, int | None]:
    work_unit_dispatch_key = dispatch_key(tick_request)
    if work_unit_dispatch_key is None:
        return False, None, None
    latest_event = work_unit_ledger.latest_event(study_root=study_root, dispatch_key=work_unit_dispatch_key)
    if not isinstance(latest_event, Mapping):
        return False, work_unit_dispatch_key, None
    if _non_empty_text(latest_event.get("event_type")) != "platform_repair_required":
        return False, work_unit_dispatch_key, None
    payload = latest_event.get("payload")
    attempt_count = None
    if isinstance(payload, Mapping):
        raw_attempt_count = payload.get("redrive_attempt_count")
        if isinstance(raw_attempt_count, int):
            attempt_count = raw_attempt_count
    return True, work_unit_dispatch_key, attempt_count


def _artifact_payload(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _artifact_signature(value: Mapping[str, Any]) -> str | None:
    for key in ("sha256", "stable_payload_sha256"):
        signature = _non_empty_text(value.get(key))
        if signature is not None:
            return signature
    if value.get("exists") is True:
        size = value.get("size")
        mtime_ns = value.get("mtime_ns")
        if size is not None or mtime_ns is not None:
            return f"size:{size}:mtime_ns:{mtime_ns}"
    return None


def _meaningful_artifact_delta_evidence(
    *,
    previous_wakeup: Mapping[str, Any],
    current_wakeup: Mapping[str, Any],
) -> dict[str, Any] | None:
    previous_artifacts = _artifact_payload(_artifact_payload(previous_wakeup.get("watched_inputs")).get("artifacts"))
    current_artifacts = _artifact_payload(_artifact_payload(current_wakeup.get("watched_inputs")).get("artifacts"))
    deltas: list[dict[str, Any]] = []
    for key in _MEANINGFUL_RESULT_ARTIFACT_KEYS:
        previous_artifact = _artifact_payload(previous_artifacts.get(key))
        current_artifact = _artifact_payload(current_artifacts.get(key))
        current_signature = _artifact_signature(current_artifact)
        if current_artifact.get("exists") is not True or current_signature is None:
            continue
        previous_signature = _artifact_signature(previous_artifact)
        if previous_signature == current_signature:
            continue
        deltas.append(
            {
                "artifact_key": key,
                "artifact_ref": _non_empty_text(current_artifact.get("path")),
                "fingerprint_before": previous_signature,
                "fingerprint_after": current_signature,
            }
        )
    if not deltas:
        return None
    evidence: dict[str, Any] = {
        "artifact_delta_ref": next(
            (item["artifact_ref"] for item in deltas if _non_empty_text(item.get("artifact_ref")) is not None),
            None,
        ),
        "meaningful_artifact_deltas": deltas,
    }
    by_key = {str(item["artifact_key"]): item for item in deltas}
    publication_eval_delta = by_key.get("publication_eval_latest")
    if publication_eval_delta is not None:
        evidence["publication_eval_fingerprint_before"] = publication_eval_delta["fingerprint_before"]
        evidence["publication_eval_fingerprint_after"] = publication_eval_delta["fingerprint_after"]
    publication_gate_delta = by_key.get("publication_gate_latest")
    if publication_gate_delta is not None:
        evidence["gate_fingerprint_before"] = publication_gate_delta["fingerprint_before"]
        evidence["gate_fingerprint_after"] = publication_gate_delta["fingerprint_after"]
    return evidence


def close_stale_platform_repair_if_meaningful_delta(
    *,
    study_root: Path,
    status_payload: Mapping[str, Any],
    tick_request: Mapping[str, Any],
    wakeup_audit: Mapping[str, Any],
    default_recorded_at: str,
) -> dict[str, Any] | None:
    work_unit_dispatch_key = dispatch_key(tick_request)
    if work_unit_dispatch_key is None:
        return None
    latest_event = work_unit_ledger.latest_event(study_root=study_root, dispatch_key=work_unit_dispatch_key)
    if not isinstance(latest_event, Mapping):
        return None
    if _non_empty_text(latest_event.get("event_type")) != "platform_repair_required":
        return None
    previous_wakeup = _read_json_object(_wakeup_latest_path(study_root)) or {}
    if _non_empty_text(previous_wakeup.get("outcome")) != "platform_repair_required":
        return None
    if _non_empty_text(previous_wakeup.get("work_unit_dispatch_key")) != work_unit_dispatch_key:
        return None
    if _non_empty_text(wakeup_audit.get("dispatch_cause")) != "input_changed":
        return None
    evidence = _meaningful_artifact_delta_evidence(
        previous_wakeup=previous_wakeup,
        current_wakeup=wakeup_audit,
    )
    if evidence is None:
        return None
    identity = identity_from_tick_request(
        study_id=_non_empty_text(status_payload.get("study_id")) or Path(study_root).name,
        quest_id=_non_empty_text(status_payload.get("quest_id")),
        tick_request=tick_request,
    )
    if identity is None:
        return None
    return work_unit_ledger.append_event(
        study_root=study_root,
        identity=identity,
        event_type="closed",
        payload={
            "source": _OUTER_LOOP_WAKEUP_SOURCE,
            "wakeup_outcome": "closed",
            "wakeup_reason": "prior platform repair requirement superseded by meaningful artifact delta",
            "closure_reason": "meaningful_artifact_delta_after_platform_repair",
            "previous_platform_repair_event_id": _non_empty_text(latest_event.get("event_id")),
            **evidence,
        },
        recorded_at=_non_empty_text(wakeup_audit.get("recorded_at")) or default_recorded_at,
    )


def open_redrive_attempt_count(
    *,
    study_root: Path,
    dispatch_key_value: str,
) -> int:
    count = 0
    for event in work_unit_ledger.read_events(study_root=study_root):
        identity = event.get("identity")
        if not isinstance(identity, Mapping) or identity.get("dispatch_key") != dispatch_key_value:
            continue
        event_type = _non_empty_text(event.get("event_type"))
        if event_type in {"closed", "needs_specificity", "superseded"}:
            count = 0
            continue
        if event_type == "dispatched":
            count += 1
    return count


def redrive_budget_exhausted(
    *,
    study_root: Path,
    tick_request: Mapping[str, Any],
    max_attempts: int = MAX_OPEN_REDRIVE_ATTEMPTS,
) -> tuple[bool, str | None, int]:
    work_unit_dispatch_key = dispatch_key(tick_request)
    if work_unit_dispatch_key is None:
        return False, None, 0
    attempt_count = open_redrive_attempt_count(
        study_root=study_root,
        dispatch_key_value=work_unit_dispatch_key,
    )
    return attempt_count >= max_attempts, work_unit_dispatch_key, attempt_count


def _closed_event_has_result_evidence(event: Mapping[str, Any]) -> bool:
    payload = event.get("payload")
    if not isinstance(payload, Mapping):
        return False
    gate_replay_status = _non_empty_text(payload.get("gate_replay_status"))
    if gate_replay_status == "clear" or payload.get("gate_clear") is True:
        return True
    if _non_empty_text(payload.get("artifact_delta_ref")) is not None:
        return True
    if _non_empty_text(payload.get("gate_fingerprint_before")) and _non_empty_text(payload.get("gate_fingerprint_after")):
        return payload.get("gate_fingerprint_before") != payload.get("gate_fingerprint_after")
    attempt_record = payload.get("attempt_record")
    if isinstance(attempt_record, Mapping) and _non_empty_text(attempt_record.get("attempt_state")) in {
        "released",
        "running",
        "retry_queued",
    }:
        return True
    attempt_result = payload.get("attempt_result")
    if isinstance(attempt_result, Mapping) and _non_empty_text(attempt_result.get("status")) is not None:
        return True
    return False


def dispatch_already_executed(
    *,
    study_root: Path,
    tick_request: Mapping[str, Any],
) -> tuple[bool, str | None]:
    work_unit_dispatch_key = dispatch_key(tick_request)
    if work_unit_dispatch_key is None:
        return False, None
    previous = _read_json_object(_wakeup_latest_path(study_root)) or {}
    previous_dispatch_key = _non_empty_text(previous.get("work_unit_dispatch_key"))
    previous_result_state = _non_empty_text(previous.get("work_unit_result_state"))
    unit_id, suffix = _unit_dispatch_suffix(tick_request)
    ledger_replay_allowed = _non_empty_text(previous.get("dispatch_cause")) != "input_changed"
    if ledger_replay_allowed and _ledger_has_executed_dispatch(
        study_root=study_root,
        dispatch_key_value=work_unit_dispatch_key,
        unit_id=unit_id,
        suffix=suffix,
    ):
        return True, work_unit_dispatch_key
    if previous_dispatch_key != work_unit_dispatch_key:
        return False, work_unit_dispatch_key
    return previous_result_state == "closed", work_unit_dispatch_key


def context_payload(tick_request: Mapping[str, Any], *, work_unit_dispatch_key: str | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    if work_unit_dispatch_key is not None:
        payload["work_unit_dispatch_key"] = work_unit_dispatch_key
    work_unit_fingerprint = _non_empty_text(tick_request.get("work_unit_fingerprint"))
    next_work_unit = tick_request.get("next_work_unit")
    if work_unit_fingerprint is not None and isinstance(next_work_unit, Mapping):
        payload["work_unit_fingerprint"] = work_unit_fingerprint
        payload["next_work_unit"] = dict(next_work_unit)
    specificity_questions = tick_request.get("specificity_questions")
    if isinstance(specificity_questions, list):
        payload["specificity_questions"] = [str(item) for item in specificity_questions if str(item).strip()]
    return payload


def strip_context(tick_request: Mapping[str, Any]) -> dict[str, Any]:
    return dict(tick_request)
