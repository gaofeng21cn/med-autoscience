from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from med_autoscience.controllers.domain_health_diagnostic_parts import provider_admission

from .paper_autonomy_supervisor_decision import (
    provider_admission_supervisor_gate,
    supervisor_block_projection,
)
from .shared import _mapping_copy, _non_empty_text


def provider_admission_projection_fields(
    *,
    payload: Mapping[str, Any],
    handoff: Mapping[str, Any],
    study_root: Path,
) -> dict[str, Any]:
    handoff_fields = _identity_bound_handoff_provider_admission_fields(handoff=handoff, payload=payload)
    if handoff_fields is not None:
        return handoff_fields
    supervisor_gate = provider_admission_supervisor_gate(payload)
    if supervisor_gate.get("blocked") is True:
        supervisor_decision = _mapping_copy(supervisor_gate.get("supervisor_decision"))
        return {
            "provider_admission_pending_count": 0,
            "provider_admission_candidates": [],
            "paper_autonomy_supervisor_decision": supervisor_decision,
            "provider_admission_blocked_by_supervisor_decision": supervisor_block_projection(supervisor_gate),
        }
    if _handoff_typed_blocker_consumes_current_action(payload=payload, handoff=handoff):
        return {
            "provider_admission_pending_count": 0,
            "provider_admission_candidates": [],
        }
    current_control_payload = _current_control_payload_for_provider_admission(
        payload=payload,
        handoff=handoff,
    )
    candidates = provider_admission.current_control_provider_admission_candidates(
        current_control_payload,
        study_root=study_root,
        status_payload=payload,
        current_control_ref=_non_empty_text(_mapping_copy(handoff.get("refs")).get("latest_path"))
        or _non_empty_text(handoff.get("source_path")),
    )
    return {
        "provider_admission_pending_count": len(candidates),
        "provider_admission_candidates": list(candidates),
    }


def _identity_bound_handoff_provider_admission_fields(
    *,
    handoff: Mapping[str, Any],
    payload: Mapping[str, Any],
) -> dict[str, Any] | None:
    candidates = [
        dict(item)
        for item in handoff.get("provider_admission_candidates") or []
        if isinstance(item, Mapping)
    ]
    pending_count = int(handoff.get("provider_admission_pending_count") or 0)
    if pending_count <= 0 and not candidates:
        return None
    current_action = _mapping_copy(payload.get("current_executable_owner_action"))
    current_work_unit = _mapping_copy(payload.get("current_work_unit"))
    if _non_empty_text(current_work_unit.get("status")) != "executable_owner_action":
        return None
    matching = [
        item
        for item in candidates
        if _same_action_identity(current_action, item) or _same_action_identity(current_work_unit, item)
    ]
    if not matching:
        return None
    return {
        "provider_admission_pending_count": len(matching),
        "provider_admission_candidates": matching,
    }


def _handoff_typed_blocker_consumes_current_action(
    *,
    payload: Mapping[str, Any],
    handoff: Mapping[str, Any],
) -> bool:
    current_work_unit = _mapping_copy(payload.get("current_work_unit"))
    if _non_empty_text(current_work_unit.get("status")) != "executable_owner_action":
        return False
    current_action = _mapping_copy(payload.get("current_executable_owner_action"))
    if not current_action:
        return False
    handoff_work_unit = _mapping_copy(handoff.get("current_work_unit"))
    handoff_envelope = _mapping_copy(handoff.get("current_execution_envelope"))
    if _non_empty_text(handoff_work_unit.get("status")) not in {"typed_blocker", "blocked_current_work_unit"} and (
        _non_empty_text(handoff_envelope.get("state_kind")) != "typed_blocker"
    ):
        return False
    handoff_state = _mapping_copy(handoff_work_unit.get("state"))
    if (
        _non_empty_text(handoff_state.get("source")) != "accepted_closeout_consumed_pending"
        and _non_empty_text(handoff_envelope.get("source")) != "accepted_closeout_consumed_pending"
    ):
        return False
    typed_blocker = _mapping_copy(handoff_state.get("typed_blocker"))
    if not typed_blocker:
        typed_blocker = _mapping_copy(handoff_work_unit.get("typed_blocker"))
    if not typed_blocker:
        typed_blocker = _mapping_copy(handoff_envelope.get("typed_blocker"))
    if not typed_blocker:
        return False
    return _same_action_identity(current_work_unit, typed_blocker) or _same_action_identity(
        current_action,
        typed_blocker,
    )


