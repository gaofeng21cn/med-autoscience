from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from med_autoscience.controllers.domain_health_diagnostic_parts.managed_wakeup import _non_empty_text
from med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission import (
    _study_current_action_for_provider_admission,
    current_control_provider_admission_candidates,
    handoff_dispatch_path,
    handoff_work_unit_id,
)
from med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_current_control import (
    materialize_provider_admission_current_control_state,
)
from med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_report_closeout_identity import (
    closeout_evidence_with_identity as _closeout_evidence_with_identity,
    closeout_identity_matches_current as _closeout_identity_matches_current,
    terminal_stage_closeout_evidence as _terminal_stage_closeout_evidence,
)
from med_autoscience.controllers.opl_execution_boundary import OPL_EXECUTION_AUTHORIZATION_BLOCKER
from med_autoscience.controllers.owner_route_reconcile_parts import supervision_surfaces
from med_autoscience.controllers.study_transition_receipt_consumption_parts.default_executor_candidates import (
    default_executor_execution_candidates,
)
from med_autoscience.profiles import WorkspaceProfile


def materialize_report_provider_admission_current_control_state(
    *,
    profile: WorkspaceProfile,
    report: Mapping[str, Any],
    apply: bool,
    generated_at: str,
) -> dict[str, Any] | None:
    candidates = [
        dict(item)
        for item in report.get("managed_study_opl_provider_admission_candidates") or []
        if isinstance(item, Mapping)
    ]
    progress_currentness = _mapping(
        _mapping(report.get("current_execution_evidence")).get("progress_currentness")
    )
    supervisor_tick = _mapping(report.get("developer_supervisor_same_tick"))
    if supervisor_tick.get("stop_reason") == "provider_handoff_written_admission_pending":
        terminal_materialize = _mapping(supervisor_tick.get("materialize"))
        if terminal_materialize:
            candidates = _provider_admission_candidates_from_same_tick_materialize(
                materialize_result=terminal_materialize,
                fallback_candidates=candidates,
                progress_currentness=progress_currentness,
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


def sync_report_provider_admission_current_control_state(
    report: dict[str, Any],
    *,
    current_control_state: Mapping[str, Any],
) -> None:
    current_execution_evidence = _mapping(report.get("current_execution_evidence"))
    candidates = _filter_candidates_blocked_by_paper_recovery_state(
        [
            dict(item)
            for item in current_control_state.get("provider_admission_candidates") or []
            if isinstance(item, Mapping)
        ],
        actions=report.get("managed_study_actions"),
    )
    report["managed_study_opl_provider_admission_candidates"] = candidates
    report["provider_admission_pending_count"] = len(candidates)
    current_execution_evidence["provider_admission_candidates"] = candidates
    synced_actions = _sync_managed_action_provider_admission_candidates(
        report.get("managed_study_actions"),
        candidates=candidates,
    )
    report["managed_study_actions"] = synced_actions
    if "managed_study_actions" in current_execution_evidence:
        current_execution_evidence["managed_study_actions"] = _sync_managed_action_provider_admission_candidates(
            current_execution_evidence.get("managed_study_actions"),
            candidates=candidates,
        )
    report["current_execution_evidence"] = current_execution_evidence
    fingerprints: list[str] = []
    for candidate in candidates:
        fingerprint = _non_empty_text(candidate.get("work_unit_fingerprint")) or _non_empty_text(
            candidate.get("action_fingerprint")
        )
        if fingerprint is not None and fingerprint not in fingerprints:
            fingerprints.append(fingerprint)
    report["action_fingerprints"] = fingerprints


def _filter_candidates_blocked_by_paper_recovery_state(
    candidates: list[dict[str, Any]],
    *,
    actions: Any,
    paper_recovery_states: Any = None,
) -> list[dict[str, Any]]:
    blocked_studies = _paper_recovery_provider_admission_blocked_studies(actions)
    blocked_studies.update(
        _paper_recovery_provider_admission_blocked_studies_from_states(paper_recovery_states)
    )
    if not blocked_studies:
        return candidates
    return [
        dict(item)
        for item in candidates
        if _non_empty_text(item.get("study_id")) not in blocked_studies
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
) -> list[Any]:
    candidates_by_study: dict[str, list[dict[str, Any]]] = {}
    for candidate in candidates:
        study_id = _non_empty_text(candidate.get("study_id"))
        if study_id is None:
            continue
        candidates_by_study.setdefault(study_id, []).append(dict(candidate))
    synced_actions: list[Any] = []
    for action in actions or []:
        if not isinstance(action, Mapping):
            synced_actions.append(action)
            continue
        synced_action = dict(action)
        study_id = _non_empty_text(synced_action.get("study_id"))
        action_candidates = candidates_by_study.get(study_id or "", [])
        synced_action["provider_admission_candidates"] = [dict(candidate) for candidate in action_candidates]
        if not action_candidates:
            synced_action.pop("provider_admission_state", None)
            synced_actions.append(synced_action)
            continue
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
        current_action = _mapping(progress_payload.get("current_executable_owner_action"))
        current_work_unit = _mapping(progress_payload.get("current_work_unit"))
        current_owner_ticket = _mapping(progress_payload.get("current_owner_ticket"))
        current_execution_envelope = _mapping(progress_payload.get("current_execution_envelope"))
        domain_transition = _mapping(progress_payload.get("domain_transition"))
        progress_first_monitoring_summary = _mapping(
            progress_payload.get("progress_first_monitoring_summary")
        )
        intervention_lane = _mapping(progress_payload.get("intervention_lane"))
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
        execution_envelope = dict(current_execution_envelope) if current_execution_envelope else {
            "state_kind": "executable_owner_action",
            "owner": next_owner,
            "next_work_unit": work_unit_id,
            "typed_blocker": None,
            "parked_state": None,
            "source": "progress_currentness.current_executable_owner_action",
        }
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
                **({"progress_first_monitoring_summary": dict(progress_first_monitoring_summary)}
                   if progress_first_monitoring_summary else {}),
                **({"intervention_lane": dict(intervention_lane)} if intervention_lane else {}),
                **({"accepted_closeout_evidence": closeout_evidence} if closeout_evidence else {}),
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
                "current_execution_envelope": dict(current_execution_envelope) if current_execution_envelope else fallback_envelope,
            }
        )
    return studies


