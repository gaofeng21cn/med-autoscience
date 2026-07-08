from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.controllers.opl_transition_readback import (
    has_opl_transition_readback as _has_opl_transition_readback,
)
from med_autoscience.controllers.paper_recovery_state.obligation_matching import (
    current_work_unit_matches_obligation as _current_work_unit_matches_obligation,
)
from med_autoscience.controllers.paper_recovery_state.provider_admission_state import (
    provider_admission_pending as _provider_admission_pending,
)
from med_autoscience.controllers.paper_recovery_state.running_attempt_identity import (
    running_attempt_has_obligation_identity as _running_attempt_has_obligation_identity,
    running_attempt_identity_surface as _running_attempt_identity_surface,
)
from med_autoscience.controllers.paper_recovery_state.state_diagnostics import (
    current_work_unit_status as _current_work_unit_status,
    first_text as _first_text,
    mapping as _mapping,
    text as _text,
    text_items as _text_items,
)
from med_autoscience.controllers.paper_recovery_state.successor_owner_resolution import (
    current_executable_owner_action as _current_executable_owner_action,
)


def projection_contradiction(
    progress: Mapping[str, Any],
    *,
    obligation: Mapping[str, Any],
) -> dict[str, Any] | None:
    operator_status = _mapping(progress.get("operator_status_card"))
    auto_parked = _mapping(progress.get("auto_runtime_parked"))
    if (
        operator_status
        and _text(operator_status.get("handling_state")) == "explicit_resume_pending"
        and auto_parked.get("parked") is False
        and auto_parked.get("superseded_by_current_owner_action") is True
        and not _has_current_provider_admission_candidate(progress, obligation=obligation)
    ):
        return {
            "condition": "operator_card_contradicts_auto_runtime_parked",
            "operator_handling_state": "explicit_resume_pending",
            "auto_runtime_parked": False,
        }
    envelope = _mapping(progress.get("current_execution_envelope"))
    if _text(envelope.get("state_kind")) == "running_provider_attempt":
        handoff = _running_attempt_identity_surface(progress)
        if not _running_attempt_has_obligation_identity(handoff, obligation=obligation):
            return {
                "condition": "running_attempt_missing_obligation_identity",
                "active_stage_attempt_id": _text(handoff.get("active_stage_attempt_id")),
                "active_run_id": _text(handoff.get("active_run_id")),
            }
    return None


def matching_terminal_closeout(
    progress: Mapping[str, Any],
    *,
    obligation: Mapping[str, Any],
) -> dict[str, Any] | None:
    for value in _terminal_closeout_candidates(progress):
        if isinstance(value, list):
            for item in value:
                candidate = _mapping(item)
                if candidate and _closeout_matches_obligation(candidate, obligation=obligation):
                    return dict(candidate)
        else:
            candidate = _mapping(value)
            if candidate and _closeout_matches_obligation(candidate, obligation=obligation):
                return dict(candidate)
    return None


def matching_provider_admission_terminal_closeout_consumed(
    progress: Mapping[str, Any],
    *,
    obligation: Mapping[str, Any],
) -> dict[str, Any] | None:
    candidate = provider_admission_terminal_closeout_consumed(
        _mapping(progress.get("opl_current_control_state_handoff"))
    )
    if candidate and _closeout_matches_obligation(candidate, obligation=obligation):
        return dict(candidate)
    return None


