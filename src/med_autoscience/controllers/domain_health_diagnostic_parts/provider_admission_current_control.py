from __future__ import annotations

from typing import Any, Mapping

from med_autoscience.controllers.domain_health_diagnostic_parts.managed_wakeup import _non_empty_text
from med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission import (
    provider_attempt_matches_identity,
)
from med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_closeout_semantics import (
    is_anti_loop_stop_loss_closeout,
)
from med_autoscience.controllers.domain_health_diagnostic_parts import (
    provider_admission_current_control_receipts as current_control_receipts,
)
from med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_current_control_arbiter import (
    _candidates_not_covered_by_live_attempt,
    _matching_accepted_closeout,
    _running_attempt_from_study,
    _stage_route_arbiter_decisions,
    _stage_route_arbiter_summary,
)
from med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_current_control_identity import (
    accepted_closeout_receipts as _accepted_closeout_receipts,
    candidate_with_identity as _candidate_with_identity,
    candidate_with_progress_currentness_identity as _candidate_with_progress_currentness_identity,
    provider_admission_current_control_study,
)
from med_autoscience.controllers.domain_health_diagnostic_parts.opl_transition_readback import (
    candidate_opl_transition_readback,
)
from med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_transition_request import (
    candidate_with_opl_transition_request as _candidate_with_opl_transition_request,
)
from med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_helpers import (
    mapping as _mapping,
    text_items as _text_items,
)
from med_autoscience.controllers.owner_route_reconcile_parts import scan_output, supervision_surfaces
from med_autoscience.profiles import WorkspaceProfile


