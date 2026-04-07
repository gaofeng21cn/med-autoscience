from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from pathlib import Path
from typing import Any

from med_autoscience import study_runtime_analysis_bundle as analysis_bundle_controller
from med_autoscience.profiles import WorkspaceProfile
from med_autoscience.runtime_protocol import study_runtime as study_runtime_protocol
from med_autoscience.study_completion import StudyCompletionState

from .study_runtime_status import (
    StudyCompletionSyncResult,
    StudyRuntimeAnalysisBundleResult,
    StudyRuntimeBindingAction,
    StudyRuntimeDaemonStep,
    StudyRuntimeDecision,
    StudyRuntimeOverlayResult,
    StudyRuntimePartialQuestRecoveryResult,
    StudyRuntimeReason,
    StudyRuntimeStatus,
    _LIVE_QUEST_STATUSES,
)

__all__ = [
    "StudyRuntimeExecutionContext",
    "StudyRuntimeExecutionOutcome",
    "_build_context_create_payload",
    "_build_execution_context",
    "_execute_blocked_refresh_runtime_decision",
    "_execute_completion_runtime_decision",
    "_execute_create_runtime_decision",
    "_execute_pause_runtime_decision",
    "_execute_resume_runtime_decision",
    "_execute_runtime_decision",
    "_persist_runtime_artifacts",
    "_run_runtime_preflight",
]


def _router_module():
    return import_module("med_autoscience.controllers.study_runtime_router")


@dataclass(frozen=True)
class StudyRuntimeExecutionContext:
    profile: WorkspaceProfile
    study_id: str
    study_root: Path
    study_payload: dict[str, Any]
    execution: dict[str, Any]
    quest_id: str
    runtime_context: study_runtime_protocol.StudyRuntimeContext
    completion_state: StudyCompletionState
    source: str

    @property
    def runtime_root(self) -> Path:
        return self.runtime_context.runtime_root

    @property
    def quest_root(self) -> Path:
        return self.runtime_context.quest_root

    @property
    def runtime_binding_path(self) -> Path:
        return self.runtime_context.runtime_binding_path

    @property
    def launch_report_path(self) -> Path:
        return self.runtime_context.launch_report_path

    @property
    def startup_payload_root(self) -> Path:
        return self.runtime_context.startup_payload_root


@dataclass
class StudyRuntimeExecutionOutcome:
    binding_last_action: StudyRuntimeBindingAction | None = None
    startup_payload_path: Path | None = None
    daemon_result: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        self.binding_last_action = self._normalize_binding_last_action(self.binding_last_action)
        if self.daemon_result is not None and not isinstance(self.daemon_result, dict):
            raise TypeError("daemon_result must be dict or None")

    def ensure_daemon_result(self) -> dict[str, Any]:
        if self.daemon_result is None:
            self.daemon_result = {}
        elif not isinstance(self.daemon_result, dict):
            raise TypeError("daemon_result must be dict or None")
        return self.daemon_result

    def record_daemon_step(
        self,
        step: StudyRuntimeDaemonStep | str,
        payload: dict[str, Any],
    ) -> None:
        if not isinstance(payload, dict):
            raise TypeError("daemon step payload must be dict")
        resolved_step = self._normalize_daemon_step(step)
        self.ensure_daemon_result()[resolved_step.value] = dict(payload)

    def daemon_step(
        self,
        step: StudyRuntimeDaemonStep | str,
    ) -> dict[str, Any]:
        resolved_step = self._normalize_daemon_step(step)
        daemon_result = self.daemon_result
        if not isinstance(daemon_result, dict):
            return {}
        nested_payload = daemon_result.get(resolved_step.value)
        if isinstance(nested_payload, dict):
            return dict(nested_payload)
        if resolved_step in {StudyRuntimeDaemonStep.RESUME, StudyRuntimeDaemonStep.PAUSE} and not any(
            key in daemon_result for key in StudyRuntimeDaemonStep
        ):
            return dict(daemon_result)
        return {}

    def quest_status_for_step(
        self,
        step: StudyRuntimeDaemonStep | str,
        *,
        fallback: str,
    ) -> str:
        payload = self.daemon_step(step)
        snapshot = payload.get("snapshot")
        if isinstance(snapshot, dict):
            status = str(snapshot.get("status") or "").strip()
            if status:
                return status
        status = str(payload.get("status") or "").strip()
        return status or fallback

    def completion_snapshot_status(self, *, fallback: str) -> str:
        completion_sync = self.daemon_step(StudyRuntimeDaemonStep.COMPLETION_SYNC)
        try:
            return StudyCompletionSyncResult.from_payload(completion_sync).snapshot_status_or(fallback)
        except (TypeError, ValueError):
            return fallback

    def serialized_daemon_result(self) -> dict[str, Any] | None:
        daemon_result = self.daemon_result
        if daemon_result is None:
            return None
        if not isinstance(daemon_result, dict):
            raise TypeError("daemon_result must be dict or None")
        if self.binding_last_action == StudyRuntimeBindingAction.RESUME:
            return self.daemon_step(StudyRuntimeDaemonStep.RESUME)
        if self.binding_last_action == StudyRuntimeBindingAction.PAUSE:
            return self.daemon_step(StudyRuntimeDaemonStep.PAUSE)
        return dict(daemon_result)

    @staticmethod
    def _normalize_binding_last_action(
        value: StudyRuntimeBindingAction | str | None,
    ) -> StudyRuntimeBindingAction | None:
        if value is None or value == "":
            return None
        if isinstance(value, StudyRuntimeBindingAction):
            return value
        if not isinstance(value, str):
            raise TypeError("binding_last_action must be str or None")
        try:
            return StudyRuntimeBindingAction(value)
        except ValueError as exc:
            raise ValueError(f"unknown study runtime binding action: {value}") from exc

    @staticmethod
    def _normalize_daemon_step(
        value: StudyRuntimeDaemonStep | str,
    ) -> StudyRuntimeDaemonStep:
        if isinstance(value, StudyRuntimeDaemonStep):
            return value
        if not isinstance(value, str):
            raise TypeError("daemon step must be str")
        try:
            return StudyRuntimeDaemonStep(value)
        except ValueError as exc:
            raise ValueError(f"unknown study runtime daemon step: {value}") from exc


