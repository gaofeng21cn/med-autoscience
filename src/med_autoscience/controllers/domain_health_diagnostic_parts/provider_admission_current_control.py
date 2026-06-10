from __future__ import annotations

from typing import Any, Mapping

from med_autoscience.controllers.domain_health_diagnostic_parts.managed_wakeup import _non_empty_text
from med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission import (
    provider_attempt_matches_identity,
    study_has_running_provider_attempt,
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
    live_studies_by_id = _live_scanned_studies_by_id(scanned_studies)
    pending_candidates = _candidates_not_covered_by_live_attempt(
        candidates,
        live_studies_by_id=live_studies_by_id,
        scanned_studies_by_id={
            study_id: dict(study)
            for study in scanned_studies or []
            if (study_id := _non_empty_text(study.get("study_id"))) is not None
        },
    )
    studies = [
        provider_admission_current_control_study(candidate) for candidate in pending_candidates
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
                "latest_action_count": len(output_actions),
                "source": "domain_health_diagnostic.provider_admission_candidates",
            },
        )
    payload["written"] = bool(apply)
    return payload


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
    return payload


def _scanned_study_with_accepted_closeout_projection(study: Mapping[str, Any]) -> dict[str, Any]:
    payload = dict(study)
    if payload.get("running_provider_attempt") is True:
        return payload
    if not _accepted_closeout_matches_identity(payload, identity=_closeout_identity(payload)):
        return payload
    payload.update(
        {
            "action_queue": [],
            "provider_admission_candidates": [],
            "provider_admission_pending_count": 0,
        }
    )
    return payload


def _closeout_identity(study: Mapping[str, Any]) -> dict[str, Any]:
    receipt = _mapping(study.get("default_executor_execution_receipt_consumption")) or _mapping(
        study.get("opl_provider_attempt")
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
        }.items()
        if value is not None
    }


def _running_attempt_from_study(study: Mapping[str, Any]) -> dict[str, Any]:
    if study_has_running_provider_attempt(study):
        return _mapping(study.get("opl_provider_attempt")) or dict(study)
    nested = _mapping(study.get("opl_provider_attempt"))
    if study_has_running_provider_attempt(nested):
        return nested
    return {}


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
        if live_attempt and provider_attempt_matches_identity(live_attempt, identity=candidate):
            continue
        scanned_study = (
            _mapping((scanned_studies_by_id or {}).get(study_id)) if study_id is not None else {}
        )
        if _accepted_closeout_matches_identity(scanned_study, identity=candidate):
            continue
        pending.append(dict(candidate))
    return pending


def _accepted_closeout_matches_identity(
    study: Mapping[str, Any],
    *,
    identity: Mapping[str, Any],
) -> bool:
    if not _identity_has_match_key(identity):
        return False
    for receipt in (
        _mapping(study.get("default_executor_execution_receipt_consumption")),
        _mapping(study.get("opl_provider_attempt")),
    ):
        if not receipt:
            continue
        if _receipt_is_accepted_closeout(receipt) and provider_attempt_matches_identity(
            receipt,
            identity=identity,
        ):
            return True
    return False


def _identity_has_match_key(identity: Mapping[str, Any]) -> bool:
    return any(
        _non_empty_text(identity.get(key)) is not None
        for key in (
            "action_type",
            "work_unit_id",
            "work_unit_fingerprint",
            "action_fingerprint",
            "dispatch_path",
            "dispatch_ref",
        )
    )


def _receipt_is_accepted_closeout(receipt: Mapping[str, Any]) -> bool:
    statuses = {
        _non_empty_text(receipt.get("execution_status")),
        _non_empty_text(receipt.get("closeout_receipt_status")),
        _non_empty_text(receipt.get("current_attempt_state")),
        _non_empty_text(receipt.get("reconciliation_status")),
    }
    return "accepted_typed_closeout" in statuses


def provider_admission_current_control_study(candidate: Mapping[str, Any]) -> dict[str, Any]:
    action = _provider_admission_current_control_action(candidate)
    owner_route = _mapping(action.get("owner_route"))
    study_id = _non_empty_text(candidate.get("study_id"))
    return {
        "study_id": study_id,
        "quest_id": _non_empty_text(candidate.get("quest_id")),
        "handoff_generated_at": _non_empty_text(candidate.get("recorded_at")),
        "handoff_scan_status": "provider_admission_from_mas_handoff",
        "study_root": _non_empty_text(candidate.get("study_root")),
        "quest_status": "provider_admission_pending",
        "active_run_id": None,
        "active_stage_attempt_id": None,
        "active_workflow_id": None,
        "running_provider_attempt": False,
        "runtime_health": {
            "health_status": "provider_admission_pending",
            "runtime_liveness_status": "not_running",
            "blocked_reason": _non_empty_text(candidate.get("blocked_reason")),
            "summary": "Current MAS owner action is ready for OPL provider admission.",
        },
        "action_queue": [action],
        "provider_admission_identity": dict(candidate),
        "provider_admission_candidates": [dict(candidate)],
        "provider_admission_pending_count": 1,
        "why_not_applied": ["provider_admission_current_control_state_required"],
        "blocked_reason": "provider_admission_current_control_state_required",
        "next_owner": "one-person-lab",
        "external_supervisor_required": True,
        "owner_route": owner_route,
        "current_execution_envelope": {
            "state_kind": "executable_owner_action",
            "owner": _non_empty_text(candidate.get("next_executable_owner")) or "one-person-lab",
            "next_work_unit": _non_empty_text(candidate.get("work_unit_id")),
            "typed_blocker": None,
            "parked_state": None,
            "source": "mas_provider_admission_identity",
        },
    }


