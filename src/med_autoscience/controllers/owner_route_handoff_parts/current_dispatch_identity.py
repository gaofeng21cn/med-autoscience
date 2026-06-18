from __future__ import annotations

from typing import Any, Mapping

from med_autoscience.controllers import control_identity
from med_autoscience.controllers.default_executor_action_policy import REQUEST_OWNER_BY_ACTION_TYPE
from med_autoscience.controllers.gate_clearing_batch_work_units import PUBLICATION_GATE_REPLAY_WORK_UNIT_IDS


def canonical_current_dispatch_identity(
    *,
    study_id: str,
    current_owner_action: Mapping[str, Any],
    current_work_unit: Mapping[str, Any],
    current_execution_envelope: Mapping[str, Any],
) -> dict[str, Any]:
    work_unit_status = _text(current_work_unit.get("status"))
    envelope_state = _text(current_execution_envelope.get("state_kind")) or _text(
        current_execution_envelope.get("execution_state_kind")
    )
    if work_unit_status == "typed_blocker":
        owner_gate_identity = _accepted_owner_gate_route_back_identity(
            current_owner_action=current_owner_action,
            current_work_unit=current_work_unit,
            study_id=study_id,
        )
        if owner_gate_identity:
            return owner_gate_identity
    if work_unit_status in {
        "typed_blocker",
        "running_provider_attempt",
        "blocked_current_work_unit",
        "blocked_typed_owner",
        "parked",
    }:
        return {"blocked": True, "source": "current_work_unit", "state_kind": work_unit_status}
    if envelope_state in {
        "typed_blocker",
        "running_provider_attempt",
        "blocked_current_work_unit",
        "blocked_typed_owner",
        "parked",
    }:
        return {"blocked": True, "source": "current_execution_envelope", "state_kind": envelope_state}
    if work_unit_status == "executable_owner_action":
        identity = _current_work_unit_dispatch_identity(current_work_unit, study_id=study_id)
        owner_action_identity = _current_owner_action_dispatch_identity(current_owner_action, study_id=study_id)
        if not identity and owner_action_identity:
            promoted = dict(owner_action_identity)
            promoted["source"] = "current_work_unit"
            return promoted
        identity = _merge_equivalent_current_owner_action_identity(
            current_work_unit_identity=identity,
            current_owner_action_identity=owner_action_identity,
        )
        if identity:
            return identity
        return {"blocked": True, "source": "current_work_unit", "state_kind": work_unit_status}
    if envelope_state == "executable_owner_action" and current_owner_action:
        identity = _current_owner_action_dispatch_identity(current_owner_action, study_id=study_id)
        if identity:
            identity["source"] = "current_execution_envelope"
            return identity
        return {"blocked": True, "source": "current_execution_envelope", "state_kind": envelope_state}
    if current_owner_action:
        identity = _current_owner_action_dispatch_identity(current_owner_action, study_id=study_id)
        if identity:
            return identity
    return {}


def _accepted_owner_gate_route_back_identity(
    *,
    current_owner_action: Mapping[str, Any],
    current_work_unit: Mapping[str, Any],
    study_id: str,
) -> dict[str, Any]:
    if not _current_owner_action_is_accepted_owner_gate_route_back(current_owner_action):
        return {}
    typed_blocker = _current_work_unit_typed_blocker(current_work_unit)
    if _typed_blocker_identity(typed_blocker) != "stage_packet_not_current_selected_dispatch":
        return {}
    identity = _current_owner_action_dispatch_identity(current_owner_action, study_id=study_id)
    work_unit_identity = _current_work_unit_dispatch_identity(current_work_unit, study_id=study_id)
    if not identity or not work_unit_identity:
        return {}
    if _text(identity.get("action_type")) != _text(work_unit_identity.get("action_type")):
        return {}
    if not work_unit_ids_equivalent_for_action(
        action_type=_text(identity.get("action_type")),
        left=_text(identity.get("work_unit_id")),
        right=_text(work_unit_identity.get("work_unit_id")),
    ):
        return {}
    if _text(identity.get("work_unit_fingerprint")) != _text(
        work_unit_identity.get("work_unit_fingerprint")
    ):
        return {}
    identity["source"] = "paper_recovery_state.accepted_owner_gate_decision"
    return identity


