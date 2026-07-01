from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .state_diagnostics import (
    first_text as _first_text,
    mapping as _mapping,
    obligation_identity as _obligation_identity,
    single_text_item as _single_text_item,
    study_id as _study_id,
    text as _text,
)
from .typed_blocker_payload import (
    current_typed_blocker as _current_typed_blocker,
    typed_blocker_reason as _typed_blocker_reason,
)


def obligation(
    progress: Mapping[str, Any],
    *,
    current_work_unit: Mapping[str, Any],
) -> dict[str, Any]:
    typed_blocker = _current_typed_blocker(current_work_unit)
    blocker_reason = _typed_blocker_reason(typed_blocker)
    currentness_basis = _mapping(current_work_unit.get("currentness_basis"))
    action_type = _obligation_action_type(progress, current_work_unit=current_work_unit)
    work_unit_id = _obligation_work_unit_id(progress, current_work_unit=current_work_unit)
    fingerprint = _obligation_fingerprint(
        progress,
        current_work_unit=current_work_unit,
        currentness_basis=currentness_basis,
    )
    identity = _obligation_identity(
        blocker_reason=blocker_reason,
        fingerprint=fingerprint,
        current_work_unit=current_work_unit,
        action_type=action_type,
        work_unit_id=work_unit_id,
    )
    study_id = _study_id(progress)
    return {
        "recovery_obligation_id": "::".join(
            [
                "paper-recovery",
                study_id or "unknown-study",
                action_type or "unknown-action",
                work_unit_id or "unknown-work-unit",
                identity,
            ]
        ),
        "study_id": study_id,
        "quest_id": _text(progress.get("quest_id")) or _text(current_work_unit.get("quest_id")),
        "owner": (
            _text(typed_blocker.get("owner"))
            or _text(current_work_unit.get("owner"))
            or _legacy_owner(progress)
        ),
        "action_type": action_type,
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": fingerprint,
        "blocker_type": blocker_reason,
        "currentness_basis": dict(currentness_basis) if currentness_basis else None,
    }


def _legacy_owner(progress: Mapping[str, Any]) -> str | None:
    return None


def _obligation_action_type(
    progress: Mapping[str, Any],
    *,
    current_work_unit: Mapping[str, Any],
) -> str | None:
    owner_action_admission = _mapping(progress.get("owner_action_admission"))
    return _first_text(
        current_work_unit.get("action_type"),
        owner_action_admission.get("action_type"),
        _single_text_item(owner_action_admission.get("allowed_actions")),
    )


def _obligation_work_unit_id(
    progress: Mapping[str, Any],
    *,
    current_work_unit: Mapping[str, Any],
) -> str | None:
    currentness_basis = _mapping(current_work_unit.get("owner_route_currentness_basis")) or _mapping(
        current_work_unit.get("currentness_basis")
    )
    owner_action_admission = _mapping(progress.get("owner_action_admission"))
    return _first_text(
        current_work_unit.get("work_unit_id"),
        currentness_basis.get("work_unit_id"),
        currentness_basis.get("explicit_publication_work_unit_id"),
        currentness_basis.get("current_publication_work_unit_id"),
        owner_action_admission.get("work_unit_id"),
    )


def _obligation_fingerprint(
    progress: Mapping[str, Any],
    *,
    current_work_unit: Mapping[str, Any],
    currentness_basis: Mapping[str, Any],
) -> str | None:
    return _first_text(
        current_work_unit.get("work_unit_fingerprint"),
        current_work_unit.get("action_fingerprint"),
        currentness_basis.get("work_unit_fingerprint"),
        currentness_basis.get("source_fingerprint"),
    )


__all__ = ["obligation"]
