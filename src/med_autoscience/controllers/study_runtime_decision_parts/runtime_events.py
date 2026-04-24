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
    if continuation_policy is None and continuation_anchor is None and continuation_reason is None:
        return None
    return {
        "quest_status": str(runtime_state.get("status") or "").strip() or (quest_status.value if quest_status is not None else None),
        "active_run_id": str(runtime_state.get("active_run_id") or "").strip() or None,
        "continuation_policy": continuation_policy,
        "continuation_anchor": continuation_anchor,
        "continuation_reason": continuation_reason,
        "runtime_state_path": str(runtime_state_path),
    }


def _record_continuation_state_if_present(*, status: StudyRuntimeStatus, quest_root: Path) -> None:
    payload = _continuation_state_payload(quest_root=quest_root, quest_status=status.quest_status)
    if payload is None:
        return
    status.record_continuation_state(StudyRuntimeContinuationState.from_payload(payload))


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


def _record_family_orchestration_companion(
    *,
    status: StudyRuntimeStatus,
    study_root: Path,
    runtime_context: study_runtime_protocol.StudyRuntimeContext,
) -> None:
    event_time = _router_module()._utc_now()
    snapshot = _runtime_event_status_snapshot(status)
    runtime_decision = status.decision.value if status.decision is not None else None
    runtime_reason = status.reason.value if status.reason is not None else None
    active_run_id = family_orchestration.resolve_active_run_id(
        snapshot.get("active_run_id"),
        ((status.extras.get("autonomous_runtime_notice") or {}) if isinstance(status.extras.get("autonomous_runtime_notice"), dict) else {}).get("active_run_id"),
        ((status.extras.get("execution_owner_guard") or {}) if isinstance(status.extras.get("execution_owner_guard"), dict) else {}).get("active_run_id"),
    )
    quest_root = Path(status.quest_root).expanduser().resolve()
    runtime_event_ref = status.extras.get("runtime_event_ref")
    runtime_event_artifact_path = (
        str(runtime_event_ref.get("artifact_path") or "").strip()
        if isinstance(runtime_event_ref, dict)
        else ""
    )
    runtime_escalation_ref = status.extras.get("runtime_escalation_ref")
    runtime_escalation_path = (
        str(runtime_escalation_ref.get("artifact_path") or "").strip()
        if isinstance(runtime_escalation_ref, dict)
        else ""
    )
    human_gates = _status_family_human_gates(
        status=status,
        study_root=study_root,
        event_time=event_time,
    )
    family_payload = family_orchestration.build_family_orchestration_companion(
        surface_kind="study_runtime_status",
        surface_id="study_runtime_status",
        event_name=f"study_runtime_status.{runtime_decision or 'observed'}",
        source_surface=str(
            status.execution.get("executor_kind")
            or status.execution.get("executor")
            or "codex_cli_autonomous"
        ),
        session_id=f"study-runtime:{status.study_id}",
        program_id=family_orchestration.resolve_program_id(status.execution),
        study_id=status.study_id,
        quest_id=status.quest_id,
        active_run_id=active_run_id,
        runtime_decision=runtime_decision,
        runtime_reason=runtime_reason,
        payload={
            "entry_mode": status.entry_mode,
            "quest_status": status.quest_status.value if status.quest_status is not None else None,
            "runtime_liveness_status": snapshot.get("runtime_liveness_status"),
            "supervisor_tick_status": snapshot.get("supervisor_tick_status"),
            "controller_owned_finalize_parking": snapshot.get("controller_owned_finalize_parking"),
        },
        event_time=event_time,
        checkpoint_id=f"study-runtime-status:{status.study_id}:{runtime_decision or 'unknown'}",
        checkpoint_label="study_runtime_status snapshot",
        audit_refs=[
            {
                "ref_kind": "repo_path",
                "ref": runtime_event_artifact_path,
                "label": "runtime_event_latest",
            }
            if runtime_event_artifact_path
            else {},
            {
                "ref_kind": "repo_path",
                "ref": runtime_escalation_path,
                "label": "runtime_escalation_record",
            }
            if runtime_escalation_path
            else {},
            {
                "ref_kind": "repo_path",
                "ref": str(quest_root / "artifacts" / "reports" / "runtime_watch" / "latest.json"),
                "label": "runtime_watch_latest",
            },
        ],
        state_refs=[
            {
                "role": "status",
                "ref_kind": "repo_path",
                "ref": str(runtime_context.launch_report_path),
                "label": "last_launch_report",
            },
            {
                "role": "audit",
                "ref_kind": "repo_path",
                "ref": str(study_root / "artifacts" / "runtime" / "runtime_supervision" / "latest.json"),
                "label": "runtime_supervision_latest",
            },
            {
                "role": "controller",
                "ref_kind": "repo_path",
                "ref": str(study_root / "artifacts" / "controller_decisions" / "latest.json"),
                "label": "controller_decisions_latest",
            },
        ],
        restoration_evidence=[
            {
                "role": "artifact",
                "ref_kind": "repo_path",
                "ref": runtime_event_artifact_path,
                "label": "runtime_event",
            }
        ]
        if runtime_event_artifact_path
        else [],
        action_graph_id="mas_runtime_orchestration",
        node_id="study_runtime_status",
        gate_id=(human_gates[0].get("gate_id") if human_gates else None),
        resume_mode="reenter_human_gate" if human_gates else "resume_from_checkpoint",
        resume_handle=f"study_runtime_status:{status.study_id}:{runtime_decision or 'unknown'}",
        human_gate_required=bool(human_gates),
        human_gates=human_gates,
    )
    status.extras["family_event_envelope"] = family_payload["family_event_envelope"]
    status.extras["family_checkpoint_lineage"] = family_payload["family_checkpoint_lineage"]
    status.extras["family_human_gates"] = family_payload["family_human_gates"]


