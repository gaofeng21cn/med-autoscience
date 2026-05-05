from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from med_autoscience.controllers.runtime_supervisor_scan_parts import platform_repair
from med_autoscience.controllers.study_progress_parts.publication_runtime import _publication_eval_specificity_request
from med_autoscience.publication_eval_specificity_targets import (
    REQUIRED_PUBLICATION_GATE_SPECIFICITY_TARGET_KINDS,
    specificity_target_status,
)


REQUIRED_TARGET_KINDS = list(REQUIRED_PUBLICATION_GATE_SPECIFICITY_TARGET_KINDS)


def publication_gate_specificity_required(
    *,
    status: Mapping[str, Any],
    progress: Mapping[str, Any],
    publication_eval_payload: Mapping[str, Any],
    blocking_reasons: Iterable[str],
) -> dict[str, Any]:
    reasons = set(blocking_reasons)
    if _text(status.get("reason")) == "publication_gate_specificity_required":
        reasons.add("publication_gate_specificity_required")
    if _text(_mapping(progress.get("ai_repair_lifecycle")).get("blocked_reason")) == "publication_gate_specificity_required":
        reasons.add("publication_gate_specificity_required")
    operator_status = _mapping(progress.get("operator_status_card"))
    no_op_suppression = _mapping(operator_status.get("no_op_suppression"))
    specificity_request = _publication_eval_specificity_request(dict(publication_eval_payload) or None)
    target_status = _publication_eval_specificity_target_status(publication_eval_payload)
    required = (
        "publication_gate_specificity_required" in reasons
        or _text(_mapping(progress.get("intervention_lane")).get("lane_id")) == "publication_gate_specificity_required"
        or _text(_mapping(progress.get("operator_verdict")).get("lane_id")) == "publication_gate_specificity_required"
        or _text(operator_status.get("handling_state")) == "publication_gate_specificity_required"
        or _text(no_op_suppression.get("outcome")) == "needs_specificity"
        or _next_work_unit_needs_specificity(no_op_suppression.get("next_work_unit"))
        or specificity_request is not None
    )
    if required and target_status.get("complete") is True:
        return {
            "required": False,
            "request": specificity_request,
            "required_target_kinds": list(REQUIRED_TARGET_KINDS),
            "missing_target_kinds": [],
            "covered_target_kinds": _string_items(target_status.get("covered_target_kinds")),
            "specificity_targets": list(target_status.get("targets") or []),
            "specificity_action_id": _text(target_status.get("action_id")),
            "gate_owner": "publication_gate",
            "specific_targets_present": True,
        }
    result = {
        "required": required,
        "request": specificity_request,
        "required_target_kinds": list(REQUIRED_TARGET_KINDS),
        "missing_target_kinds": (
            _string_items(target_status.get("missing_target_kinds"))
            if target_status.get("present") is True
            else list(REQUIRED_TARGET_KINDS)
        ),
        "covered_target_kinds": _string_items(target_status.get("covered_target_kinds")),
        "gate_owner": "publication_gate",
        "next_controller_write": {
            "surface": "publication_eval/latest.json",
            "writer": "publication_gate_controller",
            "materialization_mode": "controller_request_only",
            "required_target_kinds": list(REQUIRED_TARGET_KINDS),
        },
    }
    if target_status.get("present") is True:
        result["specificity_targets"] = list(target_status.get("targets") or [])
    if text := _text(target_status.get("error")):
        result["target_validation_error"] = text
    return result


def gate_specificity_status(gate_specificity: Mapping[str, Any]) -> dict[str, Any]:
    status = dict(gate_specificity)
    if gate_specificity.get("specific_targets_present") is True:
        status["status"] = "specific_targets_present"
    else:
        status["status"] = "blocked" if gate_specificity.get("required") is True else "not_required"
    if gate_specificity.get("required") is True:
        status.setdefault("blocked_reason", "publication_gate_specificity_required")
    return status


def _publication_eval_specificity_target_status(publication_eval_payload: Mapping[str, Any]) -> dict[str, Any]:
    actions = publication_eval_payload.get("recommended_actions")
    if not isinstance(actions, list):
        return _no_specificity_targets()
    best_status: dict[str, Any] | None = None
    for action in actions:
        if not isinstance(action, Mapping) or "specificity_targets" not in action:
            continue
        status = specificity_target_status(action.get("specificity_targets"))
        status["present"] = True
        status["action_id"] = _text(action.get("action_id"))
        if status.get("complete") is True:
            return status
        if best_status is None:
            best_status = status
    return best_status or _no_specificity_targets()


def _no_specificity_targets() -> dict[str, Any]:
    return {
        "present": False,
        "complete": False,
        "covered_target_kinds": [],
        "missing_target_kinds": list(REQUIRED_TARGET_KINDS),
    }


def _next_work_unit_needs_specificity(value: object) -> bool:
    next_work_unit = _mapping(value)
    return _text(next_work_unit.get("unit_id")) in platform_repair.SPECIFICITY_WORK_UNIT_IDS


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _string_items(value: object) -> list[str]:
    if isinstance(value, str):
        text = value.strip()
        return [text] if text else []
    if not isinstance(value, Iterable) or isinstance(value, Mapping | bytes):
        return []
    return list(dict.fromkeys(text for item in value if (text := _text(item)) is not None))
