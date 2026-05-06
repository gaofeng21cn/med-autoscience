def _is_controller_owned_finalize_parking(status: StudyRuntimeStatus) -> bool:
    if status.quest_status not in _LIVE_QUEST_STATUSES:
        return False
    try:
        continuation_state = status.continuation_state
    except KeyError:
        return False
    return (
        continuation_state.active_run_id is None
        and continuation_state.continuation_policy == _FINALIZE_PARKING_CONTINUATION_POLICY
        and continuation_state.continuation_reason == _FINALIZE_PARKING_CONTINUATION_REASON
    )


def _controller_decision_requests_human_review_milestone_stop(*, study_root: Path) -> bool:
    payload = _load_json_dict(study_root / "artifacts" / "controller_decisions" / "latest.json")
    if not payload:
        return False
    route_target = str(payload.get("route_target") or "").strip()
    if route_target and route_target != "finalize":
        return False
    action_types = {
        str(action.get("action_type") or "").strip()
        for action in (payload.get("controller_actions") or [])
        if isinstance(action, dict)
    }
    if "stop_runtime" not in action_types:
        return False
    reason = str(payload.get("reason") or "").strip().lower()
    return (
        "human-review milestone reached" in reason
        or "submission-package milestone remains parked" in reason
    )


def _evaluation_summary_reports_bundle_only_remaining(*, study_root: Path) -> bool:
    payload = _load_json_dict(study_root / "artifacts" / "eval_hygiene" / "evaluation_summary" / "latest.json")
    quality_closure_truth = payload.get("quality_closure_truth")
    if isinstance(quality_closure_truth, dict):
        state = str(quality_closure_truth.get("state") or "").strip()
        route_target = str(quality_closure_truth.get("route_target") or "").strip()
        if state == "bundle_only_remaining" and (not route_target or route_target == "finalize"):
            return True
    quality_review_loop = payload.get("quality_review_loop")
    if isinstance(quality_review_loop, dict):
        return str(quality_review_loop.get("closure_state") or "").strip() == "bundle_only_remaining"
    return False


def _is_human_review_milestone_parking(
    status: StudyRuntimeStatus,
    *,
    study_root: Path,
) -> bool:
    if status.quest_status not in _LIVE_QUEST_STATUSES:
        return False
    try:
        continuation_state = status.continuation_state
    except KeyError:
        return False
    if continuation_state.active_run_id is not None:
        return False
    if continuation_state.continuation_policy != _FINALIZE_PARKING_CONTINUATION_POLICY:
        return False
    if continuation_state.continuation_anchor not in {None, "decision"}:
        return False
    if continuation_state.continuation_reason not in {
        _FINALIZE_PARKING_CONTINUATION_REASON,
        "unchanged_publication_gate_state",
    }:
        return False
    return _controller_decision_requests_human_review_milestone_stop(
        study_root=study_root,
    ) and _evaluation_summary_reports_bundle_only_remaining(study_root=study_root)


def _is_delivered_human_review_milestone_without_live_worker(
    status: StudyRuntimeStatus,
    *,
    study_root: Path,
) -> bool:
    if status.quest_status not in _LIVE_QUEST_STATUSES and status.quest_status not in _RESUMABLE_QUEST_STATUSES:
        return False
    try:
        continuation_state = status.continuation_state
    except KeyError:
        return False
    if continuation_state.active_run_id is not None:
        return False
    if not (_has_delivered_human_package_surface(study_root) or _has_current_human_facing_delivery_manifest(study_root)):
        return False
    return _controller_decision_requests_human_review_milestone_stop(
        study_root=study_root,
    )


def _platform_repair_redrive_without_live_worker(
    status: StudyRuntimeStatus,
    *,
    audit_status: quest_state.QuestRuntimeLivenessStatus | None = None,
) -> bool:
    if audit_status is not None and audit_status is quest_state.QuestRuntimeLivenessStatus.LIVE:
        return False
    try:
        continuation_state = status.continuation_state
    except KeyError:
        return False
    return (
        continuation_state.active_run_id is None
        and continuation_state.continuation_policy == "auto"
        and continuation_state.continuation_anchor == "decision"
        and continuation_state.continuation_reason == "runtime_platform_repair_redrive"
    )


