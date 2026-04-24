from __future__ import annotations

from collections.abc import Iterator, MutableMapping
from dataclasses import dataclass, field
from enum import StrEnum
from os import PathLike
from pathlib import Path
from typing import Any

from med_autoscience.runtime_protocol import study_runtime as study_runtime_protocol
from med_autoscience.study_completion import (
    StudyCompletionState,
    StudyCompletionStateStatus,
)


__all__ = [
    "StudyCompletionSyncResult",
    "StudyRuntimeAutonomousRuntimeNotice",
    "StudyRuntimeAnalysisBundleResult",
    "StudyRuntimeAuditRecord",
    "StudyRuntimeAuditStatus",
    "StudyRuntimeBindingAction",
    "StudyRuntimeContinuationState",
    "StudyRuntimeDaemonStep",
    "StudyRuntimeDecision",
    "StudyRuntimeExecutionOwnerGuard",
    "StudyRuntimeInteractionArbitration",
    "StudyRuntimeOverlayAudit",
    "StudyRuntimeOverlayResult",
    "StudyRuntimePendingUserInteraction",
    "StudyRuntimePartialQuestRecoveryResult",
    "StudyRuntimeProgressProjection",
    "StudyRuntimePublicationSupervisorState",
    "StudyRuntimeQuestStatus",
    "StudyRuntimeReason",
    "StudyRuntimeReentryGate",
    "StudyRuntimeSummaryAlignment",
    "StudyRuntimeStartupBoundaryGate",
    "StudyRuntimeStartupContextSyncResult",
    "StudyRuntimeStartupDataReadinessReport",
    "StudyRuntimeStatus",
    "StudyRuntimeWorkspaceContractsSummary",
]

_UNSET = object()


def _absent_study_completion_state() -> StudyCompletionState:
    return StudyCompletionState(
        status=StudyCompletionStateStatus.ABSENT,
        contract=None,
        errors=(),
    )


class StudyRuntimeDecision(StrEnum):
    LIGHTWEIGHT = "lightweight"
    BLOCKED = "blocked"
    CREATE_AND_START = "create_and_start"
    CREATE_ONLY = "create_only"
    RESUME = "resume"
    RELAUNCH_STOPPED = "relaunch_stopped"
    PAUSE = "pause"
    NOOP = "noop"
    SYNC_COMPLETION = "sync_completion"
    PAUSE_AND_COMPLETE = "pause_and_complete"
    COMPLETED = "completed"


