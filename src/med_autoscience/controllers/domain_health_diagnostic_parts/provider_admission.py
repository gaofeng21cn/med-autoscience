from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from med_autoscience.controllers import control_identity
from med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_boundaries import (
    PROVIDER_ADMISSION_AUTHORITY_BOUNDARY,
    STAGE_TRANSITION_AUTHORITY_BOUNDARY,
)
from med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_handoffs import (
    handoff_dispatch_path,
    handoff_work_unit_id,
    materialized_record_only_provider_handoff,
    materialized_record_only_provider_handoffs,
    provider_admission_pending_dispatch_result,
)
from med_autoscience.controllers.gate_clearing_batch_work_units import PUBLICATION_GATE_REPLAY_WORK_UNIT_IDS
from med_autoscience.controllers.opl_execution_boundary import OPL_EXECUTION_AUTHORIZATION_BLOCKER
from med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_helpers import (
    first_text as _first_text,
    mapping as _mapping,
    non_empty_text as _non_empty_text,
    read_json_object as _read_json_object,
    text_items as _text_items,
)
from med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_identity import (
    current_action_currentness_basis as _current_action_currentness_basis,
    current_identity_is_opl_authorization_typed_blocker as _current_identity_is_opl_authorization_typed_blocker,
    current_work_unit_opl_authorization_required as _current_work_unit_opl_authorization_required,
    matches_current_action as _matches_current_action,
    matches_current_action_without_fingerprint as _matches_current_action_without_fingerprint,
    owner_route_currentness_basis_complete as _owner_route_currentness_basis_complete,
    status_requires_current_identity as _status_requires_current_identity,
    work_unit_ids_equivalent_for_action as _work_unit_ids_equivalent_for_action,
)
from med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_probe_identity import (
    provider_attempt_matches_identity,
    provider_probe_has_matching_attempt,
    provider_probe_has_non_running_actions,
    study_has_running_provider_attempt,
)
from med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_status import (
    execution_state_kind as _execution_state_kind,
    status_blocks_action_queue_self_identity as _status_blocks_action_queue_self_identity,
)
from med_autoscience.controllers.domain_health_diagnostic_parts.current_ai_reviewer_gate_replay import (
    current_ai_reviewer_gate_replay_fingerprint,
    current_ai_reviewer_gate_replay_source_eval_id,
    is_current_ai_reviewer_gate_replay_fingerprint,
    source_eval_id_from_mapping,
    study_currentness_basis,
)


