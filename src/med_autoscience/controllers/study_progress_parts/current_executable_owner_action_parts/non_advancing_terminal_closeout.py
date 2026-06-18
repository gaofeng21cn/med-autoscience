from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.controllers.current_work_unit_parts.terminal_non_advancing_apply import (
    terminal_non_advancing_apply_identity,
    terminal_stage_non_advancing_apply,
)
from med_autoscience.controllers.study_progress_parts.shared import (
    _mapping_copy,
    _non_empty_text,
)


NON_ADVANCING_APPLY_BLOCKER = "non_advancing_apply"
NON_ADVANCING_APPLY_REASON = "fresh_readback_did_not_advance_same_aggregate"


def without_same_identity_non_advancing_apply(
    payload: Mapping[str, Any],
    action: Mapping[str, Any] | None,
) -> dict[str, Any] | None:
    candidate = _mapping_copy(action)
    if not candidate:
        return None
    blocker = _canonical_non_advancing_blocker(payload)
    if not blocker:
        return candidate
    if not _same_work_unit_identity(left=blocker, right=candidate):
        return candidate
    return None


def without_same_identity_terminal_typed_blocker(
    payload: Mapping[str, Any],
    action: Mapping[str, Any] | None,
) -> dict[str, Any] | None:
    candidate = _mapping_copy(action)
    if not candidate:
        return None
    blocker = _canonical_terminal_typed_blocker(payload)
    if not blocker:
        return candidate
    if not _same_work_unit_identity(left=blocker, right=candidate):
        return candidate
    return None


