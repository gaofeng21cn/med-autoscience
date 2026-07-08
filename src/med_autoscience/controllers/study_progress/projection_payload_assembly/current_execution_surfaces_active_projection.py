from __future__ import annotations

from typing import Any, Mapping

from med_autoscience.controllers.current_work_unit import projection as current_work_unit_projection
from med_autoscience.runtime_control.owner_route_attempt_protocol import (
    currentness_basis as owner_route_currentness_basis,
)

from .current_execution_alignment import text_list
from ..shared import _mapping_copy, _non_empty_text


def build_active_current_work_unit(
    *,
    status: Mapping[str, Any],
    progress: Mapping[str, Any],
    current_executable_owner_action: Mapping[str, Any] | None,
    provider_admission: Mapping[str, Any],
    live_provider_attempt: Mapping[str, Any],
    typed_blocker: Mapping[str, Any],
    blocked_reason: str | None,
    next_owner: str | None,
    runtime_health: Mapping[str, Any],
    running_provider_attempt_bound: bool,
) -> dict[str, Any]:
    action = _executable_action_when_canonical(
        progress,
        current_executable_owner_action,
    )
    handoff = _mapping_copy(provider_admission)
    running_attempt = _mapping_copy(live_provider_attempt)
    blocker = _mapping_copy(typed_blocker)
    source_refs = _source_refs_for_current_work_unit(action, blocker, handoff, running_attempt)
    currentness_basis = _currentness_basis_for_current_work_unit(
        action=action,
        blocker=blocker,
        handoff=handoff,
        runtime_health=runtime_health,
    )
    if running_provider_attempt_bound:
        return current_work_unit_projection.running_provider_attempt_work_unit(
            owner=_non_empty_text(next_owner) or _non_empty_text(handoff.get("next_owner")),
            action_type=_work_unit_text("action_type", action, handoff, running_attempt),
            work_unit_id=_work_unit_text("work_unit_id", action, handoff, running_attempt),
            work_unit_fingerprint=_work_unit_text(
                "work_unit_fingerprint",
                action,
                handoff,
                running_attempt,
            ),
            action_fingerprint=_work_unit_text("action_fingerprint", action, handoff, running_attempt),
            source_refs=source_refs,
            currentness_basis=currentness_basis,
            running_attempt=running_attempt,
            status_payload=status,
            progress_payload=progress,
            action=action or None,
        )
    if action:
        return current_work_unit_projection.action_work_unit(
            action=action,
            owner=_non_empty_text(action.get("next_owner"))
            or _non_empty_text(action.get("owner"))
            or _non_empty_text(next_owner)
            or "med-autoscience",
            status_payload=status,
            progress_payload=progress,
            source_refs=source_refs,
            currentness_basis=currentness_basis,
            provider_admission=handoff,
        )
    if blocker or blocked_reason is not None:
        if not blocker:
            blocker = {
                key: value
                for key, value in {
                    "blocker_type": blocked_reason,
                    "blocked_reason": blocked_reason,
                    "owner": _non_empty_text(next_owner) or _non_empty_text(handoff.get("next_owner")),
                }.items()
                if value not in (None, "", [], {})
            }
        return current_work_unit_projection.typed_blocker_work_unit(
            blocker=blocker,
            action=None,
            status_payload=status,
            progress_payload=progress,
            source_refs=source_refs,
            currentness_basis=currentness_basis,
            source="study_progress.current_execution_surfaces",
        )
    return {}


def build_active_current_execution_envelope(
    *,
    progress: Mapping[str, Any],
    actions: list[dict[str, Any]],
    blocked_reason: str | None,
    next_owner: str | None,
    typed_blocker: Mapping[str, Any],
    runtime_health: Mapping[str, Any],
    current_work_unit_payload: Mapping[str, Any],
    running_provider_attempt_bound: bool,
) -> dict[str, Any]:
    current_work = _mapping_copy(current_work_unit_payload)
    state = _mapping_copy(current_work.get("state"))
    action = _executable_action_when_canonical(
        progress,
        progress.get("current_executable_owner_action"),
    )
    blocker = _mapping_copy(typed_blocker)
    if not blocker:
        blocker = _mapping_copy(state.get("typed_blocker"))
    state_kind = _non_empty_text(current_work.get("status")) or _non_empty_text(state.get("state_kind"))
    if action and not blocker:
        state_kind = "executable_owner_action"
    elif blocker and state_kind in {None, "blocked_current_work_unit"}:
        state_kind = "typed_blocker"
    elif running_provider_attempt_bound:
        state_kind = "running_provider_attempt"
    if state_kind is None:
        return {}
    identity_source = action or current_work or blocker
    envelope = {
        "state_kind": state_kind,
        "owner": _non_empty_text(identity_source.get("next_owner"))
        or _non_empty_text(identity_source.get("owner"))
        or _non_empty_text(next_owner)
        or _non_empty_text(blocker.get("owner")),
        "action_type": _non_empty_text(identity_source.get("action_type"))
        or _non_empty_text(blocker.get("action_type")),
        "next_work_unit": _non_empty_text(identity_source.get("work_unit_id"))
        or _non_empty_text(identity_source.get("next_work_unit"))
        or _non_empty_text(blocker.get("work_unit_id")),
        "work_unit_id": _non_empty_text(identity_source.get("work_unit_id"))
        or _non_empty_text(blocker.get("work_unit_id")),
        "work_unit_fingerprint": _non_empty_text(identity_source.get("work_unit_fingerprint"))
        or _non_empty_text(blocker.get("work_unit_fingerprint")),
        "action_fingerprint": _non_empty_text(identity_source.get("action_fingerprint"))
        or _non_empty_text(blocker.get("action_fingerprint")),
        "blocked_reason": blocked_reason,
        "source": _non_empty_text(state.get("source")) or _non_empty_text(action.get("source")),
        "typed_blocker": blocker,
        "actions": list(actions),
        "runtime_health": dict(runtime_health) if isinstance(runtime_health, Mapping) else {},
        "current_work_unit": current_work,
        "authority_boundary": {
            "projection_only": True,
            "runtime_owner": "one-person-lab",
            "domain_truth_owner": "med-autoscience",
            "can_authorize_provider_admission": False,
            "can_start_provider_attempt": False,
            "provider_completion_is_domain_completion": False,
            "can_claim_paper_progress": False,
        },
    }
    return {
        key: value
        for key, value in envelope.items()
        if value not in (None, "", [], {})
    }


