from __future__ import annotations

import hashlib
import json
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

from med_autoscience.controllers import paper_progress_policy_adapter
from med_autoscience.controllers.current_work_unit_parts.running_provider_attempt import (
    has_running_health,
    running_attempt_matches_current_action,
)
from med_autoscience.controllers.domain_health_diagnostic_parts.managed_wakeup import (
    _non_empty_text,
)
from med_autoscience.controllers.domain_health_diagnostic_parts.opl_transition_readback import (
    candidate_opl_transition_readback,
)
from med_autoscience.controllers.domain_health_diagnostic_parts.obligation_actuator_parts import (
    mas_domain_typed_blocker_authority_result,
)
from med_autoscience.controllers.domain_health_diagnostic_parts.obligation_actuator_parts.readback_result_validator import (
    ACCEPTED_OBLIGATION_OUTCOME_KINDS,
    ACTUATOR_AUTHORITY_BOUNDARY,
    CONSUMED_READBACK_IDENTITY_SURFACE,
    MAS_TRANSITION_REQUEST_SURFACE,
    OPL_TRANSITION_RUNTIME_KIND,
    OPL_TRANSITION_RUNTIME_OWNER,
    SUCCESS_OUTCOME_SOURCE_FAMILIES,
    allowed_outcomes_for_policy_label,
    consume_only_readback_boundary,
    opl_foundation_readback_boundary,
    outcome_has_required_consumed_readback_identity,
    outcome_has_required_foundation_readback,
    outcome_source_family,
)
from med_autoscience.profiles import WorkspaceProfile

_OBLIGATION_ACTUATOR_ALLOWED_OUTCOMES = list(ACCEPTED_OBLIGATION_OUTCOME_KINDS)


def _mas_owner_answer_readbacks(*, report: dict[str, Any]) -> list[dict[str, Any]]:
    all_actions = [
        dict(action)
        for action in report.get("managed_study_mas_owner_callable_actions") or []
        if isinstance(action, Mapping)
    ]
    if all_actions:
        report["managed_study_mas_owner_callable_actions"] = all_actions
    return all_actions


def apply_managed_study_obligation_actuator(
    *,
    report: dict[str, Any],
    profile: WorkspaceProfile,
    study_ids: tuple[str, ...],
    current_control_state: Mapping[str, Any] | None = None,
    fail_closed: bool,
    phase: str,
    refresh_owner_callable_actions: Callable[[list[dict[str, Any]]], None] | None = None,
) -> list[dict[str, Any]]:
    owner_callable_actions = _mas_owner_answer_readbacks(report=report)
    current_control = _mapping(current_control_state)
    outcomes = [
        dict(item)
        for item in report.get("managed_study_obligation_actuator_outcomes") or []
        if isinstance(item, Mapping)
    ]
    outcome_keys = {
        _obligation_actuator_outcome_key(outcome)
        for outcome in outcomes
        if _obligation_actuator_outcome_key(outcome) is not None
    }
    explicit_study_ids = {item for item in _text_items(study_ids)}
    action_results_by_study = _owner_callable_actions_by_study(
        report.get("managed_study_mas_owner_callable_actions")
    )
    refreshed_actions: list[Any] = []
    new_outcomes: list[dict[str, Any]] = []
    for action in report.get("managed_study_actions") or []:
        if not isinstance(action, Mapping):
            refreshed_actions.append(action)
            continue
        action_payload = dict(action)
        study_id = _non_empty_text(action_payload.get("study_id"))
        if study_id is None or (explicit_study_ids and study_id not in explicit_study_ids):
            refreshed_actions.append(action_payload)
            continue
        recovery = _mapping(action_payload.get("paper_recovery_state"))
        if not _recovery_requires_obligation_actuator(recovery):
            refreshed_actions.append(action_payload)
            continue
        existing_outcome = _existing_closed_outcome_for_action(
            action=action_payload,
            outcomes=outcomes,
        )
        if existing_outcome is not None:
            action_payload["dhd_apply_postcondition"] = _postcondition_from_outcome(
                existing_outcome
            )
            refreshed_actions.append(action_payload)
            continue
        outcome = _closed_obligation_outcome(
            action=action_payload,
            current_control_state=current_control,
            owner_callable_actions=action_results_by_study.get(study_id, []),
            profile=profile,
            fail_closed=fail_closed,
            phase=phase,
        )
        if outcome is None:
            refreshed_actions.append(action_payload)
            continue
        key = _obligation_actuator_outcome_key(outcome)
        if key is not None and key not in outcome_keys:
            outcomes.append(outcome)
            new_outcomes.append(outcome)
            outcome_keys.add(key)
        action_payload["dhd_apply_postcondition"] = _postcondition_from_outcome(outcome)
        refreshed_actions.append(action_payload)
    if refreshed_actions:
        report["managed_study_actions"] = refreshed_actions
        current_execution_evidence = _mapping(report.get("current_execution_evidence"))
        if "managed_study_actions" in current_execution_evidence:
            current_execution_evidence["managed_study_actions"] = refreshed_actions
            report["current_execution_evidence"] = current_execution_evidence
    if outcomes:
        report["managed_study_obligation_actuator_outcomes"] = outcomes
    if new_outcomes:
        actuator_summary = _mapping(report.get("managed_study_obligation_actuator_summary"))
        report["managed_study_obligation_actuator_summary"] = {
            **actuator_summary,
            "surface_kind": "managed_study_obligation_readback_projection_summary",
            "schema_version": 1,
            "phase": phase,
            "outcome_count": len(outcomes),
            "new_outcome_count": len(new_outcomes),
            "fail_closed_count": sum(
                1
                for outcome in outcomes
                if _mapping(outcome.get("typed_control_blocker")).get("fail_closed") is True
            ),
            "allowed_outcome_kinds": _OBLIGATION_ACTUATOR_ALLOWED_OUTCOMES,
            "authority": "med_autoscience.paper_progress_policy_adapter",
            "authority_boundary": dict(ACTUATOR_AUTHORITY_BOUNDARY),
            "consume_only_readback_boundary": _consume_only_readback_boundary(),
        }
    return owner_callable_actions


def _recovery_requires_obligation_actuator(recovery: Mapping[str, Any]) -> bool:
    if not recovery:
        return False
    if _non_empty_text(recovery.get("surface_kind")) != "paper_recovery_state":
        return False
    next_action = _mapping(recovery.get("next_safe_action"))
    obligation = _mapping(_mapping(recovery.get("current_authority")).get("obligation"))
    if not next_action and not _non_empty_text(recovery.get("recovery_obligation_id")) and not obligation:
        return False
    supervisor_decision = _mapping(recovery.get("supervisor_decision"))
    decision = _non_empty_text(supervisor_decision.get("decision"))
    if decision not in {
        None,
        "materialize_recovery_action",
        "execute_current_owner_delta",
        "stop_with_stable_typed_blocker",
        "stop_with_owner_receipt",
    }:
        return False
    phase = _non_empty_text(recovery.get("phase"))
    next_kind = _non_empty_text(next_action.get("kind"))
    return phase in {
        "owner_action_ready",
        "owner_receipt_recorded",
        "admission_pending",
        "attempt_running",
        "domain_blocked",
        "admission_blocked",
        "human_gate",
    } or next_kind in {
        "run_mas_owner_callable",
        "materialize_mas_transition_request_or_owner_callable",
        "materialize_successor_owner_action",
        "materialize_successor_owner_gate",
        "admit_provider_attempt",
        "admit_identity_bound_stage_packet",
        "resolve_owner_gate_decision",
        "route_back_to_owner_or_repair_materialization",
        "resolve_typed_blocker",
        "consume_owner_receipt",
        "honor_stable_typed_blocker",
        "publish_stable_blocker_and_stop_same_identity_redrive",
        "authorize_opl_transport_recovery_or_stable_typed_blocker",
    }


def _owner_callable_actions_by_study(value: object) -> dict[str, list[dict[str, Any]]]:
    by_study: dict[str, list[dict[str, Any]]] = {}
    for item in value or []:
        if not isinstance(item, Mapping):
            continue
        study_id = _non_empty_text(item.get("study_id"))
        if study_id is None:
            continue
        by_study.setdefault(study_id, []).append(dict(item))
    return by_study


