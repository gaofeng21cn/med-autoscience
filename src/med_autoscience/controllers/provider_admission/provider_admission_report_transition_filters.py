from __future__ import annotations

from typing import Any, Mapping

from med_autoscience.controllers.opl_transition_readback import (
    candidate_opl_transition_readback,
)
from med_autoscience.controllers.provider_admission.managed_wakeup import _non_empty_text
from med_autoscience.controllers.provider_admission.provider_admission_helpers import (
    mapping as _mapping,
)
from med_autoscience.controllers.provider_admission.provider_admission_report_candidate_merge import (
    transition_request_key as _transition_request_key,
)


def filter_transition_requests_consumed_by_currentness(
    candidates: list[dict[str, Any]],
    *,
    report: Mapping[str, Any],
    current_control_state: Mapping[str, Any],
) -> list[dict[str, Any]]:
    if not candidates:
        return []
    currentness_by_study = _transition_consuming_currentness_by_study(report)
    if not currentness_by_study:
        return [dict(candidate) for candidate in candidates]
    protected_keys = _current_control_non_advancing_transition_request_keys(current_control_state)
    filtered: list[dict[str, Any]] = []
    for candidate in candidates:
        if _transition_request_key(candidate) in protected_keys:
            filtered.append(dict(candidate))
            continue
        if _accepted_owner_gate_transition_request_candidate(candidate):
            filtered.append(dict(candidate))
            continue
        study_id = _non_empty_text(candidate.get("study_id"))
        currentness = currentness_by_study.get(study_id or "")
        if currentness and _transition_request_consumed_by_currentness(candidate, currentness):
            continue
        filtered.append(dict(candidate))
    return filtered


def _accepted_owner_gate_transition_request_candidate(candidate: Mapping[str, Any]) -> bool:
    if candidate_opl_transition_readback(candidate):
        return False
    transition_request = _mapping(candidate.get("opl_domain_progress_transition_request"))
    if not transition_request:
        transition_request = _mapping(
            _mapping(candidate.get("paper_progress_policy_result")).get(
                "opl_domain_progress_transition_request"
            )
        )
    if not transition_request:
        return False
    if candidate.get("provider_admission_requires_opl_runtime_result") is not True:
        return False
    if (
        _non_empty_text(candidate.get("source"))
        != "opl_current_control_state.study_current_executable_owner_action"
    ):
        return False
    basis = _mapping(candidate.get("currentness_basis"))
    return (
        _non_empty_text(candidate.get("mas_owner_action_source"))
        == "paper_recovery_state.accepted_owner_gate_decision"
        or _non_empty_text(candidate.get("authority"))
        == "paper_recovery_state.accepted_owner_gate_decision"
        or _non_empty_text(basis.get("source"))
        == "paper_recovery_state.accepted_owner_gate_decision"
        or _non_empty_text(basis.get("mas_owner_action_source"))
        == "paper_recovery_state.accepted_owner_gate_decision"
    )


def _current_control_non_advancing_transition_request_keys(
    current_control_state: Mapping[str, Any],
) -> set[tuple[str | None, str | None, str | None, str | None]]:
    keys: set[tuple[str | None, str | None, str | None, str | None]] = set()
    for decision in current_control_state.get("stage_route_arbiter_decisions") or []:
        if not isinstance(decision, Mapping):
            continue
        if _non_empty_text(decision.get("decision")) != "opl_transition_readback_required":
            continue
        if _non_empty_text(decision.get("evidence_status")) != "NonAdvancingApply":
            continue
        if _non_empty_text(decision.get("no_progress_signal")) != "transition_request_waits_for_opl_runtime":
            continue
        keys.add(_transition_request_key(decision))
    return keys