def provider_admission_terminal_closeout_consumed(
    handoff: Mapping[str, Any],
) -> dict[str, Any]:
    consumed = _mapping(handoff.get("provider_admission_terminal_closeout_consumed"))
    if not consumed:
        return {}
    terminal = (
        _mapping(consumed.get("latest_terminal_stage_log"))
        or _mapping(handoff.get("latest_terminal_stage_log"))
        or _mapping(handoff.get("latest_typed_owner_callable_closeout"))
    )
    paper_stage_log = _mapping(terminal.get("paper_stage_log"))
    typed_blocker = (
        _mapping(consumed.get("typed_blocker"))
        or _mapping(terminal.get("typed_blocker"))
        or _mapping(handoff.get("typed_blocker"))
        or _mapping(_mapping(handoff.get("latest_typed_owner_callable_closeout")).get("typed_blocker"))
    )
    refs = _dedupe(
        [
            _text(consumed.get("typed_blocker_ref")),
            _text(consumed.get("closeout_ref")),
            _text(terminal.get("typed_blocker_ref")),
            _text(terminal.get("closeout_ref")),
            _text(terminal.get("source_path")),
            _text(typed_blocker.get("typed_blocker_ref")),
            _text(typed_blocker.get("source_ref")),
            *_text_items(consumed.get("closeout_refs")),
            *_text_items(terminal.get("closeout_refs")),
            *_text_items(typed_blocker.get("closeout_refs")),
        ]
    )
    return {
        key: value
        for key, value in {
            **terminal,
            **consumed,
            "typed_blocker": typed_blocker or None,
            "status": _text(consumed.get("status")) or _text(terminal.get("status")) or "blocked",
            "outcome": _text(consumed.get("outcome")) or _text(terminal.get("outcome")) or _text(paper_stage_log.get("outcome")),
            "progress_delta_classification": _text(consumed.get("progress_delta_classification"))
            or _text(terminal.get("progress_delta_classification"))
            or _text(paper_stage_log.get("progress_delta_classification")),
            "blocked_reason": _first_text(
                consumed.get("blocked_reason"),
                consumed.get("blocker_type"),
                typed_blocker.get("blocked_reason"),
                typed_blocker.get("blocker_type"),
                typed_blocker.get("reason"),
                *_text_items(paper_stage_log.get("remaining_blockers")),
            ),
            "action_type": _first_text(consumed.get("action_type"), terminal.get("action_type"), typed_blocker.get("action_type")),
            "work_unit_id": _first_text(consumed.get("work_unit_id"), terminal.get("work_unit_id"), typed_blocker.get("work_unit_id")),
            "work_unit_fingerprint": _first_text(
                consumed.get("work_unit_fingerprint"),
                terminal.get("work_unit_fingerprint"),
                typed_blocker.get("work_unit_fingerprint"),
            ),
            "action_fingerprint": _first_text(
                consumed.get("action_fingerprint"),
                terminal.get("action_fingerprint"),
                typed_blocker.get("action_fingerprint"),
                consumed.get("work_unit_fingerprint"),
                terminal.get("work_unit_fingerprint"),
                typed_blocker.get("work_unit_fingerprint"),
            ),
            "stage_attempt_id": _first_text(consumed.get("stage_attempt_id"), terminal.get("stage_attempt_id")),
            "terminal_stage_attempt_id": _first_text(
                consumed.get("terminal_stage_attempt_id"),
                terminal.get("terminal_stage_attempt_id"),
                consumed.get("stage_attempt_id"),
                terminal.get("stage_attempt_id"),
            ),
            "closeout_refs": refs,
            "closeout_ref": refs[0] if refs else None,
            "source": "opl_current_control_state_handoff.provider_admission_terminal_closeout_consumed",
        }.items()
        if value not in (None, "", [], {})
    }


def closeout_refs(closeout: Mapping[str, Any]) -> list[str]:
    refs = [
        _text(closeout.get("closeout_ref")),
        _text(closeout.get("source_path")),
        _text(closeout.get("typed_blocker_ref")),
        *_text_items(closeout.get("closeout_refs")),
    ]
    return _dedupe(refs)


def suppressed_surfaces_for_owner_gate_decision(progress: Mapping[str, Any]) -> list[str]:
    suppressed = suppressed_surfaces_for_typed_blocker(progress)
    if _mapping(progress.get("current_work_unit")):
        suppressed.append("current_work_unit_typed_blocker")
    return list(dict.fromkeys(suppressed))


def suppressed_surfaces_for_typed_blocker(progress: Mapping[str, Any]) -> list[str]:
    suppressed: list[str] = []
    if _current_executable_owner_action(progress):
        suppressed.append("current_executable_owner_action")
    if _provider_admission_pending(progress):
        suppressed.append("provider_admission_candidates")
    return suppressed


