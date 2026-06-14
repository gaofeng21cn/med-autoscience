from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from med_autoscience.controllers import control_identity
from med_autoscience.controllers.domain_health_diagnostic_parts.current_ai_reviewer_gate_replay import (
    current_ai_reviewer_gate_replay_fingerprint,
    current_ai_reviewer_gate_replay_source_eval_id,
    is_current_ai_reviewer_gate_replay_fingerprint,
    study_currentness_basis,
)
from med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_handoffs import (
    handoff_dispatch_path,
)
from med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_helpers import (
    first_text as _first_text,
    mapping as _mapping,
    non_empty_text as _non_empty_text,
    text_items as _text_items,
)
from med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_identity import (
    current_action_currentness_basis as _current_action_currentness_basis,
    current_work_unit_opl_authorization_required as _current_work_unit_opl_authorization_required,
    owner_route_currentness_basis_complete as _owner_route_currentness_basis_complete,
)
from med_autoscience.controllers.gate_clearing_batch_work_units import (
    PUBLICATION_GATE_REPLAY_WORK_UNIT_IDS,
)

DEFAULT_EXECUTOR_DISPATCHES = Path("artifacts/supervision/consumer/default_executor_dispatches")
CURRENT_CONTROL_PROVIDER_ADMISSION_ACTION_OWNERS = {
    "return_to_ai_reviewer_workflow": {"ai_reviewer"},
    "run_quality_repair_batch": {"analysis-campaign", "write"},
    "run_gate_clearing_batch": {"finalize", "gate_clearing_batch", "write"},
}
CURRENT_CONTROL_PROVIDER_ADMISSION_DEFAULT_EXECUTABLE_OWNERS = {
    "return_to_ai_reviewer_workflow": "ai_reviewer",
    "run_quality_repair_batch": "write",
    "run_gate_clearing_batch": "gate_clearing_batch",
}
OPL_RUNTIME_ROUTE_OWNERS = {"one-person-lab"}
CURRENT_CONTROL_PROVIDER_ADMISSION_DISPATCH_AUTHORITIES = {
    "return_to_ai_reviewer_workflow": {"ai_reviewer_record_production_handoff"},
    "run_quality_repair_batch": {None, "quality_repair_batch_writer_handoff", "consumer_default_executor_dispatch"},
    "run_gate_clearing_batch": {None, "consumer_default_executor_dispatch"},
}