def _same_action_identity(left: Mapping[str, Any], right: Mapping[str, Any]) -> bool:
    left_action = _non_empty_text(left.get("action_type"))
    right_action = _non_empty_text(right.get("action_type"))
    if left_action is not None and right_action is not None and left_action != right_action:
        return False
    left_work_unit = _non_empty_text(left.get("work_unit_id")) or _non_empty_text(left.get("next_work_unit"))
    right_work_unit = _non_empty_text(right.get("work_unit_id")) or _non_empty_text(right.get("next_work_unit"))
    if left_work_unit is not None and right_work_unit is not None and left_work_unit != right_work_unit:
        return False
    left_fingerprint = _non_empty_text(left.get("work_unit_fingerprint")) or _non_empty_text(
        left.get("action_fingerprint")
    )
    right_fingerprint = _non_empty_text(right.get("work_unit_fingerprint")) or _non_empty_text(
        right.get("action_fingerprint")
    )
    if left_fingerprint is not None and right_fingerprint is not None and left_fingerprint != right_fingerprint:
        return False
    return (
        left_action is not None
        and right_action is not None
        and left_work_unit is not None
        and right_work_unit is not None
        and left_fingerprint is not None
        and right_fingerprint is not None
    )


def _current_control_payload_for_provider_admission(
    *,
    payload: Mapping[str, Any],
    handoff: Mapping[str, Any],
) -> dict[str, Any]:
    current_control = _mapping_copy(handoff)
    study_action = _study_current_executable_owner_action(payload)
    if study_action:
        studies = [item for item in current_control.get("studies") or [] if isinstance(item, Mapping)]
        study_id = _non_empty_text(payload.get("study_id")) or _non_empty_text(study_action.get("study_id"))
        studies = [
            {**dict(item), **study_action} if _non_empty_text(item.get("study_id")) == study_id else item
            for item in studies
        ]
        if not any(_non_empty_text(item.get("study_id")) == study_id for item in studies):
            studies.append(study_action)
        current_control["studies"] = studies
    return current_control


def _study_current_executable_owner_action(payload: Mapping[str, Any]) -> dict[str, Any]:
    current_work_unit = _mapping_copy(payload.get("current_work_unit"))
    if _non_empty_text(current_work_unit.get("status")) != "executable_owner_action":
        return {}
    current_action = _mapping_copy(payload.get("current_executable_owner_action"))
    if not current_action:
        return {}
    currentness_basis = _mapping_copy(current_work_unit.get("currentness_basis"))
    study_id = _non_empty_text(payload.get("study_id")) or _non_empty_text(current_work_unit.get("study_id"))
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
        "quest_id": _non_empty_text(payload.get("quest_id")) or _non_empty_text(current_work_unit.get("quest_id")),
        "current_work_unit": current_work_unit,
        "current_execution_envelope": _mapping_copy(payload.get("current_execution_envelope")),
        "current_executable_owner_action": current_action,
        "owner_route": {
            "next_owner": _non_empty_text(current_action.get("next_owner"))
            or _non_empty_text(current_work_unit.get("owner")),
            "allowed_actions": _text_list(current_action.get("allowed_actions"))
            or _text_list(current_work_unit.get("action_type")),
            "work_unit_fingerprint": work_unit_fingerprint,
            "source_refs": source_refs,
        },
    }


def _text_list(value: object) -> list[str]:
    if isinstance(value, str):
        text = _non_empty_text(value)
        return [text] if text is not None else []
    if not isinstance(value, list | tuple | set):
        return []
    items: list[str] = []
    for item in value:
        text = _non_empty_text(item)
        if text is not None and text not in items:
            items.append(text)
    return items
