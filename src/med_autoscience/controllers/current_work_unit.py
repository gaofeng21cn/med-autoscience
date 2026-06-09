from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from med_autoscience.runtime_control.owner_route_attempt_protocol import (
    currentness_basis as owner_route_currentness_basis,
    owner_reason_contract,
)
from med_autoscience.controllers.guarded_apply_owner_delta_contract import (
    GUARDED_APPLY_ACCEPTED_ANSWER_SHAPES,
    GUARDED_APPLY_DESIRED_DELTA,
    GUARDED_APPLY_STAGE_ID,
    guarded_apply_current_owner_delta_validation,
    guarded_apply_identity_typed_blocker,
    normalize_guarded_apply_current_owner_delta,
)


SURFACE_KIND = "current_work_unit"
SCHEMA_VERSION = 1
ALLOWED_STATUSES = (
    "executable_owner_action",
    "running_provider_attempt",
    "typed_blocker",
    "blocked_current_work_unit",
)
LIVE_ATTEMPT_SUPERSEDED_BLOCKERS = frozenset(
    {
        "live_worker_requires_worker_running",
        "managed_runtime_audit_unhealthy",
        "medical_paper_readiness_missing",
        "medical_paper_readiness_not_ready",
        "opl_current_control_state.handoff_required",
        "opl_stage_attempt_admission_required",
        "provider_admission_current_control_state_required",
        "quest_waiting_opl_runtime_owner_route",
        "repair_progress_ai_reviewer_recheck_required",
        "runtime_recovery_not_authorized",
        "runtime_recovery_retry_budget_exhausted",
    }
)
CURRENT_ACTION_SUPERSEDED_RUNTIME_BLOCKERS = frozenset(
    {
        "opl_current_control_state.handoff_required",
        "opl_stage_attempt_admission_required",
        "provider_admission_current_control_state_required",
        "quest_marked_running_but_no_live_session",
        "quest_waiting_opl_runtime_owner_route",
        "repair_progress_ai_reviewer_recheck_required",
        "repair_progress_gate_replay_required",
        "runtime_recovery_not_authorized",
    }
)
MEDICAL_READINESS_BLOCKERS = frozenset(
    {
        "medical_paper_readiness_missing",
        "medical_paper_readiness_not_ready",
    }
)
PAPER_DELTA_READINESS_SUPERSEDING_ACTION_SOURCES = frozenset(
    {
        "domain_transition",
        "repair_progress_projection.mas_owner_repair_execution_evidence",
        "study_progress.next_forced_delta.owner_action",
    }
)
PROVIDER_ADMISSION_REPAIR_ACTIONS = frozenset(
    {
        "return_to_ai_reviewer_workflow",
        "run_gate_clearing_batch",
        "run_quality_repair_batch",
    }
)
PROVIDER_ADMISSION_AUTHORITIES = frozenset({"mas_provider_admission_identity"})
REASON_ONLY_TYPED_BLOCKERS = frozenset(
    {
        "medical_paper_readiness_missing",
        "medical_paper_readiness_not_ready",
        "medical_prose_review_request_rehydrate_required",
        "paper_progress_stall_current_missing",
        "paper_progress_stall_fingerprint_stale",
        "paper_progress_stall_terminal",
        "progress_first_owner_redrive_budget_exhausted",
        "typed_closeout_packet_required",
    }
)
RUNNING_HEALTH_VALUES = frozenset(
    {
        "attempt_running",
        "live",
        "provider_admitted",
        "running",
    }
)
AUTHORITY_BOUNDARY = {
    "surface_kind": SURFACE_KIND,
    "authority": "mas_current_work_unit_reducer",
    "top_level_truth": "status",
    "stage_transition_authority": "OPL Stage Transition Authority",
    "stage_authority_role": "non_authoritative_observation_and_intent_producer",
    "allowed_statuses": list(ALLOWED_STATUSES),
    "mas_owner_authority_preserved": True,
    "can_write_stage_current_pointer": False,
    "can_write_current_owner_delta": False,
    "can_write_stage_terminal_state": False,
    "can_write_runtime_owned_surfaces": False,
    "can_write_paper_or_package": False,
    "can_authorize_quality_verdict": False,
    "can_authorize_publication_ready": False,
}