class StudyRuntimeReason(StrEnum):
    STUDY_EXECUTION_NOT_MANAGED_RUNTIME_BACKEND = "study_execution_not_managed_runtime_backend"
    STUDY_EXECUTION_RUNTIME_BACKEND_UNBOUND = "study_execution_runtime_backend_unbound"
    STUDY_EXECUTION_NOT_MANAGED = "study_execution_not_managed"
    ENTRY_MODE_NOT_MANAGED = "entry_mode_not_managed"
    STUDY_CHARTER_MISSING = "study_charter_missing"
    STUDY_CHARTER_INVALID = "study_charter_invalid"
    STUDY_COMPLETION_CONTRACT_NOT_READY = "study_completion_contract_not_ready"
    STUDY_COMPLETION_DECLARED_WITHOUT_MANAGED_QUEST = "study_completion_declared_without_managed_quest"
    QUEST_ALREADY_COMPLETED = "quest_already_completed"
    STUDY_COMPLETION_LIVE_RUNTIME_AUDIT_FAILED = "study_completion_live_runtime_audit_failed"
    STUDY_COMPLETION_READY = "study_completion_ready"
    STUDY_COMPLETION_PUBLISHABILITY_GATE_BLOCKED = "study_completion_publishability_gate_blocked"
    STUDY_COMPLETION_REQUIRES_PROGRAM_HUMAN_CONFIRMATION = (
        "study_completion_requires_program_human_confirmation"
    )
    WORKSPACE_CONTRACT_NOT_READY = "workspace_contract_not_ready"
    STUDY_DATA_READINESS_BLOCKED = "study_data_readiness_blocked"
    STARTUP_CONTRACT_RESOLUTION_FAILED = "startup_contract_resolution_failed"
    QUEST_MISSING = "quest_missing"
    CREATE_REQUEST_FAILED = "create_request_failed"
    RUNTIME_REENTRY_NOT_READY_FOR_AUTO_START = "runtime_reentry_not_ready_for_auto_start"
    STARTUP_BOUNDARY_NOT_READY_FOR_AUTO_START = "startup_boundary_not_ready_for_auto_start"
    RUNNING_QUEST_LIVE_SESSION_AUDIT_FAILED = "running_quest_live_session_audit_failed"
    STARTUP_BOUNDARY_NOT_READY_FOR_RUNNING_QUEST = "startup_boundary_not_ready_for_running_quest"
    RUNTIME_REENTRY_NOT_READY_FOR_RUNNING_QUEST = "runtime_reentry_not_ready_for_running_quest"
    QUEST_ALREADY_RUNNING = "quest_already_running"
    STARTUP_BOUNDARY_NOT_READY_FOR_RESUME = "startup_boundary_not_ready_for_resume"
    RUNTIME_REENTRY_NOT_READY_FOR_RESUME = "runtime_reentry_not_ready_for_resume"
    QUEST_MARKED_RUNNING_BUT_NO_LIVE_SESSION = "quest_marked_running_but_no_live_session"
    QUEST_PARKED_ON_UNCHANGED_FINALIZE_STATE = "quest_parked_on_unchanged_finalize_state"
    QUEST_DRIFTING_INTO_WRITE_WITHOUT_GATE_APPROVAL = "quest_drifting_into_write_without_gate_approval"
    QUEST_STALE_DECISION_AFTER_WRITE_STAGE_READY = "quest_stale_decision_after_write_stage_ready"
    RESUME_REQUEST_FAILED = "resume_request_failed"
    QUEST_MARKED_RUNNING_BUT_AUTO_RESUME_DISABLED = "quest_marked_running_but_auto_resume_disabled"
    QUEST_WAITING_FOR_USER = "quest_waiting_for_user"
    QUEST_WAITING_ON_INVALID_BLOCKING = "quest_waiting_on_invalid_blocking"
    QUEST_COMPLETION_REQUESTED_BEFORE_PUBLICATION_GATE_CLEAR = (
        "quest_completion_requested_before_publication_gate_clear"
    )
    QUEST_WAITING_FOR_EXTERNAL_INPUT = "quest_waiting_for_external_input"
    QUEST_WAITING_FOR_SUBMISSION_METADATA = "quest_waiting_for_submission_metadata"
    QUEST_WAITING_FOR_SUBMISSION_METADATA_BUT_AUTO_RESUME_DISABLED = (
        "quest_waiting_for_submission_metadata_but_auto_resume_disabled"
    )
    QUEST_STOPPED_BY_CONTROLLER_GUARD = "quest_stopped_by_controller_guard"
    QUEST_PAUSED = "quest_paused"
    QUEST_STOPPED = "quest_stopped"
    QUEST_STOPPED_REQUIRES_EXPLICIT_RERUN = "quest_stopped_requires_explicit_rerun"
    QUEST_STOPPED_EXPLICIT_RELAUNCH_REQUESTED = "quest_stopped_explicit_relaunch_requested"
    QUEST_INITIALIZED_WAITING_TO_START = "quest_initialized_waiting_to_start"
    QUEST_PAUSED_BUT_AUTO_RESUME_DISABLED = "quest_paused_but_auto_resume_disabled"
    QUEST_STOPPED_BUT_AUTO_RESUME_DISABLED = "quest_stopped_but_auto_resume_disabled"
    QUEST_INITIALIZED_BUT_AUTO_RESUME_DISABLED = "quest_initialized_but_auto_resume_disabled"
    QUEST_EXISTS_WITH_NON_RESUMABLE_STATE = "quest_exists_with_non_resumable_state"
    STUDY_RUNTIME_ANALYSIS_BUNDLE_NOT_READY = "study_runtime_analysis_bundle_not_ready"
    MANAGED_SKILL_AUDIT_NOT_AVAILABLE = "managed_skill_audit_not_available"
    RUNTIME_OVERLAY_NOT_READY = "runtime_overlay_not_ready"
    RUNTIME_OVERLAY_AUDIT_FAILED_FOR_RUNNING_QUEST = "runtime_overlay_audit_failed_for_running_quest"
    HYDRATION_VALIDATION_FAILED = "hydration_validation_failed"
    STUDY_COMPLETION_SYNCED = "study_completion_synced"


