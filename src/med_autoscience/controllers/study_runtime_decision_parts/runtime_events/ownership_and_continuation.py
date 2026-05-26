from __future__ import annotations

if __name__ != "med_autoscience.controllers.study_runtime_decision":
    from ..publication_and_submission import *  # noqa: F403
from med_autoscience import opl_runtime_contract
from med_autoscience.controllers.owner_route_reconcile_parts import hard_methodology_currentness
from med_autoscience.controllers import analysis_harmonization_owner_result
from med_autoscience.controllers import source_provenance_owner_result


def _publication_gate_allows_live_runtime_write_stage_resume(
    *,
    status: ProgressProjectionStatus,
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
    status: ProgressProjectionStatus,
    quest_root: Path,
) -> None:
    execution = status.execution
    if not opl_runtime_contract.is_opl_hosted_research_execution(execution):
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


def _load_json_dict_with_error(path: Path) -> tuple[dict[str, object], str | None]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8")) or {}
    except FileNotFoundError:
        return {}, "missing"
    except OSError:
        return {}, "read_error"
    except json.JSONDecodeError:
        return {}, "invalid_json"
    if not isinstance(payload, dict):
        return {}, "not_json_object"
    return payload, None


def _runtime_state_path(quest_root: Path) -> Path:
    return Path(quest_root).expanduser().resolve() / ".ds" / "runtime_state.json"


def _continuation_state_payload(
    *,
    quest_root: Path,
    quest_status: StudyRuntimeQuestStatus | None,
    active_run_id: str | None = None,
) -> dict[str, object] | None:
    runtime_state_path = _runtime_state_path(quest_root)
    runtime_state = _load_json_dict(runtime_state_path)
    continuation_policy = str(runtime_state.get("continuation_policy") or "").strip() or None
    continuation_anchor = str(runtime_state.get("continuation_anchor") or "").strip() or None
    continuation_reason = str(runtime_state.get("continuation_reason") or "").strip() or None
    stop_reason = str(runtime_state.get("stop_reason") or "").strip() or None
    if continuation_policy is None and continuation_anchor is None and continuation_reason is None and stop_reason is None:
        return None
    resolved_active_run_id = str(runtime_state.get("active_run_id") or "").strip() or active_run_id
    return {
        "quest_status": str(runtime_state.get("status") or "").strip() or (quest_status.value if quest_status is not None else None),
        "active_run_id": resolved_active_run_id,
        "continuation_policy": continuation_policy,
        "continuation_anchor": continuation_anchor,
        "continuation_reason": continuation_reason,
        "stop_reason": stop_reason,
        "pending_user_message_count": int(runtime_state.get("pending_user_message_count") or 0),
        "runtime_state_path": str(runtime_state_path),
    }


def _record_controller_authorization_if_present(
    *,
    status: ProgressProjectionStatus,
    quest_root: Path,
    study_root: Path | None = None,
) -> None:
    runtime_state = _load_json_dict(_runtime_state_path(quest_root))
    authorization = runtime_state.get("last_controller_decision_authorization")
    if isinstance(authorization, dict) and authorization:
        if study_root is not None and _hard_methodology_handoff_supersedes_authorization(
            study_root=study_root,
            authorization=authorization,
        ):
            status.extras["superseded_controller_decision_authorization"] = {
                "reason": "unit_harmonized_rerun_required",
                "superseded_work_unit_id": str(authorization.get("work_unit_id") or "").strip() or None,
                "superseded_work_unit_fingerprint": str(
                    authorization.get("work_unit_fingerprint") or ""
                ).strip()
                or None,
                "source_surface": "artifacts/controller/quality_repair_batch/latest.json",
            }
            return
        status.extras["last_controller_decision_authorization"] = dict(authorization)


def _hard_methodology_handoff_supersedes_authorization(
    *,
    study_root: Path,
    authorization: dict[str, object],
) -> bool:
    work_unit_id = str(authorization.get("work_unit_id") or "").strip()
    work_unit_fingerprint = str(authorization.get("work_unit_fingerprint") or "").strip()
    if (
        work_unit_id != "medical_prose_quality_analysis_source_documentation_repair"
        and work_unit_fingerprint != "decision::methodology_reframe_route_decision"
    ):
        return False
    root = Path(study_root).expanduser().resolve()
    return hard_methodology_currentness.handoff_supersedes_paths(
        source_ref=hard_methodology_currentness.quality_repair_handoff_path(root),
        consumer_paths=(
            analysis_harmonization_owner_result.result_path(study_root=root),
            source_provenance_owner_result.result_path(study_root=root),
            root / "artifacts" / "controller_decisions" / "latest.json",
        ),
    )


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


def _record_blocked_closeout_if_present(*, status: ProgressProjectionStatus, quest_root: Path) -> None:
    payload = _blocked_closeout_payload(quest_root=quest_root)
    if payload is None:
        return
    status.extras["blocked_turn_closeout"] = payload


def _execution_latest_path(study_root: Path) -> Path:
    return (
        Path(study_root).expanduser().resolve()
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_execution"
        / "latest.json"
    )


def _datetime_value(value: object):
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None


def _blocked_closeout_time(*, blocked_closeout: dict[str, object], runtime_state: dict[str, object]) -> object:
    closeout_path_text = str(blocked_closeout.get("closeout_path") or "").strip()
    if closeout_path_text:
        closeout = _load_json_dict(Path(closeout_path_text).expanduser())
        completed_at = closeout.get("completed_at")
        if completed_at:
            return completed_at
    return runtime_state.get("continuation_updated_at")


