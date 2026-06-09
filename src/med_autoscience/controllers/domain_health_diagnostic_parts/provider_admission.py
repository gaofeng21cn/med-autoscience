from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from med_autoscience.controllers.gate_clearing_batch_work_units import PUBLICATION_GATE_REPLAY_WORK_UNIT_IDS
from med_autoscience.controllers.opl_execution_boundary import OPL_EXECUTION_AUTHORIZATION_BLOCKER


DEFAULT_EXECUTOR_EXECUTION_LATEST = Path(
    "artifacts/supervision/consumer/default_executor_execution/latest.json"
)
DEFAULT_EXECUTOR_DISPATCHES = Path("artifacts/supervision/consumer/default_executor_dispatches")
CURRENT_CONTROL_PROVIDER_ADMISSION_ACTION_OWNERS = {
    "return_to_ai_reviewer_workflow": {"ai_reviewer"},
    "run_quality_repair_batch": {"write"},
    "run_gate_clearing_batch": {"gate_clearing_batch", "write"},
}
CURRENT_CONTROL_PROVIDER_ADMISSION_DISPATCH_AUTHORITIES = {
    "return_to_ai_reviewer_workflow": {"ai_reviewer_record_production_handoff"},
    "run_quality_repair_batch": {None, "quality_repair_batch_writer_handoff", "consumer_default_executor_dispatch"},
    "run_gate_clearing_batch": {None, "consumer_default_executor_dispatch"},
}
PROVIDER_ADMISSION_AUTHORITY_BOUNDARY = {
    "surface_kind": "opl_provider_admission_candidate",
    "authority": "mas_provider_admission_identity",
    "stage_transition_authority": "OPL Stage Transition Authority",
    "stage_authority_role": "non_authoritative_observation_and_intent_producer",
    "can_write_stage_current_pointer": False,
    "can_write_current_owner_delta": False,
    "can_write_stage_terminal_state": False,
    "can_write_runtime_owned_surfaces": False,
    "can_mark_provider_attempt_running": False,
    "provider_completion_is_domain_completion": False,
}
STAGE_TRANSITION_AUTHORITY_BOUNDARY = {
    "producer_kind": "runtime_provider",
    "intent_kind": "provider_observation",
    "stage_transition_authority": "one-person-lab",
    "intent_can_write_stage_current_pointer": False,
    "intent_can_write_stage_run_terminal_state": False,
    "intent_can_publish_current_owner_delta": False,
    "intent_can_write_domain_truth": False,
    "intent_can_create_owner_receipt": False,
    "intent_can_create_typed_blocker": False,
    "provider_completion_counts_as_stage_transition": False,
    "read_model_update_counts_as_stage_transition": False,
    "worklist_update_counts_as_stage_transition": False,
    "evidence_event_counts_as_stage_transition": False,
    "agent_lab_output_counts_as_stage_transition": False,
}


def materialized_record_only_provider_handoff(materialize_result: Mapping[str, Any]) -> bool:
    return bool(materialized_record_only_provider_handoffs(materialize_result))


