from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from pathlib import Path
from typing import Any
from urllib.parse import quote

from med_autoscience import study_runtime_analysis_bundle as analysis_bundle_controller
from med_autoscience.controllers import runtime_supervision as runtime_supervision_controller
from med_autoscience.profiles import WorkspaceProfile
from med_autoscience.runtime_backend import ManagedRuntimeBackend
from med_autoscience.runtime_protocol import (
    quest_state,
    study_runtime as study_runtime_protocol,
    user_message,
)
from med_autoscience.study_completion import StudyCompletionState

from .study_runtime_transport import _get_quest_session
from .study_runtime_status import (
    StudyCompletionSyncResult,
    StudyRuntimeAutonomousRuntimeNotice,
    StudyRuntimeAnalysisBundleResult,
    StudyRuntimeAuditStatus,
    StudyRuntimeBindingAction,
    StudyRuntimeDaemonStep,
    StudyRuntimeDecision,
    StudyRuntimeOverlayResult,
    StudyRuntimePartialQuestRecoveryResult,
    StudyRuntimeQuestStatus,
    StudyRuntimeReason,
    StudyRuntimeStatus,
    _LIVE_QUEST_STATUSES,
)

__all__ = [
    "StudyRuntimeExecutionContext",
    "StudyRuntimeExecutionOutcome",
    "_build_context_create_payload",
    "_build_execution_context",
    "_enable_explicit_stopped_relaunch_if_requested",
    "_execute_blocked_refresh_runtime_decision",
    "_execute_completion_runtime_decision",
    "_execute_create_runtime_decision",
    "_execute_pause_runtime_decision",
    "_execute_resume_runtime_decision",
    "_execute_runtime_decision",
    "_persist_runtime_artifacts",
    "_record_autonomous_runtime_notice_if_required",
    "_run_runtime_preflight",
]

_LIVE_CONTROLLER_REROUTE_FORCE_RESTART_AUTO_TURN_THRESHOLD = 3
_LIVE_CONTROLLER_REROUTE_REQUIRED_ACTION_BY_REASON = {
    StudyRuntimeReason.QUEST_DRIFTING_INTO_WRITE_WITHOUT_GATE_APPROVAL: "return_to_publishability_gate",
    StudyRuntimeReason.QUEST_STALE_DECISION_AFTER_WRITE_STAGE_READY: "continue_write_stage",
}


def _router_module():
    return import_module("med_autoscience.controllers.study_runtime_router")


def _should_run_startup_hydration_for_resume(*, status: StudyRuntimeStatus) -> bool:
    return status.runtime_reentry_gate_result.require_startup_hydration


def _controller_owned_interaction_reply_message(*, status: StudyRuntimeStatus) -> str | None:
    if status.reason is StudyRuntimeReason.QUEST_DRIFTING_INTO_WRITE_WITHOUT_GATE_APPROVAL:
        return (
            "MAS publication gate 尚未放行写作。请停止当前 manuscript / finalize 漂移，"
            "回到 publishability blockers 与科学锚点映射，清除门控后再继续写作或申请 completion。"
        )
    if status.reason is StudyRuntimeReason.QUEST_STALE_DECISION_AFTER_WRITE_STAGE_READY:
        return (
            "MAS publication gate 已放行写作。请结束旧的 decision 续跑点，"
            "回到当前 manuscript 主线，继续 write stage 并更新 results / figures / tables。"
        )
    pending_payload = status.extras.get("pending_user_interaction")
    arbitration_payload = status.extras.get("interaction_arbitration")
    if not isinstance(pending_payload, dict) or not isinstance(arbitration_payload, dict):
        return None
    pending_interaction_id = str(pending_payload.get("interaction_id") or "").strip()
    if not pending_interaction_id or not bool(pending_payload.get("relay_required")):
        return None
    if bool(arbitration_payload.get("requires_user_input")):
        return None
    if str(arbitration_payload.get("action") or "").strip() != StudyRuntimeDecision.RESUME.value:
        return None

    classification = str(arbitration_payload.get("classification") or "").strip()
    if classification == "premature_completion_request":
        return (
            "暂不结题。MAS publication gate 尚未 clear，请继续处理当前论文的 publishability blockers；"
            "等 publication gate 清除后，再重新申请 completion。"
        )
    if classification == "submission_metadata_only":
        return (
            "不要因 submission metadata 暂缺而阻塞当前 quest。请继续推进论文主稿与科学交付，"
            "并把缺失的投稿元数据保留在待补清单中。"
        )
    if classification == "invalid_blocking":
        return "当前交互不应阻塞 MAS 托管流程。请不要等待用户输入，按现有 study contract 继续自主推进下一步。"
    return None