def _closed_obligation_outcome(
    *,
    action: Mapping[str, Any],
    current_control_state: Mapping[str, Any],
    owner_callable_actions: list[dict[str, Any]],
    profile: WorkspaceProfile,
    fail_closed: bool,
    phase: str,
) -> dict[str, Any] | None:
    for owner_callable_action in reversed(owner_callable_actions):
        outcome = _owner_callable_action_outcome(
            action=action,
            owner_callable_action=owner_callable_action,
            phase=phase,
        )
        if outcome is not None:
            return outcome
    owner_receipt = _owner_receipt_outcome(action=action, phase=phase)
    if owner_receipt is not None:
        return owner_receipt
    running = _running_provider_attempt_outcome(
        action=action,
        current_control_state=current_control_state,
        phase=phase,
    )
    if running is not None:
        return running
    pending = _provider_admission_or_transition_request_outcome(
        action=action,
        current_control_state=current_control_state,
        phase=phase,
    )
    if pending is not None:
        return pending
    typed_blocker = _typed_blocker_outcome(action=action, phase=phase)
    if typed_blocker is not None:
        return typed_blocker
    route_back = _route_back_evidence_outcome(action=action, phase=phase)
    if route_back is not None:
        return route_back
    human_gate = _human_gate_outcome(action=action, phase=phase)
    if human_gate is not None:
        return human_gate
    if not fail_closed:
        return None
    return _fail_closed_obligation_outcome(
        action=action,
        profile=profile,
        blocker_type="non_advancing_apply",
        reason=(
            "DHD apply reached command end without provider admission, running proof, "
            "owner receipt, typed blocker, human gate, or route-back evidence for the "
            "current paper recovery obligation."
        ),
        phase=phase,
    )


def _owner_callable_action_outcome(
    *,
    action: Mapping[str, Any],
    owner_callable_action: Mapping[str, Any],
    phase: str,
) -> dict[str, Any] | None:
    if owner_callable_action.get("ok") is not True:
        return None
    record_path = _non_empty_text(owner_callable_action.get("record_path"))
    if record_path is None:
        return None
    if not _owner_callable_action_matches_obligation(
        action=action,
        owner_callable_action=owner_callable_action,
    ):
        return None
    return _obligation_outcome(
        action=action,
        outcome_kind="owner_receipt_ref",
        outcome_ref=record_path,
        phase=phase,
        details={
            "callable_surface": _non_empty_text(owner_callable_action.get("callable_surface")),
            "action_type": _non_empty_text(owner_callable_action.get("action_type")),
            "status": _non_empty_text(owner_callable_action.get("status")),
        },
    )


def _owner_callable_action_matches_obligation(
    *,
    action: Mapping[str, Any],
    owner_callable_action: Mapping[str, Any],
) -> bool:
    action_type = _non_empty_text(owner_callable_action.get("action_type"))
    if action_type is None:
        return False
    expected_action_types = _action_obligation_action_types(action)
    if expected_action_types and action_type not in expected_action_types:
        return False
    action_fingerprint = _non_empty_text(owner_callable_action.get("work_unit_fingerprint"))
    expected_fingerprints = _action_obligation_fingerprints(action)
    return not (action_fingerprint and expected_fingerprints and action_fingerprint not in expected_fingerprints)


def _action_obligation_action_types(action: Mapping[str, Any]) -> set[str]:
    recovery = _mapping(action.get("paper_recovery_state"))
    next_action = _mapping(recovery.get("next_safe_action"))
    owner_callable = _mapping(next_action.get("owner_callable"))
    candidates = (
        _action_recovery_obligation(action).get("action_type"),
        owner_callable.get("action_type"),
        next_action.get("action_type"),
        _mapping(action.get("current_executable_owner_action")).get("action_type"),
        _mapping(action.get("current_work_unit")).get("action_type"),
    )
    return {text for value in candidates if (text := _non_empty_text(value)) is not None}


def _owner_receipt_outcome(
    *,
    action: Mapping[str, Any],
    phase: str,
) -> dict[str, Any] | None:
    recovery = _mapping(action.get("paper_recovery_state"))
    next_action = _mapping(recovery.get("next_safe_action"))
    if _non_empty_text(next_action.get("kind")) == "consume_owner_receipt":
        return None
    owner_receipt_ref = _first_text(
        next_action.get("owner_receipt_ref"),
        recovery.get("owner_receipt_ref"),
        *_matching_ref_items(recovery.get("evidence_refs"), prefix="owner_receipt:"),
    )
    if owner_receipt_ref is None:
        return None
    return _obligation_outcome(
        action=action,
        outcome_kind="owner_receipt_ref",
        outcome_ref=owner_receipt_ref,
        phase=phase,
        details={"next_safe_action_kind": _non_empty_text(next_action.get("kind"))},
    )


def _running_provider_attempt_outcome(
    *,
    action: Mapping[str, Any],
    current_control_state: Mapping[str, Any],
    phase: str,
) -> dict[str, Any] | None:
    study_id = _non_empty_text(action.get("study_id"))
    study = _current_control_study(current_control_state, study_id=study_id)
    for proof in _strict_opl_running_provider_attempts(action, study):
        if not running_attempt_matches_current_action(
            running_attempt=proof,
            action=_running_attempt_expected_action(action),
        ):
            continue
        return _obligation_outcome(
            action=action,
            outcome_kind="running_provider_attempt",
            outcome_ref=_first_text(
                proof.get("active_stage_attempt_id"),
                proof.get("active_run_id"),
                proof.get("active_workflow_id"),
                _mapping(proof.get("running_attempt")).get("stage_attempt_id"),
            )
            or f"running_provider_attempt:{study_id or 'unknown-study'}",
            phase=phase,
            details={
                "opl_running_provider_attempt": proof,
                "current_control_study": study,
            },
        )
    return None


def _provider_admission_or_transition_request_outcome(
    *,
    action: Mapping[str, Any],
    current_control_state: Mapping[str, Any],
    phase: str,
) -> dict[str, Any] | None:
    candidates = _current_obligation_provider_admission_candidates(
        action=action,
        current_control_state=current_control_state,
    )
    if not candidates:
        return None
    runtime_result = candidate_opl_transition_readback(candidates[0])
    if runtime_result:
        return _obligation_outcome(
            action=action,
            outcome_kind="provider_admission_pending",
            outcome_ref=_provider_admission_outcome_ref(
                candidate=candidates[0],
                action=action,
            ),
            phase=phase,
            details={
                "provider_admission_candidates": candidates,
                "opl_runtime_result": _normalized_opl_runtime_readback(runtime_result),
            },
        )
    blocker = _typed_control_blocker_payload(
        action=action,
        blocker_type="opl_transition_readback_required",
        reason=(
            "MAS materialized a DomainProgressTransitionRuntime request, but OPL has "
            "not returned a transition event, outbox, or StageRun readback for the "
            "current paper recovery obligation."
        ),
        phase=phase,
    )
    return _obligation_outcome(
        action=action,
        outcome_kind="transition_request_pending",
        outcome_ref=_transition_request_outcome_ref(candidate=candidates[0], action=action),
        phase=phase,
        details={
            "provider_admission_candidates": candidates,
            "required_opl_runtime_result": True,
            "opl_transition_request": _mapping(
                blocker.get("opl_domain_progress_transition_request")
            ),
            "typed_control_blocker": blocker,
        },
        typed_control_blocker=blocker,
        postcondition_ok=False,
    )


def _current_obligation_provider_admission_candidates(
    *,
    action: Mapping[str, Any],
    current_control_state: Mapping[str, Any],
) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    current_control_study = _current_control_study(
        current_control_state,
        study_id=_non_empty_text(action.get("study_id")),
    )
    for source in (
        action.get("provider_admission_candidates"),
        action.get("transition_request_candidates"),
        current_control_state.get("provider_admission_candidates"),
        current_control_state.get("transition_request_candidates"),
        current_control_study.get("provider_admission_candidates"),
        current_control_study.get("transition_request_candidates"),
    ):
        for candidate in source or []:
            if (
                isinstance(candidate, Mapping)
                and _candidate_matches_action_obligation(candidate, action)
                and _candidate_has_mas_transition_request(candidate)
            ):
                candidate_payload = dict(candidate)
                if candidate_payload not in candidates:
                    candidates.append(candidate_payload)
    return candidates