class StudyRuntimeQuestStatus(StrEnum):
    CREATED = "created"
    IDLE = "idle"
    PAUSED = "paused"
    STOPPED = "stopped"
    WAITING_FOR_USER = "waiting_for_user"
    RUNNING = "running"
    RETRYING = "retrying"
    ACTIVE = "active"
    COMPLETED = "completed"


class StudyRuntimeBindingAction(StrEnum):
    BLOCKED = "blocked"
    CREATE_AND_START = "create_and_start"
    CREATE_ONLY = "create_only"
    RESUME = "resume"
    RELAUNCH_STOPPED = "relaunch_stopped"
    PAUSE = "pause"
    COMPLETED = "completed"
    NOOP = "noop"


class StudyRuntimeDaemonStep(StrEnum):
    CREATE = "create"
    RESUME = "resume"
    PAUSE = "pause"
    COMPLETION_SYNC = "completion_sync"


class StudyRuntimeAuditStatus(StrEnum):
    LIVE = "live"
    NONE = "none"
    UNKNOWN = "unknown"
    OTHER = "other"


_LIVE_QUEST_STATUSES = {
    StudyRuntimeQuestStatus.RUNNING,
    StudyRuntimeQuestStatus.RETRYING,
    StudyRuntimeQuestStatus.ACTIVE,
}
_RESUMABLE_QUEST_STATUSES = {
    StudyRuntimeQuestStatus.PAUSED,
    StudyRuntimeQuestStatus.IDLE,
    StudyRuntimeQuestStatus.CREATED,
}


@dataclass(frozen=True)
class StudyRuntimeAuditRecord:
    status: StudyRuntimeAuditStatus
    payload: dict[str, Any]

    def __post_init__(self) -> None:
        object.__setattr__(self, "status", self._normalize_status(self.status))
        object.__setattr__(self, "payload", dict(self.payload))

    def to_dict(self) -> dict[str, Any]:
        return dict(self.payload)

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "StudyRuntimeAuditRecord":
        if not isinstance(payload, dict):
            raise TypeError("study runtime audit payload must be a mapping")
        if "status" not in payload:
            raise ValueError("study runtime audit payload missing status")
        return cls(status=payload.get("status"), payload=dict(payload))

    @staticmethod
    def _normalize_status(value: StudyRuntimeAuditStatus | str) -> StudyRuntimeAuditStatus:
        if isinstance(value, StudyRuntimeAuditStatus):
            return value
        if not isinstance(value, str):
            raise TypeError("study runtime audit status must be str")
        normalized = value.strip().lower()
        if normalized == StudyRuntimeAuditStatus.LIVE.value:
            return StudyRuntimeAuditStatus.LIVE
        if normalized == StudyRuntimeAuditStatus.NONE.value:
            return StudyRuntimeAuditStatus.NONE
        if normalized == StudyRuntimeAuditStatus.UNKNOWN.value:
            return StudyRuntimeAuditStatus.UNKNOWN
        return StudyRuntimeAuditStatus.OTHER


@dataclass(frozen=True)
class StudyRuntimeAutonomousRuntimeNotice:
    required: bool
    notice_key: str
    notification_reason: str
    quest_id: str
    quest_status: str
    active_run_id: str | None
    browser_url: str | None
    quest_api_url: str | None
    quest_session_api_url: str | None
    monitoring_available: bool
    monitoring_error: str | None
    launch_report_path: str

    def __post_init__(self) -> None:
        if not isinstance(self.required, bool):
            raise TypeError("study runtime autonomous notice required must be bool")
        if not isinstance(self.monitoring_available, bool):
            raise TypeError("study runtime autonomous notice monitoring_available must be bool")
        for field_name in ("notice_key", "notification_reason", "quest_id", "quest_status", "launch_report_path"):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise TypeError(f"study runtime autonomous notice {field_name} must be non-empty str")
        for field_name in ("active_run_id", "browser_url", "quest_api_url", "quest_session_api_url", "monitoring_error"):
            value = getattr(self, field_name)
            if value is not None and not isinstance(value, str):
                raise TypeError(f"study runtime autonomous notice {field_name} must be str or None")

    def to_dict(self) -> dict[str, Any]:
        return {
            "required": self.required,
            "notice_key": self.notice_key,
            "notification_reason": self.notification_reason,
            "quest_id": self.quest_id,
            "quest_status": self.quest_status,
            "active_run_id": self.active_run_id,
            "browser_url": self.browser_url,
            "quest_api_url": self.quest_api_url,
            "quest_session_api_url": self.quest_session_api_url,
            "monitoring_available": self.monitoring_available,
            "monitoring_error": self.monitoring_error,
            "launch_report_path": self.launch_report_path,
        }

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "StudyRuntimeAutonomousRuntimeNotice":
        if not isinstance(payload, dict):
            raise TypeError("study runtime autonomous notice payload must be a mapping")
        return cls(
            required=bool(payload.get("required")),
            notice_key=str(payload.get("notice_key") or ""),
            notification_reason=str(payload.get("notification_reason") or ""),
            quest_id=str(payload.get("quest_id") or ""),
            quest_status=str(payload.get("quest_status") or ""),
            active_run_id=str(payload.get("active_run_id") or "").strip() or None,
            browser_url=str(payload.get("browser_url") or "").strip() or None,
            quest_api_url=str(payload.get("quest_api_url") or "").strip() or None,
            quest_session_api_url=str(payload.get("quest_session_api_url") or "").strip() or None,
            monitoring_available=bool(payload.get("monitoring_available")),
            monitoring_error=str(payload.get("monitoring_error") or "").strip() or None,
            launch_report_path=str(payload.get("launch_report_path") or ""),
        )