DEFAULT_EXECUTOR_EXECUTION_LATEST = Path(
    "artifacts/supervision/consumer/default_executor_execution/latest.json"
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
PROVIDER_ADMISSION_FAIL_CLOSED_TYPED_BLOCKERS = frozenset(
    {
        "no_selected_dispatch_for_requested_action_types",
        "owner_route_no_selected_dispatch_for_requested_action",
        "run_quality_repair_batch_no_longer_selected_current_owner_route",
        "run_quality_repair_batch_not_visible_in_current_opl_control_state",
        "stale_stage_attempt_current_owner_route_superseded",
        "stale_stage_packet_current_owner_route_changed",
        "stage_packet_superseded_by_current_consumed_domain_transition",
    }
)


def persisted_provider_admission_candidates(
    *,
    study_root: Path,
    status_payload: Mapping[str, Any] | None = None,
) -> list[dict[str, Any]]:
    execution_ref = Path(study_root).expanduser().resolve() / DEFAULT_EXECUTOR_EXECUTION_LATEST
    payload = _read_json_object(execution_ref)
    if payload is None:
        return []
    return provider_admission_candidates_from_execution_payload(
        payload,
        execution_ref=str(execution_ref),
        status_payload=status_payload,
    )


def current_control_provider_admission_candidates(
    current_control_payload: Mapping[str, Any] | None,
    *,
    study_root: Path,
    status_payload: Mapping[str, Any] | None = None,
    current_control_ref: str | None = None,
) -> list[dict[str, Any]]:
    payload = _mapping(current_control_payload)
    if not payload:
        return []
    status = _mapping(status_payload)
    status_study_id = _non_empty_text(status.get("study_id")) or Path(study_root).name
    studies_by_id = {
        study_id: item
        for item in payload.get("studies") or []
        if isinstance(item, Mapping)
        and (study_id := _non_empty_text(item.get("study_id"))) is not None
    }
    candidates: list[dict[str, Any]] = []
    queued_actions = [
        item for item in payload.get("action_queue") or [] if isinstance(item, Mapping)
    ]
    queued_actions.extend(_study_current_actions_for_provider_admission(payload))
    for action in queued_actions:
        if not isinstance(action, Mapping):
            continue
        study = _mapping(studies_by_id.get(_non_empty_text(action.get("study_id")) or status_study_id))
        effective_status = _status_with_current_control_study_currentness(status=status, study=study)
        current_action_identity = _current_action_identity(effective_status)
        candidate = provider_admission_candidate_from_current_control_action(
            action,
            study_root=study_root,
            status_study_id=status_study_id,
            current_action_identity=current_action_identity,
            status_payload=effective_status,
            current_control_ref=current_control_ref,
            study_payload=study,
        )
        if candidate is None:
            action_identity = _current_control_action_identity(action)
            if (
                action_identity
                and action_identity != current_action_identity
                and not _status_blocks_action_queue_self_identity(
                    effective_status,
                    current_identity=current_action_identity,
                    current_identity_required=_status_requires_current_identity(effective_status),
                )
            ):
                candidate = provider_admission_candidate_from_current_control_action(
                    action,
                    study_root=study_root,
                    status_study_id=status_study_id,
                    current_action_identity=action_identity,
                    status_payload=effective_status,
                    current_control_ref=current_control_ref,
                    study_payload=study,
                )
        if candidate is not None:
            candidates.append(candidate)
    return candidates


def provider_admission_candidate_from_current_control_action(
    action: Mapping[str, Any],
    *,
    study_root: Path,
    status_study_id: str | None = None,
    current_action_identity: Mapping[str, Any] | None = None,
    status_payload: Mapping[str, Any] | None = None,
    current_control_ref: str | None = None,
    study_payload: Mapping[str, Any] | None = None,
) -> dict[str, Any] | None:
    if not _current_control_action_requests_provider_admission(action):
        return None
    current_identity = _mapping(current_action_identity)
    if not current_identity:
        return None
    study_id = _non_empty_text(action.get("study_id")) or status_study_id
    if status_study_id is not None and study_id != status_study_id:
        return None
    if study_id is None:
        return None
    action_type = _non_empty_text(action.get("action_type"))
    if action_type is None:
        return None
    study = _mapping(study_payload)
    owner_route = _mapping(action.get("owner_route")) or _mapping(study.get("owner_route"))
    source_refs = _mapping(owner_route.get("source_refs"))
    currentness_basis = _mapping(source_refs.get("owner_route_currentness_basis"))
    work_unit_id = (
        _non_empty_text(action.get("work_unit_id"))
        or _non_empty_text(action.get("next_work_unit"))
        or _non_empty_text(action.get("controller_work_unit_id"))
        or _non_empty_text(source_refs.get("work_unit_id"))
        or _non_empty_text(currentness_basis.get("work_unit_id"))
    )
    action_fingerprint = _first_currentness_fingerprint(
        action.get("action_fingerprint"),
        action.get("work_unit_fingerprint"),
        action.get("source_fingerprint"),
        source_refs.get("work_unit_fingerprint"),
        currentness_basis.get("work_unit_fingerprint"),
        study_id=study_id,
        action_type=action_type,
        work_unit_id=work_unit_id,
    )
    dispatch_path = _current_control_action_dispatch_path(action, study_root=study_root, action_type=action_type)
    dispatch_payload = _read_json_object(dispatch_path) if dispatch_path is not None else None
    if dispatch_payload is None:
        return None
    if _non_empty_text(dispatch_payload.get("dispatch_status")) != "ready":
        return None
    if _non_empty_text(dispatch_payload.get("action_type")) != action_type:
        return None
    if not _dispatch_authority_allows_current_control_provider_admission(
        action_type=action_type,
        dispatch_authority=_non_empty_text(dispatch_payload.get("dispatch_authority")),
    ):
        return None
    next_executable_owner = _current_control_executable_owner(
        action_type=action_type,
        owner=(
            _non_empty_text(action.get("next_executable_owner"))
            or _non_empty_text(action.get("owner"))
            or _non_empty_text(owner_route.get("next_owner"))
        ),
        dispatch_payload=dispatch_payload,
        owner_route=owner_route,
    )
    if next_executable_owner is None:
        return None
    if work_unit_id is None:
        work_unit_id = handoff_work_unit_id(dispatch_payload)
    if action_fingerprint is None:
        action_fingerprint = _work_unit_fingerprint(dispatch_payload)
    if work_unit_id is None or action_fingerprint is None:
        return None
    execution = {
        **dict(dispatch_payload),
        "source": _non_empty_text(action.get("source_surface")) or "opl_current_control_state.action_queue",
        "current_control_ref": current_control_ref,
        "study_id": study_id,
        "quest_id": _non_empty_text(action.get("quest_id"))
        or _non_empty_text(study.get("quest_id"))
        or _non_empty_text(dispatch_payload.get("quest_id")),
        "action_type": action_type,
        "execution_status": "handoff_ready",
        "provider_attempt_or_lease_required": True,
        "provider_completion_is_domain_completion": False,
        "owner_route_current": True,
        "dispatch_path": str(dispatch_path),
        "action_fingerprint": action_fingerprint,
        "next_executable_owner": next_executable_owner,
        "required_output_surface": (
            _non_empty_text(action.get("required_output_surface"))
            or _non_empty_text(_mapping(owner_route.get("target_surface")).get("surface_ref"))
            or _non_empty_text(dispatch_payload.get("required_output_surface"))
        ),
        "owner_route": _merge_owner_route_currentness(
            dispatch_payload=_mapping(dispatch_payload),
            owner_route=owner_route,
            work_unit_id=work_unit_id,
            work_unit_fingerprint=action_fingerprint,
        ),
    }
    if _status_envelope_blocks_provider_admission(
        _mapping(status_payload),
        execution=execution,
        current_action_identity=current_identity,
    ):
        return None
    candidate = provider_admission_candidate_from_execution(
        execution,
        execution_ref=current_control_ref,
        status_study_id=status_study_id,
        current_action_identity=current_identity,
    )
    if candidate is None:
        return None
    candidate["source"] = _non_empty_text(action.get("source_surface")) or "opl_current_control_state.action_queue"
    candidate["current_control_ref"] = current_control_ref
    candidate["dispatch_path"] = str(dispatch_path)
    basis = _mapping(candidate.get("currentness_basis")) or _mapping(
        _mapping(candidate.get("owner_route")).get("source_refs", {})
    ).get("owner_route_currentness_basis")
    current_identity_basis = _mapping(current_identity.get("currentness_basis"))
    if isinstance(basis, Mapping):
        candidate["currentness_basis"] = {
            **dict(current_identity_basis),
            **dict(basis),
            "work_unit_id": _non_empty_text(basis.get("work_unit_id")) or work_unit_id,
            "work_unit_fingerprint": _non_empty_text(basis.get("work_unit_fingerprint"))
            or action_fingerprint,
        }
        if not _owner_route_currentness_basis_complete(candidate["currentness_basis"]):
            candidate["currentness_basis"] = {
                **dict(candidate["currentness_basis"]),
                "truth_epoch": _non_empty_text(candidate["currentness_basis"].get("truth_epoch"))
                or _non_empty_text(current_identity_basis.get("truth_epoch")),
                "runtime_health_epoch": _non_empty_text(
                    candidate["currentness_basis"].get("runtime_health_epoch")
                )
                or _non_empty_text(current_identity_basis.get("runtime_health_epoch")),
                "source_eval_id": _non_empty_text(candidate["currentness_basis"].get("source_eval_id"))
                or _non_empty_text(current_identity_basis.get("source_eval_id")),
            }
    candidate["source_refs"] = {
        **_mapping(candidate.get("source_refs")),
        "current_control_ref": current_control_ref,
        "dispatch_path": str(dispatch_path),
    }
    return candidate


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
    action_fingerprint = (
        eval_bound_fingerprint
        or _first_currentness_fingerprint(
            current.get("action_fingerprint"),
            current.get("work_unit_fingerprint"),
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


def provider_admission_candidates_from_execution_payload(
    execution_payload: Mapping[str, Any],
    *,
    execution_ref: str | None = None,
    status_payload: Mapping[str, Any] | None = None,
) -> list[dict[str, Any]]:
    status = _mapping(status_payload)
    status_study_id = _non_empty_text(status.get("study_id"))
    current_action_identity = _current_action_identity(status)
    if _status_requires_current_identity(status) and not current_action_identity:
        return []
    candidates: list[dict[str, Any]] = []
    for item in execution_payload.get("executions") or []:
        if not isinstance(item, Mapping):
            continue
        if _status_envelope_blocks_provider_admission(
            status,
            execution=item,
            current_action_identity=current_action_identity,
        ):
            continue
        candidate = provider_admission_candidate_from_execution(
            item,
            execution_ref=execution_ref,
            status_study_id=status_study_id,
            current_action_identity=current_action_identity,
        )
        if candidate is not None:
            candidates.append(candidate)
    return candidates


def provider_admission_candidate_from_execution(
    execution: Mapping[str, Any],
    *,
    execution_ref: str | None = None,
    status_study_id: str | None = None,
    current_action_identity: Mapping[str, Any] | None = None,
) -> dict[str, Any] | None:
    if not _execution_requests_provider_admission(execution):
        return None
    if not _provider_attempt_required(execution):
        return None
    if execution.get("owner_route_current") is False:
        return None
    study_id = _non_empty_text(execution.get("study_id"))
    if status_study_id is not None and study_id != status_study_id:
        return None
    action_type = _non_empty_text(execution.get("action_type"))
    work_unit_id = handoff_work_unit_id(execution)
    work_unit_fingerprint = _work_unit_fingerprint(execution)
    dispatch_path = handoff_dispatch_path(execution)
    if (
        study_id is None
        or action_type is None
        or work_unit_id is None
        or work_unit_fingerprint is None
        or dispatch_path is None
    ):
        return None
    current_identity = _mapping(current_action_identity)
    if (
        not _matches_current_action(
            action_type=action_type,
            work_unit_id=work_unit_id,
            work_unit_fingerprint=work_unit_fingerprint,
            current_action_identity=current_identity,
        )
        and not _authorization_required_execution_matches_current_action(
            execution,
            current_action_identity=current_identity,
        )
        and not _gate_replay_authorization_consumes_current_ai_reviewer_record(
            execution,
            current_action_identity=current_identity,
        )
    ):
        return None
    owner_route = _mapping(execution.get("owner_route"))
    source_refs = _mapping(owner_route.get("source_refs"))
    currentness_basis = _mapping(source_refs.get("owner_route_currentness_basis")) or _mapping(
        _mapping(_mapping(execution.get("prompt_contract")).get("owner_route_currentness_basis"))
    )
    current_identity_basis = _mapping(current_identity.get("currentness_basis"))
    if currentness_basis or current_identity_basis:
        currentness_basis = {
            **dict(current_identity_basis),
            **dict(currentness_basis),
            "work_unit_id": _non_empty_text(currentness_basis.get("work_unit_id")) or work_unit_id,
            "work_unit_fingerprint": _non_empty_text(currentness_basis.get("work_unit_fingerprint"))
            or work_unit_fingerprint,
        }
    return {
        "surface": "opl_provider_admission_candidate",
        "schema_version": 1,
        "status": "provider_admission_pending",
        "source": "default_executor_execution",
        "execution_ref": execution_ref,
        "study_id": study_id,
        "quest_id": _non_empty_text(execution.get("quest_id")),
        "action_type": action_type,
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": work_unit_fingerprint,
        "work_unit_fingerprints": _work_unit_fingerprints(
            execution,
            canonical_fingerprint=work_unit_fingerprint,
        ),
        "action_fingerprint": _non_empty_text(execution.get("action_fingerprint")) or work_unit_fingerprint,
        "dispatch_path": dispatch_path,
        "dispatch_authority": _non_empty_text(execution.get("dispatch_authority")),
        "owner_callable_surface": _non_empty_text(execution.get("owner_callable_surface")),
        "blocked_reason": _execution_blocked_reason(execution),
        "next_executable_owner": _non_empty_text(execution.get("next_executable_owner")),
        "required_output_surface": _non_empty_text(execution.get("required_output_surface")),
        "provider_attempt_or_lease_required": True,
        "provider_completion_is_domain_completion": False,
        "owner_route_current": execution.get("owner_route_current") is not False,
        "owner_route_basis": _non_empty_text(execution.get("owner_route_basis")),
        "currentness_basis": dict(currentness_basis) if currentness_basis else None,
        "authority_boundary": dict(PROVIDER_ADMISSION_AUTHORITY_BOUNDARY),
        "stage_transition_authority_boundary": dict(STAGE_TRANSITION_AUTHORITY_BOUNDARY),
        "source_refs": {
            key: source_refs[key]
            for key in (
                "work_unit_id",
                "work_unit_fingerprint",
                "blocked_reason",
                "publication_eval_path",
                "quest_root",
                "study_truth_epoch",
                "runtime_health_epoch",
            )
            if key in source_refs
        },
    }


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
    action_ids.extend(_text_items([
        current.get("action_type"),
        current.get("work_unit_id"),
        next_action.get("action_id"),
    ]))
    action_ids = list(dict.fromkeys(action_ids))
    work_unit_id = _non_empty_text(current.get("work_unit_id")) or _non_empty_text(next_action.get("action_id"))
    surface_key = _non_empty_text(current.get("surface_key")) or _non_empty_text(target_surface.get("surface_key"))
    source_ref = _non_empty_text(current.get("source_ref")) or _non_empty_text(current.get("latest_owner_answer_ref"))
    action_type = _current_action_action_type(current)
    current_action_basis = _mapping(current.get("owner_route_currentness_basis")) or _mapping(
        current.get("currentness_basis")
    )
    fingerprint = _first_currentness_fingerprint(
        current.get("work_unit_fingerprint"),
        current.get("action_fingerprint"),
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
        "source": _non_empty_text(action.get("source_surface")) or "opl_current_control_state.action_queue",
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
        "source_ref": _first_text(current_work_unit.get("input_refs")) or _non_empty_text(state.get("source_ref")),
        "source": _non_empty_text(state.get("source")) or "canonical_current_work_unit",
        "next_owner": _non_empty_text(current_work_unit.get("owner")),
        "opl_execution_authorization_required": opl_authorization_typed_blocker,
    }


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


def _status_envelope_blocks_provider_admission(
    status_payload: Mapping[str, Any],
    *,
    execution: Mapping[str, Any],
    current_action_identity: Mapping[str, Any] | None = None,
) -> bool:
    current_work_unit = _mapping(status_payload.get("current_work_unit"))
    current_work_unit_status = _non_empty_text(current_work_unit.get("status"))
    if current_work_unit_status in {
        "running_provider_attempt",
        "blocked_current_work_unit",
        "blocked_typed_owner",
        "parked",
    }:
        return True
    envelope = _mapping(status_payload.get("current_execution_envelope"))
    state_kind = _execution_state_kind(status_payload)
    if state_kind in {
        "parked",
        "running_provider_attempt",
        "blocked_current_work_unit",
        "blocked_typed_owner",
    }:
        return True
    if state_kind != "typed_blocker":
        return False
    return not _typed_blocker_envelope_allows_provider_admission(
        envelope,
        execution=execution,
        current_action_identity=_mapping(current_action_identity),
    )


def _typed_blocker_envelope_allows_provider_admission(
    envelope: Mapping[str, Any],
    *,
    execution: Mapping[str, Any],
    current_action_identity: Mapping[str, Any],
) -> bool:
    blocker = _mapping(envelope.get("typed_blocker"))
    blocker_reason = (
        _non_empty_text(blocker.get("blocker_id"))
        or _non_empty_text(blocker.get("blocker_type"))
        or _non_empty_text(blocker.get("reason"))
    )
    if blocker_reason in PROVIDER_ADMISSION_FAIL_CLOSED_TYPED_BLOCKERS:
        return False
    if _explicit_current_action_execution_matches_current_action(
        execution,
        current_action_identity=current_action_identity,
    ):
        return True
    if _authorization_required_execution_matches_current_action(
        execution,
        current_action_identity=current_action_identity,
    ):
        return True
    if _repair_progress_ai_reviewer_execution_matches_current_action(
        execution,
        current_action_identity=current_action_identity,
    ):
        return True
    if _repair_progress_gate_clearing_execution_matches_current_action(
        execution,
        current_action_identity=current_action_identity,
    ):
        return True
    if _publication_eval_repair_execution_matches_current_action(
        execution,
        current_action_identity=current_action_identity,
    ):
        return True
    if _gate_replay_authorization_consumes_current_ai_reviewer_record(
        execution,
        current_action_identity=current_action_identity,
    ):
        return True
    return blocker_reason in {
        "medical_paper_readiness_missing",
        "medical_paper_readiness_not_ready",
    } and _publication_surface_write_repair_execution_matches_current_action(
        execution,
        current_action_identity=current_action_identity,
    )


def _explicit_current_action_execution_matches_current_action(
    execution: Mapping[str, Any],
    *,
    current_action_identity: Mapping[str, Any],
) -> bool:
    if not current_action_identity:
        return False
    if _current_identity_is_opl_authorization_typed_blocker(current_action_identity):
        return False
    if _non_empty_text(current_action_identity.get("source")) == "canonical_current_work_unit":
        return False
    if not _provider_attempt_required(execution):
        return False
    if execution.get("owner_route_current") is False:
        return False
    action_type = _non_empty_text(execution.get("action_type"))
    work_unit_id = handoff_work_unit_id(execution)
    work_unit_fingerprint = _work_unit_fingerprint(execution)
    if action_type is None or work_unit_id is None or work_unit_fingerprint is None:
        return False
    return _matches_current_action(
        action_type=action_type,
        work_unit_id=work_unit_id,
        work_unit_fingerprint=work_unit_fingerprint,
        current_action_identity=current_action_identity,
    )


def _publication_surface_write_repair_execution_matches_current_action(
    execution: Mapping[str, Any],
    *,
    current_action_identity: Mapping[str, Any],
) -> bool:
    if _non_empty_text(execution.get("action_type")) != "run_quality_repair_batch":
        return False
    if not _provider_attempt_required(execution):
        return False
    if execution.get("owner_route_current") is False:
        return False
    route = _mapping(execution.get("owner_route"))
    source_refs = _mapping(route.get("source_refs"))
    source_action = _mapping(execution.get("source_action"))
    source_surface = (
        _non_empty_text(source_refs.get("source_surface"))
        or _non_empty_text(source_action.get("source_surface"))
    )
    current_stage_id = (
        _non_empty_text(source_refs.get("current_stage_id"))
        or _non_empty_text(source_action.get("current_stage_id"))
    )
    next_owner = _non_empty_text(execution.get("next_executable_owner")) or _non_empty_text(route.get("next_owner"))
    work_unit_id = handoff_work_unit_id(execution)
    work_unit_fingerprint = _work_unit_fingerprint(execution)
    if work_unit_id is None or work_unit_fingerprint is None:
        return False
    return (
        next_owner == "write"
        and current_stage_id == "08-publication_package_handoff"
        and source_surface == "artifacts/reports/medical_publication_surface/latest.json"
        and _matches_current_action(
            action_type="run_quality_repair_batch",
            work_unit_id=work_unit_id,
            work_unit_fingerprint=work_unit_fingerprint,
            current_action_identity=current_action_identity,
        )
    )


def _repair_progress_ai_reviewer_execution_matches_current_action(
    execution: Mapping[str, Any],
    *,
    current_action_identity: Mapping[str, Any],
) -> bool:
    if not current_action_identity:
        return False
    if _non_empty_text(current_action_identity.get("source")) != "repair_progress_projection.mas_owner_repair_execution_evidence":
        return False
    if _non_empty_text(current_action_identity.get("next_owner")) != "ai_reviewer":
        return False
    return _repair_progress_execution_matches_current_action(
        execution,
        current_action_identity=current_action_identity,
        action_type="return_to_ai_reviewer_workflow",
    )


def _repair_progress_gate_clearing_execution_matches_current_action(
    execution: Mapping[str, Any],
    *,
    current_action_identity: Mapping[str, Any],
) -> bool:
    if not current_action_identity:
        return False
    if _non_empty_text(current_action_identity.get("source")) != "repair_progress_projection.mas_owner_repair_execution_evidence":
        return False
    if _non_empty_text(current_action_identity.get("next_owner")) != "gate_clearing_batch":
        return False
    return _repair_progress_execution_matches_current_action(
        execution,
        current_action_identity=current_action_identity,
        action_type="run_gate_clearing_batch",
    )


def _publication_eval_repair_execution_matches_current_action(
    execution: Mapping[str, Any],
    *,
    current_action_identity: Mapping[str, Any],
) -> bool:
    if not current_action_identity:
        return False
    if _non_empty_text(current_action_identity.get("source")) != (
        "publication_eval.recommended_actions.readiness_blocker_repair"
    ):
        return False
    if _non_empty_text(current_action_identity.get("next_owner")) != "write":
        return False
    return _repair_progress_execution_matches_current_action(
        execution,
        current_action_identity=current_action_identity,
        action_type="run_quality_repair_batch",
    )


def _repair_progress_execution_matches_current_action(
    execution: Mapping[str, Any],
    *,
    current_action_identity: Mapping[str, Any],
    action_type: str,
) -> bool:
    if _non_empty_text(execution.get("action_type")) != action_type:
        return False
    if not _provider_attempt_required(execution):
        return False
    if execution.get("owner_route_current") is False:
        return False
    work_unit_id = handoff_work_unit_id(execution)
    work_unit_fingerprint = _work_unit_fingerprint(execution)
    if work_unit_id is None or work_unit_fingerprint is None:
        return False
    return _matches_current_action(
        action_type=action_type,
        work_unit_id=work_unit_id,
        work_unit_fingerprint=work_unit_fingerprint,
        current_action_identity=current_action_identity,
    )


def _canonical_provider_admission_work_unit_id(
    *,
    action_type: str | None,
    work_unit_id: str | None,
) -> str | None:
    if action_type == "run_gate_clearing_batch" and work_unit_id in PUBLICATION_GATE_REPLAY_WORK_UNIT_IDS:
        return "publication_gate_replay"
    return work_unit_id


def _execution_requests_provider_admission(execution: Mapping[str, Any]) -> bool:
    status = _non_empty_text(execution.get("execution_status"))
    if status == "handoff_ready":
        return True
    return status == "blocked" and _execution_blocked_reason(execution) == OPL_EXECUTION_AUTHORIZATION_BLOCKER


def _authorization_required_execution_matches_current_action(
    execution: Mapping[str, Any],
    *,
    current_action_identity: Mapping[str, Any],
) -> bool:
    if _execution_blocked_reason(execution) != OPL_EXECUTION_AUTHORIZATION_BLOCKER:
        return False
    if not current_action_identity:
        return False
    if not _provider_attempt_required(execution):
        return False
    if execution.get("owner_route_current") is False:
        return False
    action_type = _non_empty_text(execution.get("action_type"))
    work_unit_id = handoff_work_unit_id(execution)
    work_unit_fingerprint = _work_unit_fingerprint(execution)
    if action_type is None or work_unit_id is None or work_unit_fingerprint is None:
        return False
    if _current_identity_is_opl_authorization_typed_blocker(current_action_identity):
        return _matches_current_action_without_fingerprint(
            action_type=action_type,
            work_unit_id=work_unit_id,
            current_action_identity=current_action_identity,
        )
    return _matches_current_action(
        action_type=action_type,
        work_unit_id=work_unit_id,
        work_unit_fingerprint=work_unit_fingerprint,
        current_action_identity=current_action_identity,
    )


def _gate_replay_authorization_consumes_current_ai_reviewer_record(
    execution: Mapping[str, Any],
    *,
    current_action_identity: Mapping[str, Any],
) -> bool:
    if _execution_blocked_reason(execution) != OPL_EXECUTION_AUTHORIZATION_BLOCKER:
        return False
    if _non_empty_text(current_action_identity.get("source")) != "repair_progress_projection.mas_owner_repair_execution_evidence":
        return False
    if _non_empty_text(current_action_identity.get("next_owner")) != "ai_reviewer":
        return False
    current_action_ids = set(_text_items(current_action_identity.get("action_ids")))
    if current_action_ids and "return_to_ai_reviewer_workflow" not in current_action_ids:
        return False
    if _non_empty_text(execution.get("action_type")) != "run_gate_clearing_batch":
        return False
    if not _provider_attempt_required(execution):
        return False
    if execution.get("owner_route_current") is False:
        return False
    if not _dispatch_authority_allows_current_control_provider_admission(
        action_type="run_gate_clearing_batch",
        dispatch_authority=_non_empty_text(execution.get("dispatch_authority")),
    ):
        return False
    work_unit_id = handoff_work_unit_id(execution)
    if work_unit_id not in PUBLICATION_GATE_REPLAY_WORK_UNIT_IDS:
        return False
    return _gate_replay_execution_has_ai_reviewer_record_basis(execution, work_unit_id=work_unit_id)


def _gate_replay_execution_has_ai_reviewer_record_basis(
    execution: Mapping[str, Any],
    *,
    work_unit_id: str,
) -> bool:
    route = _mapping(execution.get("owner_route"))
    source_refs = _mapping(route.get("source_refs"))
    basis = _mapping(source_refs.get("owner_route_currentness_basis"))
    source_eval_id = _non_empty_text(source_refs.get("source_eval_id")) or _non_empty_text(
        basis.get("source_eval_id")
    )
    if source_eval_id is None:
        return work_unit_id in {
            "ai_reviewer_record_gate_consumption",
            "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
        } and _gate_replay_execution_has_repair_progress_record_basis(source_refs=source_refs, basis=basis)
    normalized = source_eval_id.replace("_", "-")
    return "ai-reviewer-record" in normalized or _gate_replay_execution_has_repair_progress_record_basis(
        source_refs=source_refs,
        basis=basis,
    )


def _gate_replay_execution_has_repair_progress_record_basis(
    *,
    source_refs: Mapping[str, Any],
    basis: Mapping[str, Any],
) -> bool:
    source_surface = _non_empty_text(source_refs.get("source_surface")) or _non_empty_text(basis.get("source_surface"))
    source_ref = _non_empty_text(source_refs.get("source_ref")) or _non_empty_text(basis.get("source_ref"))
    owner_reason = _non_empty_text(basis.get("owner_reason"))
    return (
        source_surface in {"repair_progress_projection", "repair_progress_followup.current_executable_owner_action"}
        or (source_ref is not None and "repair_execution_evidence" in source_ref)
        or owner_reason == "ai_reviewer_publication_eval_delta_or_typed_blocker"
    )


def _provider_attempt_required(execution: Mapping[str, Any]) -> bool:
    if execution.get("provider_attempt_or_lease_required") is True:
        return True
    return _non_empty_text(execution.get("owner_callable_surface")) == "opl_default_executor.stage_attempt"


def _execution_blocked_reason(execution: Mapping[str, Any]) -> str | None:
    typed_blocker = _mapping(execution.get("typed_blocker"))
    return (
        _non_empty_text(execution.get("blocked_reason"))
        or _non_empty_text(typed_blocker.get("blocker_id"))
        or _non_empty_text(typed_blocker.get("blocker_type"))
        or _non_empty_text(typed_blocker.get("reason"))
    )


def _work_unit_fingerprint(execution: Mapping[str, Any]) -> str | None:
    owner_route = _mapping(execution.get("owner_route"))
    source_refs = _mapping(owner_route.get("source_refs"))
    basis = _mapping(source_refs.get("owner_route_currentness_basis")) or _mapping(
        _mapping(execution.get("prompt_contract")).get("owner_route_currentness_basis")
    )
    return _first_currentness_fingerprint(
        execution.get("action_fingerprint"),
        owner_route.get("work_unit_fingerprint"),
        source_refs.get("work_unit_fingerprint"),
        basis.get("work_unit_fingerprint"),
        study_id=_non_empty_text(execution.get("study_id")),
        action_type=_non_empty_text(execution.get("action_type")),
        work_unit_id=handoff_work_unit_id(execution),
    )


def _work_unit_fingerprints(
    execution: Mapping[str, Any],
    *,
    canonical_fingerprint: str,
) -> list[str]:
    owner_route = _mapping(execution.get("owner_route"))
    source_refs = _mapping(owner_route.get("source_refs"))
    basis = _mapping(source_refs.get("owner_route_currentness_basis")) or _mapping(
        _mapping(execution.get("prompt_contract")).get("owner_route_currentness_basis")
    )
    fingerprints = [
        item
        for item in (
            canonical_fingerprint,
            _non_empty_text(execution.get("action_fingerprint")),
            _non_empty_text(execution.get("work_unit_fingerprint")),
            _non_empty_text(owner_route.get("work_unit_fingerprint")),
            _non_empty_text(source_refs.get("work_unit_fingerprint")),
            _non_empty_text(basis.get("work_unit_fingerprint")),
            _non_empty_text(basis.get("source_fingerprint")),
        )
        if item is not None
        and (
            not control_identity.is_synthetic_current_owner_ticket(item)
            or item == canonical_fingerprint
        )
    ]
    return list(dict.fromkeys(fingerprints))


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
        "work_unit_id": _non_empty_text(basis.get("work_unit_id")) or work_unit_id,
        "work_unit_fingerprint": _non_empty_text(basis.get("work_unit_fingerprint")) or work_unit_fingerprint,
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
