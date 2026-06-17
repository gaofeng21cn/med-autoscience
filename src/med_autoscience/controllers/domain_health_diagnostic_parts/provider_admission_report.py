from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from med_autoscience.controllers.domain_health_diagnostic_parts.managed_wakeup import _non_empty_text
from med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission import (
    current_control_provider_admission_candidates,
    candidate_with_authority_boundaries,
    handoff_dispatch_path,
    handoff_work_unit_id,
    study_has_running_provider_attempt,
)
from med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_current_control import (
    materialize_provider_admission_current_control_state,
)
from med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_report_closeout_identity import (
    closeout_evidence_with_identity as _closeout_evidence_with_identity,
    terminal_stage_closeout_evidence as _terminal_stage_closeout_evidence,
)
from med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_report_closeout_scan import (
    study_root_closeout_evidence as _study_root_closeout_evidence,
    with_candidate_root_closeout_scans as _with_candidate_root_closeout_scans,
)
from med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_report_same_tick_identity import (
    same_tick_candidate_matches_current_action as _same_tick_candidate_matches_current_action,
    same_tick_candidate_with_stage_run_identity as _same_tick_candidate_with_stage_run_identity,
    same_tick_progress_current_actions as _same_tick_progress_current_actions,
    same_tick_text_items as _same_tick_text_items,
)
from med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_report_runtime_surfaces import (
    sync_current_control_runtime_surfaces as _sync_current_control_runtime_surfaces,
)
from med_autoscience.controllers.opl_execution_boundary import OPL_EXECUTION_AUTHORIZATION_BLOCKER
from med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_transition_request import (
    candidate_with_opl_transition_request as _candidate_with_opl_transition_request,
)
from med_autoscience.controllers.domain_health_diagnostic_parts.opl_transition_readback import (
    candidate_opl_transition_readback,
)
from med_autoscience.controllers.owner_route_reconcile_parts import supervision_surfaces
from med_autoscience.controllers.owner_route_handoff_parts.accepted_owner_gate_route_back import (
    accepted_owner_gate_route_back_action as _accepted_owner_gate_route_back_action,
)
from med_autoscience.controllers.owner_callable_adapter_projection import domain_progress_transition_requests
from med_autoscience.controllers.owner_callable_adapter_projection import owner_callable_adapters
from med_autoscience.profiles import WorkspaceProfile


def materialize_report_provider_admission_current_control_state(
    *,
    profile: WorkspaceProfile,
    report: Mapping[str, Any],
    apply: bool,
    generated_at: str,
) -> dict[str, Any] | None:
    candidates = _report_provider_admission_candidates(report)
    progress_currentness = _mapping(
        _mapping(report.get("current_execution_evidence")).get("progress_currentness")
    )
    progress_currentness = _progress_currentness_with_report_recovery_states(
        progress_currentness,
        report=report,
    )
    supervisor_tick = _mapping(report.get("developer_supervisor_same_tick"))
    if supervisor_tick.get("stop_reason") == "provider_handoff_written_transition_request_pending":
        terminal_materialize = _mapping(supervisor_tick.get("materialize"))
        if terminal_materialize:
            candidates = _provider_admission_candidates_from_same_tick_materialize(
                materialize_result=terminal_materialize,
                fallback_candidates=candidates,
                progress_currentness=progress_currentness,
                source_kind="same_tick_terminal_handoff",
            )
    preview_materialize = _mapping(report.get("domain_action_request_materialization_preview"))
    if preview_materialize:
        candidates = _merge_provider_admission_candidates(
            candidates,
            _provider_admission_candidates_from_same_tick_materialize(
                materialize_result=preview_materialize,
                fallback_candidates=candidates,
                progress_currentness=progress_currentness,
                source_kind="dry_run_preview",
            ),
        )
    scanned_studies = _provider_admission_scanned_currentness_studies(
        profile=profile,
        progress_currentness=progress_currentness,
        report=report,
    )
    candidates = _filter_provider_admission_candidates_by_progress_currentness(
        candidates,
        progress_currentness=progress_currentness,
        scanned_studies=scanned_studies,
    )
    scanned_studies = _with_candidate_root_closeout_scans(
        profile=profile,
        candidates=candidates,
        scanned_studies=scanned_studies,
    )
    progress_currentness_candidates = _provider_admission_candidates_from_progress_currentness(
        profile=profile,
        progress_currentness=progress_currentness,
        scanned_studies=scanned_studies,
    )
    candidates = _merge_provider_admission_candidates(
        candidates,
        progress_currentness_candidates,
    )
    candidates = _filter_candidates_blocked_by_paper_recovery_state(
        candidates,
        actions=report.get("managed_study_actions"),
        paper_recovery_states=report.get("paper_recovery_states"),
        allow_transition_requests=True,
    )
    scanned_studies = _with_candidate_root_closeout_scans(
        profile=profile,
        candidates=progress_currentness_candidates,
        scanned_studies=scanned_studies,
    )
    return materialize_provider_admission_current_control_state(
        profile=profile,
        candidates=candidates,
        generated_at=generated_at,
        apply=apply,
        scanned_studies=scanned_studies,
    )


def _report_provider_admission_candidates(report: Mapping[str, Any]) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for key in (
        "managed_study_opl_transition_request_candidates",
        "managed_study_opl_provider_admission_candidates",
    ):
        candidates.extend(
            dict(item)
            for item in report.get(key) or []
            if isinstance(item, Mapping)
        )
    return _merge_provider_admission_candidates(candidates)