@dataclass(frozen=True)
class StudyRuntimeSummaryAlignment:
    source_of_truth: str
    runtime_state_path: str
    runtime_state_status: str | None
    source_active_run_id: str | None
    source_runtime_liveness_status: str | None
    source_supervisor_tick_status: str | None
    launch_report_path: str
    launch_report_exists: bool
    launch_report_quest_status: str | None
    launch_report_active_run_id: str | None
    launch_report_runtime_liveness_status: str | None
    launch_report_supervisor_tick_status: str | None
    aligned: bool
    mismatch_reason: str | None
    status_sync_applied: bool

    def __post_init__(self) -> None:
        for field_name in ("source_of_truth", "runtime_state_path", "launch_report_path"):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise TypeError(f"study runtime summary alignment {field_name} must be non-empty str")
        for field_name in (
            "runtime_state_status",
            "source_active_run_id",
            "source_runtime_liveness_status",
            "source_supervisor_tick_status",
            "launch_report_quest_status",
            "launch_report_active_run_id",
            "launch_report_runtime_liveness_status",
            "launch_report_supervisor_tick_status",
            "mismatch_reason",
        ):
            value = getattr(self, field_name)
            if value is not None and not isinstance(value, str):
                raise TypeError(f"study runtime summary alignment {field_name} must be str or None")
        for field_name in ("launch_report_exists", "aligned", "status_sync_applied"):
            if not isinstance(getattr(self, field_name), bool):
                raise TypeError(f"study runtime summary alignment {field_name} must be bool")

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_of_truth": self.source_of_truth,
            "runtime_state_path": self.runtime_state_path,
            "runtime_state_status": self.runtime_state_status,
            "source_active_run_id": self.source_active_run_id,
            "source_runtime_liveness_status": self.source_runtime_liveness_status,
            "source_supervisor_tick_status": self.source_supervisor_tick_status,
            "launch_report_path": self.launch_report_path,
            "launch_report_exists": self.launch_report_exists,
            "launch_report_quest_status": self.launch_report_quest_status,
            "launch_report_active_run_id": self.launch_report_active_run_id,
            "launch_report_runtime_liveness_status": self.launch_report_runtime_liveness_status,
            "launch_report_supervisor_tick_status": self.launch_report_supervisor_tick_status,
            "aligned": self.aligned,
            "mismatch_reason": self.mismatch_reason,
            "status_sync_applied": self.status_sync_applied,
        }

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "StudyRuntimeSummaryAlignment":
        if not isinstance(payload, dict):
            raise TypeError("study runtime summary alignment payload must be a mapping")
        return cls(
            source_of_truth=str(payload.get("source_of_truth") or ""),
            runtime_state_path=str(payload.get("runtime_state_path") or ""),
            runtime_state_status=str(payload.get("runtime_state_status") or "").strip() or None,
            source_active_run_id=str(payload.get("source_active_run_id") or "").strip() or None,
            source_runtime_liveness_status=str(payload.get("source_runtime_liveness_status") or "").strip() or None,
            source_supervisor_tick_status=str(payload.get("source_supervisor_tick_status") or "").strip() or None,
            launch_report_path=str(payload.get("launch_report_path") or ""),
            launch_report_exists=bool(payload.get("launch_report_exists")),
            launch_report_quest_status=str(payload.get("launch_report_quest_status") or "").strip() or None,
            launch_report_active_run_id=str(payload.get("launch_report_active_run_id") or "").strip() or None,
            launch_report_runtime_liveness_status=(
                str(payload.get("launch_report_runtime_liveness_status") or "").strip() or None
            ),
            launch_report_supervisor_tick_status=(
                str(payload.get("launch_report_supervisor_tick_status") or "").strip() or None
            ),
            aligned=bool(payload.get("aligned")),
            mismatch_reason=str(payload.get("mismatch_reason") or "").strip() or None,
            status_sync_applied=bool(payload.get("status_sync_applied")),
        )


