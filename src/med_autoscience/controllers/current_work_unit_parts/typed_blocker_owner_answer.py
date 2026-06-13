from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from .primitives import mapping as _mapping
from .primitives import text as _text
from .primitives import text_items as _text_items


ActionSupersedesTypedBlocker = Callable[..., bool]


def typed_blocker_answer_ref(blocker: Mapping[str, Any]) -> str | None:
    closeout_refs = _text_items(blocker.get("closeout_refs"))
    for ref in closeout_refs:
        if ref.endswith("#typed_blocker"):
            return ref
    return _text(blocker.get("typed_blocker_ref")) or _text(blocker.get("source_ref"))


def typed_blocker_has_owner_answer_currentness(blocker: Mapping[str, Any] | None) -> bool:
    payload = _mapping(blocker)
    if not payload:
        return False
    if typed_blocker_answer_ref(payload) is not None:
        return True
    if _text(payload.get("latest_owner_answer_ref")) is not None:
        return True
    if _text_items(payload.get("closeout_refs")):
        return True
    if _mapping(payload.get("owner_answer_binding")):
        return True
    basis = _mapping(payload.get("currentness_basis")) or _mapping(
        payload.get("owner_route_currentness_basis")
    )
    return bool(
        _text(basis.get("work_unit_id"))
        and (
            _text(basis.get("work_unit_fingerprint"))
            or _text(basis.get("source_fingerprint"))
            or _text(basis.get("stage_attempt_id"))
        )
    )


def typed_blocker_is_stage_owner_answer(blocker: Mapping[str, Any] | None) -> bool:
    payload = _mapping(blocker)
    if not payload:
        return False
    basis = _mapping(payload.get("currentness_basis")) or _mapping(
        payload.get("owner_route_currentness_basis")
    )
    return (
        _text(basis.get("source")) == "stage_owner_answer.typed_blocker"
        or _text(payload.get("latest_owner_answer_kind")) == "typed_blocker"
        and _text(payload.get("action_type")) == "complete_medical_paper_readiness_surface"
    )


def typed_blocker_precedes_stage_owner_answer(
    *,
    blocker: Mapping[str, Any] | None,
    action: Mapping[str, Any] | None,
    progress: Mapping[str, Any],
    action_supersedes_typed_blocker: ActionSupersedesTypedBlocker,
) -> bool:
    payload = _mapping(blocker)
    if not payload:
        return False
    if typed_blocker_is_stage_owner_answer(payload):
        return False
    if action is not None and action_supersedes_typed_blocker(
        action=action,
        blocker=payload,
        progress=progress,
    ):
        return False
    if not typed_blocker_has_owner_answer_currentness(payload):
        return False
    return (
        _text(payload.get("stage_attempt_id")) is not None
        or _text(payload.get("terminal_closeout_status")) is not None
        or _text(payload.get("terminal_closeout_outcome")) is not None
        or bool(_text_items(payload.get("closeout_refs")))
        or default_executor_closeout_ref(payload)
    )


def default_executor_closeout_ref(blocker: Mapping[str, Any]) -> bool:
    for value in (
        _text(blocker.get("typed_blocker_ref")),
        _text(blocker.get("source_ref")),
        _text(blocker.get("latest_owner_answer_ref")),
        *_text_items(blocker.get("acceptance_refs")),
    ):
        if value is not None and "default_executor_execution/" in value:
            return True
    return False


__all__ = [
    "default_executor_closeout_ref",
    "typed_blocker_answer_ref",
    "typed_blocker_has_owner_answer_currentness",
    "typed_blocker_is_stage_owner_answer",
    "typed_blocker_precedes_stage_owner_answer",
]
