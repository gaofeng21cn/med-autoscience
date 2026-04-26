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
    if unit_id is None or action_type is None:
        return None, None
    return unit_id, f"::{unit_id}::{action_type}"


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
    previous_outcome = _non_empty_text(previous.get("outcome"))
    if previous_dispatch_key != work_unit_dispatch_key:
        unit_id, suffix = _unit_dispatch_suffix(tick_request)
        if (
            unit_id in _UPSTREAM_REPAIR_UNITS
            and suffix is not None
            and previous_dispatch_key is not None
            and previous_dispatch_key.endswith(suffix)
            and previous_outcome in {"dispatched", "skipped_matching_work_unit"}
        ):
            return True, work_unit_dispatch_key
        return False, work_unit_dispatch_key
    return previous_outcome in {"dispatched", "skipped_matching_work_unit"}, work_unit_dispatch_key


def context_payload(tick_request: Mapping[str, Any], *, work_unit_dispatch_key: str | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    if work_unit_dispatch_key is not None:
        payload["work_unit_dispatch_key"] = work_unit_dispatch_key
    work_unit_fingerprint = _non_empty_text(tick_request.get("work_unit_fingerprint"))
    next_work_unit = tick_request.get("next_work_unit")
    if work_unit_fingerprint is not None and isinstance(next_work_unit, Mapping):
        payload["work_unit_fingerprint"] = work_unit_fingerprint
        payload["next_work_unit"] = dict(next_work_unit)
    return payload


def strip_context(tick_request: Mapping[str, Any]) -> dict[str, Any]:
    payload = dict(tick_request)
    payload.pop("work_unit_fingerprint", None)
    payload.pop("next_work_unit", None)
    return payload