def materialize_provider_admission_current_control_state(
    *,
    profile: WorkspaceProfile,
    candidates: list[dict[str, Any]],
    generated_at: str,
    apply: bool,
    scanned_studies: list[dict[str, Any]] | None = None,
) -> dict[str, Any] | None:
    if not candidates and not scanned_studies:
        return None
    latest_path = supervision_surfaces.latest_path(profile)
    history_path = supervision_surfaces.history_path(profile)
    previous_payload = supervision_surfaces.read_json_object(latest_path)
    scanned_studies = _normalized_scanned_studies(scanned_studies)
    scanned_studies_by_id = {
        study_id: dict(study)
        for study in scanned_studies or []
        if (study_id := _non_empty_text(study.get("study_id"))) is not None
    }
    candidates = [
        _candidate_with_opl_transition_request(
            _candidate_with_identity(
                _candidate_with_progress_currentness_identity(
                    candidate,
                    scanned_studies_by_id=scanned_studies_by_id,
                )
            ),
            source="dhd.provider_admission_current_control",
        )
        for candidate in candidates
    ]
    scanned_studies = _scanned_studies_with_candidate_closeout_projection(
        scanned_studies,
        candidates=candidates,
    )
    scanned_studies_by_id = {
        study_id: dict(study)
        for study in scanned_studies or []
        if (study_id := _non_empty_text(study.get("study_id"))) is not None
    }
    live_studies_by_id = _live_scanned_studies_by_id(scanned_studies)
    arbiter_decisions = _stage_route_arbiter_decisions(
        candidates,
        live_studies_by_id=live_studies_by_id,
        scanned_studies_by_id=scanned_studies_by_id,
    )
    transition_request_candidates = _candidates_not_covered_by_live_attempt(
        candidates,
        live_studies_by_id=live_studies_by_id,
        scanned_studies_by_id=scanned_studies_by_id,
    )
    pending_candidates = [
        candidate
        for candidate in transition_request_candidates
        if candidate_opl_transition_readback(candidate)
    ]
    terminal_precedence_by_study = _terminal_precedence_by_study(scanned_studies)
    studies = [
        _study_with_terminal_precedence(
            provider_admission_current_control_study(candidate),
            terminal_precedence_by_study=terminal_precedence_by_study,
        )
        for candidate in transition_request_candidates
    ]
    candidate_study_ids = {
        study_id
        for study in studies
        if (study_id := _non_empty_text(study.get("study_id"))) is not None
    }
    studies.extend(
        dict(study)
        for study in scanned_studies or []
        if (study_id := _non_empty_text(study.get("study_id"))) is not None
        and study_id not in candidate_study_ids
    )
    action_queue = [
        action
        for study in studies
        for action in study.get("action_queue", [])
        if isinstance(action, Mapping)
    ]
    output_studies, output_actions = scan_output.merge_previous_unscanned_study_handoff(
        previous_payload=previous_payload,
        scanned_studies=studies,
        scanned_action_queue=action_queue,
        retain_unscanned_studies=True,
    )
    output_studies, output_actions, unscanned_audit = _audit_only_unscanned_handoff(
        output_studies=output_studies,
        output_actions=output_actions,
        scanned_study_ids={
            study_id
            for study in studies
            if (study_id := _non_empty_text(study.get("study_id"))) is not None
        },
    )
    current_execution_envelopes = scan_output.merge_current_execution_envelopes(
        previous_payload=previous_payload,
        output_studies=output_studies,
        scanned_studies=studies,
        retain_unscanned_studies=True,
    )
    payload = scan_output.build_scan_domain_routes_payload(
        schema_version=1,
        generated_at=generated_at,
        workspace_root=profile.workspace_root,
        developer_mode_payload={
            "mode": "developer_apply_safe",
            "mode_label": "focused_provider_admission_current_control",
            "scheduler_owner": "opl_current_control_state",
            "safe_actions_enabled": True,
            "repo_level_repair_authority": False,
        },
        safe_actions_enabled=True,
        two_layer_ai_repair_policy={},
        studies=output_studies,
        action_queue=output_actions,
        current_execution_envelopes=current_execution_envelopes,
        queue_history={
            "history_path": str(history_path),
            "latest_action_count": len(output_actions),
            "provider_admission_pending_count": len(pending_candidates),
            "transition_request_pending_count": len(transition_request_candidates),
        },
        workspace_daemon_lifecycle={},
        provider_readiness=None,
        latest_path=latest_path,
        history_path=history_path,
        provider_admission_candidates=[dict(candidate) for candidate in pending_candidates],
    )
    payload["provider_admission_pending_count"] = len(pending_candidates)
    payload["provider_admission_candidates"] = [dict(candidate) for candidate in pending_candidates]
    payload["transition_request_pending_count"] = len(transition_request_candidates)
    payload["transition_request_candidates"] = [
        dict(candidate) for candidate in transition_request_candidates
    ]
    payload["stage_route_arbiter"] = _stage_route_arbiter_summary(
        decisions=arbiter_decisions,
        candidate_count=len(candidates),
        pending_count=len(pending_candidates),
    )
    payload["stage_route_arbiter_decisions"] = arbiter_decisions
    payload["unscanned_handoff_retention"] = unscanned_audit
    payload["current_control_refresh_source"] = "domain_health_diagnostic.provider_admission_candidates"
    payload = _payload_with_consumed_closeout_typed_blockers(payload)
    if apply:
        supervision_surfaces.write_json(latest_path, payload)
        supervision_surfaces.append_json_line(
            history_path,
            {
                "generated_at": generated_at,
                "study_ids": [
                    study_id
                    for study in studies
                    if (study_id := _non_empty_text(study.get("study_id"))) is not None
                ],
                "action_ids": [action.get("action_id") for action in output_actions],
                "provider_admission_pending_count": len(pending_candidates),
                "transition_request_pending_count": len(transition_request_candidates),
                "stage_route_arbiter_decision_counts": payload["stage_route_arbiter"][
                    "decision_counts"
                ],
                "unscanned_active_action_suppressed_count": unscanned_audit[
                    "active_action_suppressed_count"
                ],
                "latest_action_count": len(output_actions),
                "source": "domain_health_diagnostic.provider_admission_candidates",
            },
        )
    payload["written"] = bool(apply)
    return payload