def _study_current_actions_for_provider_admission(payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    queued_keys = {
        _provider_admission_action_key(item)
        for item in payload.get("action_queue") or []
        if isinstance(item, Mapping)
    }
    for study in payload.get("studies") or []:
        if not isinstance(study, Mapping):
            continue
        action = _study_current_action_for_provider_admission(study)
        if action is None:
            continue
        key = _provider_admission_action_key(action)
        if key in queued_keys:
            continue
        queued_keys.add(key)
        actions.append(action)
    return actions


def _study_current_action_for_provider_admission(study: Mapping[str, Any]) -> dict[str, Any] | None:
    current = _mapping(study.get("current_executable_owner_action"))
    if not current:
        return None
    action_type = _current_action_action_type(current)
    if action_type is None:
        return None
    owner = _non_empty_text(current.get("next_owner")) or _non_empty_text(current.get("owner"))
    executable_owner = _current_control_executable_owner(action_type=action_type, owner=owner)
    if executable_owner is None:
        return None
    work_unit_id = _non_empty_text(current.get("work_unit_id")) or _non_empty_text(current.get("next_work_unit"))
    if work_unit_id is None:
        return None
    study_id = _non_empty_text(study.get("study_id"))
    source_eval_id = current_ai_reviewer_gate_replay_source_eval_id(
        study=study,
        current=current,
        action_type=action_type,
        work_unit_id=work_unit_id,
    )
    eval_bound_fingerprint = current_ai_reviewer_gate_replay_fingerprint(
        study_id=study_id,
        action_type=action_type,
        work_unit_id=work_unit_id,
        source_eval_id=source_eval_id,
    )
    current_work_unit = _mapping(study.get("current_work_unit"))
    current_work_unit_basis = _mapping(current_work_unit.get("currentness_basis"))
    current_action_basis = _mapping(current.get("owner_route_currentness_basis")) or _mapping(
        current.get("currentness_basis")
    )
    repair_precedence = _mapping(current.get("repair_progress_precedence"))
    action_fingerprint = (
        eval_bound_fingerprint
        or _first_currentness_fingerprint(
            current.get("action_fingerprint"),
            current.get("work_unit_fingerprint"),
            current.get("source_fingerprint"),
            repair_precedence.get("source_fingerprint"),
            current_action_basis.get("work_unit_fingerprint"),
            current_action_basis.get("source_fingerprint"),
            current_work_unit.get("action_fingerprint"),
            current_work_unit.get("work_unit_fingerprint"),
            current_work_unit_basis.get("work_unit_fingerprint"),
            current_work_unit_basis.get("source_fingerprint"),
            study_id=study_id,
            action_type=action_type,
            work_unit_id=work_unit_id,
        )
    )
    if action_fingerprint is None and _currentness_basis_can_bind_stable_ticket(
        current_work_unit_basis
    ):
        action_fingerprint = _stable_provider_admission_ticket(
            study_id=study_id,
            action_type=action_type,
            work_unit_id=work_unit_id,
        )
    if action_fingerprint is None:
        return None
    source_refs = {
        key: value
        for key, value in {
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": action_fingerprint,
            "source_eval_id": source_eval_id,
            "owner_route_currentness_basis": study_currentness_basis(
                study=study,
                current=current,
                work_unit_id=work_unit_id,
                work_unit_fingerprint=action_fingerprint,
                source_eval_id=source_eval_id,
            ),
        }.items()
        if value is not None
    }
    return {
        "study_id": study_id,
        "quest_id": _non_empty_text(study.get("quest_id")),
        "action_type": action_type,
        "status": "queued",
        "owner": executable_owner,
        "next_executable_owner": executable_owner,
        "next_work_unit": work_unit_id,
        "work_unit_id": work_unit_id,
        "action_fingerprint": action_fingerprint,
        "work_unit_fingerprint": action_fingerprint,
        "required_output_surface": _required_output_surface(current),
        "provider_attempt_or_lease_required": True,
        "provider_completion_is_domain_completion": False,
        "source_surface": "opl_current_control_state.study_current_executable_owner_action",
        "owner_route": {
            "next_owner": executable_owner,
            "allowed_actions": [action_type],
            "work_unit_fingerprint": action_fingerprint,
            "source_refs": source_refs,
        },
    }


def _provider_admission_action_key(action: Mapping[str, Any]) -> tuple[str | None, str | None, str | None]:
    fingerprint = _non_empty_text(action.get("work_unit_fingerprint")) or _non_empty_text(
        action.get("action_fingerprint")
    )
    if is_current_ai_reviewer_gate_replay_fingerprint(fingerprint):
        return (
            _non_empty_text(action.get("study_id")),
            _current_action_action_type(action),
            fingerprint,
        )
    return (
        _non_empty_text(action.get("study_id")),
        _current_action_action_type(action),
        _canonical_provider_admission_work_unit_id(
            action_type=_current_action_action_type(action),
            work_unit_id=_non_empty_text(action.get("work_unit_id"))
            or _non_empty_text(action.get("next_work_unit")),
        ),
    )


def _current_action_action_type(action: Mapping[str, Any]) -> str | None:
    action_type = _non_empty_text(action.get("action_type"))
    if action_type is not None:
        return action_type
    for item in _text_items(action.get("allowed_actions")):
        if item in CURRENT_CONTROL_PROVIDER_ADMISSION_ACTION_OWNERS:
            return item
    return None


def _stable_provider_admission_ticket(
    *,
    study_id: str | None,
    action_type: str | None,
    work_unit_id: str | None,
) -> str | None:
    return control_identity.stable_current_owner_ticket_fingerprint(
        study_id=study_id,
        work_unit_id=work_unit_id,
        action_type=action_type,
    )


def _first_non_synthetic_fingerprint(*values: object) -> str | None:
    for value in values:
        text = _non_empty_text(value)
        if text is not None and not control_identity.is_synthetic_current_owner_ticket(text):
            return text
    return None


def _first_currentness_fingerprint(
    *values: object,
    study_id: str | None,
    action_type: str | None,
    work_unit_id: str | None,
) -> str | None:
    fingerprint = _first_non_synthetic_fingerprint(*values)
    if fingerprint is not None:
        return fingerprint
    stable_ticket = _stable_provider_admission_ticket(
        study_id=study_id,
        action_type=action_type,
        work_unit_id=work_unit_id,
    )
    if stable_ticket is None:
        return None
    for value in values:
        if _non_empty_text(value) == stable_ticket:
            return stable_ticket
    return None


def _currentness_basis_can_bind_stable_ticket(basis: Mapping[str, Any]) -> bool:
    if _non_empty_text(basis.get("work_unit_id")) is None:
        return False
    if _non_empty_text(basis.get("truth_epoch")) is None:
        return False
    return (
        _non_empty_text(basis.get("runtime_health_epoch")) is not None
        or _non_empty_text(basis.get("source_eval_id")) is not None
    )


def _required_output_surface(current: Mapping[str, Any]) -> str | None:
    return (
        _non_empty_text(current.get("required_output_surface"))
        or _non_empty_text(_mapping(current.get("target_surface")).get("surface_ref"))
    )


def _current_action_can_bind_stable_ticket(
    *,
    status_payload: Mapping[str, Any],
    current: Mapping[str, Any],
    currentness_basis: Mapping[str, Any],
) -> bool:
    if _currentness_basis_can_bind_stable_ticket(currentness_basis):
        return True
    if _non_empty_text(current.get("source_ref")) is not None:
        return True
    if _non_empty_text(current.get("source_eval_id")) is not None:
        return True
    return _non_empty_text(status_payload.get("generated_at")) is not None or _non_empty_text(
        status_payload.get("study_progress_generated_at")
    ) is not None


def _status_with_current_control_study_currentness(
    *,
    status: Mapping[str, Any],
    study: Mapping[str, Any],
) -> dict[str, Any]:
    payload = dict(status)
    for key in (
        "current_work_unit",
        "current_execution_envelope",
        "current_executable_owner_action",
        "current_owner_ticket",
    ):
        if _mapping(payload.get(key)):
            continue
        value = _mapping(study.get(key))
        if value:
            payload[key] = value
    return payload


def _current_action_identity(status_payload: Mapping[str, Any]) -> dict[str, Any]:
    current_work_unit = _mapping(status_payload.get("current_work_unit"))
    if current_work_unit:
        identity = _current_work_unit_identity(current_work_unit)
        if identity:
            return identity
    current = _mapping(status_payload.get("current_executable_owner_action"))
    if not current:
        return {}
    study_id = _non_empty_text(status_payload.get("study_id"))
    target_surface = _mapping(current.get("target_surface"))
    next_action = _mapping(current.get("next_action"))
    action_ids = _text_items(current.get("allowed_actions"))
    action_ids.extend(
        _text_items(
            [
                current.get("action_type"),
                current.get("work_unit_id"),
                next_action.get("action_id"),
            ]
        )
    )
    action_ids = list(dict.fromkeys(action_ids))
    work_unit_id = _non_empty_text(current.get("work_unit_id")) or _non_empty_text(
        next_action.get("action_id")
    )
    surface_key = _non_empty_text(current.get("surface_key")) or _non_empty_text(
        target_surface.get("surface_key")
    )
    source_ref = _non_empty_text(current.get("source_ref")) or _non_empty_text(
        current.get("latest_owner_answer_ref")
    )
    action_type = _current_action_action_type(current)
    current_action_basis = _mapping(current.get("owner_route_currentness_basis")) or _mapping(
        current.get("currentness_basis")
    )
    fingerprint = _first_currentness_fingerprint(
        current.get("work_unit_fingerprint"),
        current.get("action_fingerprint"),
        current.get("source_fingerprint"),
        _mapping(current.get("repair_progress_precedence")).get("source_fingerprint"),
        current_action_basis.get("work_unit_fingerprint"),
        current_action_basis.get("source_fingerprint"),
        study_id=study_id,
        action_type=action_type,
        work_unit_id=work_unit_id,
    )
    if fingerprint is None and _current_action_can_bind_stable_ticket(
        status_payload=status_payload,
        current=current,
        currentness_basis=current_action_basis,
    ):
        fingerprint = _stable_provider_admission_ticket(
            study_id=study_id,
            action_type=action_type,
            work_unit_id=work_unit_id,
        )
    fingerprints: list[str] = []
    if fingerprint is not None:
        fingerprints.append(fingerprint)
    if work_unit_id is not None and source_ref is not None:
        fingerprints.append(
            "stage-current-owner-delta::"
            f"{work_unit_id}::{surface_key or 'unspecified_surface'}::{source_ref}"
        )
    repair_precedence = _mapping(current.get("repair_progress_precedence"))
    repair_fingerprint = _non_empty_text(repair_precedence.get("source_fingerprint"))
    if repair_fingerprint is not None:
        fingerprints.append(repair_fingerprint)
    ticket = _mapping(status_payload.get("current_owner_ticket"))
    for item in ticket.get("required_input_refs") or []:
        text = _non_empty_text(item)
        if text is not None and text.startswith("sha256:"):
            fingerprints.append(text)
    fingerprints = list(dict.fromkeys(fingerprints))
    if fingerprint is None and fingerprints:
        fingerprint = fingerprints[0]
    basis = _current_action_currentness_basis(
        status_payload=status_payload,
        current=current,
        work_unit_id=work_unit_id,
        work_unit_fingerprint=fingerprint,
    )
    return {
        "action_ids": action_ids,
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": fingerprint,
        "work_unit_fingerprints": fingerprints,
        "source_ref": source_ref,
        "source": _non_empty_text(current.get("source")),
        "next_owner": _non_empty_text(current.get("next_owner")),
        "currentness_basis": basis if basis else None,
    }


def _current_control_action_identity(action: Mapping[str, Any]) -> dict[str, Any]:
    if _non_empty_text(action.get("source_surface")) not in {
        None,
        "opl_current_control_state.action_queue",
        "opl_current_control_state.study_current_executable_owner_action",
    }:
        return {}
    action_type = _current_action_action_type(action)
    work_unit_id = (
        _non_empty_text(action.get("work_unit_id"))
        or _non_empty_text(action.get("next_work_unit"))
        or _non_empty_text(action.get("controller_work_unit_id"))
    )
    fingerprint = (
        _non_empty_text(action.get("work_unit_fingerprint"))
        or _non_empty_text(action.get("action_fingerprint"))
        or _non_empty_text(action.get("source_fingerprint"))
    )
    owner_route = _mapping(action.get("owner_route"))
    source_refs = _mapping(owner_route.get("source_refs"))
    currentness_basis = _mapping(source_refs.get("owner_route_currentness_basis"))
    if not _owner_route_currentness_basis_complete(currentness_basis):
        return {}
    work_unit_id = (
        work_unit_id
        or _non_empty_text(source_refs.get("work_unit_id"))
        or _non_empty_text(currentness_basis.get("work_unit_id"))
    )
    fingerprint = (
        fingerprint
        or _non_empty_text(source_refs.get("work_unit_fingerprint"))
        or _non_empty_text(currentness_basis.get("work_unit_fingerprint"))
    )
    if action_type is None or work_unit_id is None or fingerprint is None:
        return {}
    if not _current_control_action_requests_provider_admission(action):
        return {}
    fingerprints = [
        item
        for item in (
            _non_empty_text(action.get("work_unit_fingerprint")),
            _non_empty_text(action.get("action_fingerprint")),
            _non_empty_text(action.get("source_fingerprint")),
            _non_empty_text(source_refs.get("work_unit_fingerprint")),
            _non_empty_text(currentness_basis.get("work_unit_fingerprint")),
        )
        if item is not None
    ]
    return {
        "action_ids": [action_type, work_unit_id],
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": fingerprint,
        "work_unit_fingerprints": list(dict.fromkeys(fingerprints)),
        "source": _non_empty_text(action.get("source_surface"))
        or "opl_current_control_state.action_queue",
        "next_owner": _non_empty_text(action.get("next_executable_owner"))
        or _non_empty_text(action.get("owner"))
        or _non_empty_text(owner_route.get("next_owner")),
    }


def _current_work_unit_identity(current_work_unit: Mapping[str, Any]) -> dict[str, Any]:
    status = _non_empty_text(current_work_unit.get("status"))
    if status not in {"executable_owner_action", "typed_blocker"}:
        return {}
    opl_authorization_typed_blocker = (
        status == "typed_blocker"
        and _current_work_unit_opl_authorization_required(current_work_unit)
    )
    if status == "typed_blocker" and not opl_authorization_typed_blocker:
        return {}
    state = _mapping(current_work_unit.get("state"))
    currentness_basis = _mapping(current_work_unit.get("currentness_basis"))
    action_type = _non_empty_text(current_work_unit.get("action_type"))
    work_unit_id = _non_empty_text(current_work_unit.get("work_unit_id"))
    source_eval_id = current_ai_reviewer_gate_replay_source_eval_id(
        study={"current_work_unit": current_work_unit},
        current={},
        action_type=action_type,
        work_unit_id=work_unit_id,
    )
    eval_bound_fingerprint = current_ai_reviewer_gate_replay_fingerprint(
        study_id=_non_empty_text(current_work_unit.get("study_id")),
        action_type=action_type,
        work_unit_id=work_unit_id,
        source_eval_id=source_eval_id,
    )
    fingerprint = (
        eval_bound_fingerprint
        or _first_currentness_fingerprint(
            current_work_unit.get("work_unit_fingerprint"),
            current_work_unit.get("action_fingerprint"),
            currentness_basis.get("work_unit_fingerprint"),
            currentness_basis.get("source_fingerprint"),
            study_id=_non_empty_text(current_work_unit.get("study_id")),
            action_type=action_type,
            work_unit_id=work_unit_id,
        )
    )
    fingerprints = [
        item
        for item in (
            eval_bound_fingerprint,
            _non_empty_text(current_work_unit.get("work_unit_fingerprint")),
            _non_empty_text(current_work_unit.get("action_fingerprint")),
            _non_empty_text(currentness_basis.get("work_unit_fingerprint")),
            _non_empty_text(currentness_basis.get("source_fingerprint")),
        )
        if item is not None
        and (
            not control_identity.is_synthetic_current_owner_ticket(item)
            or item == fingerprint
        )
    ]
    return {
        "action_ids": [item for item in (action_type, work_unit_id) if item is not None],
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": fingerprint,
        "work_unit_fingerprints": list(dict.fromkeys(fingerprints)),
        "source_ref": _first_text(current_work_unit.get("input_refs"))
        or _non_empty_text(state.get("source_ref")),
        "source": _non_empty_text(state.get("source")) or "canonical_current_work_unit",
        "next_owner": _non_empty_text(current_work_unit.get("owner")),
        "opl_execution_authorization_required": opl_authorization_typed_blocker,
    }


def _canonical_provider_admission_work_unit_id(
    *,
    action_type: str | None,
    work_unit_id: str | None,
) -> str | None:
    if action_type == "run_gate_clearing_batch" and work_unit_id in PUBLICATION_GATE_REPLAY_WORK_UNIT_IDS:
        return "publication_gate_replay"
    return work_unit_id


def _current_control_action_requests_provider_admission(action: Mapping[str, Any]) -> bool:
    action_type = _non_empty_text(action.get("action_type"))
    if action_type is None:
        return False
    if _non_empty_text(action.get("status")) not in {"queued", "pending", "ready"}:
        return False
    owner = _non_empty_text(action.get("next_executable_owner")) or _non_empty_text(action.get("owner"))
    return _current_control_executable_owner(action_type=action_type, owner=owner) is not None


def _current_control_owner_allowed(*, action_type: str, owner: str | None) -> bool:
    expected_owners = CURRENT_CONTROL_PROVIDER_ADMISSION_ACTION_OWNERS.get(action_type)
    return owner in expected_owners if expected_owners is not None else False


def _current_control_executable_owner(
    *,
    action_type: str,
    owner: str | None,
    dispatch_payload: Mapping[str, Any] | None = None,
    owner_route: Mapping[str, Any] | None = None,
) -> str | None:
    if _current_control_owner_allowed(action_type=action_type, owner=owner):
        return owner
    if owner not in OPL_RUNTIME_ROUTE_OWNERS:
        return None
    for candidate in (
        _non_empty_text(_mapping(dispatch_payload).get("next_executable_owner")),
        _non_empty_text(_mapping(owner_route).get("next_owner")),
        CURRENT_CONTROL_PROVIDER_ADMISSION_DEFAULT_EXECUTABLE_OWNERS.get(action_type),
    ):
        if _current_control_owner_allowed(action_type=action_type, owner=candidate):
            return candidate
    return None


def _dispatch_authority_allows_current_control_provider_admission(
    *,
    action_type: str,
    dispatch_authority: str | None,
) -> bool:
    allowed = CURRENT_CONTROL_PROVIDER_ADMISSION_DISPATCH_AUTHORITIES.get(action_type)
    return dispatch_authority in allowed if allowed is not None else False


def _current_control_action_dispatch_path(
    action: Mapping[str, Any],
    *,
    study_root: Path,
    action_type: str,
) -> Path | None:
    explicit = handoff_dispatch_path(action)
    if explicit is not None:
        return Path(explicit).expanduser().resolve()
    return (Path(study_root).expanduser().resolve() / DEFAULT_EXECUTOR_DISPATCHES / f"{action_type}.json")


def _merge_owner_route_currentness(
    *,
    dispatch_payload: Mapping[str, Any],
    owner_route: Mapping[str, Any],
    work_unit_id: str,
    work_unit_fingerprint: str,
) -> dict[str, Any]:
    route = _mapping(dispatch_payload.get("owner_route"))
    if not route:
        route = dict(owner_route)
    source_refs = _mapping(route.get("source_refs"))
    candidate_source_refs = _mapping(owner_route.get("source_refs"))
    basis = (
        _mapping(candidate_source_refs.get("owner_route_currentness_basis"))
        or _mapping(source_refs.get("owner_route_currentness_basis"))
    )
    basis = {
        **basis,
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": work_unit_fingerprint,
    }
    source_refs = {
        **source_refs,
        **{
            key: value
            for key, value in candidate_source_refs.items()
            if key not in source_refs or key == "owner_route_currentness_basis"
        },
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": work_unit_fingerprint,
        "owner_route_currentness_basis": basis,
    }
    route["source_refs"] = source_refs
    route["work_unit_fingerprint"] = work_unit_fingerprint
    return route