def build_current_work_unit(
    *,
    status: Mapping[str, Any] | None = None,
    progress: Mapping[str, Any] | None = None,
    actions: Sequence[Mapping[str, Any]] | None = None,
    current_executable_owner_action: Mapping[str, Any] | None = None,
    current_execution_envelope: Mapping[str, Any] | None = None,
    owner_route: Mapping[str, Any] | None = None,
    provider_admission: Mapping[str, Any] | None = None,
    provider_running_proof: Mapping[str, Any] | None = None,
    live_provider_attempt: Mapping[str, Any] | None = None,
    typed_blocker: Mapping[str, Any] | None = None,
    blocked_reason: str | None = None,
    next_owner: str | None = None,
    runtime_health: Mapping[str, Any] | None = None,
    source_refs: Sequence[str] | None = None,
) -> dict[str, Any]:
    status_payload = _mapping(status)
    progress_payload = _mapping(progress)
    route_payload = _mapping(owner_route)
    runtime_health_payload = _mapping(runtime_health)
    resolved_source_refs = _source_refs(status_payload, progress_payload, source_refs)
    stage_owner_answer_action = _stage_owner_answer_missing_action(progress_payload)
    action = _first_action(actions) or _action_from_current_action(current_executable_owner_action)
    if stage_owner_answer_action is not None and not _action_supersedes_stage_owner_answer(
        action=action,
        progress=progress_payload,
    ):
        action = stage_owner_answer_action
    elif action is not None and _action_consumed_by_dispatch_receipt(action=action, progress=progress_payload):
        action = None
    if action is None:
        action = _action_from_envelope(current_execution_envelope)
    resolved_typed_blocker = _typed_blocker(
        typed_blocker,
        blocked_reason=blocked_reason,
        owner=next_owner,
    )
    running_attempt = _strict_running_provider_attempt(
        live_provider_attempt=live_provider_attempt,
        provider_running_proof=provider_running_proof,
        runtime_health=runtime_health_payload,
        owner=next_owner,
    )
    if running_attempt is None:
        running_attempt = _strict_running_provider_attempt(
            live_provider_attempt=provider_admission,
            provider_running_proof=None,
            runtime_health=runtime_health_payload,
            owner=next_owner,
        )
    if running_attempt is not None and _running_attempt_invalidated_by_progress(progress_payload):
        running_attempt = None
    if (
        running_attempt is not None
        and stage_owner_answer_action is not None
        and not _running_attempt_satisfies_stage_owner_answer(
            running_attempt=running_attempt,
            owner_answer_action=stage_owner_answer_action,
        )
    ):
        running_attempt = None
    stage_owner_identity_blocker = _stage_owner_answer_identity_typed_blocker(progress_payload)
    basis = _currentness_basis(
        owner_route=route_payload,
        action=action,
        progress=progress_payload,
        runtime_health=runtime_health_payload,
        running_attempt=running_attempt,
    )
    if running_attempt is not None:
        if _running_attempt_can_supersede_blocker(resolved_typed_blocker):
            return _current_work_unit(
                status="running_provider_attempt",
                owner=_text(running_attempt.get("owner")) or _text(next_owner),
                action_type=_text(running_attempt.get("action_type")),
                work_unit_id=_running_work_unit_id(running_attempt),
                work_unit_fingerprint=_text(running_attempt.get("work_unit_fingerprint")),
                action_fingerprint=_text(running_attempt.get("action_fingerprint")),
                input_refs=resolved_source_refs,
                required_output_contract=_running_required_output_contract(running_attempt),
                acceptance_refs=_text_items(running_attempt.get("acceptance_refs")),
                currentness_basis=basis,
                state={
                    "state_kind": "running_provider_attempt",
                    "provider_attempt_proof": _provider_attempt_proof_state(running_attempt),
                    "strict_running_proof": True,
                    "pending_provider_admission_only": False,
                },
                status_payload=status_payload,
                progress_payload=progress_payload,
                action=action,
            )
        if resolved_typed_blocker is not None:
            return _typed_blocker_work_unit(
                blocker=resolved_typed_blocker,
                action=action,
                status_payload=status_payload,
                progress_payload=progress_payload,
                source_refs=resolved_source_refs,
                currentness_basis=basis,
                source="typed_blocker",
            )
    if stage_owner_identity_blocker is not None:
        return _typed_blocker_work_unit(
            blocker=stage_owner_identity_blocker,
            action=action,
            status_payload=status_payload,
            progress_payload=progress_payload,
            source_refs=resolved_source_refs,
            currentness_basis=basis,
            source="stage_owner_answer_identity",
            status_kind="blocked_current_work_unit",
        )
    stage_owner_answer_blocker = _stage_owner_answer_typed_blocker(progress_payload)
    if stage_owner_answer_blocker is not None and not _action_supersedes_stage_owner_answer(
        action=action,
        progress=progress_payload,
    ):
        return _typed_blocker_work_unit(
            blocker=stage_owner_answer_blocker,
            action=action,
            status_payload=status_payload,
            progress_payload=progress_payload,
            source_refs=resolved_source_refs,
            currentness_basis=basis,
            source="stage_owner_answer",
        )
    if action is not None and _action_supersedes_typed_blocker(
        action=action,
        blocker=resolved_typed_blocker,
        progress=progress_payload,
    ):
        return _action_work_unit(
            action=action,
            owner=_action_owner(action, next_owner=next_owner),
            status_payload=status_payload,
            progress_payload=progress_payload,
            source_refs=resolved_source_refs,
            currentness_basis=basis,
            provider_admission=provider_admission,
        )
    if resolved_typed_blocker is not None:
        return _typed_blocker_work_unit(
            blocker=resolved_typed_blocker,
            action=action,
            status_payload=status_payload,
            progress_payload=progress_payload,
            source_refs=resolved_source_refs,
            currentness_basis=basis,
            source="typed_blocker",
        )
    if action is not None:
        return _action_work_unit(
            action=action,
            owner=_action_owner(action, next_owner=next_owner),
            status_payload=status_payload,
            progress_payload=progress_payload,
            source_refs=resolved_source_refs,
            currentness_basis=basis,
            provider_admission=provider_admission,
        )
    blocker = _minimal_blocker(blocked_reason or "current_work_unit_unresolved", owner=next_owner)
    return _typed_blocker_work_unit(
        blocker=blocker,
        action=None,
        status_payload=status_payload,
        progress_payload=progress_payload,
        source_refs=resolved_source_refs,
        currentness_basis=basis,
        source="blocked_current_work_unit",
        status_kind="blocked_current_work_unit",
    )


def _action_work_unit(
    *,
    action: Mapping[str, Any],
    owner: str,
    status_payload: Mapping[str, Any],
    progress_payload: Mapping[str, Any],
    source_refs: Sequence[str],
    currentness_basis: Mapping[str, Any],
    provider_admission: Mapping[str, Any] | None,
) -> dict[str, Any]:
    action_type = _action_type(action)
    work_unit_id = _work_unit_id(action.get("next_work_unit")) or _work_unit_id(action.get("work_unit_id")) or action_type
    pending_provider_admission = _provider_admission_pending(provider_admission)
    return _current_work_unit(
        status="executable_owner_action",
        owner=owner,
        action_type=action_type,
        work_unit_id=work_unit_id,
        work_unit_fingerprint=_work_unit_fingerprint(action, currentness_basis=currentness_basis),
        action_fingerprint=_action_fingerprint(action, currentness_basis=currentness_basis),
        input_refs=_input_refs(action, source_refs),
        required_output_contract=_required_output_contract(action),
        acceptance_refs=_acceptance_refs(action),
        currentness_basis=currentness_basis,
        state={
            "state_kind": "executable_owner_action",
            "source": _action_source(action),
            "next_work_unit": work_unit_id,
            "owner_answer_missing": action.get("owner_answer_missing") is True,
            "owner_answer_still_required": action.get("owner_answer_still_required") is True,
            "latest_owner_answer_ref": _text(action.get("latest_owner_answer_ref")),
            "provider_admission_pending": pending_provider_admission,
            "pending_provider_admission_evidence": _pending_provider_admission_evidence(
                provider_admission
            )
            if pending_provider_admission
            else None,
        },
        status_payload=status_payload,
        progress_payload=progress_payload,
        action=action,
    )