@dataclass(frozen=True)
class StudyRuntimeExecutionOwnerGuard:
    owner: str
    supervisor_only: bool
    guard_reason: str
    active_run_id: str | None
    current_required_action: str
    allowed_actions: tuple[str, ...]
    forbidden_actions: tuple[str, ...]
    runtime_owned_roots: tuple[str, ...]
    takeover_required: bool
    takeover_action: str
    publication_gate_allows_direct_write: bool
    controller_stage_note: str
    payload: dict[str, Any]

    def __post_init__(self) -> None:
        for field_name in ("owner", "guard_reason", "current_required_action", "takeover_action", "controller_stage_note"):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise TypeError(f"study runtime execution owner guard {field_name} must be non-empty str")
        if not isinstance(self.supervisor_only, bool):
            raise TypeError("study runtime execution owner guard supervisor_only must be bool")
        if self.active_run_id is not None and not isinstance(self.active_run_id, str):
            raise TypeError("study runtime execution owner guard active_run_id must be str or None")
        if not isinstance(self.takeover_required, bool):
            raise TypeError("study runtime execution owner guard takeover_required must be bool")
        if not isinstance(self.publication_gate_allows_direct_write, bool):
            raise TypeError(
                "study runtime execution owner guard publication_gate_allows_direct_write must be bool"
            )
        object.__setattr__(self, "allowed_actions", tuple(str(item) for item in self.allowed_actions))
        object.__setattr__(self, "forbidden_actions", tuple(str(item) for item in self.forbidden_actions))
        object.__setattr__(self, "runtime_owned_roots", tuple(str(item) for item in self.runtime_owned_roots))
        object.__setattr__(self, "payload", dict(self.payload))

    def to_dict(self) -> dict[str, Any]:
        return dict(self.payload)

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "StudyRuntimeExecutionOwnerGuard":
        if not isinstance(payload, dict):
            raise TypeError("study runtime execution owner guard payload must be a mapping")
        allowed_actions = payload.get("allowed_actions")
        if not isinstance(allowed_actions, list):
            raise ValueError("study runtime execution owner guard allowed_actions must be a list")
        forbidden_actions = payload.get("forbidden_actions")
        if not isinstance(forbidden_actions, list):
            raise ValueError("study runtime execution owner guard forbidden_actions must be a list")
        runtime_owned_roots = payload.get("runtime_owned_roots")
        if not isinstance(runtime_owned_roots, list):
            raise ValueError("study runtime execution owner guard runtime_owned_roots must be a list")
        publication_gate_allows_direct_write = payload.get("publication_gate_allows_direct_write")
        if not isinstance(publication_gate_allows_direct_write, bool):
            raise TypeError(
                "study runtime execution owner guard publication_gate_allows_direct_write must be bool"
            )
        return cls(
            owner=str(payload.get("owner") or ""),
            supervisor_only=bool(payload.get("supervisor_only")),
            guard_reason=str(payload.get("guard_reason") or ""),
            active_run_id=str(payload.get("active_run_id") or "").strip() or None,
            current_required_action=str(payload.get("current_required_action") or ""),
            allowed_actions=tuple(str(item) for item in allowed_actions),
            forbidden_actions=tuple(str(item) for item in forbidden_actions),
            runtime_owned_roots=tuple(str(item) for item in runtime_owned_roots),
            takeover_required=bool(payload.get("takeover_required")),
            takeover_action=str(payload.get("takeover_action") or ""),
            publication_gate_allows_direct_write=publication_gate_allows_direct_write,
            controller_stage_note=str(payload.get("controller_stage_note") or ""),
            payload=dict(payload),
        )