def _provider_admission_current_control_action(candidate: Mapping[str, Any]) -> dict[str, Any]:
    action_type = _non_empty_text(candidate.get("action_type"))
    study_id = _non_empty_text(candidate.get("study_id"))
    work_unit_id = _non_empty_text(candidate.get("work_unit_id"))
    action_fingerprint = _non_empty_text(candidate.get("action_fingerprint")) or _non_empty_text(
        candidate.get("work_unit_fingerprint")
    )
    source_refs = {
        key: value
        for key, value in {
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": action_fingerprint,
            "provider_admission_identity_ref": _non_empty_text(candidate.get("execution_ref")),
            "dispatch_path": _non_empty_text(candidate.get("dispatch_path")),
            "blocked_reason": _non_empty_text(candidate.get("blocked_reason")),
        }.items()
        if value is not None
    }
    owner_route = {
        "surface": "domain_route_owner_route",
        "schema_version": 2,
        "study_id": study_id,
        "quest_id": _non_empty_text(candidate.get("quest_id")),
        "truth_epoch": _non_empty_text(_mapping(candidate.get("currentness_basis")).get("truth_epoch"))
        or action_fingerprint,
        "runtime_health_epoch": _non_empty_text(
            _mapping(candidate.get("currentness_basis")).get("runtime_health_epoch")
        )
        or action_fingerprint,
        "work_unit_fingerprint": action_fingerprint,
        "failure_signature": action_type,
        "trace_id": f"provider-admission::{study_id}::{action_type}",
        "route_epoch": action_fingerprint,
        "source_fingerprint": action_fingerprint,
        "current_owner": "med-autoscience",
        "next_owner": _non_empty_text(candidate.get("next_executable_owner")),
        "owner_reason": work_unit_id or action_type,
        "active_run_id": None,
        "allowed_actions": [action_type] if action_type is not None else [],
        "blocked_actions": [],
        "source_refs": {
            **source_refs,
            "owner_route_currentness_basis": dict(_mapping(candidate.get("currentness_basis"))),
        },
        "idempotency_key": f"provider-admission::{study_id}::{action_fingerprint}",
    }
    return {
        key: value
        for key, value in {
            "study_id": study_id,
            "quest_id": _non_empty_text(candidate.get("quest_id")),
            "action_type": action_type,
            "action_id": f"provider-admission::{study_id}::{action_type}",
            "status": "queued",
            "reason": _non_empty_text(candidate.get("blocked_reason")) or "provider_admission_pending",
            "owner": _non_empty_text(candidate.get("next_executable_owner")),
            "request_owner": _non_empty_text(candidate.get("next_executable_owner")),
            "recommended_owner": _non_empty_text(candidate.get("next_executable_owner")),
            "authority": "mas_provider_admission_identity",
            "required_output_surface": _non_empty_text(candidate.get("required_output_surface")),
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": action_fingerprint,
            "action_fingerprint": action_fingerprint,
            "source_surface": "mas_opl_runtime_owner_handoff.provider_admission_identity",
            "source_ref": _non_empty_text(candidate.get("execution_ref")),
            "provider_attempt_or_lease_required": True,
            "provider_completion_is_domain_completion": False,
            "dispatch_path": _non_empty_text(candidate.get("dispatch_path")),
            "blocked_reason": _non_empty_text(candidate.get("blocked_reason")),
            "owner_route": owner_route,
            "handoff_packet": {
                "surface": "provider_admission_current_control_handoff",
                "authority": "mas_provider_admission_identity",
                "owner": _non_empty_text(candidate.get("next_executable_owner")),
                "request_owner": _non_empty_text(candidate.get("next_executable_owner")),
                "recommended_owner": _non_empty_text(candidate.get("next_executable_owner")),
                "next_executable_owner": _non_empty_text(candidate.get("next_executable_owner")),
                "required_output_surface": _non_empty_text(candidate.get("required_output_surface")),
                "next_work_unit": work_unit_id,
                "work_unit_fingerprint": action_fingerprint,
                "source_ref": _non_empty_text(candidate.get("execution_ref")),
                "owner_route": owner_route,
            },
        }.items()
        if value is not None
    }


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


__all__ = [
    "materialize_provider_admission_current_control_state",
    "provider_admission_current_control_study",
]