def _route_back_evidence_outcome(
    *,
    action: Mapping[str, Any],
    phase: str,
) -> dict[str, Any] | None:
    recovery = _mapping(action.get("paper_recovery_state"))
    next_action = _mapping(recovery.get("next_safe_action"))
    accepted_owner_gate = _mapping(next_action.get("accepted_owner_gate_decision"))
    route_back_ref, ref_source = _first_text_with_source(
        ("next_safe_action", next_action.get("route_back_evidence_ref")),
        ("accepted_owner_gate_decision", accepted_owner_gate.get("route_back_evidence_ref")),
        *(
            ("paper_recovery_state.evidence_refs", ref)
            for ref in _matching_ref_items(recovery.get("evidence_refs"), prefix="route_back:")
        ),
    )
    if route_back_ref is None:
        return None
    details = {
        "next_safe_action_kind": _non_empty_text(next_action.get("kind")),
        "domain_authority_ref_source": ref_source,
    }
    if ref_source == "accepted_owner_gate_decision":
        details.update(
            _owner_gate_decision_authority_details(
                accepted_owner_gate=accepted_owner_gate,
                accepted_ref=route_back_ref,
                accepted_shape="route_back_evidence_ref",
            )
        )
    return _obligation_outcome(
        action=action,
        outcome_kind="route_back_evidence_ref",
        outcome_ref=route_back_ref,
        phase=phase,
        details=details,
    )


def _human_gate_outcome(
    *,
    action: Mapping[str, Any],
    phase: str,
) -> dict[str, Any] | None:
    recovery = _mapping(action.get("paper_recovery_state"))
    supervisor_decision = _mapping(recovery.get("supervisor_decision"))
    supervisor_next = _mapping(supervisor_decision.get("next_safe_action"))
    next_action = _mapping(recovery.get("next_safe_action"))
    accepted_owner_gate = _mapping(next_action.get("accepted_owner_gate_decision"))
    human_gate_ref, ref_source = _first_text_with_source(
        ("next_safe_action", next_action.get("human_gate_ref")),
        ("supervisor_decision.next_safe_action", supervisor_next.get("human_gate_ref")),
        ("accepted_owner_gate_decision", accepted_owner_gate.get("human_gate_ref")),
        *(
            ("paper_recovery_state.evidence_refs", ref)
            for ref in _matching_ref_items(recovery.get("evidence_refs"), prefix="human_gate:")
        ),
    )
    if human_gate_ref is None:
        return None
    details = {
        "next_safe_action_kind": _non_empty_text(next_action.get("kind")),
        "domain_authority_ref_source": ref_source,
    }
    if ref_source == "accepted_owner_gate_decision":
        details.update(
            _owner_gate_decision_authority_details(
                accepted_owner_gate=accepted_owner_gate,
                accepted_ref=human_gate_ref,
                accepted_shape="human_gate_ref",
            )
        )
    return _obligation_outcome(
        action=action,
        outcome_kind="human_gate_ref",
        outcome_ref=human_gate_ref,
        phase=phase,
        details=details,
    )


def _typed_blocker_outcome(
    *,
    action: Mapping[str, Any],
    phase: str,
) -> dict[str, Any] | None:
    typed_blocker = _current_typed_blocker_payload(action)
    typed_blocker_ref, ref_source = _first_text_with_source(
        ("typed_blocker.typed_blocker_ref", typed_blocker.get("typed_blocker_ref")),
        ("typed_blocker.latest_owner_answer_ref", typed_blocker.get("latest_owner_answer_ref")),
        ("typed_blocker.source_ref", typed_blocker.get("source_ref")),
        *(
            ("paper_recovery_state.evidence_refs", ref)
            for ref in _matching_ref_items(
                _mapping(action.get("paper_recovery_state")).get("evidence_refs"),
                prefix="typed_blocker:",
            )
        ),
    )
    if typed_blocker_ref is None:
        return None
    details = {
        "blocker_type": _first_text(
            typed_blocker.get("blocker_type"),
            typed_blocker.get("blocked_reason"),
        ),
        "domain_authority_ref_source": ref_source,
    }
    if ref_source != "paper_recovery_state.evidence_refs" and typed_blocker:
        details.update(
            _typed_blocker_authority_details(
                typed_blocker=typed_blocker,
                typed_blocker_ref=typed_blocker_ref,
            )
        )
    return _obligation_outcome(
        action=action,
        outcome_kind="typed_blocker_ref",
        outcome_ref=typed_blocker_ref,
        phase=phase,
        details=details,
    )


def _fail_closed_obligation_outcome(
    *,
    action: Mapping[str, Any],
    profile: WorkspaceProfile,
    blocker_type: str,
    reason: str,
    phase: str,
) -> dict[str, Any]:
    study_id = _non_empty_text(action.get("study_id")) or "unknown-study"
    study_root = _study_root_for_obligation_outcome(action=action, profile=profile, study_id=study_id)
    payload = _typed_control_blocker_payload(
        action=action,
        blocker_type=blocker_type,
        reason=reason,
        phase=phase,
    )
    authority_result = (
        mas_domain_typed_blocker_authority_result.persist_obligation_typed_blocker(
            study_root=study_root,
            payload=payload,
        )
    )
    typed_blocker_ref = _non_empty_text(authority_result.get("typed_blocker_ref"))
    typed_blocker_payload = _mapping(authority_result.get("payload")) or payload
    authority_result_boundary = _mapping(authority_result.get("authority_boundary"))
    return _obligation_outcome(
        action=action,
        outcome_kind="typed_blocker_ref",
        outcome_ref=typed_blocker_ref,
        phase=phase,
        details={
            "typed_control_blocker": typed_blocker_payload,
            "authority_result_adapter": authority_result.get("surface_kind"),
            "authority_result_ref": typed_blocker_ref,
            "authority_result_boundary": authority_result_boundary,
            "authority_result_history_ref": authority_result.get("history_ref"),
        },
        typed_control_blocker={
            **typed_blocker_payload,
            "typed_blocker_ref": typed_blocker_ref,
            "authority_result_ref": typed_blocker_ref,
            "authority_result_adapter": authority_result.get("surface_kind"),
            "authority_result_boundary": authority_result_boundary,
        },
        postcondition_ok=False,
    )


