from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any


_UPSTREAM_REPAIR_UNITS = frozenset(
    {
        "analysis_claim_evidence_repair",
        "manuscript_story_repair",
        "figure_results_trace_repair",
        "treatment_gap_reporting_repair",
    }
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
    if work_unit_fingerprint is None or unit_id is None or action_type is None:
        return None
    return f"{work_unit_fingerprint}::{unit_id}::{action_type}"


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
