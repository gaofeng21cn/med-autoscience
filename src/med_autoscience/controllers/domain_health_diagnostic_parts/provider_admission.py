from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from med_autoscience.controllers import control_identity
from med_autoscience.controllers import paper_progress_policy_adapter
from med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_boundaries import (
    provider_admission_authority_boundary,
    provider_admission_candidate_with_authority_boundaries,
    stage_transition_authority_boundary,
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
from med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_current_control_actions import (
    _current_action_identity,
    _current_action_action_type,
    _current_control_action_dispatch_path,
    _current_control_action_requests_provider_admission,
    _current_control_executable_owner,
    _dispatch_authority_allows_current_control_provider_admission,
    _first_currentness_fingerprint,
    _merge_owner_route_currentness,
    _provider_admission_action_key,
    _status_with_current_control_study_currentness,
    _study_current_action_for_provider_admission,
    _study_current_actions_for_provider_admission,
)
from med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_helpers import (
    mapping as _mapping,
    non_empty_text as _non_empty_text,
    read_json_object as _read_json_object,
    text_items as _text_items,
)
from med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_identity import (
    current_identity_is_opl_authorization_typed_blocker as _current_identity_is_opl_authorization_typed_blocker,
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
from med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_stage_run_identity import (
    candidate_with_stage_run_admission_identity as _candidate_with_stage_run_admission_identity,
)
from med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_status_currentness import (
    current_control_payload_with_status_currentness,
)
from med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_status import (
    execution_state_kind as _execution_state_kind,
    status_blocks_action_queue_self_identity as _status_blocks_action_queue_self_identity,
)
from med_autoscience.controllers.domain_health_diagnostic_parts.current_ai_reviewer_gate_replay import (
    source_eval_id_from_mapping,
)


DEFAULT_EXECUTOR_EXECUTION_LATEST = Path(
    "artifacts/supervision/consumer/default_executor_execution/latest.json"
)
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
ACCEPTED_OWNER_GATE_DECISION_SOURCE = "paper_recovery_state.accepted_owner_gate_decision"


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
        if candidate is not None:
            candidates.append(candidate_with_authority_boundaries(candidate))
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
    canonical_current_fingerprint = _current_identity_fingerprint_for_action(
        action_type=action_type,
        work_unit_id=work_unit_id,
        current_action_identity=current_identity,
    )
    if canonical_current_fingerprint is not None:
        action_fingerprint = canonical_current_fingerprint
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
    return candidate_with_authority_boundaries(
        _candidate_with_stage_run_admission_identity(
            candidate,
            execution=execution,
            dispatch_payload=_mapping(dispatch_payload),
            dispatch_path=dispatch_path,
            study_root=study_root,
            allow_dispatch_ref_stage_packet_authority=True,
        )
    )


def _current_identity_fingerprint_for_action(
    *,
    action_type: str,
    work_unit_id: str,
    current_action_identity: Mapping[str, Any],
) -> str | None:
    if not _matches_current_action_without_fingerprint(
        action_type=action_type,
        work_unit_id=work_unit_id,
        current_action_identity=current_action_identity,
    ):
        return None
    return _non_empty_text(current_action_identity.get("work_unit_fingerprint"))


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
            **dict(currentness_basis),
            **dict(current_identity_basis),
            "work_unit_id": _non_empty_text(currentness_basis.get("work_unit_id")) or work_unit_id,
            "work_unit_fingerprint": _non_empty_text(current_identity_basis.get("work_unit_fingerprint"))
            or _non_empty_text(currentness_basis.get("work_unit_fingerprint"))
            or work_unit_fingerprint,
        }
    candidate = {
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
        "authority_boundary": provider_admission_authority_boundary(),
        "stage_transition_authority_boundary": stage_transition_authority_boundary(),
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
    return candidate_with_authority_boundaries(
        _candidate_with_stage_run_admission_identity(
            _candidate_with_paper_progress_policy_result(candidate, execution=execution),
            execution=execution,
            allow_dispatch_ref_stage_packet_authority=True,
        )
    )


def _candidate_with_paper_progress_policy_result(
    candidate: Mapping[str, Any],
    *,
    execution: Mapping[str, Any],
) -> dict[str, Any]:
    existing_policy = _mapping(execution.get("paper_progress_policy_result")) or _mapping(
        candidate.get("paper_progress_policy_result")
    )
    existing_outbox_record = _mapping(
        existing_policy.get("opl_domain_progress_command_outbox_record")
    )
    policy_result = (
        existing_policy
        if existing_policy and existing_outbox_record
        else paper_progress_policy_adapter.build_policy_result(
            _paper_progress_policy_payload(candidate, execution=execution),
            source="dhd.provider_admission_candidate",
        )
    )
    if not policy_result:
        return dict(candidate)
    return {
        **dict(candidate),
        "paper_progress_policy_result": dict(policy_result),
        "current_control_command_outbox_record": _mapping(
            policy_result.get("opl_domain_progress_command_outbox_record")
        ),
    }


def _paper_progress_policy_payload(
    candidate: Mapping[str, Any],
    *,
    execution: Mapping[str, Any],
) -> dict[str, Any]:
    currentness_basis = _mapping(candidate.get("currentness_basis"))
    current_action = {
        "surface_kind": "current_executable_owner_action",
        "status": "ready",
        "source": _non_empty_text(candidate.get("source")) or _non_empty_text(execution.get("source")),
        "next_owner": _non_empty_text(candidate.get("next_executable_owner"))
        or _non_empty_text(execution.get("next_executable_owner")),
        "owner": _non_empty_text(candidate.get("next_executable_owner"))
        or _non_empty_text(execution.get("next_executable_owner")),
        "action_type": _non_empty_text(candidate.get("action_type")),
        "work_unit_id": _non_empty_text(candidate.get("work_unit_id")),
        "work_unit_fingerprint": _non_empty_text(candidate.get("work_unit_fingerprint")),
        "action_fingerprint": _non_empty_text(candidate.get("action_fingerprint"))
        or _non_empty_text(candidate.get("work_unit_fingerprint")),
        "currentness_basis": dict(currentness_basis) if currentness_basis else None,
    }
    current_work_unit = {
        "surface_kind": "current_work_unit",
        "status": "executable_owner_action",
        "owner": current_action["next_owner"],
        "action_type": current_action["action_type"],
        "work_unit_id": current_action["work_unit_id"],
        "work_unit_fingerprint": current_action["work_unit_fingerprint"],
        "action_fingerprint": current_action["action_fingerprint"],
        "currentness_basis": dict(currentness_basis) if currentness_basis else None,
    }
    return {
        "study_id": _non_empty_text(candidate.get("study_id")),
        "quest_id": _non_empty_text(candidate.get("quest_id")),
        "current_work_unit": current_work_unit,
        "current_executable_owner_action": current_action,
    }


def candidate_with_authority_boundaries(candidate: Mapping[str, Any]) -> dict[str, Any]:
    return provider_admission_candidate_with_authority_boundaries(candidate)


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
    if (
        blocker_reason == "stage_packet_not_current_selected_dispatch"
        and _owner_gate_route_back_execution_matches_current_action(
            execution,
            current_action_identity=current_action_identity,
        )
    ):
        return True
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


def _owner_gate_route_back_execution_matches_current_action(
    execution: Mapping[str, Any],
    *,
    current_action_identity: Mapping[str, Any],
) -> bool:
    if _non_empty_text(current_action_identity.get("source")) != ACCEPTED_OWNER_GATE_DECISION_SOURCE:
        return False
    return _explicit_current_action_execution_matches_current_action(
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
    if not _current_action_identity_has_provider_currentness(current_action_identity):
        return False
    return _matches_current_action(
        action_type=action_type,
        work_unit_id=work_unit_id,
        work_unit_fingerprint=work_unit_fingerprint,
        current_action_identity=current_action_identity,
    )


def _current_action_identity_has_provider_currentness(identity: Mapping[str, Any]) -> bool:
    if _non_empty_text(identity.get("work_unit_fingerprint")) is not None:
        return True
    if _text_items(identity.get("work_unit_fingerprints")):
        return True
    basis = _mapping(identity.get("currentness_basis"))
    return (
        _non_empty_text(basis.get("work_unit_fingerprint")) is not None
        or _non_empty_text(basis.get("source_fingerprint")) is not None
        or _non_empty_text(identity.get("source_ref")) is not None
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
    if (
        _current_identity_is_opl_authorization_typed_blocker(current_action_identity)
        and _non_empty_text(current_action_identity.get("work_unit_fingerprint")) is None
        and not _text_items(current_action_identity.get("work_unit_fingerprints"))
    ):
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