def _typed_control_blocker_payload(
    *,
    action: Mapping[str, Any],
    blocker_type: str,
    reason: str,
    phase: str,
) -> dict[str, Any]:
    obligation = _action_recovery_obligation(action)
    next_action = _mapping(_mapping(action.get("paper_recovery_state")).get("next_safe_action"))
    policy_result = paper_progress_policy_adapter.build_non_advancing_policy_blocker(
        {
            "study_id": _non_empty_text(action.get("study_id")) or _non_empty_text(obligation.get("study_id")),
            "quest_id": _non_empty_text(action.get("quest_id")) or _non_empty_text(obligation.get("quest_id")),
            "current_work_unit": _mapping(action.get("current_work_unit")),
            "current_executable_owner_action": _mapping(action.get("current_executable_owner_action")),
            "paper_recovery_state": _mapping(action.get("paper_recovery_state")),
        },
        reason=reason,
    )
    payload = {
        "surface_kind": "mas_domain_typed_blocker",
        "schema_version": 1,
        "status": "typed_blocker",
        "fail_closed": True,
        "blocker_type": blocker_type,
        "reason": reason,
        "source": "domain_health_diagnostic.obligation_readback_projection",
        "source_projection_surface": "domain_health_diagnostic_obligation_readback_projection",
        "owner_answer_shape": "typed_blocker_ref",
        "mas_authority_result_shape": "typed_blocker_ref",
        "private_actuator_surface_retired": True,
        "actuator_private_write_authority": False,
        "actuator_phase": phase,
        "study_id": _non_empty_text(action.get("study_id")) or _non_empty_text(obligation.get("study_id")),
        "quest_id": _non_empty_text(action.get("quest_id")) or _non_empty_text(obligation.get("quest_id")),
        "owner": _first_text(
            obligation.get("owner"),
            next_action.get("owner"),
            _mapping(action.get("current_executable_owner_action")).get("next_owner"),
            _mapping(action.get("current_work_unit")).get("owner"),
            "MedAutoScience",
        ),
        "action_type": _first_text(
            obligation.get("action_type"),
            next_action.get("action_type"),
            _mapping(action.get("current_executable_owner_action")).get("action_type"),
            _mapping(action.get("current_work_unit")).get("action_type"),
        ),
        "work_unit_id": _first_text(
            obligation.get("work_unit_id"),
            next_action.get("work_unit_id"),
            _mapping(action.get("current_executable_owner_action")).get("work_unit_id"),
            _mapping(action.get("current_work_unit")).get("work_unit_id"),
        ),
        "work_unit_fingerprint": _action_obligation_fingerprint(action),
        "next_safe_action_kind": _non_empty_text(next_action.get("kind")),
        "required_outcome_kinds": list(_OBLIGATION_ACTUATOR_ALLOWED_OUTCOMES),
        "paper_package_mutation_allowed": False,
        "publication_ready_claim_allowed": False,
        "provider_completion_is_domain_completion": False,
        "non_advancing_apply": blocker_type in {
            "non_advancing_apply",
            "opl_transition_readback_required",
        },
        "paper_progress_policy_result": policy_result,
        "opl_domain_progress_transition_request": _mapping(
            policy_result.get("opl_domain_progress_transition_request")
        ),
        "non_advancing_apply_requirement": {
            "runtime_owner": OPL_TRANSITION_RUNTIME_OWNER,
            "runtime_kind": OPL_TRANSITION_RUNTIME_KIND,
            "mas_can_apply_non_advancing_transition": False,
            "mas_can_persist_opl_event_or_outbox": False,
            "required_outcome": "typed_blocker_ref",
        },
        "authority_boundary": dict(ACTUATOR_AUTHORITY_BOUNDARY),
        "consume_only_readback_boundary": _consume_only_readback_boundary(),
    }
    cleaned = {key: value for key, value in payload.items() if value not in (None, "", [], {})}
    cleaned["typed_blocker_id"] = "dhd-obligation-blocker:" + hashlib.sha256(
        json.dumps(cleaned, ensure_ascii=True, sort_keys=True).encode("utf-8")
    ).hexdigest()[:24]
    return cleaned


def _existing_closed_outcome_for_action(
    *,
    action: Mapping[str, Any],
    outcomes: list[dict[str, Any]],
) -> dict[str, Any] | None:
    study_id = _non_empty_text(action.get("study_id"))
    if study_id is None:
        return None
    recovery = _mapping(action.get("paper_recovery_state"))
    recovery_obligation_id = _non_empty_text(recovery.get("recovery_obligation_id"))
    next_kind = _non_empty_text(_mapping(recovery.get("next_safe_action")).get("kind"))
    action_type = _action_obligation_action_type(action)
    work_unit_id = _action_obligation_work_unit_id(action)
    work_unit_fingerprint = _action_obligation_fingerprint(action)
    identity_incomplete = _action_obligation_identity_incomplete(
        action_type=action_type,
        work_unit_id=work_unit_id,
        work_unit_fingerprint=work_unit_fingerprint,
    )
    for outcome in reversed(outcomes):
        if outcome.get("postcondition_ok") is not True:
            continue
        if _non_empty_text(outcome.get("study_id")) != study_id:
            continue
        if (
            next_kind == "consume_owner_receipt"
            and _non_empty_text(outcome.get("outcome_kind")) == "owner_receipt_ref"
        ):
            continue
        if recovery_obligation_id is not None:
            if _non_empty_text(outcome.get("recovery_obligation_id")) == recovery_obligation_id:
                return outcome
            if not identity_incomplete:
                continue
        if (
            _non_empty_text(outcome.get("action_type")) == action_type
            and _non_empty_text(outcome.get("work_unit_id")) == work_unit_id
            and _non_empty_text(outcome.get("work_unit_fingerprint")) == work_unit_fingerprint
            and _non_empty_text(outcome.get("paper_recovery_next_safe_action_kind")) == next_kind
        ):
            return outcome
        if identity_incomplete:
            return outcome
    return None


def _action_obligation_identity_incomplete(
    *,
    action_type: str | None,
    work_unit_id: str | None,
    work_unit_fingerprint: str | None,
) -> bool:
    return (
        action_type in {None, "unknown-action"}
        or work_unit_id in {None, "unknown-work-unit", "current_work_unit_unresolved"}
        or work_unit_fingerprint in {None, "current_work_unit_unresolved"}
    )


def _action_obligation_action_type(action: Mapping[str, Any]) -> str | None:
    obligation = _action_recovery_obligation(action)
    return _first_text(
        obligation.get("action_type"),
        _mapping(action.get("current_executable_owner_action")).get("action_type"),
        _mapping(action.get("current_work_unit")).get("action_type"),
    )


def _action_obligation_work_unit_id(action: Mapping[str, Any]) -> str | None:
    obligation = _action_recovery_obligation(action)
    return _first_text(
        obligation.get("work_unit_id"),
        _mapping(action.get("current_executable_owner_action")).get("work_unit_id"),
        _mapping(action.get("current_work_unit")).get("work_unit_id"),
    )


def _obligation_outcome(
    *,
    action: Mapping[str, Any],
    outcome_kind: str,
    outcome_ref: object,
    phase: str,
    details: Mapping[str, Any] | None = None,
    typed_control_blocker: Mapping[str, Any] | None = None,
    postcondition_ok: bool = True,
) -> dict[str, Any]:
    decision = _action_supervisor_decision(action)
    decision_kind = _non_empty_text(decision.get("decision"))
    obligation = _supervisor_obligation(action=action, supervisor_decision=decision)
    obligation_ref = _paper_autonomy_obligation_ref(
        action=action,
        supervisor_decision=decision,
        obligation=obligation,
    )
    obligation_identity = _paper_autonomy_obligation_identity(action=action, obligation=obligation)
    allowed_decision_outcomes = allowed_outcomes_for_policy_label(decision_kind)
    outcome_allowed = outcome_kind in allowed_decision_outcomes
    source_family = outcome_source_family(outcome_kind)
    opl_foundation = opl_foundation_readback_boundary(source_family=source_family)
    outcome_ref_text = _non_empty_text(outcome_ref)
    consumed_readback_identity = _consumed_obligation_readback_identity(
        source_family=source_family,
        outcome_kind=outcome_kind,
        outcome_ref=outcome_ref_text,
        details=_mapping(details),
    )
    success_proof = _dhd_apply_success_proof(
        outcome_kind=outcome_kind,
        source_family=source_family,
        opl_foundation=opl_foundation,
        consumed_readback_identity=consumed_readback_identity,
        outcome_allowed=outcome_allowed,
    )
    effective_postcondition_ok = (
        postcondition_ok
        and outcome_allowed
        and source_family != "mas_policy_request_projection"
        and bool(success_proof)
    )
    decision_id = _paper_autonomy_supervisor_decision_id(
        action=action,
        decision_kind=decision_kind,
        obligation_ref=obligation_ref,
    )
    payload = {
        "surface_kind": "managed_study_obligation_actuator_outcome",
        "schema_version": 1,
        "study_id": _non_empty_text(action.get("study_id")) or _non_empty_text(obligation.get("study_id")),
        "quest_id": _non_empty_text(action.get("quest_id")) or _non_empty_text(obligation.get("quest_id")),
        "phase": phase,
        "outcome_kind": outcome_kind,
        outcome_kind: outcome_ref,
        "exactly_one_outcome": True,
        "postcondition_ok": effective_postcondition_ok,
        "outcome_source_family": source_family,
        "opl_foundation_readback_boundary": opl_foundation,
        "dhd_apply_success_proof": success_proof if effective_postcondition_ok else None,
        "success_requires_opl_foundation_readback_boundary": True,
        "success_requires_consumed_readback_identity": True,
        "success_outcome_source_family": (
            source_family
            if effective_postcondition_ok
            and source_family in SUCCESS_OUTCOME_SOURCE_FAMILIES
            else None
        ),
        "consumed_obligation_readback_identity": (
            consumed_readback_identity if effective_postcondition_ok else None
        ),
        "request_projection_only": source_family == "mas_policy_request_projection",
        "paper_autonomy_supervisor_decision_id": decision_id,
        "paper_autonomy_supervisor_decision_kind": decision_kind,
        "paper_autonomy_supervisor_allowed_outcome_kinds": sorted(allowed_decision_outcomes),
        "paper_autonomy_supervisor_outcome_allowed": outcome_allowed,
        "paper_autonomy_obligation_ref": obligation_ref,
        "paper_autonomy_obligation_identity": obligation_identity,
        "authority_boundary": dict(ACTUATOR_AUTHORITY_BOUNDARY),
        "consume_only_readback_boundary": _consume_only_readback_boundary(),
        "paper_recovery_next_safe_action_kind": _non_empty_text(
            _mapping(_mapping(action.get("paper_recovery_state")).get("next_safe_action")).get("kind")
        ),
        "recovery_obligation_id": _non_empty_text(
            _mapping(action.get("paper_recovery_state")).get("recovery_obligation_id")
        )
        or _non_empty_text(obligation.get("recovery_obligation_id")),
        "action_type": _action_obligation_action_type(action),
        "work_unit_id": _action_obligation_work_unit_id(action),
        "work_unit_fingerprint": _action_obligation_fingerprint(action),
        "details": _clean_payload(_mapping(details)),
        "typed_control_blocker": _clean_payload(_mapping(typed_control_blocker)),
    }
    return _clean_payload(payload)