def _source_refs_for_current_work_unit(*items: Mapping[str, Any]) -> list[str]:
    refs: list[str] = []
    for item in items:
        payload = _mapping_copy(item)
        for key in (
            "source_ref",
            "typed_blocker_ref",
            "receipt_ref",
            "source_path",
            "owner_receipt_ref",
        ):
            _append_text_ref(refs, payload.get(key))
        source_refs = payload.get("source_refs")
        if isinstance(source_refs, Mapping):
            for value in source_refs.values():
                _append_text_ref(refs, value)
        else:
            _append_text_ref(refs, source_refs)
        _append_text_ref(refs, payload.get("input_refs"))
        _append_text_ref(refs, payload.get("acceptance_refs"))
    return refs


def _append_text_ref(refs: list[str], value: object) -> None:
    for item in text_list(value):
        if item not in refs:
            refs.append(item)


def _currentness_basis_for_current_work_unit(
    *,
    action: Mapping[str, Any],
    blocker: Mapping[str, Any],
    handoff: Mapping[str, Any],
    runtime_health: Mapping[str, Any],
) -> dict[str, Any]:
    basis: dict[str, Any] = {}
    owner_route = _mapping_copy(handoff.get("owner_route"))
    if owner_route:
        basis.update(owner_route_currentness_basis(owner_route))
    for payload in (handoff, action, blocker, runtime_health):
        basis.update(_mapping_copy(payload.get("owner_route_currentness_basis")))
        basis.update(_mapping_copy(payload.get("currentness_basis")))
    identity = _identity_values({**handoff, **blocker, **action})
    if identity.get("action_type") and not basis.get("action_type"):
        basis["action_type"] = identity["action_type"]
    if identity.get("work_unit_id") and not basis.get("work_unit_id"):
        basis["work_unit_id"] = identity["work_unit_id"]
    if identity.get("fingerprint") and not basis.get("work_unit_fingerprint"):
        basis["work_unit_fingerprint"] = identity["fingerprint"]
    for key in ("route_identity_key", "attempt_idempotency_key"):
        if identity.get(key) and not basis.get(key):
            basis[key] = identity[key]
    return {
        key: value
        for key, value in basis.items()
        if value not in (None, "", [], {})
    }


def _identity_values(value: Mapping[str, Any]) -> dict[str, str | None]:
    basis = _mapping_copy(value.get("owner_route_currentness_basis")) or _mapping_copy(
        value.get("currentness_basis")
    )
    state = _mapping_copy(value.get("state"))
    runtime_health = _mapping_copy(value.get("runtime_health"))
    return {
        "action_type": _non_empty_text(value.get("action_type"))
        or _non_empty_text(runtime_health.get("action_type")),
        "work_unit_id": _non_empty_text(value.get("work_unit_id"))
        or _non_empty_text(value.get("next_work_unit"))
        or _non_empty_text(runtime_health.get("work_unit_id"))
        or _non_empty_text(runtime_health.get("next_work_unit"))
        or _non_empty_text(state.get("next_work_unit"))
        or _non_empty_text(basis.get("work_unit_id")),
        "fingerprint": _non_empty_text(value.get("work_unit_fingerprint"))
        or _non_empty_text(value.get("action_fingerprint"))
        or _non_empty_text(runtime_health.get("work_unit_fingerprint"))
        or _non_empty_text(runtime_health.get("action_fingerprint"))
        or _non_empty_text(basis.get("work_unit_fingerprint")),
        "route_identity_key": _non_empty_text(value.get("route_identity_key"))
        or _non_empty_text(runtime_health.get("route_identity_key"))
        or _non_empty_text(basis.get("route_identity_key")),
        "attempt_idempotency_key": _non_empty_text(value.get("attempt_idempotency_key"))
        or _non_empty_text(runtime_health.get("attempt_idempotency_key"))
        or _non_empty_text(basis.get("attempt_idempotency_key")),
    }


def _work_unit_text(key: str, *items: Mapping[str, Any]) -> str | None:
    for item in items:
        payload = _mapping_copy(item)
        value = _non_empty_text(payload.get(key))
        if value is not None:
            return value
        runtime_health = _mapping_copy(payload.get("runtime_health"))
        value = _non_empty_text(runtime_health.get(key))
        if value is not None:
            return value
    return None


def _executable_action_when_canonical(
    progress: Mapping[str, Any],
    action: Mapping[str, Any] | None,
) -> dict[str, Any]:
    payload = _mapping_copy(action)
    next_action = _mapping_copy(progress.get("next_action"))
    if _non_empty_text(next_action.get("surface_kind")) != "mas_next_action_envelope":
        return {}
    return payload