def _current_owner_action_is_accepted_owner_gate_route_back(
    current_owner_action: Mapping[str, Any],
) -> bool:
    if _text(current_owner_action.get("source")) == "paper_recovery_state.accepted_owner_gate_decision":
        return True
    if _text(current_owner_action.get("authority")) == "paper_recovery_state.accepted_owner_gate_decision":
        return True
    return _text(current_owner_action.get("source_surface")) == "paper_recovery_state.accepted_owner_gate_decision"


def _current_work_unit_typed_blocker(current_work_unit: Mapping[str, Any]) -> Mapping[str, Any]:
    state = _mapping(current_work_unit.get("state"))
    return _mapping(state.get("typed_blocker")) or _mapping(current_work_unit.get("typed_blocker"))


def _typed_blocker_identity(typed_blocker: Mapping[str, Any]) -> str | None:
    return (
        _text(typed_blocker.get("blocker_id"))
        or _text(typed_blocker.get("blocker_type"))
        or _text(typed_blocker.get("reason"))
        or _text(typed_blocker.get("blocked_reason"))
    )


def dispatch_matches_current_owner_action(
    dispatch: Mapping[str, Any],
    current_owner_action: Mapping[str, Any],
    *,
    canonical_identity: Mapping[str, Any] | None = None,
) -> bool:
    action_type = _text(dispatch.get("action_type"))
    current_action_type = _text(current_owner_action.get("action_type"))
    if action_type is None or current_action_type is None or action_type != current_action_type:
        return False
    current_work_unit_id = _current_owner_action_work_unit_id(current_owner_action)
    if current_work_unit_id is None:
        return False
    dispatch_work_unit_id = owner_route_work_unit_id(dispatch_owner_route(dispatch))
    if not work_unit_ids_equivalent_for_action(
        action_type=action_type,
        left=dispatch_work_unit_id,
        right=current_work_unit_id,
    ):
        return False
    owner_route = dispatch_owner_route(dispatch)
    allowed_actions = set(_string_list(owner_route.get("allowed_actions")))
    if allowed_actions and action_type not in allowed_actions:
        return False
    current_owner_route = _mapping(current_owner_action.get("owner_route"))
    current_allowed_actions = set(_string_list(current_owner_route.get("allowed_actions")))
    if current_allowed_actions and action_type not in current_allowed_actions:
        return False
    current_fingerprint = _current_owner_action_expected_fingerprint(
        current_owner_action=current_owner_action,
        canonical_identity=_mapping(canonical_identity),
    )
    if current_fingerprint is not None and dispatch_work_unit_fingerprint(dispatch) != current_fingerprint:
        return False
    return True


def dispatch_with_current_owner_action_identity(
    *,
    dispatch: Mapping[str, Any],
    current_owner_action: Mapping[str, Any],
    canonical_identity: Mapping[str, Any] | None = None,
) -> Mapping[str, Any]:
    action_type = _text(dispatch.get("action_type"))
    current_action_type = _text(current_owner_action.get("action_type"))
    if action_type is None or current_action_type is None or action_type != current_action_type:
        return dispatch
    if dispatch_matches_current_owner_action(
        dispatch,
        current_owner_action,
        canonical_identity=canonical_identity,
    ):
        return dispatch
    current_owner_route = _current_owner_action_route_for_dispatch(
        dispatch=dispatch,
        current_owner_action=current_owner_action,
        canonical_identity=_mapping(canonical_identity),
    )
    if not current_owner_route:
        return dispatch
    allowed_actions = set(_string_list(current_owner_route.get("allowed_actions")))
    if allowed_actions and action_type not in allowed_actions:
        return dispatch

    updated = dict(dispatch)
    updated["owner_route"] = dict(current_owner_route)
    if next_owner := _default_executor_owner_for_action(
        action_type=action_type,
        dispatch=dispatch,
        current_owner_action=current_owner_action,
        current_owner_route=current_owner_route,
    ):
        updated["next_executable_owner"] = next_owner
    if _current_owner_action_promotes_dispatch_authority(current_owner_action):
        updated["dispatch_authority"] = _text(current_owner_action.get("source"))
    source_fingerprint = _text(current_owner_route.get("source_fingerprint")) or _text(
        current_owner_route.get("work_unit_fingerprint")
    )
    if source_fingerprint is not None:
        updated["source_fingerprint"] = source_fingerprint
        updated["action_fingerprint"] = source_fingerprint

    prompt_contract = dict(_mapping(updated.get("prompt_contract")))
    prompt_contract["owner_route"] = dict(current_owner_route)
    prompt_contract["action_type"] = action_type
    if next_owner := _text(updated.get("next_executable_owner")):
        prompt_contract["next_executable_owner"] = next_owner
    if source_fingerprint is not None:
        prompt_contract["source_fingerprint"] = source_fingerprint
    updated["prompt_contract"] = prompt_contract
    return updated if updated != dict(dispatch) else dispatch