def _typed_blocker_work_unit(
    *,
    blocker: Mapping[str, Any],
    action: Mapping[str, Any] | None,
    status_payload: Mapping[str, Any],
    progress_payload: Mapping[str, Any],
    source_refs: Sequence[str],
    currentness_basis: Mapping[str, Any],
    source: str,
    status_kind: str = "typed_blocker",
) -> dict[str, Any]:
    owner = _text(blocker.get("owner")) or _text(blocker.get("next_owner")) or "med-autoscience"
    blocker_type = (
        _text(blocker.get("blocker_type"))
        or _text(blocker.get("blocker_id"))
        or _text(blocker.get("blocked_reason"))
        or "typed_blocker"
    )
    return _current_work_unit(
        status=status_kind,
        owner=owner,
        action_type=_text(blocker.get("action_type")) or _text(blocker.get("work_unit_id")),
        work_unit_id=_work_unit_id(blocker.get("work_unit_id")) or _work_unit_id(blocker.get("next_work_unit")),
        work_unit_fingerprint=_text(blocker.get("work_unit_fingerprint")),
        action_fingerprint=_text(blocker.get("action_fingerprint")),
        input_refs=_input_refs(blocker, source_refs),
        required_output_contract=_required_output_contract(blocker),
        acceptance_refs=_acceptance_refs(blocker),
        currentness_basis=currentness_basis,
        state={
            "state_kind": status_kind,
            "source": source,
            "typed_blocker": dict(blocker),
            "blocker_type": blocker_type,
            "mas_owner_authority_preserved": True,
            "stale_queue_or_handoff_can_override": False,
        },
        status_payload=status_payload,
        progress_payload=progress_payload,
        action=action,
    )


def _current_work_unit(
    *,
    status: str,
    owner: str | None,
    action_type: str | None,
    work_unit_id: str | None,
    work_unit_fingerprint: str | None,
    action_fingerprint: str | None,
    input_refs: Sequence[str],
    required_output_contract: Mapping[str, Any],
    acceptance_refs: Sequence[str],
    currentness_basis: Mapping[str, Any],
    state: Mapping[str, Any],
    status_payload: Mapping[str, Any],
    progress_payload: Mapping[str, Any],
    action: Mapping[str, Any] | None,
) -> dict[str, Any]:
    basis = dict(currentness_basis)
    if work_unit_id and not basis.get("work_unit_id"):
        basis["work_unit_id"] = work_unit_id
    if work_unit_fingerprint and not basis.get("work_unit_fingerprint"):
        basis["work_unit_fingerprint"] = work_unit_fingerprint
    return {
        "surface_kind": SURFACE_KIND,
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "study_id": _text(progress_payload.get("study_id")) or _text(status_payload.get("study_id")),
        "quest_id": _text(progress_payload.get("quest_id")) or _text(status_payload.get("quest_id")),
        "stage_id": _stage_id(action=action, progress=progress_payload, status=status_payload),
        "owner": owner or "med-autoscience",
        "action_type": action_type,
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": work_unit_fingerprint,
        "action_fingerprint": action_fingerprint,
        "input_refs": list(dict.fromkeys(input_refs)),
        "required_output_contract": dict(required_output_contract),
        "acceptance_refs": list(dict.fromkeys(acceptance_refs)),
        "state": {key: value for key, value in state.items() if value not in (None, "", [], {})},
        "currentness_basis": basis,
        "authority_boundary": dict(AUTHORITY_BOUNDARY),
    }


def _strict_running_provider_attempt(
    *,
    live_provider_attempt: Mapping[str, Any] | None,
    provider_running_proof: Mapping[str, Any] | None,
    runtime_health: Mapping[str, Any],
    owner: str | None,
) -> dict[str, Any] | None:
    attempt = _mapping(provider_running_proof) or _mapping(live_provider_attempt)
    if attempt.get("running_provider_attempt") is not True:
        return None
    if _attempt_has_matching_terminal_closeout(attempt):
        return None
    active_stage_attempt_id = _text(attempt.get("active_stage_attempt_id"))
    active_run_id = _text(attempt.get("active_run_id"))
    active_workflow_id = _text(attempt.get("active_workflow_id"))
    if active_stage_attempt_id is None and active_run_id is None and active_workflow_id is None:
        return None
    health = _mapping(attempt.get("runtime_health")) or runtime_health
    if health.get("strict_live") is False:
        return None
    if not _has_running_health(health):
        return None
    return {
        **attempt,
        "owner": _text(owner) or _text(attempt.get("next_owner")) or _text(attempt.get("owner")),
        "active_stage_attempt_id": active_stage_attempt_id,
        "active_run_id": active_run_id,
        "active_workflow_id": active_workflow_id,
        "runtime_health": health,
    }


def _has_running_health(health: Mapping[str, Any]) -> bool:
    values = {
        _text(health.get("health_status")),
        _text(health.get("runtime_liveness_status")),
        _text(health.get("provider_status")),
        _text(health.get("attempt_state")),
        _text(health.get("status")),
    }
    return bool(values.intersection(RUNNING_HEALTH_VALUES))


def _running_work_unit_id(running_attempt: Mapping[str, Any]) -> str | None:
    health = _mapping(running_attempt.get("runtime_health"))
    return (
        _work_unit_id(running_attempt.get("work_unit_id"))
        or _work_unit_id(running_attempt.get("next_work_unit"))
        or _work_unit_id(health.get("work_unit_id"))
        or _text(running_attempt.get("action_type"))
        or _text(running_attempt.get("active_stage_attempt_id"))
        or _text(running_attempt.get("active_workflow_id"))
        or _text(running_attempt.get("active_run_id"))
    )


def _provider_attempt_proof_state(running_attempt: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "running_provider_attempt": True,
        "active_stage_attempt_id": _text(running_attempt.get("active_stage_attempt_id")),
        "active_run_id": _text(running_attempt.get("active_run_id")),
        "active_workflow_id": _text(running_attempt.get("active_workflow_id")),
        "runtime_health": _mapping(running_attempt.get("runtime_health")) or None,
    }


