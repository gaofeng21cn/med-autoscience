from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.controllers.current_work_unit_parts.action_projection_fields import (
    action_type as _action_type,
    work_unit_id as _work_unit_id,
)
from med_autoscience.controllers.current_work_unit_parts.policy_constants import (
    PROVIDER_ADMISSION_AUTHORITIES,
)
from med_autoscience.controllers.current_work_unit_parts.primitives import (
    mapping as _mapping,
    text as _text,
)
from med_autoscience.controllers.study_progress_parts.current_executable_owner_action_parts.repair_progress import (
    owner_action_from_repair_progress_projection,
)


REPAIR_PROGRESS_EVIDENCE_SOURCE = "repair_progress_projection.mas_owner_repair_execution_evidence"
PAPER_RECOVERY_SUCCESSOR_SOURCE = "paper_recovery_state.next_safe_action.successor_owner_action"
GATE_FOLLOWTHROUGH_SUCCESSOR_SOURCE = "gate_clearing_batch_followthrough.actionable_current_work_unit"
QUALITY_REPAIR_ACTION = "run_quality_repair_batch"


def repair_progress_action_consuming_current_action(
    *,
    progress: Mapping[str, Any],
    current_action: Mapping[str, Any] | None,
    provider_admission: Mapping[str, Any] | None,
    surface_kind: str,
) -> dict[str, Any] | None:
    repair_action = owner_action_from_repair_progress_projection(
        progress,
        surface_kind=surface_kind,
    )
    if not _repair_progress_consumes_current_action(
        repair_action=repair_action,
        current_action=current_action,
        provider_admission=provider_admission,
        progress=progress,
    ):
        return None
    return repair_action


def _repair_progress_consumes_current_action(
    *,
    repair_action: Mapping[str, Any] | None,
    current_action: Mapping[str, Any] | None,
    provider_admission: Mapping[str, Any] | None,
    progress: Mapping[str, Any],
) -> bool:
    repair = _mapping(repair_action)
    current = _mapping(current_action)
    if not repair or not current:
        return False
    if _provider_handoff_matches_current_action(
        provider_admission=provider_admission,
        current_action=current,
    ):
        return False
    if (_text(repair.get("source_surface")) or _text(repair.get("source"))) != REPAIR_PROGRESS_EVIDENCE_SOURCE:
        return False
    if _action_type(current) != QUALITY_REPAIR_ACTION:
        return False
    progress_projection = _mapping(progress.get("repair_progress_projection"))
    if progress_projection.get("paper_delta_observed") is not True:
        return False
    if progress_projection.get("accepted_owner_receipt") is not True:
        return False
    if _paper_recovery_successor_action_ready(current) and not _repair_progress_matches_current_successor(
        current_action=current,
        progress=progress,
        progress_projection=progress_projection,
    ):
        return False
    if _gate_followthrough_successor_action_ready(current) and not _repair_progress_matches_current_successor(
        current_action=current,
        progress=progress,
        progress_projection=progress_projection,
    ):
        return False
    precedence = _mapping(repair.get("repair_progress_precedence"))
    source_work_unit = _work_unit_id(precedence.get("source_work_unit_id")) or _work_unit_id(
        progress_projection.get("work_unit_id")
    )
    if source_work_unit is None or source_work_unit != _work_unit_id(current.get("work_unit_id")):
        return False
    repair_eval = _text(repair.get("source_eval_id")) or _text(progress_projection.get("source_eval_id"))
    current_eval = _text(current.get("source_eval_id"))
    if repair_eval is not None and current_eval is not None and repair_eval != current_eval:
        return False
    return True


def _provider_handoff_matches_current_action(
    *,
    provider_admission: Mapping[str, Any] | None,
    current_action: Mapping[str, Any],
) -> bool:
    handoff = _mapping(provider_admission)
    if not handoff:
        return False
    if not _handoff_is_active_provider_control(handoff):
        return False
    handoff_action = _matching_handoff_action(handoff)
    if not handoff_action:
        return False
    return _action_identity_matches(handoff_action, current_action)


def _handoff_is_active_provider_control(handoff: Mapping[str, Any]) -> bool:
    if handoff.get("running_provider_attempt") is True:
        return True
    if handoff.get("provider_admission_pending_count") not in (None, 0):
        return True
    if handoff.get("provider_attempt_or_lease_required") is True:
        return True
    if _text(handoff.get("execution_status")) == "handoff_ready":
        return True
    if any(_mapping(item) for item in handoff.get("provider_admission_candidates") or []):
        return True
    return any(
        _text(_mapping(item).get("authority")) in PROVIDER_ADMISSION_AUTHORITIES
        for item in handoff.get("action_queue") or []
    )


def _matching_handoff_action(handoff: Mapping[str, Any]) -> dict[str, Any]:
    for key in ("current_executable_owner_action", "owner_action"):
        action = _mapping(handoff.get(key))
        if action:
            return action
    current_work_unit = _mapping(handoff.get("current_work_unit"))
    if _text(current_work_unit.get("status")) == "executable_owner_action":
        return current_work_unit
    for item in handoff.get("provider_admission_candidates") or []:
        action = _mapping(item)
        if action:
            return action
    return {}