def _payload_with_consumed_closeout_typed_blockers(payload: dict[str, Any]) -> dict[str, Any]:
    closeouts_by_study = _consumed_closeouts_by_study(payload.get("stage_route_arbiter_decisions"))
    if not closeouts_by_study:
        return payload
    studies: list[dict[str, Any]] = []
    changed = False
    for study in payload.get("studies") or []:
        if not isinstance(study, Mapping):
            continue
        study_id = _non_empty_text(study.get("study_id"))
        closeout = closeouts_by_study.get(study_id)
        if closeout is None:
            studies.append(dict(study))
            continue
        identity = _closeout_identity(study)
        typed_blocker = _typed_blocker_from_closeout(
            closeout,
            identity={
                **identity,
                "action_type": _non_empty_text(closeout.get("action_type")),
                "work_unit_id": _non_empty_text(closeout.get("work_unit_id")),
                "work_unit_fingerprint": _non_empty_text(closeout.get("work_unit_fingerprint"))
                or _non_empty_text(closeout.get("action_fingerprint")),
                "action_fingerprint": _non_empty_text(closeout.get("action_fingerprint"))
                or _non_empty_text(closeout.get("work_unit_fingerprint")),
            },
        )
        if not typed_blocker:
            studies.append(dict(study))
            continue
        projected = _study_with_accepted_closeout_typed_blocker(
            study,
            typed_blocker=typed_blocker,
            source="accepted_closeout_consumed_pending",
        )
        studies.append(projected)
        changed = changed or projected != study
    if not changed:
        return payload
    return {**payload, "studies": studies}


def _consumed_closeouts_by_study(decisions: object) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for decision in decisions or []:
        if not isinstance(decision, Mapping):
            continue
        if _non_empty_text(decision.get("decision")) != "accepted_closeout_consumed_pending":
            continue
        study_id = _non_empty_text(decision.get("study_id"))
        evidence = _mapping(decision.get("evidence"))
        if study_id is not None and evidence:
            result[study_id] = dict(evidence)
    return result