def _normalized_opl_runtime_readback(readback: Mapping[str, Any]) -> dict[str, Any]:
    result = dict(readback)
    identity = _mapping(result.get("identity"))
    causality = _mapping(result.get("causality"))
    latest = _mapping(result.get("latest_transaction_readback"))
    stage_run_identity = _mapping(identity.get("stage_run_identity"))
    refs = {
        "event_id": _first_text(
            result.get("event_id"),
            identity.get("latest_event_id"),
            identity.get("event_id"),
            causality.get("event_id"),
            latest.get("event_id"),
            latest.get("transition_event_id"),
        ),
        "outbox_item_id": _first_text(
            result.get("outbox_item_id"),
            identity.get("latest_outbox_item_id"),
            identity.get("outbox_item_id"),
            causality.get("outbox_item_id"),
            latest.get("outbox_item_id"),
        ),
        "transaction_id": _first_text(
            result.get("transaction_id"),
            identity.get("latest_transaction_id"),
            identity.get("transaction_id"),
            causality.get("transaction_id"),
            latest.get("transaction_id"),
        ),
        "stage_run_id": _first_text(
            result.get("stage_run_id"),
            stage_run_identity.get("stage_run_id"),
            stage_run_identity.get("stage_run_identity_ref"),
        ),
    }
    for key, value in refs.items():
        if value is not None and _non_empty_text(result.get(key)) is None:
            result[key] = value
    result["canonical_runtime_refs"] = refs
    return _clean_payload(result)


def _consumed_obligation_readback_identity(
    *,
    source_family: str,
    outcome_kind: str,
    outcome_ref: str | None,
    details: Mapping[str, Any],
) -> dict[str, Any]:
    identity: dict[str, Any] = {
        "surface_kind": CONSUMED_READBACK_IDENTITY_SURFACE,
        "source_family": source_family,
        "outcome_kind": outcome_kind,
        "outcome_ref": outcome_ref,
    }
    if source_family == "opl_runtime_readback":
        if outcome_kind == "provider_admission_pending":
            runtime_result = _mapping(details.get("opl_runtime_result"))
            runtime_refs = _mapping(runtime_result.get("canonical_runtime_refs"))
            identity.update(
                {
                    "runtime_owner": _first_text(
                        runtime_result.get("runtime_owner"),
                        OPL_TRANSITION_RUNTIME_OWNER,
                    ),
                    "runtime_kind": _first_text(
                        runtime_result.get("runtime_kind"),
                        OPL_TRANSITION_RUNTIME_KIND,
                    ),
                    "event_id": _first_text(
                        runtime_refs.get("event_id"),
                        runtime_result.get("event_id"),
                    ),
                    "outbox_item_id": _first_text(
                        runtime_refs.get("outbox_item_id"),
                        runtime_result.get("outbox_item_id"),
                    ),
                    "transaction_id": _first_text(
                        runtime_refs.get("transaction_id"),
                        runtime_result.get("transaction_id"),
                    ),
                    "stage_run_id": _first_text(
                        runtime_refs.get("stage_run_id"),
                        runtime_result.get("stage_run_id"),
                    ),
                }
            )
        elif outcome_kind == "running_provider_attempt":
            running = _mapping(details.get("opl_running_provider_attempt"))
            identity.update(
                {
                    "runtime_owner": _first_text(
                        running.get("runtime_owner"),
                        running.get("provider_attempt_owner"),
                        OPL_TRANSITION_RUNTIME_OWNER,
                    ),
                    "runtime_kind": _first_text(
                        running.get("runtime_kind"),
                        OPL_TRANSITION_RUNTIME_KIND,
                    ),
                    "stage_run_id": _first_text(
                        outcome_ref,
                        running.get("active_stage_attempt_id"),
                        running.get("active_run_id"),
                        running.get("active_workflow_id"),
                        _mapping(running.get("stage_run_identity")).get("stage_run_id"),
                    ),
                }
            )
    elif source_family == "mas_owner_answer_readback":
        identity["owner_answer_ref"] = outcome_ref
    elif source_family == "mas_domain_authority_readback":
        identity["domain_authority_ref"] = outcome_ref
        identity.update(_mas_domain_authority_readback_identity(details=details))
    return _clean_payload(identity)


def _mas_domain_authority_readback_identity(*, details: Mapping[str, Any]) -> dict[str, Any]:
    boundary = (
        _mapping(details.get("domain_authority_boundary"))
        or _mapping(details.get("authority_result_boundary"))
        or _mapping(_mapping(details.get("typed_control_blocker")).get("authority_result_boundary"))
    )
    return _clean_payload(
        {
            "domain_authority_ref_source": _non_empty_text(
                details.get("domain_authority_ref_source")
            ),
            "domain_authority_surface": _first_text(
                details.get("domain_authority_surface"),
                details.get("authority_result_surface"),
                boundary.get("authority_result_surface"),
            ),
            "authority_result_ref": _first_text(
                details.get("authority_result_ref"),
                details.get("domain_authority_ref"),
            ),
            "authority_result_surface": _first_text(
                details.get("authority_result_surface"),
                boundary.get("authority_result_surface"),
            ),
            "accepted_answer_shape": _non_empty_text(details.get("accepted_answer_shape")),
            "domain_authority_boundary": boundary,
        }
    )


def _consume_only_readback_boundary() -> dict[str, Any]:
    return consume_only_readback_boundary()


def _dhd_apply_success_proof(
    *,
    outcome_kind: str,
    source_family: str,
    opl_foundation: Mapping[str, Any],
    consumed_readback_identity: Mapping[str, Any],
    outcome_allowed: bool,
) -> dict[str, Any]:
    if not outcome_allowed:
        return {}
    if not outcome_has_required_foundation_readback(
        source_family=source_family,
        opl_foundation=opl_foundation,
    ):
        return {}
    if not outcome_has_required_consumed_readback_identity(
        source_family=source_family,
        outcome_kind=outcome_kind,
        consumed_readback_identity=consumed_readback_identity,
    ):
        return {}
    consume_only = _consume_only_readback_boundary()
    return _clean_payload(
        {
            "surface_kind": "dhd_apply_success_proof",
            "success_outcome_source_family": source_family,
            "opl_foundation_readback_boundary": dict(opl_foundation),
            "consumed_obligation_readback_identity": dict(consumed_readback_identity),
            "consume_only_readback_boundary": consume_only,
            "request_projection_only": False,
            "request_projection_is_success_outcome": consume_only.get(
                "request_projection_is_success_outcome"
            ),
            "supervisor_disallowed_outcome_is_success": consume_only.get(
                "supervisor_disallowed_outcome_is_success"
            ),
            "mas_can_store_recovery_obligation": consume_only.get(
                "mas_can_store_recovery_obligation"
            ),
            "mas_can_run_supervisor_decision_engine": consume_only.get(
                "mas_can_run_supervisor_decision_engine"
            ),
            "mas_can_run_fixed_point_runtime": consume_only.get(
                "mas_can_run_fixed_point_runtime"
            ),
            "mas_can_replay_obligation": consume_only.get("mas_can_replay_obligation"),
        }
    )


