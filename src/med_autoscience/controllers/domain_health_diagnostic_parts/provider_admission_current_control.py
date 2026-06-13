from __future__ import annotations

from typing import Any, Mapping

from med_autoscience.controllers.domain_health_diagnostic_parts.managed_wakeup import _non_empty_text
from med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission import (
    provider_attempt_matches_identity,
    study_has_running_provider_attempt,
)
from med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_closeout_semantics import (
    is_anti_loop_stop_loss_closeout,
)
from med_autoscience.controllers.domain_health_diagnostic_parts import (
    provider_admission_current_control_receipts as current_control_receipts,
)
from med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_current_control_identity import (
    accepted_closeout_receipts as _accepted_closeout_receipts,
    attempt_idempotency_key as _attempt_idempotency_key,
    candidate_with_identity as _candidate_with_identity,
    candidate_with_progress_currentness_identity as _candidate_with_progress_currentness_identity,
    missing_identity_fields as _missing_identity_fields,
    provider_admission_current_control_study,
    route_identity_key as _route_identity_key,
    weak_provider_admission_identity as _weak_provider_admission_identity,
)
from med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_helpers import (
    mapping as _mapping,
    text_items as _text_items,
)
from med_autoscience.controllers.owner_route_reconcile_parts import scan_output, supervision_surfaces
from med_autoscience.profiles import WorkspaceProfile

ARBITER_SURFACE_KIND = "mas_opl_stage_route_arbiter"
ARBITER_SCHEMA_VERSION = 1
ARBITER_AUTHORITY_BOUNDARY = {
    "arbiter_surface": "currentness_projection_only",
    "can_write_domain_truth": False,
    "can_authorize_publication_ready": False,
    "provider_completion_is_domain_ready": False,
}


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
        _candidate_with_identity(
            _candidate_with_progress_currentness_identity(
                candidate,
                scanned_studies_by_id=scanned_studies_by_id,
            )
        )
        for candidate in candidates
    ]
    live_studies_by_id = _live_scanned_studies_by_id(scanned_studies)
    arbiter_decisions = _stage_route_arbiter_decisions(
        candidates,
        live_studies_by_id=live_studies_by_id,
        scanned_studies_by_id=scanned_studies_by_id,
    )
    pending_candidates = _candidates_not_covered_by_live_attempt(
        candidates,
        live_studies_by_id=live_studies_by_id,
        scanned_studies_by_id=scanned_studies_by_id,
    )
    terminal_precedence_by_study = _terminal_precedence_by_study(scanned_studies)
    studies = [
        _study_with_terminal_precedence(
            provider_admission_current_control_study(candidate),
            terminal_precedence_by_study=terminal_precedence_by_study,
        )
        for candidate in pending_candidates
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
        },
        workspace_daemon_lifecycle={},
        provider_readiness=None,
        latest_path=latest_path,
        history_path=history_path,
        provider_admission_candidates=[dict(candidate) for candidate in pending_candidates],
    )
    payload["provider_admission_pending_count"] = len(pending_candidates)
    payload["provider_admission_candidates"] = [dict(candidate) for candidate in pending_candidates]
    payload["stage_route_arbiter"] = _stage_route_arbiter_summary(
        decisions=arbiter_decisions,
        candidate_count=len(candidates),
        pending_count=len(pending_candidates),
    )
    payload["stage_route_arbiter_decisions"] = arbiter_decisions
    payload["unscanned_handoff_retention"] = unscanned_audit
    payload["current_control_refresh_source"] = "domain_health_diagnostic.provider_admission_candidates"
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


