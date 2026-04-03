from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from med_autoscience.controllers import (
    journal_shortlist as journal_shortlist_controller,
    medical_analysis_contract as medical_analysis_contract_controller,
    medical_reporting_contract as medical_reporting_contract_controller,
    quest_hydration as quest_hydration_controller,
    runtime_reentry_gate as runtime_reentry_gate_controller,
    startup_hydration_validation as startup_hydration_validation_controller,
    startup_data_readiness as startup_data_readiness_controller,
    startup_boundary_gate as startup_boundary_gate_controller,
)
from med_autoscience.overlay import installer as overlay_installer
from med_autoscience.policies.automation_ready import render_automation_ready_summary
from med_autoscience.policies.controller_first import render_controller_first_summary
from med_autoscience.profiles import WorkspaceProfile
from med_autoscience.runtime_protocol import quest_state
from med_autoscience.runtime_protocol import study_runtime as study_runtime_protocol
from med_autoscience.runtime_transport import med_deepscientist as med_deepscientist_transport
from med_autoscience.study_completion import (
    StudyCompletionState,
    StudyCompletionStateStatus,
    resolve_study_completion_state,
)
from med_autoscience.controllers.study_runtime_types import (
    StudyCompletionSyncResult,
    StudyRuntimeAnalysisBundleResult,
    StudyRuntimeAuditRecord,
    StudyRuntimeAuditStatus,
    StudyRuntimeBindingAction,
    StudyRuntimeDaemonStep,
    StudyRuntimeDecision,
    StudyRuntimeExecutionContext,
    StudyRuntimeExecutionOutcome,
    StudyRuntimeOverlayAudit,
    StudyRuntimeOverlayResult,
    StudyRuntimePartialQuestRecoveryResult,
    StudyRuntimeQuestStatus,
    StudyRuntimeReason,
    StudyRuntimeReentryGate,
    StudyRuntimeStartupBoundaryGate,
    StudyRuntimeStartupContextSyncResult,
    StudyRuntimeStartupDataReadinessReport,
    StudyRuntimeStatus,
    StudyRuntimeWorkspaceContractsSummary,
    _LIVE_QUEST_STATUSES,
    _RESUMABLE_QUEST_STATUSES,
)
from med_autoscience.controllers.study_runtime_completion import (
    _build_study_completion_request_message,
    _study_completion_state,
    _sync_study_completion,
)
from med_autoscience.controllers.study_runtime_decision import (
    _record_quest_runtime_audits,
    _status_payload,
    _status_state,
)
from med_autoscience.controllers.study_runtime_startup import (
    _audit_runtime_overlay,
    _build_create_payload,
    _build_startup_contract,
    _prepare_runtime_overlay,
    _run_startup_hydration,
    _runtime_reentry_requires_managed_skill_audit,
    _runtime_reentry_requires_startup_hydration,
    _sync_existing_quest_startup_context,
)
from med_autoscience import study_runtime_analysis_bundle as analysis_bundle_controller
from med_autoscience.workspace_contracts import inspect_workspace_contracts


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _timestamp_slug() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _load_yaml_dict(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"missing required YAML file: {path}")
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"expected YAML mapping at {path}")
    return payload


def _resolve_study(
    *,
    profile: WorkspaceProfile,
    study_id: str | None,
    study_root: Path | None,
) -> tuple[str, Path, dict[str, Any]]:
    if study_id is None and study_root is None:
        raise ValueError("study_id or study_root is required")
    if study_root is not None:
        resolved_study_root = Path(study_root).expanduser().resolve()
    else:
        resolved_study_root = (profile.studies_root / str(study_id)).resolve()
    study_payload = _load_yaml_dict(resolved_study_root / "study.yaml")
    resolved_study_id = str(study_payload.get("study_id") or study_id or resolved_study_root.name).strip()
    if not resolved_study_id:
        raise ValueError(f"could not resolve study_id from {resolved_study_root / 'study.yaml'}")
    if study_id is not None and str(study_id).strip() != resolved_study_id:
        raise ValueError(f"study_id mismatch: expected {study_id}, got {resolved_study_id}")
    return resolved_study_id, resolved_study_root, study_payload


def _execution_payload(study_payload: dict[str, Any]) -> dict[str, Any]:
    execution = study_payload.get("execution")
    if not isinstance(execution, dict):
        return {}
    return dict(execution)