def _action_supervisor_decision(action: Mapping[str, Any]) -> dict[str, Any]:
    recovery = _mapping(action.get("paper_recovery_state"))
    for candidate in (
        recovery.get("paper_autonomy_supervisor_decision"),
        recovery.get("supervisor_decision"),
        action.get("paper_autonomy_supervisor_decision"),
        action.get("supervisor_decision"),
    ):
        decision = _mapping(candidate)
        if decision:
            return decision
    return {}


def _supervisor_obligation(
    *,
    action: Mapping[str, Any],
    supervisor_decision: Mapping[str, Any],
) -> dict[str, Any]:
    obligation = _mapping(supervisor_decision.get("paper_autonomy_obligation"))
    if obligation:
        return obligation
    return _action_recovery_obligation(action)


def _paper_autonomy_obligation_ref(
    *,
    action: Mapping[str, Any],
    supervisor_decision: Mapping[str, Any],
    obligation: Mapping[str, Any],
) -> str:
    recovery = _mapping(action.get("paper_recovery_state"))
    return _first_text(
        supervisor_decision.get("paper_autonomy_obligation_ref"),
        obligation.get("paper_autonomy_obligation_id"),
        obligation.get("recovery_obligation_id"),
        recovery.get("recovery_obligation_id"),
        _action_obligation_fingerprint(action),
        _non_empty_text(action.get("study_id")),
        "unknown-obligation",
    ) or "unknown-obligation"


def _paper_autonomy_supervisor_decision_id(
    *,
    action: Mapping[str, Any],
    decision_kind: str | None,
    obligation_ref: str,
) -> str:
    decision = _action_supervisor_decision(action)
    explicit = _non_empty_text(decision.get("decision_id"))
    if explicit is not None:
        return explicit
    return "::".join(
        (
            "supervisor-decision",
            decision_kind or "unknown-decision",
            obligation_ref,
        )
    )


def _paper_autonomy_obligation_identity(
    *,
    action: Mapping[str, Any],
    obligation: Mapping[str, Any],
) -> dict[str, Any]:
    current_action = _mapping(action.get("current_executable_owner_action"))
    current_work_unit = _mapping(action.get("current_work_unit"))
    return _clean_payload(
        {
            "study_id": _first_text(
                obligation.get("study_id"),
                action.get("study_id"),
                current_work_unit.get("study_id"),
            ),
            "quest_id": _first_text(
                obligation.get("quest_id"),
                action.get("quest_id"),
                current_work_unit.get("quest_id"),
            ),
            "stage_id": _first_text(obligation.get("stage_id"), current_work_unit.get("stage_id")),
            "action_type": _first_text(
                obligation.get("action_type"),
                current_action.get("action_type"),
                current_work_unit.get("action_type"),
            ),
            "work_unit_id": _first_text(
                obligation.get("work_unit_id"),
                current_action.get("work_unit_id"),
                current_work_unit.get("work_unit_id"),
            ),
            "work_unit_fingerprint": _first_text(
                obligation.get("work_unit_fingerprint"),
                _action_obligation_fingerprint(action),
            ),
            "route_identity_key": _first_text(
                obligation.get("route_identity_key"),
                current_work_unit.get("route_identity_key"),
            ),
            "attempt_idempotency_key": _first_text(
                obligation.get("attempt_idempotency_key"),
                current_work_unit.get("attempt_idempotency_key"),
                current_work_unit.get("idempotency_key"),
            ),
        }
    )


def _obligation_outcome_ref(outcome: Mapping[str, Any]) -> str | None:
    outcome_kind = _non_empty_text(outcome.get("outcome_kind"))
    if outcome_kind is None:
        return None
    value = outcome.get(outcome_kind)
    if isinstance(value, Mapping):
        return _first_text(value.get("rejected_ref"), value.get("ref"), value.get("path"))
    return _non_empty_text(value)


def _postcondition_from_outcome(outcome: Mapping[str, Any]) -> dict[str, Any]:
    outcome_kind = _non_empty_text(outcome.get("outcome_kind"))
    success_proof = _clean_payload(_mapping(outcome.get("dhd_apply_success_proof")))
    return {
        "surface_kind": "dhd_apply_obligation_postcondition",
        "schema_version": 1,
        "ok": bool(outcome.get("postcondition_ok")) is True,
        "exactly_one_outcome": outcome.get("exactly_one_outcome") is True,
        "outcome_kind": outcome_kind,
        "outcome_ref": _obligation_outcome_ref(outcome) if outcome_kind else None,
        "allowed_outcome_kinds": list(_OBLIGATION_ACTUATOR_ALLOWED_OUTCOMES),
        "paper_autonomy_supervisor_decision_id": _non_empty_text(
            outcome.get("paper_autonomy_supervisor_decision_id")
        ),
        "paper_autonomy_supervisor_decision_kind": _non_empty_text(
            outcome.get("paper_autonomy_supervisor_decision_kind")
        ),
        "paper_autonomy_supervisor_outcome_allowed": outcome.get(
            "paper_autonomy_supervisor_outcome_allowed"
        )
        is True,
        "outcome_source_family": _non_empty_text(outcome.get("outcome_source_family")),
        "opl_foundation_readback_boundary": _clean_payload(
            _mapping(outcome.get("opl_foundation_readback_boundary"))
        ),
        "success_requires_opl_foundation_readback_boundary": (
            outcome.get("success_requires_opl_foundation_readback_boundary") is True
        ),
        "success_requires_consumed_readback_identity": (
            outcome.get("success_requires_consumed_readback_identity") is True
        ),
        "success_outcome_source_family": _non_empty_text(
            outcome.get("success_outcome_source_family")
        ),
        "consumed_obligation_readback_identity": _clean_payload(
            _mapping(outcome.get("consumed_obligation_readback_identity"))
        ),
        "dhd_apply_success_proof": success_proof,
        "request_projection_only": outcome.get("request_projection_only") is True,
        "paper_autonomy_obligation_ref": _non_empty_text(
            outcome.get("paper_autonomy_obligation_ref")
        ),
        "paper_autonomy_obligation_identity": _clean_payload(
            _mapping(outcome.get("paper_autonomy_obligation_identity"))
        ),
        "authority_boundary": dict(ACTUATOR_AUTHORITY_BOUNDARY),
        "consume_only_readback_boundary": _consume_only_readback_boundary(),
    }


def _obligation_actuator_outcome_key(outcome: Mapping[str, Any]) -> tuple[str, str, str, str] | None:
    study_id = _non_empty_text(outcome.get("study_id"))
    outcome_kind = _non_empty_text(outcome.get("outcome_kind"))
    if study_id is None or outcome_kind is None:
        return None
    return (
        study_id,
        _non_empty_text(outcome.get("recovery_obligation_id")) or "",
        outcome_kind,
        _obligation_outcome_ref(outcome) or "",
    )


def _first_text(*values: object) -> str | None:
    for value in values:
        text = _non_empty_text(value)
        if text is not None:
            return text
    return None


def _first_text_with_source(*values: tuple[str, object]) -> tuple[str | None, str | None]:
    for source, value in values:
        text = _non_empty_text(value)
        if text is not None:
            return text, source
    return None, None


def _matching_ref_items(value: object, *, prefix: str) -> list[str]:
    values = value if isinstance(value, list | tuple | set) else [value]
    return [
        text
        for item in values
        if (text := _non_empty_text(item)) is not None and text.startswith(prefix)
    ]


