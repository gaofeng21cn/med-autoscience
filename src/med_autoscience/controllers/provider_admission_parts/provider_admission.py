from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from med_autoscience.controllers.provider_admission_parts.provider_admission_handoffs import (
    handoff_dispatch_path,
    handoff_work_unit_id,
    materialized_record_only_provider_handoff,
    materialized_record_only_provider_handoffs,
    transition_request_pending_dispatch_result,
)
from med_autoscience.controllers.provider_admission_parts.provider_admission_current_control_actions import (
    accepted_owner_gate_admission_matches_selected_dispatch_blocker,
    _current_action_identity,
    _current_control_action_dispatch_path,
    _current_control_action_identity,
    _current_control_action_requests_provider_admission,
    _current_control_executable_owner,
    _dispatch_authority_allows_current_control_provider_admission,
    _first_currentness_fingerprint,
    _merge_owner_route_currentness,
)
from med_autoscience.controllers.provider_admission_parts.provider_admission_helpers import (
    mapping as _mapping,
    non_empty_text as _non_empty_text,
    read_json_object as _read_json_object,
    text_items as _text_items,
)
from med_autoscience.controllers.provider_admission_parts.provider_admission_identity import (
    matches_current_action as _matches_current_action,
    owner_route_currentness_basis_complete as _owner_route_currentness_basis_complete,
    work_unit_ids_equivalent_for_action as _work_unit_ids_equivalent_for_action,
)
from med_autoscience.controllers.provider_admission_parts.provider_admission_probe_identity import (
    provider_attempt_matches_identity,
    provider_probe_has_matching_attempt,
    provider_probe_has_non_running_actions,
    study_has_running_provider_attempt,
)
from med_autoscience.controllers.provider_admission_parts import provider_admission_policy_projection
from med_autoscience.controllers.provider_admission_parts.provider_admission_stage_run_identity import (
    candidate_with_stage_run_admission_identity as _candidate_with_stage_run_admission_identity,
)
from med_autoscience.controllers.provider_admission_parts.provider_admission_request_only import (
    current_identity_fingerprint_for_action as _current_identity_fingerprint_for_action,
    first_present_text as _first_present_text,
    request_only_transition_dispatch_path as _request_only_transition_dispatch_path,
    request_only_transition_stage_packet_ref as _request_only_transition_stage_packet_ref,
    request_only_transition_stage_packet_refs as _request_only_transition_stage_packet_refs,
)
from med_autoscience.controllers.provider_admission_parts.provider_admission_transition_log_readback import (
    candidate_with_transition_log_readback as _candidate_with_log_readback,
)
from med_autoscience.controllers.provider_admission_parts.provider_admission_status_currentness import (
    current_control_payload_with_status_currentness,
)
from med_autoscience.controllers.provider_admission_parts.provider_admission_execution import (
    ACCEPTED_OWNER_GATE_DECISION_SOURCE,
    CURRENT_EXECUTABLE_OWNER_ACTION_SOURCE,
    PAPER_RECOVERY_SUCCESSOR_OWNER_ACTION_SOURCE,
    _status_envelope_blocks_provider_admission,
    _work_unit_fingerprint,
    candidate_with_authority_boundaries,
    provider_admission_candidate_from_execution,
    provider_admission_candidates_from_execution_payload,
)
from med_autoscience.controllers.provider_admission_parts.provider_admission_status import (
    status_blocks_action_queue_self_identity as _status_blocks_action_queue_self_identity,
)
from med_autoscience.controllers.provider_admission_parts.current_ai_reviewer_gate_replay import (
    source_eval_id_from_mapping,
)
from med_autoscience.controllers.study_transition_receipt_consumption_parts.owner_callable_candidates import (
    latest_owner_callable_receipt_payload,
)


