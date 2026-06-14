from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from med_autoscience.runtime_control import owner_route as owner_route_part


def current_executable_owner_action_identity_from_study(
    *,
    study: Mapping[str, Any],
    fallback_action: Mapping[str, Any],
) -> dict[str, Any]:
    current_work_unit = _mapping(study.get("current_work_unit"))
    if current_work_unit:
        return _merge_identity_owner_route_refs(
            current_work_unit_owner_action_identity(current_work_unit),
            _mapping(study.get("owner_route")),
        )
    current_action = _mapping(study.get("current_executable_owner_action"))
    if current_action:
        return _merge_identity_owner_route_refs(
            current_executable_owner_action_identity(current_action),
            _mapping(study.get("owner_route")),
        )
    current_envelope = _mapping(study.get("current_execution_envelope"))
    if current_envelope:
        return current_execution_envelope_owner_action_identity(
            current_envelope,
            fallback_action=fallback_action,
        )
    return current_executable_owner_action_identity(fallback_action)


def current_work_unit_owner_action_identity(current_work_unit: Mapping[str, Any]) -> dict[str, Any]:
    if _text(current_work_unit.get("status")) != "executable_owner_action":
        return {}
    action_type = _text(current_work_unit.get("action_type"))
    work_unit_id = _text(current_work_unit.get("work_unit_id"))
    source_refs = _mapping(_mapping(current_work_unit.get("currentness_basis")).get("source_refs"))
    route_source_refs = _mapping(_mapping(current_work_unit.get("owner_route")).get("source_refs"))
    currentness_basis = _mapping(current_work_unit.get("currentness_basis"))
    fingerprint = (
        _text(current_work_unit.get("work_unit_fingerprint"))
        or _text(current_work_unit.get("action_fingerprint"))
        or _text(source_refs.get("work_unit_fingerprint"))
        or _text(route_source_refs.get("work_unit_fingerprint"))
        or _text(currentness_basis.get("work_unit_fingerprint"))
    )
    fingerprints = [
        item
        for item in (
            _text(current_work_unit.get("work_unit_fingerprint")),
            _text(current_work_unit.get("action_fingerprint")),
            _text(source_refs.get("work_unit_fingerprint")),
            _text(route_source_refs.get("work_unit_fingerprint")),
            _text(currentness_basis.get("work_unit_fingerprint")),
            _text(currentness_basis.get("source_fingerprint")),
        )
        if item is not None
    ]
    return {
        "source": "canonical_current_work_unit",
        "next_owner": _text(current_work_unit.get("owner")),
        "action_ids": [item for item in (action_type, work_unit_id) if item is not None],
        "action_type": action_type,
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": fingerprint,
        "work_unit_fingerprints": list(dict.fromkeys(fingerprints)),
    }


def current_execution_envelope_owner_action_identity(
    envelope: Mapping[str, Any],
    *,
    fallback_action: Mapping[str, Any],
) -> dict[str, Any]:
    state_kind = _text(envelope.get("state_kind")) or _text(envelope.get("execution_state_kind"))
    if state_kind != "executable_owner_action":
        return {}
    work_unit_id = _text(envelope.get("next_work_unit"))
    identity = {
        "source": "current_execution_envelope",
        "next_owner": _text(envelope.get("owner")),
        "action_ids": [],
        "work_unit_id": work_unit_id,
    }
    fallback_identity = current_executable_owner_action_identity(fallback_action)
    if not fallback_identity:
        return identity
    fallback_work_unit_id = _text(fallback_identity.get("work_unit_id"))
    if work_unit_id is not None and fallback_work_unit_id != work_unit_id:
        return identity
    next_owner = _text(identity.get("next_owner"))
    fallback_next_owner = _text(fallback_identity.get("next_owner"))
    if next_owner is not None and fallback_next_owner is not None and fallback_next_owner != next_owner:
        return identity
    fingerprints = [
        *_text_items(fallback_identity.get("work_unit_fingerprints")),
        _text(fallback_identity.get("work_unit_fingerprint")),
    ]
    return {
        **identity,
        "action_type": _text(fallback_identity.get("action_type")),
        "action_ids": _text_items(fallback_identity.get("action_ids")),
        "work_unit_fingerprint": _text(fallback_identity.get("work_unit_fingerprint")),
        "work_unit_fingerprints": list(dict.fromkeys(item for item in fingerprints if item is not None)),
    }