def _typed_blocker_authority_details(
    *,
    typed_blocker: Mapping[str, Any],
    typed_blocker_ref: str,
) -> dict[str, Any]:
    boundary = _mapping(typed_blocker.get("authority_result_boundary")) or {
        "surface_kind": "mas_domain_typed_blocker_authority_boundary",
        "authority_owner": _first_text(typed_blocker.get("authority_owner"), "med-autoscience"),
        "authority_result_surface": "mas_domain_typed_blocker",
        "adapter_role": "consume_existing_mas_domain_typed_blocker_result",
        "actuator_private_write_authority": False,
        "can_create_opl_command": False,
        "can_create_opl_event": False,
        "can_create_opl_outbox": False,
        "can_create_opl_stage_run": False,
        "can_store_recovery_obligation": False,
        "can_run_supervisor_decision_engine": False,
        "can_authorize_provider_admission": False,
        "can_claim_paper_progress": False,
        "can_write_publication_eval": False,
        "can_write_controller_decision": False,
    }
    return {
        "domain_authority_surface": "mas_domain_typed_blocker",
        "domain_authority_ref": typed_blocker_ref,
        "authority_result_ref": _first_text(
            typed_blocker.get("authority_result_ref"),
            typed_blocker_ref,
        ),
        "authority_result_surface": _first_text(
            typed_blocker.get("authority_result_surface"),
            "mas_domain_typed_blocker",
        ),
        "accepted_answer_shape": "typed_blocker_ref",
        "domain_authority_boundary": boundary,
        "authority_result_boundary": boundary,
    }


def _owner_gate_decision_authority_details(
    *,
    accepted_owner_gate: Mapping[str, Any],
    accepted_ref: str,
    accepted_shape: str,
) -> dict[str, Any]:
    boundary = {
        "surface_kind": "mas_owner_gate_decision_authority_boundary",
        "authority_owner": "med-autoscience",
        "authority_result_surface": "owner_gate_decision",
        "adapter_role": "consume_accepted_owner_gate_decision_result",
        "accepted_answer_shape": accepted_shape,
        "actuator_private_write_authority": False,
        "can_create_opl_command": False,
        "can_create_opl_event": False,
        "can_create_opl_outbox": False,
        "can_create_opl_stage_run": False,
        "can_store_recovery_obligation": False,
        "can_run_supervisor_decision_engine": False,
        "can_generate_human_gate_resume_token": False,
        "can_authorize_provider_admission": False,
        "can_claim_paper_progress": False,
        "can_write_publication_eval": False,
        "can_write_controller_decision": False,
    }
    return {
        "domain_authority_surface": "owner_gate_decision",
        "domain_authority_ref": accepted_ref,
        "authority_result_ref": _first_text(
            accepted_owner_gate.get("owner_gate_decision_ref"),
            accepted_ref,
        ),
        "authority_result_surface": "owner_gate_decision",
        "accepted_answer_shape": accepted_shape,
        "accepted_owner_gate_decision": dict(accepted_owner_gate),
        "domain_authority_boundary": boundary,
    }


def _current_control_study(
    current_control_state: Mapping[str, Any],
    *,
    study_id: str | None,
) -> dict[str, Any]:
    if study_id is None:
        return {}
    if _non_empty_text(current_control_state.get("study_id")) == study_id:
        return dict(current_control_state)
    for study in current_control_state.get("studies") or []:
        if isinstance(study, Mapping) and _non_empty_text(study.get("study_id")) == study_id:
            return dict(study)
    return {}


def _action_has_running_provider_attempt_evidence(value: Mapping[str, Any]) -> bool:
    return bool(_strict_opl_running_provider_attempts(value, {}))


def _strict_opl_running_provider_attempts(*values: Mapping[str, Any]) -> list[dict[str, Any]]:
    proofs: list[dict[str, Any]] = []
    for value in values:
        for proof in _running_provider_attempt_candidates(value):
            if _strict_opl_running_provider_attempt(proof):
                proofs.append(proof)
    return proofs


def _running_provider_attempt_candidates(value: Mapping[str, Any]) -> list[dict[str, Any]]:
    if not value:
        return []
    candidates: list[dict[str, Any]] = []
    payload = _mapping(value)
    if payload.get("running_provider_attempt") is True:
        candidates.append(payload)
    for key in (
        "opl_provider_attempt",
        "provider_attempt_proof",
        "running_attempt",
        "runtime_liveness",
        "runtime_liveness_audit",
    ):
        nested = _mapping(payload.get(key))
        if nested:
            if "runtime_health" not in nested and key in {"runtime_liveness", "runtime_liveness_audit"}:
                nested = {**nested, "runtime_health": dict(nested)}
            candidates.append(nested)
    for key in ("current_execution_envelope", "current_work_unit"):
        nested = _mapping(payload.get(key))
        if nested:
            candidates.extend(_running_provider_attempt_candidates(nested))
            state = _mapping(nested.get("state"))
            if state:
                candidates.extend(_running_provider_attempt_candidates(state))
    return candidates


def _strict_opl_running_provider_attempt(proof: Mapping[str, Any]) -> bool:
    if proof.get("running_provider_attempt") is not True:
        return False
    if _running_provider_attempt_owner(proof) != OPL_TRANSITION_RUNTIME_OWNER:
        return False
    if _running_provider_attempt_ref(proof) is None:
        return False
    health = _mapping(proof.get("runtime_health")) or proof
    if health.get("strict_live") is False:
        return False
    if not has_running_health(health):
        return False
    boundary = _mapping(proof.get("authority_boundary"))
    if boundary and boundary.get("mas_can_authorize_provider_admission") is not False:
        return False
    return True


def _running_provider_attempt_owner(proof: Mapping[str, Any]) -> str | None:
    health = _mapping(proof.get("runtime_health"))
    return _first_text(
        proof.get("runtime_owner"),
        proof.get("provider_attempt_owner"),
        proof.get("queue_owner"),
        proof.get("owner"),
        health.get("runtime_owner"),
        health.get("provider_attempt_owner"),
    )


def _running_provider_attempt_ref(proof: Mapping[str, Any]) -> str | None:
    return _first_text(
        proof.get("active_stage_attempt_id"),
        proof.get("active_run_id"),
        proof.get("active_workflow_id"),
        _mapping(proof.get("running_attempt")).get("stage_attempt_id"),
        _mapping(proof.get("stage_run_identity")).get("stage_run_id"),
        _mapping(proof.get("stage_run_identity")).get("stage_run_identity_ref"),
    )


def _running_attempt_expected_action(action: Mapping[str, Any]) -> dict[str, Any]:
    obligation = _action_recovery_obligation(action)
    current_action = _mapping(action.get("current_executable_owner_action"))
    current_work_unit = _mapping(action.get("current_work_unit"))
    payload = {
        "action_type": _first_text(
            obligation.get("action_type"),
            current_action.get("action_type"),
            current_work_unit.get("action_type"),
        ),
        "work_unit_id": _first_text(
            obligation.get("work_unit_id"),
            current_action.get("work_unit_id"),
            current_work_unit.get("work_unit_id"),
        ),
        "work_unit_fingerprint": _first_text(
            obligation.get("work_unit_fingerprint"),
            obligation.get("action_fingerprint"),
            current_action.get("work_unit_fingerprint"),
            current_action.get("action_fingerprint"),
            current_work_unit.get("work_unit_fingerprint"),
            current_work_unit.get("action_fingerprint"),
        ),
    }
    return {key: value for key, value in payload.items() if value not in (None, "", [], {})}


def _provider_admission_outcome_ref(
    *,
    candidate: Mapping[str, Any],
    action: Mapping[str, Any],
) -> str:
    return (
        _non_empty_text(candidate.get("action_id"))
        or _non_empty_text(candidate.get("dispatch_path"))
        or _transition_request_outcome_ref(candidate=candidate, action=action)
    )