def _running_required_output_contract(running_attempt: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "accepted_terminal_results": ["owner_receipt", "typed_blocker", "provider_closeout"],
        "provider_attempt_running_proof_required": True,
        "strict_running_proof_observed": True,
        "owner_receipt_or_typed_blocker_required_for_completion": True,
        "active_stage_attempt_id": _text(running_attempt.get("active_stage_attempt_id")),
        "active_workflow_id": _text(running_attempt.get("active_workflow_id")),
    }


def _running_attempt_can_supersede_blocker(blocker: Mapping[str, Any] | None) -> bool:
    payload = _mapping(blocker)
    if not payload:
        return True
    return _text(payload.get("blocker_type")) in LIVE_ATTEMPT_SUPERSEDED_BLOCKERS


def _running_attempt_satisfies_stage_owner_answer(
    *,
    running_attempt: Mapping[str, Any],
    owner_answer_action: Mapping[str, Any],
) -> bool:
    expected_stage_id = _text(owner_answer_action.get("stage_id"))
    expected_work_unit = _text(owner_answer_action.get("work_unit_id"))
    expected_fingerprint = _text(owner_answer_action.get("work_unit_fingerprint"))
    expected_owner_answer_ref = _text(owner_answer_action.get("latest_owner_answer_ref"))
    expected_lineage_ref = _text(_mapping(owner_answer_action.get("owner_route_currentness_basis")).get("lineage_ref"))
    attempt_stage_id = _text(running_attempt.get("stage_id"))
    if expected_stage_id is not None and attempt_stage_id != expected_stage_id:
        return False
    attempt_lineage_ref = _text(running_attempt.get("lineage_ref")) or _text(
        _mapping(running_attempt.get("runtime_health")).get("lineage_ref")
    )
    if expected_lineage_ref is not None and attempt_lineage_ref != expected_lineage_ref:
        return False
    attempt_work_unit = (
        _text(running_attempt.get("work_unit_id"))
        or _text(running_attempt.get("next_work_unit"))
        or _text(_mapping(running_attempt.get("runtime_health")).get("work_unit_id"))
    )
    if expected_work_unit is not None and attempt_work_unit != expected_work_unit:
        return False
    if expected_fingerprint is not None:
        attempt_fingerprints = {
            text
            for value in (
                running_attempt.get("work_unit_fingerprint"),
                running_attempt.get("action_fingerprint"),
                running_attempt.get("lineage_ref"),
                _mapping(running_attempt.get("runtime_health")).get("work_unit_fingerprint"),
            )
            if (text := _text(value)) is not None
        }
        if expected_fingerprint not in attempt_fingerprints:
            return False
    observed_answer_refs = _stage_owner_answer_refs(running_attempt)
    if expected_owner_answer_ref is None:
        return False
    if expected_owner_answer_ref not in observed_answer_refs:
        return False
    return any(
        ref in observed_answer_refs
        for ref in _text_items(owner_answer_action.get("acceptance_refs")) + [expected_owner_answer_ref]
    )


def _stage_owner_answer_refs(payload: Mapping[str, Any]) -> set[str]:
    refs: set[str] = set()
    for key in (
        "domain_owner_receipt_ref",
        "quality_gate_receipt_ref",
        "typed_blocker_ref",
        "human_gate_ref",
        "route_back_evidence_ref",
    ):
        if ref := _text(payload.get(key)):
            refs.add(ref)
    for key in (
        "domain_owner_receipt_refs",
        "quality_gate_receipt_refs",
        "typed_blocker_refs",
        "human_gate_refs",
        "route_back_evidence_refs",
    ):
        refs.update(_text_items(payload.get(key)))
    runtime_health = _mapping(payload.get("runtime_health"))
    if runtime_health:
        refs.update(_stage_owner_answer_refs(runtime_health))
    return refs


def _running_attempt_invalidated_by_progress(progress: Mapping[str, Any]) -> bool:
    runtime_refs = _mapping(progress.get("opl_runtime_refs"))
    if runtime_refs.get("strict_live") is not False:
        return False
    if _text(runtime_refs.get("active_run_id")) is not None:
        return False
    auto_parked = _mapping(progress.get("auto_runtime_parked"))
    if auto_parked.get("superseded_by_current_owner_action") is not True:
        return False
    return _text(runtime_refs.get("runtime_liveness_status")) in {
        "unknown",
        "none",
        "not_live",
        "stale",
        "parked",
    }


def _attempt_has_matching_terminal_closeout(attempt: Mapping[str, Any]) -> bool:
    terminal = _mapping(attempt.get("latest_terminal_stage_log"))
    if not terminal:
        return False
    active_attempt_id = _stage_attempt_id_from_handoff(attempt)
    terminal_attempt_id = _text(terminal.get("stage_attempt_id"))
    if active_attempt_id is not None and terminal_attempt_id != active_attempt_id:
        return False
    if active_attempt_id is None and terminal_attempt_id is None:
        return False
    status = _text(terminal.get("status"))
    if status in {
        "blocked",
        "closed",
        "closed_with_domain_owner_refs",
        "completed",
        "failed",
        "terminal",
        "typed_blocked",
    }:
        return True
    return _text(terminal.get("source_path")) is not None and _text(terminal.get("record_path")) is not None


def _stage_attempt_id_from_handoff(handoff: Mapping[str, Any]) -> str | None:
    if text := _text(handoff.get("active_stage_attempt_id")):
        return text
    active_run_id = _text(handoff.get("active_run_id"))
    prefix = "opl-stage-attempt://"
    if active_run_id is not None and active_run_id.startswith(prefix):
        attempt_id = active_run_id[len(prefix) :].strip()
        return attempt_id or None
    return None


def _stage_owner_answer_typed_blocker(progress: Mapping[str, Any]) -> dict[str, Any] | None:
    delta = _stage_current_owner_delta(progress)
    if not _stage_delta_is_typed_blocker_owner_answer(progress=progress, delta=delta):
        return None
    reason = (
        _text(delta.get("reason"))
        or _text(delta.get("blocker_id"))
        or _text(delta.get("blocker_type"))
        or "typed_blocker"
    )
    source_ref = _text(delta.get("latest_owner_answer_ref")) or _text(delta.get("source_ref"))
    work_unit = _text(delta.get("action")) or _text(delta.get("action_type"))
    return {
        "blocker_type": reason,
        "blocker_id": reason,
        "owner": _text(delta.get("owner")) or "MedAutoScience",
        "work_unit_id": work_unit,
        "source_ref": source_ref,
        "latest_owner_answer_ref": source_ref,
        "latest_owner_answer_kind": "typed_blocker",
        "acceptance_refs": _text_items(delta.get("acceptance_refs")),
    }


