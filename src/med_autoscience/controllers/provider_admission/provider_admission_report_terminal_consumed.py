from __future__ import annotations

from typing import Any, Mapping

from med_autoscience.controllers.paper_recovery_state import build_paper_recovery_state
from med_autoscience.controllers.provider_admission.managed_wakeup import _non_empty_text
from med_autoscience.controllers.provider_admission.provider_admission_helpers import (
    mapping as _mapping,
)


def sync_managed_action_provider_admission_candidates(
    actions: Any,
    *,
    candidates: list[dict[str, Any]],
    transition_request_candidates: list[dict[str, Any]] | None = None,
    terminal_consumed_by_study: Mapping[str, Mapping[str, Any]] | None = None,
) -> list[Any]:
    candidates_by_study: dict[str, list[dict[str, Any]]] = {}
    for candidate in candidates:
        study_id = _non_empty_text(candidate.get("study_id"))
        if study_id is None:
            continue
        candidates_by_study.setdefault(study_id, []).append(dict(candidate))
    transition_requests_by_study: dict[str, list[dict[str, Any]]] = {}
    for candidate in transition_request_candidates or []:
        study_id = _non_empty_text(candidate.get("study_id"))
        if study_id is None:
            continue
        transition_requests_by_study.setdefault(study_id, []).append(dict(candidate))
    synced_actions: list[Any] = []
    for action in actions or []:
        if not isinstance(action, Mapping):
            synced_actions.append(action)
            continue
        synced_action = dict(action)
        study_id = _non_empty_text(synced_action.get("study_id"))
        terminal_consumed = _mapping((terminal_consumed_by_study or {}).get(study_id or ""))
        if terminal_consumed and _terminal_consumed_matches_action_state(
            terminal_consumed,
            synced_action,
        ):
            synced_actions.append(
                _managed_action_with_terminal_consumed(
                    synced_action,
                    terminal_consumed=terminal_consumed,
                )
            )
            continue
        action_candidates = candidates_by_study.get(study_id or "", [])
        if not action_candidates:
            transition_requests = transition_requests_by_study.get(study_id or "", [])
            if transition_requests:
                synced_action["provider_admission_candidates"] = []
                synced_action["provider_admission_state"] = {
                    "status": "none",
                    "candidate_count": 0,
                    "running_provider_attempt": False,
                }
                synced_actions.append(synced_action)
                continue
            if (
                "provider_admission_candidates" in synced_action
                or "provider_admission_state" in synced_action
            ):
                synced_action["provider_admission_candidates"] = []
                synced_action.pop("provider_admission_state", None)
            synced_actions.append(synced_action)
            continue
        synced_action["provider_admission_candidates"] = [dict(candidate) for candidate in action_candidates]
        synced_action["provider_admission_state"] = {
            **_mapping(synced_action.get("provider_admission_state")),
            "status": _non_empty_text(
                _mapping(synced_action.get("provider_admission_state")).get("status")
            ) or "pending",
            "candidate_count": len(action_candidates),
            "running_provider_attempt": bool(synced_action.get("running_provider_attempt")) is True,
        }
        synced_actions.append(synced_action)
    return synced_actions


def terminal_consumed_by_study(
    current_control_state: Mapping[str, Any],
) -> dict[str, dict[str, Any]]:
    consumed_by_study: dict[str, dict[str, Any]] = {}
    for study in current_control_state.get("studies") or []:
        study_payload = _mapping(study)
        study_id = _non_empty_text(study_payload.get("study_id"))
        consumed = _terminal_consumed_readback(study_payload)
        if study_id is not None and consumed:
            consumed_by_study[study_id] = consumed
    latest = _terminal_consumed_readback(current_control_state)
    identity = _mapping(latest.get("currentness_identity"))
    study_id = _non_empty_text(identity.get("study_id")) or _non_empty_text(latest.get("study_id"))
    if study_id is not None and latest:
        consumed_by_study.setdefault(study_id, latest)
    return consumed_by_study


