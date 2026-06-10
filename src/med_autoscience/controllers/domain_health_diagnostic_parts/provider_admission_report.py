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
from med_autoscience.controllers.opl_execution_boundary import OPL_EXECUTION_AUTHORIZATION_BLOCKER
from med_autoscience.controllers.owner_route_reconcile_parts import supervision_surfaces
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
    scanned_studies = _provider_admission_scanned_currentness_studies(progress_currentness)
    candidates = _filter_provider_admission_candidates_by_progress_currentness(
        candidates,
        progress_currentness=progress_currentness,
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
    progress_currentness = _mapping(current_execution_evidence.get("progress_currentness"))
    candidates = _merge_provider_admission_candidates(
        _filter_provider_admission_candidates_by_progress_currentness(
            [
                dict(item)
                for item in report.get("managed_study_opl_provider_admission_candidates") or []
                if isinstance(item, Mapping)
            ],
            progress_currentness=progress_currentness,
        ),
        _filter_provider_admission_candidates_by_progress_currentness(
            [
                dict(item)
                for item in current_control_state.get("provider_admission_candidates") or []
                if isinstance(item, Mapping)
            ],
            progress_currentness=progress_currentness,
        ),
    )
    report["managed_study_opl_provider_admission_candidates"] = candidates
    report["provider_admission_pending_count"] = len(candidates)
    current_execution_evidence["provider_admission_candidates"] = candidates
    report["current_execution_evidence"] = current_execution_evidence
    fingerprints = _same_tick_text_items(report.get("action_fingerprints"))
    for candidate in candidates:
        fingerprint = _non_empty_text(candidate.get("work_unit_fingerprint")) or _non_empty_text(
            candidate.get("action_fingerprint")
        )
        if fingerprint is not None and fingerprint not in fingerprints:
            fingerprints.append(fingerprint)
    report["action_fingerprints"] = fingerprints


def _provider_admission_scanned_currentness_studies(
    progress_currentness: Mapping[str, Any] | None,
) -> list[dict[str, Any]]:
    studies: list[dict[str, Any]] = []
    for study_id, payload in _mapping(progress_currentness).items():
        normalized_study_id = _non_empty_text(study_id)
        if normalized_study_id is None:
            continue
        current_action = _mapping(_mapping(payload).get("current_executable_owner_action"))
        if not current_action:
            continue
        current_work_unit = _mapping(_mapping(payload).get("current_work_unit"))
        current_owner_ticket = _mapping(_mapping(payload).get("current_owner_ticket"))
        current_execution_envelope = _mapping(_mapping(payload).get("current_execution_envelope"))
        domain_transition = _mapping(_mapping(payload).get("domain_transition"))
        progress_first_monitoring_summary = _mapping(
            _mapping(payload).get("progress_first_monitoring_summary")
        )
        intervention_lane = _mapping(_mapping(payload).get("intervention_lane"))
        next_owner = _non_empty_text(current_action.get("next_owner"))
        work_unit_id = _non_empty_text(current_action.get("work_unit_id"))
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
                "quest_id": _non_empty_text(current_action.get("quest_id")) or normalized_study_id,
                "handoff_scan_status": "scanned_no_provider_admission",
                "provider_admission_pending_count": 0,
                "action_queue": [],
                "current_executable_owner_action": dict(current_action),
                **({"current_work_unit": dict(current_work_unit)} if current_work_unit else {}),
                **({"current_owner_ticket": dict(current_owner_ticket)} if current_owner_ticket else {}),
                **({"domain_transition": dict(domain_transition)} if domain_transition else {}),
                **({"progress_first_monitoring_summary": dict(progress_first_monitoring_summary)}
                   if progress_first_monitoring_summary else {}),
                **({"intervention_lane": dict(intervention_lane)} if intervention_lane else {}),
                "current_execution_envelope": execution_envelope,
            }
        )
    return studies


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
        filtered.append(dict(candidate))
    return filtered


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