def persisted_provider_admission_candidates(
    *,
    study_root: Path,
    status_payload: Mapping[str, Any] | None = None,
    allow_legacy_fallback: bool = False,
) -> list[dict[str, Any]]:
    payload, execution_ref = latest_owner_callable_receipt_payload(
        study_root=study_root,
        allow_legacy_fallback=allow_legacy_fallback,
    )
    if payload is None:
        return []
    return provider_admission_candidates_from_execution_payload(
        payload,
        execution_ref=execution_ref,
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
    for action in queued_actions:
        if not isinstance(action, Mapping):
            continue
        study = _mapping(studies_by_id.get(_non_empty_text(action.get("study_id")) or status_study_id))
        current_action_identity = _current_control_current_identity(
            action=action,
            status_payload=status,
            study_payload=study,
        )
        if _status_blocks_action_queue_self_identity(
            status,
            current_identity=current_action_identity,
            current_identity_required=True,
        ):
            continue
        candidate = provider_admission_candidate_from_current_control_action(
            action,
            study_root=study_root,
            status_study_id=status_study_id,
            current_action_identity=current_action_identity,
            status_payload=status,
            current_control_ref=current_control_ref,
            study_payload=study,
        )
        if candidate is not None:
            candidate = candidate_with_authority_boundaries(candidate)
            candidate = _candidate_with_log_readback(candidate, study_root=study_root)
            candidates.append(candidate_with_authority_boundaries(candidate))
    return candidates


def _current_control_current_identity(
    *,
    action: Mapping[str, Any],
    status_payload: Mapping[str, Any],
    study_payload: Mapping[str, Any],
) -> dict[str, Any]:
    status_identity = _current_action_identity(status_payload)
    if status_identity:
        return status_identity
    study_identity = _current_action_identity(study_payload)
    if study_identity:
        return study_identity
    if accepted_owner_gate_admission_matches_selected_dispatch_blocker(study=study_payload):
        return _current_control_action_identity(action)
    return {}


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
    owner_route = _mapping(action.get("owner_route"))
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
        accepted_owner_gate_dispatch_path = _accepted_owner_gate_stage_packet_dispatch_path(
            action,
            study_root=study_root,
        )
        accepted_owner_gate_dispatch_payload = (
            _read_json_object(accepted_owner_gate_dispatch_path)
            if accepted_owner_gate_dispatch_path is not None
            else None
        )
        if accepted_owner_gate_dispatch_payload is not None:
            dispatch_path = accepted_owner_gate_dispatch_path
            dispatch_payload = accepted_owner_gate_dispatch_payload
    if dispatch_payload is None:
        return _request_only_transition_action_candidate(
            action,
            study_root=study_root,
            status_study_id=status_study_id,
            current_action_identity=current_identity,
            status_payload=_mapping(status_payload),
            current_control_ref=current_control_ref,
            study_payload=study,
        )
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
        "execution_status": "transition_request_pending",
        "provider_attempt_or_lease_required": False,
        "provider_admission_requires_opl_runtime_result": True,
        "opl_transition_runtime_required": True,
        "provider_completion_is_domain_completion": False,
        "work_unit_id": work_unit_id,
        "mas_owner_action_source": _non_empty_text(action.get("mas_owner_action_source")),
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
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": action_fingerprint,
        "action_fingerprint": action_fingerprint,
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
            allow_dispatch_ref_stage_packet_identity_recovery=True,
        )
    )


def _accepted_owner_gate_stage_packet_dispatch_path(
    action: Mapping[str, Any],
    *,
    study_root: Path,
) -> Path | None:
    source = (
        _non_empty_text(action.get("mas_owner_action_source"))
        or _non_empty_text(action.get("source"))
        or _non_empty_text(action.get("source_surface"))
        or _non_empty_text(_mapping(action.get("owner_route_currentness_basis")).get("source"))
    )
    if source != ACCEPTED_OWNER_GATE_DECISION_SOURCE:
        return None
    basis = _mapping(action.get("owner_route_currentness_basis")) or _mapping(
        action.get("currentness_basis")
    )
    refs = (
        _non_empty_text(action.get("stage_packet_ref")),
        *_text_items(action.get("stage_packet_refs")),
        _non_empty_text(basis.get("stage_packet_ref")),
        *_text_items(basis.get("stage_packet_refs")),
    )
    for ref in refs:
        if ref is None:
            continue
        path = _resolve_stage_packet_ref(ref, study_root=study_root)
        if path.exists():
            return path
    return None


