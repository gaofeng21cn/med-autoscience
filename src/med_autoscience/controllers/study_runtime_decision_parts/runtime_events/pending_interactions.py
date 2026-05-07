from __future__ import annotations

if __name__ != "med_autoscience.controllers.study_runtime_decision":
    from .runtime_summary import *  # noqa: F403


def _find_pending_interaction_artifact_path(
    *,
    quest_root: Path,
    interaction_id: str,
    legacy_restore_import_diagnostic: bool = False,
) -> Path | None:
    resolved_interaction_id = str(interaction_id or "").strip()
    if not resolved_interaction_id:
        return None
    candidates: list[Path] = []
    patterns = [f"artifacts/*/{resolved_interaction_id}.json"]
    if legacy_restore_import_diagnostic or quest_state.is_legacy_restore_import_context(quest_root):
        patterns.append(f".ds/worktrees/*/artifacts/*/{resolved_interaction_id}.json")
    for pattern in patterns:
        candidates.extend(quest_root.glob(pattern))
    return quest_state.find_latest(candidates)


def _controller_stop_source(stop_reason: str | None) -> str | None:
    normalized = str(stop_reason or "").strip()
    if not normalized.startswith("controller_stop:"):
        return None
    source = normalized.split(":", 1)[1].strip()
    return source or None


def _controller_stop_is_auto_recoverable(
    *,
    stop_reason: str | None,
    publication_gate_report: dict[str, object] | None,
) -> bool:
    stop_source = _controller_stop_source(stop_reason)
    if stop_source not in _AUTO_RECOVERY_CONTROLLER_STOP_SOURCES:
        return False
    return _publication_supervisor_requests_automated_continuation(
        publication_gate_report,
        require_blocked_status=True,
    ) or _publication_gate_allows_post_clear_runtime_continuation(publication_gate_report)


def _publication_gate_requests_submission_hardening_continuation(
    publication_gate_report: dict[str, object] | None,
) -> bool:
    if not isinstance(publication_gate_report, dict):
        return False
    if str(publication_gate_report.get("status") or "").strip() in {"", "clear"}:
        return False
    if _publication_supervisor_requires_human_confirmation_from_payload(publication_gate_report):
        return False
    blockers = {
        str(item).strip()
        for item in (publication_gate_report.get("blockers") or [])
        if str(item).strip()
    }
    named_blockers = {
        str(item).strip()
        for item in (publication_gate_report.get("medical_publication_surface_named_blockers") or [])
        if str(item).strip()
    }
    return (
        "submission_hardening_incomplete" in blockers
        or "submission_hardening_incomplete" in named_blockers
    ) and str(publication_gate_report.get("medical_publication_surface_route_back_recommendation") or "").strip() == "return_to_finalize"


def _publication_supervisor_requires_human_confirmation_from_payload(payload: dict[str, object]) -> bool:
    return _publication_supervisor_current_required_action(payload) == _HUMAN_CONFIRMATION_REQUIRED_ACTION


def _int_or_none(value: object) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return int(text)
    except ValueError:
        return None


def _stopped_controller_owned_auto_recovery_context(
    *,
    status: StudyRuntimeStatus,
    quest_root: Path,
    publication_gate_report: dict[str, object] | None,
) -> dict[str, str | None] | None:
    if status.quest_status is not StudyRuntimeQuestStatus.STOPPED:
        return None
    publication_gate_status = str((publication_gate_report or {}).get("status") or "").strip() or None
    if publication_gate_status is None or _publication_supervisor_requires_human_confirmation(status):
        return None
    runtime_state = _load_json_dict(_runtime_state_path(quest_root))
    continuation_policy = str(runtime_state.get("continuation_policy") or "").strip() or None
    continuation_anchor = str(runtime_state.get("continuation_anchor") or "").strip() or None
    continuation_reason = str(runtime_state.get("continuation_reason") or "").strip() or None
    stop_reason = str(runtime_state.get("stop_reason") or "").strip() or None
    if continuation_policy not in {"auto", "wait_for_user_or_resume"}:
        return None
    recovery_mode: str | None = None
    pending_user_message_count = _int_or_none(runtime_state.get("pending_user_message_count"))
    has_pending_user_message = pending_user_message_count is not None and pending_user_message_count > 0
    controller_stopped_for_submission_hardening = (
        stop_reason is not None
        and stop_reason.startswith("controller_stop:")
        and has_pending_user_message
        and continuation_anchor == "decision"
        and continuation_reason is not None
        and continuation_reason.startswith("decision:")
        and _publication_gate_requests_submission_hardening_continuation(publication_gate_report)
    )
    if controller_stopped_for_submission_hardening:
        recovery_mode = "managed_auto_continuation"
    if stop_reason == "user_stop":
        if (
            continuation_reason is not None
            and continuation_reason.startswith("decision:")
            and has_pending_user_message
        ):
            recovery_mode = "managed_auto_continuation"
        else:
            return None
    elif recovery_mode is not None:
        pass
    elif stop_reason and not stop_reason.startswith("controller_stop:"):
        return None
    elif continuation_anchor == "decision" and continuation_reason is not None and continuation_reason.startswith("decision:"):
        recovery_mode = "decision"
    if recovery_mode is None and _controller_stop_is_auto_recoverable(
        stop_reason=stop_reason,
        publication_gate_report=publication_gate_report,
    ):
        recovery_mode = "controller_guard"
    if recovery_mode is None:
        return None
    return {
        "active_interaction_id": str(runtime_state.get("active_interaction_id") or "").strip() or None,
        "stop_reason": stop_reason,
        "continuation_reason": continuation_reason,
        "recovery_mode": recovery_mode,
    }


