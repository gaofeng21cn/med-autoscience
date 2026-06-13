from __future__ import annotations

from collections.abc import Collection, Mapping
from typing import Any

from med_autoscience.controllers import control_identity
from med_autoscience.controllers.current_work_unit_parts.action_projection_fields import (
    action_type as _action_type,
    work_unit_id as _work_unit_id,
)
from med_autoscience.controllers.current_work_unit_parts.primitives import (
    mapping as _mapping,
    text as _text,
    text_items as _text_items,
)
from med_autoscience.controllers.current_work_unit_parts.policy_constants import (
    OPL_CURRENT_CONTROL_ACTION_QUEUE_SOURCE,
)


def action_has_strong_currentness_identity(
    action: Mapping[str, Any],
    *,
    gate_replay_work_units: Collection[str],
) -> bool:
    if _action_type(action) is None:
        return False
    if _work_unit_id(action.get("next_work_unit")) is None and _work_unit_id(action.get("work_unit_id")) is None:
        return False
    fingerprint = _action_strong_currentness_fingerprint(
        action,
        gate_replay_work_units=gate_replay_work_units,
    )
    if fingerprint is None or control_identity.is_synthetic_current_owner_ticket(fingerprint):
        return False
    return True


def action_matches_next_forced_delta(
    *,
    action: Mapping[str, Any],
    progress: Mapping[str, Any],
) -> bool:
    next_forced_delta = _mapping(progress.get("next_forced_delta"))
    owner_action = _mapping(next_forced_delta.get("owner_action"))
    if not owner_action:
        return False
    expected_owner = _text(owner_action.get("next_owner")) or _text(owner_action.get("owner"))
    action_owner = _text(action.get("owner")) or _text(action.get("next_owner"))
    if expected_owner is None or action_owner != expected_owner:
        return False
    expected_work_unit = (
        _work_unit_id(owner_action.get("next_work_unit"))
        or _work_unit_id(owner_action.get("work_unit_id"))
        or _work_unit_id(next_forced_delta.get("work_unit_id"))
    )
    action_work_unit = (
        _work_unit_id(action.get("work_unit_id"))
        or _work_unit_id(action.get("next_work_unit"))
        or _work_unit_id(action.get("controller_next_work_unit"))
    )
    if expected_work_unit is None or action_work_unit != expected_work_unit:
        return False
    if expected_work_unit == "complete_medical_paper_readiness_surface":
        return False
    expected_actions = _text_items(owner_action.get("allowed_actions")) or _text_items(
        next_forced_delta.get("allowed_actions")
    )
    owner_action_type = _text(owner_action.get("action_type"))
    if owner_action_type is not None and owner_action_type not in expected_actions:
        expected_actions = [owner_action_type, *expected_actions]
    if not expected_actions:
        return False
    return _action_type(action) in set(expected_actions)


def action_with_derived_currentness_identity(
    *,
    action: Mapping[str, Any],
    progress: Mapping[str, Any],
    gate_replay_work_units: Collection[str],
) -> dict[str, Any]:
    payload = dict(action)
    if _action_strong_currentness_fingerprint(
        payload,
        gate_replay_work_units=gate_replay_work_units,
    ) is not None:
        return payload
    fingerprint = _route_currentness_fingerprint(
        action=payload,
        progress=progress,
        gate_replay_work_units=gate_replay_work_units,
    )
    if fingerprint is None:
        return payload
    payload["work_unit_fingerprint"] = fingerprint
    payload["action_fingerprint"] = fingerprint
    basis = dict(_mapping(payload.get("owner_route_currentness_basis")))
    basis["source"] = _text(payload.get("source_surface")) or _text(payload.get("source"))
    basis["work_unit_id"] = _work_unit_id(payload.get("work_unit_id")) or _work_unit_id(
        payload.get("next_work_unit")
    )
    basis["work_unit_fingerprint"] = fingerprint
    if source_eval_id := _text(payload.get("source_eval_id")):
        basis["source_eval_id"] = source_eval_id
    payload["owner_route_currentness_basis"] = basis
    return payload


def _action_strong_currentness_fingerprint(
    action: Mapping[str, Any],
    *,
    gate_replay_work_units: Collection[str],
) -> str | None:
    basis = _mapping(action.get("owner_route_currentness_basis"))
    fingerprint = (
        _text(action.get("work_unit_fingerprint"))
        or _text(action.get("action_fingerprint"))
        or _text(action.get("fingerprint"))
        or _text(basis.get("work_unit_fingerprint"))
        or _text(basis.get("source_fingerprint"))
    )
    if fingerprint is not None:
        if control_identity.is_synthetic_current_owner_ticket(fingerprint):
            return None
        return fingerprint
    return _route_currentness_fingerprint(
        action=action,
        progress={},
        gate_replay_work_units=gate_replay_work_units,
    )


def _route_currentness_fingerprint(
    *,
    action: Mapping[str, Any],
    progress: Mapping[str, Any],
    gate_replay_work_units: Collection[str],
) -> str | None:
    source = _text(action.get("source_surface")) or _text(action.get("source"))
    if source == "current_executable_owner_action":
        source = "study_progress.next_forced_delta.owner_action"
    if source not in {"study_progress.next_forced_delta.owner_action", OPL_CURRENT_CONTROL_ACTION_QUEUE_SOURCE}:
        return None
    for key in ("work_unit_fingerprint", "action_fingerprint", "fingerprint"):
        if control_identity.is_synthetic_current_owner_ticket(action.get(key)):
            return None
    action_type = _action_type(action)
    work_unit_id = _work_unit_id(action.get("work_unit_id")) or _work_unit_id(action.get("next_work_unit"))
    if action_type is None or work_unit_id is None:
        return None
    if action_type == "run_quality_repair_batch":
        return None
    if action_type == "run_gate_clearing_batch" and work_unit_id not in gate_replay_work_units:
        return None
    if source == OPL_CURRENT_CONTROL_ACTION_QUEUE_SOURCE and not action_matches_next_forced_delta(
        action=action,
        progress=progress,
    ):
        return None
    if (
        source == "study_progress.next_forced_delta.owner_action"
        and _mapping(action.get("target_surface")) == {}
        and _mapping(progress.get("next_forced_delta")) == {}
        and _text(action.get("source_eval_id")) is None
    ):
        return None
    target = _mapping(action.get("target_surface"))
    return control_identity.stable_route_currentness_fingerprint(
        study_id=_text(progress.get("study_id")),
        source=source,
        work_unit_id=work_unit_id,
        action_type=action_type,
        next_owner=_text(action.get("next_owner")) or _text(action.get("owner")),
        source_eval_id=_text(action.get("source_eval_id")),
        target_surface_ref=_text(target.get("surface_ref")),
        required_delta_kind=_text(action.get("required_delta_kind")),
    )


__all__ = [
    "action_has_strong_currentness_identity",
    "action_matches_next_forced_delta",
    "action_with_derived_currentness_identity",
]