def _user_pause_contract_without_live_worker(
    status: StudyRuntimeStatus,
    *,
    audit_status: quest_state.QuestRuntimeLivenessStatus | None = None,
) -> bool:
    if audit_status is not None and audit_status is quest_state.QuestRuntimeLivenessStatus.LIVE:
        return False
    if (
        status.quest_status not in _LIVE_QUEST_STATUSES
        and status.quest_status not in _RESUMABLE_QUEST_STATUSES
        and status.quest_status is not StudyRuntimeQuestStatus.STOPPED
    ):
        return False
    try:
        continuation_state = status.continuation_state
    except KeyError:
        return False
    return continuation_state.active_run_id is None and continuation_state.stop_reason == "user_pause"


def _has_delivered_human_package_surface(study_root: Path) -> bool:
    return resolve_delivered_submission_package_manual_finish_contract(study_root=study_root) is not None


def _has_current_human_facing_delivery_manifest(study_root: Path) -> bool:
    manifest = _load_json_dict(study_root / "manuscript" / "delivery_manifest.json")
    if not manifest:
        return False
    stage = str(manifest.get("stage") or "").strip()
    source_signature = str(manifest.get("source_signature") or "").strip()
    authority_signature = str(manifest.get("authority_source_signature") or "").strip()
    evaluated_signature = str(manifest.get("evaluated_source_signature") or "").strip()
    if stage != "submission_minimal" or not source_signature:
        return False
    return source_signature == authority_signature == evaluated_signature


def _should_block_platform_repair_redrive_for_delivered_package(
    status: StudyRuntimeStatus,
    *,
    study_root: Path,
) -> bool:
    return _has_delivered_human_package_surface(study_root) and _platform_repair_redrive_without_live_worker(status)


def _should_park_delivered_package_without_live_worker(
    status: StudyRuntimeStatus,
    *,
    study_root: Path,
    audit_status: quest_state.QuestRuntimeLivenessStatus | None = None,
) -> bool:
    if not _has_delivered_human_package_surface(study_root):
        return False
    if audit_status is quest_state.QuestRuntimeLivenessStatus.LIVE:
        return False
    if status.quest_status not in _LIVE_QUEST_STATUSES and status.quest_status not in _RESUMABLE_QUEST_STATUSES:
        return False
    try:
        continuation_state = status.continuation_state
    except KeyError:
        return True
    return continuation_state.active_run_id is None


def _should_park_delivered_or_redriven_package_without_live_worker(
    status: StudyRuntimeStatus,
    *,
    study_root: Path,
    audit_status: quest_state.QuestRuntimeLivenessStatus | None = None,
    manual_finish_compatibility_guard: bool = False,
) -> bool:
    return (
        manual_finish_compatibility_guard
        and _platform_repair_redrive_without_live_worker(status, audit_status=audit_status)
    ) or _should_park_delivered_package_without_live_worker(
        status,
        study_root=study_root,
        audit_status=audit_status,
    )


def _controller_decision_requires_human_confirmation(*, study_root: Path) -> bool:
    decision_path = Path(study_root).expanduser().resolve() / "artifacts" / "controller_decisions" / "latest.json"
    summary_path = stable_controller_confirmation_summary_path(study_root=study_root)
    try:
        if decision_path.exists():
            materialize_controller_confirmation_summary(
                study_root=study_root,
                decision_ref=decision_path,
            )
        if summary_path.exists():
            summary = read_controller_confirmation_summary(
                study_root=study_root,
                ref=summary_path,
            )
            return str(summary.get("status") or "").strip() == "pending"
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        pass
    payload = _load_json_dict(study_root / "artifacts" / "controller_decisions" / "latest.json")
    return bool(payload.get("requires_human_confirmation"))


def _publication_supervisor_requires_human_confirmation(status: StudyRuntimeStatus) -> bool:
    payload = status.extras.get("publication_supervisor_state")
    return _publication_supervisor_current_required_action(payload) == _HUMAN_CONFIRMATION_REQUIRED_ACTION


def _runtime_liveness_audit_payload(status: StudyRuntimeStatus) -> dict[str, object]:
    payload = status.extras.get("runtime_liveness_audit")
    return dict(payload) if isinstance(payload, dict) else {}