def current_executable_owner_action_identity(action: Mapping[str, Any]) -> dict[str, Any]:
    action_type = _text(action.get("action_type"))
    work_unit_id = (
        _text(action.get("work_unit_id"))
        or _text(action.get("next_work_unit"))
        or _text(action.get("controller_work_unit_id"))
    )
    fingerprint = (
        _text(action.get("action_fingerprint"))
        or _text(action.get("work_unit_fingerprint"))
        or _text(action.get("source_fingerprint"))
    )
    owner_route = _mapping(action.get("owner_route"))
    source_refs = _mapping(owner_route.get("source_refs"))
    if work_unit_id is None:
        work_unit_id = _text(source_refs.get("work_unit_id"))
    if fingerprint is None:
        fingerprint = _text(source_refs.get("work_unit_fingerprint"))
    source = _text(action.get("source")) or _text(source_refs.get("source"))
    if (
        source is None
        and (
            _mapping(action.get("repair_progress_followup"))
            or (_text(action.get("reason")) or "").startswith("repair_progress_")
        )
    ):
        source = "repair_progress_projection.mas_owner_repair_execution_evidence"
    return {
        "source": source or "owner_route_reconcile.current_control_action_queue",
        "next_owner": (
            _text(action.get("next_executable_owner"))
            or _text(action.get("owner"))
            or _text(owner_route.get("next_owner"))
        ),
        "action_type": action_type,
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": fingerprint,
        "allowed_actions": [action_type] if action_type is not None else [],
        "repair_progress_precedence": {
            "source_fingerprint": fingerprint,
        } if fingerprint is not None else {},
    }


def current_executable_owner_action_from_current_work_unit(
    current_work_unit_payload: Mapping[str, Any],
) -> dict[str, Any]:
    payload = _mapping(current_work_unit_payload)
    if _text(payload.get("status")) != "executable_owner_action":
        return {}
    action_type = _text(payload.get("action_type"))
    work_unit_id = _text(payload.get("work_unit_id"))
    owner = _text(payload.get("owner"))
    contract = _mapping(payload.get("required_output_contract"))
    target_surface = _mapping(contract.get("target_surface"))
    required_output_surface = _text(contract.get("required_output_surface"))
    if not target_surface and required_output_surface is not None:
        target_surface = {
            "ref_kind": "mas_owner_surface",
            "surface_ref": required_output_surface,
        }
    return {
        "surface_kind": "current_executable_owner_action",
        "schema_version": 1,
        "status": "ready",
        "source": "canonical_current_work_unit",
        "next_owner": owner,
        "work_unit_id": work_unit_id,
        "action_type": action_type,
        "allowed_actions": [action_type] if action_type is not None else [],
        "work_unit_fingerprint": _text(payload.get("work_unit_fingerprint")),
        "action_fingerprint": _text(payload.get("action_fingerprint")),
        "required_output_surface": required_output_surface,
        "target_surface": target_surface or None,
        "source_ref": current_work_unit_source_ref(payload),
        "authority_boundary": {
            "refs_only": True,
            "source_current_work_unit": True,
            "can_write_runtime_owned_surfaces": False,
            "can_write_paper_or_package": False,
            "can_authorize_quality_verdict": False,
            "can_authorize_publication_ready": False,
        },
    }


def current_work_unit_source_ref(current_work_unit_payload: Mapping[str, Any]) -> str | None:
    for item in current_work_unit_payload.get("input_refs") or []:
        text = _text(item)
        if text is not None:
            return text
    state = _mapping(current_work_unit_payload.get("state"))
    return _text(state.get("source_ref"))


def _merge_identity_owner_route_refs(
    identity: Mapping[str, Any],
    owner_route: Mapping[str, Any],
) -> dict[str, Any]:
    route = owner_route_part.ensure_owner_route_v2(_mapping(owner_route))
    if not identity or not route:
        return dict(identity)
    source_refs = _mapping(route.get("source_refs"))
    basis = _mapping(source_refs.get("owner_route_currentness_basis"))
    fingerprints = [
        *_text_items(identity.get("work_unit_fingerprints")),
        _text(route.get("work_unit_fingerprint")),
        _text(route.get("source_fingerprint")),
        _text(source_refs.get("work_unit_fingerprint")),
        _text(source_refs.get("source_fingerprint")),
        _text(basis.get("work_unit_fingerprint")),
        _text(basis.get("source_fingerprint")),
    ]
    work_unit_id = (
        _text(identity.get("work_unit_id"))
        or _text(source_refs.get("work_unit_id"))
        or _text(basis.get("work_unit_id"))
    )
    fingerprint = _text(identity.get("work_unit_fingerprint")) or next(
        (item for item in fingerprints if item is not None),
        None,
    )
    return {
        **dict(identity),
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": fingerprint,
        "work_unit_fingerprints": list(dict.fromkeys(item for item in fingerprints if item is not None)),
    }


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _text_items(value: object) -> list[str]:
    if isinstance(value, str):
        text = _text(value)
        return [text] if text is not None else []
    if isinstance(value, Mapping | bytes):
        return []
    if not isinstance(value, Iterable):
        return []
    return list(dict.fromkeys(item for item in (_text(item) for item in value) if item is not None))


__all__ = [
    "current_executable_owner_action_from_current_work_unit",
    "current_executable_owner_action_identity",
    "current_executable_owner_action_identity_from_study",
    "current_execution_envelope_owner_action_identity",
    "current_work_unit_owner_action_identity",
    "current_work_unit_source_ref",
]
