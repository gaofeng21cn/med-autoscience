from __future__ import annotations

from typing import Any, Mapping

from med_autoscience.controllers import control_identity
from med_autoscience.controllers.current_work_unit_parts.stage_packet_blockers import (
    is_selected_dispatch_stage_packet_blocker as _is_selected_dispatch_stage_packet_blocker,
)
from med_autoscience.controllers.gate_clearing_batch_work_units import (
    PUBLICATION_GATE_REPLAY_WORK_UNIT_IDS,
)
from med_autoscience.controllers.opl_execution_boundary import OPL_EXECUTION_AUTHORIZATION_BLOCKER
from med_autoscience.controllers.opl_transition_readback import (
    candidate_opl_transition_readback,
)
from med_autoscience.controllers.provider_admission_parts import (
    provider_admission_policy_projection,
)
from med_autoscience.controllers.provider_admission_parts.provider_admission_boundaries import (
    provider_admission_authority_boundary,
    provider_admission_candidate_with_authority_boundaries,
    stage_transition_authority_boundary,
)
from med_autoscience.controllers.provider_admission_parts.provider_admission_current_control_actions import (
    _current_action_identity,
    _dispatch_authority_allows_current_control_provider_admission,
    _first_currentness_fingerprint,
)
from med_autoscience.controllers.provider_admission_parts.provider_admission_handoffs import (
    handoff_dispatch_path,
    handoff_work_unit_id,
)
from med_autoscience.controllers.provider_admission_parts.provider_admission_helpers import (
    mapping as _mapping,
    non_empty_text as _non_empty_text,
    text_items as _text_items,
)
from med_autoscience.controllers.provider_admission_parts.provider_admission_identity import (
    current_identity_is_opl_authorization_typed_blocker as _current_identity_is_opl_authorization_typed_blocker,
    matches_current_action as _matches_current_action,
    matches_current_action_without_fingerprint as _matches_current_action_without_fingerprint,
    status_requires_current_identity as _status_requires_current_identity,
)
from med_autoscience.controllers.provider_admission_parts.provider_admission_stage_run_identity import (
    candidate_with_stage_run_admission_identity as _candidate_with_stage_run_admission_identity,
)
from med_autoscience.controllers.provider_admission_parts.provider_admission_status import (
    execution_state_kind as _execution_state_kind,
)
from med_autoscience.controllers.stage_outcome_authority_parts.execution_surfaces import (
    OWNER_CALLABLE_RECEIPT_SURFACE,
)


OWNER_CALLABLE_ADAPTER_RECEIPT_LATEST = (
    "artifacts/supervision/consumer/owner_callable_adapter_receipts/latest.json"
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
CURRENT_EXECUTABLE_OWNER_ACTION_SOURCE = (
    "opl_current_control_state.study_current_executable_owner_action"
)
PAPER_RECOVERY_SUCCESSOR_OWNER_ACTION_SOURCE = (
    "paper_recovery_state.next_safe_action.successor_owner_action"
)


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
    if not _provider_attempt_required(execution) and not _execution_requests_transition_runtime(
        execution
    ):
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
    transition_runtime_only = _execution_requests_transition_runtime(execution)
    if (
        study_id is None
        or action_type is None
        or work_unit_id is None
        or work_unit_fingerprint is None
        or (dispatch_path is None and not transition_runtime_only)
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
        "status": "transition_request_pending",
        "source": _execution_payload_source(execution, execution_ref=execution_ref),
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
        **({"dispatch_path": dispatch_path} if dispatch_path is not None else {}),
        "dispatch_authority": _non_empty_text(execution.get("dispatch_authority")),
        "mas_owner_action_source": _non_empty_text(execution.get("mas_owner_action_source")),
        "owner_callable_surface": _non_empty_text(execution.get("owner_callable_surface")),
        "blocked_reason": _execution_blocked_reason(execution),
        "next_executable_owner": _non_empty_text(execution.get("next_executable_owner")),
        "required_output_surface": _non_empty_text(execution.get("required_output_surface")),
        "provider_attempt_or_lease_required": False,
        "provider_admission_requires_opl_runtime_result": True,
        "opl_transition_runtime_required": True,
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
                "mas_owner_action_source",
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
            provider_admission_policy_projection.candidate_with_paper_progress_policy_result(
                candidate,
                execution=execution,
            ),
            execution=execution,
            allow_dispatch_ref_stage_packet_identity_recovery=True,
        )
    )