def _transition_consuming_currentness_by_study(
    report: Mapping[str, Any],
) -> dict[str, dict[str, Any]]:
    contexts: dict[str, dict[str, Any]] = {}
    progress_currentness = _mapping(
        _mapping(report.get("current_execution_evidence")).get("progress_currentness")
    )
    for study_id, payload in progress_currentness.items():
        normalized_study_id = _non_empty_text(study_id)
        currentness = _mapping(payload)
        if normalized_study_id is not None and _currentness_consumes_transition_request(currentness):
            contexts[normalized_study_id] = dict(currentness)
    for action in report.get("managed_study_actions") or []:
        currentness = _mapping(action)
        study_id = _non_empty_text(currentness.get("study_id"))
        if study_id is not None and _currentness_consumes_transition_request(currentness):
            contexts.setdefault(study_id, dict(currentness))
    return contexts


def _currentness_consumes_transition_request(currentness: Mapping[str, Any]) -> bool:
    if currentness.get("provider_admission_pending_count") not in (None, 0):
        return False
    if currentness.get("transition_request_pending_count") not in (None, 0):
        return False
    if currentness.get("provider_admission_candidates") or currentness.get("transition_request_candidates"):
        return False
    if _terminal_closeout_consumed_by_currentness(currentness):
        return True
    current_work_unit = _mapping(currentness.get("current_work_unit"))
    current_execution = _mapping(currentness.get("current_execution_envelope"))
    return _non_empty_text(current_work_unit.get("status")) in {
        "owner_receipt_recorded",
        "typed_blocker",
        "blocked_current_work_unit",
    } or _non_empty_text(current_execution.get("state_kind")) in {
        "owner_receipt_recorded",
        "typed_blocker",
        "blocked_current_work_unit",
    }


def _terminal_closeout_consumed_by_currentness(currentness: Mapping[str, Any]) -> bool:
    consumed = _mapping(currentness.get("provider_admission_terminal_closeout_consumed"))
    if not consumed:
        handoff = _mapping(currentness.get("opl_current_control_state_handoff"))
        consumed = _mapping(handoff.get("provider_admission_terminal_closeout_consumed"))
    if not consumed:
        return False
    return any(
        _non_empty_text(consumed.get(key)) is not None
        for key in (
            "stage_attempt_id",
            "owner_receipt_ref",
            "typed_blocker_ref",
            "work_unit_id",
            "work_unit_fingerprint",
            "action_fingerprint",
        )
    )


def _transition_request_consumed_by_currentness(
    candidate: Mapping[str, Any],
    currentness: Mapping[str, Any],
) -> bool:
    if candidate.get("same_tick_materialized_provider_admission") is not True:
        return False
    materialization_source = _non_empty_text(candidate.get("same_tick_materialization_source"))
    if materialization_source != "dry_run_preview":
        return False
    return _candidate_matches_currentness(candidate, currentness=currentness)


def _candidate_matches_currentness(
    candidate: Mapping[str, Any],
    *,
    currentness: Mapping[str, Any],
) -> bool:
    current_work_unit = _mapping(currentness.get("current_work_unit"))
    current_action = _mapping(currentness.get("current_executable_owner_action"))
    identities = [current_work_unit, current_action]
    candidate_action = _non_empty_text(candidate.get("action_type"))
    candidate_work_unit = _non_empty_text(candidate.get("work_unit_id"))
    candidate_fingerprint = _non_empty_text(candidate.get("work_unit_fingerprint")) or _non_empty_text(
        candidate.get("action_fingerprint")
    )
    for identity in identities:
        if not identity:
            continue
        action_type = _non_empty_text(identity.get("action_type"))
        work_unit_id = _non_empty_text(identity.get("work_unit_id"))
        fingerprint = _non_empty_text(identity.get("work_unit_fingerprint")) or _non_empty_text(
            identity.get("action_fingerprint")
        )
        if candidate_action is not None and action_type is not None and candidate_action != action_type:
            continue
        if candidate_work_unit is not None and work_unit_id is not None and candidate_work_unit != work_unit_id:
            continue
        if candidate_fingerprint is not None and fingerprint is not None and candidate_fingerprint != fingerprint:
            continue
        if action_type is not None or work_unit_id is not None or fingerprint is not None:
            return True
    return False


__all__ = ["filter_transition_requests_consumed_by_currentness"]