def dispatch_owner_route(dispatch: Mapping[str, Any]) -> Mapping[str, Any]:
    prompt_contract = _mapping(dispatch.get("prompt_contract"))
    return _mapping(dispatch.get("owner_route")) or _mapping(prompt_contract.get("owner_route"))


def owner_route_work_unit_id(owner_route: Mapping[str, Any]) -> str | None:
    source_refs = _mapping(owner_route.get("source_refs"))
    basis = _mapping(source_refs.get("owner_route_currentness_basis"))
    return (
        _text(source_refs.get("work_unit_id"))
        or _text(owner_route.get("work_unit_id"))
        or _text(basis.get("work_unit_id"))
    )


def dispatch_work_unit_fingerprint(dispatch: Mapping[str, Any]) -> str | None:
    owner_route = dispatch_owner_route(dispatch)
    source_refs = _mapping(owner_route.get("source_refs"))
    basis = _mapping(source_refs.get("owner_route_currentness_basis"))
    return (
        _text(dispatch.get("work_unit_fingerprint"))
        or _text(dispatch.get("action_fingerprint"))
        or _text(dispatch.get("source_fingerprint"))
        or _text(owner_route.get("work_unit_fingerprint"))
        or _text(owner_route.get("source_fingerprint"))
        or _text(source_refs.get("work_unit_fingerprint"))
        or _text(source_refs.get("source_fingerprint"))
        or _text(basis.get("work_unit_fingerprint"))
        or _text(basis.get("source_fingerprint"))
    )


def work_unit_ids_equivalent_for_action(
    *,
    action_type: str | None,
    left: str | None,
    right: str | None,
) -> bool:
    if left == right:
        return True
    return (
        action_type == "run_gate_clearing_batch"
        and left in PUBLICATION_GATE_REPLAY_WORK_UNIT_IDS
        and right in PUBLICATION_GATE_REPLAY_WORK_UNIT_IDS
    )


def _current_work_unit_dispatch_identity(
    current_work_unit: Mapping[str, Any],
    *,
    study_id: str,
) -> dict[str, Any]:
    action_type = _text(current_work_unit.get("action_type"))
    work_unit_id = _text(current_work_unit.get("work_unit_id"))
    currentness_basis = _mapping(current_work_unit.get("currentness_basis"))
    fingerprint = (
        _text(current_work_unit.get("work_unit_fingerprint"))
        or _text(current_work_unit.get("action_fingerprint"))
        or _text(currentness_basis.get("work_unit_fingerprint"))
        or _text(currentness_basis.get("source_fingerprint"))
    )
    action_ids = [item for item in (action_type, work_unit_id) if item is not None]
    if action_type is None or work_unit_id is None:
        return {}
    if fingerprint is None or control_identity.is_synthetic_current_owner_ticket(fingerprint):
        fingerprint = _route_currentness_fingerprint_from_basis(
            study_id=study_id,
            action_type=action_type,
            work_unit_id=work_unit_id,
            basis=currentness_basis,
        )
    if fingerprint is None:
        return {}
    identity = {
        "source": "current_work_unit",
        "action_type": action_type,
        "action_ids": action_ids,
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": fingerprint,
    }
    basis = _currentness_basis_from_identity(
        work_unit_id=work_unit_id,
        work_unit_fingerprint=fingerprint,
        source=currentness_basis,
    )
    if basis:
        identity["owner_route_currentness_basis"] = basis
    return identity


