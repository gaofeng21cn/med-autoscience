from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from med_autoscience.controllers.stage_route_currentness_identity import (
    currentness_identities_match,
)

from . import progress_blocking_selection
from . import terminal_closeout_owner_answer_identity


def terminal_closeout_owner_answer_dispatches_only(
    *,
    progress: Mapping[str, Any],
    dispatches: list[dict[str, Any]],
    dispatch_work_unit_id: Callable[[Mapping[str, Any]], str | None],
) -> list[dict[str, Any]]:
    if not terminal_closeout_owner_answer_required(progress):
        return dispatches
    return [
        dispatch
        for dispatch in dispatches
        if dispatch_matches_terminal_closeout_owner_answer(
            progress=progress,
            dispatch=dispatch,
            dispatch_work_unit_id=dispatch_work_unit_id,
        )
    ]


def terminal_closeout_owner_answer_required(progress: Mapping[str, Any]) -> bool:
    envelope = _mapping(progress.get("current_execution_envelope"))
    state_kind = _text(envelope.get("state_kind")) or _text(envelope.get("execution_state_kind"))
    return (
        state_kind == "typed_blocker"
        and progress_blocking_selection.fresh_progress_typed_blocker_reason(envelope)
        == "terminal_closeout_owner_answer_required"
    )


def dispatch_matches_terminal_closeout_owner_answer(
    *,
    progress: Mapping[str, Any],
    dispatch: Mapping[str, Any],
    dispatch_work_unit_id: Callable[[Mapping[str, Any]], str | None],
) -> bool:
    if not terminal_closeout_owner_answer_required(progress):
        return False
    envelope = _mapping(progress.get("current_execution_envelope"))
    blocker = _mapping(envelope.get("typed_blocker"))
    action_type = _text(blocker.get("action_type"))
    if action_type is not None and _text(dispatch.get("action_type")) != action_type:
        return False
    expected_work_unit = terminal_closeout_owner_answer_identity.work_unit_id(progress)
    dispatch_work_unit = dispatch_work_unit_id(dispatch)
    if (
        expected_work_unit is not None
        and dispatch_work_unit is not None
        and dispatch_work_unit != expected_work_unit
    ):
        return False
    if _terminal_closeout_owner_answer_ref_matches_dispatch(
        progress=progress,
        dispatch=dispatch,
    ):
        return True
    return currentness_identities_match(
        terminal_closeout_owner_answer_identity.currentness_identity(progress),
        dispatch,
        require_fingerprint=True,
    )


def _terminal_closeout_owner_answer_ref_matches_dispatch(
    *,
    progress: Mapping[str, Any],
    dispatch: Mapping[str, Any],
) -> bool:
    envelope = _mapping(progress.get("current_execution_envelope"))
    blocker = _mapping(envelope.get("typed_blocker"))
    closeout_refs = [
        ref
        for ref in (
            *list(blocker.get("closeout_refs") or []),
            blocker.get("source_ref"),
            blocker.get("typed_blocker_ref"),
        )
        if _text(ref) is not None
    ]
    if not closeout_refs:
        return False
    dispatch_refs = _mapping(dispatch.get("refs"))
    dispatch_ref_values = [
        dispatch_refs.get("dispatch_path"),
        dispatch_refs.get("immutable_dispatch_path"),
        dispatch_refs.get("stage_packet_path"),
    ]
    return any(
        _refs_match(closeout_ref, dispatch_ref)
        for closeout_ref in closeout_refs
        for dispatch_ref in dispatch_ref_values
    )


def _refs_match(left: object, right: object) -> bool:
    left_text = _normalized_ref(left)
    right_text = _normalized_ref(right)
    return bool(
        left_text
        and right_text
        and (
            left_text == right_text
            or left_text.endswith(f"/{right_text}")
            or right_text.endswith(f"/{left_text}")
        )
    )


def _normalized_ref(value: object) -> str | None:
    text = _text(value)
    if text is None:
        return None
    return text.replace("\\", "/").lstrip("./")


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "dispatch_matches_terminal_closeout_owner_answer",
    "terminal_closeout_owner_answer_dispatches_only",
    "terminal_closeout_owner_answer_required",
]