def sync_report_provider_admission_current_control_state(
    report: dict[str, Any],
    *,
    current_control_state: Mapping[str, Any],
) -> None:
    current_execution_evidence = _mapping(report.get("current_execution_evidence"))
    transition_request_candidates = [
        dict(item)
        for item in current_control_state.get("transition_request_candidates") or []
        if isinstance(item, Mapping)
        and not candidate_opl_transition_readback(item)
    ]
    current_control_provider_candidates = [
        dict(item)
        for item in current_control_state.get("provider_admission_candidates") or []
        if isinstance(item, Mapping)
    ]
    provider_candidate_transition_requests = _transition_request_only_candidates(
        current_control_provider_candidates
    )
    transition_request_candidates.extend(provider_candidate_transition_requests)
    transition_request_candidates = _filter_transition_requests_consumed_by_currentness(
        transition_request_candidates,
        report=report,
    )
    candidates = _filter_candidates_blocked_by_paper_recovery_state(
        [
            dict(item)
            for item in current_control_provider_candidates
            if item not in provider_candidate_transition_requests
        ],
        actions=report.get("managed_study_actions"),
    )
    report["managed_study_opl_provider_admission_candidates"] = candidates
    report["managed_study_opl_transition_request_candidates"] = transition_request_candidates
    report["provider_admission_pending_count"] = len(candidates)
    report["transition_request_pending_count"] = len(transition_request_candidates)
    current_execution_evidence["provider_admission_candidates"] = candidates
    current_execution_evidence["transition_request_candidates"] = transition_request_candidates
    if candidates or transition_request_candidates:
        _sync_current_control_runtime_surfaces(report, current_control_state=current_control_state)
    synced_actions = _sync_managed_action_provider_admission_candidates(
        report.get("managed_study_actions"),
        candidates=candidates,
        transition_request_candidates=transition_request_candidates,
    )
    report["managed_study_actions"] = synced_actions
    if "managed_study_actions" in current_execution_evidence:
        current_execution_evidence["managed_study_actions"] = _sync_managed_action_provider_admission_candidates(
            current_execution_evidence.get("managed_study_actions"),
            candidates=candidates,
            transition_request_candidates=transition_request_candidates,
        )
    report["current_execution_evidence"] = current_execution_evidence
    fingerprints: list[str] = []
    for candidate in [*candidates, *transition_request_candidates]:
        fingerprint = _non_empty_text(candidate.get("work_unit_fingerprint")) or _non_empty_text(
            candidate.get("action_fingerprint")
        )
        if fingerprint is not None and fingerprint not in fingerprints:
            fingerprints.append(fingerprint)
    report["action_fingerprints"] = fingerprints


def _transition_request_only_candidates(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        dict(candidate)
        for candidate in candidates
        if not candidate_opl_transition_readback(candidate)
        and (
            _mapping(candidate.get("opl_domain_progress_transition_request"))
            or _mapping(_mapping(candidate.get("paper_progress_policy_result")).get(
                "opl_domain_progress_transition_request"
            ))
        )
        and candidate.get("provider_admission_requires_opl_runtime_result") is True
    ]


def _filter_transition_requests_consumed_by_currentness(
    candidates: list[dict[str, Any]],
    *,
    report: Mapping[str, Any],
) -> list[dict[str, Any]]:
    if not candidates:
        return []
    currentness_by_study = _transition_consuming_currentness_by_study(report)
    if not currentness_by_study:
        return [dict(candidate) for candidate in candidates]
    filtered: list[dict[str, Any]] = []
    for candidate in candidates:
        study_id = _non_empty_text(candidate.get("study_id"))
        currentness = currentness_by_study.get(study_id or "")
        if currentness and _transition_request_consumed_by_currentness(candidate, currentness):
            continue
        filtered.append(dict(candidate))
    return filtered


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


def _transition_request_consumed_by_currentness(
    candidate: Mapping[str, Any],
    currentness: Mapping[str, Any],
) -> bool:
    if candidate.get("same_tick_materialized_provider_admission") is not True:
        return False
    if _non_empty_text(candidate.get("same_tick_materialization_source")) != "dry_run_preview":
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


def _filter_candidates_blocked_by_paper_recovery_state(
    candidates: list[dict[str, Any]],
    *,
    actions: Any,
    paper_recovery_states: Any = None,
    allow_transition_requests: bool = False,
) -> list[dict[str, Any]]:
    blocked_studies = _paper_recovery_provider_admission_blocked_studies(actions)
    blocked_studies.update(
        _paper_recovery_provider_admission_blocked_studies_from_states(paper_recovery_states)
    )
    blocked_studies.update(_running_provider_attempt_studies(actions))
    if not blocked_studies:
        return candidates
    return [
        dict(item)
        for item in candidates
        if _non_empty_text(item.get("study_id")) not in blocked_studies
        or (allow_transition_requests and not candidate_opl_transition_readback(item))
    ]


def _paper_recovery_provider_admission_blocked_studies(actions: Any) -> set[str]:
    blocked: set[str] = set()
    for action in actions or []:
        if not isinstance(action, Mapping):
            continue
        study_id = _non_empty_text(action.get("study_id"))
        if study_id is None:
            continue
        recovery = _mapping(action.get("paper_recovery_state"))
        if _paper_recovery_blocks_provider_admission(recovery):
            blocked.add(study_id)
    return blocked


def _running_provider_attempt_studies(actions: Any) -> set[str]:
    running: set[str] = set()
    for action in actions or []:
        if not isinstance(action, Mapping):
            continue
        study_id = _non_empty_text(action.get("study_id"))
        if study_id is None:
            continue
        if _action_has_running_provider_attempt(action):
            running.add(study_id)
    return running