def _current_owner_action_dispatch_identity(
    current_owner_action: Mapping[str, Any],
    *,
    study_id: str,
) -> dict[str, Any]:
    action_type = _text(current_owner_action.get("action_type"))
    next_action = _mapping(current_owner_action.get("next_action"))
    work_unit_id = _text(current_owner_action.get("work_unit_id")) or _text(next_action.get("action_id"))
    basis = _mapping(current_owner_action.get("owner_route_currentness_basis"))
    fingerprint = (
        _text(current_owner_action.get("work_unit_fingerprint"))
        or _text(current_owner_action.get("action_fingerprint"))
        or _text(current_owner_action.get("source_fingerprint"))
        or _text(basis.get("work_unit_fingerprint"))
        or _text(basis.get("source_fingerprint"))
    )
    action_ids = list(
        dict.fromkeys(
            [
                item
                for item in (
                    *_string_list(current_owner_action.get("allowed_actions")),
                    action_type,
                    work_unit_id,
                    _text(next_action.get("action_id")),
                )
                if item is not None
            ]
        )
    )
    if action_type is None or work_unit_id is None:
        return {}
    if fingerprint is None or control_identity.is_synthetic_current_owner_ticket(fingerprint):
        fingerprint = _route_currentness_fingerprint_from_basis(
            study_id=study_id,
            action_type=action_type,
            work_unit_id=work_unit_id,
            basis=basis,
        )
    if fingerprint is None:
        return {}
    source = _text(current_owner_action.get("source")) or "current_executable_owner_action"
    identity = {
        "source": source,
        "action_type": action_type,
        "action_ids": action_ids,
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": fingerprint,
    }
    currentness_basis = _currentness_basis_from_identity(
        work_unit_id=work_unit_id,
        work_unit_fingerprint=fingerprint,
        source=basis,
    )
    if source is not None:
        currentness_basis["source"] = source
    if currentness_basis:
        identity["owner_route_currentness_basis"] = currentness_basis
    return identity