def _task_intake_override_allows_stopped_auto_resume(*, quest_root: Path) -> bool:
    runtime_state = _load_json_dict(_runtime_state_path(quest_root))
    stop_reason = str(runtime_state.get("stop_reason") or "").strip() or None
    if stop_reason is None:
        return True
    return _controller_stop_source(stop_reason) == "runtime_watch_outer_loop_wakeup"


def _stopped_invalid_blocking_auto_resume_allowed(
    *, stopped_recovery_context: dict[str, str | None] | None
) -> bool:
    if not isinstance(stopped_recovery_context, dict):
        return False
    stop_reason = str(stopped_recovery_context.get("stop_reason") or "").strip() or None
    return stop_reason is None


def _pending_user_interaction_payload(
    *,
    runtime_root: Path,
    quest_root: Path,
    quest_id: str,
    runtime_backend=None,
    fallback_interaction_id: str | None = None,
) -> dict[str, object] | None:
    session_payload: dict[str, object] = {}
    if runtime_backend is not None:
        try:
            raw_session_payload = runtime_backend.get_quest_session(
                runtime_root=runtime_root,
                quest_id=quest_id,
            )
        except (RuntimeError, OSError, ValueError):
            raw_session_payload = {}
        if isinstance(raw_session_payload, dict):
            session_payload = raw_session_payload
    snapshot = session_payload.get("snapshot")
    if not isinstance(snapshot, dict):
        snapshot = {}
    waiting_interaction_id = str(snapshot.get("waiting_interaction_id") or "").strip() or None
    default_reply_interaction_id = str(snapshot.get("default_reply_interaction_id") or "").strip() or None
    active_interaction_id = str(snapshot.get("active_interaction_id") or "").strip() or None
    raw_pending_decisions = snapshot.get("pending_decisions")
    pending_decisions = (
        [str(item).strip() for item in raw_pending_decisions if str(item).strip()]
        if isinstance(raw_pending_decisions, list)
        else []
    )
    interaction_id = (
        waiting_interaction_id
        or default_reply_interaction_id
        or (pending_decisions[0] if pending_decisions else None)
        or active_interaction_id
        or (str(fallback_interaction_id or "").strip() or None)
    )
    if interaction_id is None:
        return None
    interaction_artifact_path = _find_pending_interaction_artifact_path(
        quest_root=quest_root,
        interaction_id=interaction_id,
    )
    artifact_payload = _load_json_dict(interaction_artifact_path) if interaction_artifact_path is not None else {}
    reply_schema = artifact_payload.get("reply_schema")
    if not isinstance(reply_schema, dict):
        reply_schema = {}
    reply_mode = str(artifact_payload.get("reply_mode") or "").strip() or None
    submission_metadata_only = _waiting_submission_metadata_only(quest_root)
    guidance_requires_user_decision = (
        artifact_payload.get("guidance_vm", {}).get("requires_user_decision")
        if isinstance(artifact_payload.get("guidance_vm"), dict)
        else None
    )
    if submission_metadata_only and guidance_requires_user_decision is not True:
        guidance_requires_user_decision = True
    return {
        "interaction_id": interaction_id,
        "kind": str(artifact_payload.get("kind") or "").strip() or None,
        "waiting_interaction_id": waiting_interaction_id,
        "default_reply_interaction_id": default_reply_interaction_id,
        "pending_decisions": pending_decisions,
        "blocking": reply_mode == "blocking" or waiting_interaction_id == interaction_id,
        "reply_mode": reply_mode,
        "expects_reply": bool(artifact_payload.get("expects_reply", waiting_interaction_id == interaction_id)),
        "allow_free_text": bool(artifact_payload.get("allow_free_text", True)),
        "message": str(artifact_payload.get("message") or "").strip() or None,
        "summary": str(artifact_payload.get("summary") or "").strip() or None,
        "reply_schema": reply_schema,
        "decision_type": str(reply_schema.get("decision_type") or "").strip() or None,
        "options_count": (
            len(artifact_payload.get("options") or [])
            if isinstance(artifact_payload.get("options"), list)
            else 0
        ),
        "guidance_requires_user_decision": guidance_requires_user_decision,
        "source_artifact_path": str(interaction_artifact_path) if interaction_artifact_path is not None else None,
        "relay_required": True,
    }


def _record_pending_user_interaction_if_required(
    *,
    status: StudyRuntimeStatus,
    runtime_root: Path,
    quest_root: Path,
    quest_id: str,
    publication_gate_report: dict[str, object] | None,
    runtime_backend=None,
) -> None:
    stopped_recovery_context = _stopped_controller_owned_auto_recovery_context(
        status=status,
        quest_root=quest_root,
        publication_gate_report=publication_gate_report,
    )
    if (
        status.quest_status is not StudyRuntimeQuestStatus.WAITING_FOR_USER
        and not _is_controller_owned_finalize_parking(status)
        and stopped_recovery_context is None
    ):
        return
    payload = _pending_user_interaction_payload(
        runtime_root=runtime_root,
        quest_root=quest_root,
        quest_id=quest_id,
        runtime_backend=runtime_backend,
        fallback_interaction_id=(
            str(stopped_recovery_context.get("active_interaction_id") or "").strip()
            if isinstance(stopped_recovery_context, dict)
            else None
        ),
    )
    if payload is None:
        return
    status.record_pending_user_interaction(payload)


__all__ = [name for name in globals() if not name.startswith("__")]