def _stage_route_arbiter_decisions(
    candidates: list[dict[str, Any]],
    *,
    live_studies_by_id: Mapping[str, Mapping[str, Any]],
    scanned_studies_by_id: Mapping[str, Mapping[str, Any]],
) -> list[dict[str, Any]]:
    decisions: list[dict[str, Any]] = []
    for candidate in candidates:
        study_id = _non_empty_text(candidate.get("study_id"))
        scanned_study = (
            _mapping(scanned_studies_by_id.get(study_id)) if study_id is not None else {}
        )
        terminal_precedence = _terminal_closeout_precedence_evidence(
            scanned_study,
            identity=candidate,
        )
        if terminal_precedence:
            decisions.append(
                _arbiter_decision(
                    candidate,
                    decision="terminal_closeout_precedes_live_projection",
                    effect="suppress_provider_admission_pending",
                    evidence=terminal_precedence,
                )
            )
            continue
        if current_control_receipts.accepted_closeout_matches_identity(
            scanned_study,
            identity=candidate,
        ):
            decisions.append(
                _arbiter_decision(
                    candidate,
                    decision="accepted_closeout_consumed_pending",
                    effect="suppress_provider_admission_pending",
                    evidence=_matching_accepted_closeout(scanned_study, identity=candidate),
                )
            )
            continue
        live_study = _mapping(live_studies_by_id.get(study_id)) if study_id is not None else {}
        live_attempt = _running_attempt_from_study(live_study)
        if live_attempt and provider_attempt_matches_identity(live_attempt, identity=candidate):
            decisions.append(
                _arbiter_decision(
                    candidate,
                    decision="running_identity_observed",
                    effect="suppress_provider_admission_pending",
                    evidence=live_attempt,
                )
            )
            continue
        weak_identity = _current_control_weak_provider_admission_identity(candidate)
        if weak_identity:
            decisions.append(
                _arbiter_decision(
                    candidate,
                    decision="weak_provider_admission_identity",
                    effect="suppress_provider_admission_pending",
                    evidence=weak_identity,
                )
            )
            continue
        typed_blocker_precedence = _current_typed_blocker_precedence_evidence(
            scanned_study,
            identity=candidate,
        )
        if typed_blocker_precedence:
            decisions.append(
                _arbiter_decision(
                    candidate,
                    decision="current_typed_blocker_precedes_provider_admission",
                    effect="suppress_provider_admission_pending",
                    evidence=typed_blocker_precedence,
                )
            )
            continue
        decisions.append(
            _arbiter_decision(
                candidate,
                decision="pending_provider_admission",
                effect="retain_provider_admission_pending",
                evidence={},
            )
        )
    return decisions


def _arbiter_decision(
    candidate: Mapping[str, Any],
    *,
    decision: str,
    effect: str,
    evidence: Mapping[str, Any],
) -> dict[str, Any]:
    evidence_status = _evidence_status(evidence)
    no_progress_signal = _arbiter_no_progress_signal(
        decision=decision,
        evidence_status=evidence_status,
    )
    payload: dict[str, Any] = {
        "surface_kind": "mas_opl_stage_route_arbiter_decision",
        "schema_version": ARBITER_SCHEMA_VERSION,
        "decision": decision,
        "effect": effect,
        "study_id": _non_empty_text(candidate.get("study_id")),
        "quest_id": _non_empty_text(candidate.get("quest_id")),
        "action_type": _non_empty_text(candidate.get("action_type")),
        "work_unit_id": _non_empty_text(candidate.get("work_unit_id")),
        "work_unit_fingerprint": _non_empty_text(candidate.get("work_unit_fingerprint"))
        or _non_empty_text(candidate.get("action_fingerprint")),
        "action_fingerprint": _non_empty_text(candidate.get("action_fingerprint")),
        "route_identity_key": _route_identity_key(candidate),
        "attempt_idempotency_key": _attempt_idempotency_key(candidate),
        "dispatch_path": _non_empty_text(candidate.get("dispatch_path")),
        "dispatch_ref": _non_empty_text(candidate.get("dispatch_ref")),
        "active_stage_attempt_id": _non_empty_text(evidence.get("active_stage_attempt_id"))
        or _non_empty_text(evidence.get("stage_attempt_id")),
        "active_run_id": _non_empty_text(evidence.get("active_run_id")),
        "active_workflow_id": _non_empty_text(evidence.get("active_workflow_id")),
        "missing_identity_fields": _missing_identity_fields(evidence),
        "evidence_status": evidence_status,
        "no_progress_signal": no_progress_signal,
        "anti_loop_classification": _arbiter_anti_loop_classification(no_progress_signal),
        "authority_boundary": dict(ARBITER_AUTHORITY_BOUNDARY),
    }
    return {key: value for key, value in payload.items() if value is not None}