def _action_identity_matches(left: Mapping[str, Any], right: Mapping[str, Any]) -> bool:
    if _action_type(left) != _action_type(right):
        return False
    left_work_unit = _work_unit_id(left.get("work_unit_id")) or _work_unit_id(left.get("next_work_unit"))
    right_work_unit = _work_unit_id(right.get("work_unit_id")) or _work_unit_id(right.get("next_work_unit"))
    if left_work_unit is None or right_work_unit is None or left_work_unit != right_work_unit:
        return False
    left_fingerprint = _fingerprint(left)
    right_fingerprint = _fingerprint(right)
    return bool(left_fingerprint and right_fingerprint and left_fingerprint == right_fingerprint)


def _fingerprint(action: Mapping[str, Any]) -> str | None:
    basis = _mapping(action.get("owner_route_currentness_basis")) or _mapping(action.get("currentness_basis"))
    return (
        _text(action.get("work_unit_fingerprint"))
        or _text(action.get("action_fingerprint"))
        or _text(action.get("fingerprint"))
        or _text(basis.get("work_unit_fingerprint"))
        or _text(basis.get("source_fingerprint"))
    )


def _repair_identity_fingerprint(repair: Mapping[str, Any]) -> str | None:
    basis = _mapping(repair.get("owner_route_currentness_basis")) or _mapping(repair.get("currentness_basis"))
    return (
        _text(repair.get("work_unit_fingerprint"))
        or _text(repair.get("action_fingerprint"))
        or _text(repair.get("fingerprint"))
        or _text(basis.get("work_unit_fingerprint"))
        or _text(repair.get("source_fingerprint"))
    )


def _repair_progress_matches_current_successor(
    *,
    current_action: Mapping[str, Any],
    progress: Mapping[str, Any],
    progress_projection: Mapping[str, Any],
) -> bool:
    source_work_unit = _work_unit_id(progress_projection.get("work_unit_id"))
    current_work_unit = _work_unit_id(current_action.get("work_unit_id"))
    if source_work_unit is None or current_work_unit is None or source_work_unit != current_work_unit:
        return False
    repair_eval = _text(progress_projection.get("source_eval_id"))
    current_eval = _text(current_action.get("source_eval_id"))
    if repair_eval is not None and current_eval is not None and repair_eval != current_eval:
        return False
    followthrough = _mapping(progress.get("gate_clearing_batch_followthrough"))
    if not followthrough:
        return False
    currentness = _mapping(followthrough.get("work_unit_currentness"))
    if _text(currentness.get("current_actionability_status")) != "actionable":
        return False
    if currentness.get("lacks_specific_blocker_object") is True:
        return False
    followthrough_work_unit = (
        _work_unit_id(followthrough.get("work_unit_id"))
        or _work_unit_id(currentness.get("current_publication_work_unit_id"))
        or _work_unit_id(_mapping(followthrough.get("current_publication_work_unit")).get("unit_id"))
    )
    if followthrough_work_unit is None or followthrough_work_unit != current_work_unit:
        return False
    current_fingerprint = _fingerprint(current_action)
    followthrough_fingerprint = (
        _text(followthrough.get("work_unit_fingerprint"))
        or _text(currentness.get("current_work_unit_fingerprint"))
        or _text(currentness.get("explicit_work_unit_fingerprint"))
    )
    if current_fingerprint is None or followthrough_fingerprint is None:
        return False
    if current_fingerprint != followthrough_fingerprint:
        return False
    repair_fingerprint = _repair_identity_fingerprint(progress_projection)
    if repair_fingerprint is None or repair_fingerprint != current_fingerprint:
        return False
    followthrough_eval = _text(followthrough.get("source_eval_id"))
    if repair_eval is not None and followthrough_eval is not None and repair_eval != followthrough_eval:
        return False
    return True


def _paper_recovery_successor_action_ready(action: Mapping[str, Any]) -> bool:
    if _text(action.get("source")) != PAPER_RECOVERY_SUCCESSOR_SOURCE:
        return False
    successor = _mapping(action.get("paper_recovery_successor"))
    if successor.get("provider_admission_allowed") is not True:
        return False
    return (
        _action_type(action) is not None
        and _work_unit_id(action.get("work_unit_id")) is not None
        and (_text(action.get("work_unit_fingerprint")) or _text(action.get("action_fingerprint")))
        is not None
    )


def _gate_followthrough_successor_action_ready(action: Mapping[str, Any]) -> bool:
    source = _text(action.get("source_surface")) or _text(action.get("source"))
    if source != GATE_FOLLOWTHROUGH_SUCCESSOR_SOURCE:
        return False
    if _action_type(action) != QUALITY_REPAIR_ACTION:
        return False
    return (
        _work_unit_id(action.get("work_unit_id")) is not None
        and (_text(action.get("work_unit_fingerprint")) or _text(action.get("action_fingerprint")))
        is not None
    )


__all__ = ["repair_progress_action_consuming_current_action"]