def _has_current_provider_admission_candidate(
    progress: Mapping[str, Any],
    *,
    obligation: Mapping[str, Any],
) -> bool:
    current_work_unit = _mapping(progress.get("current_work_unit"))
    if (
        _current_work_unit_status(current_work_unit) == "executable_owner_action"
        and _mapping(current_work_unit.get("state")).get("provider_admission_pending") is True
        and _has_opl_transition_readback(current_work_unit)
        and _current_work_unit_matches_obligation(current_work_unit, obligation=obligation)
    ):
        return True
    return any(
        _has_opl_transition_readback(candidate)
        and _provider_admission_candidate_matches_obligation(candidate, obligation=obligation)
        for candidate in progress.get("provider_admission_candidates") or []
        if isinstance(candidate, Mapping)
    )


def _provider_admission_candidate_matches_obligation(
    candidate: Mapping[str, Any],
    *,
    obligation: Mapping[str, Any],
) -> bool:
    study_id = _text(obligation.get("study_id"))
    action_type = _text(obligation.get("action_type"))
    work_unit_id = _text(obligation.get("work_unit_id"))
    fingerprint = _text(obligation.get("work_unit_fingerprint"))
    candidate_study_id = _first_text(candidate.get("study_id"), candidate.get("quest_id"))
    if study_id is None or candidate_study_id != study_id:
        return False
    if action_type and _text(candidate.get("action_type")) != action_type:
        return False
    if work_unit_id and _text(candidate.get("work_unit_id")) != work_unit_id:
        return False
    if fingerprint is None:
        return False
    candidate_fingerprints = {
        value
        for value in (
            _text(candidate.get("work_unit_fingerprint")),
            _text(candidate.get("action_fingerprint")),
            *_text_items(candidate.get("work_unit_fingerprints")),
        )
        if value is not None
    }
    return fingerprint in candidate_fingerprints


def _terminal_closeout_candidates(progress: Mapping[str, Any]) -> tuple[object, ...]:
    handoff = _mapping(progress.get("opl_current_control_state_handoff"))
    consumed = provider_admission_terminal_closeout_consumed(handoff)
    return (
        progress.get("terminal_closeout_precedence_evidence"),
        progress.get("terminal_closeout"),
        progress.get("accepted_closeout_evidence"),
        consumed if consumed else None,
    )


def _closeout_matches_obligation(
    closeout: Mapping[str, Any],
    *,
    obligation: Mapping[str, Any],
) -> bool:
    obligation_id = _text(obligation.get("recovery_obligation_id"))
    closeout_obligation_id = _text(closeout.get("recovery_obligation_id"))
    if obligation_id and closeout_obligation_id and closeout_obligation_id != obligation_id:
        return False
    action_type = _text(obligation.get("action_type"))
    work_unit_id = _text(obligation.get("work_unit_id"))
    fingerprint = _text(obligation.get("work_unit_fingerprint"))
    if action_type and _text(closeout.get("action_type")) not in {None, action_type}:
        return False
    if work_unit_id and _text(closeout.get("work_unit_id")) not in {None, work_unit_id}:
        return False
    if fingerprint and closeout_obligation_id != obligation_id:
        closeout_fingerprints = {
            value
            for value in (
                _text(closeout.get("work_unit_fingerprint")),
                _text(closeout.get("action_fingerprint")),
            )
            if value is not None
        }
        if closeout_fingerprints and fingerprint not in closeout_fingerprints:
            return False
    return bool(
        _text(closeout.get("stage_attempt_id"))
        or _text(closeout.get("terminal_stage_attempt_id"))
        or _text(closeout.get("active_stage_attempt_id"))
        or closeout_refs(closeout)
    )


def _dedupe(values: list[str | None]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value is not None))


__all__ = [
    "closeout_refs",
    "matching_provider_admission_terminal_closeout_consumed",
    "matching_terminal_closeout",
    "projection_contradiction",
    "provider_admission_terminal_closeout_consumed",
    "suppressed_surfaces_for_owner_gate_decision",
    "suppressed_surfaces_for_typed_blocker",
]
