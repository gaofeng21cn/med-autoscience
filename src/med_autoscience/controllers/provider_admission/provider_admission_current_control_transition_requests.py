from __future__ import annotations

from typing import Any, Mapping

from med_autoscience.controllers.opl_transition_readback import (
    candidate_opl_transition_readback,
    provider_admission_opl_transition_readback,
)
from med_autoscience.controllers.provider_admission.managed_wakeup import _non_empty_text
from med_autoscience.controllers.provider_admission.provider_admission_helpers import (
    mapping as _mapping,
)


def candidates_with_scanned_study_provider_readbacks(
    candidates: list[dict[str, Any]],
    *,
    scanned_studies: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    merged = [dict(candidate) for candidate in candidates]
    index_by_key = {
        transition_request_readback_identity_key(candidate): index
        for index, candidate in enumerate(merged)
    }
    for study in scanned_studies:
        for candidate in _study_provider_readback_candidates(study):
            key = transition_request_readback_identity_key(candidate)
            if key in index_by_key:
                existing_index = index_by_key[key]
                existing = merged[existing_index]
                if provider_admission_opl_transition_readback(
                    candidate
                ) and not provider_admission_opl_transition_readback(existing):
                    merged[existing_index] = {
                        **existing,
                        **candidate,
                    }
                continue
            merged.append(candidate)
            index_by_key[key] = len(merged) - 1
    return merged


def _study_provider_readback_candidates(study: Mapping[str, Any]) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for item in study.get("provider_admission_candidates") or []:
        if not isinstance(item, Mapping):
            continue
        if provider_admission_opl_transition_readback(item):
            candidates.append(dict(item))
    handoff = _mapping(study.get("opl_current_control_state_handoff"))
    for item in handoff.get("provider_admission_candidates") or []:
        if not isinstance(item, Mapping):
            continue
        if provider_admission_opl_transition_readback(item):
            candidates.append(dict(item))
    return candidates


def arbiter_candidate_key(decision: Mapping[str, Any]) -> tuple[str | None, ...]:
    return (
        _non_empty_text(decision.get("study_id")),
        _non_empty_text(decision.get("action_type")),
        _non_empty_text(decision.get("work_unit_id")),
        _non_empty_text(decision.get("work_unit_fingerprint"))
        or _non_empty_text(decision.get("action_fingerprint")),
    )


def candidate_key(candidate: Mapping[str, Any]) -> tuple[str | None, ...]:
    return (
        _non_empty_text(candidate.get("study_id")),
        _non_empty_text(candidate.get("action_type")),
        _non_empty_text(candidate.get("work_unit_id")),
        _non_empty_text(candidate.get("work_unit_fingerprint"))
        or _non_empty_text(candidate.get("action_fingerprint")),
    )


def candidate_with_transition_request_pending_state(
    candidate: Mapping[str, Any],
) -> dict[str, Any]:
    payload = dict(candidate)
    payload["provider_admission_pending"] = False
    payload["provider_admission_requires_opl_runtime_result"] = True
    payload["provider_attempt_or_lease_required"] = False
    payload["status"] = "transition_request_pending"
    payload["dispatch_status"] = "transition_request_pending"
    return payload


def merge_transition_request_candidates(
    candidates: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    merged: list[dict[str, Any]] = []
    index_by_key: dict[tuple[str | None, ...], int] = {}
    for candidate in candidates:
        key = candidate_key(candidate)
        if key in index_by_key:
            existing_index = index_by_key[key]
            merged[existing_index] = _merge_candidate_payloads(
                merged[existing_index],
                candidate,
            )
            continue
        index_by_key[key] = len(merged)
        merged.append(dict(candidate))
    return merged


def _merge_candidate_payloads(
    existing: Mapping[str, Any],
    incoming: Mapping[str, Any],
) -> dict[str, Any]:
    merged = {**dict(existing), **dict(incoming)}
    for key, value in existing.items():
        if merged.get(key) in (None, "", [], {}):
            merged[key] = value
    for key, value in incoming.items():
        if isinstance(value, Mapping):
            base = _mapping(existing.get(key))
            if base:
                merged[key] = {**base, **dict(value)}
    return merged


def candidates_without_transition_requests_consumed_by_provider_readback(
    candidates: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    provider_readback_keys = {
        transition_request_readback_identity_key(candidate)
        for candidate in candidates
        if provider_admission_opl_transition_readback(candidate)
    }
    if not provider_readback_keys:
        return [dict(candidate) for candidate in candidates]
    return [
        dict(candidate)
        for candidate in candidates
        if not (
            transition_request_readback_identity_key(candidate) in provider_readback_keys
            and _transition_request_only_candidate(candidate)
        )
    ]


def candidates_without_transition_requests_consumed_by_currentness(
    candidates: list[dict[str, Any]],
    *,
    scanned_studies_by_id: Mapping[str, Mapping[str, Any]],
) -> list[dict[str, Any]]:
    return [
        dict(candidate)
        for candidate in candidates
        if not _transition_request_consumed_by_scanned_currentness(
            candidate,
            scanned_studies_by_id=scanned_studies_by_id,
        )
    ]


def _transition_request_consumed_by_scanned_currentness(
    candidate: Mapping[str, Any],
    *,
    scanned_studies_by_id: Mapping[str, Mapping[str, Any]],
) -> bool:
    if not _transition_request_only_candidate(candidate):
        return False
    study_id = _non_empty_text(candidate.get("study_id"))
    if study_id is None:
        return False
    currentness = _mapping(scanned_studies_by_id.get(study_id))
    if not _currentness_consumes_transition_request(currentness):
        return False
    consumed = _currentness_terminal_closeout_consumed(currentness)
    if not consumed:
        return False
    return _consumed_closeout_matches_candidate(consumed, candidate)


def _currentness_consumes_transition_request(currentness: Mapping[str, Any]) -> bool:
    if currentness.get("provider_admission_pending_count") not in (None, 0):
        return False
    if currentness.get("transition_request_pending_count") not in (None, 0):
        return False
    if currentness.get("provider_admission_candidates") or currentness.get(
        "transition_request_candidates"
    ):
        return False
    return bool(_currentness_terminal_closeout_consumed(currentness))


def _currentness_terminal_closeout_consumed(
    currentness: Mapping[str, Any],
) -> dict[str, Any]:
    consumed = _mapping(currentness.get("provider_admission_terminal_closeout_consumed"))
    if consumed:
        return consumed
    handoff = _mapping(currentness.get("opl_current_control_state_handoff"))
    return _mapping(handoff.get("provider_admission_terminal_closeout_consumed"))


def _consumed_closeout_matches_candidate(
    consumed: Mapping[str, Any],
    candidate: Mapping[str, Any],
) -> bool:
    if _non_empty_text(consumed.get("action_type")) not in (
        None,
        _non_empty_text(candidate.get("action_type")),
    ):
        return False
    if _non_empty_text(consumed.get("work_unit_id")) not in (
        None,
        _non_empty_text(candidate.get("work_unit_id")),
    ):
        return False
    consumed_fingerprint = _non_empty_text(
        consumed.get("work_unit_fingerprint")
    ) or _non_empty_text(consumed.get("action_fingerprint"))
    candidate_fingerprint = _non_empty_text(
        candidate.get("work_unit_fingerprint")
    ) or _non_empty_text(candidate.get("action_fingerprint"))
    if consumed_fingerprint not in (None, candidate_fingerprint):
        return False
    return _consumed_closeout_has_matching_runtime_identity(consumed, candidate)


def _consumed_closeout_has_matching_runtime_identity(
    consumed: Mapping[str, Any],
    candidate: Mapping[str, Any],
) -> bool:
    for key in (
        "route_identity_key",
        "attempt_idempotency_key",
        "idempotency_key",
    ):
        consumed_value = _non_empty_text(consumed.get(key))
        candidate_value = _non_empty_text(candidate.get(key))
        if (
            consumed_value is not None
            and candidate_value is not None
            and consumed_value == candidate_value
        ):
            return True
    return _non_empty_text(consumed.get("stage_attempt_id")) is not None


def transition_request_readback_identity_key(
    candidate: Mapping[str, Any],
) -> tuple[str | None, ...]:
    transition_request = _mapping(candidate.get("opl_domain_progress_transition_request"))
    if not transition_request:
        transition_request = _mapping(
            _mapping(candidate.get("paper_progress_policy_result")).get(
                "opl_domain_progress_transition_request"
            )
        )
    return (
        *candidate_key(candidate),
        _non_empty_text(candidate.get("route_identity_key")),
        _non_empty_text(candidate.get("attempt_idempotency_key")),
        _non_empty_text(candidate.get("idempotency_key"))
        or _non_empty_text(transition_request.get("idempotency_key")),
    )


def _transition_request_only_candidate(candidate: Mapping[str, Any]) -> bool:
    if candidate_opl_transition_readback(candidate):
        return False
    if candidate.get("provider_admission_requires_opl_runtime_result") is not True:
        return False
    return bool(
        _mapping(candidate.get("opl_domain_progress_transition_request"))
        or _mapping(
            _mapping(candidate.get("paper_progress_policy_result")).get(
                "opl_domain_progress_transition_request"
            )
        )
    )


def arbiter_decision_retains_transition_request(decision: Mapping[str, Any]) -> bool:
    if _non_empty_text(decision.get("mas_owner_action_source")) == (
        "paper_recovery_state.accepted_owner_gate_decision"
    ):
        return True
    currentness_basis = _mapping(decision.get("currentness_basis"))
    if _non_empty_text(currentness_basis.get("source")) == (
        "paper_recovery_state.accepted_owner_gate_decision"
    ) or _non_empty_text(currentness_basis.get("mas_owner_action_source")) == (
        "paper_recovery_state.accepted_owner_gate_decision"
    ):
        return True
    evidence = _mapping(decision.get("evidence"))
    weak_identity = _mapping(evidence.get("weak_provider_admission_identity"))
    return not weak_identity


__all__ = [
    "arbiter_candidate_key",
    "arbiter_decision_retains_transition_request",
    "candidate_key",
    "candidate_with_transition_request_pending_state",
    "candidates_with_scanned_study_provider_readbacks",
    "candidates_without_transition_requests_consumed_by_currentness",
    "candidates_without_transition_requests_consumed_by_provider_readback",
    "merge_transition_request_candidates",
    "transition_request_readback_identity_key",
]