def _build_execution_context(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    study_root: Path,
    study_payload: dict[str, Any],
    source: str,
) -> StudyRuntimeExecutionContext:
    execution = _execution_payload(study_payload)
    quest_id = str(execution.get("quest_id") or study_id).strip() or study_id
    runtime_context = study_runtime_protocol.resolve_study_runtime_context(
        profile=profile,
        study_root=study_root,
        study_id=study_id,
        quest_id=quest_id,
    )
    completion_state = _study_completion_state(study_root=study_root)
    return StudyRuntimeExecutionContext(
        profile=profile,
        study_id=study_id,
        study_root=study_root,
        study_payload=study_payload,
        execution=execution,
        quest_id=quest_id,
        runtime_context=runtime_context,
        completion_state=completion_state,
        source=source,
    )


def _build_context_create_payload(context: StudyRuntimeExecutionContext) -> dict[str, Any]:
    return _build_create_payload(
        profile=context.profile,
        study_id=context.study_id,
        study_root=context.study_root,
        study_payload=context.study_payload,
        execution=context.execution,
    )


def _run_runtime_preflight(
    *,
    status: StudyRuntimeStatus,
    context: StudyRuntimeExecutionContext,
) -> None:
    if status.decision in {
        StudyRuntimeDecision.CREATE_AND_START,
        StudyRuntimeDecision.CREATE_ONLY,
        StudyRuntimeDecision.RESUME,
    }:
        analysis_bundle_result = StudyRuntimeAnalysisBundleResult.from_payload(
            analysis_bundle_controller.ensure_study_runtime_analysis_bundle()
        )
        status.record_analysis_bundle(analysis_bundle_result)
        if not analysis_bundle_result.ready:
            status.set_decision(
                StudyRuntimeDecision.BLOCKED,
                StudyRuntimeReason.STUDY_RUNTIME_ANALYSIS_BUNDLE_NOT_READY,
            )
        elif status.runtime_reentry_requires_managed_skill_audit and not context.profile.enable_medical_overlay:
            status.set_decision(
                StudyRuntimeDecision.BLOCKED,
                StudyRuntimeReason.MANAGED_SKILL_AUDIT_NOT_AVAILABLE,
            )
        elif context.profile.enable_medical_overlay and status.decision == StudyRuntimeDecision.RESUME:
            runtime_overlay_result = StudyRuntimeOverlayResult.from_payload(
                _prepare_runtime_overlay(
                    profile=context.profile,
                    quest_root=context.quest_root,
                )
            )
            status.record_runtime_overlay(runtime_overlay_result)
            if not runtime_overlay_result.audit.all_roots_ready:
                status.set_decision(
                    StudyRuntimeDecision.BLOCKED,
                    StudyRuntimeReason.RUNTIME_OVERLAY_NOT_READY,
                )
    elif context.profile.enable_medical_overlay and status.quest_exists:
        runtime_overlay_result = StudyRuntimeOverlayResult.from_payload(
            {"audit": _audit_runtime_overlay(profile=context.profile, quest_root=context.quest_root)}
        )
        status.record_runtime_overlay(runtime_overlay_result)
        if status.quest_status in _LIVE_QUEST_STATUSES and not runtime_overlay_result.audit.all_roots_ready:
            status.set_decision(
                StudyRuntimeDecision.PAUSE,
                StudyRuntimeReason.RUNTIME_OVERLAY_AUDIT_FAILED_FOR_RUNNING_QUEST,
            )