def _launch_report_runtime_liveness_status(payload: dict[str, object]) -> str | None:
    runtime_liveness_audit = payload.get("runtime_liveness_audit")
    if isinstance(runtime_liveness_audit, dict):
        status = str(runtime_liveness_audit.get("status") or "").strip()
        if status:
            return status
    status = str(payload.get("runtime_liveness_status") or "").strip()
    return status or None


def _launch_report_supervisor_tick_status(payload: dict[str, object]) -> str | None:
    supervisor_tick_audit = payload.get("supervisor_tick_audit")
    if isinstance(supervisor_tick_audit, dict):
        status = str(supervisor_tick_audit.get("status") or "").strip()
        if status:
            return status
    status = str(payload.get("supervisor_tick_status") or "").strip()
    return status or None


def _record_runtime_event(
    *,
    status: StudyRuntimeStatus,
    runtime_context: study_runtime_protocol.StudyRuntimeContext,
    runtime_backend=None,
) -> None:
    execution = status.execution
    if (
        runtime_backend is None
        or str(execution.get("auto_entry") or "").strip() != "on_managed_research_intent"
        or not status.quest_exists
    ):
        status.extras.pop("runtime_event_ref", None)
        status.extras.pop("runtime_event", None)
        return
    try:
        session_payload = _get_quest_session(
            runtime_root=runtime_context.runtime_root,
            quest_id=status.quest_id,
            runtime_backend=runtime_backend,
        )
    except (RuntimeError, OSError, ValueError):
        status.extras.pop("runtime_event_ref", None)
        status.extras.pop("runtime_event", None)
        return
    runtime_event_ref = session_payload.get("runtime_event_ref")
    if isinstance(runtime_event_ref, dict):
        status.record_runtime_event_ref(runtime_event_ref)
    else:
        status.extras.pop("runtime_event_ref", None)
    runtime_event = session_payload.get("runtime_event")
    if isinstance(runtime_event, dict):
        status["runtime_event"] = dict(runtime_event)
    else:
        status.extras.pop("runtime_event", None)