def _stage_owner_answer_missing_action(progress: Mapping[str, Any]) -> dict[str, Any] | None:
    delta = _stage_current_owner_delta(progress)
    if not _stage_delta_requires_mas_owner_answer(delta):
        return None
    validation = guarded_apply_current_owner_delta_validation(delta)
    if validation.get("valid") is not True:
        return None
    normalized = normalize_guarded_apply_current_owner_delta(_mapping(validation.get("normalized")) or delta)
    stage_id = _text(normalized.get("stage_id")) or _text(progress.get("current_stage")) or GUARDED_APPLY_STAGE_ID
    desired_delta = _text(normalized.get("desired_delta")) or GUARDED_APPLY_DESIRED_DELTA
    accepted_return_shape = list(
        dict.fromkeys(
            [
                *_text_items(normalized.get("accepted_answer_shape")),
                *GUARDED_APPLY_ACCEPTED_ANSWER_SHAPES,
            ]
        )
    )
    work_unit_fingerprint = (
        _text(normalized.get("work_unit_fingerprint"))
        or _text(normalized.get("source_fingerprint"))
        or _text(normalized.get("lineage_ref"))
    )
    owner = _text(normalized.get("owner")) or _text(normalized.get("current_owner")) or "med-autoscience"
    return {
        "source": "stage_kernel_projection.current_owner_delta",
        "source_surface": "stage_kernel_projection.current_owner_delta",
        "stage_id": stage_id,
        "action_type": _text(normalized.get("action")) or stage_id,
        "owner": owner,
        "next_owner": owner,
        "recommended_owner": owner,
        "work_unit_id": desired_delta,
        "next_work_unit": desired_delta,
        "work_unit_fingerprint": work_unit_fingerprint,
        "action_fingerprint": work_unit_fingerprint,
        "required_delta_kind": desired_delta,
        "owner_receipt_required": True,
        "input_refs": _text_items(normalized.get("input_refs")),
        "acceptance_refs": _text_items(normalized.get("acceptance_refs")),
        "required_output_contract": {
            "owner_receipt_required": True,
            "quality_gate_receipt_accepted": True,
            "typed_blocker_accepted": True,
            "human_gate_accepted": True,
            "route_back_evidence_accepted": True,
            "accepted_return_shape": accepted_return_shape,
            "desired_delta": desired_delta,
            "latest_owner_answer_ref": _text(normalized.get("latest_owner_answer_ref")),
            "domain_ready_authorized": normalized.get("domain_ready_authorized") is True,
        },
        "owner_route_currentness_basis": {
            "source": "stage_kernel_projection.current_owner_delta",
            "stage_id": stage_id,
            "lineage_ref": _text(normalized.get("lineage_ref")),
            "work_unit_id": desired_delta,
            "work_unit_fingerprint": work_unit_fingerprint,
            "owner_answer_missing": True,
        },
        "owner_answer_missing": True,
        "owner_answer_still_required": True,
        "latest_owner_answer_ref": _text(normalized.get("latest_owner_answer_ref")),
    }


def _stage_owner_answer_identity_typed_blocker(progress: Mapping[str, Any]) -> dict[str, Any] | None:
    delta = _stage_current_owner_delta(progress)
    if not _stage_delta_requires_mas_owner_answer(delta, allow_invalid_owner_answer_fields=True):
        return None
    blocker = guarded_apply_identity_typed_blocker(delta)
    if blocker is None:
        return None
    normalized = normalize_guarded_apply_current_owner_delta(delta)
    return {
        **blocker,
        "blocker_type": "current_owner_delta_identity_missing_or_invalid",
        "work_unit_id": _text(normalized.get("desired_delta")) or GUARDED_APPLY_DESIRED_DELTA,
        "stage_id": _text(normalized.get("stage_id")) or GUARDED_APPLY_STAGE_ID,
        "source_ref": _text(normalized.get("lineage_ref")),
        "missing_required_fields": list(
            _mapping(blocker.get("current_owner_delta_validation")).get("missing_required_fields") or []
        ),
    }


def _stage_delta_requires_mas_owner_answer(
    delta: Mapping[str, Any],
    *,
    allow_invalid_owner_answer_fields: bool = False,
) -> bool:
    normalized = normalize_guarded_apply_current_owner_delta(delta)
    if not normalized:
        return False
    hard_gate = _mapping(delta.get("hard_gate"))
    if (
        normalized.get("owner_answer_missing") is not True
        and _text(hard_gate.get("state")) != "owner_answer_missing"
    ):
        return False
    if normalized.get("owner_answer_still_required") is False:
        return False
    if not allow_invalid_owner_answer_fields and _text(normalized.get("latest_owner_answer_ref")) is not None:
        return False
    if _text(normalized.get("stage_id")) != GUARDED_APPLY_STAGE_ID:
        return False
    if _text(normalized.get("desired_delta")) != GUARDED_APPLY_DESIRED_DELTA:
        return False
    owner = _text(normalized.get("owner")) or _text(normalized.get("current_owner"))
    return owner in {"med-autoscience", "MedAutoScience", None}


def _stage_delta_is_typed_blocker_owner_answer(
    *,
    progress: Mapping[str, Any],
    delta: Mapping[str, Any],
) -> bool:
    hard_gate = _mapping(delta.get("hard_gate"))
    if _text(hard_gate.get("state")) == "domain_owner_answer_recorded":
        answer_kind = (
            _text(hard_gate.get("owner_answer_kind"))
            or _text(delta.get("latest_owner_answer_kind"))
            or _text(delta.get("source_kind"))
        )
        return answer_kind == "typed_blocker"
    stage_kernel = _mapping(progress.get("stage_kernel_projection"))
    stage_run_kernel = _mapping(stage_kernel.get("stage_run_kernel"))
    return (
        _text(stage_run_kernel.get("status")) == "TypedBlocked"
        and _text(delta.get("source_kind")) == "typed_blocker"
        and _text(delta.get("source_ref")) is not None
    )


