from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from med_autoscience.profiles import WorkspaceProfile
from med_autoscience.developer_supervisor_mode import resolve_developer_supervisor_mode

from . import developer_apply_gate
from .. import domain_status_projection
from .. import domain_transition_currentness
from ..paper_mission_owner_surface import current_controller_authorization


SURFACE = "current_controller_decision_refresh"


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _read_json_object(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return dict(payload) if isinstance(payload, Mapping) else None


def refresh_controller_decision_after_ai_reviewer_eval(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    study_root: Path,
    apply: bool = True,
    source: str = "ai_reviewer_publication_eval_workflow",
) -> dict[str, Any]:
    try:
        status = domain_status_projection.progress_projection(
            profile=profile,
            study_id=study_id,
            study_root=study_root,
            entry_mode=None,
        )
        status_payload = dict(status) if isinstance(status, Mapping) else status.to_dict()
    except (OSError, TypeError, ValueError, RuntimeError) as exc:
        return {
            "refresh_status": "blocked",
            "blocked_reason": "progress_projection_unavailable",
            "error": str(exc),
        }
    tick_request_result = _controller_refresh_tick_request(study_root=study_root, status_payload=status_payload)
    if tick_request_result.get("refresh_status") == "blocked":
        return tick_request_result
    tick_request_payload = tick_request_result.get("tick_request")
    if tick_request_payload is None:
        return {
            "refresh_status": "skipped",
            "skipped_reason": "outer_loop_tick_request_unavailable",
        }
    tick_request = _mapping(tick_request_payload)
    if not apply:
        return _dry_run_refresh(study_id=study_id, tick_request=tick_request)
    return _materialize_controller_refresh(
        profile=profile,
        study_id=study_id,
        study_root=study_root,
        status_payload=status_payload,
        tick_request=tick_request,
        source=source,
    )


def refresh_controller_decisions_for_current_publication_eval(
    *,
    profile: WorkspaceProfile,
    study_ids: Iterable[str],
    mode: str,
    apply: bool,
    generated_at: str,
    schema_version: int,
    resolve_study_ids,
    study_root,
) -> dict[str, Any]:
    developer_mode = resolve_developer_supervisor_mode(
        requested_mode=mode,
        apply_safe_actions=apply,
        scheduler_owner="controller_decision_refresh",
    )
    developer_mode_payload = developer_mode.to_dict()
    if apply and developer_apply_gate.blocked(developer_mode_payload):
        return {
            "surface": SURFACE,
            "schema_version": schema_version,
            "generated_at": generated_at,
            "workspace_root": str(profile.workspace_root),
            "dry_run": False,
            "requested_mode": mode,
            "effective_mode": developer_mode.mode,
            "developer_supervisor_mode": developer_mode_payload,
            "refresh_count": 0,
            "materialized_count": 0,
            "blocked_count": 1,
            "skipped_count": 0,
            "refreshes": [
                {
                    "refresh_status": "blocked",
                    "blocked_reason": developer_apply_gate.block_reason(developer_mode_payload)
                    or "developer_apply_safe_required",
                }
            ],
        }
    resolved_study_ids = resolve_study_ids(profile, study_ids)
    refreshes = [
        {
            "study_id": study_id,
            **refresh_controller_decision_after_ai_reviewer_eval(
                profile=profile,
                study_id=study_id,
                study_root=study_root(profile, study_id),
                apply=apply,
                source=SURFACE,
            ),
        }
        for study_id in resolved_study_ids
    ]
    return {
        "surface": SURFACE,
        "schema_version": schema_version,
        "generated_at": generated_at,
        "workspace_root": str(profile.workspace_root),
        "dry_run": not apply,
        "requested_mode": mode,
        "effective_mode": developer_mode.mode,
        "developer_supervisor_mode": developer_mode_payload,
        "requested_studies": list(resolved_study_ids),
        "refresh_count": len(refreshes),
        "materialized_count": sum(item.get("refresh_status") == "materialized" for item in refreshes),
        "blocked_count": sum(item.get("refresh_status") == "blocked" for item in refreshes),
        "skipped_count": sum(item.get("refresh_status") == "skipped" for item in refreshes),
        "dry_run_count": sum(item.get("refresh_status") == "dry_run" for item in refreshes),
        "paper_package_mutation_allowed": False,
        "quality_gate_relaxation_allowed": False,
        "manual_study_patch_allowed": False,
        "medical_claim_authoring_allowed": False,
        "refreshes": refreshes,
    }


def _dry_run_refresh(*, study_id: str, tick_request: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "refresh_status": "dry_run",
        "study_id": study_id,
        "publication_eval_ref": dict(tick_request.get("publication_eval_ref") or {}),
        "decision_type": _text(tick_request.get("decision_type")),
        "work_unit_fingerprint": _text(tick_request.get("work_unit_fingerprint")),
        "next_work_unit": dict(tick_request.get("next_work_unit")) if isinstance(tick_request.get("next_work_unit"), Mapping) else None,
        "blocking_work_units": list(tick_request.get("blocking_work_units") or []),
    }


def _materialize_controller_refresh(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    study_root: Path,
    status_payload: Mapping[str, Any],
    tick_request: Mapping[str, Any],
    source: str,
) -> dict[str, Any]:
    from .. import study_outer_loop

    try:
        refresh_result = study_outer_loop.materialize_non_dispatching_outer_loop_decision(
            profile=profile,
            study_id=study_id,
            study_root=study_root,
            status_payload=status_payload,
            charter_ref=tick_request["charter_ref"],
            publication_eval_ref=tick_request["publication_eval_ref"],
            decision_type=tick_request["decision_type"],
            route_target=tick_request.get("route_target"),
            route_key_question=tick_request.get("route_key_question"),
            route_rationale=tick_request.get("route_rationale"),
            source_route_key_question=tick_request.get("source_route_key_question"),
            work_unit_fingerprint=tick_request.get("work_unit_fingerprint"),
            next_work_unit=tick_request.get("next_work_unit"),
            blocking_work_units=tick_request.get("blocking_work_units") or [],
            requires_human_confirmation=bool(tick_request.get("requires_human_confirmation")),
            controller_actions=tick_request.get("controller_actions") or [],
            reason=str(tick_request.get("reason") or ""),
            source=source,
        )
    except (OSError, TypeError, ValueError, RuntimeError) as exc:
        return {
            "refresh_status": "blocked",
            "blocked_reason": "non_dispatching_controller_decision_materialization_failed",
            "error": str(exc),
        }
    runtime_authorization = authorize_current_controller_decision_after_refresh(
        profile=profile,
        study_id=study_id,
        study_root=study_root,
        status_payload=status_payload,
        tick_request=tick_request,
        source=source,
    )
    return {
        "refresh_status": "materialized",
        **dict(refresh_result),
        "runtime_authorization": runtime_authorization,
    }


def _controller_refresh_tick_request(
    *,
    study_root: Path,
    status_payload: Mapping[str, Any],
) -> dict[str, Any]:
    from .. import study_outer_loop

    try:
        tick_request = study_outer_loop.build_runtime_readback_outer_loop_tick_request(
            study_root=study_root,
            status_payload=status_payload,
        )
    except (OSError, TypeError, ValueError, RuntimeError) as exc:
        return {
            "refresh_status": "blocked",
            "blocked_reason": "outer_loop_tick_request_failed",
            "error": str(exc),
        }
    fallback_tick_request = domain_transition_currentness.status_domain_transition_tick_request(
        study_root=study_root,
        status_payload=status_payload,
    )
    if isinstance(fallback_tick_request, dict) and not _tick_request_matches_status_transition(
        tick_request=tick_request,
        status_payload=status_payload,
    ):
        tick_request = fallback_tick_request
    return {"refresh_status": "ok", "tick_request": tick_request}


def _tick_request_matches_status_transition(
    *,
    tick_request: object,
    status_payload: Mapping[str, Any],
) -> bool:
    fallback_transition = (
        status_payload.get("domain_transition") if isinstance(status_payload.get("domain_transition"), Mapping) else {}
    )
    fallback_transition_unit = (
        fallback_transition.get("next_work_unit") if isinstance(fallback_transition.get("next_work_unit"), Mapping) else {}
    )
    return domain_transition_currentness.tick_request_matches_domain_transition(
        tick_request=tick_request if isinstance(tick_request, Mapping) else {},
        transition_action=str(fallback_transition.get("controller_action") or "").strip(),
        transition_type=str(fallback_transition.get("decision_type") or "").strip(),
        transition_unit_id=str(fallback_transition_unit.get("unit_id") or "").strip(),
        transition_route_target=str(fallback_transition.get("route_target") or "").strip() or None,
    )




def authorize_current_controller_decision_after_refresh(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    study_root: Path,
    status_payload: Mapping[str, Any],
    tick_request: Mapping[str, Any],
    source: str,
) -> dict[str, Any]:
    _ = profile
    publication_eval_payload = publication_eval_payload_for_tick(tick_request)
    if publication_eval_payload is None:
        return {
            "authorization_status": "skipped",
            "skipped_reason": "publication_eval_payload_unavailable",
            "opl_action_status": "skipped",
        }
    authorization = current_controller_authorization.current_controller_authorization_payload(
        study_root=study_root,
        publication_eval_payload=publication_eval_payload,
        read_json_object=_read_json_object,
        allow_specificity_work_unit=False,
    )
    if authorization is None:
        authorization = current_controller_authorization.story_surface_delta_authorization_payload(
            study_root=study_root,
            publication_eval_payload=publication_eval_payload,
            read_json_object=_read_json_object,
        )
    if authorization is None:
        return {
            "authorization_status": "skipped",
            "skipped_reason": "current_controller_authorization_missing",
            "opl_action_status": "skipped",
        }
    quest_id = _text(status_payload.get("quest_id"))
    handoff = {
        "surface_kind": "mas_controller_authorization_opl_action_request",
        "study_id": study_id,
        "quest_id": quest_id,
        "source": source,
        "requested_opl_action": "run_stage_attempt",
        "work_unit_id": _text(authorization.get("work_unit_id")),
        "work_unit_fingerprint": _text(authorization.get("work_unit_fingerprint")),
        "owner_answer": dict(authorization),
        "typed_blocker": {
            "blocker_type": "opl_stage_attempt_required",
            "owner": "one-person-lab",
            "domain_owner": "med-autoscience",
            "reason": "current_controller_authorization_ready",
        },
        "authority_boundary": {
            "mas_writes_generic_runtime_queue": False,
            "mas_writes_runtime_state": False,
            "mas_submits_runtime_chat": False,
            "mas_resumes_provider_worker": False,
            "opl_writes_mas_truth": False,
            "mas_owner_receipt_required": True,
        },
    }
    return {
        "authorization_status": "owner_handoff_ready",
        "current_controller_authorization": dict(authorization),
        "opl_action_status": "owner_route_required",
        "queue_owner": "one-person-lab",
        "recommended_task_kind": "stage_outcome/opl-handoff",
        "runtime_owner_handoff": handoff,
    }

def publication_eval_payload_for_tick(tick_request: Mapping[str, Any]) -> dict[str, Any] | None:
    publication_eval_ref = tick_request.get("publication_eval_ref")
    publication_eval_path = _text(publication_eval_ref.get("artifact_path")) if isinstance(publication_eval_ref, Mapping) else None
    if publication_eval_path is None:
        return None
    return _read_json_object(Path(publication_eval_path))


__all__ = [
    "authorize_current_controller_decision_after_refresh",
    "refresh_controller_decision_after_ai_reviewer_eval",
    "publication_eval_payload_for_tick",
]
