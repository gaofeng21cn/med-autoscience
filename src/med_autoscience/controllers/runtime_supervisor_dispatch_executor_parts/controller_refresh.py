from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.profiles import WorkspaceProfile

from .. import study_runtime_router
from ..runtime_supervisor_scan_parts import platform_current_controller, platform_repair_pending_redrive


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


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
    authorization = platform_current_controller.write_current_controller_authorization(
        runtime_state_path=runtime_state_path,
        study_root=study_root,
        study_id=study_id,
        quest_id=quest_id,
        publication_eval_payload=publication_eval_payload,
        read_json_object=_read_json_object,
        write_json=_write_json,
        append_json_line=_append_json_line,
        continuation_reason="controller_work_unit_pending",
        repair_clear_reason="ai_reviewer_controller_decision_refresh",
        repair_extra={"controller_decision_refresh_source": source},
    )
    if authorization is None:
        return {
            "authorization_status": "skipped",
            "skipped_reason": "current_controller_authorization_missing",
            "runtime_state_path": str(runtime_state_path),
            "runtime_resume_status": "skipped",
        }
    if authorization.get("written") is not True:
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
        authorization_status="written",
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
    pending_resume = platform_repair_pending_redrive.mark_existing_pending_user_message_redrive(
        runtime_state_path=runtime_state_path,
        study_id=study_id,
        quest_id=quest_id,
        source=source,
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
        authorization_status="pending_user_message_redrive_marked",
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
    try:
        resume_result = study_runtime_router.ensure_study_runtime(
            profile=profile,
            study_id=study_id,
            study_root=study_root,
            source=source,
        )
    except (OSError, TypeError, ValueError, RuntimeError) as exc:
        payload: dict[str, Any] = {
            "authorization_status": authorization_status,
            "current_controller_authorization": dict(authorization),
            "runtime_resume_status": "blocked",
            "runtime_resume_blocked_reason": "ensure_study_runtime_failed",
            "error": str(exc),
        }
        if existing_pending_user_message_resume is not None:
            payload["existing_pending_user_message_resume"] = dict(existing_pending_user_message_resume)
        return payload
    payload = {
        "authorization_status": authorization_status,
        "current_controller_authorization": dict(authorization),
        "runtime_resume_status": "requested",
        "resume_result": dict(resume_result) if isinstance(resume_result, Mapping) else resume_result,
    }
    if existing_pending_user_message_resume is not None:
        payload["existing_pending_user_message_resume"] = dict(existing_pending_user_message_resume)
    return payload


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
    "publication_eval_payload_for_tick",
    "runtime_state_path_for_status",
]