def _execute_create_runtime_decision(
    *,
    status: StudyRuntimeStatus,
    context: StudyRuntimeExecutionContext,
) -> StudyRuntimeExecutionOutcome:
    planned_decision = status.decision
    outcome = StudyRuntimeExecutionOutcome()
    create_payload = _build_context_create_payload(context)
    startup_contract_validation = study_runtime_protocol.validate_startup_contract_resolution(
        startup_contract=dict(create_payload.get("startup_contract") or {})
    )
    status.record_startup_contract_validation(startup_contract_validation.to_dict())
    if startup_contract_validation.status is not study_runtime_protocol.StartupContractValidationStatus.CLEAR:
        status.set_decision(
            StudyRuntimeDecision.BLOCKED,
            StudyRuntimeReason.STARTUP_CONTRACT_RESOLUTION_FAILED,
        )
    partial_quest_recovery = study_runtime_protocol.archive_invalid_partial_quest_root(
        quest_root=context.quest_root,
        runtime_root=context.runtime_root,
        slug=_timestamp_slug(),
    )
    if partial_quest_recovery is not None:
        status.record_partial_quest_recovery(StudyRuntimePartialQuestRecoveryResult.from_payload(partial_quest_recovery))
    create_payload["auto_start"] = False
    if status.decision not in {StudyRuntimeDecision.CREATE_AND_START, StudyRuntimeDecision.CREATE_ONLY}:
        return outcome
    outcome.startup_payload_path = study_runtime_protocol.write_startup_payload(
        startup_payload_root=context.startup_payload_root,
        create_payload=create_payload,
        slug=_timestamp_slug(),
    )
    create_result = med_deepscientist_transport.create_quest(
        runtime_root=context.runtime_root,
        payload=create_payload,
    )
    outcome.record_daemon_step(StudyRuntimeDaemonStep.CREATE, create_result)
    status.update_quest_runtime(
        quest_id=create_payload["quest_id"],
        quest_root=context.quest_root,
        quest_exists=True,
        quest_status=outcome.quest_status_for_step(StudyRuntimeDaemonStep.CREATE, fallback="created"),
    )
    if context.profile.enable_medical_overlay:
        runtime_overlay_result = StudyRuntimeOverlayResult.from_payload(
            _prepare_runtime_overlay(
                profile=context.profile,
                quest_root=context.quest_root,
            )
        )
        status.record_runtime_overlay(runtime_overlay_result)
        if not runtime_overlay_result.audit.all_roots_ready:
            status.set_decision(
                StudyRuntimeDecision.BLOCKED,
                StudyRuntimeReason.RUNTIME_OVERLAY_NOT_READY,
            )
    if status.decision == StudyRuntimeDecision.BLOCKED:
        outcome.binding_last_action = StudyRuntimeBindingAction.BLOCKED
        return outcome
    hydration_result, validation_result = _run_startup_hydration(
        quest_root=context.quest_root,
        create_payload=create_payload,
    )
    status.record_startup_hydration(hydration_result, validation_result)
    if validation_result.status is not study_runtime_protocol.StartupHydrationValidationStatus.CLEAR:
        status.set_decision(
            StudyRuntimeDecision.BLOCKED,
            StudyRuntimeReason.HYDRATION_VALIDATION_FAILED,
        )
        outcome.binding_last_action = StudyRuntimeBindingAction.BLOCKED
        return outcome
    if planned_decision == StudyRuntimeDecision.CREATE_AND_START:
        resume_result = med_deepscientist_transport.resume_quest(
            runtime_root=context.runtime_root,
            quest_id=status.quest_id,
            source=context.source,
        )
        outcome.record_daemon_step(StudyRuntimeDaemonStep.RESUME, resume_result)
        status.update_quest_runtime(
            quest_status=outcome.quest_status_for_step(StudyRuntimeDaemonStep.RESUME, fallback="running"),
        )
        outcome.binding_last_action = StudyRuntimeBindingAction.CREATE_AND_START
    else:
        outcome.binding_last_action = StudyRuntimeBindingAction.CREATE_ONLY
    return outcome


def _execute_resume_runtime_decision(
    *,
    status: StudyRuntimeStatus,
    context: StudyRuntimeExecutionContext,
) -> StudyRuntimeExecutionOutcome:
    outcome = StudyRuntimeExecutionOutcome()
    create_payload = _build_context_create_payload(context)
    startup_context_sync = _sync_existing_quest_startup_context(
        runtime_root=context.runtime_root,
        quest_id=status.quest_id,
        create_payload=create_payload,
    )
    status.record_startup_context_sync(StudyRuntimeStartupContextSyncResult.from_payload(startup_context_sync))
    hydration_result, validation_result = _run_startup_hydration(
        quest_root=context.quest_root,
        create_payload=create_payload,
    )
    status.record_startup_hydration(hydration_result, validation_result)
    if validation_result.status is not study_runtime_protocol.StartupHydrationValidationStatus.CLEAR:
        status.set_decision(
            StudyRuntimeDecision.BLOCKED,
            StudyRuntimeReason.HYDRATION_VALIDATION_FAILED,
        )
        outcome.binding_last_action = StudyRuntimeBindingAction.BLOCKED
        return outcome
    resume_result = med_deepscientist_transport.resume_quest(
        runtime_root=context.runtime_root,
        quest_id=status.quest_id,
        source=context.source,
    )
    outcome.record_daemon_step(StudyRuntimeDaemonStep.RESUME, resume_result)
    status.update_quest_runtime(
        quest_status=outcome.quest_status_for_step(StudyRuntimeDaemonStep.RESUME, fallback="running"),
    )
    outcome.binding_last_action = StudyRuntimeBindingAction.RESUME
    return outcome