def _execution_payload_source(
    execution: Mapping[str, Any],
    *,
    execution_ref: str | None,
) -> str:
    if _non_empty_text(execution.get("surface")) == OWNER_CALLABLE_RECEIPT_SURFACE:
        return "owner_callable_adapter_receipt"
    if execution_ref and execution_ref.endswith(str(OWNER_CALLABLE_ADAPTER_RECEIPT_LATEST)):
        return "owner_callable_adapter_receipt"
    return "owner_callable_adapter_receipt"


def candidate_with_authority_boundaries(candidate: Mapping[str, Any]) -> dict[str, Any]:
    return provider_admission_candidate_with_authority_boundaries(
        provider_admission_policy_projection.with_readback_backed_status(
            _candidate_with_transition_request_identity(candidate)
        )
    )


def _candidate_with_transition_request_identity(candidate: Mapping[str, Any]) -> dict[str, Any]:
    payload = dict(candidate)
    request = _mapping(payload.get("opl_domain_progress_transition_request"))
    if not request:
        request = _mapping(
            _mapping(payload.get("paper_progress_policy_result")).get(
                "opl_domain_progress_transition_request"
            )
        )
    if not request:
        return payload
    request_key = _non_empty_text(request.get("idempotency_key")) or _non_empty_text(
        request.get("request_idempotency_key")
    )
    stage_run_identity = _mapping(request.get("stage_run_identity"))
    source_refs = dict(_mapping(payload.get("source_refs")))
    route_key = (
        _non_empty_text(stage_run_identity.get("route_identity_key"))
        or _non_empty_text(source_refs.get("route_identity_key"))
        or _non_empty_text(payload.get("route_identity_key"))
        or request_key
    )
    attempt_key = (
        _non_empty_text(stage_run_identity.get("attempt_idempotency_key"))
        or _non_empty_text(source_refs.get("attempt_idempotency_key"))
        or _non_empty_text(payload.get("attempt_idempotency_key"))
        or route_key
    )
    if (
        request_key is not None
        and _non_empty_text(request.get("recommended_transition_kind")) is not None
        and _paper_policy_request_identity_should_override_provider_identity(payload)
    ):
        route_key = request_key
        attempt_key = request_key
    if route_key is not None:
        payload["route_identity_key"] = route_key
    if attempt_key is not None:
        payload["attempt_idempotency_key"] = attempt_key
    if attempt_key is not None:
        payload["idempotency_key"] = attempt_key
    elif request_key is not None:
        payload["idempotency_key"] = request_key
    if route_key is not None:
        source_refs["route_identity_key"] = route_key
    if attempt_key is not None:
        source_refs["attempt_idempotency_key"] = attempt_key
    if source_refs:
        payload["source_refs"] = source_refs
    owner_basis = dict(_mapping(source_refs.get("owner_route_currentness_basis")))
    if owner_basis:
        source_refs["owner_route_currentness_basis"] = owner_basis
    return payload


def _paper_policy_request_identity_should_override_provider_identity(
    candidate: Mapping[str, Any],
) -> bool:
    if candidate_opl_transition_readback(candidate):
        return False
    if _non_empty_text(candidate.get("action_type")) == "request_opl_stage_attempt":
        return True
    if _candidate_is_mas_request_only_owner_action(candidate):
        return False
    source = _non_empty_text(candidate.get("source"))
    source_surface = _non_empty_text(candidate.get("source_surface"))
    if source == CURRENT_EXECUTABLE_OWNER_ACTION_SOURCE or (
        source is None and source_surface == CURRENT_EXECUTABLE_OWNER_ACTION_SOURCE
    ):
        return True
    if _non_empty_text(candidate.get("dispatch_path")) is not None:
        return False
    if _non_empty_text(candidate.get("dispatch_ref")) is not None:
        return False
    source_refs = _mapping(candidate.get("source_refs"))
    if _non_empty_text(source_refs.get("dispatch_path")) is not None:
        return False
    if _non_empty_text(source_refs.get("dispatch_ref")) is not None:
        return False
    return True