def _arbiter_no_progress_signal(
    *,
    decision: str,
    evidence_status: str | None,
) -> str | None:
    if decision not in {
        "accepted_closeout_consumed_pending",
        "terminal_closeout_precedes_live_projection",
    }:
        return None
    if evidence_status == "repeat_suppressed":
        return "same_work_unit_repeat_suppressed_terminal_stage"
    if evidence_status in {
        "owner_output_already_current",
        "record_only_archive",
    }:
        return "idempotent_noop_without_new_owner_delta"
    return None


def _arbiter_anti_loop_classification(no_progress_signal: str | None) -> str | None:
    if no_progress_signal == "same_work_unit_repeat_suppressed_terminal_stage":
        return "provider_admission_echo"
    if no_progress_signal == "idempotent_noop_without_new_owner_delta":
        return "same_work_unit_no_delta"
    return None


def _stage_route_arbiter_summary(
    *,
    decisions: list[dict[str, Any]],
    candidate_count: int,
    pending_count: int,
) -> dict[str, Any]:
    decision_counts: dict[str, int] = {}
    for decision in decisions:
        key = _non_empty_text(decision.get("decision"))
        if key is None:
            continue
        decision_counts[key] = decision_counts.get(key, 0) + 1
    return {
        "surface_kind": ARBITER_SURFACE_KIND,
        "schema_version": ARBITER_SCHEMA_VERSION,
        "candidate_count": candidate_count,
        "pending_count": pending_count,
        "decision_counts": decision_counts,
        "ordinary_planning_root": "current_owner_delta",
        "authority_boundary": dict(ARBITER_AUTHORITY_BOUNDARY),
    }


def _matching_accepted_closeout(
    study: Mapping[str, Any],
    *,
    identity: Mapping[str, Any],
) -> dict[str, Any]:
    for receipt in _accepted_closeout_receipts(study):
        if current_control_receipts.receipt_identity_inferred_from_current_work_unit(receipt):
            continue
        if current_control_receipts.receipt_is_accepted_closeout(
            receipt
        ) and current_control_receipts.accepted_closeout_matches_candidate_identity(
            receipt,
            identity=identity,
        ):
            return receipt
    return {}


def _terminal_closeout_precedence_evidence(
    study: Mapping[str, Any],
    *,
    identity: Mapping[str, Any],
) -> dict[str, Any]:
    precedence_evidence = _mapping(study.get("terminal_closeout_precedence_evidence"))
    if (
        precedence_evidence
        and current_control_receipts.receipt_is_accepted_closeout(precedence_evidence)
        and provider_attempt_matches_identity(precedence_evidence, identity=identity)
    ):
        return precedence_evidence
    live_attempt = _running_attempt_from_study(study)
    if not live_attempt or not provider_attempt_matches_identity(live_attempt, identity=identity):
        return {}
    closeout = _matching_accepted_closeout(study, identity=identity)
    if not closeout:
        return {}
    if current_control_receipts.receipt_matches_live_attempt(closeout, live_attempt):
        return closeout
    return {}


def _evidence_status(evidence: Mapping[str, Any]) -> str | None:
    return (
        _non_empty_text(evidence.get("status"))
        or _non_empty_text(evidence.get("execution_status"))
        or _non_empty_text(evidence.get("closeout_receipt_status"))
        or _non_empty_text(evidence.get("current_attempt_state"))
        or _non_empty_text(evidence.get("reconciliation_status"))
        or _non_empty_text(evidence.get("stage_closeout_status"))
        or _non_empty_text(_mapping(evidence.get("runtime_health")).get("runtime_liveness_status"))
    )