def sync_progress_currentness_terminal_consumed(
    progress_currentness: Any,
    *,
    terminal_consumed_by_study: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    synced: dict[str, Any] = {}
    for study_id, payload in _mapping(progress_currentness).items():
        action = _mapping(payload)
        terminal_consumed = _mapping(terminal_consumed_by_study.get(_non_empty_text(study_id) or ""))
        if terminal_consumed and _terminal_consumed_matches_action_state(terminal_consumed, action):
            synced[study_id] = _managed_action_with_terminal_consumed(
                action,
                terminal_consumed=terminal_consumed,
            )
        else:
            synced[study_id] = dict(action)
    return synced


def sync_report_paper_recovery_states_from_actions(
    report: dict[str, Any],
    *,
    actions: list[Any],
    terminal_consumed_by_study: Mapping[str, Mapping[str, Any]],
) -> None:
    states = {
        study_id: dict(recovery)
        for study_id, recovery in _mapping(report.get("paper_recovery_states")).items()
        if isinstance(recovery, Mapping)
    }
    for action in actions:
        action_payload = _mapping(action)
        study_id = _non_empty_text(action_payload.get("study_id"))
        recovery = _mapping(action_payload.get("paper_recovery_state"))
        if (
            study_id is not None
            and study_id in terminal_consumed_by_study
            and recovery
        ):
            states[study_id] = dict(recovery)
    if states:
        report["paper_recovery_states"] = states


def _terminal_consumed_readback(payload: Mapping[str, Any]) -> dict[str, Any]:
    for key in (
        "provider_admission_terminal_closeout_consumed",
        "latest_provider_admission_terminal_consumed_readback",
    ):
        consumed = _mapping(payload.get(key))
        if _non_empty_text(consumed.get("status")) == "provider_admission_terminal_consumed":
            return dict(consumed)
    return {}


def _terminal_consumed_matches_action_state(
    consumed: Mapping[str, Any],
    action: Mapping[str, Any],
) -> bool:
    candidates = [
        _mapping(action.get("current_executable_owner_action")),
        _mapping(action.get("current_work_unit")),
        _mapping(action.get("paper_recovery_state")),
        *[
            _mapping(candidate)
            for candidate in action.get("provider_admission_candidates") or []
            if isinstance(candidate, Mapping)
        ],
    ]
    return any(_terminal_consumed_matches_identity(consumed, candidate) for candidate in candidates)


def _terminal_consumed_matches_identity(
    consumed: Mapping[str, Any],
    candidate: Mapping[str, Any],
) -> bool:
    if not consumed or not candidate:
        return False
    identity = _mapping(consumed.get("currentness_identity")) or consumed
    expected_study = _non_empty_text(identity.get("study_id"))
    candidate_study = _non_empty_text(candidate.get("study_id"))
    if expected_study is not None and candidate_study is not None and expected_study != candidate_study:
        return False
    for key in ("action_type", "work_unit_id"):
        expected = _non_empty_text(identity.get(key))
        observed = _non_empty_text(candidate.get(key))
        if expected is not None and observed is not None and expected != observed:
            return False
    expected_fingerprint = _non_empty_text(identity.get("work_unit_fingerprint")) or _non_empty_text(
        identity.get("action_fingerprint")
    )
    observed_fingerprint = _non_empty_text(candidate.get("work_unit_fingerprint")) or _non_empty_text(
        candidate.get("action_fingerprint")
    )
    if (
        expected_fingerprint is not None
        and observed_fingerprint is not None
        and expected_fingerprint != observed_fingerprint
    ):
        return False
    expected_route = _non_empty_text(identity.get("route_identity_key"))
    observed_route = _non_empty_text(candidate.get("route_identity_key"))
    if expected_route is not None and observed_route is not None and expected_route != observed_route:
        return False
    expected_attempt = _non_empty_text(identity.get("attempt_idempotency_key"))
    observed_attempt = _non_empty_text(candidate.get("attempt_idempotency_key"))
    if expected_attempt is not None and observed_attempt is not None and expected_attempt != observed_attempt:
        return False
    return expected_fingerprint is not None or expected_route is not None or expected_attempt is not None


def _managed_action_with_terminal_consumed(
    action: Mapping[str, Any],
    *,
    terminal_consumed: Mapping[str, Any],
) -> dict[str, Any]:
    updated = dict(action)
    consumed = dict(terminal_consumed)
    updated["provider_admission_candidates"] = []
    updated["provider_admission_pending_count"] = 0
    updated["transition_request_candidates"] = []
    updated["transition_request_pending_count"] = 0
    updated.pop("provider_admission_state", None)
    updated["provider_admission_terminal_closeout_consumed"] = consumed
    updated["opl_current_control_state_handoff"] = _handoff_with_terminal_consumed(
        _mapping(updated.get("opl_current_control_state_handoff")),
        terminal_consumed=consumed,
    )
    current_action = _mapping(updated.get("current_executable_owner_action"))
    if current_action and _terminal_consumed_matches_identity(consumed, current_action):
        updated.pop("current_executable_owner_action", None)
    current_work_unit = _mapping(updated.get("current_work_unit"))
    if current_work_unit and _terminal_consumed_matches_identity(consumed, current_work_unit):
        updated["current_work_unit"] = _current_work_unit_with_terminal_consumed(
            current_work_unit,
            terminal_consumed=consumed,
        )
    updated["paper_recovery_state"] = build_paper_recovery_state(updated)
    supervisor_decision = _mapping(updated["paper_recovery_state"].get("supervisor_decision"))
    if supervisor_decision:
        updated["supervisor_decision"] = dict(supervisor_decision)
    else:
        updated.pop("supervisor_decision", None)
    return updated


def _handoff_with_terminal_consumed(
    handoff: Mapping[str, Any],
    *,
    terminal_consumed: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        **dict(handoff),
        "running_provider_attempt": False,
        "provider_admission_pending_count": 0,
        "provider_admission_candidates": [],
        "transition_request_pending_count": 0,
        "transition_request_candidates": [],
        "provider_admission_terminal_closeout_consumed": dict(terminal_consumed),
    }


def _current_work_unit_with_terminal_consumed(
    current_work_unit: Mapping[str, Any],
    *,
    terminal_consumed: Mapping[str, Any],
) -> dict[str, Any]:
    state = dict(_mapping(current_work_unit.get("state")))
    state.update(
        {
            "provider_admission_pending": False,
            "transition_request_pending": False,
            "provider_attempt_or_lease_required": False,
            "provider_admission_requires_opl_runtime_result": False,
            "provider_admission_terminal_consumed": True,
            "provider_admission_terminal_consumed_readback": dict(terminal_consumed),
        }
    )
    return {
        **dict(current_work_unit),
        "state": {key: value for key, value in state.items() if value not in (None, "", [], {})},
    }


__all__ = [
    "sync_managed_action_provider_admission_candidates",
    "sync_progress_currentness_terminal_consumed",
    "sync_report_paper_recovery_states_from_actions",
    "terminal_consumed_by_study",
]