def _resolve_stage_packet_ref(ref: str, *, study_root: Path) -> Path:
    path = Path(ref).expanduser()
    if path.is_absolute():
        return path.resolve()
    root = Path(study_root).expanduser().resolve()
    study_id = root.name
    if len(path.parts) >= 2 and path.parts[:2] == ("studies", study_id):
        return (root.parent.parent / path).resolve()
    return (root / path).resolve()


def _request_only_transition_action_candidate(
    action: Mapping[str, Any],
    *,
    study_root: Path,
    status_study_id: str | None,
    current_action_identity: Mapping[str, Any],
    status_payload: Mapping[str, Any],
    current_control_ref: str | None,
    study_payload: Mapping[str, Any],
) -> dict[str, Any] | None:
    action_type = _non_empty_text(action.get("action_type"))
    source = (
        _non_empty_text(action.get("mas_owner_action_source"))
        or _non_empty_text(action.get("source"))
        or _non_empty_text(action.get("source_surface"))
        or _non_empty_text(_mapping(action.get("owner_route_currentness_basis")).get("source"))
    )
    if source != PAPER_RECOVERY_SUCCESSOR_OWNER_ACTION_SOURCE:
        return None
    if action_type is None:
        return None
    if (
        action_type != "request_opl_stage_attempt"
        and not _mapping(action.get("opl_domain_progress_transition_request"))
        and not _mapping(
            _mapping(action.get("paper_progress_policy_result")).get(
                "opl_domain_progress_transition_request"
            )
        )
    ):
        return None
    study_id = _non_empty_text(action.get("study_id")) or status_study_id
    if status_study_id is not None and study_id != status_study_id:
        return None
    if study_id is None:
        return None
    current_identity = _mapping(current_action_identity)
    if not current_identity:
        return None
    study = _mapping(study_payload)
    work_unit_id = _non_empty_text(action.get("work_unit_id")) or _non_empty_text(
        action.get("next_work_unit")
    )
    action_basis = _mapping(action.get("owner_route_currentness_basis")) or _mapping(
        action.get("currentness_basis")
    )
    current_identity_basis = _mapping(current_identity.get("currentness_basis"))
    action_fingerprint = _first_currentness_fingerprint(
        action.get("action_fingerprint"),
        action.get("work_unit_fingerprint"),
        action.get("source_fingerprint"),
        action_basis.get("work_unit_fingerprint"),
        action_basis.get("source_fingerprint"),
        current_identity.get("work_unit_fingerprint"),
        current_identity.get("action_fingerprint"),
        current_identity_basis.get("work_unit_fingerprint"),
        current_identity_basis.get("source_fingerprint"),
        study_id=study_id,
        action_type=action_type,
        work_unit_id=work_unit_id,
    )
    if work_unit_id is None or action_fingerprint is None:
        return None
    route_identity_key = _first_present_text(
        action.get("route_identity_key"),
        current_identity.get("route_identity_key"),
        action_basis.get("route_identity_key"),
        current_identity_basis.get("route_identity_key"),
    )
    attempt_idempotency_key = _first_present_text(
        action.get("attempt_idempotency_key"),
        current_identity.get("attempt_idempotency_key"),
        action_basis.get("attempt_idempotency_key"),
        current_identity_basis.get("attempt_idempotency_key"),
        action.get("idempotency_key"),
        current_identity.get("idempotency_key"),
    )
    if attempt_idempotency_key is None:
        attempt_idempotency_key = route_identity_key
    stage_packet_ref = _request_only_transition_stage_packet_ref(
        action=action,
        current_action_identity=current_identity,
        study_id=study_id,
        work_unit_id=work_unit_id,
    )
    stage_packet_refs = _request_only_transition_stage_packet_refs(
        action=action,
        current_action_identity=current_identity,
        stage_packet_ref=stage_packet_ref,
    )
    dispatch_path = _request_only_transition_dispatch_path(
        action,
        study_root=study_root,
        action_type=action_type,
    )
    if not _matches_current_action(
        action_type=action_type,
        work_unit_id=work_unit_id,
        work_unit_fingerprint=action_fingerprint,
        current_action_identity=current_identity,
    ):
        return None
    owner = _non_empty_text(action.get("next_executable_owner")) or _non_empty_text(
        action.get("owner")
    )
    executable_owner = _current_control_executable_owner(action_type=action_type, owner=owner)
    if executable_owner is None:
        return None
    currentness_basis = {
        **dict(current_identity_basis),
        **dict(action_basis),
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": action_fingerprint,
        "action_fingerprint": action_fingerprint,
    }
    currentness_basis = {key: value for key, value in currentness_basis.items() if value is not None}
    execution = {
        "source": CURRENT_EXECUTABLE_OWNER_ACTION_SOURCE if dispatch_path is not None else source,
        "current_control_ref": current_control_ref,
        "study_id": study_id,
        "quest_id": _non_empty_text(action.get("quest_id"))
        or _non_empty_text(study.get("quest_id"))
        or _non_empty_text(status_payload.get("quest_id")),
        "action_type": action_type,
        "execution_status": "transition_request_pending",
        "provider_attempt_or_lease_required": False,
        "provider_admission_requires_opl_runtime_result": True,
        "opl_transition_runtime_required": True,
        "provider_completion_is_domain_completion": False,
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": action_fingerprint,
        "action_fingerprint": action_fingerprint,
        "next_executable_owner": executable_owner,
        "route_identity_key": route_identity_key,
        "attempt_idempotency_key": attempt_idempotency_key,
        "idempotency_key": attempt_idempotency_key,
        "required_output_surface": _non_empty_text(action.get("required_output_surface")),
        "stage_packet_ref": stage_packet_ref,
        "stage_packet_refs": stage_packet_refs,
        "checkpoint_refs": stage_packet_refs,
        "mas_owner_action_source": source,
        "owner_route_current": True,
        "owner_route": {
            "next_owner": executable_owner,
            "allowed_actions": [action_type],
            "work_unit_fingerprint": action_fingerprint,
            "source_refs": {
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": action_fingerprint,
                "action_fingerprint": action_fingerprint,
                "mas_owner_action_source": source,
                "stage_packet_ref": stage_packet_ref,
                "stage_packet_refs": stage_packet_refs,
                "route_identity_key": route_identity_key,
                "attempt_idempotency_key": attempt_idempotency_key,
                "owner_route_currentness_basis": currentness_basis,
            },
        },
    }
    candidate = provider_admission_candidate_from_execution(
        execution,
        execution_ref=current_control_ref,
        status_study_id=status_study_id,
        current_action_identity=current_identity,
    )
    if candidate is None:
        return None
    candidate["source"] = CURRENT_EXECUTABLE_OWNER_ACTION_SOURCE if dispatch_path is not None else source
    candidate["current_control_ref"] = current_control_ref
    candidate["mas_owner_action_source"] = source
    candidate["provider_admission_pending"] = False
    candidate["provider_attempt_or_lease_required"] = False
    candidate["provider_admission_requires_opl_runtime_result"] = True
    candidate["opl_transition_runtime_required"] = True
    candidate["currentness_basis"] = currentness_basis
    if route_identity_key is not None:
        candidate["route_identity_key"] = route_identity_key
    if attempt_idempotency_key is not None:
        candidate["attempt_idempotency_key"] = attempt_idempotency_key
        candidate["idempotency_key"] = attempt_idempotency_key
    if dispatch_path is not None:
        candidate["dispatch_path"] = str(dispatch_path)
    else:
        candidate.pop("dispatch_path", None)
    candidate["stage_packet_ref"] = stage_packet_ref
    candidate["stage_packet_refs"] = stage_packet_refs
    candidate["checkpoint_refs"] = stage_packet_refs
    candidate["source_refs"] = {
        **_mapping(candidate.get("source_refs")),
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": action_fingerprint,
        "action_fingerprint": action_fingerprint,
        "current_control_ref": current_control_ref,
        "dispatch_path": str(dispatch_path) if dispatch_path is not None else None,
        "mas_owner_action_source": source,
        "stage_packet_ref": stage_packet_ref,
        "stage_packet_refs": stage_packet_refs,
        "route_identity_key": route_identity_key,
        "attempt_idempotency_key": attempt_idempotency_key,
    }
    return candidate_with_authority_boundaries(candidate)
