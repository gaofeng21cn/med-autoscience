from __future__ import annotations

import hashlib
import json
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

from med_autoscience.controllers import gate_clearing_batch, quality_repair_batch
from med_autoscience.controllers.domain_health_diagnostic_parts.managed_wakeup import (
    _non_empty_text,
)
from med_autoscience.profiles import WorkspaceProfile

MAS_OWNER_CALLABLE_DRAIN_MAX_PASSES = 3


def _drain_mas_owner_callable_actions(
    *,
    report: dict[str, Any],
    profile: WorkspaceProfile,
    study_ids: tuple[str, ...],
    refresh_owner_callable_actions: Callable[[list[dict[str, Any]]], None] | None = None,
    max_passes: int = MAS_OWNER_CALLABLE_DRAIN_MAX_PASSES,
) -> list[dict[str, Any]]:
    all_actions = [
        dict(action)
        for action in report.get("managed_study_mas_owner_callable_actions") or []
        if isinstance(action, Mapping)
    ]
    seen = {
        key
        for action in all_actions
        if (key := _mas_owner_callable_action_dedupe_key(action)) is not None
    }
    for _ in range(max(1, max_passes)):
        owner_callable_actions = _apply_mas_owner_callable_actions(
            report=report,
            profile=profile,
            study_ids=study_ids,
            seen=seen,
        )
        if not owner_callable_actions:
            break
        all_actions.extend(owner_callable_actions)
        report["managed_study_mas_owner_callable_actions"] = all_actions
        if refresh_owner_callable_actions is not None:
            refresh_owner_callable_actions(owner_callable_actions)
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
    owner_callable_actions = _drain_mas_owner_callable_actions(
        report=report,
        profile=profile,
        study_ids=study_ids,
        refresh_owner_callable_actions=refresh_owner_callable_actions,
    )
    if not fail_closed:
        return owner_callable_actions
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
        outcome = _closed_obligation_outcome(
            action=action_payload,
            current_control_state=current_control,
            owner_callable_actions=action_results_by_study.get(study_id, []),
            profile=profile,
            phase=phase,
        )
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
            "surface_kind": "managed_study_obligation_actuator_summary",
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
            "authority": "domain_health_diagnostic_obligation_actuator",
        }
    return owner_callable_actions