@dataclass(frozen=True)
class StudyRuntimePendingUserInteraction:
    interaction_id: str
    kind: str | None
    waiting_interaction_id: str | None
    default_reply_interaction_id: str | None
    pending_decisions: tuple[str, ...]
    blocking: bool
    reply_mode: str | None
    expects_reply: bool
    allow_free_text: bool
    message: str | None
    summary: str | None
    reply_schema: dict[str, Any]
    decision_type: str | None
    options_count: int
    guidance_requires_user_decision: bool | None
    source_artifact_path: str | None
    relay_required: bool

    def __post_init__(self) -> None:
        if not isinstance(self.interaction_id, str) or not self.interaction_id.strip():
            raise TypeError("study runtime pending user interaction interaction_id must be non-empty str")
        for field_name in (
            "kind",
            "waiting_interaction_id",
            "default_reply_interaction_id",
            "reply_mode",
            "message",
            "summary",
            "decision_type",
            "source_artifact_path",
        ):
            value = getattr(self, field_name)
            if value is not None and not isinstance(value, str):
                raise TypeError(f"study runtime pending user interaction {field_name} must be str or None")
        if not isinstance(self.blocking, bool):
            raise TypeError("study runtime pending user interaction blocking must be bool")
        if not isinstance(self.expects_reply, bool):
            raise TypeError("study runtime pending user interaction expects_reply must be bool")
        if not isinstance(self.allow_free_text, bool):
            raise TypeError("study runtime pending user interaction allow_free_text must be bool")
        if not isinstance(self.options_count, int) or self.options_count < 0:
            raise TypeError("study runtime pending user interaction options_count must be non-negative int")
        if self.guidance_requires_user_decision is not None and not isinstance(
            self.guidance_requires_user_decision,
            bool,
        ):
            raise TypeError(
                "study runtime pending user interaction guidance_requires_user_decision must be bool or None"
            )
        if not isinstance(self.relay_required, bool):
            raise TypeError("study runtime pending user interaction relay_required must be bool")
        object.__setattr__(self, "pending_decisions", tuple(str(item) for item in self.pending_decisions if str(item).strip()))
        object.__setattr__(self, "reply_schema", dict(self.reply_schema))

    def to_dict(self) -> dict[str, Any]:
        return {
            "interaction_id": self.interaction_id,
            "kind": self.kind,
            "waiting_interaction_id": self.waiting_interaction_id,
            "default_reply_interaction_id": self.default_reply_interaction_id,
            "pending_decisions": list(self.pending_decisions),
            "blocking": self.blocking,
            "reply_mode": self.reply_mode,
            "expects_reply": self.expects_reply,
            "allow_free_text": self.allow_free_text,
            "message": self.message,
            "summary": self.summary,
            "reply_schema": dict(self.reply_schema),
            "decision_type": self.decision_type,
            "options_count": self.options_count,
            "guidance_requires_user_decision": self.guidance_requires_user_decision,
            "source_artifact_path": self.source_artifact_path,
            "relay_required": self.relay_required,
        }

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "StudyRuntimePendingUserInteraction":
        if not isinstance(payload, dict):
            raise TypeError("study runtime pending user interaction payload must be a mapping")
        pending_decisions = payload.get("pending_decisions")
        if pending_decisions is None:
            pending_decisions = []
        if not isinstance(pending_decisions, (list, tuple)):
            raise TypeError("study runtime pending user interaction pending_decisions must be a list")
        reply_schema = payload.get("reply_schema")
        if reply_schema is None:
            reply_schema = {}
        if not isinstance(reply_schema, dict):
            raise TypeError("study runtime pending user interaction reply_schema must be a mapping")
        return cls(
            interaction_id=str(payload.get("interaction_id") or ""),
            kind=str(payload.get("kind") or "").strip() or None,
            waiting_interaction_id=str(payload.get("waiting_interaction_id") or "").strip() or None,
            default_reply_interaction_id=str(payload.get("default_reply_interaction_id") or "").strip() or None,
            pending_decisions=tuple(str(item) for item in pending_decisions),
            blocking=bool(payload.get("blocking")),
            reply_mode=str(payload.get("reply_mode") or "").strip() or None,
            expects_reply=bool(payload.get("expects_reply")),
            allow_free_text=bool(payload.get("allow_free_text")),
            message=str(payload.get("message") or "").strip() or None,
            summary=str(payload.get("summary") or "").strip() or None,
            reply_schema=reply_schema,
            decision_type=str(payload.get("decision_type") or "").strip() or None,
            options_count=int(payload.get("options_count") or 0),
            guidance_requires_user_decision=payload.get("guidance_requires_user_decision"),
            source_artifact_path=str(payload.get("source_artifact_path") or "").strip() or None,
            relay_required=bool(payload.get("relay_required")),
        )