def _sync_runtime_summary_if_needed(
    *,
    status: StudyRuntimeStatus,
    runtime_context: study_runtime_protocol.StudyRuntimeContext,
) -> None:
    current_snapshot = _runtime_event_status_snapshot(status)
    current_quest_status = (
        str(current_snapshot.get("quest_status") or "").strip() or (status.quest_status.value if status.quest_status is not None else None)
    )
    current_active_run_id = str(current_snapshot.get("active_run_id") or "").strip() or None
    current_runtime_liveness_status = str(current_snapshot.get("runtime_liveness_status") or "").strip() or None
    current_supervisor_tick_status = str(current_snapshot.get("supervisor_tick_status") or "").strip() or None
    current_publication_supervisor_state = (
        dict(status.extras.get("publication_supervisor_state") or {})
        if isinstance(status.extras.get("publication_supervisor_state"), dict)
        else {}
    )
    launch_report_path = runtime_context.launch_report_path
    launch_report_payload = _load_json_dict(launch_report_path) if launch_report_path.exists() else {}
    launch_report_exists = launch_report_path.exists()
    launch_report_quest_status = str(launch_report_payload.get("quest_status") or "").strip() or None
    launch_report_active_run_id = str(launch_report_payload.get("active_run_id") or "").strip() or None
    launch_report_runtime_liveness_status = _launch_report_runtime_liveness_status(launch_report_payload)
    launch_report_supervisor_tick_status = _launch_report_supervisor_tick_status(launch_report_payload)
    launch_report_publication_supervisor_state = (
        dict(launch_report_payload.get("publication_supervisor_state") or {})
        if isinstance(launch_report_payload.get("publication_supervisor_state"), dict)
        else {}
    )
    aligned = launch_report_exists and (
        launch_report_quest_status == current_quest_status
        and launch_report_active_run_id == current_active_run_id
        and launch_report_runtime_liveness_status == current_runtime_liveness_status
        and launch_report_supervisor_tick_status == current_supervisor_tick_status
        and launch_report_publication_supervisor_state == current_publication_supervisor_state
    )
    mismatch_reason: str | None = None
    if not launch_report_exists:
        mismatch_reason = "launch_report_missing"
    elif launch_report_quest_status != current_quest_status:
        mismatch_reason = "launch_report_quest_status_mismatch"
    elif launch_report_active_run_id != current_active_run_id:
        mismatch_reason = "launch_report_active_run_id_mismatch"
    elif launch_report_runtime_liveness_status != current_runtime_liveness_status:
        mismatch_reason = "launch_report_runtime_liveness_status_mismatch"
    elif launch_report_supervisor_tick_status != current_supervisor_tick_status:
        mismatch_reason = "launch_report_supervisor_tick_status_mismatch"
    elif launch_report_publication_supervisor_state != current_publication_supervisor_state:
        mismatch_reason = "launch_report_publication_supervisor_state_mismatch"
    status_sync_applied = False
    if not aligned:
        study_runtime_protocol.persist_runtime_artifacts(
            runtime_binding_path=runtime_context.runtime_binding_path,
            launch_report_path=launch_report_path,
            runtime_root=runtime_context.runtime_root,
            study_id=status.study_id,
            study_root=Path(status.study_root),
            quest_id=status.quest_id if status.quest_exists else None,
            last_action=None,
            status=status.to_dict(),
            source="study_runtime_status",
            force=False,
            startup_payload_path=None,
            daemon_result=None,
            recorded_at=_router_module()._utc_now(),
        )
        status_sync_applied = True
    status.record_runtime_summary_alignment(
        StudyRuntimeSummaryAlignment(
            source_of_truth="study_runtime_status",
            runtime_state_path=str(_runtime_state_path(runtime_context.quest_root)),
            runtime_state_status=current_quest_status,
            source_active_run_id=current_active_run_id,
            source_runtime_liveness_status=current_runtime_liveness_status,
            source_supervisor_tick_status=current_supervisor_tick_status,
            launch_report_path=str(launch_report_path),
            launch_report_exists=launch_report_exists,
            launch_report_quest_status=launch_report_quest_status,
            launch_report_active_run_id=launch_report_active_run_id,
            launch_report_runtime_liveness_status=launch_report_runtime_liveness_status,
            launch_report_supervisor_tick_status=launch_report_supervisor_tick_status,
            aligned=aligned,
            mismatch_reason=mismatch_reason,
            status_sync_applied=status_sync_applied,
        )
    )


def _should_refresh_runtime_supervision_from_status(
    *,
    status: StudyRuntimeStatus,
    study_root: Path,
) -> bool:
    latest_report_path = study_root / "artifacts" / "runtime" / "runtime_supervision" / "latest.json"
    latest_report = _read_json_mapping(latest_report_path)
    if latest_report is None:
        return False
    status_payload = status.to_dict()
    facts = runtime_supervision_controller._runtime_facts(status_payload)
    strict_live = bool(facts["strict_live"])
    decision = str(status_payload.get("decision") or "").strip() or None
    reason = str(status_payload.get("reason") or "").strip() or None
    quest_status = str(status_payload.get("quest_status") or "").strip() or None
    if strict_live:
        target_health_status = "live"
    elif runtime_supervision_controller._needs_drop_detection(status_payload, strict_live=strict_live):
        target_health_status = "degraded"
    else:
        return False
    return any(
        (
            (str(latest_report.get("health_status") or "").strip() or None) != target_health_status,
            (str(latest_report.get("active_run_id") or "").strip() or None) != facts["active_run_id"],
            (str(latest_report.get("runtime_liveness_status") or "").strip() or None)
            != facts["runtime_liveness_status"],
            (str(latest_report.get("runtime_decision") or "").strip() or None) != decision,
            (str(latest_report.get("runtime_reason") or "").strip() or None) != reason,
            (str(latest_report.get("quest_status") or "").strip() or None) != quest_status,
        )
    )


def _find_pending_interaction_artifact_path(*, quest_root: Path, interaction_id: str) -> Path | None:
    resolved_interaction_id = str(interaction_id or "").strip()
    if not resolved_interaction_id:
        return None
    candidates: list[Path] = []
    patterns = (
        f".ds/worktrees/*/artifacts/*/{resolved_interaction_id}.json",
        f"artifacts/*/{resolved_interaction_id}.json",
    )
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
    return stop_reason is None


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