_OBLIGATION_ACTUATOR_ALLOWED_OUTCOMES = [
    "provider_admission_pending",
    "running_provider_attempt",
    "owner_receipt_ref",
    "typed_blocker_ref",
    "human_gate_ref",
    "route_back_evidence_ref",
]


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
    }:
        return False
    phase = _non_empty_text(recovery.get("phase"))
    next_kind = _non_empty_text(next_action.get("kind"))
    return phase in {
        "owner_action_ready",
        "admission_pending",
        "attempt_running",
        "domain_blocked",
        "admission_blocked",
        "human_gate",
    } or next_kind in {
        "run_mas_owner_callable",
        "materialize_provider_admission_or_owner_callable",
        "materialize_successor_owner_action",
        "materialize_successor_owner_gate",
        "admit_provider_attempt",
        "admit_identity_bound_stage_packet",
        "resolve_owner_gate_decision",
        "route_back_to_owner_or_repair_materialization",
        "resolve_typed_blocker",
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
    phase: str,
) -> dict[str, Any]:
    for owner_callable_action in reversed(owner_callable_actions):
        outcome = _owner_callable_action_outcome(
            action=action,
            owner_callable_action=owner_callable_action,
            phase=phase,
        )
        if outcome is not None:
            return outcome
    running = _running_provider_attempt_outcome(
        action=action,
        current_control_state=current_control_state,
        phase=phase,
    )
    if running is not None:
        return running
    pending = _provider_admission_pending_outcome(
        action=action,
        current_control_state=current_control_state,
        phase=phase,
    )
    if pending is not None:
        return pending
    route_back = _route_back_evidence_outcome(action=action, phase=phase)
    if route_back is not None:
        return route_back
    human_gate = _human_gate_outcome(action=action, phase=phase)
    if human_gate is not None:
        return human_gate
    typed_blocker = _typed_blocker_outcome(action=action, phase=phase)
    if typed_blocker is not None:
        return typed_blocker
    return _fail_closed_obligation_outcome(
        action=action,
        profile=profile,
        blocker_type="dhd_apply_no_closed_obligation_outcome",
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
    obligation = _action_recovery_obligation(action)
    expected_action_type = (
        _non_empty_text(obligation.get("action_type"))
        or _non_empty_text(_mapping(action.get("current_executable_owner_action")).get("action_type"))
        or _non_empty_text(_mapping(action.get("current_work_unit")).get("action_type"))
    )
    if expected_action_type is not None and expected_action_type != action_type:
        return False
    action_fingerprint = _non_empty_text(owner_callable_action.get("work_unit_fingerprint"))
    expected_fingerprint = _action_obligation_fingerprint(action)
    return not (action_fingerprint and expected_fingerprint and action_fingerprint != expected_fingerprint)


def _running_provider_attempt_outcome(
    *,
    action: Mapping[str, Any],
    current_control_state: Mapping[str, Any],
    phase: str,
) -> dict[str, Any] | None:
    study_id = _non_empty_text(action.get("study_id"))
    study = _current_control_study(current_control_state, study_id=study_id)
    if _action_has_running_provider_attempt_evidence(action) or _action_has_running_provider_attempt_evidence(study):
        return _obligation_outcome(
            action=action,
            outcome_kind="running_provider_attempt",
            outcome_ref=_first_text(
                action.get("active_stage_attempt_id"),
                action.get("active_run_id"),
                study.get("active_stage_attempt_id"),
                study.get("active_run_id"),
                _mapping(study.get("running_attempt")).get("stage_attempt_id"),
            )
            or f"running_provider_attempt:{study_id or 'unknown-study'}",
            phase=phase,
            details={"current_control_study": study},
        )
    return None


def _provider_admission_pending_outcome(
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
    return _obligation_outcome(
        action=action,
        outcome_kind="provider_admission_pending",
        outcome_ref=_non_empty_text(candidates[0].get("action_id"))
        or _non_empty_text(candidates[0].get("dispatch_path"))
        or f"provider_admission_pending:{_non_empty_text(action.get('study_id')) or 'unknown-study'}",
        phase=phase,
        details={"provider_admission_candidates": candidates},
    )


def _current_obligation_provider_admission_candidates(
    *,
    action: Mapping[str, Any],
    current_control_state: Mapping[str, Any],
) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for source in (
        action.get("provider_admission_candidates"),
        current_control_state.get("provider_admission_candidates"),
        _current_control_study(
            current_control_state,
            study_id=_non_empty_text(action.get("study_id")),
        ).get("provider_admission_candidates"),
        current_control_state.get("action_queue"),
    ):
        for candidate in source or []:
            if isinstance(candidate, Mapping) and _candidate_matches_action_obligation(candidate, action):
                candidates.append(dict(candidate))
    return candidates


def _route_back_evidence_outcome(
    *,
    action: Mapping[str, Any],
    phase: str,
) -> dict[str, Any] | None:
    recovery = _mapping(action.get("paper_recovery_state"))
    next_action = _mapping(recovery.get("next_safe_action"))
    accepted_owner_gate = _mapping(next_action.get("accepted_owner_gate_decision"))
    route_back_ref = _first_text(
        next_action.get("route_back_evidence_ref"),
        accepted_owner_gate.get("route_back_evidence_ref"),
        *_matching_ref_items(recovery.get("evidence_refs"), prefix="route_back:"),
    )
    if route_back_ref is None:
        return None
    return _obligation_outcome(
        action=action,
        outcome_kind="route_back_evidence_ref",
        outcome_ref=route_back_ref,
        phase=phase,
        details={"next_safe_action_kind": _non_empty_text(next_action.get("kind"))},
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
    human_gate_ref = _first_text(
        next_action.get("human_gate_ref"),
        supervisor_next.get("human_gate_ref"),
        *_matching_ref_items(recovery.get("evidence_refs"), prefix="human_gate:"),
    )
    if human_gate_ref is None:
        return None
    return _obligation_outcome(
        action=action,
        outcome_kind="human_gate_ref",
        outcome_ref=human_gate_ref,
        phase=phase,
        details={"next_safe_action_kind": _non_empty_text(next_action.get("kind"))},
    )


def _typed_blocker_outcome(
    *,
    action: Mapping[str, Any],
    phase: str,
) -> dict[str, Any] | None:
    typed_blocker = _current_typed_blocker_payload(action)
    typed_blocker_ref = _first_text(
        typed_blocker.get("typed_blocker_ref"),
        typed_blocker.get("latest_owner_answer_ref"),
        typed_blocker.get("source_ref"),
        *_matching_ref_items(_mapping(action.get("paper_recovery_state")).get("evidence_refs"), prefix="typed_blocker:"),
    )
    if typed_blocker_ref is None:
        return None
    return _obligation_outcome(
        action=action,
        outcome_kind="typed_blocker_ref",
        outcome_ref=typed_blocker_ref,
        phase=phase,
        details={
            "blocker_type": _first_text(
                typed_blocker.get("blocker_type"),
                typed_blocker.get("blocked_reason"),
            ),
        },
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
    study_root = _study_root_for_owner_callable(action=action, profile=profile, study_id=study_id)
    payload = _typed_control_blocker_payload(
        action=action,
        blocker_type=blocker_type,
        reason=reason,
        phase=phase,
    )
    blocker_path = (
        study_root
        / "artifacts"
        / "controller"
        / "domain_health_diagnostic_obligation_actuator"
        / "latest.json"
    )
    blocker_path.parent.mkdir(parents=True, exist_ok=True)
    blocker_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    history_path = blocker_path.parent / "history.jsonl"
    with history_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")
    typed_blocker_ref = str(blocker_path)
    return _obligation_outcome(
        action=action,
        outcome_kind="typed_blocker_ref",
        outcome_ref=typed_blocker_ref,
        phase=phase,
        details={"typed_control_blocker": payload},
        typed_control_blocker={**payload, "typed_blocker_ref": typed_blocker_ref},
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
    payload = {
        "surface_kind": "domain_health_diagnostic_obligation_actuator_typed_blocker",
        "schema_version": 1,
        "status": "typed_blocker",
        "fail_closed": True,
        "blocker_type": blocker_type,
        "reason": reason,
        "source": "domain_health_diagnostic.obligation_actuator",
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
    }
    cleaned = {key: value for key, value in payload.items() if value not in (None, "", [], {})}
    cleaned["typed_blocker_id"] = "dhd-obligation-blocker:" + hashlib.sha256(
        json.dumps(cleaned, ensure_ascii=True, sort_keys=True).encode("utf-8")
    ).hexdigest()[:24]
    return cleaned


def _obligation_outcome(
    *,
    action: Mapping[str, Any],
    outcome_kind: str,
    outcome_ref: str,
    phase: str,
    details: Mapping[str, Any] | None = None,
    typed_control_blocker: Mapping[str, Any] | None = None,
    postcondition_ok: bool = True,
) -> dict[str, Any]:
    obligation = _action_recovery_obligation(action)
    payload = {
        "surface_kind": "managed_study_obligation_actuator_outcome",
        "schema_version": 1,
        "study_id": _non_empty_text(action.get("study_id")) or _non_empty_text(obligation.get("study_id")),
        "quest_id": _non_empty_text(action.get("quest_id")) or _non_empty_text(obligation.get("quest_id")),
        "phase": phase,
        "outcome_kind": outcome_kind,
        outcome_kind: outcome_ref,
        "exactly_one_outcome": True,
        "postcondition_ok": postcondition_ok,
        "paper_recovery_next_safe_action_kind": _non_empty_text(
            _mapping(_mapping(action.get("paper_recovery_state")).get("next_safe_action")).get("kind")
        ),
        "recovery_obligation_id": _non_empty_text(
            _mapping(action.get("paper_recovery_state")).get("recovery_obligation_id")
        )
        or _non_empty_text(obligation.get("recovery_obligation_id")),
        "action_type": _first_text(
            obligation.get("action_type"),
            _mapping(action.get("current_executable_owner_action")).get("action_type"),
            _mapping(action.get("current_work_unit")).get("action_type"),
        ),
        "work_unit_id": _first_text(
            obligation.get("work_unit_id"),
            _mapping(action.get("current_executable_owner_action")).get("work_unit_id"),
            _mapping(action.get("current_work_unit")).get("work_unit_id"),
        ),
        "work_unit_fingerprint": _action_obligation_fingerprint(action),
        "details": _clean_payload(_mapping(details)),
        "typed_control_blocker": _clean_payload(_mapping(typed_control_blocker)),
    }
    return _clean_payload(payload)


def _postcondition_from_outcome(outcome: Mapping[str, Any]) -> dict[str, Any]:
    outcome_kind = _non_empty_text(outcome.get("outcome_kind"))
    return {
        "surface_kind": "dhd_apply_obligation_postcondition",
        "schema_version": 1,
        "ok": bool(outcome.get("postcondition_ok")) is True,
        "exactly_one_outcome": outcome.get("exactly_one_outcome") is True,
        "outcome_kind": outcome_kind,
        "outcome_ref": _non_empty_text(outcome.get(outcome_kind)) if outcome_kind else None,
        "allowed_outcome_kinds": list(_OBLIGATION_ACTUATOR_ALLOWED_OUTCOMES),
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
        _non_empty_text(outcome.get(outcome_kind)) or "",
    )


def _first_text(*values: object) -> str | None:
    for value in values:
        text = _non_empty_text(value)
        if text is not None:
            return text
    return None


def _matching_ref_items(value: object, *, prefix: str) -> list[str]:
    values = value if isinstance(value, list | tuple | set) else [value]
    return [
        text
        for item in values
        if (text := _non_empty_text(item)) is not None and text.startswith(prefix)
    ]


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
    if not value:
        return False
    if value.get("running_provider_attempt") is not True:
        return False
    return any(
        _non_empty_text(ref) is not None
        for ref in (
            value.get("active_stage_attempt_id"),
            value.get("active_run_id"),
            value.get("active_workflow_id"),
            _mapping(value.get("running_attempt")).get("stage_attempt_id"),
            _mapping(value.get("opl_provider_attempt")).get("stage_attempt_id"),
        )
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
    return _first_text(
        _action_recovery_obligation(action).get("work_unit_fingerprint"),
        _mapping(action.get("current_executable_owner_action")).get("work_unit_fingerprint"),
        _mapping(action.get("current_executable_owner_action")).get("action_fingerprint"),
        _mapping(action.get("current_work_unit")).get("work_unit_fingerprint"),
        _mapping(action.get("current_work_unit")).get("action_fingerprint"),
        _mas_owner_callable_action_fingerprint(action),
    )


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


def _apply_mas_owner_callable_actions(
    *,
    report: Mapping[str, Any],
    profile: WorkspaceProfile,
    study_ids: tuple[str, ...],
    seen: set[tuple[str, str, str, str]] | None = None,
) -> list[dict[str, Any]]:
    seen_keys = seen if seen is not None else set()
    explicit_study_ids = {item for item in _text_items(study_ids)}
    results: list[dict[str, Any]] = []
    for action in report.get("managed_study_actions") or []:
        if not isinstance(action, Mapping):
            continue
        study_id = _non_empty_text(action.get("study_id"))
        if study_id is None:
            continue
        if explicit_study_ids and study_id not in explicit_study_ids:
            continue
        owner_callable = _mas_owner_callable_request(action)
        if owner_callable is None:
            continue
        dedupe_key = _mas_owner_callable_request_dedupe_key(
            action=action,
            study_id=study_id,
            owner_callable=owner_callable,
        )
        if dedupe_key in seen_keys:
            continue
        seen_keys.add(dedupe_key)
        result = _run_mas_owner_callable(
            profile=profile,
            study_id=study_id,
            study_root=_study_root_for_owner_callable(action=action, profile=profile, study_id=study_id),
            quest_id=_non_empty_text(action.get("quest_id")) or study_id,
            owner_callable=owner_callable,
        )
        result["work_unit_fingerprint"] = _mas_owner_callable_action_fingerprint(action)
        results.append(result)
    return results


def _mas_owner_callable_request_dedupe_key(
    *,
    action: Mapping[str, Any],
    study_id: str,
    owner_callable: Mapping[str, Any],
) -> tuple[str, str, str, str]:
    return (
        study_id,
        _non_empty_text(owner_callable.get("callable_surface")) or "",
        _non_empty_text(owner_callable.get("action_type")) or "",
        _mas_owner_callable_action_fingerprint(action),
    )


def _mas_owner_callable_action_dedupe_key(
    action: Mapping[str, Any],
) -> tuple[str, str, str, str] | None:
    study_id = _non_empty_text(action.get("study_id"))
    surface = _non_empty_text(action.get("callable_surface"))
    if study_id is None or surface is None:
        return None
    return (
        study_id,
        surface,
        _non_empty_text(action.get("action_type")) or "",
        _non_empty_text(action.get("work_unit_fingerprint")) or "",
    )


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


def _mas_owner_callable_request(action: Mapping[str, Any]) -> dict[str, Any] | None:
    recovery = _mapping(action.get("paper_recovery_state"))
    supervisor_decision = _mapping(recovery.get("supervisor_decision"))
    if _non_empty_text(supervisor_decision.get("decision")) != "materialize_recovery_action":
        return None
    next_safe_action = _mapping(recovery.get("next_safe_action"))
    if _non_empty_text(next_safe_action.get("kind")) != "run_mas_owner_callable":
        return None
    if next_safe_action.get("provider_admission_allowed") is True:
        return None
    owner_callable = _mapping(next_safe_action.get("owner_callable"))
    surface = _non_empty_text(owner_callable.get("callable_surface"))
    if surface not in {
        "gate_clearing_batch.run_gate_clearing_batch",
        "quality_repair_batch.run_quality_repair_batch",
    }:
        return None
    return owner_callable


def _study_root_for_owner_callable(
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


def _run_mas_owner_callable(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    study_root: Path,
    quest_id: str,
    owner_callable: Mapping[str, Any],
) -> dict[str, Any]:
    surface = _non_empty_text(owner_callable.get("callable_surface"))
    if surface == "gate_clearing_batch.run_gate_clearing_batch":
        result = gate_clearing_batch.run_gate_clearing_batch(
            profile=profile,
            study_id=study_id,
            study_root=study_root,
            quest_id=quest_id,
            source="domain_health_diagnostic_mas_owner_callable",
        )
    elif surface == "quality_repair_batch.run_quality_repair_batch":
        result = quality_repair_batch.run_quality_repair_batch(
            profile=profile,
            study_id=study_id,
            study_root=study_root,
            quest_id=quest_id,
            source="domain_health_diagnostic_mas_owner_callable",
        )
    else:
        raise ValueError(f"unsupported MAS owner callable surface: {surface}")
    return {
        "surface_kind": "mas_owner_callable_action",
        "study_id": study_id,
        "quest_id": quest_id,
        "owner": _non_empty_text(owner_callable.get("owner")),
        "action_type": _non_empty_text(owner_callable.get("action_type")),
        "callable_surface": surface,
        "study_root": str(study_root),
        "result": result,
        "ok": bool(_mapping(result).get("ok")),
        "status": _non_empty_text(_mapping(result).get("status")),
        "record_path": _non_empty_text(_mapping(result).get("record_path")),
    }




def _text_items(values: object) -> list[str]:
    return [
        text
        for value in values or []
        if (text := _non_empty_text(value)) is not None
    ]


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}