def _build_execution_context(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    study_root: Path,
    study_payload: dict[str, Any],
    source: str,
) -> StudyRuntimeExecutionContext:
    router = _router_module()
    execution = router._execution_payload(study_payload)
    quest_id = str(execution.get("quest_id") or study_id).strip() or study_id
    runtime_context = study_runtime_protocol.resolve_study_runtime_context(
        profile=profile,
        study_root=study_root,
        study_id=study_id,
        quest_id=quest_id,
    )
    completion_state = router._study_completion_state(study_root=study_root)
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
    router = _router_module()
    return router._build_create_payload(
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
    router = _router_module()
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
                router._prepare_runtime_overlay(
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
        should_prepare_existing_overlay = status.quest_status not in _LIVE_QUEST_STATUSES
        runtime_overlay_payload = (
            router._prepare_runtime_overlay(
                profile=context.profile,
                quest_root=context.quest_root,
            )
            if should_prepare_existing_overlay
            else {"audit": router._audit_runtime_overlay(profile=context.profile, quest_root=context.quest_root)}
        )
        runtime_overlay_result = StudyRuntimeOverlayResult.from_payload(runtime_overlay_payload)
        status.record_runtime_overlay(runtime_overlay_result)
        if should_prepare_existing_overlay and not runtime_overlay_result.audit.all_roots_ready:
            status.set_decision(
                StudyRuntimeDecision.BLOCKED,
                StudyRuntimeReason.RUNTIME_OVERLAY_NOT_READY,
            )
        if (
            status.quest_status in _LIVE_QUEST_STATUSES
            and status.decision
            in {
                StudyRuntimeDecision.NOOP,
                StudyRuntimeDecision.PAUSE,
                StudyRuntimeDecision.PAUSE_AND_COMPLETE,
            }
            and not runtime_overlay_result.audit.all_roots_ready
        ):
            status.set_decision(
                StudyRuntimeDecision.PAUSE,
                StudyRuntimeReason.RUNTIME_OVERLAY_AUDIT_FAILED_FOR_RUNNING_QUEST,
            )


def _execute_create_runtime_decision(
    *,
    status: StudyRuntimeStatus,
    context: StudyRuntimeExecutionContext,
) -> StudyRuntimeExecutionOutcome:
    router = _router_module()
    planned_decision = status.decision
    outcome = StudyRuntimeExecutionOutcome()
    create_payload = router._build_context_create_payload(context)
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
        slug=router._timestamp_slug(),
    )
    if partial_quest_recovery is not None:
        status.record_partial_quest_recovery(StudyRuntimePartialQuestRecoveryResult.from_payload(partial_quest_recovery))
    create_payload["auto_start"] = False
    if status.decision not in {StudyRuntimeDecision.CREATE_AND_START, StudyRuntimeDecision.CREATE_ONLY}:
        return outcome
    outcome.startup_payload_path = study_runtime_protocol.write_startup_payload(
        startup_payload_root=context.startup_payload_root,
        create_payload=create_payload,
        slug=router._timestamp_slug(),
    )
    try:
        create_result = router._create_quest(
            runtime_root=context.runtime_root,
            payload=create_payload,
        )
    except RuntimeError as exc:
        outcome.record_daemon_step(
            StudyRuntimeDaemonStep.CREATE,
            {
                "ok": False,
                "status": "unavailable",
                "error": str(exc),
            },
        )
        status.set_decision(
            StudyRuntimeDecision.BLOCKED,
            StudyRuntimeReason.CREATE_REQUEST_FAILED,
        )
        outcome.binding_last_action = StudyRuntimeBindingAction.BLOCKED
        return outcome
    outcome.record_daemon_step(StudyRuntimeDaemonStep.CREATE, create_result)
    status.update_quest_runtime(
        quest_id=create_payload["quest_id"],
        quest_root=context.quest_root,
        quest_exists=True,
        quest_status=outcome.quest_status_for_step(StudyRuntimeDaemonStep.CREATE, fallback="created"),
    )
    if context.profile.enable_medical_overlay:
        runtime_overlay_result = StudyRuntimeOverlayResult.from_payload(
            router._prepare_runtime_overlay(
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
    hydration_result, validation_result = router._run_startup_hydration(
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
        try:
            resume_result = router._resume_quest(
                runtime_root=context.runtime_root,
                quest_id=status.quest_id,
                source=context.source,
            )
        except RuntimeError as exc:
            outcome.record_daemon_step(
                StudyRuntimeDaemonStep.RESUME,
                {
                    "ok": False,
                    "status": "unavailable",
                    "error": str(exc),
                },
            )
            status.set_decision(
                StudyRuntimeDecision.BLOCKED,
                StudyRuntimeReason.RESUME_REQUEST_FAILED,
            )
            outcome.binding_last_action = StudyRuntimeBindingAction.BLOCKED
            return outcome
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
    router = _router_module()
    outcome = StudyRuntimeExecutionOutcome()
    create_payload = router._build_context_create_payload(context)
    startup_context_sync = router._sync_existing_quest_startup_context(
        runtime_root=context.runtime_root,
        quest_id=status.quest_id,
        create_payload=create_payload,
        execution=context.execution,
    )
    status.record_startup_context_sync(startup_context_sync)
    hydration_result, validation_result = router._run_startup_hydration(
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
    try:
        resume_result = router._resume_quest(
            runtime_root=context.runtime_root,
            quest_id=status.quest_id,
            source=context.source,
        )
    except RuntimeError as exc:
        outcome.record_daemon_step(
            StudyRuntimeDaemonStep.RESUME,
            {
                "ok": False,
                "status": "unavailable",
                "error": str(exc),
            },
        )
        status.set_decision(
            StudyRuntimeDecision.BLOCKED,
            StudyRuntimeReason.RESUME_REQUEST_FAILED,
        )
        outcome.binding_last_action = StudyRuntimeBindingAction.BLOCKED
        return outcome
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
    router = _router_module()
    outcome = StudyRuntimeExecutionOutcome(binding_last_action=StudyRuntimeBindingAction.BLOCKED)
    create_payload = router._build_context_create_payload(context)
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
    startup_context_sync = router._sync_existing_quest_startup_context(
        runtime_root=context.runtime_root,
        quest_id=status.quest_id,
        create_payload=create_payload,
        execution=context.execution,
    )
    status.record_startup_context_sync(startup_context_sync)
    hydration_result, validation_result = router._run_startup_hydration(
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
    router = _router_module()
    pause_result = router._pause_quest(
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
    router = _router_module()
    outcome = StudyRuntimeExecutionOutcome()
    if status.decision == StudyRuntimeDecision.PAUSE_AND_COMPLETE:
        pause_result = router._pause_quest(
            runtime_root=context.runtime_root,
            quest_id=status.quest_id,
            source=context.source,
        )
        outcome.record_daemon_step(StudyRuntimeDaemonStep.PAUSE, pause_result)
        status.update_quest_runtime(
            quest_status=outcome.quest_status_for_step(StudyRuntimeDaemonStep.PAUSE, fallback="paused"),
        )
    completion_sync = StudyCompletionSyncResult.from_payload(
        router._sync_study_completion(
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
    router = _router_module()
    if status.decision in {StudyRuntimeDecision.CREATE_AND_START, StudyRuntimeDecision.CREATE_ONLY}:
        return router._execute_create_runtime_decision(status=status, context=context)
    if status.decision == StudyRuntimeDecision.RESUME:
        return router._execute_resume_runtime_decision(status=status, context=context)
    if status.should_refresh_startup_hydration_while_blocked():
        return router._execute_blocked_refresh_runtime_decision(status=status, context=context)
    if status.decision == StudyRuntimeDecision.PAUSE:
        return router._execute_pause_runtime_decision(status=status, context=context)
    if status.decision in {StudyRuntimeDecision.SYNC_COMPLETION, StudyRuntimeDecision.PAUSE_AND_COMPLETE}:
        return router._execute_completion_runtime_decision(status=status, context=context)
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


def _runtime_escalation_trigger_source(reason: StudyRuntimeReason | None) -> str:
    if reason in {
        StudyRuntimeReason.STARTUP_BOUNDARY_NOT_READY_FOR_RESUME,
        StudyRuntimeReason.QUEST_PAUSED_BUT_AUTO_RESUME_DISABLED,
        StudyRuntimeReason.QUEST_INITIALIZED_BUT_AUTO_RESUME_DISABLED,
    }:
        return "startup_boundary_gate"
    if reason is StudyRuntimeReason.RUNTIME_REENTRY_NOT_READY_FOR_RESUME:
        return "runtime_reentry_gate"
    return "study_runtime_status"


def _runtime_escalation_recommended_actions(reason: StudyRuntimeReason | None) -> tuple[str, ...]:
    if reason is StudyRuntimeReason.RUNTIME_REENTRY_NOT_READY_FOR_RESUME:
        return ("refresh_startup_hydration", "controller_review_required")
    if reason in {
        StudyRuntimeReason.QUEST_PAUSED_BUT_AUTO_RESUME_DISABLED,
        StudyRuntimeReason.QUEST_INITIALIZED_BUT_AUTO_RESUME_DISABLED,
    }:
        return ("refresh_startup_hydration", "controller_review_required")
    return ("refresh_startup_hydration", "controller_review_required")


def _runtime_escalation_evidence_refs(status: StudyRuntimeStatus) -> tuple[str, ...]:
    evidence_refs: list[str] = []
    for key in ("startup_hydration", "startup_hydration_validation"):
        payload = status.extras.get(key)
        if not isinstance(payload, dict):
            continue
        report_path = str(payload.get("report_path") or "").strip()
        if report_path:
            evidence_refs.append(report_path)
    return tuple(evidence_refs)


def _maybe_emit_runtime_escalation_record(
    *,
    status: StudyRuntimeStatus,
    context: StudyRuntimeExecutionContext,
) -> None:
    if not status.should_refresh_startup_hydration_while_blocked():
        return
    reason = status.reason
    if reason is None:
        return
    emitted_at = _router_module()._utc_now()
    launch_report_path = str(context.launch_report_path)
    record = study_runtime_protocol.RuntimeEscalationRecord(
        schema_version=1,
        record_id=f"runtime-escalation::{context.study_id}::{status.quest_id}::{reason.value}::{emitted_at}",
        study_id=context.study_id,
        quest_id=status.quest_id,
        emitted_at=emitted_at,
        trigger=study_runtime_protocol.RuntimeEscalationTrigger(
            trigger_id=reason.value,
            source=_runtime_escalation_trigger_source(reason),
        ),
        scope="quest",
        severity="quest",
        reason=reason.value,
        recommended_actions=_runtime_escalation_recommended_actions(reason),
        evidence_refs=_runtime_escalation_evidence_refs(status),
        runtime_context_refs={
            "launch_report_path": launch_report_path,
        },
        summary_ref=launch_report_path,
        artifact_path=None,
    )
    written_record = study_runtime_protocol.write_runtime_escalation_record(
        quest_root=context.quest_root,
        record=record,
    )
    status.record_runtime_escalation_ref(written_record.ref())


def _persist_runtime_artifacts(
    *,
    status: StudyRuntimeStatus,
    context: StudyRuntimeExecutionContext,
    outcome: StudyRuntimeExecutionOutcome,
    force: bool,
    source: str,
) -> None:
    router = _router_module()
    artifact_paths = router.study_runtime_protocol.persist_runtime_artifacts(
        runtime_binding_path=context.runtime_binding_path,
        launch_report_path=context.launch_report_path,
        runtime_root=context.runtime_root,
        study_id=context.study_id,
        study_root=context.study_root,
        quest_id=status.quest_id.strip() or None,
        last_action=outcome.binding_last_action.value if outcome.binding_last_action is not None else None,
        status=status.to_dict(),
        source=source,
        force=force,
        startup_payload_path=outcome.startup_payload_path,
        daemon_result=outcome.serialized_daemon_result(),
        recorded_at=router._utc_now(),
    )
    status.record_runtime_artifacts(
        runtime_binding_path=artifact_paths.runtime_binding_path,
        launch_report_path=artifact_paths.launch_report_path,
        startup_payload_path=artifact_paths.startup_payload_path,
    )
    _maybe_emit_runtime_escalation_record(status=status, context=context)
    if "runtime_escalation_ref" in status.extras:
        router.study_runtime_protocol.write_launch_report(
            launch_report_path=context.launch_report_path,
            status=status.to_dict(),
            source=source,
            force=force,
            startup_payload_path=outcome.startup_payload_path,
            daemon_result=outcome.serialized_daemon_result(),
            recorded_at=router._utc_now(),
        )