def _transition_request_outcome_ref(
    *,
    candidate: Mapping[str, Any],
    action: Mapping[str, Any],
) -> str:
    request = _mapping(candidate.get("opl_domain_progress_transition_request"))
    if not request:
        request = _mapping(
            _mapping(candidate.get("paper_progress_policy_result")).get(
                "opl_domain_progress_transition_request"
            )
        )
    return (
        _non_empty_text(request.get("idempotency_key"))
        or _non_empty_text(candidate.get("action_id"))
        or _non_empty_text(candidate.get("dispatch_path"))
        or f"transition_request_pending:{_non_empty_text(action.get('study_id')) or 'unknown-study'}"
    )


def _candidate_matches_action_obligation(
    candidate: Mapping[str, Any],
    action: Mapping[str, Any],
) -> bool:
    study_id = _non_empty_text(action.get("study_id"))
    candidate_study_id = _first_text(candidate.get("study_id"), candidate.get("quest_id"))
    if study_id is not None and candidate_study_id is not None and candidate_study_id != study_id:
        return False
    expected_action_type = _first_text(
        _action_recovery_obligation(action).get("action_type"),
        _mapping(action.get("current_executable_owner_action")).get("action_type"),
        _mapping(action.get("current_work_unit")).get("action_type"),
    )
    candidate_action_type = _non_empty_text(candidate.get("action_type"))
    if (
        expected_action_type is not None
        and candidate_action_type is not None
        and candidate_action_type != expected_action_type
    ):
        return False
    expected_work_unit = _first_text(
        _action_recovery_obligation(action).get("work_unit_id"),
        _mapping(action.get("current_executable_owner_action")).get("work_unit_id"),
        _mapping(action.get("current_work_unit")).get("work_unit_id"),
    )
    candidate_work_unit = _first_text(candidate.get("work_unit_id"), candidate.get("next_work_unit"))
    if (
        expected_work_unit is not None
        and candidate_work_unit is not None
        and candidate_work_unit != expected_work_unit
    ):
        return False
    expected_fingerprint = _action_obligation_fingerprint(action)
    candidate_fingerprints = {
        text
        for value in (
            candidate.get("work_unit_fingerprint"),
            candidate.get("action_fingerprint"),
            candidate.get("source_fingerprint"),
            *_text_items(candidate.get("work_unit_fingerprints")),
        )
        if (text := _non_empty_text(value)) is not None
    }
    if expected_fingerprint is not None and candidate_fingerprints:
        return expected_fingerprint in candidate_fingerprints
    return True


def _candidate_has_mas_transition_request(candidate: Mapping[str, Any]) -> bool:
    request = _mapping(candidate.get("opl_domain_progress_transition_request"))
    if not request:
        request = _mapping(
            _mapping(candidate.get("paper_progress_policy_result")).get(
                "opl_domain_progress_transition_request"
            )
        )
    if not request:
        return False
    if _non_empty_text(request.get("surface_kind")) != MAS_TRANSITION_REQUEST_SURFACE:
        return False
    if _non_empty_text(request.get("target_runtime_owner")) != OPL_TRANSITION_RUNTIME_OWNER:
        return False
    runtime_kind = _non_empty_text(request.get("target_runtime_kind")) or _non_empty_text(
        request.get("runtime_kind")
    )
    if runtime_kind != OPL_TRANSITION_RUNTIME_KIND:
        return False
    if request.get("mas_can_create_opl_outbox_record") is not False:
        return False
    if _mas_transition_request_has_runtime_field(request):
        return False
    aggregate_identity = _mapping(request.get("aggregate_identity"))
    required_identity = (
        aggregate_identity.get("aggregate_kind"),
        aggregate_identity.get("aggregate_id"),
        aggregate_identity.get("study_id"),
        aggregate_identity.get("work_unit_id"),
        request.get("idempotency_key"),
        request.get("source_generation"),
        request.get("expected_version"),
    )
    if any(_non_empty_text(value) is None for value in required_identity):
        return False
    return bool(_mapping(request.get("required_postcondition")))


def _mas_transition_request_has_runtime_field(request: Mapping[str, Any]) -> bool:
    forbidden_fields = {
        "current_control_command_outbox_record",
        "opl_domain_progress_transition_command",
        "opl_domain_progress_transition_event",
        "opl_domain_progress_transition_outbox_item",
        "stage_run_identity",
        "projection_metadata",
        "read_model_generation_metadata",
    }
    return any(field in request for field in forbidden_fields)


def _current_typed_blocker_payload(action: Mapping[str, Any]) -> dict[str, Any]:
    current_work_unit = _mapping(action.get("current_work_unit"))
    state = _mapping(current_work_unit.get("state"))
    typed_blocker = (
        _mapping(state.get("typed_blocker"))
        or _mapping(current_work_unit.get("typed_blocker"))
        or _mapping(action.get("typed_blocker"))
    )
    return dict(typed_blocker)


def _action_recovery_obligation(action: Mapping[str, Any]) -> dict[str, Any]:
    recovery = _mapping(action.get("paper_recovery_state"))
    return _mapping(_mapping(recovery.get("current_authority")).get("obligation"))


def _action_obligation_fingerprint(action: Mapping[str, Any]) -> str | None:
    return _first_text(*_action_obligation_fingerprints(action))


def _action_obligation_fingerprints(action: Mapping[str, Any]) -> tuple[str, ...]:
    recovery = _mapping(action.get("paper_recovery_state"))
    next_action = _mapping(recovery.get("next_safe_action"))
    owner_callable = _mapping(next_action.get("owner_callable"))
    candidates = (
        _action_recovery_obligation(action).get("work_unit_fingerprint"),
        _action_recovery_obligation(action).get("action_fingerprint"),
        owner_callable.get("work_unit_fingerprint"),
        owner_callable.get("action_fingerprint"),
        next_action.get("work_unit_fingerprint"),
        next_action.get("action_fingerprint"),
        _mapping(action.get("current_executable_owner_action")).get("work_unit_fingerprint"),
        _mapping(action.get("current_executable_owner_action")).get("action_fingerprint"),
        _mapping(action.get("current_work_unit")).get("work_unit_fingerprint"),
        _mapping(action.get("current_work_unit")).get("action_fingerprint"),
        _mas_owner_callable_action_fingerprint(action),
    )
    return tuple(dict.fromkeys(text for value in candidates if (text := _non_empty_text(value)) is not None))


def _clean_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    cleaned: dict[str, Any] = {}
    for key, value in payload.items():
        if value in (None, "", [], {}):
            continue
        if isinstance(value, Mapping):
            nested = _clean_payload(value)
            if nested:
                cleaned[key] = nested
        elif isinstance(value, list):
            cleaned_list = [
                _clean_payload(item) if isinstance(item, Mapping) else item
                for item in value
                if item not in (None, "", [], {})
            ]
            if cleaned_list:
                cleaned[key] = cleaned_list
        else:
            cleaned[key] = value
    return cleaned


def _mas_owner_callable_action_fingerprint(action: Mapping[str, Any]) -> str:
    for key in ("work_unit_fingerprint", "action_fingerprint"):
        text = _non_empty_text(action.get(key))
        if text is not None:
            return text
    current_work_unit = _mapping(action.get("current_work_unit"))
    for key in ("work_unit_fingerprint", "action_fingerprint"):
        text = _non_empty_text(current_work_unit.get(key))
        if text is not None:
            return text
    recovery = _mapping(action.get("paper_recovery_state"))
    current_authority = _mapping(recovery.get("current_authority"))
    obligation = _mapping(current_authority.get("obligation"))
    for key in ("work_unit_fingerprint", "action_fingerprint"):
        text = _non_empty_text(obligation.get(key))
        if text is not None:
            return text
    return ""


def _study_root_for_obligation_outcome(
    *,
    action: Mapping[str, Any],
    profile: WorkspaceProfile,
    study_id: str,
) -> Path:
    for key in ("study_root", "study_root_path"):
        text = _non_empty_text(action.get(key))
        if text is not None:
            return Path(text).expanduser().resolve()
    return (Path(profile.studies_root) / study_id).expanduser().resolve()


def _text_items(values: object) -> list[str]:
    return [
        text
        for value in values or []
        if (text := _non_empty_text(value)) is not None
    ]


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}