def _execution_is_later_than_closeout(
    *,
    execution: dict[str, object],
    blocked_closeout: dict[str, object],
    runtime_state: dict[str, object],
) -> bool:
    closeout_at = _datetime_value(_blocked_closeout_time(blocked_closeout=blocked_closeout, runtime_state=runtime_state))
    execution_at = _datetime_value(execution.get("generated_at"))
    if closeout_at is None or execution_at is None:
        return False
    return execution_at > closeout_at


def _controller_action_types(runtime_state: dict[str, object]) -> set[str]:
    authorization = runtime_state.get("last_controller_decision_authorization")
    if not isinstance(authorization, dict):
        return set()
    values = authorization.get("controller_actions")
    if not isinstance(values, list):
        return set()
    return {str(item).strip() for item in values if str(item or "").strip()}


def _superseding_default_executor_execution(
    *,
    status: ProgressProjectionStatus,
    study_root: Path,
    runtime_state: dict[str, object],
    blocked_closeout: dict[str, object],
) -> dict[str, object] | None:
    execution_path = _execution_latest_path(study_root)
    payload = _load_json_dict(execution_path)
    if not payload:
        return None
    if str(payload.get("surface") or "").strip() != "default_executor_dispatch_execution_study_latest":
        return None
    if int(payload.get("blocked_count") or 0) != 0:
        return None
    controller_actions = _controller_action_types(runtime_state)
    if not controller_actions:
        return None
    blocked_run_id = str(blocked_closeout.get("run_id") or "").strip() or None
    for item in payload.get("executions") or []:
        if not isinstance(item, dict):
            continue
        action_type = str(item.get("action_type") or "").strip()
        if action_type not in controller_actions:
            continue
        if str(item.get("execution_status") or "").strip() != "executed":
            continue
        if str(item.get("blocked_reason") or "").strip():
            continue
        if str(item.get("study_id") or "").strip() != status.study_id:
            continue
        if str(item.get("quest_id") or "").strip() not in {"", status.quest_id}:
            continue
        if not _execution_is_later_than_closeout(
            execution=item,
            blocked_closeout=blocked_closeout,
            runtime_state=runtime_state,
        ):
            continue
        return {
            "source_surface": "default_executor_execution/latest.json",
            "source_path": str(execution_path),
            "superseded_run_id": blocked_run_id,
            "execution_id": str(item.get("execution_id") or "").strip() or None,
            "action_type": action_type,
            "execution_status": "executed",
            "generated_at": str(item.get("generated_at") or "").strip() or None,
            "owner_callable_surface": str(item.get("owner_callable_surface") or "").strip() or None,
        }
    return None


def _record_blocked_closeout_supersession_if_present(
    *,
    status: ProgressProjectionStatus,
    study_root: Path,
    quest_root: Path,
) -> None:
    blocked_closeout = status.extras.get("blocked_turn_closeout")
    if not isinstance(blocked_closeout, dict):
        return
    runtime_state_path = _runtime_state_path(quest_root)
    runtime_state = _load_json_dict(runtime_state_path)
    supersession = _superseding_default_executor_execution(
        status=status,
        study_root=study_root,
        runtime_state=runtime_state,
        blocked_closeout=blocked_closeout,
    )
    if supersession is None:
        return
    status.extras.pop("blocked_turn_closeout", None)
    status.extras["blocked_turn_closeout_supersession"] = supersession
    status.record_continuation_state(
        StudyRuntimeContinuationState.from_payload(
            {
                "quest_status": status.quest_status.value if status.quest_status is not None else None,
                "active_run_id": None,
                "continuation_policy": "auto",
                "continuation_anchor": "decision",
                "continuation_reason": "controller_work_unit_pending",
                "pending_user_message_count": int(runtime_state.get("pending_user_message_count") or 0),
                "runtime_state_path": str(runtime_state_path),
            }
        )
    )


def _record_continuation_state_if_present(
    *,
    status: ProgressProjectionStatus,
    quest_root: Path,
    active_run_id: str | None = None,
    live_opl_provider_attempt: bool = False,
) -> None:
    resolved_active_run_id = active_run_id
    runtime_liveness = status.extras.get("runtime_liveness_audit")
    live_opl_provider_attempt = live_opl_provider_attempt or (
        isinstance(runtime_liveness, dict)
        and str(runtime_liveness.get("source") or "").strip() == "opl_current_control_state_provider_attempt"
        and str(runtime_liveness.get("status") or "").strip() == "live"
        and str(runtime_liveness.get("active_run_id") or "").strip()
    )
    if resolved_active_run_id is None and live_opl_provider_attempt:
        resolved_active_run_id = str(runtime_liveness.get("active_run_id") or "").strip() or None
    payload = _continuation_state_payload(
        quest_root=quest_root,
        quest_status=status.quest_status,
        active_run_id=resolved_active_run_id,
    )
    if payload is None:
        return
    if live_opl_provider_attempt and resolved_active_run_id is not None:
        payload = {
            **payload,
            "active_run_id": resolved_active_run_id,
            "continuation_policy": "auto",
            "continuation_anchor": "decision",
            "continuation_reason": "controller_work_unit_pending",
            "stop_reason": None,
        }
    status.record_continuation_state(StudyRuntimeContinuationState.from_payload(payload))


__all__ = [name for name in globals() if not name.startswith("__")]