def _current_owner_action_route_for_dispatch(
    *,
    dispatch: Mapping[str, Any],
    current_owner_action: Mapping[str, Any],
    canonical_identity: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    current_owner_route = _mapping(current_owner_action.get("owner_route"))
    if current_owner_route:
        return current_owner_route
    action_type = _text(dispatch.get("action_type"))
    current_action_type = _text(current_owner_action.get("action_type"))
    if action_type is None or current_action_type is None or action_type != current_action_type:
        return {}
    current_work_unit_id = _current_owner_action_work_unit_id(current_owner_action)
    if current_work_unit_id is None:
        return {}
    owner_route = dict(dispatch_owner_route(dispatch))
    if not owner_route:
        return {}
    dispatch_work_unit_id = owner_route_work_unit_id(owner_route)
    current_fingerprint = _current_owner_action_expected_fingerprint(
        current_owner_action=current_owner_action,
        canonical_identity=_mapping(canonical_identity),
    )
    if not work_unit_ids_equivalent_for_action(
        action_type=action_type,
        left=dispatch_work_unit_id,
        right=current_work_unit_id,
    ) and not _current_owner_action_can_override_stale_dispatch_work_unit(
        current_owner_action=current_owner_action,
        canonical_identity=_mapping(canonical_identity),
        current_work_unit_id=current_work_unit_id,
        current_fingerprint=current_fingerprint,
    ):
        return {}
    source_refs = dict(_mapping(owner_route.get("source_refs")))
    basis = dict(
        _mapping(current_owner_action.get("owner_route_currentness_basis"))
        or _mapping(_mapping(canonical_identity).get("owner_route_currentness_basis"))
        or _mapping(source_refs.get("owner_route_currentness_basis"))
    )
    basis["work_unit_id"] = current_work_unit_id
    if current_fingerprint is not None:
        basis["work_unit_fingerprint"] = current_fingerprint
    source_refs["work_unit_id"] = current_work_unit_id
    if current_fingerprint is not None:
        source_refs["work_unit_fingerprint"] = current_fingerprint
    if truth_epoch := _text(basis.get("truth_epoch")):
        owner_route["truth_epoch"] = truth_epoch
        owner_route["route_epoch"] = truth_epoch
        source_refs["study_truth_epoch"] = truth_epoch
    if runtime_health_epoch := _text(basis.get("runtime_health_epoch")):
        owner_route["runtime_health_epoch"] = runtime_health_epoch
        source_refs["runtime_health_epoch"] = runtime_health_epoch
    if source_eval_id := _text(basis.get("source_eval_id")):
        source_refs["source_eval_id"] = source_eval_id
    source_refs["owner_route_currentness_basis"] = basis
    if source := _text(current_owner_action.get("source")):
        basis["source"] = source
        source_refs["owner_route_currentness_basis"] = basis
        source_refs["current_owner_action_source"] = source
    owner_route["source_refs"] = source_refs
    owner_route["owner_reason"] = current_work_unit_id
    if current_fingerprint is not None:
        owner_route["work_unit_fingerprint"] = current_fingerprint
        owner_route["source_fingerprint"] = current_fingerprint
    if _text(owner_route.get("idempotency_key")) is None:
        study_id = (
            _text(owner_route.get("study_id"))
            or _text(dispatch.get("study_id"))
            or _text(current_owner_action.get("study_id"))
        )
        identity_basis = current_fingerprint or current_work_unit_id
        owner_route["idempotency_key"] = "::".join(
            item for item in ("owner-route", study_id, identity_basis, action_type) if item
        )
    return owner_route


def _current_owner_action_can_override_stale_dispatch_work_unit(
    *,
    current_owner_action: Mapping[str, Any],
    canonical_identity: Mapping[str, Any],
    current_work_unit_id: str,
    current_fingerprint: str | None,
) -> bool:
    if current_fingerprint is None:
        return False
    basis = _mapping(current_owner_action.get("owner_route_currentness_basis")) or _mapping(
        canonical_identity.get("owner_route_currentness_basis")
    )
    if _text(basis.get("work_unit_id")) != current_work_unit_id:
        return False
    if _text(basis.get("work_unit_fingerprint")) != current_fingerprint:
        return False
    if _text(basis.get("truth_epoch")) is None:
        return False
    return _text(basis.get("runtime_health_epoch")) is not None or _text(basis.get("source_eval_id")) is not None


def _default_executor_owner_for_action(
    *,
    action_type: str,
    dispatch: Mapping[str, Any],
    current_owner_action: Mapping[str, Any],
    current_owner_route: Mapping[str, Any],
) -> str | None:
    return (
        REQUEST_OWNER_BY_ACTION_TYPE.get(action_type)
        or _text(current_owner_route.get("next_owner"))
        or _text(dispatch.get("next_executable_owner"))
        or _text(current_owner_action.get("next_owner"))
    )


def _current_owner_action_promotes_dispatch_authority(current_owner_action: Mapping[str, Any]) -> bool:
    return _text(current_owner_action.get("source")) == "stage_native_workspace_next_action"


def _current_owner_action_work_unit_id(current_owner_action: Mapping[str, Any]) -> str | None:
    next_action = _mapping(current_owner_action.get("next_action"))
    basis = _mapping(current_owner_action.get("owner_route_currentness_basis"))
    return (
        _text(current_owner_action.get("work_unit_id"))
        or _text(next_action.get("action_id"))
        or _text(basis.get("work_unit_id"))
    )


def _current_owner_action_work_unit_fingerprint(
    current_owner_action: Mapping[str, Any],
) -> str | None:
    basis = _mapping(current_owner_action.get("owner_route_currentness_basis"))
    return (
        _text(current_owner_action.get("work_unit_fingerprint"))
        or _text(current_owner_action.get("action_fingerprint"))
        or _text(current_owner_action.get("source_fingerprint"))
        or _text(basis.get("work_unit_fingerprint"))
        or _text(basis.get("source_fingerprint"))
    )


def _merge_equivalent_current_owner_action_identity(
    *,
    current_work_unit_identity: Mapping[str, Any],
    current_owner_action_identity: Mapping[str, Any],
) -> dict[str, Any]:
    work_unit = dict(current_work_unit_identity)
    owner_action = _mapping(current_owner_action_identity)
    if not work_unit or not owner_action:
        return work_unit
    action_type = _text(work_unit.get("action_type"))
    if action_type != _text(owner_action.get("action_type")):
        return work_unit
    work_unit_id = _text(work_unit.get("work_unit_id"))
    owner_action_work_unit_id = _text(owner_action.get("work_unit_id"))
    if not work_unit_ids_equivalent_for_action(
        action_type=action_type,
        left=work_unit_id,
        right=owner_action_work_unit_id,
    ):
        return work_unit
    owner_action_fingerprint = _text(owner_action.get("work_unit_fingerprint"))
    if owner_action_fingerprint is None:
        return work_unit
    work_unit["work_unit_fingerprint"] = owner_action_fingerprint
    action_ids = list(
        dict.fromkeys(
            [
                *list(work_unit.get("action_ids") or []),
                *list(owner_action.get("action_ids") or []),
            ]
        )
    )
    if action_ids:
        work_unit["action_ids"] = action_ids
    current_basis = dict(_mapping(work_unit.get("owner_route_currentness_basis")))
    owner_action_basis = _mapping(owner_action.get("owner_route_currentness_basis"))
    for key in ("truth_epoch", "runtime_health_epoch", "source_eval_id", "source"):
        if not _text(current_basis.get(key)) and (value := _text(owner_action_basis.get(key))):
            current_basis[key] = value
    if work_unit_id is not None:
        current_basis["work_unit_id"] = work_unit_id
    current_basis["work_unit_fingerprint"] = owner_action_fingerprint
    work_unit["owner_route_currentness_basis"] = current_basis
    return work_unit


def _current_owner_action_expected_fingerprint(
    *,
    current_owner_action: Mapping[str, Any],
    canonical_identity: Mapping[str, Any],
) -> str | None:
    return (
        _current_owner_action_work_unit_fingerprint(current_owner_action)
        or _text(canonical_identity.get("work_unit_fingerprint"))
    )


def _currentness_basis_from_identity(
    *,
    work_unit_id: str | None,
    work_unit_fingerprint: str | None,
    source: Mapping[str, Any],
) -> dict[str, str]:
    basis: dict[str, str] = {}
    for key in ("truth_epoch", "runtime_health_epoch", "source_eval_id"):
        if text := _text(source.get(key)):
            basis[key] = text
    if work_unit_id is not None:
        basis["work_unit_id"] = work_unit_id
    if work_unit_fingerprint is not None:
        basis["work_unit_fingerprint"] = work_unit_fingerprint
    return basis


def _route_currentness_fingerprint_from_basis(
    *,
    study_id: str | None,
    action_type: str | None,
    work_unit_id: str | None,
    basis: Mapping[str, Any],
) -> str | None:
    truth_epoch = _text(basis.get("truth_epoch"))
    runtime_health_epoch = _text(basis.get("runtime_health_epoch"))
    source_eval_id = _text(basis.get("source_eval_id"))
    basis_work_unit_id = _text(basis.get("work_unit_id")) or work_unit_id
    if not any((truth_epoch, runtime_health_epoch, source_eval_id)):
        return None
    return control_identity.stable_route_currentness_fingerprint(
        study_id=study_id,
        source="owner_route_currentness_basis",
        work_unit_id=basis_work_unit_id,
        action_type=action_type,
        source_eval_id=source_eval_id,
    )


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [text for text in (_text(entry) for entry in value) if text is not None]


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "canonical_current_dispatch_identity",
    "dispatch_matches_current_owner_action",
    "dispatch_owner_route",
    "dispatch_with_current_owner_action_identity",
    "dispatch_work_unit_fingerprint",
    "owner_route_work_unit_id",
    "work_unit_ids_equivalent_for_action",
]