def _live_scanned_studies_by_id(
    scanned_studies: list[dict[str, Any]] | None,
) -> dict[str, dict[str, Any]]:
    return {
        study_id: dict(study)
        for study in scanned_studies or []
        if (study_id := _non_empty_text(study.get("study_id"))) is not None
        and study_has_running_provider_attempt(study)
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
    if not receipt:
        receipt = _mapping(study.get("current_work_unit")) or _mapping(
            study.get("current_executable_owner_action")
        )
    if not receipt:
        envelope = _mapping(study.get("current_execution_envelope"))
        receipt = {
            "work_unit_id": _non_empty_text(envelope.get("next_work_unit")),
        }
    return {
        key: value
        for key, value in {
            "action_type": _non_empty_text(receipt.get("action_type")),
            "work_unit_id": _non_empty_text(receipt.get("work_unit_id")),
            "work_unit_fingerprint": _non_empty_text(receipt.get("work_unit_fingerprint")),
            "action_fingerprint": _non_empty_text(receipt.get("action_fingerprint")),
            "dispatch_path": _non_empty_text(receipt.get("dispatch_path")),
            "dispatch_ref": _non_empty_text(receipt.get("dispatch_ref")),
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
    explicit_blocker_present = (
        _non_empty_text(embedded.get("surface_kind")) == "mas_domain_typed_blocker"
        or is_anti_loop_stop_loss_closeout(closeout)
        or _non_empty_text(closeout.get("status")) in {"closed_with_typed_blocker"}
        or _non_empty_text(closeout.get("stage_closeout_status")) in {"closed_with_typed_blocker"}
        or _non_empty_text(closeout.get("outcome")) in {
            "typed_blocker",
            "repeat_suppressed_with_typed_blocker",
        }
        or _non_empty_text(closeout.get("stage_closeout_outcome")) in {
            "typed_blocker",
            "repeat_suppressed_with_typed_blocker",
        }
        or any(
            _non_empty_text(value) is not None
            for value in (
                closeout.get("typed_blocker_reason"),
                closeout.get("typed_blocker_ref"),
                paper_log.get("progress_delta_classification")
                if _non_empty_text(paper_log.get("progress_delta_classification")) == "typed_blocker"
                else None,
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
    )
    if blocker_type is None:
        return {}
    owner = (
        _non_empty_text(embedded.get("owner"))
        or _non_empty_text(embedded.get("next_owner"))
        or _non_empty_text(closeout.get("next_owner"))
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
        "progress_delta_classification": _non_empty_text(closeout.get("progress_delta_classification"))
        or _non_empty_text(paper_log.get("progress_delta_classification")),
    }
    return {key: value for key, value in payload.items() if value not in (None, "", [], {})}


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


def _running_attempt_from_study(study: Mapping[str, Any]) -> dict[str, Any]:
    if study_has_running_provider_attempt(study):
        return _mapping(study.get("opl_provider_attempt")) or dict(study)
    nested = _mapping(study.get("opl_provider_attempt"))
    if study_has_running_provider_attempt(nested):
        return nested
    progress_first = _live_attempt_from_progress_first_summary(study)
    if progress_first:
        return progress_first
    current_work_unit = _live_attempt_from_current_work_unit(study)
    if current_work_unit:
        return current_work_unit
    return {}


def _live_attempt_from_progress_first_summary(study: Mapping[str, Any]) -> dict[str, Any]:
    progress_first = _mapping(study.get("progress_first_monitoring_summary"))
    if progress_first.get("running_provider_attempt") is not True:
        return {}
    attempt = _live_attempt_from_mapping(
        progress_first,
        study=study,
        source="progress_first_monitoring_summary.live_provider_attempt",
    )
    if attempt:
        return attempt
    return {}


def _live_attempt_from_current_work_unit(study: Mapping[str, Any]) -> dict[str, Any]:
    current = _mapping(study.get("current_work_unit"))
    state = _mapping(current.get("state"))
    proof = _mapping(state.get("provider_attempt_proof"))
    if proof.get("running_provider_attempt") is not True:
        return {}
    return _live_attempt_from_mapping(
        proof,
        study={**dict(study), "current_work_unit": current},
        source="current_work_unit.provider_attempt_proof",
    )


def _live_attempt_from_mapping(
    payload: Mapping[str, Any],
    *,
    study: Mapping[str, Any],
    source: str,
) -> dict[str, Any]:
    active_run_id = _non_empty_text(payload.get("active_run_id"))
    active_stage_attempt_id = _non_empty_text(payload.get("active_stage_attempt_id")) or _stage_id_from_run_id(
        active_run_id
    )
    active_workflow_id = _non_empty_text(payload.get("active_workflow_id"))
    if (active_stage_attempt_id or active_run_id or active_workflow_id) is None:
        return {}
    runtime_health = _mapping(payload.get("runtime_health")) or _mapping(payload.get("worker_liveness"))
    if runtime_health:
        runtime_liveness = _non_empty_text(runtime_health.get("runtime_liveness_status"))
        health_status = _non_empty_text(runtime_health.get("health_status"))
        if runtime_liveness not in {None, "live", "running"} and health_status not in {
            "live",
            "running",
        }:
            return {}
    current = _mapping(study.get("current_work_unit"))
    current_state = _mapping(current.get("state"))
    basis = _mapping(current.get("currentness_basis"))
    current_action = _mapping(study.get("current_executable_owner_action"))
    return {
        key: value
        for key, value in {
            "running_provider_attempt": True,
            "active_run_id": active_run_id,
            "active_stage_attempt_id": active_stage_attempt_id,
            "active_workflow_id": active_workflow_id,
            "owner": _non_empty_text(payload.get("owner"))
            or _non_empty_text(study.get("next_owner"))
            or _non_empty_text(current.get("owner")),
            "action_type": _non_empty_text(payload.get("action_type"))
            or _non_empty_text(current.get("action_type"))
            or _non_empty_text(current_action.get("action_type")),
            "work_unit_id": _non_empty_text(payload.get("work_unit_id"))
            or _non_empty_text(payload.get("next_work_unit"))
            or _non_empty_text(current.get("work_unit_id"))
            or _non_empty_text(basis.get("work_unit_id")),
            "work_unit_fingerprint": _non_empty_text(payload.get("work_unit_fingerprint"))
            or _non_empty_text(payload.get("action_fingerprint"))
            or _non_empty_text(current.get("work_unit_fingerprint"))
            or _non_empty_text(current.get("action_fingerprint"))
            or _non_empty_text(basis.get("work_unit_fingerprint")),
            "action_fingerprint": _non_empty_text(payload.get("action_fingerprint"))
            or _non_empty_text(payload.get("work_unit_fingerprint"))
            or _non_empty_text(current.get("action_fingerprint"))
            or _non_empty_text(current.get("work_unit_fingerprint"))
            or _non_empty_text(basis.get("work_unit_fingerprint")),
            "runtime_health": runtime_health
            or _mapping(current_state.get("runtime_health"))
            or {"health_status": "running", "runtime_liveness_status": "live"},
            "source": source,
        }.items()
        if value not in (None, "", [], {})
    }


def _stage_id_from_run_id(run_id: str | None) -> str | None:
    if run_id is None:
        return None
    prefix = "opl-stage-attempt://"
    if run_id.startswith(prefix):
        return _non_empty_text(run_id.removeprefix(prefix))
    return None


def _candidates_not_covered_by_live_attempt(
    candidates: list[dict[str, Any]],
    *,
    live_studies_by_id: Mapping[str, Mapping[str, Any]],
    scanned_studies_by_id: Mapping[str, Mapping[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    pending: list[dict[str, Any]] = []
    for candidate in candidates:
        study_id = _non_empty_text(candidate.get("study_id"))
        live_study = _mapping(live_studies_by_id.get(study_id)) if study_id is not None else {}
        live_attempt = _running_attempt_from_study(live_study)
        scanned_study = (
            _mapping((scanned_studies_by_id or {}).get(study_id)) if study_id is not None else {}
        )
        if _terminal_closeout_precedence_evidence(scanned_study, identity=candidate):
            continue
        if current_control_receipts.accepted_closeout_matches_identity(
            scanned_study,
            identity=candidate,
        ):
            continue
        if live_attempt and provider_attempt_matches_identity(live_attempt, identity=candidate):
            continue
        if _current_control_weak_provider_admission_identity(candidate):
            continue
        if _current_typed_blocker_precedence_evidence(scanned_study, identity=candidate):
            continue
        pending.append(dict(candidate))
    return pending


def _current_typed_blocker_precedence_evidence(
    study: Mapping[str, Any],
    *,
    identity: Mapping[str, Any],
) -> dict[str, Any]:
    blocker = _current_typed_blocker(study)
    if not blocker:
        return {}
    expected_action = _non_empty_text(identity.get("action_type"))
    expected_work_unit = _non_empty_text(identity.get("work_unit_id"))
    blocker_action = _non_empty_text(blocker.get("action_type"))
    blocker_work_unit = _non_empty_text(blocker.get("work_unit_id"))
    if expected_action is not None and blocker_action is not None and blocker_action != expected_action:
        return {}
    if expected_work_unit is not None and blocker_work_unit is not None and blocker_work_unit != expected_work_unit:
        return {}
    if expected_action is None and expected_work_unit is None:
        return {}
    if blocker_action is None and blocker_work_unit is None:
        return {}
    return blocker


def _current_typed_blocker(study: Mapping[str, Any]) -> dict[str, Any]:
    current = _mapping(study.get("current_work_unit"))
    current_status = _non_empty_text(current.get("status"))
    if current_status == "typed_blocker":
        state = _mapping(current.get("state"))
        typed_blocker = _mapping(state.get("typed_blocker")) or _mapping(current.get("typed_blocker"))
        return {
            key: value
            for key, value in {
                **typed_blocker,
                "status": "typed_blocker",
                "owner": _non_empty_text(current.get("owner")) or _non_empty_text(typed_blocker.get("owner")),
                "action_type": _non_empty_text(current.get("action_type"))
                or _non_empty_text(typed_blocker.get("action_type")),
                "work_unit_id": _non_empty_text(current.get("work_unit_id"))
                or _non_empty_text(typed_blocker.get("work_unit_id")),
                "work_unit_fingerprint": _non_empty_text(current.get("work_unit_fingerprint"))
                or _non_empty_text(current.get("action_fingerprint"))
                or _non_empty_text(typed_blocker.get("work_unit_fingerprint"))
                or _non_empty_text(typed_blocker.get("action_fingerprint")),
                "source": "current_work_unit.typed_blocker",
                "blocker_type": _non_empty_text(typed_blocker.get("blocker_type"))
                or _non_empty_text(typed_blocker.get("blocker_id"))
                or _non_empty_text(state.get("blocker_type")),
            }.items()
            if value not in (None, "", [], {})
        }
    if current:
        return {}
    envelope = _mapping(study.get("current_execution_envelope"))
    state_kind = _non_empty_text(envelope.get("state_kind")) or _non_empty_text(
        envelope.get("execution_state_kind")
    )
    if state_kind != "typed_blocker":
        return {}
    typed_blocker = _mapping(envelope.get("typed_blocker"))
    return {
        key: value
        for key, value in {
            **typed_blocker,
            "status": "typed_blocker",
            "owner": _non_empty_text(envelope.get("owner")) or _non_empty_text(typed_blocker.get("owner")),
            "action_type": _non_empty_text(typed_blocker.get("action_type")),
            "work_unit_id": _non_empty_text(typed_blocker.get("work_unit_id")),
            "work_unit_fingerprint": _non_empty_text(typed_blocker.get("work_unit_fingerprint"))
            or _non_empty_text(typed_blocker.get("action_fingerprint")),
            "source": "current_execution_envelope.typed_blocker",
            "blocker_type": _non_empty_text(typed_blocker.get("blocker_type"))
            or _non_empty_text(typed_blocker.get("blocker_id"))
            or _non_empty_text(typed_blocker.get("reason")),
        }.items()
        if value not in (None, "", [], {})
    }


def _current_control_weak_provider_admission_identity(identity: Mapping[str, Any]) -> dict[str, Any]:
    weak_identity = _weak_provider_admission_identity(identity)
    if not weak_identity:
        return {}
    current_control_missing = [
        field
        for field in weak_identity.get("missing_identity_fields") or []
        if field
        in {
            "study_id",
            "action_type",
            "work_unit_id",
            "work_unit_fingerprint",
            "dispatch_path_or_ref",
            "currentness_basis",
        }
    ]
    if not current_control_missing:
        return {}
    return {
        "status": "weak_provider_admission_identity",
        "missing_identity_fields": current_control_missing,
    }


__all__ = [
    "materialize_provider_admission_current_control_state",
    "provider_admission_current_control_study",
]