def _audit_only_unscanned_handoff(
    *,
    output_studies: list[dict[str, Any]],
    output_actions: list[dict[str, Any]],
    scanned_study_ids: set[str],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    retained_ids = {
        study_id
        for study in output_studies
        if (study_id := _non_empty_text(study.get("study_id"))) is not None
        and study_id not in scanned_study_ids
    }
    if not retained_ids:
        return output_studies, output_actions, _unscanned_handoff_retention_payload(
            retained_ids=[],
            active_action_suppressed_count=0,
        )
    sanitized_studies: list[dict[str, Any]] = []
    suppressed_count = 0
    for study in output_studies:
        study_id = _non_empty_text(study.get("study_id"))
        if study_id not in retained_ids:
            sanitized_studies.append(dict(study))
            continue
        action_queue = [
            dict(action)
            for action in study.get("action_queue") or []
            if isinstance(action, Mapping)
        ]
        suppressed_count += len(action_queue)
        payload = dict(study)
        payload["retained_unscanned_study"] = True
        payload["active_provider_admission_allowed"] = False
        payload["unscanned_action_queue_retained_for_audit"] = action_queue
        payload["action_queue"] = []
        sanitized_studies.append(payload)
    active_actions = [
        dict(action)
        for action in output_actions
        if _non_empty_text(action.get("study_id")) not in retained_ids
    ]
    suppressed_count += len(output_actions) - len(active_actions)
    return (
        sanitized_studies,
        active_actions,
        _unscanned_handoff_retention_payload(
            retained_ids=sorted(retained_ids),
            active_action_suppressed_count=suppressed_count,
        ),
    )


def _unscanned_handoff_retention_payload(
    *,
    retained_ids: list[str],
    active_action_suppressed_count: int,
) -> dict[str, Any]:
    return {
        "surface_kind": "provider_admission_current_control_unscanned_handoff_retention",
        "retained_unscanned_study_ids": retained_ids,
        "active_action_suppressed_count": active_action_suppressed_count,
        "active_queue_semantics": "scanned_studies_only",
        "retention_semantics": "audit_only",
    }


def _live_scanned_studies_by_id(
    scanned_studies: list[dict[str, Any]] | None,
) -> dict[str, dict[str, Any]]:
    return {
        study_id: dict(study)
        for study in scanned_studies or []
        if (study_id := _non_empty_text(study.get("study_id"))) is not None
        and _running_attempt_from_study(study)
    }


def _normalized_scanned_studies(
    scanned_studies: list[dict[str, Any]] | None,
) -> list[dict[str, Any]]:
    return [
        _scanned_study_with_accepted_closeout_projection(
            _scanned_study_with_live_attempt_projection(study)
        )
        for study in scanned_studies or []
    ]


def _scanned_study_with_live_attempt_projection(study: Mapping[str, Any]) -> dict[str, Any]:
    payload = dict(study)
    live_attempt = _running_attempt_from_study(payload)
    if not live_attempt:
        return payload
    work_unit_id = _non_empty_text(live_attempt.get("work_unit_id")) or _non_empty_text(
        _mapping(payload.get("current_execution_envelope")).get("next_work_unit")
    )
    payload.update(
        {
            "handoff_scan_status": _non_empty_text(payload.get("handoff_scan_status"))
            or "running_provider_attempt_observed",
            "quest_status": _non_empty_text(payload.get("quest_status")) or "running",
            "active_run_id": _non_empty_text(live_attempt.get("active_run_id")),
            "active_stage_attempt_id": _non_empty_text(live_attempt.get("active_stage_attempt_id")),
            "active_workflow_id": _non_empty_text(live_attempt.get("active_workflow_id")),
            "running_provider_attempt": True,
            "runtime_health": _mapping(live_attempt.get("runtime_health")),
            "action_queue": [],
            "provider_admission_candidates": [],
            "provider_admission_pending_count": 0,
            "why_not_applied": None,
            "blocked_reason": None,
            "typed_blocker": None,
            "next_owner": "supervisor_only/live_provider_attempt",
            "external_supervisor_required": False,
            "opl_provider_attempt": live_attempt,
            "current_execution_envelope": {
                "state_kind": "running_provider_attempt",
                "owner": _non_empty_text(live_attempt.get("owner"))
                or "supervisor_only/live_provider_attempt",
                "next_work_unit": work_unit_id,
                "typed_blocker": None,
                "parked_state": None,
                "source": _non_empty_text(live_attempt.get("source"))
                or "opl_provider_attempt",
            },
        }
    )
    current = _mapping(payload.get("current_work_unit"))
    if current:
        state = _mapping(current.get("state"))
        payload["current_work_unit"] = {
            **current,
            "status": "running_provider_attempt",
            "owner": _non_empty_text(live_attempt.get("owner"))
            or _non_empty_text(current.get("owner"))
            or "supervisor_only/live_provider_attempt",
            "action_type": _non_empty_text(live_attempt.get("action_type"))
            or _non_empty_text(current.get("action_type")),
            "work_unit_id": work_unit_id or _non_empty_text(current.get("work_unit_id")),
            "work_unit_fingerprint": _non_empty_text(live_attempt.get("work_unit_fingerprint"))
            or _non_empty_text(live_attempt.get("action_fingerprint"))
            or _non_empty_text(current.get("work_unit_fingerprint")),
            "action_fingerprint": _non_empty_text(live_attempt.get("action_fingerprint"))
            or _non_empty_text(live_attempt.get("work_unit_fingerprint"))
            or _non_empty_text(current.get("action_fingerprint")),
            "state": {
                **state,
                "state_kind": "running_provider_attempt",
                "source": _non_empty_text(live_attempt.get("source"))
                or "opl_provider_attempt",
                "provider_attempt_proof": dict(live_attempt),
                "strict_running_proof": True,
                "typed_blocker": None,
                "blocker_type": None,
                "stale_queue_or_handoff_can_override": False,
            },
        }
    return payload


def _scanned_study_with_accepted_closeout_projection(study: Mapping[str, Any]) -> dict[str, Any]:
    payload = dict(study)
    terminal_closeout = _accepted_closeout_for_live_attempt(payload)
    if terminal_closeout:
        typed_blocker = _typed_blocker_from_closeout(
            terminal_closeout,
            identity=_closeout_identity(payload),
        )
        terminal_envelope = {
            "state_kind": "typed_blocker" if typed_blocker else "terminal_closeout_observed",
            "owner": _non_empty_text(typed_blocker.get("owner")) if typed_blocker else "med-autoscience",
            "next_work_unit": None if typed_blocker else _non_empty_text(terminal_closeout.get("work_unit_id")),
            "typed_blocker": typed_blocker or None,
            "parked_state": None,
            "source": "terminal_closeout_precedes_live_projection",
        }
        current_action = _mapping(payload.get("current_executable_owner_action"))
        existing_envelope = _mapping(payload.get("current_execution_envelope"))
        if current_action and not provider_attempt_matches_identity(terminal_closeout, identity=current_action):
            terminal_envelope = existing_envelope or {
                "state_kind": "executable_owner_action",
                "owner": _non_empty_text(current_action.get("next_owner")),
                "next_work_unit": _non_empty_text(current_action.get("work_unit_id")),
                "typed_blocker": None,
                "parked_state": None,
                "source": "progress_currentness.current_executable_owner_action",
            }
        payload.update(
            {
                "quest_status": _non_empty_text(payload.get("quest_status")) or "active",
                "active_run_id": None,
                "active_stage_attempt_id": None,
                "active_workflow_id": None,
                "running_provider_attempt": False,
                "runtime_health": {
                    "health_status": "terminal_closeout_observed",
                    "runtime_liveness_status": "not_running",
                    "summary": "Terminal closeout for the same stage attempt suppresses stale running projection.",
                },
                "action_queue": [],
                "provider_admission_candidates": [],
                "provider_admission_pending_count": 0,
                "terminal_closeout_precedence_evidence": terminal_closeout,
                "stale_running_projection_suppressed": True,
                "opl_provider_attempt": terminal_closeout,
                "current_execution_envelope": terminal_envelope,
            }
        )
        if typed_blocker:
            payload["typed_blocker"] = typed_blocker
            payload["blocked_reason"] = _non_empty_text(typed_blocker.get("blocker_type"))
            payload["next_owner"] = _non_empty_text(typed_blocker.get("owner"))
            current = _mapping(payload.get("current_work_unit"))
            if current:
                payload["current_work_unit"] = {
                    **current,
                    "status": "typed_blocker",
                    "owner": _non_empty_text(typed_blocker.get("owner"))
                    or _non_empty_text(current.get("owner")),
                    "state": {
                        **_mapping(current.get("state")),
                        "state_kind": "typed_blocker",
                        "source": "terminal_closeout_precedes_live_projection",
                        "typed_blocker": typed_blocker,
                        "blocker_type": _non_empty_text(typed_blocker.get("blocker_type")),
                        "stale_queue_or_handoff_can_override": False,
                    },
                }
        return payload
    if payload.get("running_provider_attempt") is True:
        return payload
    identity = _closeout_identity(payload)
    accepted_closeout = _matching_accepted_closeout(payload, identity=identity)
    if not accepted_closeout:
        return payload
    typed_blocker = _typed_blocker_from_closeout(accepted_closeout, identity=identity)
    payload.update(
        {
            "action_queue": [],
            "provider_admission_candidates": [],
            "provider_admission_pending_count": 0,
        }
    )
    if typed_blocker:
        payload.update(
            {
                "blocked_reason": _non_empty_text(typed_blocker.get("blocker_type")),
                "next_owner": _non_empty_text(typed_blocker.get("owner")),
                "typed_blocker": typed_blocker,
                "current_execution_envelope": {
                    "state_kind": "typed_blocker",
                    "owner": _non_empty_text(typed_blocker.get("owner")) or "med-autoscience",
                    "next_work_unit": None,
                    "typed_blocker": typed_blocker,
                    "parked_state": None,
                    "source": "accepted_closeout_consumed_pending",
                },
            }
        )
        current = _mapping(payload.get("current_work_unit"))
        if current:
            payload["current_work_unit"] = {
                **current,
                "status": "typed_blocker",
                "owner": _non_empty_text(typed_blocker.get("owner")) or _non_empty_text(current.get("owner")),
                "state": {
                    **_mapping(current.get("state")),
                    "state_kind": "typed_blocker",
                    "source": "accepted_closeout_consumed_pending",
                    "typed_blocker": typed_blocker,
                    "blocker_type": _non_empty_text(typed_blocker.get("blocker_type")),
                    "stale_queue_or_handoff_can_override": False,
                },
            }
    return payload


def _scanned_studies_with_candidate_closeout_projection(
    studies: list[dict[str, Any]],
    *,
    candidates: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    candidates_by_study: dict[str, list[dict[str, Any]]] = {}
    for candidate in candidates:
        study_id = _non_empty_text(candidate.get("study_id"))
        if study_id is None:
            continue
        candidates_by_study.setdefault(study_id, []).append(candidate)
    return [
        _scanned_study_with_candidate_closeout_projection(
            study,
            candidates=candidates_by_study.get(_non_empty_text(study.get("study_id")) or "", []),
        )
        for study in studies
    ]


def _scanned_study_with_candidate_closeout_projection(
    study: Mapping[str, Any],
    *,
    candidates: list[dict[str, Any]],
) -> dict[str, Any]:
    if not candidates or study.get("running_provider_attempt") is True:
        return dict(study)
    for candidate in candidates:
        accepted_closeout = _matching_accepted_closeout(study, identity=candidate)
        if not accepted_closeout:
            continue
        typed_blocker = _typed_blocker_from_closeout(accepted_closeout, identity=candidate)
        if typed_blocker:
            return _study_with_accepted_closeout_typed_blocker(
                study,
                typed_blocker=typed_blocker,
                source="accepted_closeout_consumed_pending",
            )
    return dict(study)


def _study_with_accepted_closeout_typed_blocker(
    study: Mapping[str, Any],
    *,
    typed_blocker: Mapping[str, Any],
    source: str,
) -> dict[str, Any]:
    payload = dict(study)
    payload.update(
        {
            "action_queue": [],
            "provider_admission_candidates": [],
            "provider_admission_pending_count": 0,
            "blocked_reason": _non_empty_text(typed_blocker.get("blocker_type")),
            "next_owner": _non_empty_text(typed_blocker.get("owner")),
            "typed_blocker": dict(typed_blocker),
            "current_execution_envelope": {
                "state_kind": "typed_blocker",
                "owner": _non_empty_text(typed_blocker.get("owner")) or "med-autoscience",
                "next_work_unit": None,
                "typed_blocker": dict(typed_blocker),
                "parked_state": None,
                "source": source,
            },
        }
    )
    current = _mapping(payload.get("current_work_unit"))
    if current:
        payload["current_work_unit"] = {
            **current,
            "status": "typed_blocker",
            "owner": _non_empty_text(typed_blocker.get("owner")) or _non_empty_text(current.get("owner")),
            "state": {
                **_mapping(current.get("state")),
                "state_kind": "typed_blocker",
                "source": source,
                "typed_blocker": dict(typed_blocker),
                "blocker_type": _non_empty_text(typed_blocker.get("blocker_type")),
                "stale_queue_or_handoff_can_override": False,
            },
        }
    return payload


def _terminal_precedence_by_study(
    scanned_studies: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for study in scanned_studies:
        study_id = _non_empty_text(study.get("study_id"))
        evidence = _mapping(study.get("terminal_closeout_precedence_evidence"))
        if study_id is not None and evidence:
            result[study_id] = dict(evidence)
    return result


def _study_with_terminal_precedence(
    study: dict[str, Any],
    *,
    terminal_precedence_by_study: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    study_id = _non_empty_text(study.get("study_id"))
    evidence = _mapping(terminal_precedence_by_study.get(study_id)) if study_id is not None else {}
    if not evidence:
        return study
    payload = dict(study)
    payload["terminal_closeout_precedence_evidence"] = dict(evidence)
    payload["stale_running_projection_suppressed"] = True
    payload["running_provider_attempt"] = False
    payload["active_run_id"] = None
    payload["active_stage_attempt_id"] = None
    payload["active_workflow_id"] = None
    runtime_health = _mapping(payload.get("runtime_health"))
    payload["runtime_health"] = {
        **runtime_health,
        "health_status": _non_empty_text(runtime_health.get("health_status"))
        or "provider_admission_pending",
        "runtime_liveness_status": "not_running",
        "stale_running_projection_suppressed": True,
    }
    return payload


def _closeout_identity(study: Mapping[str, Any]) -> dict[str, Any]:
    receipt = _mapping(study.get("default_executor_execution_receipt_consumption")) or _mapping(
        study.get("opl_provider_attempt")
    )
    current_work_unit = _mapping(study.get("current_work_unit"))
    current_action = _mapping(study.get("current_executable_owner_action"))
    envelope = _mapping(study.get("current_execution_envelope"))
    if not receipt:
        receipt = current_work_unit or current_action
    if not receipt:
        receipt = {
            "work_unit_id": _non_empty_text(envelope.get("next_work_unit")),
        }
    owner = (
        _non_empty_text(receipt.get("next_executable_owner"))
        or _non_empty_text(receipt.get("owner"))
        or _non_empty_text(current_action.get("next_executable_owner"))
        or _non_empty_text(current_action.get("owner"))
        or _non_empty_text(current_work_unit.get("next_executable_owner"))
        or _non_empty_text(current_work_unit.get("owner"))
        or _non_empty_text(envelope.get("owner"))
    )
    return {
        key: value
        for key, value in {
            "action_type": _non_empty_text(receipt.get("action_type")),
            "work_unit_id": _non_empty_text(receipt.get("work_unit_id")),
            "work_unit_fingerprint": _non_empty_text(receipt.get("work_unit_fingerprint")),
            "action_fingerprint": _non_empty_text(receipt.get("action_fingerprint")),
            "dispatch_path": _non_empty_text(receipt.get("dispatch_path")),
            "dispatch_ref": _non_empty_text(receipt.get("dispatch_ref")),
            "owner": owner,
            "next_executable_owner": owner,
        }.items()
        if value is not None
    }


def _typed_blocker_from_closeout(
    closeout: Mapping[str, Any],
    *,
    identity: Mapping[str, Any],
) -> dict[str, Any]:
    embedded = _mapping(closeout.get("typed_blocker"))
    paper_log = _mapping(closeout.get("paper_stage_log"))
    owner_result = _mapping(closeout.get("owner_result"))
    paper_log_classification = _non_empty_text(paper_log.get("progress_delta_classification"))
    progress_delta_classification = _non_empty_text(
        closeout.get("progress_delta_classification")
    ) or paper_log_classification
    closeout_marks_typed_blocker = (
        _non_empty_text(embedded.get("surface_kind")) == "mas_domain_typed_blocker"
        or is_anti_loop_stop_loss_closeout(closeout)
        or _non_empty_text(closeout.get("status")) in {"closed_with_typed_blocker"}
        or _non_empty_text(closeout.get("stage_closeout_status")) in {"closed_with_typed_blocker"}
        or _non_empty_text(closeout.get("outcome"))
        in {
            "typed_blocker",
            "repeat_suppressed_with_typed_blocker",
        }
        or _non_empty_text(closeout.get("stage_closeout_outcome"))
        in {
            "typed_blocker",
            "repeat_suppressed_with_typed_blocker",
        }
        or paper_log_classification == "typed_blocker"
    )
    remaining_blockers = (
        list(paper_log.get("remaining_blockers") or [])
        if closeout_marks_typed_blocker
        else []
    )
    explicit_blocker_present = (
        closeout_marks_typed_blocker
        or any(
            _non_empty_text(value) is not None
            for value in (
                closeout.get("typed_blocker_reason"),
                closeout.get("typed_blocker_ref"),
                owner_result.get("blocked_reason"),
                *remaining_blockers,
            )
        )
    )
    if not explicit_blocker_present:
        return {}
    blocker_type = (
        _non_empty_text(embedded.get("blocker_type"))
        or _non_empty_text(embedded.get("blocker_kind"))
        or _non_empty_text(embedded.get("blocker_id"))
        or _non_empty_text(embedded.get("reason"))
        or _non_empty_text(closeout.get("typed_blocker_reason"))
        or _non_empty_text(closeout.get("blocked_reason"))
        or _non_empty_text(owner_result.get("blocked_reason"))
        or _first_text(remaining_blockers)
    )
    if blocker_type is None:
        return {}
    owner = (
        _non_empty_text(embedded.get("owner"))
        or _non_empty_text(embedded.get("next_owner"))
        or _non_empty_text(owner_result.get("owner"))
        or _non_empty_text(closeout.get("next_owner"))
        or _non_empty_text(identity.get("next_executable_owner"))
        or _non_empty_text(identity.get("owner"))
        or "med-autoscience"
    )
    source_ref = (
        _non_empty_text(closeout.get("source_path"))
        or _non_empty_text(closeout.get("typed_blocker_ref"))
        or _non_empty_text(closeout.get("receipt_ref"))
    )
    closeout_refs = _text_items(closeout.get("closeout_refs"))
    if source_ref is None and closeout_refs:
        source_ref = closeout_refs[0]
    payload = {
        **embedded,
        "blocker_type": blocker_type,
        "blocked_reason": blocker_type,
        "owner": owner,
        "action_type": _non_empty_text(closeout.get("action_type"))
        or _non_empty_text(identity.get("action_type")),
        "work_unit_id": _non_empty_text(closeout.get("work_unit_id"))
        or _non_empty_text(identity.get("work_unit_id")),
        "work_unit_fingerprint": _non_empty_text(closeout.get("work_unit_fingerprint"))
        or _non_empty_text(closeout.get("action_fingerprint"))
        or _non_empty_text(identity.get("work_unit_fingerprint"))
        or _non_empty_text(identity.get("action_fingerprint")),
        "action_fingerprint": _non_empty_text(closeout.get("action_fingerprint"))
        or _non_empty_text(closeout.get("work_unit_fingerprint"))
        or _non_empty_text(identity.get("action_fingerprint"))
        or _non_empty_text(identity.get("work_unit_fingerprint")),
        "source_ref": source_ref,
        "typed_blocker_ref": _non_empty_text(closeout.get("typed_blocker_ref")) or source_ref,
        "closeout_refs": closeout_refs,
        "stage_attempt_id": _non_empty_text(closeout.get("stage_attempt_id")),
        "terminal_closeout_status": _non_empty_text(closeout.get("stage_closeout_status"))
        or _non_empty_text(closeout.get("status")),
        "terminal_closeout_outcome": _non_empty_text(closeout.get("outcome"))
        or _non_empty_text(paper_log.get("outcome")),
        "progress_delta_classification": progress_delta_classification,
    }
    return {key: value for key, value in payload.items() if value not in (None, "", [], {})}


def _first_text(value: object) -> str | None:
    for item in _text_items(value):
        return item
    return _non_empty_text(value)


def _accepted_closeout_for_live_attempt(study: Mapping[str, Any]) -> dict[str, Any]:
    live_attempt = _running_attempt_from_study(study)
    if not live_attempt:
        return {}
    for receipt in _accepted_closeout_receipts(study):
        if current_control_receipts.receipt_is_accepted_closeout(
            receipt
        ) and current_control_receipts.receipt_matches_live_attempt(
            receipt,
            live_attempt,
        ):
            return receipt
    return {}


__all__ = [
    "materialize_provider_admission_current_control_state",
    "provider_admission_current_control_study",
]