def _action_has_running_provider_attempt(action: Mapping[str, Any]) -> bool:
    if study_has_running_provider_attempt(action):
        return True
    envelope = _mapping(action.get("current_execution_envelope"))
    if (
        _non_empty_text(envelope.get("state_kind")) == "running_provider_attempt"
        and _live_worker_liveness(action)
    ):
        return True
    for key in (
        "opl_provider_attempt",
        "provider_attempt_proof",
        "progress_first_monitoring_summary",
    ):
        nested = _mapping(action.get(key))
        if nested and study_has_running_provider_attempt(nested):
            return True
    current_work_unit_state = _mapping(_mapping(action.get("current_work_unit")).get("state"))
    proof = _mapping(current_work_unit_state.get("provider_attempt_proof"))
    if proof and study_has_running_provider_attempt(proof):
        return True
    return False


def _live_worker_liveness(action: Mapping[str, Any]) -> dict[str, Any]:
    runtime_health = _mapping(action.get("runtime_health_snapshot")) or _mapping(
        action.get("runtime_health")
    )
    worker_liveness = _mapping(runtime_health.get("worker_liveness_state")) or _mapping(
        runtime_health.get("worker_liveness")
    )
    if worker_liveness.get("worker_running") is False:
        return {}
    state = _non_empty_text(worker_liveness.get("state"))
    runtime_liveness = _non_empty_text(worker_liveness.get("runtime_liveness_status"))
    if state not in {None, "live", "running"} and runtime_liveness not in {"live", "running"}:
        return {}
    active = (
        _non_empty_text(worker_liveness.get("active_stage_attempt_id"))
        or _non_empty_text(worker_liveness.get("active_run_id"))
        or _non_empty_text(worker_liveness.get("active_workflow_id"))
    )
    return dict(worker_liveness) if active is not None else {}


def _paper_recovery_provider_admission_blocked_studies_from_states(states: Any) -> set[str]:
    blocked: set[str] = set()
    for study_id, recovery in _mapping(states).items():
        normalized_study_id = _non_empty_text(study_id)
        if normalized_study_id is None:
            continue
        if _paper_recovery_blocks_provider_admission(_mapping(recovery)):
            blocked.add(normalized_study_id)
    return blocked


def _paper_recovery_blocks_provider_admission(recovery: Mapping[str, Any]) -> bool:
    next_safe_action = _mapping(recovery.get("next_safe_action"))
    if _non_empty_text(next_safe_action.get("kind")) in {
        "materialize_mas_transition_request_or_owner_callable",
        "materialize_successor_owner_action",
        "materialize_successor_owner_gate",
        "run_mas_owner_callable",
    }:
        return False
    accepted_owner_gate_decision = _mapping(next_safe_action.get("accepted_owner_gate_decision"))
    if next_safe_action.get("provider_admission_allowed") is False and (
        _non_empty_text(next_safe_action.get("kind")),
        _non_empty_text(accepted_owner_gate_decision.get("decision")),
    ) == ("route_back_to_owner_or_repair_materialization", "route_back_to_mas_packet_materialization_bug"):
        return True
    suppressed = {
        item
        for item in recovery.get("suppressed_surfaces") or []
        if isinstance(item, str)
    }
    return (
        _non_empty_text(recovery.get("phase")) == "domain_blocked"
        and next_safe_action.get("provider_admission_allowed") is False
        and "provider_admission_candidates" in suppressed
    )


