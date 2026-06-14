from __future__ import annotations

from collections.abc import Collection, Mapping
from typing import Any

from med_autoscience.controllers.current_work_unit_parts.action_projection_fields import (
    action_fingerprint as _action_fingerprint,
    action_type as _action_type,
    work_unit_fingerprint as _work_unit_fingerprint,
    work_unit_id as _work_unit_id,
)
from med_autoscience.controllers.current_work_unit_parts.currentness_identity import (
    action_has_strong_currentness_identity as _action_has_strong_currentness_identity,
)
from med_autoscience.controllers.current_work_unit_parts.primitives import (
    mapping as _mapping,
    text as _text,
)


def stage_packet_blocker_current_identity_action(
    *,
    blocker: Mapping[str, Any],
    action: Mapping[str, Any] | None,
    progress: Mapping[str, Any],
    gate_replay_work_units: Collection[str],
) -> dict[str, Any] | None:
    blocker_type = _text(blocker.get("blocker_type")) or _text(blocker.get("blocked_reason"))
    if blocker_type != "stage_packet_not_current_selected_dispatch":
        return None
    blocker_work_unit = _work_unit_id(blocker.get("work_unit_id")) or _work_unit_id(
        blocker.get("next_work_unit")
    )
    blocker_action_type = _text(blocker.get("action_type"))
    progress_first = _mapping(progress.get("progress_first_monitoring_summary"))
    candidates = (
        _owner_gate_current_identity_action(
            blocker=blocker,
            progress=progress,
            blocker_action_type=blocker_action_type,
            blocker_work_unit=blocker_work_unit,
        ),
        _mapping(progress_first.get("current_executable_owner_action")),
        _mapping(progress.get("current_executable_owner_action")),
        _mapping(action),
    )
    for candidate in candidates:
        if not candidate:
            continue
        candidate_work_unit = _work_unit_id(candidate.get("work_unit_id")) or _work_unit_id(
            candidate.get("next_work_unit")
        )
        if (
            blocker_work_unit is not None
            and candidate_work_unit is not None
            and candidate_work_unit != blocker_work_unit
        ):
            continue
        if blocker_action_type is not None and _action_type(candidate) != blocker_action_type:
            continue
        if not _action_has_strong_currentness_identity(
            candidate,
            gate_replay_work_units=gate_replay_work_units,
        ):
            continue
        return dict(candidate)
    return None


def _owner_gate_current_identity_action(
    *,
    blocker: Mapping[str, Any],
    progress: Mapping[str, Any],
    blocker_action_type: str | None,
    blocker_work_unit: str | None,
) -> dict[str, Any]:
    blocker_type = _text(blocker.get("blocker_type")) or _text(blocker.get("blocked_reason"))
    progress_study_id = _text(progress.get("study_id")) or _text(progress.get("quest_id"))
    for event in reversed(_owner_gate_decision_events(progress)):
        payload = _mapping(event.get("payload"))
        identity = _mapping(payload.get("current_owner_identity"))
        if not identity:
            continue
        if _text(identity.get("blocker_type")) != blocker_type:
            continue
        identity_study_id = _text(identity.get("study_id"))
        if progress_study_id is not None and identity_study_id != progress_study_id:
            continue
        identity_action_type = _text(identity.get("action_type"))
        if blocker_action_type is not None and identity_action_type != blocker_action_type:
            continue
        identity_work_unit = _work_unit_id(identity.get("work_unit_id")) or _work_unit_id(
            identity.get("next_work_unit")
        )
        if blocker_work_unit is not None and identity_work_unit != blocker_work_unit:
            continue
        fingerprint = _text(identity.get("work_unit_fingerprint")) or _text(
            identity.get("action_fingerprint")
        )
        if fingerprint is None:
            continue
        source_ref = (
            _text(payload.get("route_back_evidence_ref"))
            or _text(payload.get("human_gate_ref"))
            or _text(payload.get("owner_gate_decision_ref"))
            or _text(payload.get("stable_typed_blocker_ref"))
        )
        if source_ref is None:
            continue
        currentness_basis = {
            "source": "study_intervention_event.owner_gate_decision",
            "truth_epoch": fingerprint,
            "runtime_health_epoch": fingerprint,
            "work_unit_id": identity_work_unit,
            "work_unit_fingerprint": fingerprint,
            "action_fingerprint": fingerprint,
        }
        return {
            key: value
            for key, value in {
                "surface_kind": "current_executable_owner_action",
                "status": "ready",
                "source": "study_intervention_event.owner_gate_decision",
                "authority": "study_intervention_event.owner_gate_decision",
                "action_type": identity_action_type,
                "allowed_actions": [identity_action_type] if identity_action_type is not None else [],
                "work_unit_id": identity_work_unit,
                "work_unit_fingerprint": fingerprint,
                "action_fingerprint": fingerprint,
                "source_ref": source_ref,
                "owner_route_currentness_basis": currentness_basis,
            }.items()
            if value not in (None, "", [], {})
        }
    return {}