def canonical_current_work_unit_terminal_typed_blocker(
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    return _canonical_terminal_typed_blocker(payload)


def canonical_current_work_unit_has_non_advancing_apply(
    payload: Mapping[str, Any],
) -> bool:
    return bool(_canonical_non_advancing_blocker(payload))


def _canonical_non_advancing_blocker(payload: Mapping[str, Any]) -> dict[str, Any]:
    current_blocker = _current_work_unit_non_advancing_blocker(payload)
    if current_blocker:
        return current_blocker
    terminal_blocker = _terminal_closeout_non_advancing_blocker(payload)
    if terminal_blocker:
        return terminal_blocker
    return {}


def _canonical_terminal_typed_blocker(payload: Mapping[str, Any]) -> dict[str, Any]:
    current_work_unit = _mapping_copy(payload.get("current_work_unit"))
    if _non_empty_text(current_work_unit.get("status")) not in {"typed_blocker", "blocked_current_work_unit"}:
        return {}
    state = _mapping_copy(current_work_unit.get("state"))
    typed_blocker = _mapping_copy(state.get("typed_blocker")) or _mapping_copy(
        current_work_unit.get("typed_blocker")
    )
    if not _typed_blocker_has_terminal_owner_answer(typed_blocker, state=state):
        return {}
    return _compact(
        {
            **typed_blocker,
            "work_unit_id": _non_empty_text(current_work_unit.get("work_unit_id"))
            or _non_empty_text(typed_blocker.get("work_unit_id")),
            "work_unit_fingerprint": _non_empty_text(current_work_unit.get("work_unit_fingerprint"))
            or _non_empty_text(current_work_unit.get("action_fingerprint"))
            or _non_empty_text(typed_blocker.get("work_unit_fingerprint"))
            or _non_empty_text(typed_blocker.get("action_fingerprint")),
            "action_fingerprint": _non_empty_text(current_work_unit.get("action_fingerprint"))
            or _non_empty_text(current_work_unit.get("work_unit_fingerprint"))
            or _non_empty_text(typed_blocker.get("action_fingerprint"))
            or _non_empty_text(typed_blocker.get("work_unit_fingerprint")),
        }
    )


def _current_work_unit_non_advancing_blocker(payload: Mapping[str, Any]) -> dict[str, Any]:
    current_work_unit = _mapping_copy(payload.get("current_work_unit"))
    if _non_empty_text(current_work_unit.get("status")) != "typed_blocker":
        return {}
    state = _mapping_copy(current_work_unit.get("state"))
    typed_blocker = _mapping_copy(state.get("typed_blocker")) or _mapping_copy(
        current_work_unit.get("typed_blocker")
    )
    if not _typed_blocker_is_non_advancing_apply(typed_blocker, state=state):
        return {}
    return _compact(
        {
            **typed_blocker,
            "work_unit_id": _non_empty_text(current_work_unit.get("work_unit_id"))
            or _non_empty_text(typed_blocker.get("work_unit_id")),
            "work_unit_fingerprint": _non_empty_text(current_work_unit.get("work_unit_fingerprint"))
            or _non_empty_text(current_work_unit.get("action_fingerprint"))
            or _non_empty_text(typed_blocker.get("work_unit_fingerprint"))
            or _non_empty_text(typed_blocker.get("action_fingerprint")),
            "action_fingerprint": _non_empty_text(current_work_unit.get("action_fingerprint"))
            or _non_empty_text(current_work_unit.get("work_unit_fingerprint"))
            or _non_empty_text(typed_blocker.get("action_fingerprint"))
            or _non_empty_text(typed_blocker.get("work_unit_fingerprint")),
        }
    )


def _terminal_closeout_non_advancing_blocker(payload: Mapping[str, Any]) -> dict[str, Any]:
    terminal = _latest_terminal_stage(payload)
    if not terminal_stage_non_advancing_apply(
        terminal,
        mapping=_mapping_copy,
        text=_non_empty_text,
    ):
        return {}
    identity = terminal_non_advancing_apply_identity(
        terminal,
        mapping=_mapping_copy,
        text=_non_empty_text,
    )
    return _compact(
        {
            **identity,
            "blocker_type": NON_ADVANCING_APPLY_BLOCKER,
            "blocked_reason": NON_ADVANCING_APPLY_REASON,
            "non_advancing_apply": True,
        }
    )


def _latest_terminal_stage(payload: Mapping[str, Any]) -> dict[str, Any]:
    handoff = _mapping_copy(payload.get("opl_current_control_state_handoff"))
    progress_first = _mapping_copy(payload.get("progress_first_monitoring_summary"))
    for value in (
        progress_first.get("latest_terminal_stage"),
        progress_first.get("latest_terminal_stage_log"),
        handoff.get("latest_terminal_stage_log"),
        payload.get("latest_terminal_stage"),
        payload.get("latest_terminal_stage_log"),
    ):
        terminal = _mapping_copy(value)
        if terminal:
            return terminal
    return {}


def _typed_blocker_has_terminal_owner_answer(
    typed_blocker: Mapping[str, Any],
    *,
    state: Mapping[str, Any],
) -> bool:
    if _typed_blocker_is_non_advancing_apply(typed_blocker, state=state):
        return True
    if _non_empty_text(typed_blocker.get("terminal_closeout_outcome")) == "typed_blocker":
        return True
    if _non_empty_text(typed_blocker.get("latest_owner_answer_kind")) == "typed_blocker":
        return _non_empty_text(typed_blocker.get("latest_owner_answer_ref")) is not None
    if _non_empty_text(typed_blocker.get("owner_answer_shape")) == "typed_blocker_ref":
        return _non_empty_text(typed_blocker.get("latest_owner_answer_ref")) is not None
    if _non_empty_text(typed_blocker.get("typed_blocker_ref")) is not None:
        return True
    return bool(
        _non_empty_text(typed_blocker.get("source_ref"))
        or _non_empty_text(typed_blocker.get("closeout_ref"))
        or typed_blocker.get("closeout_refs")
        or typed_blocker.get("acceptance_refs")
    )


def _typed_blocker_is_non_advancing_apply(
    typed_blocker: Mapping[str, Any],
    *,
    state: Mapping[str, Any],
) -> bool:
    if typed_blocker.get("non_advancing_apply") is True:
        return True
    values = (
        state.get("blocker_type"),
        state.get("blocked_reason"),
        state.get("reason"),
        typed_blocker.get("blocker_type"),
        typed_blocker.get("blocker_id"),
        typed_blocker.get("blocked_reason"),
        typed_blocker.get("reason"),
        typed_blocker.get("no_progress_signal"),
    )
    return any(
        (text := _non_empty_text(value)) in {NON_ADVANCING_APPLY_BLOCKER, NON_ADVANCING_APPLY_REASON}
        for value in values
    )


def _same_work_unit_identity(
    *,
    left: Mapping[str, Any],
    right: Mapping[str, Any],
) -> bool:
    left_work_unit = _non_empty_text(left.get("work_unit_id"))
    right_work_unit = _non_empty_text(right.get("work_unit_id")) or _non_empty_text(
        right.get("next_work_unit")
    )
    if left_work_unit is not None and right_work_unit is not None and left_work_unit != right_work_unit:
        return False
    left_fingerprint = _non_empty_text(left.get("work_unit_fingerprint")) or _non_empty_text(
        left.get("action_fingerprint")
    )
    right_fingerprint = (
        _non_empty_text(right.get("work_unit_fingerprint"))
        or _non_empty_text(right.get("action_fingerprint"))
        or _non_empty_text(right.get("fingerprint"))
    )
    if left_fingerprint is not None and right_fingerprint is not None:
        return left_fingerprint == right_fingerprint
    return left_work_unit is not None and left_work_unit == right_work_unit


def _compact(payload: Mapping[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in payload.items() if value not in (None, "", [], {})}


__all__ = [
    "canonical_current_work_unit_terminal_typed_blocker",
    "canonical_current_work_unit_has_non_advancing_apply",
    "without_same_identity_non_advancing_apply",
    "without_same_identity_terminal_typed_blocker",
]