def _stage_current_owner_delta(progress: Mapping[str, Any]) -> dict[str, Any]:
    direct = _mapping(progress.get("current_owner_delta"))
    if direct:
        return direct
    stage_kernel = _mapping(progress.get("stage_kernel_projection"))
    delta = _mapping(stage_kernel.get("current_owner_delta"))
    if delta:
        return delta
    stage_run_kernel = _mapping(stage_kernel.get("stage_run_kernel"))
    return _mapping(stage_run_kernel.get("current_owner_delta"))


def _action_supersedes_stage_owner_answer(
    *,
    action: Mapping[str, Any] | None,
    progress: Mapping[str, Any],
) -> bool:
    payload = _mapping(action)
    if not payload:
        return False
    if _provider_admission_repair_action_supersedes_readiness_blocker(payload):
        return True
    if _gate_consumption_action_supersedes_readiness_blocker(payload):
        return True
    return _paper_delta_domain_transition_supersedes_readiness_blocker(
        action=payload,
        progress=progress,
    )


def _action_supersedes_typed_blocker(
    *,
    action: Mapping[str, Any],
    blocker: Mapping[str, Any] | None,
    progress: Mapping[str, Any] | None = None,
) -> bool:
    payload = _mapping(blocker)
    if not payload:
        return True
    blocker_type = _text(payload.get("blocker_type"))
    if blocker_type in CURRENT_ACTION_SUPERSEDED_RUNTIME_BLOCKERS:
        return (
            _action_is_stage_current_owner_delta(action)
            or _provider_admission_repair_action_supersedes_readiness_blocker(action)
            or _paper_delta_domain_transition_supersedes_readiness_blocker(
                action=action,
                progress=_mapping(progress),
            )
        )
    if blocker_type not in MEDICAL_READINESS_BLOCKERS:
        return False
    if _text(action.get("action_type")) == "complete_medical_paper_readiness_surface":
        return True
    if "complete_medical_paper_readiness_surface" in _text_items(action.get("allowed_actions")):
        return True
    if _provider_admission_repair_action_supersedes_readiness_blocker(action):
        return True
    if _gate_consumption_action_supersedes_readiness_blocker(action):
        return True
    return _paper_delta_domain_transition_supersedes_readiness_blocker(
        action=action,
        progress=_mapping(progress),
    )


def _action_is_stage_current_owner_delta(action: Mapping[str, Any]) -> bool:
    return (
        _text(action.get("source_surface"))
        or _text(action.get("source"))
    ) == "stage_kernel_projection.current_owner_delta"


def _paper_delta_domain_transition_supersedes_readiness_blocker(
    *,
    action: Mapping[str, Any],
    progress: Mapping[str, Any],
) -> bool:
    progress_first = _mapping(progress.get("progress_first_sprint_state"))
    paper_delta = _mapping(progress.get("paper_progress_delta"))
    if progress_first.get("paper_progress_delta_counted") is not True and _delta_count(paper_delta) <= 0:
        return False
    action_source = _text(action.get("source_surface")) or _text(action.get("source"))
    if action_source not in PAPER_DELTA_READINESS_SUPERSEDING_ACTION_SOURCES:
        return False
    if _text(action.get("action_type")) not in {
        "request_opl_stage_attempt",
        "return_to_ai_reviewer_workflow",
        "run_gate_clearing_batch",
        "run_quality_repair_batch",
    }:
        return False
    return _text(action.get("work_unit_id")) != "complete_medical_paper_readiness_surface"


def _provider_admission_repair_action_supersedes_readiness_blocker(action: Mapping[str, Any]) -> bool:
    action_type = _text(action.get("action_type"))
    action_types = {action_type, *_text_items(action.get("allowed_actions"))}
    if not action_types.intersection(PROVIDER_ADMISSION_REPAIR_ACTIONS):
        return False
    if _text(action.get("work_unit_id")) == "complete_medical_paper_readiness_surface":
        return False
    if _text(action.get("next_work_unit")) == "complete_medical_paper_readiness_surface":
        return False
    if _mapping(action.get("repair_progress_followup")).get("accepted_owner_receipt") is True:
        return True
    authority = _text(action.get("authority"))
    if authority in PROVIDER_ADMISSION_AUTHORITIES:
        return True
    if _mapping(action.get("repair_progress_precedence")).get("accepted_owner_receipt") is True:
        return True
    action_id = _text(action.get("action_id"))
    if action_id is not None and action_id.startswith("provider-admission::"):
        return True
    for key in ("action_fingerprint", "work_unit_fingerprint", "fingerprint"):
        text = _text(action.get(key))
        if text is not None and text.startswith("study-progress-current-owner-ticket::"):
            return True
    return False


def _gate_consumption_action_supersedes_readiness_blocker(action: Mapping[str, Any]) -> bool:
    action_types = {_text(action.get("action_type")), *_text_items(action.get("allowed_actions"))}
    if not action_types.intersection({"request_opl_stage_attempt", "run_gate_clearing_batch", "run_quality_repair_batch"}):
        return False
    work_unit = _text(action.get("work_unit_id")) or _text(action.get("next_work_unit"))
    if work_unit != "ai_reviewer_record_gate_consumption":
        return False
    target = _mapping(action.get("target_surface"))
    return _text(target.get("surface_ref")) == "artifacts/controller/gate_clearing_batch/latest.json"


def _typed_blocker(
    typed_blocker: Mapping[str, Any] | None,
    *,
    blocked_reason: str | None,
    owner: str | None,
) -> dict[str, Any] | None:
    if isinstance(typed_blocker, Mapping) and typed_blocker:
        return dict(typed_blocker)
    text = _text(blocked_reason)
    if text is None:
        return None
    if not _reason_only_blocked_reason_is_typed_blocker(reason=text, owner=owner):
        return None
    return _minimal_blocker(text, owner=owner)


def _minimal_blocker(blocker_type: str, *, owner: str | None) -> dict[str, Any]:
    return {
        "blocker_type": blocker_type,
        "owner": _text(owner) or "med-autoscience",
    }


