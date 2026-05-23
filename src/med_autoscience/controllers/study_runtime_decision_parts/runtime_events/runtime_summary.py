from __future__ import annotations

from collections.abc import Mapping

if __name__ != "med_autoscience.controllers.study_runtime_decision":
    from .human_gates import *  # noqa: F403

from med_autoscience.controllers.opl_runtime_refs import resolve_opl_runtime_refs


def _public_executor_source_surface(execution: dict[str, Any]) -> str:
    executor_kind = str(execution.get("executor_kind") or "").strip()
    if executor_kind in {"codex_cli", "hermes_agent"}:
        return executor_kind
    executor = str(execution.get("executor") or "").strip()
    if executor == "hermes_agent":
        return "hermes_agent"
    return "codex_cli"


def _record_family_orchestration_companion(
    *,
    status: ProgressProjectionStatus,
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
        surface_kind="progress_projection",
        surface_id="progress_projection",
        event_name=f"progress_projection.{runtime_decision or 'observed'}",
        source_surface=_public_executor_source_surface(status.execution),
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
        checkpoint_id=f"progress-projection:{status.study_id}:{runtime_decision or 'unknown'}",
        checkpoint_label="progress_projection snapshot",
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
                "ref": str(quest_root / "artifacts" / "reports" / "domain_health_diagnostic" / "latest.json"),
                "label": "domain_health_diagnostic_latest",
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
                "ref": str(study_root / "artifacts" / "supervision" / "opl_runtime_owner_handoff" / "latest.json"),
                "label": "opl_runtime_owner_handoff_latest",
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
        node_id="progress_projection",
        gate_id=(human_gates[0].get("gate_id") if human_gates else None),
        resume_mode="reenter_human_gate" if human_gates else "resume_from_checkpoint",
        resume_handle=f"progress_projection:{status.study_id}:{runtime_decision or 'unknown'}",
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
    status: ProgressProjectionStatus,
    runtime_context: study_runtime_protocol.StudyRuntimeContext,
) -> None:
    if not status.quest_exists:
        status.extras.pop("runtime_event_ref", None)
        status.extras.pop("runtime_event", None)
        return
    try:
        runtime_event_ref = study_runtime_protocol.read_runtime_event_record_ref(
            quest_root=runtime_context.quest_root
        )
    except (OSError, RuntimeError, TypeError, ValueError):
        status.extras.pop("runtime_event_ref", None)
        status.extras.pop("runtime_event", None)
        return
    if runtime_event_ref is None:
        status.extras.pop("runtime_event_ref", None)
        status.extras.pop("runtime_event", None)
        return
    status.record_runtime_event_ref(runtime_event_ref)
    status.extras.pop("runtime_event", None)


