from __future__ import annotations

if __name__ != "med_autoscience.controllers.study_runtime_decision":
    from .human_gates import *  # noqa: F403


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
    launch_report_stale = bool(
        launch_report_exists
        and launch_report_active_run_id is not None
        and launch_report_runtime_liveness_status == "live"
        and (
            current_active_run_id != launch_report_active_run_id
            or current_runtime_liveness_status != "live"
        )
    )
    status_sync_applied = False
    if not aligned:
        if launch_report_stale:
            status.extras["last_known_run_id"] = launch_report_active_run_id
            status.extras["stale_launch_report_invalidated"] = True
            status.extras["stale_launch_report_active_run_id"] = launch_report_active_run_id
            status.extras["stale_launch_report_runtime_liveness_status"] = launch_report_runtime_liveness_status
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
            launch_report_stale=launch_report_stale,
            stale_launch_report_active_run_id=launch_report_active_run_id if launch_report_stale else None,
            stale_launch_report_runtime_liveness_status=(
                launch_report_runtime_liveness_status if launch_report_stale else None
            ),
        )
    )


def _should_refresh_runtime_supervision_from_status(
    *,
    status: StudyRuntimeStatus,
    study_root: Path,
) -> bool:
    status_payload = status.to_dict()
    facts = runtime_supervision_controller._runtime_facts(status_payload)
    strict_live = bool(facts["strict_live"])
    decision = str(status_payload.get("decision") or "").strip() or None
    reason = str(status_payload.get("reason") or "").strip() or None
    quest_status = str(status_payload.get("quest_status") or "").strip() or None
    runtime_health_snapshot = status_payload.get("runtime_health_snapshot")
    if not isinstance(runtime_health_snapshot, dict):
        runtime_health_snapshot = {}
    runtime_health_action = str(runtime_health_snapshot.get("canonical_runtime_action") or "").strip() or None
    runtime_health_attempt_state = str(runtime_health_snapshot.get("attempt_state") or "").strip() or None
    retry_budget_remaining = runtime_health_snapshot.get("retry_budget_remaining")
    if runtime_health_action == "escalate_runtime" or (
        runtime_health_attempt_state == "escalated"
        and retry_budget_remaining == 0
    ):
        target_health_status = "escalated"
    elif runtime_health_action == "recover_runtime" or runtime_health_attempt_state == "recovering":
        target_health_status = "recovering"
    elif strict_live:
        target_health_status = "live"
    elif runtime_supervision_controller.needs_recovery_projection(status_payload, strict_live=strict_live):
        target_health_status = "recovering"
    elif runtime_supervision_controller._needs_drop_detection(status_payload, strict_live=strict_live):
        target_health_status = "degraded"
    else:
        return False
    latest_report_path = study_root / "artifacts" / "runtime" / "runtime_supervision" / "latest.json"
    latest_report = _read_json_mapping(latest_report_path)
    if latest_report is None:
        return True
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


__all__ = [name for name in globals() if not name.startswith("__")]