def _owner_gate_decision_events(progress: Mapping[str, Any]) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for key in ("study_intervention_events", "intervention_events"):
        for item in progress.get(key) or []:
            event = _mapping(item)
            if _text(event.get("intent")) == "owner_gate_decision":
                events.append(dict(event))
    return events


def action_currentness_basis(action: Mapping[str, Any]) -> dict[str, Any]:
    source_refs = _mapping(action.get("source_refs"))
    return (
        _mapping(action.get("owner_route_currentness_basis"))
        or _mapping(action.get("currentness_basis"))
        or _mapping(source_refs.get("owner_route_currentness_basis"))
    )


def currentness_basis_with_current_action_identity(
    basis: Mapping[str, Any],
    *,
    action: Mapping[str, Any],
    action_basis: Mapping[str, Any],
    work_unit_id: str | None,
    work_unit_fingerprint: str | None,
    action_fingerprint: str | None,
) -> dict[str, Any]:
    merged = dict(basis)
    for key, value in action_basis.items():
        if value not in (None, "", [], {}) and key in {
            "source",
            "source_eval_id",
            "explicit_publication_work_unit_id",
        }:
            merged[key] = value
    for key, value in {
        "source_eval_id": _text(action.get("source_eval_id")),
        "truth_epoch": _text(action.get("truth_epoch")),
        "runtime_health_epoch": _text(action.get("runtime_health_epoch")),
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": work_unit_fingerprint,
        "action_fingerprint": action_fingerprint,
    }.items():
        if value is not None:
            merged[key] = value
    return {key: value for key, value in merged.items() if value not in (None, "", [], {})}


def terminal_action_blocker_has_fresher_identity(
    blocker: Mapping[str, Any],
    *,
    existing_blocker: Mapping[str, Any] | None,
) -> bool:
    existing = _mapping(existing_blocker)
    if not existing:
        return False
    blocker_type = _text(blocker.get("blocker_type")) or _text(blocker.get("blocked_reason"))
    existing_type = _text(existing.get("blocker_type")) or _text(existing.get("blocked_reason"))
    if blocker_type != "stage_packet_not_current_selected_dispatch" or existing_type != blocker_type:
        return False
    blocker_work_unit = _work_unit_id(blocker.get("work_unit_id")) or _work_unit_id(blocker.get("next_work_unit"))
    existing_work_unit = _work_unit_id(existing.get("work_unit_id")) or _work_unit_id(existing.get("next_work_unit"))
    if blocker_work_unit is not None and existing_work_unit is not None and blocker_work_unit != existing_work_unit:
        return False
    blocker_fingerprint = _text(blocker.get("work_unit_fingerprint")) or _text(blocker.get("action_fingerprint"))
    existing_fingerprint = _text(existing.get("work_unit_fingerprint")) or _text(existing.get("action_fingerprint"))
    return bool(blocker_fingerprint and existing_fingerprint and blocker_fingerprint != existing_fingerprint)


def current_work_unit_fingerprint(
    action: Mapping[str, Any],
    *,
    currentness_basis: Mapping[str, Any],
) -> str | None:
    return _work_unit_fingerprint(action, currentness_basis=currentness_basis)


def current_action_fingerprint(
    action: Mapping[str, Any],
    *,
    currentness_basis: Mapping[str, Any],
) -> str | None:
    return _action_fingerprint(action, currentness_basis=currentness_basis)


__all__ = [
    "action_currentness_basis",
    "current_action_fingerprint",
    "current_work_unit_fingerprint",
    "currentness_basis_with_current_action_identity",
    "stage_packet_blocker_current_identity_action",
    "terminal_action_blocker_has_fresher_identity",
]