def _candidate_is_mas_request_only_owner_action(candidate: Mapping[str, Any]) -> bool:
    source_refs = _mapping(candidate.get("source_refs"))
    currentness_basis = _mapping(candidate.get("currentness_basis")) or _mapping(
        source_refs.get("owner_route_currentness_basis")
    )
    source = (
        _non_empty_text(candidate.get("mas_owner_action_source"))
        or _non_empty_text(source_refs.get("mas_owner_action_source"))
        or _non_empty_text(currentness_basis.get("mas_owner_action_source"))
        or _non_empty_text(currentness_basis.get("source"))
    )
    return source in {
        "gate_clearing_batch_followthrough.actionable_current_work_unit",
        PAPER_RECOVERY_SUCCESSOR_OWNER_ACTION_SOURCE,
    }


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
        _is_selected_dispatch_stage_packet_blocker(blocker_reason)
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
    if _non_empty_text(current_action_identity.get("source")) == "opl_current_control_state.action_queue":
        return False
    if not _provider_attempt_required(execution) and not _execution_requests_transition_runtime(
        execution
    ):
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
    if status in {"handoff_ready", "transition_request_pending"}:
        return True
    return status == "blocked" and _execution_blocked_reason(execution) == OPL_EXECUTION_AUTHORIZATION_BLOCKER


def _execution_requests_transition_runtime(execution: Mapping[str, Any]) -> bool:
    if _non_empty_text(execution.get("execution_status")) != "transition_request_pending":
        return False
    if execution.get("provider_admission_requires_opl_runtime_result") is not True:
        return False
    if execution.get("opl_transition_runtime_required") is not True:
        return False
    return True


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
    return _non_empty_text(execution.get("owner_callable_surface")) == "opl_owner_callable_adapter.stage_attempt"


def _execution_blocked_reason(execution: Mapping[str, Any]) -> str | None:
    typed_blocker = _mapping(execution.get("typed_blocker"))
    return (
        _non_empty_text(execution.get("blocked_reason"))
        or _non_empty_text(typed_blocker.get("blocker_id"))
        or _non_empty_text(typed_blocker.get("blocker_type"))
        or _non_empty_text(typed_blocker.get("reason"))
    )


def _work_unit_fingerprint(execution: Mapping[str, Any]) -> str | None:
    study_id = _non_empty_text(execution.get("study_id"))
    action_type = _non_empty_text(execution.get("action_type"))
    work_unit_id = handoff_work_unit_id(execution)
    stable_ticket = control_identity.stable_current_owner_ticket_fingerprint(
        study_id=study_id,
        work_unit_id=work_unit_id,
        action_type=action_type,
    )
    explicit_action_fingerprint = _non_empty_text(execution.get("action_fingerprint"))
    if explicit_action_fingerprint is not None and explicit_action_fingerprint == stable_ticket:
        return explicit_action_fingerprint
    owner_route = _mapping(execution.get("owner_route"))
    source_refs = _mapping(owner_route.get("source_refs"))
    basis = _mapping(source_refs.get("owner_route_currentness_basis")) or _mapping(
        _mapping(execution.get("prompt_contract")).get("owner_route_currentness_basis")
    )
    return _first_currentness_fingerprint(
        execution.get("action_fingerprint"),
        execution.get("work_unit_fingerprint"),
        execution.get("source_fingerprint"),
        owner_route.get("work_unit_fingerprint"),
        source_refs.get("work_unit_fingerprint"),
        basis.get("work_unit_fingerprint"),
        study_id=study_id,
        action_type=action_type,
        work_unit_id=work_unit_id,
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