def _reason_only_blocked_reason_is_typed_blocker(*, reason: str, owner: str | None) -> bool:
    if reason in REASON_ONLY_TYPED_BLOCKERS:
        return True
    contract = owner_reason_contract(reason=reason, owner=owner)
    if contract.get("registered") is not True:
        return True
    return not any(_text(action) is not None for action in contract.get("allowed_actions") or [])


def _currentness_basis(
    *,
    owner_route: Mapping[str, Any],
    action: Mapping[str, Any] | None,
    progress: Mapping[str, Any],
    runtime_health: Mapping[str, Any],
    running_attempt: Mapping[str, Any] | None,
) -> dict[str, Any]:
    basis = _mapping(owner_route_currentness_basis(owner_route)) if owner_route else {}
    action_payload = _mapping(action)
    action_source_refs = _mapping(action_payload.get("source_refs"))
    embedded = (
        _mapping(action_payload.get("owner_route_currentness_basis"))
        or _mapping(action_payload.get("currentness_basis"))
        or _mapping(action_source_refs.get("owner_route_currentness_basis"))
    )
    publication_eval = _mapping(progress.get("publication_eval"))
    running = _mapping(running_attempt)
    result = {
        **basis,
        **{key: value for key, value in embedded.items() if value not in (None, "", [], {})},
    }
    for key, value in {
        "source_eval_id": (
            _text(action_payload.get("source_eval_id"))
            or _text(action_source_refs.get("source_eval_id"))
            or _text(publication_eval.get("eval_id"))
        ),
        "work_unit_id": _work_unit_id(action_payload.get("work_unit_id"))
        or _work_unit_id(action_payload.get("next_work_unit"))
        or _running_work_unit_id(running),
        "work_unit_fingerprint": _work_unit_fingerprint(action_payload, currentness_basis=result)
        or _text(running.get("work_unit_fingerprint")),
        "truth_epoch": _text(action_payload.get("truth_epoch")) or _text(progress.get("truth_epoch")),
        "runtime_health_epoch": _text(runtime_health.get("runtime_health_epoch"))
        or _text(action_payload.get("runtime_health_epoch")),
    }.items():
        if value is not None and result.get(key) in (None, "", [], {}):
            result[key] = value
    return {key: value for key, value in result.items() if value not in (None, "", [], {})}


def _action_consumed_by_dispatch_receipt(
    *,
    action: Mapping[str, Any],
    progress: Mapping[str, Any],
) -> bool:
    consumption = _mapping(_mapping(progress.get("progress_first_monitoring_summary")).get("dispatch_consumption"))
    if not consumption:
        consumption = _mapping(progress.get("dispatch_consumption"))
    if _text(consumption.get("consumption_status")) != "consumed":
        return False
    action_work_unit = _work_unit_id(action.get("work_unit_id")) or _work_unit_id(action.get("next_work_unit"))
    consumed_work_unit = _work_unit_id(consumption.get("work_unit_id"))
    if action_work_unit is None or consumed_work_unit != action_work_unit:
        return False
    action_fingerprints = {
        text
        for value in (
            action.get("work_unit_fingerprint"),
            action.get("action_fingerprint"),
            action.get("fingerprint"),
        )
        if (text := _text(value)) is not None
    }
    if not action_fingerprints:
        current_action = _mapping(progress.get("current_executable_owner_action"))
        current_action_work_unit = _work_unit_id(current_action.get("work_unit_id")) or _work_unit_id(
            current_action.get("next_work_unit")
        )
        if (
            current_action_work_unit == action_work_unit
            and _text(current_action.get("action_type")) == _text(action.get("action_type"))
        ):
            action_fingerprints.update(
                text
                for value in (
                    current_action.get("work_unit_fingerprint"),
                    current_action.get("action_fingerprint"),
                    current_action.get("fingerprint"),
                )
                if (text := _text(value)) is not None
            )
    consumed_fingerprints = {
        text
        for value in (
            consumption.get("work_unit_fingerprint"),
            consumption.get("action_fingerprint"),
            _mapping(consumption.get("canonical_work_unit_identity")).get("work_unit_fingerprint"),
        )
        if (text := _text(value)) is not None
    }
    if not action_fingerprints or not consumed_fingerprints:
        return False
    return bool(action_fingerprints.intersection(consumed_fingerprints))


def _action_from_current_action(current_action: Mapping[str, Any] | None) -> dict[str, Any] | None:
    current = _mapping(current_action)
    if _text(current.get("surface_kind")) != "current_executable_owner_action":
        return None
    allowed_actions = _text_items(current.get("allowed_actions"))
    action_type = _text(current.get("action_type")) or (allowed_actions[0] if allowed_actions else None)
    owner = _text(current.get("next_owner")) or _text(current.get("owner"))
    work_unit_id = _text(current.get("work_unit_id"))
    if action_type is None and owner is None and work_unit_id is None:
        return None
    return {
        **current,
        "action_type": action_type,
        "owner": owner,
        "recommended_owner": _text(current.get("recommended_owner")) or owner,
        "next_owner": owner,
        "next_work_unit": work_unit_id or action_type,
        "work_unit_id": work_unit_id,
        "source_surface": _text(current.get("source")) or _text(current.get("source_surface")),
    }


def _action_from_envelope(envelope: Mapping[str, Any] | None) -> dict[str, Any] | None:
    payload = _mapping(envelope)
    if _text(payload.get("state_kind")) != "executable_owner_action":
        return None
    work_unit_id = _work_unit_id(payload.get("next_work_unit"))
    owner = _text(payload.get("owner"))
    if owner is None and work_unit_id is None:
        return None
    return {
        "owner": owner,
        "next_owner": owner,
        "work_unit_id": work_unit_id,
        "next_work_unit": work_unit_id,
        "source_surface": "current_execution_envelope",
    }


def _first_action(actions: Sequence[Mapping[str, Any]] | None) -> dict[str, Any] | None:
    for item in actions or []:
        if isinstance(item, Mapping):
            return dict(item)
    return None