def _relay_controller_owned_runtime_reply_if_required(
    *,
    status: StudyRuntimeStatus,
    context: StudyRuntimeExecutionContext,
) -> dict[str, Any] | None:
    message = _controller_owned_interaction_reply_message(status=status)
    if message is None:
        return None
    pending_payload = status.extras.get("pending_user_interaction")
    runtime_state = quest_state.load_runtime_state(context.quest_root)
    runtime_state["quest_id"] = status.quest_id
    if isinstance(pending_payload, dict):
        runtime_state.setdefault(
            "active_interaction_id",
            str(pending_payload.get("interaction_id") or "").strip() or None,
        )
    record = user_message.enqueue_user_message(
        quest_root=context.quest_root,
        runtime_state=runtime_state,
        message=message,
        source=context.source,
    )
    status.extras["controller_owned_runtime_reply"] = {
        "message_id": record.get("message_id"),
        "reply_to_interaction_id": record.get("reply_to_interaction_id"),
        "content": record.get("content"),
        "source": record.get("source"),
    }
    return record


def _should_skip_redundant_resume_for_live_controller_reroute(*, status: StudyRuntimeStatus) -> bool:
    if status.reason not in _LIVE_CONTROLLER_REROUTE_REQUIRED_ACTION_BY_REASON:
        return False
    payload = status.extras.get("runtime_liveness_audit")
    if not isinstance(payload, dict):
        return False
    runtime_audit = payload.get("runtime_audit")
    resolved_active_run_id = str(payload.get("active_run_id") or "").strip() or None
    if resolved_active_run_id is None and isinstance(runtime_audit, dict):
        resolved_active_run_id = str(runtime_audit.get("active_run_id") or "").strip() or None
    if resolved_active_run_id is None:
        return False
    if str(payload.get("status") or "").strip().lower() != StudyRuntimeAuditStatus.LIVE.value:
        return False
    return isinstance(runtime_audit, dict) and runtime_audit.get("worker_running") is True


def _should_force_restart_for_live_controller_reroute(
    *,
    status: StudyRuntimeStatus,
    context: StudyRuntimeExecutionContext,
) -> bool:
    if not _should_skip_redundant_resume_for_live_controller_reroute(status=status):
        return False
    publication_supervisor_state = status.extras.get("publication_supervisor_state")
    if not isinstance(publication_supervisor_state, dict):
        return False
    current_required_action = str(publication_supervisor_state.get("current_required_action") or "").strip()
    expected_action = _LIVE_CONTROLLER_REROUTE_REQUIRED_ACTION_BY_REASON.get(status.reason)
    if expected_action is None or current_required_action != expected_action:
        return False
    runtime_state = quest_state.load_runtime_state(context.quest_root)
    if int(runtime_state.get("pending_user_message_count") or 0) > 0:
        return False
    continuation_anchor = str(runtime_state.get("continuation_anchor") or "").strip()
    continuation_reason = str(runtime_state.get("continuation_reason") or "").strip()
    if continuation_anchor != "decision" or not continuation_reason.startswith("decision:"):
        return False
    same_fingerprint_auto_turn_count = int(runtime_state.get("same_fingerprint_auto_turn_count") or 0)
    return same_fingerprint_auto_turn_count >= _LIVE_CONTROLLER_REROUTE_FORCE_RESTART_AUTO_TURN_THRESHOLD


