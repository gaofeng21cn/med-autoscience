from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.profiles import WorkspaceProfile

from .. import domain_status_projection
from .. import domain_transition_currentness
from ..owner_route_reconcile_parts import current_controller_authorization, pending_user_messages
from ..owner_route_reconcile_parts import opl_pending_user_message_handoff


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


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(payload), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _append_json_line(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(dict(payload), ensure_ascii=False, sort_keys=True) + "\n")


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
        tick_request = study_outer_loop.build_domain_health_diagnostic_outer_loop_tick_request(
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
    runtime_state_path = runtime_state_path_for_status(profile=profile, status_payload=status_payload)
    if runtime_state_path is None:
        return {
            "authorization_status": "skipped",
            "skipped_reason": "runtime_state_path_unavailable",
            "runtime_resume_status": "skipped",
        }
    publication_eval_payload = publication_eval_payload_for_tick(tick_request)
    if publication_eval_payload is None:
        return {
            "authorization_status": "skipped",
            "skipped_reason": "publication_eval_payload_unavailable",
            "runtime_state_path": str(runtime_state_path),
            "runtime_resume_status": "skipped",
        }
    quest_id = _text(status_payload.get("quest_id"))
    authorization = _current_controller_authorization_handoff(
        runtime_state_path=runtime_state_path,
        study_root=study_root,
        study_id=study_id,
        quest_id=quest_id,
        publication_eval_payload=publication_eval_payload,
    )
    if authorization is None:
        return {
            "authorization_status": "skipped",
            "skipped_reason": "current_controller_authorization_missing",
            "runtime_state_path": str(runtime_state_path),
            "runtime_resume_status": "skipped",
        }
    if authorization.get("written") is not True and authorization.get("handoff_ready") is not True:
        if _text(authorization.get("reason")) == "pending_user_messages_present":
            return _resume_existing_pending_user_message(
                profile=profile,
                study_id=study_id,
                study_root=study_root,
                quest_id=quest_id,
                runtime_state_path=runtime_state_path,
                authorization=authorization,
                source=source,
            )
        return {
            "authorization_status": "blocked",
            "blocked_reason": _text(authorization.get("reason")) or "current_controller_authorization_not_written",
            "current_controller_authorization": authorization,
            "runtime_resume_status": "skipped",
        }
    return _request_runtime_resume(
        profile=profile,
        study_id=study_id,
        study_root=study_root,
        authorization_status="owner_handoff_ready",
        authorization=authorization,
        source=source,
    )


def _resume_existing_pending_user_message(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    study_root: Path,
    quest_id: str | None,
    runtime_state_path: Path,
    authorization: Mapping[str, Any],
    source: str,
) -> dict[str, Any]:
    pending_resume = opl_pending_user_message_handoff.mark_existing_pending_user_message_handoff(
        runtime_state_path=runtime_state_path,
        study_id=study_id,
        quest_id=quest_id,
        source=source,
        runtime_state=_read_json_object(runtime_state_path),
    )
    if pending_resume.get("marked") is not True:
        return {
            "authorization_status": "blocked",
            "blocked_reason": _text(pending_resume.get("reason")) or "existing_pending_user_message_redrive_not_marked",
            "current_controller_authorization": dict(authorization),
            "existing_pending_user_message_resume": pending_resume,
            "runtime_resume_status": "skipped",
        }
    return _request_runtime_resume(
        profile=profile,
        study_id=study_id,
        study_root=study_root,
        authorization_status="pending_user_message_owner_handoff_ready",
        authorization=authorization,
        source=source,
        existing_pending_user_message_resume=pending_resume,
    )


def _request_runtime_resume(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    study_root: Path,
    authorization_status: str,
    authorization: Mapping[str, Any],
    source: str,
    existing_pending_user_message_resume: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    active_prompt_refresh = _runtime_owner_prompt_refresh_handoff(
        profile=profile,
        study_id=study_id,
        study_root=study_root,
        authorization=authorization,
        source=source,
    )
    payload = {
        "authorization_status": authorization_status,
        "current_controller_authorization": dict(authorization),
        "runtime_resume_status": "owner_route_required",
        "queue_owner": "one-person-lab",
        "delegated_runtime_owner": "one-person-lab",
        "runtime_state_mutated": False,
        "recommended_task_kind": "domain_route/owner-handoff",
        "runtime_owner_handoff": {
            "surface_kind": "mas_controller_authorization_runtime_handoff",
            "study_id": study_id,
            "quest_id": _text(authorization.get("quest_id")),
            "source": source,
            "runtime_state_path": _text(authorization.get("path")),
            "work_unit_id": _text(authorization.get("work_unit_id")),
            "work_unit_fingerprint": _text(authorization.get("work_unit_fingerprint")),
            "queue_owner": "one-person-lab",
            "domain_truth_owner": "med-autoscience",
            "recommended_task_kind": "domain_route/owner-handoff",
            "authority_boundary": {
                "mas_writes_generic_runtime_queue": False,
                "mas_submits_runtime_chat": False,
                "mas_resumes_provider_worker": False,
                "opl_writes_mas_truth": False,
                "mas_owner_receipt_required": True,
            },
        },
    }
    if active_prompt_refresh is not None:
        payload["active_prompt_refresh"] = active_prompt_refresh
    if existing_pending_user_message_resume is not None:
        payload["existing_pending_user_message_resume"] = dict(existing_pending_user_message_resume)
    return payload


def _runtime_owner_prompt_refresh_handoff(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    study_root: Path,
    authorization: Mapping[str, Any],
    source: str,
) -> dict[str, Any] | None:
    _ = (profile, study_id, study_root, source)
    alignment = _active_prompt_alignment(authorization=authorization)
    if alignment.get("status") not in {"prompt_unavailable", "stale"}:
        return None
    return {
        **alignment,
        "status": "owner_route_required",
        "reason": "active_codex_prompt_stale_for_current_controller_authorization",
        "queue_owner": "one-person-lab",
        "runtime_state_mutated": False,
        "recommended_task_kind": "domain_route/owner-handoff",
    }


def _current_controller_authorization_handoff(
    *,
    runtime_state_path: Path,
    study_root: Path,
    study_id: str,
    quest_id: str | None,
    publication_eval_payload: Mapping[str, Any],
) -> dict[str, Any] | None:
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
        return None
    runtime_state = _read_json_object(runtime_state_path)
    if runtime_state is None:
        return {"written": False, "handoff_ready": False, "reason": "runtime_state_missing_or_invalid", "path": str(runtime_state_path)}
    if pending_user_messages.pending_count(runtime_state) > 0:
        return {"written": False, "handoff_ready": False, "reason": "pending_user_messages_present", "path": str(runtime_state_path), **authorization}
    clearable_keys: list[str] = []
    for key in (
        "retry_state",
        "last_stage_fingerprint",
        "last_stage_fingerprint_at",
        "blocked_turn_closeout",
        "last_liveness_reconcile_reason",
    ):
        if key in runtime_state:
            clearable_keys.append(key)
    return {
        "written": False,
        "handoff_ready": True,
        "runtime_state_mutated": False,
        "events_jsonl_mutated": False,
        "delegated_runtime_owner": "one-person-lab",
        "path": str(runtime_state_path),
        "study_id": study_id,
        "quest_id": _text(runtime_state.get("quest_id")) or quest_id,
        "cleared_keys": clearable_keys,
        "proposed_runtime_state": {
            "continuation_policy": "auto",
            "continuation_anchor": "decision",
            "continuation_reason": "controller_work_unit_pending",
            "last_controller_decision_authorization": authorization,
            "same_fingerprint_auto_turn_count": 0,
        },
        **authorization,
    }


def _active_prompt_alignment(*, authorization: Mapping[str, Any]) -> dict[str, Any]:
    runtime_state_path = _text(authorization.get("path"))
    if runtime_state_path is None:
        return {"status": "runtime_state_path_unavailable"}
    runtime_state = _read_json_object(Path(runtime_state_path))
    if runtime_state is None:
        return {"status": "runtime_state_missing_or_invalid", "runtime_state_path": runtime_state_path}
    active_run_id = _text(runtime_state.get("active_run_id"))
    if runtime_state.get("worker_running") is not True or active_run_id is None:
        return {
            "status": "no_live_active_prompt",
            "runtime_state_path": runtime_state_path,
            "active_run_id": active_run_id,
        }
    prompt_path = Path(runtime_state_path).parent / "runs" / active_run_id / "prompt.md"
    expected_fingerprint = _text(authorization.get("work_unit_fingerprint"))
    expected_work_unit_id = _text(authorization.get("work_unit_id"))
    try:
        prompt_text = prompt_path.read_text(encoding="utf-8")
    except OSError:
        return {
            "status": "prompt_unavailable",
            "runtime_state_path": runtime_state_path,
            "active_run_id": active_run_id,
            "prompt_path": str(prompt_path),
            "expected_work_unit_fingerprint": expected_fingerprint,
            "expected_work_unit_id": expected_work_unit_id,
        }
    fingerprint_matches = expected_fingerprint is not None and expected_fingerprint in prompt_text
    work_unit_matches = expected_work_unit_id is not None and expected_work_unit_id in prompt_text
    status = "aligned" if fingerprint_matches or work_unit_matches else "stale"
    return {
        "status": status,
        "runtime_state_path": runtime_state_path,
        "active_run_id": active_run_id,
        "stale_active_run_id": active_run_id if status == "stale" else None,
        "prompt_path": str(prompt_path),
        "expected_work_unit_fingerprint": expected_fingerprint,
        "expected_work_unit_id": expected_work_unit_id,
        "fingerprint_matches": fingerprint_matches,
        "work_unit_matches": work_unit_matches,
    }


def runtime_state_path_for_status(
    *,
    profile: WorkspaceProfile,
    status_payload: Mapping[str, Any],
) -> Path | None:
    quest_root = _text(status_payload.get("quest_root"))
    if quest_root is not None:
        return Path(quest_root).expanduser().resolve() / ".ds" / "runtime_state.json"
    quest_id = _text(status_payload.get("quest_id"))
    if quest_id is None:
        return None
    return Path(profile.runtime_root).expanduser().resolve() / quest_id / ".ds" / "runtime_state.json"


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
    "runtime_state_path_for_status",
]
