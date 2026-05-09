from __future__ import annotations

if __name__ != "med_autoscience.controllers.study_runtime_decision":
    from ..publication_and_submission import *  # noqa: F403


def _publication_gate_allows_live_runtime_write_stage_resume(
    *,
    status: StudyRuntimeStatus,
    publication_gate_report: dict[str, object] | None,
) -> bool:
    if not _publication_gate_allows_post_clear_runtime_continuation(publication_gate_report):
        return False
    try:
        continuation_state = status.continuation_state
    except KeyError:
        return False
    return (
        continuation_state.active_run_id is not None
        and continuation_state.continuation_policy == "auto"
        and continuation_state.continuation_anchor == "decision"
        and continuation_state.continuation_reason is not None
        and continuation_state.continuation_reason.startswith("decision:")
    )


def _publication_gate_allows_post_clear_runtime_continuation(
    publication_gate_report: dict[str, object] | None,
) -> bool:
    if not isinstance(publication_gate_report, dict):
        return False
    if _publication_gate_requires_live_runtime_reroute(publication_gate_report):
        return False
    if bool(publication_gate_report.get("bundle_tasks_downstream_only")):
        return False
    if _publication_supervisor_current_required_action(publication_gate_report) not in {
        "continue_write_stage",
        "continue_bundle_stage",
    }:
        return False
    if str(publication_gate_report.get("status") or "").strip() not in {"", "clear"}:
        return False
    return _publication_supervisor_requests_automated_continuation(
        publication_gate_report,
        require_blocked_status=False,
    )


def _runtime_owned_roots(quest_root: Path) -> tuple[str, ...]:
    return (
        str(quest_root),
        str(quest_root / ".ds"),
        str(quest_root / "paper"),
        str(quest_root / "release"),
        str(quest_root / "artifacts"),
    )


def _record_execution_owner_guard(
    *,
    status: StudyRuntimeStatus,
    quest_root: Path,
) -> None:
    execution = status.execution
    if not runtime_backend_contract.is_managed_research_execution(execution):
        return
    if not status.quest_exists or status.quest_status not in _LIVE_QUEST_STATUSES:
        return
    try:
        runtime_liveness = status.runtime_liveness_audit_record
    except KeyError:
        return
    if runtime_liveness.status is StudyRuntimeAuditStatus.NONE:
        return
    try:
        active_run_id = status.autonomous_runtime_notice.active_run_id
    except KeyError:
        active_run_id = str(runtime_liveness.payload.get("active_run_id") or "").strip() or None
    publication_gate_allows_direct_write = _publication_gate_allows_direct_write(status)
    guard_reason = "live_managed_runtime"
    current_required_action = "supervise_managed_runtime"
    controller_stage_note = (
        "live managed runtime owns study-local execution; the foreground agent must stay supervisor-only "
        "until explicit takeover"
    )
    if runtime_liveness.status is not StudyRuntimeAuditStatus.LIVE:
        guard_reason = "managed_runtime_audit_unhealthy"
        current_required_action = "inspect_runtime_health_and_decide_intervention"
        controller_stage_note = (
            "managed runtime still owns study-local execution, but the liveness audit is unhealthy; "
            "stay supervisor-only until the runtime is inspected and explicitly paused or resumed"
        )
    payload = {
        "owner": "managed_runtime",
        "supervisor_only": True,
        "guard_reason": guard_reason,
        "active_run_id": active_run_id,
        "current_required_action": current_required_action,
        "allowed_actions": list(_SUPERVISOR_ONLY_ALLOWED_ACTIONS),
        "forbidden_actions": list(_SUPERVISOR_ONLY_FORBIDDEN_ACTIONS),
        "runtime_owned_roots": list(_runtime_owned_roots(quest_root)),
        "takeover_required": True,
        "takeover_action": "pause_runtime_then_explicit_human_takeover",
        "publication_gate_allows_direct_write": publication_gate_allows_direct_write,
        "controller_stage_note": controller_stage_note,
    }
    status.record_execution_owner_guard(StudyRuntimeExecutionOwnerGuard.from_payload(payload))


def _load_json_dict(path: Path) -> dict[str, object]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8")) or {}
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _runtime_state_path(quest_root: Path) -> Path:
    return Path(quest_root).expanduser().resolve() / ".ds" / "runtime_state.json"


def _continuation_state_payload(*, quest_root: Path, quest_status: StudyRuntimeQuestStatus | None) -> dict[str, object] | None:
    runtime_state_path = _runtime_state_path(quest_root)
    runtime_state = _load_json_dict(runtime_state_path)
    continuation_policy = str(runtime_state.get("continuation_policy") or "").strip() or None
    continuation_anchor = str(runtime_state.get("continuation_anchor") or "").strip() or None
    continuation_reason = str(runtime_state.get("continuation_reason") or "").strip() or None
    stop_reason = str(runtime_state.get("stop_reason") or "").strip() or None
    if continuation_policy is None and continuation_anchor is None and continuation_reason is None and stop_reason is None:
        return None
    return {
        "quest_status": str(runtime_state.get("status") or "").strip() or (quest_status.value if quest_status is not None else None),
        "active_run_id": str(runtime_state.get("active_run_id") or "").strip() or None,
        "continuation_policy": continuation_policy,
        "continuation_anchor": continuation_anchor,
        "continuation_reason": continuation_reason,
        "stop_reason": stop_reason,
        "runtime_state_path": str(runtime_state_path),
    }


def _blocked_closeout_payload(*, quest_root: Path) -> dict[str, object] | None:
    runtime_state = _load_json_dict(_runtime_state_path(quest_root))
    blocked_closeout = runtime_state.get("blocked_turn_closeout")
    if not isinstance(blocked_closeout, dict):
        return None
    payload = {
        "run_id": str(blocked_closeout.get("run_id") or "").strip() or None,
        "closeout_path": str(blocked_closeout.get("closeout_path") or "").strip() or None,
        "blocked_reason": str(blocked_closeout.get("blocked_reason") or "").strip() or None,
        "next_owner": str(blocked_closeout.get("next_owner") or "").strip() or None,
    }
    if not any(payload.values()):
        return None
    return payload


def _record_blocked_closeout_if_present(*, status: StudyRuntimeStatus, quest_root: Path) -> None:
    payload = _blocked_closeout_payload(quest_root=quest_root)
    if payload is None:
        return
    status.extras["blocked_turn_closeout"] = payload


def _record_continuation_state_if_present(*, status: StudyRuntimeStatus, quest_root: Path) -> None:
    payload = _continuation_state_payload(quest_root=quest_root, quest_status=status.quest_status)
    if payload is None:
        return
    status.record_continuation_state(StudyRuntimeContinuationState.from_payload(payload))


__all__ = [name for name in globals() if not name.startswith("__")]