def _with_candidate_root_closeout_scans(
    *,
    profile: WorkspaceProfile,
    candidates: list[dict[str, Any]],
    scanned_studies: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    studies = [dict(study) for study in scanned_studies]
    study_index_by_id = {
        study_id: index
        for index, study in enumerate(studies)
        if (study_id := _non_empty_text(study.get("study_id"))) is not None
    }
    for candidate in candidates:
        study_id = _non_empty_text(candidate.get("study_id"))
        if study_id is None:
            continue
        closeout_evidence = _study_root_closeout_evidence(
            study_root=Path(profile.studies_root) / study_id,
            identity=candidate,
        )
        if not closeout_evidence:
            continue
        if study_id in study_index_by_id:
            study = dict(studies[study_index_by_id[study_id]])
            study["accepted_closeout_evidence"] = [
                *_mapping_list(study.get("accepted_closeout_evidence")),
                *closeout_evidence,
            ]
            studies[study_index_by_id[study_id]] = study
            continue
        studies.append(
            {
                "study_id": study_id,
                "quest_id": _non_empty_text(candidate.get("quest_id")) or study_id,
                "handoff_scan_status": "scanned_no_provider_admission",
                "provider_admission_pending_count": 0,
                "running_provider_attempt": False,
                "action_queue": [],
                "accepted_closeout_evidence": closeout_evidence,
                "current_execution_envelope": {
                    "state_kind": "terminal_closeout_observed",
                    "owner": _non_empty_text(candidate.get("next_executable_owner"))
                    or _non_empty_text(candidate.get("recommended_owner"))
                    or _non_empty_text(candidate.get("request_owner")),
                    "next_work_unit": _non_empty_text(candidate.get("work_unit_id")),
                    "typed_blocker": None,
                    "parked_state": None,
                    "source": "candidate_root_closeout_evidence",
                },
            }
        )
        study_index_by_id[study_id] = len(studies) - 1
    return studies


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


def _study_root_closeout_evidence(
    *,
    study_root: Path,
    identity: Mapping[str, Any],
) -> list[dict[str, Any]]:
    if not identity:
        return []
    evidence: list[dict[str, Any]] = []
    for execution, execution_ref in default_executor_execution_candidates(study_root=study_root):
        closeout = _closeout_evidence_with_identity(execution, identity=identity)
        if not _closeout_identity_matches_current(closeout, identity=identity):
            continue
        closeout["source_path"] = _non_empty_text(closeout.get("source_path")) or execution_ref
        evidence.append(closeout)
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
        study_root = Path(profile.studies_root) / study_id
        status_payload = {
            "study_id": study_id,
            "quest_id": _non_empty_text(study.get("quest_id")) or study_id,
            "study_root": str(study_root),
            **_mapping(progress_by_study.get(study_id)),
        }
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


def _merge_provider_admission_candidates(
    *candidate_groups: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    merged: list[dict[str, Any]] = []
    seen: set[tuple[str | None, str | None, str | None, str | None]] = set()
    for group in candidate_groups:
        for candidate in group:
            key = (
                _non_empty_text(candidate.get("study_id")),
                _non_empty_text(candidate.get("action_type")),
                _non_empty_text(candidate.get("work_unit_id")),
                _non_empty_text(candidate.get("dispatch_path")),
            )
            if key in seen:
                continue
            seen.add(key)
            merged.append(dict(candidate))
    return merged


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
) -> list[dict[str, Any]]:
    fallback_by_identity = {
        (_non_empty_text(candidate.get("study_id")), _non_empty_text(candidate.get("action_type"))): candidate
        for candidate in fallback_candidates
    }
    current_action_by_study = _same_tick_progress_current_actions(progress_currentness)
    candidates: list[dict[str, Any]] = []
    for dispatch in materialize_result.get("default_executor_dispatches") or []:
        if not isinstance(dispatch, Mapping):
            continue
        if _non_empty_text(dispatch.get("dispatch_status")) != "ready":
            continue
        study_id = _non_empty_text(dispatch.get("study_id"))
        action_type = _non_empty_text(dispatch.get("action_type"))
        base = dict(fallback_by_identity.get((study_id, action_type), {}))
        candidate = {
            **base,
            "surface": "opl_provider_admission_candidate",
            "schema_version": 1,
            "status": "provider_admission_pending",
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
            "dispatch_authority": _non_empty_text(dispatch.get("dispatch_authority"))
            or _non_empty_text(base.get("dispatch_authority")),
            "blocked_reason": OPL_EXECUTION_AUTHORIZATION_BLOCKER,
            "next_executable_owner": _non_empty_text(dispatch.get("next_executable_owner"))
            or _non_empty_text(base.get("next_executable_owner")),
            "required_output_surface": _non_empty_text(dispatch.get("required_output_surface"))
            or _non_empty_text(base.get("required_output_surface")),
            "provider_attempt_or_lease_required": True,
            "provider_completion_is_domain_completion": False,
            "owner_route_current": True,
            "same_tick_materialized_provider_admission": True,
        }
        currentness_basis = _same_tick_materialized_currentness_basis(
            candidate,
            base=base,
            materialize_result=materialize_result,
        )
        if currentness_basis:
            candidate["currentness_basis"] = currentness_basis
        candidate = _same_tick_candidate_with_stage_run_identity(candidate)
        if candidate["study_id"] is not None and candidate["action_type"] is not None:
            current_action_identity = current_action_by_study.get(candidate["study_id"])
            if current_action_identity is not None and not _same_tick_candidate_matches_current_action(
                candidate,
                current_action_identity=current_action_identity,
            ):
                continue
            candidates.append({key: value for key, value in candidate.items() if value is not None})
    return candidates


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
            **dict(current_basis),
            **dict(currentness_basis),
            "work_unit_id": _non_empty_text(currentness_basis.get("work_unit_id"))
            or _non_empty_text(current_action_identity.get("work_unit_id"))
            or _non_empty_text(payload.get("work_unit_id")),
            "work_unit_fingerprint": _non_empty_text(currentness_basis.get("work_unit_fingerprint"))
            or fingerprint,
        }
    return payload


