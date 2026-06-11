from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.controllers.domain_action_request_materializer_parts import (
    fresh_progress_arbitration,
)
from med_autoscience.controllers.stage_route_currentness_identity import (
    currentness_identities_match,
)


SUPPORTED_REPAIR_PROGRESS_ACTIONS = frozenset(
    {
        "return_to_ai_reviewer_workflow",
        "run_gate_clearing_batch",
    }
)


def current_action_is_repair_progress_followup(current_action: Mapping[str, Any]) -> bool:
    source = _text(current_action.get("source")) or _text(current_action.get("source_surface"))
    if source != "repair_progress_projection.mas_owner_repair_execution_evidence":
        return False
    action_type = fresh_progress_arbitration.current_action_supported_action_type(current_action)
    if action_type not in SUPPORTED_REPAIR_PROGRESS_ACTIONS:
        return False
    return has_repair_progress_evidence(current_action)


def generated_action_is_repair_progress_followup(action: Mapping[str, Any]) -> bool:
    if _text(action.get("current_action_source")) != (
        "repair_progress_projection.mas_owner_repair_execution_evidence"
    ):
        return False
    if _text(action.get("action_type")) not in SUPPORTED_REPAIR_PROGRESS_ACTIONS:
        return False
    return has_repair_progress_evidence(action)


def has_repair_progress_evidence(action: Mapping[str, Any]) -> bool:
    return bool(
        _mapping(action.get("repair_progress_precedence"))
        or _text(action.get("source_ref")) is not None
    )


def typed_blocker_allows_repair_progress_followup(
    *,
    envelope: Mapping[str, Any],
    current_action: Mapping[str, Any],
) -> bool:
    state_kind = _text(envelope.get("state_kind")) or _text(envelope.get("execution_state_kind"))
    if state_kind != "typed_blocker":
        return False
    if not current_action_is_repair_progress_followup(current_action):
        return False
    blocker = _mapping(envelope.get("typed_blocker"))
    if _text(blocker.get("owner")) != "one-person-lab":
        return False
    if not any(
        "opl_execution_authorization_required" in reason
        for reason in _typed_blocker_reasons(blocker)
    ):
        return False
    if not currentness_identities_match(current_action, blocker, require_fingerprint=True):
        return False
    return _text(current_action.get("action_type")) == _text(blocker.get("action_type"))


def generated_action_matches_scan_currentness(
    *,
    study: Mapping[str, Any],
    fresh_action: Mapping[str, Any],
) -> bool:
    if not generated_action_is_repair_progress_followup(fresh_action):
        return False
    envelope = _mapping(study.get("current_execution_envelope"))
    state_kind = _text(envelope.get("state_kind")) or _text(envelope.get("execution_state_kind"))
    if state_kind == "running_provider_attempt":
        return False
    return any(
        currentness_identities_match(fresh_action, candidate)
        for candidate in scan_currentness_candidates(study)
    )


def generated_action_matches_action_currentness(
    *,
    fresh_action: Mapping[str, Any],
    currentness_action: Mapping[str, Any],
) -> bool:
    return generated_action_is_repair_progress_followup(
        fresh_action
    ) and currentness_identities_match(fresh_action, currentness_action)


def scan_currentness_candidates(study: Mapping[str, Any]) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for value in (
        study.get("owner_route"),
        study.get("current_executable_owner_action"),
        study.get("current_work_unit"),
    ):
        payload = _mapping(value)
        if payload:
            candidates.append(payload)
    envelope = _mapping(study.get("current_execution_envelope"))
    if envelope:
        candidates.append(envelope)
    for action in study.get("action_queue") or []:
        payload = _mapping(action)
        if payload:
            candidates.append(payload)
    return candidates


def _typed_blocker_reasons(blocker: Mapping[str, Any]) -> set[str]:
    return {
        text
        for value in (
            blocker.get("blocker_id"),
            blocker.get("blocker_type"),
            blocker.get("reason"),
            blocker.get("blocked_reason"),
            blocker.get("terminal_closeout_status"),
            blocker.get("terminal_closeout_outcome"),
        )
        if (text := _text(value)) is not None
    }


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "current_action_is_repair_progress_followup",
    "generated_action_is_repair_progress_followup",
    "generated_action_matches_action_currentness",
    "generated_action_matches_scan_currentness",
    "has_repair_progress_evidence",
    "scan_currentness_candidates",
    "typed_blocker_allows_repair_progress_followup",
]
