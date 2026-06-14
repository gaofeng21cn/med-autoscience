from __future__ import annotations

from typing import Any, Mapping

from med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_helpers import (
    mapping as _mapping,
    non_empty_text as _non_empty_text,
    text_items as _text_items,
)


def current_control_payload_with_status_currentness(
    current_control_payload: Mapping[str, Any] | None,
    *,
    status_payload: Mapping[str, Any] | None,
) -> dict[str, Any]:
    payload = dict(_mapping(current_control_payload))
    status = _mapping(status_payload)
    study = _status_currentness_study(status)
    if not study:
        return payload
    study_id = _non_empty_text(study.get("study_id"))
    studies = [dict(item) if isinstance(item, Mapping) else item for item in payload.get("studies") or []]
    merged: list[Any] = []
    replaced = False
    for item in studies:
        if isinstance(item, Mapping) and _non_empty_text(item.get("study_id")) == study_id:
            merged.append({**dict(item), **study})
            replaced = True
        else:
            merged.append(item)
    if not replaced:
        merged.append(study)
    payload["studies"] = merged
    return payload


def _status_currentness_study(status: Mapping[str, Any]) -> dict[str, Any]:
    current_work_unit = _mapping(status.get("current_work_unit"))
    current_work_unit_status = _non_empty_text(current_work_unit.get("status"))
    if current_work_unit_status != "executable_owner_action":
        return {}
    current_action = _mapping(status.get("current_executable_owner_action"))
    if not current_action:
        return {}
    currentness_basis = _mapping(current_work_unit.get("currentness_basis"))
    study_id = _non_empty_text(status.get("study_id")) or _non_empty_text(current_work_unit.get("study_id"))
    if study_id is None:
        return {}
    work_unit_id = _non_empty_text(current_work_unit.get("work_unit_id")) or _non_empty_text(
        current_action.get("work_unit_id")
    )
    work_unit_fingerprint = _non_empty_text(current_work_unit.get("work_unit_fingerprint")) or _non_empty_text(
        current_action.get("work_unit_fingerprint")
    )
    action_fingerprint = _non_empty_text(current_work_unit.get("action_fingerprint")) or _non_empty_text(
        current_action.get("action_fingerprint")
    )
    source_refs = {
        key: value
        for key, value in {
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": work_unit_fingerprint,
            "action_fingerprint": action_fingerprint,
            "owner_route_currentness_basis": currentness_basis or None,
        }.items()
        if value not in (None, "", [], {})
    }
    return {
        "study_id": study_id,
        "quest_id": _non_empty_text(status.get("quest_id")) or _non_empty_text(current_work_unit.get("quest_id")),
        "current_work_unit": dict(current_work_unit),
        "current_execution_envelope": dict(_mapping(status.get("current_execution_envelope"))),
        "current_executable_owner_action": dict(current_action),
        "owner_route": {
            "next_owner": _non_empty_text(current_action.get("next_owner"))
            or _non_empty_text(current_work_unit.get("owner")),
            "allowed_actions": _text_items(current_action.get("allowed_actions"))
            or _text_items(current_work_unit.get("action_type")),
            "work_unit_fingerprint": work_unit_fingerprint,
            "source_refs": source_refs,
        },
    }


__all__ = ["current_control_payload_with_status_currentness"]