def _same_tick_candidate_with_stage_run_identity(candidate: Mapping[str, Any]) -> dict[str, Any]:
    payload = dict(candidate)
    study_id = _non_empty_text(payload.get("study_id"))
    fingerprint = _non_empty_text(payload.get("work_unit_fingerprint")) or _non_empty_text(
        payload.get("action_fingerprint")
    )
    route_key = _non_empty_text(payload.get("route_identity_key"))
    if route_key is None and study_id is not None and fingerprint is not None:
        route_key = f"provider-admission::{study_id}::{fingerprint}"
    attempt_key = _non_empty_text(payload.get("attempt_idempotency_key")) or route_key
    dispatch_ref = _non_empty_text(payload.get("dispatch_ref")) or _non_empty_text(payload.get("dispatch_path"))
    stage_packet_ref = _non_empty_text(payload.get("stage_packet_ref")) or dispatch_ref
    stage_packet_refs = _same_tick_text_items(payload.get("stage_packet_refs"))
    if stage_packet_ref is not None and stage_packet_ref not in stage_packet_refs:
        stage_packet_refs.append(stage_packet_ref)
    for key, value in {
        "dispatch_ref": dispatch_ref,
        "stage_packet_ref": stage_packet_ref,
        "route_identity_key": route_key,
        "attempt_idempotency_key": attempt_key,
        "idempotency_key": attempt_key,
    }.items():
        if value is not None:
            payload[key] = value
    if stage_packet_refs:
        payload["stage_packet_refs"] = stage_packet_refs
        payload.setdefault("checkpoint_refs", list(stage_packet_refs))
    source_refs = dict(_mapping(payload.get("source_refs")))
    for key, value in {
        "dispatch_ref": dispatch_ref,
        "stage_packet_ref": stage_packet_ref,
        "route_identity_key": route_key,
        "attempt_idempotency_key": attempt_key,
    }.items():
        if value is not None:
            source_refs[key] = value
    if stage_packet_refs:
        source_refs["stage_packet_refs"] = stage_packet_refs
    if source_refs:
        payload["source_refs"] = source_refs
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