def _provider_admission_pending(provider_admission: Mapping[str, Any] | None) -> bool:
    payload = _mapping(provider_admission)
    if not payload:
        return False
    if payload.get("running_provider_attempt") is True:
        return False
    return (
        payload.get("provider_admission_pending_count") not in (None, 0)
        or payload.get("provider_attempt_or_lease_required") is True
        or _text(payload.get("execution_status")) == "handoff_ready"
        or any(
            _text(item.get("authority")) in PROVIDER_ADMISSION_AUTHORITIES
            for item in payload.get("action_queue") or []
            if isinstance(item, Mapping)
        )
    )


def _pending_provider_admission_evidence(provider_admission: Mapping[str, Any] | None) -> dict[str, Any]:
    payload = _mapping(provider_admission)
    return {
        "provider_admission_pending_count": payload.get("provider_admission_pending_count"),
        "execution_status": _text(payload.get("execution_status")),
        "provider_attempt_or_lease_required": payload.get("provider_attempt_or_lease_required") is True,
        "running_provider_attempt": payload.get("running_provider_attempt") is True,
    }


def _action_owner(action: Mapping[str, Any], *, next_owner: str | None) -> str:
    return (
        _text(action.get("owner"))
        or _text(action.get("recommended_owner"))
        or _text(action.get("next_owner"))
        or _text(next_owner)
        or "med-autoscience"
    )


def _action_source(action: Mapping[str, Any]) -> str | None:
    source = _text(action.get("source_surface")) or _text(action.get("source"))
    if source is not None:
        return source
    if (
        _mapping(action.get("repair_progress_followup")).get("accepted_owner_receipt") is True
        or _mapping(action.get("repair_progress_precedence")).get("accepted_owner_receipt") is True
    ):
        return "repair_progress_projection.mas_owner_repair_execution_evidence"
    return None


def _action_type(action: Mapping[str, Any]) -> str | None:
    return _text(action.get("action_type")) or _first_text(_text_items(action.get("allowed_actions")))


def _work_unit_id(value: object) -> str | None:
    if isinstance(value, Mapping):
        return (
            _text(value.get("unit_id"))
            or _text(value.get("work_unit_id"))
            or _text(value.get("id"))
            or _text(value.get("ref"))
        )
    return _text(value)


def _work_unit_fingerprint(
    action: Mapping[str, Any],
    *,
    currentness_basis: Mapping[str, Any],
) -> str | None:
    return (
        _text(action.get("work_unit_fingerprint"))
        or _text(action.get("fingerprint"))
        or _text(currentness_basis.get("work_unit_fingerprint"))
    )


def _action_fingerprint(
    action: Mapping[str, Any],
    *,
    currentness_basis: Mapping[str, Any],
) -> str | None:
    return (
        _text(action.get("action_fingerprint"))
        or _text(action.get("fingerprint"))
        or _text(action.get("work_unit_fingerprint"))
        or _text(currentness_basis.get("work_unit_fingerprint"))
    )


def _input_refs(action: Mapping[str, Any], source_refs: Sequence[str]) -> list[str]:
    refs = list(source_refs)
    for key in (
        "source_ref",
        "latest_owner_answer_ref",
        "dispatch_path",
        "request_ref",
        "stage_packet_ref",
    ):
        if ref := _text(action.get(key)):
            refs.append(ref)
    refs.extend(_text_items(action.get("input_refs")))
    refs.extend(_text_items(action.get("source_refs")))
    return list(dict.fromkeys(refs))


def _required_output_contract(action: Mapping[str, Any]) -> dict[str, Any]:
    explicit = _mapping(action.get("required_output_contract"))
    if explicit:
        return explicit
    contract = {
        "owner_receipt_required": action.get("owner_receipt_required") is not False,
        "typed_blocker_accepted": True,
        "accepted_terminal_results": ["owner_receipt", "typed_blocker"],
        "required_delta_kind": _text(action.get("required_delta_kind")),
        "target_surface": _mapping(action.get("target_surface")) or None,
        "required_output_surface": _text(action.get("required_output_surface")),
    }
    return {key: value for key, value in contract.items() if value not in (None, "", [], {})}


def _acceptance_refs(action: Mapping[str, Any]) -> list[str]:
    refs = _text_items(action.get("acceptance_refs"))
    refs.extend(_text_items(action.get("closeout_refs")))
    for key in ("owner_receipt_ref", "typed_blocker_ref", "source_ref"):
        if ref := _text(action.get(key)):
            refs.append(ref)
    return list(dict.fromkeys(refs))


def _source_refs(
    status: Mapping[str, Any],
    progress: Mapping[str, Any],
    source_refs: Sequence[str] | None,
) -> list[str]:
    refs: list[str] = []
    for item in source_refs or []:
        ref = _text(item)
        if ref is not None:
            refs.append(ref)
    refs.extend(_refs_from(_mapping(progress.get("refs"))))
    refs.extend(_refs_from(_mapping(status.get("refs"))))
    return sorted(dict.fromkeys(refs))


def _refs_from(value: Mapping[str, Any]) -> list[str]:
    refs: list[str] = []
    for key in ("controller_decision_path", "publication_eval_path", "runtime_status_summary_path"):
        if (ref := _text(value.get(key))) is not None:
            refs.append(ref)
    return refs


def _stage_id(
    *,
    action: Mapping[str, Any] | None,
    progress: Mapping[str, Any],
    status: Mapping[str, Any],
) -> str | None:
    action_payload = _mapping(action)
    return (
        _text(action_payload.get("stage_id"))
        or _text(progress.get("current_stage"))
        or _text(status.get("current_stage"))
        or _text(status.get("stage_id"))
    )


def _delta_count(value: Mapping[str, Any]) -> int:
    try:
        return int(value.get("count") or 0)
    except (TypeError, ValueError):
        return 0


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _text_items(value: object) -> list[str]:
    if isinstance(value, str):
        text = _text(value)
        return [text] if text is not None else []
    if not isinstance(value, (list, tuple, set)):
        return []
    result: list[str] = []
    for item in value:
        text = _text(item)
        if text is not None and text not in result:
            result.append(text)
    return result


def _first_text(items: Sequence[str]) -> str | None:
    return items[0] if items else None


__all__ = [
    "ALLOWED_STATUSES",
    "SURFACE_KIND",
    "build_current_work_unit",
]