@dataclass(frozen=True)
class StudyRuntimeExecutionContext:
    profile: WorkspaceProfile
    study_id: str
    study_root: Path
    study_payload: dict[str, Any]
    execution: dict[str, Any]
    quest_id: str
    runtime_context: study_runtime_protocol.StudyRuntimeContext
    runtime_backend: ManagedRuntimeBackend
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

    def active_run_id(self) -> str | None:
        daemon_result = self.daemon_result
        if not isinstance(daemon_result, dict):
            return None
        for step in (StudyRuntimeDaemonStep.RESUME, StudyRuntimeDaemonStep.CREATE):
            payload = self.daemon_step(step)
            snapshot = payload.get("snapshot")
            snapshot_run_id = str(snapshot.get("active_run_id") or "").strip() if isinstance(snapshot, dict) else ""
            payload_run_id = str(payload.get("active_run_id") or "").strip()
            if snapshot_run_id:
                return snapshot_run_id
            if payload_run_id:
                return payload_run_id
        return None

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
    execution = router._execution_payload(study_payload, profile=profile)
    quest_id = str(execution.get("quest_id") or study_id).strip() or study_id
    runtime_context = study_runtime_protocol.resolve_study_runtime_context(
        profile=profile,
        study_root=study_root,
        study_id=study_id,
        quest_id=quest_id,
    )
    runtime_backend = router._managed_runtime_backend_for_execution(
        execution,
        profile=profile,
        runtime_root=runtime_context.runtime_root,
    ) or router._default_managed_runtime_backend()
    completion_state = router._study_completion_state(study_root=study_root)
    return StudyRuntimeExecutionContext(
        profile=profile,
        study_id=study_id,
        study_root=study_root,
        study_payload=study_payload,
        execution=execution,
        quest_id=quest_id,
        runtime_context=runtime_context,
        runtime_backend=runtime_backend,
        completion_state=completion_state,
        source=source,
    )


def _enable_explicit_stopped_relaunch_if_requested(
    *,
    status: StudyRuntimeStatus,
) -> None:
    if (
        status.decision is not StudyRuntimeDecision.BLOCKED
        or status.reason is not StudyRuntimeReason.QUEST_STOPPED_REQUIRES_EXPLICIT_RERUN
        or status.quest_status is not StudyRuntimeQuestStatus.STOPPED
    ):
        return
    if not status.startup_boundary_allows_compute_stage:
        status.set_decision(
            StudyRuntimeDecision.BLOCKED,
            StudyRuntimeReason.STARTUP_BOUNDARY_NOT_READY_FOR_RESUME,
        )
        return
    if not status.runtime_reentry_allows_runtime_entry:
        status.set_decision(
            StudyRuntimeDecision.BLOCKED,
            StudyRuntimeReason.RUNTIME_REENTRY_NOT_READY_FOR_RESUME,
        )
        return
    status.set_decision(
        StudyRuntimeDecision.RELAUNCH_STOPPED,
        StudyRuntimeReason.QUEST_STOPPED_EXPLICIT_RELAUNCH_REQUESTED,
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
        ):
            if not runtime_overlay_result.audit.all_roots_ready:
                runtime_overlay_result = StudyRuntimeOverlayResult.from_payload(
                    router._prepare_runtime_overlay(
                        profile=context.profile,
                        quest_root=context.quest_root,
                    )
                )
                status.record_runtime_overlay(runtime_overlay_result)
            if not runtime_overlay_result.audit.all_roots_ready:
                status.set_decision(
                    StudyRuntimeDecision.PAUSE,
                    StudyRuntimeReason.RUNTIME_OVERLAY_AUDIT_FAILED_FOR_RUNNING_QUEST,
                )


def _resume_postcondition_payload(
    *,
    status: StudyRuntimeStatus,
    resume_result: dict[str, Any],
) -> dict[str, Any]:
    snapshot = dict(resume_result.get("snapshot") or {}) if isinstance(resume_result.get("snapshot"), dict) else {}
    interaction_arbitration = status.extras.get("interaction_arbitration")
    snapshot_status = str(snapshot.get("status") or resume_result.get("status") or "").strip() or None
    active_run_id = str(snapshot.get("active_run_id") or resume_result.get("active_run_id") or "").strip() or None
    scheduled = bool(resume_result.get("scheduled"))
    started = bool(resume_result.get("started"))
    queued = bool(resume_result.get("queued"))
    effective = (
        active_run_id is not None
        or snapshot_status in {"running", "retrying", "active"}
    )
    failure_mode = None
    if not effective:
        failure_mode = "no_effect"
        if isinstance(interaction_arbitration, dict):
            action = str(interaction_arbitration.get("action") or "").strip()
            if snapshot_status == "waiting_for_user" and action == StudyRuntimeDecision.RESUME.value:
                failure_mode = "waiting_state_preserved"
    return {
        "effective": effective,
        "failure_mode": failure_mode,
        "snapshot_status": snapshot_status,
        "active_run_id": active_run_id,
        "scheduled": scheduled,
        "started": started,
        "queued": queued,
    }