def _execute_blocked_refresh_runtime_decision(
    *,
    status: StudyRuntimeStatus,
    context: StudyRuntimeExecutionContext,
) -> StudyRuntimeExecutionOutcome:
    outcome = StudyRuntimeExecutionOutcome(binding_last_action=StudyRuntimeBindingAction.BLOCKED)
    create_payload = _build_context_create_payload(context)
    startup_contract_validation = study_runtime_protocol.validate_startup_contract_resolution(
        startup_contract=dict(create_payload.get("startup_contract") or {})
    )
    status.record_startup_contract_validation(startup_contract_validation.to_dict())
    if startup_contract_validation.status is not study_runtime_protocol.StartupContractValidationStatus.CLEAR:
        status.set_decision(
            StudyRuntimeDecision.BLOCKED,
            StudyRuntimeReason.STARTUP_CONTRACT_RESOLUTION_FAILED,
        )
        return outcome
    startup_context_sync = _sync_existing_quest_startup_context(
        runtime_root=context.runtime_root,
        quest_id=status.quest_id,
        create_payload=create_payload,
    )
    status.record_startup_context_sync(StudyRuntimeStartupContextSyncResult.from_payload(startup_context_sync))
    hydration_result, validation_result = _run_startup_hydration(
        quest_root=context.quest_root,
        create_payload=create_payload,
    )
    status.record_startup_hydration(hydration_result, validation_result)
    if validation_result.status is not study_runtime_protocol.StartupHydrationValidationStatus.CLEAR:
        status.set_decision(
            StudyRuntimeDecision.BLOCKED,
            StudyRuntimeReason.HYDRATION_VALIDATION_FAILED,
        )
    return outcome


def _execute_pause_runtime_decision(
    *,
    status: StudyRuntimeStatus,
    context: StudyRuntimeExecutionContext,
) -> StudyRuntimeExecutionOutcome:
    pause_result = med_deepscientist_transport.pause_quest(
        runtime_root=context.runtime_root,
        quest_id=status.quest_id,
        source=context.source,
    )
    outcome = StudyRuntimeExecutionOutcome(binding_last_action=StudyRuntimeBindingAction.PAUSE)
    outcome.record_daemon_step(StudyRuntimeDaemonStep.PAUSE, pause_result)
    status.update_quest_runtime(
        quest_status=outcome.quest_status_for_step(StudyRuntimeDaemonStep.PAUSE, fallback="paused"),
    )
    return outcome


def _execute_completion_runtime_decision(
    *,
    status: StudyRuntimeStatus,
    context: StudyRuntimeExecutionContext,
) -> StudyRuntimeExecutionOutcome:
    outcome = StudyRuntimeExecutionOutcome()
    if status.decision == StudyRuntimeDecision.PAUSE_AND_COMPLETE:
        pause_result = med_deepscientist_transport.pause_quest(
            runtime_root=context.runtime_root,
            quest_id=status.quest_id,
            source=context.source,
        )
        outcome.record_daemon_step(StudyRuntimeDaemonStep.PAUSE, pause_result)
        status.update_quest_runtime(
            quest_status=outcome.quest_status_for_step(StudyRuntimeDaemonStep.PAUSE, fallback="paused"),
        )
    completion_sync = StudyCompletionSyncResult.from_payload(
        _sync_study_completion(
            runtime_root=context.runtime_root,
            quest_id=status.quest_id,
            study_id=context.study_id,
            study_root=context.study_root,
            completion_state=context.completion_state,
            source=context.source,
        )
    )
    outcome.record_daemon_step(StudyRuntimeDaemonStep.COMPLETION_SYNC, completion_sync.to_dict())
    status.record_completion_sync(completion_sync)
    status.update_quest_runtime(
        quest_status=completion_sync.snapshot_status_or("completed"),
    )
    status.set_decision(
        StudyRuntimeDecision.COMPLETED,
        StudyRuntimeReason.STUDY_COMPLETION_SYNCED,
    )
    outcome.binding_last_action = StudyRuntimeBindingAction.COMPLETED
    return outcome