def _same_tick_progress_current_actions(
    progress_currentness: Mapping[str, Any] | None,
) -> dict[str, dict[str, Any]]:
    current_actions: dict[str, dict[str, Any]] = {}
    for study_id, payload in _mapping(progress_currentness).items():
        normalized_study_id = _non_empty_text(study_id)
        if normalized_study_id is None:
            continue
        current = _mapping(_mapping(payload).get("current_executable_owner_action"))
        if not current:
            continue
        current_work_unit = _mapping(_mapping(payload).get("current_work_unit"))
        current_work_unit_basis = _mapping(current_work_unit.get("currentness_basis"))
        next_action = _mapping(current.get("next_action"))
        repair_precedence = _mapping(current.get("repair_progress_precedence"))
        allowed_actions = _same_tick_text_items(current.get("allowed_actions"))
        explicit_fingerprints = _same_tick_text_items(
            [
                current.get("work_unit_fingerprint"),
                current.get("action_fingerprint"),
                current.get("source_fingerprint"),
                repair_precedence.get("source_fingerprint"),
                current_work_unit.get("work_unit_fingerprint"),
                current_work_unit.get("action_fingerprint"),
                current_work_unit_basis.get("work_unit_fingerprint"),
                current_work_unit_basis.get("source_fingerprint"),
            ]
        )
        projected_action = _study_current_action_for_provider_admission(
            {
                "study_id": normalized_study_id,
                "quest_id": _non_empty_text(_mapping(payload).get("quest_id")) or normalized_study_id,
                "current_executable_owner_action": dict(current),
                **(
                    {"current_work_unit": dict(_mapping(_mapping(payload).get("current_work_unit")))}
                    if _mapping(_mapping(payload).get("current_work_unit"))
                    else {}
                ),
                **(
                    {"domain_transition": dict(_mapping(_mapping(payload).get("domain_transition")))}
                    if _mapping(_mapping(payload).get("domain_transition"))
                    else {}
                ),
                **(
                    {
                        "progress_first_monitoring_summary": dict(
                            _mapping(_mapping(payload).get("progress_first_monitoring_summary"))
                        )
                    }
                    if _mapping(_mapping(payload).get("progress_first_monitoring_summary"))
                    else {}
                ),
                **(
                    {"intervention_lane": dict(_mapping(_mapping(payload).get("intervention_lane")))}
                    if _mapping(_mapping(payload).get("intervention_lane"))
                    else {}
                ),
            }
        )
        if projected_action is not None:
            explicit_fingerprints.extend(
                _same_tick_text_items(
                    [
                        projected_action.get("work_unit_fingerprint"),
                        projected_action.get("action_fingerprint"),
                    ]
                )
            )
        current_actions[normalized_study_id] = {
            "action_type": _non_empty_text(current.get("action_type")),
            "action_ids": list(
                dict.fromkeys(
                    [
                        *allowed_actions,
                        *_same_tick_text_items([current.get("action_type"), next_action.get("action_id")]),
                    ]
                )
            ),
            "work_unit_id": _non_empty_text(current.get("work_unit_id"))
            or _non_empty_text(next_action.get("action_id")),
            "explicit_fingerprints": _same_tick_current_action_fingerprints(
                current=current,
                work_unit_id=(
                    _non_empty_text(current.get("work_unit_id"))
                    or _non_empty_text(next_action.get("action_id"))
                ),
                existing_fingerprints=explicit_fingerprints,
            ),
            "source_ref": _non_empty_text(current.get("source_ref"))
            or _non_empty_text(current.get("latest_owner_answer_ref")),
        }
    return current_actions