def _sync_runtime_summary_if_needed(
    *,
    status: ProgressProjectionStatus,
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
    launch_report_exists = launch_report_path.exists()
    launch_report_payload, launch_report_read_error = _load_json_dict_with_error(launch_report_path)
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
    if launch_report_read_error is not None:
        mismatch_reason = f"launch_report_{launch_report_read_error}"
    elif not launch_report_exists:
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
            source="progress_projection",
            force=False,
            startup_payload_path=None,
            daemon_result=None,
            recorded_at=_router_module()._utc_now(),
        )
        status_sync_applied = True
    status.record_runtime_summary_alignment(
        StudyRuntimeSummaryAlignment(
            source_of_truth="progress_projection",
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


def _should_materialize_opl_runtime_owner_handoff_from_status(
    *,
    status: ProgressProjectionStatus,
    study_root: Path,
) -> bool:
    status_payload = status.to_dict()
    refs = resolve_opl_runtime_refs(status_payload)
    strict_live = refs.strict_live
    reason = str(status_payload.get("reason") or "").strip() or None
    study_id = str(status_payload.get("study_id") or "").strip() or None
    quest_id = str(status_payload.get("quest_id") or "").strip() or None
    quest_root = str(status_payload.get("quest_root") or "").strip() or None
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
        handoff_context = "escalated"
    elif runtime_health_action == "recover_runtime" or runtime_health_attempt_state == "recovering":
        handoff_context = "recovering"
    elif strict_live:
        handoff_context = "live"
    elif _opl_runtime_recovery_projection_needed(status_payload, refs=refs):
        handoff_context = "recovering"
    elif reason == "quest_waiting_opl_runtime_owner_route":
        handoff_context = "blocked"
    elif _opl_runtime_drop_detection_needed(status_payload, strict_live=strict_live):
        handoff_context = "degraded"
    else:
        return False
    latest_handoff_path = study_root / "artifacts" / "supervision" / "opl_runtime_owner_handoff" / "latest.json"
    latest_handoff = _read_json_mapping(latest_handoff_path)
    if latest_handoff is None:
        return True
    latest_typed_blocker = latest_handoff.get("typed_blocker")
    if not isinstance(latest_typed_blocker, dict):
        latest_typed_blocker = {}
    latest_refs = latest_handoff.get("opl_current_control_state_ref")
    if not isinstance(latest_refs, dict):
        latest_refs = {}
    return any(
        (
            (str(latest_handoff.get("status") or "").strip() or None) != "handoff_required",
            latest_handoff.get("mas_materializes_runtime_supervision") is not False,
            latest_handoff.get("mas_runtime_read_model_retired") is not True,
            latest_handoff.get("provider_completion_is_domain_completion") is not False,
            latest_handoff.get("queue_succeeded_is_domain_completion") is not False,
            (str(latest_handoff.get("runtime_owner") or "").strip() or None) != "one-person-lab",
            (str(latest_handoff.get("domain_owner") or "").strip() or None) != "med-autoscience",
            (str(latest_handoff.get("study_id") or "").strip() or None) != study_id,
            (str(latest_handoff.get("quest_id") or "").strip() or None) != quest_id,
            (str(latest_handoff.get("quest_root") or "").strip() or None) != quest_root,
            (str(latest_handoff.get("reason") or "").strip() or None) != reason,
            latest_refs.get("required") is not True,
            (str(latest_refs.get("hydrate_from") or "").strip() or None) != "MAS DomainIntent / owner-route refs",
            (str(latest_typed_blocker.get("blocker_type") or "").strip() or None)
            != "opl_runtime_owner_handoff_required",
            (str(latest_typed_blocker.get("owner") or "").strip() or None) != "one-person-lab",
            (str(latest_typed_blocker.get("domain_owner") or "").strip() or None) != "med-autoscience",
            not handoff_context,
        )
    )


def _opl_runtime_recovery_projection_needed(
    status_payload: Mapping[str, Any],
    *,
    refs: Any,
) -> bool:
    if refs.strict_live:
        return False
    if _status_payload_human_gate_required_for_opl_runtime_ref(status_payload):
        return False
    quest_status = str(status_payload.get("quest_status") or "").strip()
    if quest_status not in {"running", "active"}:
        return False
    supervisor_tick_audit = status_payload.get("supervisor_tick_audit")
    supervisor_tick_status = (
        str(supervisor_tick_audit.get("status") or "").strip()
        if isinstance(supervisor_tick_audit, Mapping)
        else None
    )
    if supervisor_tick_status not in {"missing", "stale", "invalid"}:
        return False
    return refs.active_run_id is None


def _status_payload_human_gate_required_for_opl_runtime_ref(status_payload: Mapping[str, Any]) -> bool:
    family_checkpoint_lineage = status_payload.get("family_checkpoint_lineage")
    resume_contract = (
        family_checkpoint_lineage.get("resume_contract")
        if isinstance(family_checkpoint_lineage, Mapping)
        else None
    )
    if isinstance(resume_contract, Mapping) and isinstance(resume_contract.get("human_gate_required"), bool):
        return bool(resume_contract.get("human_gate_required"))
    interaction_arbitration = status_payload.get("interaction_arbitration")
    if isinstance(interaction_arbitration, Mapping) and bool(interaction_arbitration.get("requires_user_input")):
        return True
    publication_supervisor_state = status_payload.get("publication_supervisor_state")
    if isinstance(publication_supervisor_state, Mapping):
        current_required_action = str(publication_supervisor_state.get("current_required_action") or "").strip()
        return current_required_action == "human_confirmation_required"
    return False


def _opl_runtime_drop_detection_needed(status_payload: Mapping[str, Any], *, strict_live: bool) -> bool:
    if strict_live:
        return False
    decision = str(status_payload.get("decision") or "").strip()
    reason = str(status_payload.get("reason") or "").strip()
    quest_status = str(status_payload.get("quest_status") or "").strip()
    if reason in {
        "quest_marked_running_but_no_live_session",
        "running_quest_live_session_audit_failed",
        "resume_request_failed",
        "create_request_failed",
    }:
        return True
    if decision in {"create_and_start", "resume", "relaunch_stopped"}:
        return False
    return quest_status in {"running", "active"}


__all__ = [name for name in globals() if not name.startswith("__")]