def _execute_runtime_decision(
    *,
    status: StudyRuntimeStatus,
    context: StudyRuntimeExecutionContext,
) -> StudyRuntimeExecutionOutcome:
    if status.decision in {StudyRuntimeDecision.CREATE_AND_START, StudyRuntimeDecision.CREATE_ONLY}:
        return _execute_create_runtime_decision(status=status, context=context)
    if status.decision == StudyRuntimeDecision.RESUME:
        return _execute_resume_runtime_decision(status=status, context=context)
    if status.should_refresh_startup_hydration_while_blocked():
        return _execute_blocked_refresh_runtime_decision(status=status, context=context)
    if status.decision == StudyRuntimeDecision.PAUSE:
        return _execute_pause_runtime_decision(status=status, context=context)
    if status.decision in {StudyRuntimeDecision.SYNC_COMPLETION, StudyRuntimeDecision.PAUSE_AND_COMPLETE}:
        return _execute_completion_runtime_decision(status=status, context=context)
    if status.decision == StudyRuntimeDecision.COMPLETED:
        return StudyRuntimeExecutionOutcome(binding_last_action=StudyRuntimeBindingAction.COMPLETED)
    if status.decision == StudyRuntimeDecision.NOOP:
        return StudyRuntimeExecutionOutcome(binding_last_action=StudyRuntimeBindingAction.NOOP)
    if status.decision == StudyRuntimeDecision.BLOCKED:
        return StudyRuntimeExecutionOutcome(
            binding_last_action=StudyRuntimeBindingAction.BLOCKED if status.quest_exists else None
        )
    if status.decision == StudyRuntimeDecision.LIGHTWEIGHT:
        return StudyRuntimeExecutionOutcome()
    raise ValueError(f"unsupported study runtime decision: {status.decision}")


def study_runtime_status(
    *,
    profile: WorkspaceProfile,
    study_id: str | None = None,
    study_root: Path | None = None,
    entry_mode: str | None = None,
) -> dict[str, Any]:
    resolved_study_id, resolved_study_root, study_payload = _resolve_study(
        profile=profile,
        study_id=study_id,
        study_root=study_root,
    )
    return _status_payload(
        profile=profile,
        study_id=resolved_study_id,
        study_root=resolved_study_root,
        study_payload=study_payload,
        entry_mode=entry_mode,
    )


def ensure_study_runtime(
    *,
    profile: WorkspaceProfile,
    study_id: str | None = None,
    study_root: Path | None = None,
    entry_mode: str | None = None,
    force: bool = False,
    source: str = "med_autoscience",
) -> dict[str, Any]:
    resolved_study_id, resolved_study_root, study_payload = _resolve_study(
        profile=profile,
        study_id=study_id,
        study_root=study_root,
    )
    context = _build_execution_context(
        profile=profile,
        study_id=resolved_study_id,
        study_root=resolved_study_root,
        study_payload=study_payload,
        source=source,
    )
    status = _status_state(
        profile=profile,
        study_id=resolved_study_id,
        study_root=resolved_study_root,
        study_payload=study_payload,
        entry_mode=entry_mode,
    )
    _run_runtime_preflight(status=status, context=context)
    outcome = _execute_runtime_decision(status=status, context=context)

    artifact_paths = study_runtime_protocol.persist_runtime_artifacts(
        runtime_binding_path=context.runtime_binding_path,
        launch_report_path=context.launch_report_path,
        runtime_root=context.runtime_root,
        study_id=resolved_study_id,
        study_root=resolved_study_root,
        quest_id=status.quest_id.strip() or None,
        last_action=outcome.binding_last_action.value if outcome.binding_last_action is not None else None,
        status=status.to_dict(),
        source=source,
        force=force,
        startup_payload_path=outcome.startup_payload_path,
        daemon_result=outcome.serialized_daemon_result(),
        recorded_at=_utc_now(),
    )
    status.record_runtime_artifacts(
        runtime_binding_path=artifact_paths.runtime_binding_path,
        launch_report_path=artifact_paths.launch_report_path,
        startup_payload_path=artifact_paths.startup_payload_path,
    )
    return status.to_dict()
