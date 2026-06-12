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
from med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_closeout_semantics import (
    is_anti_loop_stop_loss_closeout,
)
from med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_current_control import (
    materialize_provider_admission_current_control_state,
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
    candidates = _merge_provider_admission_candidates(
        candidates,
        _provider_admission_candidates_from_progress_currentness(
            profile=profile,
            progress_currentness=progress_currentness,
            scanned_studies=scanned_studies,
        ),
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
    candidates = [
        dict(item)
        for item in current_control_state.get("provider_admission_candidates") or []
        if isinstance(item, Mapping)
    ]
    report["managed_study_opl_provider_admission_candidates"] = candidates
    report["provider_admission_pending_count"] = len(candidates)
    current_execution_evidence["provider_admission_candidates"] = candidates
    report["current_execution_evidence"] = current_execution_evidence
    fingerprints: list[str] = []
    for candidate in candidates:
        fingerprint = _non_empty_text(candidate.get("work_unit_fingerprint")) or _non_empty_text(
            candidate.get("action_fingerprint")
        )
        if fingerprint is not None and fingerprint not in fingerprints:
            fingerprints.append(fingerprint)
    report["action_fingerprints"] = fingerprints


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


def _terminal_stage_closeout_evidence(
    terminal: Mapping[str, Any],
    *,
    identity: Mapping[str, Any],
) -> dict[str, Any]:
    status = _non_empty_text(terminal.get("status"))
    classification = _non_empty_text(terminal.get("progress_delta_classification"))
    blocker_id = _terminal_stage_blocker_id(terminal)
    payload = {
        **dict(terminal),
        "surface_kind": _non_empty_text(terminal.get("surface_kind")) or "stage_attempt_closeout_packet",
        "status": status,
        "stage_closeout_status": status,
        "execution_status": status,
        "outcome": "typed_blocker" if classification == "typed_blocker" else _non_empty_text(terminal.get("outcome")),
        "blocked_reason": blocker_id,
        "typed_blocker_reason": blocker_id,
        "typed_blocker_ref": _non_empty_text(terminal.get("source_path")),
        "typed_blocker": {
            "blocker_id": blocker_id,
            "blocker_type": blocker_id,
            "owner": "one-person-lab",
            "write_permitted": False,
        },
    }
    return _closeout_evidence_with_identity(payload, identity=identity)


def _terminal_stage_blocker_id(terminal: Mapping[str, Any]) -> str:
    typed_blocker = _mapping(terminal.get("typed_blocker"))
    semantic = _mapping(terminal.get("terminal_closeout_semantic_completeness"))
    for value in (
        terminal.get("blocked_reason"),
        terminal.get("typed_blocker_reason"),
        terminal.get("blocker_id"),
        terminal.get("blocker_type"),
        typed_blocker.get("blocker_id"),
        typed_blocker.get("blocker_type"),
        typed_blocker.get("reason"),
        semantic.get("typed_blocker"),
    ):
        text = _non_empty_text(value)
        if text is not None:
            return text
    if _non_empty_text(terminal.get("status")) == "repeat_suppressed":
        return "anti_loop_budget_exhausted"
    return _non_empty_text(terminal.get("status")) or "terminal_closeout_observed"


def _closeout_evidence_with_identity(
    closeout: Mapping[str, Any],
    *,
    identity: Mapping[str, Any],
) -> dict[str, Any]:
    result = dict(closeout)
    had_native_identity = _closeout_has_native_current_identity(result)
    for key, value in {
        "surface_kind": _non_empty_text(result.get("surface_kind"))
        or _non_empty_text(result.get("stage_closeout_surface_kind")),
        "status": _non_empty_text(result.get("status"))
        or _non_empty_text(result.get("stage_closeout_status")),
        "outcome": _non_empty_text(result.get("outcome"))
        or _non_empty_text(result.get("stage_closeout_outcome")),
    }.items():
        if value is not None:
            result[key] = value
    if (
        _closeout_has_opl_execution_authorization_blocker(result)
        and not is_anti_loop_stop_loss_closeout(result)
    ):
        result["identity_binding_status"] = "mismatch"
        return result
    for key in (
        "action_type",
        "work_unit_id",
        "work_unit_fingerprint",
        "action_fingerprint",
        "source_eval_id",
        "truth_epoch",
        "runtime_health_epoch",
    ):
        if result.get(key) in (None, "", [], {}) and identity.get(key) not in (None, "", [], {}):
            result[key] = identity[key]
    if not had_native_identity:
        result["identity_binding_status"] = "inferred_from_current_work_unit"
    basis = _mapping(result.get("owner_route_currentness_basis"))
    if not basis:
        basis = {
            key: result.get(key)
            for key in (
                "work_unit_id",
                "work_unit_fingerprint",
                "source_eval_id",
                "truth_epoch",
                "runtime_health_epoch",
            )
            if result.get(key) not in (None, "", [], {})
        }
        if basis:
            result["owner_route_currentness_basis"] = basis
    return result


def _closeout_has_native_current_identity(closeout: Mapping[str, Any]) -> bool:
    if _mapping(closeout.get("owner_route_currentness_basis")):
        return True
    work_unit = _non_empty_text(closeout.get("work_unit_id"))
    fingerprint = _non_empty_text(closeout.get("work_unit_fingerprint")) or _non_empty_text(
        closeout.get("action_fingerprint")
    )
    source_eval_id = _non_empty_text(closeout.get("source_eval_id"))
    return work_unit is not None and (fingerprint is not None or source_eval_id is not None)


def _closeout_identity_matches_current(
    closeout: Mapping[str, Any],
    *,
    identity: Mapping[str, Any],
) -> bool:
    if closeout.get("identity_binding_status") == "mismatch":
        return False
    expected_action = _non_empty_text(identity.get("action_type"))
    expected_work_unit = _non_empty_text(identity.get("work_unit_id"))
    if expected_action is not None and _non_empty_text(closeout.get("action_type")) != expected_action:
        return False
    if expected_work_unit is not None and _non_empty_text(closeout.get("work_unit_id")) != expected_work_unit:
        return False
    expected_fingerprint = _non_empty_text(identity.get("work_unit_fingerprint")) or _non_empty_text(
        identity.get("action_fingerprint")
    )
    closeout_fingerprint = _non_empty_text(closeout.get("work_unit_fingerprint")) or _non_empty_text(
        closeout.get("action_fingerprint")
    )
    if expected_fingerprint is None:
        return True
    if closeout_fingerprint == expected_fingerprint:
        return True
    return closeout_fingerprint is None and is_anti_loop_stop_loss_closeout(closeout)


def _closeout_has_opl_execution_authorization_blocker(closeout: Mapping[str, Any]) -> bool:
    typed_blocker = _mapping(closeout.get("typed_blocker"))
    direct_values = (
        closeout.get("blocked_reason"),
        closeout.get("typed_blocker_reason"),
        typed_blocker.get("blocker_id"),
        typed_blocker.get("blocker_type"),
        typed_blocker.get("blocked_reason"),
    )
    if any(_non_empty_text(value) == OPL_EXECUTION_AUTHORIZATION_BLOCKER for value in direct_values):
        return True
    text_values = (
        closeout.get("outcome"),
        closeout.get("problem_summary"),
        closeout.get("semantic_gap"),
        *list(closeout.get("remaining_blockers") or []),
    )
    return any(
        OPL_EXECUTION_AUTHORIZATION_BLOCKER in text
        for value in text_values
        if (text := _non_empty_text(value)) is not None
    )


def _progress_currentness_current_identity(payload: Mapping[str, Any]) -> dict[str, Any]:
    current_work_unit = _mapping(payload.get("current_work_unit"))
    current_action = _mapping(payload.get("current_executable_owner_action"))
    currentness_basis = _mapping(current_work_unit.get("currentness_basis")) or _mapping(
        current_action.get("owner_route_currentness_basis")
    )
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
        _non_empty_text(current_work_unit.get("action_type"))
        or _non_empty_text(current_action.get("action_type"))
        or _non_empty_text(owner_action.get("action_type"))
        or (allowed_actions[0] if len(allowed_actions) == 1 else None)
    )
    work_unit_id = (
        _non_empty_text(current_work_unit.get("work_unit_id"))
        or _non_empty_text(current_action.get("work_unit_id"))
        or _non_empty_text(owner_action.get("work_unit_id"))
        or _non_empty_text(next_forced_delta.get("work_unit_id"))
        or _non_empty_text(ticket_work_unit.get("work_unit_id"))
        or _non_empty_text(ticket_work_unit.get("unit_id"))
    )
    fingerprint = (
        _non_empty_text(current_work_unit.get("work_unit_fingerprint"))
        or _non_empty_text(current_work_unit.get("action_fingerprint"))
        or _non_empty_text(current_action.get("work_unit_fingerprint"))
        or _non_empty_text(current_action.get("action_fingerprint"))
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
    blocked_scanned_study_ids = _scanned_study_ids_without_provider_admission(scanned_studies)
    if not current_action_by_study and not blocked_scanned_study_ids:
        return [dict(candidate) for candidate in candidates]
    filtered: list[dict[str, Any]] = []
    for candidate in candidates:
        study_id = _non_empty_text(candidate.get("study_id"))
        if study_id in blocked_scanned_study_ids:
            continue
        current_action_identity = current_action_by_study.get(study_id) if study_id is not None else None
        if current_action_identity is not None and not _same_tick_candidate_matches_current_action(
            candidate,
            current_action_identity=current_action_identity,
        ):
            continue
        filtered.append(dict(candidate))
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
        }
        if candidate["study_id"] is not None and candidate["action_type"] is not None:
            current_action_identity = current_action_by_study.get(candidate["study_id"])
            if current_action_identity is not None and not _same_tick_candidate_matches_current_action(
                candidate,
                current_action_identity=current_action_identity,
            ):
                continue
            candidates.append({key: value for key, value in candidate.items() if value is not None})
    return candidates


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
        next_action = _mapping(current.get("next_action"))
        repair_precedence = _mapping(current.get("repair_progress_precedence"))
        allowed_actions = _same_tick_text_items(current.get("allowed_actions"))
        explicit_fingerprints = _same_tick_text_items(
            [
                current.get("work_unit_fingerprint"),
                current.get("action_fingerprint"),
                current.get("source_fingerprint"),
                repair_precedence.get("source_fingerprint"),
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
            "explicit_fingerprints": explicit_fingerprints,
            "source_ref": _non_empty_text(current.get("source_ref"))
            or _non_empty_text(current.get("latest_owner_answer_ref")),
        }
    return current_actions


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


__all__ = [
    "materialize_report_provider_admission_current_control_state",
    "sync_report_provider_admission_current_control_state",
]