@dataclass(frozen=True)
class StudyRuntimeInteractionArbitration:
    classification: str
    action: str
    reason_code: str
    requires_user_input: bool
    valid_blocking: bool
    kind: str | None
    decision_type: str | None
    source_artifact_path: str | None
    controller_stage_note: str
    payload: dict[str, Any]

    def __post_init__(self) -> None:
        for field_name in ("classification", "action", "reason_code", "controller_stage_note"):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise TypeError(f"study runtime interaction arbitration {field_name} must be non-empty str")
        for field_name in ("kind", "decision_type", "source_artifact_path"):
            value = getattr(self, field_name)
            if value is not None and not isinstance(value, str):
                raise TypeError(f"study runtime interaction arbitration {field_name} must be str or None")
        if not isinstance(self.requires_user_input, bool):
            raise TypeError("study runtime interaction arbitration requires_user_input must be bool")
        if not isinstance(self.valid_blocking, bool):
            raise TypeError("study runtime interaction arbitration valid_blocking must be bool")
        object.__setattr__(self, "payload", dict(self.payload))

    def to_dict(self) -> dict[str, Any]:
        return dict(self.payload)

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "StudyRuntimeInteractionArbitration":
        if not isinstance(payload, dict):
            raise TypeError("study runtime interaction arbitration payload must be a mapping")
        return cls(
            classification=str(payload.get("classification") or ""),
            action=str(payload.get("action") or ""),
            reason_code=str(payload.get("reason_code") or ""),
            requires_user_input=bool(payload.get("requires_user_input")),
            valid_blocking=bool(payload.get("valid_blocking")),
            kind=str(payload.get("kind") or "").strip() or None,
            decision_type=str(payload.get("decision_type") or "").strip() or None,
            source_artifact_path=str(payload.get("source_artifact_path") or "").strip() or None,
            controller_stage_note=str(payload.get("controller_stage_note") or ""),
            payload=dict(payload),
        )


@dataclass(frozen=True)
class StudyRuntimeContinuationState:
    quest_status: str | None
    active_run_id: str | None
    continuation_policy: str | None
    continuation_anchor: str | None
    continuation_reason: str | None
    runtime_state_path: str

    def __post_init__(self) -> None:
        for field_name in (
            "quest_status",
            "active_run_id",
            "continuation_policy",
            "continuation_anchor",
            "continuation_reason",
        ):
            value = getattr(self, field_name)
            if value is not None and not isinstance(value, str):
                raise TypeError(f"study runtime continuation state {field_name} must be str or None")
        if not isinstance(self.runtime_state_path, str) or not self.runtime_state_path.strip():
            raise TypeError("study runtime continuation state runtime_state_path must be non-empty str")

    def to_dict(self) -> dict[str, Any]:
        return {
            "quest_status": self.quest_status,
            "active_run_id": self.active_run_id,
            "continuation_policy": self.continuation_policy,
            "continuation_anchor": self.continuation_anchor,
            "continuation_reason": self.continuation_reason,
            "runtime_state_path": self.runtime_state_path,
        }

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "StudyRuntimeContinuationState":
        if not isinstance(payload, dict):
            raise TypeError("study runtime continuation state payload must be a mapping")
        return cls(
            quest_status=str(payload.get("quest_status") or "").strip() or None,
            active_run_id=str(payload.get("active_run_id") or "").strip() or None,
            continuation_policy=str(payload.get("continuation_policy") or "").strip() or None,
            continuation_anchor=str(payload.get("continuation_anchor") or "").strip() or None,
            continuation_reason=str(payload.get("continuation_reason") or "").strip() or None,
            runtime_state_path=str(payload.get("runtime_state_path") or ""),
        )