def _stale_progress_without_live_bash_sessions(status: StudyRuntimeStatus) -> bool:
    runtime_liveness_audit = _runtime_liveness_audit_payload(status)
    if not bool(runtime_liveness_audit.get("stale_progress")):
        return False
    if str(runtime_liveness_audit.get("liveness_guard_reason") or "").strip() != "stale_progress_watchdog":
        return False
    bash_session_audit = status.extras.get("bash_session_audit")
    if not isinstance(bash_session_audit, dict):
        return False
    if str(bash_session_audit.get("status") or "").strip() != "none":
        return False
    live_session_count = bash_session_audit.get("live_session_count")
    if live_session_count is None:
        return True
    try:
        return int(live_session_count) == 0
    except (TypeError, ValueError):
        return False


def _live_worker_missing_active_run_id(status: StudyRuntimeStatus) -> bool:
    audit = _runtime_liveness_audit_payload(status)
    if str(audit.get("liveness_guard_reason") or "").strip() != "live_runtime_missing_active_run_id":
        return False
    runtime_audit = dict(audit.get("runtime_audit") or {}) if isinstance(audit.get("runtime_audit"), dict) else {}
    active_run_id = str(audit.get("active_run_id") or runtime_audit.get("active_run_id") or "").strip()
    return runtime_audit.get("worker_running") is True and not active_run_id


def _runtime_overlay_ready_for_resume(status: StudyRuntimeStatus) -> bool:
    payload = status.extras.get("runtime_overlay")
    if not isinstance(payload, dict):
        return True
    audit = payload.get("audit")
    if not isinstance(audit, dict):
        return True
    return audit.get("all_roots_ready") is not False


def _set_running_quest_recovery_decision(
    *,
    status: StudyRuntimeStatus,
    execution: dict[str, object],
) -> None:
    if _user_pause_contract_without_live_worker(status):
        status.set_decision(
            StudyRuntimeDecision.BLOCKED,
            StudyRuntimeReason.QUEST_USER_PAUSED_REQUIRES_EXPLICIT_WAKEUP,
        )
    elif not status.startup_boundary_allows_compute_stage:
        status.set_decision(
            StudyRuntimeDecision.BLOCKED,
            StudyRuntimeReason.STARTUP_BOUNDARY_NOT_READY_FOR_RESUME,
        )
    elif not status.runtime_reentry_allows_runtime_entry:
        status.set_decision(
            StudyRuntimeDecision.BLOCKED,
            StudyRuntimeReason.RUNTIME_REENTRY_NOT_READY_FOR_RESUME,
        )
    elif not _runtime_overlay_ready_for_resume(status):
        status.set_decision(
            StudyRuntimeDecision.BLOCKED,
            StudyRuntimeReason.RUNNING_QUEST_LIVE_SESSION_AUDIT_FAILED,
        )
    elif execution.get("auto_resume") is True:
        status.set_decision(
            StudyRuntimeDecision.RESUME,
            StudyRuntimeReason.QUEST_MARKED_RUNNING_BUT_NO_LIVE_SESSION,
        )
    else:
        status.set_decision(
            StudyRuntimeDecision.BLOCKED,
            StudyRuntimeReason.QUEST_MARKED_RUNNING_BUT_AUTO_RESUME_DISABLED,
        )


def _runtime_event_status_snapshot(status: StudyRuntimeStatus) -> dict[str, object]:
    runtime_liveness_audit = _runtime_liveness_audit_payload(status)
    runtime_audit = (
        dict(runtime_liveness_audit.get("runtime_audit") or {})
        if isinstance(runtime_liveness_audit.get("runtime_audit"), dict)
        else {}
    )
    continuation_state = status.extras.get("continuation_state")
    supervisor_tick_audit = status.extras.get("supervisor_tick_audit")
    return {
        "quest_status": status.quest_status.value if status.quest_status is not None else None,
        "decision": status.decision.value if status.decision is not None else None,
        "reason": status.reason.value if status.reason is not None else None,
        "active_run_id": str(runtime_liveness_audit.get("active_run_id") or runtime_audit.get("active_run_id") or "").strip() or None,
        "runtime_liveness_status": str(runtime_liveness_audit.get("status") or "").strip() or None,
        "worker_running": runtime_audit.get("worker_running") if isinstance(runtime_audit.get("worker_running"), bool) else None,
        "continuation_policy": (
            str(continuation_state.get("continuation_policy") or "").strip() or None
            if isinstance(continuation_state, dict)
            else None
        ),
        "continuation_anchor": (
            str(continuation_state.get("continuation_anchor") or "").strip() or None
            if isinstance(continuation_state, dict)
            else None
        ),
        "continuation_reason": (
            str(continuation_state.get("continuation_reason") or "").strip() or None
            if isinstance(continuation_state, dict)
            else None
        ),
        "supervisor_tick_status": (
            str(supervisor_tick_audit.get("status") or "").strip() or None
            if isinstance(supervisor_tick_audit, dict)
            else None
        ),
        "controller_owned_finalize_parking": _is_controller_owned_finalize_parking(status),
        "runtime_escalation_ref": (
            dict(status.extras.get("runtime_escalation_ref"))
            if isinstance(status.extras.get("runtime_escalation_ref"), dict)
            else None
        ),
    }