def materialized_record_only_provider_handoffs(materialize_result: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    handoffs: list[Mapping[str, Any]] = []
    for item in materialize_result.get("default_executor_dispatches") or []:
        if not isinstance(item, Mapping):
            continue
        if _non_empty_text(item.get("dispatch_status")) != "ready":
            continue
        if _non_empty_text(item.get("dispatch_authority")) != "ai_reviewer_record_production_handoff":
            continue
        handoffs.append(item)
    return handoffs


def provider_admission_pending_dispatch_result(
    *,
    materialize_result: Mapping[str, Any],
) -> dict[str, Any]:
    executions: list[dict[str, Any]] = []
    for handoff in materialized_record_only_provider_handoffs(materialize_result):
        executions.append(
            {
                "surface": "default_executor_dispatch_execution",
                "study_id": _non_empty_text(handoff.get("study_id")),
                "quest_id": _non_empty_text(handoff.get("quest_id")),
                "action_type": _non_empty_text(handoff.get("action_type")),
                "work_unit_id": handoff_work_unit_id(handoff),
                "dispatch_path": handoff_dispatch_path(handoff),
                "dispatch_authority": _non_empty_text(handoff.get("dispatch_authority")),
                "execution_status": "provider_admission_pending",
                "blocked_reason": None,
                "next_executable_owner": _non_empty_text(handoff.get("next_executable_owner")),
                "required_output_surface": _non_empty_text(handoff.get("required_output_surface")),
                "will_start_llm": False,
                "provider_attempt_or_lease_required": True,
                "provider_completion_is_domain_completion": False,
            }
        )
    return {
        "surface": "domain_owner_action_dispatch",
        "schema_version": 1,
        "execution_count": 0,
        "executed_count": 0,
        "blocked_count": 0,
        "repeat_suppressed_count": 0,
        "dry_run_count": 0,
        "codex_dispatch_count": 0,
        "suppressed_dispatch_count": len(executions),
        "provider_admission_pending_count": len(executions),
        "executions": executions,
        "written_files": [],
    }


def handoff_dispatch_path(handoff: Mapping[str, Any]) -> str | None:
    refs = _mapping(handoff.get("refs"))
    return (
        _non_empty_text(handoff.get("dispatch_path"))
        or _non_empty_text(handoff.get("stage_packet_ref"))
        or _non_empty_text(refs.get("stage_packet_path"))
        or _non_empty_text(refs.get("immutable_dispatch_path"))
        or _non_empty_text(refs.get("dispatch_path"))
    )


def handoff_work_unit_id(handoff: Mapping[str, Any]) -> str | None:
    owner_route = _mapping(handoff.get("owner_route")) or _mapping(
        _mapping(handoff.get("prompt_contract")).get("owner_route")
    )
    source_refs = _mapping(owner_route.get("source_refs"))
    basis = _mapping(source_refs.get("owner_route_currentness_basis"))
    return (
        _non_empty_text(source_refs.get("work_unit_id"))
        or _non_empty_text(owner_route.get("work_unit_id"))
        or _non_empty_text(basis.get("work_unit_id"))
        or _non_empty_text(owner_route.get("work_unit_fingerprint"))
        or _non_empty_text(basis.get("work_unit_fingerprint"))
    )


def provider_probe_has_matching_attempt(
    scan_result: Mapping[str, Any],
    *,
    identity: Mapping[str, str],
) -> bool:
    expected_study_id = _non_empty_text(identity.get("study_id"))
    for study in scan_result.get("studies") or []:
        if not isinstance(study, Mapping):
            continue
        if expected_study_id is not None and _non_empty_text(study.get("study_id")) != expected_study_id:
            continue
        if not study_has_running_provider_attempt(study):
            continue
        live_attempt = _mapping(study.get("opl_provider_attempt")) or study
        if provider_attempt_matches_identity(live_attempt, identity=identity):
            return True
    return False


def study_has_running_provider_attempt(study: Mapping[str, Any]) -> bool:
    return study.get("running_provider_attempt") is True and (
        _non_empty_text(study.get("active_stage_attempt_id"))
        or _non_empty_text(study.get("active_run_id"))
        or _non_empty_text(study.get("active_workflow_id"))
    ) is not None


def provider_attempt_matches_identity(
    live_attempt: Mapping[str, Any],
    *,
    identity: Mapping[str, str],
) -> bool:
    expected_action = _non_empty_text(identity.get("action_type"))
    if expected_action is not None and _non_empty_text(live_attempt.get("action_type")) != expected_action:
        return False
    expected_work_unit = _non_empty_text(identity.get("work_unit_id"))
    if expected_work_unit is not None and _non_empty_text(live_attempt.get("work_unit_id")) != expected_work_unit:
        return False
    expected_fingerprints = {
        text
        for value in (identity.get("action_fingerprint"), identity.get("work_unit_fingerprint"))
        if (text := _non_empty_text(value)) is not None
    }
    if expected_fingerprints:
        live_fingerprints = _provider_attempt_fingerprints(live_attempt)
        if not live_fingerprints or live_fingerprints.isdisjoint(expected_fingerprints):
            return False
    expected_dispatch = _non_empty_text(identity.get("dispatch_path"))
    live_dispatch = _non_empty_text(live_attempt.get("dispatch_ref")) or _non_empty_text(live_attempt.get("dispatch_path"))
    if expected_dispatch is None or live_dispatch is None:
        return True
    normalized_expected = expected_dispatch.replace("\\", "/")
    normalized_live = live_dispatch.replace("\\", "/")
    return normalized_expected == normalized_live or normalized_expected.endswith(f"/{normalized_live}")


def _provider_attempt_fingerprints(live_attempt: Mapping[str, Any]) -> set[str]:
    owner_route = _mapping(live_attempt.get("owner_route"))
    source_refs = _mapping(owner_route.get("source_refs"))
    basis = _mapping(source_refs.get("owner_route_currentness_basis"))
    return {
        text
        for value in (
            live_attempt.get("action_fingerprint"),
            live_attempt.get("work_unit_fingerprint"),
            owner_route.get("work_unit_fingerprint"),
            source_refs.get("work_unit_fingerprint"),
            basis.get("work_unit_fingerprint"),
        )
        if (text := _non_empty_text(value)) is not None
    }


def provider_probe_has_non_running_actions(scan_result: Mapping[str, Any]) -> bool:
    running_study_ids = {
        study_id
        for study in scan_result.get("studies") or []
        if isinstance(study, Mapping)
        and study.get("running_provider_attempt") is True
        and (study_id := _non_empty_text(study.get("study_id"))) is not None
    }
    for action in scan_result.get("action_queue") or []:
        if not isinstance(action, Mapping):
            continue
        study_id = _non_empty_text(action.get("study_id"))
        if study_id is None or study_id not in running_study_ids:
            return True
    return False


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
            if action_identity and action_identity != current_action_identity:
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
    action_fingerprint = (
        _non_empty_text(action.get("action_fingerprint"))
        or _non_empty_text(action.get("work_unit_fingerprint"))
        or _non_empty_text(action.get("source_fingerprint"))
        or _non_empty_text(source_refs.get("work_unit_fingerprint"))
        or _non_empty_text(currentness_basis.get("work_unit_fingerprint"))
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
        "next_executable_owner": (
            _non_empty_text(action.get("next_executable_owner"))
            or _non_empty_text(action.get("owner"))
            or _non_empty_text(owner_route.get("next_owner"))
            or _non_empty_text(dispatch_payload.get("next_executable_owner"))
        ),
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
    if not _current_control_owner_allowed(action_type=action_type, owner=owner):
        return None
    work_unit_id = _non_empty_text(current.get("work_unit_id")) or _non_empty_text(current.get("next_work_unit"))
    if work_unit_id is None:
        return None
    study_id = _non_empty_text(study.get("study_id"))
    action_fingerprint = (
        _non_empty_text(current.get("action_fingerprint"))
        or _non_empty_text(current.get("work_unit_fingerprint"))
        or _non_empty_text(_mapping(study.get("current_work_unit")).get("action_fingerprint"))
        or _non_empty_text(_mapping(study.get("current_work_unit")).get("work_unit_fingerprint"))
        or _stable_provider_admission_ticket(
            study_id=study_id,
            action_type=action_type,
            work_unit_id=work_unit_id,
        )
    )
    source_refs = {
        key: value
        for key, value in {
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": action_fingerprint,
            "owner_route_currentness_basis": _study_currentness_basis(
                study=study,
                current=current,
                work_unit_id=work_unit_id,
                work_unit_fingerprint=action_fingerprint,
            ),
        }.items()
        if value is not None
    }
    return {
        "study_id": study_id,
        "quest_id": _non_empty_text(study.get("quest_id")),
        "action_type": action_type,
        "status": "queued",
        "owner": owner,
        "next_executable_owner": owner,
        "next_work_unit": work_unit_id,
        "work_unit_id": work_unit_id,
        "action_fingerprint": action_fingerprint,
        "work_unit_fingerprint": action_fingerprint,
        "required_output_surface": _required_output_surface(current),
        "provider_attempt_or_lease_required": True,
        "provider_completion_is_domain_completion": False,
        "source_surface": "opl_current_control_state.study_current_executable_owner_action",
        "owner_route": {
            "next_owner": owner,
            "allowed_actions": [action_type],
            "work_unit_fingerprint": action_fingerprint,
            "source_refs": source_refs,
        },
    }


def _provider_admission_action_key(action: Mapping[str, Any]) -> tuple[str | None, str | None, str | None]:
    return (
        _non_empty_text(action.get("study_id")),
        _current_action_action_type(action),
        _non_empty_text(action.get("work_unit_id")) or _non_empty_text(action.get("next_work_unit")),
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
    if study_id is None or action_type is None or work_unit_id is None:
        return None
    return f"study-progress-current-owner-ticket::{study_id}::{work_unit_id}::{action_type}"


def _study_currentness_basis(
    *,
    study: Mapping[str, Any],
    current: Mapping[str, Any],
    work_unit_id: str,
    work_unit_fingerprint: str | None,
) -> dict[str, Any]:
    current_work_unit = _mapping(study.get("current_work_unit"))
    basis = _mapping(current_work_unit.get("currentness_basis"))
    return {
        key: value
        for key, value in {
            **basis,
            "work_unit_id": _non_empty_text(basis.get("work_unit_id")) or work_unit_id,
            "work_unit_fingerprint": _non_empty_text(basis.get("work_unit_fingerprint")) or work_unit_fingerprint,
            "source": _non_empty_text(current.get("source")),
        }.items()
        if value is not None
    }


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
    if not _matches_current_action(
        action_type=action_type,
        work_unit_id=work_unit_id,
        work_unit_fingerprint=work_unit_fingerprint,
        current_action_identity=_mapping(current_action_identity),
    ) and not _gate_replay_authorization_consumes_current_ai_reviewer_record(
        execution,
        current_action_identity=_mapping(current_action_identity),
    ):
        return None
    owner_route = _mapping(execution.get("owner_route"))
    source_refs = _mapping(owner_route.get("source_refs"))
    currentness_basis = _mapping(source_refs.get("owner_route_currentness_basis")) or _mapping(
        _mapping(_mapping(execution.get("prompt_contract")).get("owner_route_currentness_basis"))
    )
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
    fingerprint = _non_empty_text(current.get("work_unit_fingerprint"))
    fingerprints: list[str] = []
    if fingerprint is not None:
        fingerprints.append(fingerprint)
    repair_precedence = _mapping(current.get("repair_progress_precedence"))
    repair_fingerprint = _non_empty_text(repair_precedence.get("source_fingerprint"))
    if repair_fingerprint is not None:
        fingerprints.append(repair_fingerprint)
    ticket = _mapping(status_payload.get("current_owner_ticket"))
    for item in ticket.get("required_input_refs") or []:
        text = _non_empty_text(item)
        if text is not None and (text.startswith("sha256:") or text.startswith("study-progress-current-owner-ticket::")):
            fingerprints.append(text)
    if fingerprint is None and work_unit_id is not None and source_ref is not None:
        fingerprints.append(
            "stage-current-owner-delta::"
            f"{work_unit_id}::{surface_key or 'unspecified_surface'}::{source_ref}"
        )
    if study_id is not None and work_unit_id is not None:
        for action_id in action_ids or [work_unit_id]:
            fingerprints.append(
                f"study-progress-current-owner-ticket::{study_id}::{work_unit_id}::{action_id}"
            )
    fingerprints = list(dict.fromkeys(fingerprints))
    if fingerprint is None and fingerprints:
        fingerprint = fingerprints[0]
    return {
        "action_ids": action_ids,
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": fingerprint,
        "work_unit_fingerprints": fingerprints,
        "source_ref": source_ref,
        "source": _non_empty_text(current.get("source")),
        "next_owner": _non_empty_text(current.get("next_owner")),
    }


def _current_control_action_identity(action: Mapping[str, Any]) -> dict[str, Any]:
    if _non_empty_text(action.get("source_surface")) not in {None, "opl_current_control_state.action_queue"}:
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


def _owner_route_currentness_basis_complete(currentness_basis: Mapping[str, Any]) -> bool:
    if _non_empty_text(currentness_basis.get("work_unit_id")) is None:
        return False
    if _non_empty_text(currentness_basis.get("work_unit_fingerprint")) is None:
        return False
    if _non_empty_text(currentness_basis.get("truth_epoch")) is None:
        return False
    return (
        _non_empty_text(currentness_basis.get("runtime_health_epoch")) is not None
        or _non_empty_text(currentness_basis.get("source_eval_id")) is not None
    )


def _status_requires_current_identity(status_payload: Mapping[str, Any]) -> bool:
    if _mapping(status_payload.get("current_work_unit")):
        return True
    if _mapping(status_payload.get("current_executable_owner_action")):
        return True
    envelope = _mapping(status_payload.get("current_execution_envelope"))
    state_kind = _non_empty_text(envelope.get("state_kind")) or _non_empty_text(envelope.get("execution_state_kind"))
    if state_kind in {"executable_owner_action", "running_provider_attempt"}:
        return True
    if _mapping(status_payload.get("opl_current_control_state_handoff")):
        return True
    if _mapping(status_payload.get("opl_current_control_state")):
        return True
    return False


def _current_work_unit_identity(current_work_unit: Mapping[str, Any]) -> dict[str, Any]:
    if _non_empty_text(current_work_unit.get("status")) != "executable_owner_action":
        return {}
    state = _mapping(current_work_unit.get("state"))
    currentness_basis = _mapping(current_work_unit.get("currentness_basis"))
    action_type = _non_empty_text(current_work_unit.get("action_type"))
    work_unit_id = _non_empty_text(current_work_unit.get("work_unit_id"))
    fingerprint = (
        _non_empty_text(current_work_unit.get("work_unit_fingerprint"))
        or _non_empty_text(current_work_unit.get("action_fingerprint"))
        or _non_empty_text(currentness_basis.get("work_unit_fingerprint"))
        or _non_empty_text(currentness_basis.get("source_fingerprint"))
        or _stable_provider_admission_ticket(
            study_id=_non_empty_text(current_work_unit.get("study_id")),
            action_type=action_type,
            work_unit_id=work_unit_id,
        )
    )
    fingerprints = [
        item
        for item in (
            _non_empty_text(current_work_unit.get("work_unit_fingerprint")),
            _non_empty_text(current_work_unit.get("action_fingerprint")),
            _non_empty_text(currentness_basis.get("work_unit_fingerprint")),
            _non_empty_text(currentness_basis.get("source_fingerprint")),
        )
        if item is not None
    ]
    return {
        "action_ids": [item for item in (action_type, work_unit_id) if item is not None],
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": fingerprint,
        "work_unit_fingerprints": list(dict.fromkeys(fingerprints)),
        "source_ref": _first_text(current_work_unit.get("input_refs")) or _non_empty_text(state.get("source_ref")),
        "source": _non_empty_text(state.get("source")) or "canonical_current_work_unit",
        "next_owner": _non_empty_text(current_work_unit.get("owner")),
    }


def _status_envelope_blocks_provider_admission(
    status_payload: Mapping[str, Any],
    *,
    execution: Mapping[str, Any],
    current_action_identity: Mapping[str, Any] | None = None,
) -> bool:
    envelope = _mapping(status_payload.get("current_execution_envelope"))
    state_kind = _non_empty_text(envelope.get("state_kind")) or _non_empty_text(envelope.get("execution_state_kind"))
    if state_kind in {"parked", "running_provider_attempt"}:
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
    if _gate_replay_authorization_consumes_current_ai_reviewer_record(
        execution,
        current_action_identity=current_action_identity,
    ):
        return True
    blocker = _mapping(envelope.get("typed_blocker"))
    blocker_reason = (
        _non_empty_text(blocker.get("blocker_id"))
        or _non_empty_text(blocker.get("blocker_type"))
        or _non_empty_text(blocker.get("reason"))
    )
    if blocker_reason in {"medical_paper_readiness_missing", "medical_paper_readiness_not_ready"} and (
        _current_control_provider_admission_execution_has_current_identity(execution)
    ):
        return True
    if blocker_reason != "medical_paper_readiness_missing":
        return False
    if _non_empty_text(execution.get("action_type")) != "run_quality_repair_batch":
        return False
    if not _provider_attempt_required(execution):
        return False
    if execution.get("owner_route_current") is False:
        return False
    route = _mapping(execution.get("owner_route"))
    source_refs = _mapping(route.get("source_refs"))
    source_surface = (
        _non_empty_text(source_refs.get("source_surface"))
        or _non_empty_text(_mapping(execution.get("source_action")).get("source_surface"))
    )
    current_stage_id = (
        _non_empty_text(source_refs.get("current_stage_id"))
        or _non_empty_text(_mapping(execution.get("source_action")).get("current_stage_id"))
    )
    next_owner = (
        _non_empty_text(execution.get("next_executable_owner"))
        or _non_empty_text(route.get("next_owner"))
    )
    return (
        next_owner == "write"
        and current_stage_id == "08-publication_package_handoff"
        and source_surface == "artifacts/reports/medical_publication_surface/latest.json"
    )


def _current_control_provider_admission_execution_has_current_identity(execution: Mapping[str, Any]) -> bool:
    if _non_empty_text(execution.get("source")) not in {
        "opl_current_control_state.action_queue",
        "opl_current_control_state.study_current_executable_owner_action",
    }:
        return False
    action_type = _non_empty_text(execution.get("action_type"))
    if action_type not in CURRENT_CONTROL_PROVIDER_ADMISSION_ACTION_OWNERS:
        return False
    if not _execution_requests_provider_admission(execution):
        return False
    if not _provider_attempt_required(execution):
        return False
    if execution.get("owner_route_current") is False:
        return False
    if not _dispatch_authority_allows_current_control_provider_admission(
        action_type=action_type,
        dispatch_authority=_non_empty_text(execution.get("dispatch_authority")),
    ):
        return False
    expected_owners = CURRENT_CONTROL_PROVIDER_ADMISSION_ACTION_OWNERS[action_type]
    route = _mapping(execution.get("owner_route"))
    next_owner = _non_empty_text(execution.get("next_executable_owner")) or _non_empty_text(route.get("next_owner"))
    if next_owner not in expected_owners:
        return False
    return (
        handoff_work_unit_id(execution) is not None
        and _work_unit_fingerprint(execution) is not None
        and handoff_dispatch_path(execution) is not None
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


def _matches_current_action(
    *,
    action_type: str,
    work_unit_id: str,
    work_unit_fingerprint: str,
    current_action_identity: Mapping[str, Any],
) -> bool:
    if not current_action_identity:
        return False
    expected_work_unit_id = _non_empty_text(current_action_identity.get("work_unit_id"))
    action_ids = set(_text_items(current_action_identity.get("action_ids")))
    expected_fingerprints = set(_text_items(current_action_identity.get("work_unit_fingerprints")))
    if expected_fingerprints:
        if work_unit_fingerprint not in expected_fingerprints:
            return False
        if not _provider_admission_ticket_matches_action(
            work_unit_fingerprint=work_unit_fingerprint,
            action_type=action_type,
            work_unit_id=work_unit_id,
        ):
            return False
        if action_ids and action_type not in action_ids:
            return False
        return True
    expected_fingerprint = _non_empty_text(current_action_identity.get("work_unit_fingerprint"))
    if expected_fingerprint is not None:
        if work_unit_fingerprint != expected_fingerprint:
            return False
        if not _provider_admission_ticket_matches_action(
            work_unit_fingerprint=work_unit_fingerprint,
            action_type=action_type,
            work_unit_id=work_unit_id,
        ):
            return False
        if action_ids and action_type not in action_ids:
            return False
        return True
    if expected_work_unit_id is not None and work_unit_id != expected_work_unit_id:
        return False
    if action_ids and action_type not in action_ids:
        return False
    expected_source_ref = _non_empty_text(current_action_identity.get("source_ref"))
    if expected_source_ref is not None:
        return expected_source_ref in work_unit_fingerprint
    return True


def _provider_admission_ticket_matches_action(
    *,
    work_unit_fingerprint: str,
    action_type: str,
    work_unit_id: str,
) -> bool:
    prefix = "study-progress-current-owner-ticket::"
    if not work_unit_fingerprint.startswith(prefix):
        return True
    parts = work_unit_fingerprint.split("::")
    if len(parts) < 4:
        return False
    ticket_work_unit_id = _non_empty_text(parts[2])
    ticket_action_type = _non_empty_text(parts[3])
    return (
        ticket_work_unit_id == work_unit_id
        and (ticket_action_type == action_type or ticket_action_type == work_unit_id)
    )


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
    return (
        _non_empty_text(execution.get("action_fingerprint"))
        or _non_empty_text(owner_route.get("work_unit_fingerprint"))
        or _non_empty_text(source_refs.get("work_unit_fingerprint"))
        or _non_empty_text(basis.get("work_unit_fingerprint"))
    )


def _current_control_action_requests_provider_admission(action: Mapping[str, Any]) -> bool:
    action_type = _non_empty_text(action.get("action_type"))
    if action_type is None:
        return False
    if _non_empty_text(action.get("status")) not in {"queued", "pending", "ready"}:
        return False
    owner = _non_empty_text(action.get("next_executable_owner")) or _non_empty_text(action.get("owner"))
    return _current_control_owner_allowed(action_type=action_type, owner=owner)


def _current_control_owner_allowed(*, action_type: str, owner: str | None) -> bool:
    expected_owners = CURRENT_CONTROL_PROVIDER_ADMISSION_ACTION_OWNERS.get(action_type)
    return owner in expected_owners if expected_owners is not None else False


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


def _read_json_object(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object at {path}")
    return payload


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text_items(value: object) -> list[str]:
    if isinstance(value, str):
        text = _non_empty_text(value)
        return [text] if text is not None else []
    if not isinstance(value, list | tuple | set):
        return []
    result: list[str] = []
    for item in value:
        text = _non_empty_text(item)
        if text is not None and text not in result:
            result.append(text)
    return result


def _first_text(value: object) -> str | None:
    for item in _text_items(value):
        return item
    return None


def _non_empty_text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None
