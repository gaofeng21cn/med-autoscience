from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .current_action_identity import action_matches_canonical_executable_work_unit
from .shared import _mapping_copy, _non_empty_text


def current_control_executable_owner_action(handoff: Mapping[str, Any]) -> dict[str, Any] | None:
    if handoff.get("running_provider_attempt") is True:
        return None
    current_work_unit = _mapping_copy(handoff.get("current_work_unit"))
    current_envelope = _mapping_copy(handoff.get("current_execution_envelope"))
    if _non_empty_text(current_work_unit.get("status")) != "executable_owner_action":
        return None
    if current_envelope and _non_empty_text(current_envelope.get("state_kind")) != "executable_owner_action":
        return None
    action = _mapping_copy(handoff.get("current_executable_owner_action"))
    if _non_empty_text(action.get("surface_kind")) != "current_executable_owner_action":
        return None
    if not action_matches_canonical_executable_work_unit(
        action=action,
        current_work_unit=current_work_unit,
        require_ready_status=True,
    ):
        return None
    if not _envelope_matches_executable_action(
        envelope=current_envelope,
        current_work_unit=current_work_unit,
        action=action,
    ):
        return None
    return action


def current_control_executable_currentness_handoff(
    handoff: Mapping[str, Any],
    *,
    current_control_executable_action: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    action = _mapping_copy(current_control_executable_action) or current_control_executable_owner_action(handoff)
    if not action:
        return dict(handoff)
    current_work_unit = _mapping_copy(handoff.get("current_work_unit"))
    current_envelope = _mapping_copy(handoff.get("current_execution_envelope"))
    updated = dict(handoff)
    updated["typed_blocker"] = None
    updated["blocked_reason"] = None
    updated["next_owner"] = _non_empty_text(action.get("next_owner")) or _non_empty_text(
        current_work_unit.get("owner")
    )
    if _non_empty_text(current_work_unit.get("status")) == "executable_owner_action":
        updated["current_work_unit"] = current_work_unit
    if _non_empty_text(current_envelope.get("state_kind")) == "executable_owner_action":
        updated["current_execution_envelope"] = current_envelope
    updated["current_executable_owner_action"] = dict(action)
    return updated


def _envelope_matches_executable_action(
    *,
    envelope: Mapping[str, Any],
    current_work_unit: Mapping[str, Any],
    action: Mapping[str, Any],
) -> bool:
    if not envelope:
        return True
    envelope_owner = _non_empty_text(envelope.get("owner"))
    canonical_owner = _non_empty_text(current_work_unit.get("owner")) or _non_empty_text(
        action.get("next_owner")
    )
    if envelope_owner is not None and canonical_owner is not None and envelope_owner != canonical_owner:
        return False
    envelope_work_unit = _non_empty_text(envelope.get("next_work_unit")) or _non_empty_text(
        envelope.get("work_unit_id")
    )
    canonical_work_unit = _non_empty_text(current_work_unit.get("work_unit_id")) or _non_empty_text(
        action.get("work_unit_id")
    )
    if (
        envelope_work_unit is not None
        and canonical_work_unit is not None
        and envelope_work_unit != canonical_work_unit
    ):
        return False
    envelope_action = _non_empty_text(envelope.get("action_type"))
    canonical_action = _non_empty_text(current_work_unit.get("action_type")) or _non_empty_text(
        action.get("action_type")
    )
    if envelope_action is not None and canonical_action is not None and envelope_action != canonical_action:
        return False
    envelope_fingerprint = _non_empty_text(envelope.get("work_unit_fingerprint")) or _non_empty_text(
        envelope.get("action_fingerprint")
    )
    canonical_fingerprint = _non_empty_text(current_work_unit.get("work_unit_fingerprint")) or _non_empty_text(
        current_work_unit.get("action_fingerprint")
    ) or _non_empty_text(action.get("work_unit_fingerprint")) or _non_empty_text(action.get("action_fingerprint"))
    if (
        envelope_fingerprint is not None
        and canonical_fingerprint is not None
        and envelope_fingerprint != canonical_fingerprint
    ):
        return False
    return True
