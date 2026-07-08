from __future__ import annotations

from typing import Any, Mapping

from med_autoscience.controllers import current_work_unit
from med_autoscience.controllers.current_work_unit.policy_constants import (
    CURRENT_ACTION_SUPERSEDED_RUNTIME_BLOCKERS,
)

from ..shared import _mapping_copy, _non_empty_text


def current_action_aligned_with_execution_envelope(
    *,
    action: Mapping[str, Any],
    envelope: Mapping[str, Any],
) -> dict[str, Any] | None:
    if not action:
        return None
    if _non_empty_text(action.get("surface_kind")) != "current_executable_owner_action":
        return None
    state_kind = _non_empty_text(envelope.get("state_kind"))
    if state_kind == "typed_blocker":
        typed_blocker = _mapping_copy(envelope.get("typed_blocker"))
        blocker_reason = typed_blocker_reason(typed_blocker) or _envelope_typed_blocker_reason(envelope)
        if (
            blocker_reason not in CURRENT_ACTION_SUPERSEDED_RUNTIME_BLOCKERS
            and not current_work_unit.action_supersedes_typed_blocker(
                action=action,
                blocker=typed_blocker,
                progress=envelope.get("progress_payload"),
            )
        ):
            return None
        return dict(action)
    action_source = _non_empty_text(action.get("source_surface")) or _non_empty_text(action.get("source"))
    if (
        state_kind == "typed_blocker"
        and action_source == "study_progress.next_forced_delta.owner_action"
        and _envelope_typed_blocker_reason(envelope) == "gate_clearing_batch_source_eval_currentness_mismatch"
    ):
        return dict(action)
    if (
        state_kind == "typed_blocker"
        and action_source == "study_progress.next_forced_delta.owner_action"
        and action.get("terminal_stage_next_forced_delta") is True
    ):
        return dict(action)
    if state_kind != "executable_owner_action":
        return None
    envelope_work_unit = _work_unit_identity(envelope.get("next_work_unit"))
    envelope_action = _non_empty_text(envelope.get("action_type"))
    action_type = _non_empty_text(action.get("action_type"))
    action_work_units = {
        item
        for item in (
            _non_empty_text(action.get("work_unit_id")),
            _non_empty_text(action.get("action_type")),
            *text_list(action.get("allowed_actions")),
        )
        if item is not None
    }
    if envelope_work_unit is not None and action_work_units and envelope_work_unit not in action_work_units:
        return None
    if envelope_action is not None and action_type is not None and envelope_action != action_type:
        return None
    envelope_fingerprint = _fingerprint_identity(envelope)
    action_fingerprint = _fingerprint_identity(action)
    if envelope_fingerprint is not None and action_fingerprint is not None:
        if envelope_fingerprint != action_fingerprint:
            return None
    return dict(action)


def typed_blocker_reason(typed_blocker: Mapping[str, Any]) -> str | None:
    for key in ("blocked_reason", "blocker_type", "blocker_kind", "reason", "blocker_id"):
        if text := _non_empty_text(typed_blocker.get(key)):
            return text
    anti_loop_budget = _mapping_copy(typed_blocker.get("anti_loop_budget"))
    if _non_empty_text(anti_loop_budget.get("status")) == "exhausted":
        return "anti_loop_budget_exhausted"
    return None


def text_list(value: object) -> list[str]:
    if isinstance(value, str):
        text = value.strip()
        return [text] if text else []
    if not isinstance(value, list | tuple | set):
        return []
    return [text for item in value if (text := _non_empty_text(item)) is not None]


def _envelope_typed_blocker_reason(envelope: Mapping[str, Any]) -> str | None:
    blocker = _mapping_copy(envelope.get("typed_blocker"))
    for key in ("blocker_type", "blocker_id", "blocked_reason", "reason"):
        if text := _non_empty_text(blocker.get(key)):
            return text
    return None


def _work_unit_identity(value: object) -> str | None:
    if isinstance(value, Mapping):
        return _non_empty_text(value.get("unit_id")) or _non_empty_text(value.get("work_unit_id"))
    return _non_empty_text(value)


def _fingerprint_identity(value: Mapping[str, Any]) -> str | None:
    basis = _mapping_copy(value.get("owner_route_currentness_basis")) or _mapping_copy(value.get("currentness_basis"))
    return (
        _non_empty_text(value.get("work_unit_fingerprint"))
        or _non_empty_text(value.get("action_fingerprint"))
        or _non_empty_text(value.get("fingerprint"))
        or _non_empty_text(value.get("source_fingerprint"))
        or _non_empty_text(basis.get("work_unit_fingerprint"))
        or _non_empty_text(basis.get("source_fingerprint"))
    )


__all__ = [
    "current_action_aligned_with_execution_envelope",
    "text_list",
    "typed_blocker_reason",
]