def _apply_resume_postcondition(
    *,
    status: StudyRuntimeStatus,
    outcome: StudyRuntimeExecutionOutcome,
) -> bool:
    resume_result = outcome.daemon_step(StudyRuntimeDaemonStep.RESUME)
    payload = _resume_postcondition_payload(status=status, resume_result=resume_result)
    status._record_dict_extra("resume_postcondition", payload)
    if payload["effective"]:
        return True
    status.set_decision(
        StudyRuntimeDecision.BLOCKED,
        StudyRuntimeReason.RESUME_REQUEST_FAILED,
    )
    outcome.binding_last_action = StudyRuntimeBindingAction.BLOCKED
    return False


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
            runtime_backend=context.runtime_backend,
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
        study_root=context.study_root,
        workspace_root=context.profile.workspace_root,
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
                runtime_backend=context.runtime_backend,
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
        if not _apply_resume_postcondition(status=status, outcome=outcome):
            return outcome
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
    if _should_run_startup_hydration_for_resume(status=status):
        hydration_result, validation_result = router._run_startup_hydration(
            quest_root=context.quest_root,
            create_payload=create_payload,
            study_root=context.study_root,
            workspace_root=context.profile.workspace_root,
        )
        status.record_startup_hydration(hydration_result, validation_result)
        if validation_result.status is not study_runtime_protocol.StartupHydrationValidationStatus.CLEAR:
            status.set_decision(
                StudyRuntimeDecision.BLOCKED,
                StudyRuntimeReason.HYDRATION_VALIDATION_FAILED,
            )
            outcome.binding_last_action = StudyRuntimeBindingAction.BLOCKED
            return outcome
    force_live_controller_reroute_restart = _should_force_restart_for_live_controller_reroute(
        status=status,
        context=context,
    )
    if force_live_controller_reroute_restart:
        pause_result = router._pause_quest(
            runtime_root=context.runtime_root,
            quest_id=status.quest_id,
            source=context.source,
            runtime_backend=context.runtime_backend,
        )
        outcome.record_daemon_step(StudyRuntimeDaemonStep.PAUSE, pause_result)
        status.update_quest_runtime(
            quest_status=outcome.quest_status_for_step(StudyRuntimeDaemonStep.PAUSE, fallback="paused"),
        )
        status.extras["controller_reroute_restart"] = {
            "forced": True,
            "threshold": _LIVE_CONTROLLER_REROUTE_FORCE_RESTART_AUTO_TURN_THRESHOLD,
            "same_fingerprint_auto_turn_count": int(
                quest_state.load_runtime_state(context.quest_root).get("same_fingerprint_auto_turn_count") or 0
            ),
        }
    _relay_controller_owned_runtime_reply_if_required(status=status, context=context)
    if _should_skip_redundant_resume_for_live_controller_reroute(status=status) and not force_live_controller_reroute_restart:
        outcome.binding_last_action = StudyRuntimeBindingAction.NOOP
        return outcome
    try:
        resume_result = router._resume_quest(
            runtime_root=context.runtime_root,
            quest_id=status.quest_id,
            source=context.source,
            runtime_backend=context.runtime_backend,
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
    if not _apply_resume_postcondition(status=status, outcome=outcome):
        return outcome
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
        study_root=context.study_root,
        workspace_root=context.profile.workspace_root,
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
        runtime_backend=context.runtime_backend,
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
            runtime_backend=context.runtime_backend,
        )
        outcome.record_daemon_step(StudyRuntimeDaemonStep.PAUSE, pause_result)
        status.update_quest_runtime(
            quest_status=outcome.quest_status_for_step(StudyRuntimeDaemonStep.PAUSE, fallback="paused"),
        )
    completion_sync = StudyCompletionSyncResult.from_payload(
        router._sync_study_completion(
            runtime_root=context.runtime_root,
            quest_id=status.quest_id,
            completion_state=context.completion_state,
            source=context.source,
            runtime_backend=context.runtime_backend,
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
    if status.decision == StudyRuntimeDecision.RELAUNCH_STOPPED:
        outcome = router._execute_resume_runtime_decision(status=status, context=context)
        if outcome.binding_last_action is StudyRuntimeBindingAction.RESUME:
            outcome.binding_last_action = StudyRuntimeBindingAction.RELAUNCH_STOPPED
        return outcome
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


def _managed_runtime_notice_reason(
    *,
    binding_last_action: StudyRuntimeBindingAction | None,
    strict_live: bool,
) -> str:
    if not strict_live:
        if binding_last_action in {
            StudyRuntimeBindingAction.CREATE_AND_START,
            StudyRuntimeBindingAction.RESUME,
            StudyRuntimeBindingAction.RELAUNCH_STOPPED,
        }:
            return "managed_runtime_recovery_requested"
        return "managed_runtime_degraded"
    if binding_last_action is StudyRuntimeBindingAction.CREATE_AND_START:
        return "managed_runtime_started"
    if binding_last_action is StudyRuntimeBindingAction.RESUME:
        return "managed_runtime_resumed"
    if binding_last_action is StudyRuntimeBindingAction.RELAUNCH_STOPPED:
        return "managed_runtime_relaunched"
    return "detected_existing_live_managed_runtime"


def _should_record_autonomous_runtime_notice(status: StudyRuntimeStatus) -> bool:
    return (
        _router_module()._managed_runtime_backend_for_execution(status.execution) is not None
        and str(status.execution.get("auto_entry") or "").strip() == "on_managed_research_intent"
        and status.quest_exists
        and status.quest_status in _LIVE_QUEST_STATUSES
    )


def _runtime_audit_worker_running(payload: dict[str, Any]) -> bool:
    runtime_audit = payload.get("runtime_audit")
    if isinstance(runtime_audit, dict):
        return runtime_audit.get("worker_running") is True
    return payload.get("worker_running") is True


def _is_strictly_live_runtime_notice(
    *,
    status: StudyRuntimeStatus,
    active_run_id: str | None,
) -> bool:
    if active_run_id is None:
        return False
    payload = status.extras.get("runtime_liveness_audit")
    if not isinstance(payload, dict):
        return False
    audit_status = str(payload.get("status") or "").strip().lower()
    return audit_status == StudyRuntimeAuditStatus.LIVE.value and _runtime_audit_worker_running(payload)


def _record_autonomous_runtime_notice_if_required(
    *,
    status: StudyRuntimeStatus,
    runtime_root: Path,
    launch_report_path: Path,
    binding_last_action: StudyRuntimeBindingAction | None = None,
    active_run_id: str | None = None,
) -> None:
    if not _should_record_autonomous_runtime_notice(status):
        return
    router = _router_module()
    managed_runtime_backend = router._managed_runtime_backend_for_execution(status.execution)
    if managed_runtime_backend is None:
        return
    browser_url: str | None = None
    monitoring_error: str | None = None
    try:
        browser_url = managed_runtime_backend.resolve_daemon_url(runtime_root=runtime_root)
    except (RuntimeError, OSError, ValueError) as exc:
        monitoring_error = str(exc)
    resolved_active_run_id = str(active_run_id or "").strip() or None
    if resolved_active_run_id is None:
        payload = status.extras.get("runtime_liveness_audit")
        if isinstance(payload, dict):
            resolved_active_run_id = str(payload.get("active_run_id") or "").strip() or None
            if resolved_active_run_id is None:
                runtime_audit = payload.get("runtime_audit")
                if isinstance(runtime_audit, dict):
                    resolved_active_run_id = str(runtime_audit.get("active_run_id") or "").strip() or None
    strict_live = _is_strictly_live_runtime_notice(
        status=status,
        active_run_id=resolved_active_run_id,
    )
    if resolved_active_run_id is None and not strict_live:
        return
    quest_status = status.quest_status.value if status.quest_status is not None else "unknown"
    encoded_quest_id = quote(status.quest_id, safe="")
    status.record_autonomous_runtime_notice(
        StudyRuntimeAutonomousRuntimeNotice(
            required=True,
            notice_key=f"quest:{status.quest_id}:{resolved_active_run_id or quest_status}",
            notification_reason=_managed_runtime_notice_reason(
                binding_last_action=binding_last_action,
                strict_live=strict_live,
            ),
            quest_id=status.quest_id,
            quest_status=quest_status,
            active_run_id=resolved_active_run_id,
            browser_url=browser_url,
            quest_api_url=f"{browser_url}/api/quests/{encoded_quest_id}" if browser_url is not None else None,
            quest_session_api_url=(
                f"{browser_url}/api/quests/{encoded_quest_id}/session" if browser_url is not None else None
            ),
            monitoring_available=browser_url is not None,
            monitoring_error=monitoring_error,
            launch_report_path=str(launch_report_path),
        )
    )


def _runtime_event_status_snapshot(status: StudyRuntimeStatus) -> dict[str, object]:
    runtime_liveness_audit = (
        dict(status.extras.get("runtime_liveness_audit"))
        if isinstance(status.extras.get("runtime_liveness_audit"), dict)
        else {}
    )
    runtime_audit = (
        dict(runtime_liveness_audit.get("runtime_audit"))
        if isinstance(runtime_liveness_audit.get("runtime_audit"), dict)
        else {}
    )
    continuation_state = status.extras.get("continuation_state")
    supervisor_tick_audit = status.extras.get("supervisor_tick_audit")
    return {
        "quest_status": status.quest_status.value if status.quest_status is not None else None,
        "decision": status.decision.value if status.decision is not None else None,
        "reason": status.reason.value if status.reason is not None else None,
        "active_run_id": (
            str(runtime_liveness_audit.get("active_run_id") or runtime_audit.get("active_run_id") or "").strip() or None
        ),
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
        "controller_owned_finalize_parking": False,
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


def _post_transition_quest_status(
    *,
    status: StudyRuntimeStatus,
    outcome: StudyRuntimeExecutionOutcome,
) -> StudyRuntimeQuestStatus | None:
    if outcome.binding_last_action is StudyRuntimeBindingAction.CREATE_AND_START:
        return StudyRuntimeQuestStatus(
            outcome.quest_status_for_step(StudyRuntimeDaemonStep.CREATE, fallback="created")
        )
    if outcome.binding_last_action in {
        StudyRuntimeBindingAction.RESUME,
        StudyRuntimeBindingAction.RELAUNCH_STOPPED,
    }:
        return StudyRuntimeQuestStatus(
            outcome.quest_status_for_step(StudyRuntimeDaemonStep.RESUME, fallback="running")
        )
    if outcome.binding_last_action is StudyRuntimeBindingAction.PAUSE:
        return StudyRuntimeQuestStatus(
            outcome.quest_status_for_step(StudyRuntimeDaemonStep.PAUSE, fallback="paused")
        )
    if outcome.binding_last_action is StudyRuntimeBindingAction.COMPLETED:
        return StudyRuntimeQuestStatus(outcome.completion_snapshot_status(fallback="completed"))
    return status.quest_status


def _record_transition_runtime_event(
    *,
    status: StudyRuntimeStatus,
    context: StudyRuntimeExecutionContext,
    outcome: StudyRuntimeExecutionOutcome,
) -> None:
    if outcome.binding_last_action not in {
        StudyRuntimeBindingAction.CREATE_AND_START,
        StudyRuntimeBindingAction.RESUME,
        StudyRuntimeBindingAction.RELAUNCH_STOPPED,
        StudyRuntimeBindingAction.PAUSE,
        StudyRuntimeBindingAction.COMPLETED,
    }:
        return
    execution = status.execution
    if (
        _router_module()._managed_runtime_backend_for_execution(execution) is None
        or str(execution.get("auto_entry") or "").strip() != "on_managed_research_intent"
        or not status.quest_exists
    ):
        status.extras.pop("runtime_event_ref", None)
        status.extras.pop("runtime_event", None)
        return
    post_transition_status = _post_transition_quest_status(status=status, outcome=outcome)
    status.update_quest_runtime(quest_status=post_transition_status)
    try:
        session_payload = _get_quest_session(
            runtime_root=context.runtime_root,
            quest_id=status.quest_id,
            runtime_backend=context.runtime_backend,
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
    recorded_at = router._utc_now()
    _record_transition_runtime_event(status=status, context=context, outcome=outcome)
    _record_autonomous_runtime_notice_if_required(
        status=status,
        runtime_root=context.runtime_root,
        launch_report_path=context.launch_report_path,
        binding_last_action=outcome.binding_last_action,
        active_run_id=outcome.active_run_id(),
    )
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
        recorded_at=recorded_at,
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
            recorded_at=recorded_at,
        )
    runtime_supervision_controller.materialize_runtime_supervision(
        study_root=context.study_root,
        status_payload=status.to_dict(),
        recorded_at=recorded_at,
        apply=True,
    )