def _runtime_event_outer_loop_input(status: StudyRuntimeStatus) -> dict[str, object]:
    snapshot = _runtime_event_status_snapshot(status)
    interaction_arbitration = status.extras.get("interaction_arbitration")
    return {
        "quest_status": snapshot["quest_status"],
        "decision": snapshot["decision"],
        "reason": snapshot["reason"],
        "active_run_id": snapshot["active_run_id"],
        "runtime_liveness_status": snapshot["runtime_liveness_status"],
        "worker_running": snapshot["worker_running"],
        "supervisor_tick_status": snapshot["supervisor_tick_status"],
        "controller_owned_finalize_parking": snapshot["controller_owned_finalize_parking"],
        "interaction_action": (
            str(interaction_arbitration.get("action") or "").strip() or None
            if isinstance(interaction_arbitration, dict)
            else None
        ),
        "interaction_requires_user_input": (
            bool(interaction_arbitration.get("requires_user_input"))
            if isinstance(interaction_arbitration, dict)
            else False
        ),
        "runtime_escalation_ref": snapshot["runtime_escalation_ref"],
    }


def _status_family_human_gates(
    *,
    status: StudyRuntimeStatus,
    study_root: Path,
    event_time: str,
) -> list[dict[str, object]]:
    gates: list[dict[str, object]] = []
    pending_interaction = status.extras.get("pending_user_interaction")
    interaction_arbitration = status.extras.get("interaction_arbitration")
    pending_interaction_id = (
        str(pending_interaction.get("interaction_id") or "").strip()
        if isinstance(pending_interaction, dict)
        else ""
    )
    pending_interaction_ref = (
        str(pending_interaction.get("source_artifact_path") or "").strip()
        if isinstance(pending_interaction, dict)
        else ""
    )
    pending_interaction_requires_human_gate = True
    if isinstance(interaction_arbitration, dict):
        pending_interaction_requires_human_gate = bool(interaction_arbitration.get("requires_user_input"))
    if pending_interaction_id and pending_interaction_requires_human_gate:
        pending_decisions = (
            [
                str(item).strip()
                for item in (pending_interaction.get("pending_decisions") or [])
                if str(item).strip()
            ]
            if isinstance(pending_interaction, dict)
            else []
        )
        gates.append(
            family_orchestration.build_family_human_gate(
                gate_id=f"status-waiting-{status.study_id}-{pending_interaction_id}",
                gate_kind="runtime_pending_user_interaction",
                requested_at=event_time,
                request_surface_kind="study_runtime_status",
                request_surface_id="study_runtime_status",
                evidence_refs=[
                    {
                        "ref_kind": "repo_path",
                        "ref": pending_interaction_ref,
                        "label": "pending_user_interaction",
                    }
                ]
                if pending_interaction_ref
                else [],
                decision_options=pending_decisions or ["reply"],
            )
        )

    controller_requires_human_confirmation = _controller_decision_requires_human_confirmation(study_root=study_root)
    publication_requires_human_confirmation = _publication_supervisor_requires_human_confirmation(status)
    if controller_requires_human_confirmation or publication_requires_human_confirmation:
        gates.append(
            family_orchestration.build_family_human_gate(
                gate_id=f"status-human-confirmation-{status.study_id}",
                gate_kind="controller_human_confirmation",
                requested_at=event_time,
                request_surface_kind="study_runtime_status",
                request_surface_id="study_runtime_status",
                evidence_refs=[
                    {
                        "ref_kind": "repo_path",
                        "ref": str(study_root / "artifacts" / "controller_decisions" / "latest.json"),
                        "label": "controller_decision_latest",
                    }
                ],
                decision_options=["approve", "request_changes", "reject"],
            )
        )
    return gates