def _sync_managed_action_provider_admission_candidates(
    actions: Any,
    *,
    candidates: list[dict[str, Any]],
    transition_request_candidates: list[dict[str, Any]] | None = None,
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


def _provider_admission_scanned_currentness_studies(
    *,
    profile: WorkspaceProfile,
    progress_currentness: Mapping[str, Any] | None,
    report: Mapping[str, Any] | None = None,
) -> list[dict[str, Any]]:
    studies: list[dict[str, Any]] = []
    seen_study_ids: set[str] = set()
    for study_id, payload in _mapping(progress_currentness).items():
        normalized_study_id = _non_empty_text(study_id)
        if normalized_study_id is None:
            continue
        progress_payload = _mapping(payload)
        progress_payload = _progress_payload_with_owner_gate_route_back_action(progress_payload)
        current_action = _mapping(progress_payload.get("current_executable_owner_action"))
        current_work_unit = _mapping(progress_payload.get("current_work_unit"))
        current_owner_ticket = _mapping(progress_payload.get("current_owner_ticket"))
        current_execution_envelope = _mapping(progress_payload.get("current_execution_envelope"))
        domain_transition = _mapping(progress_payload.get("domain_transition"))
        paper_recovery_state = _mapping(progress_payload.get("paper_recovery_state"))
        progress_first_monitoring_summary = _mapping(
            progress_payload.get("progress_first_monitoring_summary")
        )
        intervention_lane = _mapping(progress_payload.get("intervention_lane"))
        running_provider_attempt = _running_provider_attempt_projection(progress_payload)
        identity = _progress_currentness_current_identity(progress_payload)
        closeout_evidence = _progress_currentness_closeout_evidence(
            progress_payload,
            identity=identity,
        )
        closeout_evidence.extend(
            _study_root_closeout_evidence(
                study_root=Path(profile.studies_root) / normalized_study_id,
                identity=identity,
            )
        )
        if not any((current_action, current_work_unit, current_execution_envelope, closeout_evidence)):
            continue
        next_owner = _non_empty_text(current_action.get("next_owner"))
        work_unit_id = _non_empty_text(current_action.get("work_unit_id")) or _non_empty_text(
            current_work_unit.get("work_unit_id")
        )
        execution_envelope = (
            dict(running_provider_attempt)
            if running_provider_attempt
            else dict(current_execution_envelope)
            if current_execution_envelope
            else {
            "state_kind": "executable_owner_action",
            "owner": next_owner,
            "next_work_unit": work_unit_id,
            "typed_blocker": None,
            "parked_state": None,
            "source": "progress_currentness.current_executable_owner_action",
        }
        )
        studies.append(
            {
                "study_id": normalized_study_id,
                "quest_id": _non_empty_text(current_action.get("quest_id"))
                or _non_empty_text(current_work_unit.get("quest_id"))
                or normalized_study_id,
                "handoff_scan_status": "scanned_no_provider_admission",
                "provider_admission_pending_count": 0,
                "action_queue": [],
                **({"current_executable_owner_action": dict(current_action)} if current_action else {}),
                **({"current_work_unit": dict(current_work_unit)} if current_work_unit else {}),
                **({"current_owner_ticket": dict(current_owner_ticket)} if current_owner_ticket else {}),
                **({"domain_transition": dict(domain_transition)} if domain_transition else {}),
                **({"paper_recovery_state": dict(paper_recovery_state)} if paper_recovery_state else {}),
                **({"progress_first_monitoring_summary": dict(progress_first_monitoring_summary)}
                   if progress_first_monitoring_summary else {}),
                **({"intervention_lane": dict(intervention_lane)} if intervention_lane else {}),
                **({"accepted_closeout_evidence": closeout_evidence} if closeout_evidence else {}),
                **_running_provider_attempt_study_fields(running_provider_attempt),
                "current_execution_envelope": execution_envelope,
            }
        )
        seen_study_ids.add(normalized_study_id)
    studies.extend(
        _provider_admission_scanned_report_studies(
            report=report,
            seen_study_ids=seen_study_ids,
        )
    )
    return studies


def _provider_admission_scanned_report_studies(
    *,
    report: Mapping[str, Any] | None,
    seen_study_ids: set[str],
) -> list[dict[str, Any]]:
    studies: list[dict[str, Any]] = []
    for item in _mapping(report).get("managed_study_actions") or []:
        study = _mapping(item)
        study_id = _non_empty_text(study.get("study_id"))
        if study_id is None or study_id in seen_study_ids:
            continue
        current_work_unit = _mapping(study.get("current_work_unit"))
        current_action = _mapping(study.get("current_executable_owner_action"))
        current_execution_envelope = _mapping(study.get("current_execution_envelope"))
        paper_recovery_state = _mapping(study.get("paper_recovery_state"))
        if not any((current_work_unit, current_action, current_execution_envelope)):
            continue
        work_unit_id = _non_empty_text(current_action.get("work_unit_id")) or _non_empty_text(
            current_work_unit.get("work_unit_id")
        )
        next_owner = _non_empty_text(current_action.get("next_owner")) or _non_empty_text(
            current_work_unit.get("owner")
        )
        fallback_envelope = {
            "state_kind": _non_empty_text(current_work_unit.get("status")) or "parked",
            "owner": next_owner,
            "next_work_unit": work_unit_id if current_action else None,
            "typed_blocker": _mapping(_mapping(current_work_unit.get("state")).get("typed_blocker"))
            or _mapping(current_work_unit.get("typed_blocker"))
            or None,
            "parked_state": None,
            "source": "domain_health_diagnostic.managed_study_actions",
        }
        studies.append(
            {
                "study_id": study_id,
                "quest_id": _non_empty_text(study.get("quest_id")) or study_id,
                "handoff_scan_status": "scanned_no_provider_admission",
                "provider_admission_pending_count": 0,
                "running_provider_attempt": bool(study.get("running_provider_attempt")) is True,
                "action_queue": [],
                **({"current_executable_owner_action": dict(current_action)} if current_action else {}),
                **({"current_work_unit": dict(current_work_unit)} if current_work_unit else {}),
                **({"paper_recovery_state": dict(paper_recovery_state)} if paper_recovery_state else {}),
                "current_execution_envelope": dict(current_execution_envelope) if current_execution_envelope else fallback_envelope,
            }
        )
    return studies


def _progress_currentness_with_report_recovery_states(
    progress_currentness: Mapping[str, Any] | None,
    *,
    report: Mapping[str, Any] | None,
) -> dict[str, Any]:
    merged = {
        study_id: dict(payload)
        for study_id, payload in _mapping(progress_currentness).items()
        if isinstance(payload, Mapping)
    }
    for study_id, recovery in _report_paper_recovery_states(report).items():
        if _mapping(merged.get(study_id)).get("paper_recovery_state"):
            continue
        merged[study_id] = {
            **_mapping(merged.get(study_id)),
            "study_id": study_id,
            "paper_recovery_state": dict(recovery),
        }
    return merged


def _report_paper_recovery_states(
    report: Mapping[str, Any] | None,
) -> dict[str, dict[str, Any]]:
    states: dict[str, dict[str, Any]] = {}
    for study_id, recovery in _mapping(_mapping(report).get("paper_recovery_states")).items():
        normalized_study_id = _non_empty_text(study_id)
        recovery_payload = _mapping(recovery)
        if normalized_study_id is not None and recovery_payload:
            states[normalized_study_id] = dict(recovery_payload)
    for action in _mapping(report).get("managed_study_actions") or []:
        action_payload = _mapping(action)
        study_id = _non_empty_text(action_payload.get("study_id"))
        recovery = _mapping(action_payload.get("paper_recovery_state"))
        if study_id is not None and recovery and study_id not in states:
            states[study_id] = dict(recovery)
    return states


def _progress_currentness_closeout_evidence(
    payload: Mapping[str, Any],
    *,
    identity: Mapping[str, Any] | None = None,
) -> list[dict[str, Any]]:
    evidence: list[dict[str, Any]] = []
    identity = _mapping(identity) or _progress_currentness_current_identity(payload)
    for key in (
        "default_executor_execution_receipt_consumption",
        "terminal_closeout_precedence_evidence",
        "latest_stage_attempt_closeout",
        "stage_attempt_closeout",
    ):
        item = _mapping(payload.get(key))
        if item:
            evidence.append(_closeout_evidence_with_identity(item, identity=identity))
    progress_first = _mapping(payload.get("progress_first_monitoring_summary"))
    for key in ("latest_terminal_stage", "latest_terminal_stage_log"):
        item = _mapping(progress_first.get(key))
        if item:
            evidence.append(_terminal_stage_closeout_evidence(item, identity=identity))
    for key in (
        "accepted_closeout_evidence",
        "stage_attempt_closeouts",
        "default_executor_execution_receipt_consumptions",
    ):
        for item in payload.get(key) or []:
            mapped = _mapping(item)
            if mapped:
                evidence.append(_closeout_evidence_with_identity(mapped, identity=identity))
    return evidence


def _progress_currentness_current_identity(payload: Mapping[str, Any]) -> dict[str, Any]:
    current_work_unit = _mapping(payload.get("current_work_unit"))
    current_action = _mapping(payload.get("current_executable_owner_action"))
    current_action_basis = _mapping(current_action.get("owner_route_currentness_basis")) or _mapping(
        current_action.get("currentness_basis")
    )
    current_work_unit_basis = _mapping(current_work_unit.get("currentness_basis"))
    currentness_basis = current_action_basis or current_work_unit_basis
    next_forced_delta = _mapping(payload.get("next_forced_delta"))
    owner_action = _mapping(next_forced_delta.get("owner_action"))
    current_owner_ticket = _mapping(next_forced_delta.get("current_owner_ticket")) or _mapping(
        payload.get("current_owner_ticket")
    )
    ticket_work_unit = _mapping(current_owner_ticket.get("work_unit"))
    allowed_actions = _same_tick_text_items(current_action.get("allowed_actions")) or _same_tick_text_items(
        owner_action.get("allowed_actions")
    )
    action_type = (
        _non_empty_text(current_action.get("action_type"))
        or _non_empty_text(current_work_unit.get("action_type"))
        or _non_empty_text(owner_action.get("action_type"))
        or (allowed_actions[0] if len(allowed_actions) == 1 else None)
    )
    work_unit_id = (
        _non_empty_text(current_action.get("work_unit_id"))
        or _non_empty_text(current_work_unit.get("work_unit_id"))
        or _non_empty_text(owner_action.get("work_unit_id"))
        or _non_empty_text(next_forced_delta.get("work_unit_id"))
        or _non_empty_text(ticket_work_unit.get("work_unit_id"))
        or _non_empty_text(ticket_work_unit.get("unit_id"))
    )
    fingerprint = (
        _non_empty_text(current_action.get("work_unit_fingerprint"))
        or _non_empty_text(current_action.get("action_fingerprint"))
        or _non_empty_text(current_work_unit.get("work_unit_fingerprint"))
        or _non_empty_text(current_work_unit.get("action_fingerprint"))
        or _non_empty_text(currentness_basis.get("work_unit_fingerprint"))
    )
    return {
        key: value
        for key, value in {
            "action_type": action_type,
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": fingerprint,
            "action_fingerprint": fingerprint,
            "source_eval_id": _non_empty_text(current_action.get("source_eval_id"))
            or _non_empty_text(currentness_basis.get("source_eval_id")),
            "truth_epoch": _non_empty_text(currentness_basis.get("truth_epoch")),
            "runtime_health_epoch": _non_empty_text(currentness_basis.get("runtime_health_epoch")),
        }.items()
        if value not in (None, "", [], {})
    }


def _provider_admission_candidates_from_progress_currentness(
    *,
    profile: WorkspaceProfile,
    progress_currentness: Mapping[str, Any] | None,
    scanned_studies: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if not scanned_studies:
        return []
    current_control_ref = str(supervision_surfaces.latest_path(profile))
    candidates: list[dict[str, Any]] = []
    progress_by_study = _mapping(progress_currentness)
    for study in scanned_studies:
        study_id = _non_empty_text(study.get("study_id"))
        if study_id is None:
            continue
        if study.get("running_provider_attempt") is True:
            continue
        study_root = Path(profile.studies_root) / study_id
        status_payload = {
            "study_id": study_id,
            "quest_id": _non_empty_text(study.get("quest_id")) or study_id,
            "study_root": str(study_root),
            **_mapping(progress_by_study.get(study_id)),
        }
        status_payload = _progress_payload_with_owner_gate_route_back_action(status_payload)
        current_work_unit = _mapping(status_payload.get("current_work_unit"))
        if current_work_unit and _non_empty_text(current_work_unit.get("study_id")) is None:
            status_payload["current_work_unit"] = {
                **current_work_unit,
                "study_id": study_id,
            }
        if not _mapping(status_payload.get("current_executable_owner_action")):
            current_action = _mapping(study.get("current_executable_owner_action"))
            if current_action:
                status_payload["current_executable_owner_action"] = current_action
        if not _mapping(status_payload.get("current_execution_envelope")):
            envelope = _mapping(study.get("current_execution_envelope"))
            if envelope:
                status_payload["current_execution_envelope"] = envelope
        candidates.extend(
            _explicit_provider_admission_candidates_from_progress_currentness(
                status_payload,
                source="dhd.provider_admission_progress_currentness",
            )
        )
        candidates.extend(
            current_control_provider_admission_candidates(
                {
                    "surface": "opl_current_control_state_handoff",
                    "schema_version": 1,
                    "studies": [dict(study)],
                    "action_queue": [],
                },
                study_root=study_root,
                status_payload=status_payload,
                current_control_ref=current_control_ref,
            )
        )
    return candidates


def _explicit_provider_admission_candidates_from_progress_currentness(
    progress_payload: Mapping[str, Any],
    *,
    source: str,
) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for key in ("transition_request_candidates", "provider_admission_candidates"):
        for item in progress_payload.get(key) or []:
            if not isinstance(item, Mapping):
                continue
            enriched = {
                **dict(item),
                **(
                    {
                        "current_execution_envelope": dict(
                            _mapping(progress_payload.get("current_execution_envelope"))
                        )
                    }
                    if _mapping(progress_payload.get("current_execution_envelope"))
                    else {}
                ),
            }
            candidate = _candidate_with_opl_transition_request(
                enriched,
                source=source,
                current_action_source=_non_empty_text(item.get("source")) or "progress_currentness",
            )
            candidates.append(candidate_with_authority_boundaries(candidate))
    return candidates


def _running_provider_attempt_projection(payload: Mapping[str, Any]) -> dict[str, Any]:
    envelope = _mapping(payload.get("current_execution_envelope"))
    if _non_empty_text(envelope.get("state_kind")) == "running_provider_attempt":
        return dict(envelope)
    current_work_unit = _mapping(payload.get("current_work_unit"))
    if _non_empty_text(current_work_unit.get("status")) == "running_provider_attempt":
        state = _mapping(current_work_unit.get("state"))
        proof = _mapping(state.get("provider_attempt_proof"))
        return {
            "state_kind": "running_provider_attempt",
            "owner": _non_empty_text(current_work_unit.get("owner")),
            "next_work_unit": _non_empty_text(current_work_unit.get("work_unit_id")),
            "typed_blocker": None,
            "parked_state": None,
            "source": _non_empty_text(state.get("source")) or "progress_currentness.current_work_unit",
            **({"provider_attempt_proof": proof} if proof else {}),
        }
    return {}


def _running_provider_attempt_study_fields(envelope: Mapping[str, Any]) -> dict[str, Any]:
    if not envelope:
        return {}
    proof = _mapping(envelope.get("provider_attempt_proof"))
    return {
        key: value
        for key, value in {
            "running_provider_attempt": True,
            "active_run_id": _non_empty_text(envelope.get("active_run_id"))
            or _non_empty_text(proof.get("active_run_id")),
            "active_stage_attempt_id": _non_empty_text(envelope.get("active_stage_attempt_id"))
            or _non_empty_text(proof.get("active_stage_attempt_id")),
            "active_workflow_id": _non_empty_text(envelope.get("active_workflow_id"))
            or _non_empty_text(proof.get("active_workflow_id")),
            "runtime_health": _mapping(envelope.get("runtime_health")) or _mapping(proof.get("runtime_health")),
            "opl_provider_attempt": _mapping(envelope.get("opl_provider_attempt")) or proof,
        }.items()
        if value not in (None, "", {}, [])
    }


def _progress_payload_with_owner_gate_route_back_action(
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    current_work_unit = _mapping(payload.get("current_work_unit"))
    owner_gate_action = _accepted_owner_gate_route_back_action(
        current_progress=payload,
        current_work_unit=current_work_unit,
    )
    if not owner_gate_action:
        return dict(payload)
    return {
        **dict(payload),
        "current_executable_owner_action": dict(owner_gate_action),
    }


def _merge_provider_admission_candidates(
    *candidate_groups: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    merged: list[dict[str, Any]] = []
    index_by_key: dict[tuple[str | None, str | None, str | None, str | None], int] = {}
    for group in candidate_groups:
        for candidate in group:
            key = (
                _non_empty_text(candidate.get("study_id")),
                _non_empty_text(candidate.get("action_type")),
                _non_empty_text(candidate.get("work_unit_id")),
                _non_empty_text(candidate.get("dispatch_path")),
            )
            if key in index_by_key:
                existing_index = index_by_key[key]
                existing = merged[existing_index]
                if _provider_admission_identity_rank(candidate) > _provider_admission_identity_rank(existing):
                    merged[existing_index] = _merge_provider_admission_candidate_payloads(
                        existing,
                        candidate,
                    )
                else:
                    merged[existing_index] = _merge_provider_admission_candidate_payloads(
                        candidate,
                        existing,
                    )
                continue
            index_by_key[key] = len(merged)
            merged.append(dict(candidate))
    return merged


def _merge_provider_admission_candidate_payloads(
    weaker: Mapping[str, Any],
    stronger: Mapping[str, Any],
) -> dict[str, Any]:
    merged = {
        **dict(weaker),
        **dict(stronger),
        **{
            key: dict(value)
            for key in (
                "current_execution_envelope",
                "paper_progress_policy_result",
                "opl_domain_progress_transition_request",
                "projection_metadata",
                "authority_boundary",
                "stage_transition_authority_boundary",
            )
            if isinstance((value := stronger.get(key)), Mapping)
        },
    }
    for key, value in weaker.items():
        if merged.get(key) in (None, "", [], {}):
            merged[key] = value
    return merged


def _provider_admission_identity_rank(candidate: Mapping[str, Any]) -> tuple[int, int, int]:
    stage_packet_refs = [
        item
        for item in candidate.get("stage_packet_refs") or []
        if _non_empty_text(item) is not None
    ]
    has_stage_packet_identity = int(
        _non_empty_text(candidate.get("stage_packet_ref")) is not None
        or bool(stage_packet_refs)
    )
    has_route_identity = int(
        _non_empty_text(candidate.get("route_identity_key")) is not None
        and _non_empty_text(candidate.get("attempt_idempotency_key")) is not None
    )
    basis = _mapping(candidate.get("currentness_basis"))
    has_currentness_basis = int(
        _non_empty_text(basis.get("work_unit_id")) is not None
        and _non_empty_text(basis.get("work_unit_fingerprint")) is not None
        and _non_empty_text(basis.get("truth_epoch")) is not None
        and (
            _non_empty_text(basis.get("runtime_health_epoch")) is not None
            or _non_empty_text(basis.get("source_eval_id")) is not None
        )
    )
    return (has_stage_packet_identity, has_route_identity, has_currentness_basis)


def _filter_provider_admission_candidates_by_progress_currentness(
    candidates: list[dict[str, Any]],
    *,
    progress_currentness: Mapping[str, Any] | None,
    scanned_studies: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    current_action_by_study = _same_tick_progress_current_actions(progress_currentness)
    if not current_action_by_study:
        return [dict(candidate) for candidate in candidates]
    filtered: list[dict[str, Any]] = []
    for candidate in candidates:
        study_id = _non_empty_text(candidate.get("study_id"))
        current_action_identity = current_action_by_study.get(study_id) if study_id is not None else None
        if current_action_identity is not None and not _same_tick_candidate_matches_current_action(
            candidate,
            current_action_identity=current_action_identity,
        ):
            continue
        filtered.append(
            _candidate_with_current_action_identity(
                candidate,
                current_action_identity=current_action_identity,
            )
        )
    return filtered


def _scanned_study_ids_without_provider_admission(
    scanned_studies: list[dict[str, Any]] | None,
) -> set[str]:
    blocked: set[str] = set()
    for study in scanned_studies or []:
        study_id = _non_empty_text(study.get("study_id"))
        if study_id is None:
            continue
        if _mapping(study.get("current_executable_owner_action")):
            continue
        if study.get("provider_admission_pending_count", 0) > 0 or study.get("provider_admission_candidates"):
            continue
        current_work_unit = _mapping(study.get("current_work_unit"))
        envelope = _mapping(study.get("current_execution_envelope"))
        if _non_empty_text(current_work_unit.get("status")) == "typed_blocker":
            blocked.add(study_id)
            continue
        if _non_empty_text(envelope.get("state_kind")) == "typed_blocker":
            blocked.add(study_id)
    return blocked


def _provider_admission_candidates_from_same_tick_materialize(
    *,
    materialize_result: Mapping[str, Any],
    fallback_candidates: list[dict[str, Any]],
    progress_currentness: Mapping[str, Any] | None = None,
    source_kind: str = "same_tick_terminal_handoff",
) -> list[dict[str, Any]]:
    fallback_by_identity = {
        (_non_empty_text(candidate.get("study_id")), _non_empty_text(candidate.get("action_type"))): candidate
        for candidate in fallback_candidates
    }
    current_action_by_study = _same_tick_progress_current_actions(progress_currentness)
    candidates: list[dict[str, Any]] = []
    for dispatch in _same_tick_transition_request_dispatches(materialize_result):
        if not isinstance(dispatch, Mapping):
            continue
        if _non_empty_text(dispatch.get("dispatch_status")) not in {"ready", "transition_request_pending"}:
            continue
        study_id = _non_empty_text(dispatch.get("study_id"))
        action_type = _non_empty_text(dispatch.get("action_type"))
        base = dict(fallback_by_identity.get((study_id, action_type), {}))
        dispatch_refs = _mapping(dispatch.get("refs"))
        stage_packet_ref = (
            _non_empty_text(dispatch.get("stage_packet_ref"))
            or _non_empty_text(dispatch_refs.get("stage_packet_ref"))
            or _non_empty_text(dispatch_refs.get("stage_packet_path"))
            or _non_empty_text(dispatch_refs.get("immutable_dispatch_path"))
            or _non_empty_text(base.get("stage_packet_ref"))
        )
        stage_packet_refs = _same_tick_text_items(dispatch.get("stage_packet_refs")) or _same_tick_text_items(
            dispatch_refs.get("stage_packet_refs")
        ) or _same_tick_text_items(
            base.get("stage_packet_refs")
        )
        if stage_packet_ref is not None and stage_packet_ref not in stage_packet_refs:
            stage_packet_refs.append(stage_packet_ref)
        candidate = {
            **base,
            "surface": "opl_provider_admission_candidate",
            "schema_version": 1,
            "status": "transition_request_pending",
            "dispatch_status": _non_empty_text(dispatch.get("dispatch_status"))
            or _non_empty_text(base.get("dispatch_status")),
            "source": _non_empty_text(base.get("source")) or "same_tick_materialized_dispatch",
            "study_id": study_id,
            "quest_id": _non_empty_text(dispatch.get("quest_id")) or _non_empty_text(base.get("quest_id")),
            "action_type": action_type,
            "work_unit_id": _non_empty_text(dispatch.get("work_unit_id"))
            or _non_empty_text(base.get("work_unit_id"))
            or handoff_work_unit_id(dispatch),
            "work_unit_fingerprint": _non_empty_text(dispatch.get("work_unit_fingerprint"))
            or _non_empty_text(dispatch.get("action_fingerprint"))
            or _non_empty_text(base.get("work_unit_fingerprint")),
            "action_fingerprint": _non_empty_text(dispatch.get("action_fingerprint"))
            or _non_empty_text(dispatch.get("work_unit_fingerprint"))
            or _non_empty_text(base.get("action_fingerprint")),
            "dispatch_path": _non_empty_text(dispatch.get("dispatch_path"))
            or _non_empty_text(base.get("dispatch_path"))
            or handoff_dispatch_path(dispatch),
            "stage_packet_ref": stage_packet_ref,
            "stage_packet_refs": stage_packet_refs or None,
            "dispatch_authority": _non_empty_text(dispatch.get("dispatch_authority"))
            or _non_empty_text(base.get("dispatch_authority")),
            "blocked_reason": OPL_EXECUTION_AUTHORIZATION_BLOCKER,
            "next_executable_owner": _non_empty_text(dispatch.get("next_executable_owner"))
            or _non_empty_text(base.get("next_executable_owner")),
            "required_output_surface": _non_empty_text(dispatch.get("required_output_surface"))
            or _non_empty_text(base.get("required_output_surface")),
            "provider_attempt_or_lease_required": False,
            "opl_transition_runtime_required": True,
            "provider_admission_pending": False,
            "provider_admission_requires_opl_runtime_result": True,
            "provider_completion_is_domain_completion": False,
            "owner_route_current": True,
            "same_tick_materialized_provider_admission": True,
            "same_tick_materialization_source": source_kind,
        }
        currentness_basis = _same_tick_materialized_currentness_basis(
            candidate,
            base=base,
            materialize_result=materialize_result,
        )
        if currentness_basis:
            candidate["currentness_basis"] = currentness_basis
        candidate = _same_tick_candidate_with_stage_run_identity(candidate)
        candidate = _candidate_with_opl_transition_request(
            candidate,
            source="dhd.provider_admission_same_tick_materialized_dispatch",
            current_action_source="same_tick_materialized_dispatch",
        )
        if candidate["study_id"] is not None and candidate["action_type"] is not None:
            current_action_identity = current_action_by_study.get(candidate["study_id"])
            if current_action_identity is not None and not _same_tick_candidate_matches_current_action(
                candidate,
                current_action_identity=current_action_identity,
            ):
                continue
            candidate = _candidate_with_current_action_identity(
                candidate,
                current_action_identity=current_action_identity,
            )
            candidates.append(
                candidate_with_authority_boundaries(
                    {key: value for key, value in candidate.items() if value is not None}
                )
            )
    return candidates


def _same_tick_transition_request_dispatches(
    materialize_result: Mapping[str, Any],
) -> list[dict[str, Any]]:
    dispatches = domain_progress_transition_requests(materialize_result)
    if dispatches:
        return dispatches
    return [
        dict(item)
        for item in owner_callable_adapters(materialize_result)
        if isinstance(item, Mapping)
    ]


def _candidate_with_current_action_identity(
    candidate: Mapping[str, Any],
    *,
    current_action_identity: Mapping[str, Any] | None,
) -> dict[str, Any]:
    payload = dict(candidate)
    if not current_action_identity:
        return payload
    fingerprint = _non_empty_text(payload.get("work_unit_fingerprint")) or _non_empty_text(
        payload.get("action_fingerprint")
    )
    if fingerprint is None:
        return payload
    if _non_empty_text(payload.get("route_identity_key")) is None:
        study_id = _non_empty_text(payload.get("study_id"))
        if study_id is not None:
            payload["route_identity_key"] = f"provider-admission::{study_id}::{fingerprint}"
    if _non_empty_text(payload.get("attempt_idempotency_key")) is None and _non_empty_text(
        payload.get("route_identity_key")
    ) is not None:
        payload["attempt_idempotency_key"] = _non_empty_text(payload.get("route_identity_key"))
    currentness_basis = _mapping(payload.get("currentness_basis"))
    current_basis = _mapping(current_action_identity.get("currentness_basis"))
    if current_basis:
        payload["currentness_basis"] = {
            **dict(currentness_basis),
            **dict(current_basis),
            "work_unit_id": _non_empty_text(currentness_basis.get("work_unit_id"))
            or _non_empty_text(current_action_identity.get("work_unit_id"))
            or _non_empty_text(payload.get("work_unit_id")),
            "work_unit_fingerprint": _non_empty_text(currentness_basis.get("work_unit_fingerprint"))
            or fingerprint,
            "source_eval_id": _non_empty_text(currentness_basis.get("source_eval_id"))
            or _non_empty_text(current_basis.get("source_eval_id")),
        }
    return payload


def _same_tick_materialized_currentness_basis(
    candidate: Mapping[str, Any],
    *,
    base: Mapping[str, Any],
    materialize_result: Mapping[str, Any],
) -> dict[str, Any]:
    base_basis = _mapping(base.get("currentness_basis"))
    work_unit_id = _non_empty_text(candidate.get("work_unit_id"))
    fingerprint = _non_empty_text(candidate.get("work_unit_fingerprint")) or _non_empty_text(
        candidate.get("action_fingerprint")
    )
    if work_unit_id is None or fingerprint is None:
        return dict(base_basis)
    generated_at = (
        _non_empty_text(base_basis.get("truth_epoch"))
        or _non_empty_text(materialize_result.get("generated_at"))
        or _non_empty_text(materialize_result.get("scanned_at"))
        or fingerprint
    )
    runtime_epoch = (
        _non_empty_text(base_basis.get("runtime_health_epoch"))
        or _non_empty_text(materialize_result.get("runtime_health_epoch"))
        or generated_at
    )
    basis = {
        **dict(base_basis),
        "work_unit_id": _non_empty_text(base_basis.get("work_unit_id")) or work_unit_id,
        "work_unit_fingerprint": _non_empty_text(base_basis.get("work_unit_fingerprint")) or fingerprint,
        "truth_epoch": generated_at,
        "runtime_health_epoch": runtime_epoch,
        "admission_identity_source": "same_tick_materialized_dispatch",
    }
    source_eval_id = _non_empty_text(base_basis.get("source_eval_id")) or _non_empty_text(
        candidate.get("source_eval_id")
    )
    if source_eval_id is not None:
        basis["source_eval_id"] = source_eval_id
    return {key: value for key, value in basis.items() if value not in (None, "", [], {})}


def _same_tick_materialized_candidate(candidate: Mapping[str, Any]) -> bool:
    if candidate.get("same_tick_materialized_provider_admission") is True:
        return True
    return _non_empty_text(candidate.get("source")) == "same_tick_materialized_dispatch"


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _mapping_list(value: object) -> list[dict[str, Any]]:
    return [dict(item) for item in value or [] if isinstance(item, Mapping)]


__all__ = [
    "materialize_report_provider_admission_current_control_state",
    "sync_report_provider_admission_current_control_state",
]