def _same_tick_current_action_fingerprints(
    *,
    current: Mapping[str, Any],
    work_unit_id: str | None,
    existing_fingerprints: list[str],
) -> list[str]:
    fingerprints = list(existing_fingerprints)
    source_ref = _non_empty_text(current.get("source_ref")) or _non_empty_text(
        current.get("latest_owner_answer_ref")
    )
    target_surface = _mapping(current.get("target_surface"))
    surface_key = _non_empty_text(current.get("surface_key")) or _non_empty_text(
        target_surface.get("surface_key")
    )
    if work_unit_id is not None and source_ref is not None:
        fingerprints.append(
            "stage-current-owner-delta::"
            f"{work_unit_id}::{surface_key or 'unspecified_surface'}::{source_ref}"
        )
    return list(dict.fromkeys(fingerprints))


def _same_tick_candidate_matches_current_action(
    candidate: Mapping[str, Any],
    *,
    current_action_identity: Mapping[str, Any],
) -> bool:
    action_type = _non_empty_text(candidate.get("action_type"))
    work_unit_id = _non_empty_text(candidate.get("work_unit_id"))
    work_unit_fingerprint = _non_empty_text(candidate.get("work_unit_fingerprint")) or _non_empty_text(
        candidate.get("action_fingerprint")
    )
    if action_type is None:
        return False
    expected_action_type = _non_empty_text(current_action_identity.get("action_type"))
    if expected_action_type is not None and action_type != expected_action_type:
        return False
    action_ids = {
        item
        for item in _same_tick_text_items(current_action_identity.get("action_ids"))
    }
    if action_ids and action_type not in action_ids:
        return False
    expected_work_unit_id = _non_empty_text(current_action_identity.get("work_unit_id"))
    if expected_work_unit_id is not None and work_unit_id != expected_work_unit_id:
        return False
    expected_fingerprints = set(_same_tick_text_items(current_action_identity.get("explicit_fingerprints")))
    if expected_fingerprints:
        return work_unit_fingerprint in expected_fingerprints
    expected_source_ref = _non_empty_text(current_action_identity.get("source_ref"))
    if expected_source_ref is not None:
        return work_unit_fingerprint is not None and expected_source_ref in work_unit_fingerprint
    if _same_tick_materialized_candidate(candidate):
        return False
    return True


def _same_tick_text_items(value: object) -> list[str]:
    if isinstance(value, str):
        text = _non_empty_text(value)
        return [text] if text is not None else []
    if not isinstance(value, list | tuple | set):
        return []
    result: list[str] = []
    for item in value:
        text = _non_empty_text(item)
        if text is not None and text not in result:
            result.append(text)
    return result


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _mapping_list(value: object) -> list[dict[str, Any]]:
    return [dict(item) for item in value or [] if isinstance(item, Mapping)]


__all__ = [
    "materialize_report_provider_admission_current_control_state",
    "sync_report_provider_admission_current_control_state",
]
