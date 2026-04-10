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
    STUDY_EXECUTION_NOT_MED_DEEPSCIENTIST = "study_execution_not_med_deepscientist"
    STUDY_EXECUTION_NOT_MANAGED = "study_execution_not_managed"
    ENTRY_MODE_NOT_MANAGED = "entry_mode_not_managed"
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
    launch_report_path: str
    launch_report_exists: bool
    launch_report_quest_status: str | None
    aligned: bool
    mismatch_reason: str | None
    status_sync_applied: bool

    def __post_init__(self) -> None:
        for field_name in ("source_of_truth", "runtime_state_path", "launch_report_path"):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise TypeError(f"study runtime summary alignment {field_name} must be non-empty str")
        for field_name in ("runtime_state_status", "launch_report_quest_status", "mismatch_reason"):
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
            "launch_report_path": self.launch_report_path,
            "launch_report_exists": self.launch_report_exists,
            "launch_report_quest_status": self.launch_report_quest_status,
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
            launch_report_path=str(payload.get("launch_report_path") or ""),
            launch_report_exists=bool(payload.get("launch_report_exists")),
            launch_report_quest_status=str(payload.get("launch_report_quest_status") or "").strip() or None,
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


@dataclass(frozen=True)
class StudyRuntimeAnalysisBundleResult:
    ready: bool
    payload: dict[str, Any]

    def __post_init__(self) -> None:
        if not isinstance(self.ready, bool):
            raise TypeError("study runtime analysis bundle ready must be bool")
        object.__setattr__(self, "payload", dict(self.payload))

    def to_dict(self) -> dict[str, Any]:
        return dict(self.payload)

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "StudyRuntimeAnalysisBundleResult":
        if not isinstance(payload, dict):
            raise TypeError("study runtime analysis bundle payload must be a mapping")
        if "ready" not in payload:
            raise ValueError("study runtime analysis bundle payload missing ready")
        ready = payload.get("ready")
        if not isinstance(ready, bool):
            raise TypeError("study runtime analysis bundle ready must be bool")
        return cls(ready=ready, payload=dict(payload))


@dataclass(frozen=True)
class StudyRuntimeOverlayAudit:
    all_roots_ready: bool
    payload: dict[str, Any]

    def __post_init__(self) -> None:
        if not isinstance(self.all_roots_ready, bool):
            raise TypeError("study runtime overlay audit all_roots_ready must be bool")
        object.__setattr__(self, "payload", dict(self.payload))

    def to_dict(self) -> dict[str, Any]:
        return dict(self.payload)

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "StudyRuntimeOverlayAudit":
        if not isinstance(payload, dict):
            raise TypeError("study runtime overlay audit payload must be a mapping")
        if "all_roots_ready" not in payload:
            raise ValueError("study runtime overlay audit payload missing all_roots_ready")
        all_roots_ready = payload.get("all_roots_ready")
        if not isinstance(all_roots_ready, bool):
            raise TypeError("study runtime overlay audit all_roots_ready must be bool")
        return cls(all_roots_ready=all_roots_ready, payload=dict(payload))


@dataclass(frozen=True)
class StudyRuntimeOverlayResult:
    audit: StudyRuntimeOverlayAudit
    payload: dict[str, Any]

    def __post_init__(self) -> None:
        object.__setattr__(self, "payload", dict(self.payload))

    def to_dict(self) -> dict[str, Any]:
        return dict(self.payload)

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "StudyRuntimeOverlayResult":
        if not isinstance(payload, dict):
            raise TypeError("study runtime overlay payload must be a mapping")
        audit = payload.get("audit")
        if not isinstance(audit, dict):
            raise ValueError("study runtime overlay payload missing audit")
        return cls(
            audit=StudyRuntimeOverlayAudit.from_payload(audit),
            payload=dict(payload),
        )


@dataclass(frozen=True)
class StudyRuntimeStartupContextSyncResult:
    ok: bool
    payload: dict[str, Any]

    def __post_init__(self) -> None:
        if not isinstance(self.ok, bool):
            raise TypeError("study runtime startup context sync ok must be bool")
        object.__setattr__(self, "payload", dict(self.payload))

    def to_dict(self) -> dict[str, Any]:
        return dict(self.payload)

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "StudyRuntimeStartupContextSyncResult":
        if not isinstance(payload, dict):
            raise TypeError("study runtime startup context sync payload must be a mapping")
        if "ok" not in payload:
            raise ValueError("study runtime startup context sync payload missing ok")
        ok = payload.get("ok")
        if not isinstance(ok, bool):
            raise TypeError("study runtime startup context sync ok must be bool")
        normalized_payload = dict(payload)
        snapshot = payload.get("snapshot")
        if snapshot is not None and not isinstance(snapshot, dict):
            raise ValueError("study runtime startup context sync snapshot must be a mapping")
        if ok:
            if not isinstance(snapshot, dict):
                raise ValueError("study runtime startup context sync payload missing snapshot")
            payload_quest_id = str(payload.get("quest_id") or "").strip()
            snapshot_quest_id = str(snapshot.get("quest_id") or "").strip()
            if payload_quest_id and snapshot_quest_id and payload_quest_id != snapshot_quest_id:
                raise ValueError("study runtime startup context sync quest_id mismatch")
            quest_id = payload_quest_id or snapshot_quest_id
            if not quest_id:
                raise ValueError("study runtime startup context sync payload missing quest_id")
            if not isinstance(snapshot.get("startup_contract"), dict):
                raise ValueError("study runtime startup context sync snapshot missing startup_contract")
            normalized_snapshot = dict(snapshot)
            normalized_snapshot["quest_id"] = quest_id
            normalized_payload["quest_id"] = quest_id
            normalized_payload["snapshot"] = normalized_snapshot
        return cls(ok=ok, payload=normalized_payload)


@dataclass(frozen=True)
class StudyRuntimePartialQuestRecoveryResult:
    status: str
    quest_root: str
    archived_root: str
    missing_required_files: tuple[str, ...]
    payload: dict[str, Any]

    def __post_init__(self) -> None:
        object.__setattr__(self, "payload", dict(self.payload))
        object.__setattr__(self, "missing_required_files", tuple(str(item) for item in self.missing_required_files))

    def to_dict(self) -> dict[str, Any]:
        return dict(self.payload)

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "StudyRuntimePartialQuestRecoveryResult":
        if not isinstance(payload, dict):
            raise TypeError("study runtime partial quest recovery payload must be a mapping")
        status = str(payload.get("status") or "").strip()
        if not status:
            raise ValueError("study runtime partial quest recovery payload missing status")
        quest_root = str(payload.get("quest_root") or "").strip()
        if not quest_root:
            raise ValueError("study runtime partial quest recovery payload missing quest_root")
        archived_root = str(payload.get("archived_root") or "").strip()
        if not archived_root:
            raise ValueError("study runtime partial quest recovery payload missing archived_root")
        missing_required_files = payload.get("missing_required_files")
        if not isinstance(missing_required_files, list):
            raise ValueError("study runtime partial quest recovery payload missing missing_required_files")
        return cls(
            status=status,
            quest_root=quest_root,
            archived_root=archived_root,
            missing_required_files=tuple(str(item) for item in missing_required_files),
            payload=dict(payload),
        )


@dataclass(frozen=True)
class StudyRuntimeWorkspaceContractsSummary:
    overall_ready: bool
    payload: dict[str, Any]

    def __post_init__(self) -> None:
        if not isinstance(self.overall_ready, bool):
            raise TypeError("study runtime workspace contracts overall_ready must be bool")
        object.__setattr__(self, "payload", dict(self.payload))

    def to_dict(self) -> dict[str, Any]:
        return dict(self.payload)

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "StudyRuntimeWorkspaceContractsSummary":
        if not isinstance(payload, dict):
            raise TypeError("study runtime workspace contracts payload must be a mapping")
        overall_ready = payload.get("overall_ready", False)
        if not isinstance(overall_ready, bool):
            raise TypeError("study runtime workspace contracts overall_ready must be bool")
        return cls(overall_ready=overall_ready, payload=dict(payload))


@dataclass(frozen=True)
class StudyRuntimeStartupDataReadinessReport:
    unresolved_contract_study_ids: tuple[str, ...]
    payload: dict[str, Any]

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "unresolved_contract_study_ids",
            tuple(str(item) for item in self.unresolved_contract_study_ids),
        )
        object.__setattr__(self, "payload", dict(self.payload))

    def to_dict(self) -> dict[str, Any]:
        return dict(self.payload)

    def has_unresolved_contract_for(self, study_id: str) -> bool:
        return study_id in self.unresolved_contract_study_ids

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "StudyRuntimeStartupDataReadinessReport":
        if not isinstance(payload, dict):
            raise TypeError("study runtime startup data readiness payload must be a mapping")
        study_summary = payload.get("study_summary")
        unresolved_contract_study_ids: tuple[str, ...] = ()
        if study_summary is not None:
            if not isinstance(study_summary, dict):
                raise ValueError("study runtime startup data readiness study_summary must be a mapping")
            raw_unresolved = study_summary.get("unresolved_contract_study_ids", [])
            if not isinstance(raw_unresolved, list):
                raise ValueError(
                    "study runtime startup data readiness unresolved_contract_study_ids must be a list"
                )
            unresolved_contract_study_ids = tuple(str(item) for item in raw_unresolved)
        return cls(
            unresolved_contract_study_ids=unresolved_contract_study_ids,
            payload=dict(payload),
        )


@dataclass(frozen=True)
class StudyRuntimeStartupBoundaryGate:
    allow_compute_stage: bool
    required_first_anchor: str
    effective_custom_profile: str
    legacy_code_execution_allowed: bool
    payload: dict[str, Any]

    def __post_init__(self) -> None:
        if not isinstance(self.allow_compute_stage, bool):
            raise TypeError("study runtime startup boundary allow_compute_stage must be bool")
        if not isinstance(self.required_first_anchor, str):
            raise TypeError("study runtime startup boundary required_first_anchor must be str")
        if not isinstance(self.effective_custom_profile, str):
            raise TypeError("study runtime startup boundary effective_custom_profile must be str")
        if not isinstance(self.legacy_code_execution_allowed, bool):
            raise TypeError("study runtime startup boundary legacy_code_execution_allowed must be bool")
        object.__setattr__(self, "payload", dict(self.payload))

    def to_dict(self) -> dict[str, Any]:
        return dict(self.payload)

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "StudyRuntimeStartupBoundaryGate":
        if not isinstance(payload, dict):
            raise TypeError("study runtime startup boundary payload must be a mapping")
        allow_compute_stage = payload.get("allow_compute_stage", False)
        if not isinstance(allow_compute_stage, bool):
            raise TypeError("study runtime startup boundary allow_compute_stage must be bool")
        required_first_anchor = str(payload.get("required_first_anchor") or "")
        effective_custom_profile = str(payload.get("effective_custom_profile") or "")
        legacy_code_execution_allowed = payload.get("legacy_code_execution_allowed", False)
        if not isinstance(legacy_code_execution_allowed, bool):
            raise TypeError("study runtime startup boundary legacy_code_execution_allowed must be bool")
        return cls(
            allow_compute_stage=allow_compute_stage,
            required_first_anchor=required_first_anchor,
            effective_custom_profile=effective_custom_profile,
            legacy_code_execution_allowed=legacy_code_execution_allowed,
            payload=dict(payload),
        )


@dataclass(frozen=True)
class StudyRuntimeReentryGate:
    allow_runtime_entry: bool
    require_startup_hydration: bool
    require_managed_skill_audit: bool
    payload: dict[str, Any]

    def __post_init__(self) -> None:
        if not isinstance(self.allow_runtime_entry, bool):
            raise TypeError("study runtime reentry allow_runtime_entry must be bool")
        if not isinstance(self.require_startup_hydration, bool):
            raise TypeError("study runtime reentry require_startup_hydration must be bool")
        if not isinstance(self.require_managed_skill_audit, bool):
            raise TypeError("study runtime reentry require_managed_skill_audit must be bool")
        object.__setattr__(self, "payload", dict(self.payload))

    def to_dict(self) -> dict[str, Any]:
        return dict(self.payload)

    @classmethod
    def from_payload(
        cls,
        payload: dict[str, Any],
        *,
        default_allow_runtime_entry: bool = False,
    ) -> "StudyRuntimeReentryGate":
        if not isinstance(payload, dict):
            raise TypeError("study runtime reentry payload must be a mapping")
        allow_runtime_entry = payload.get("allow_runtime_entry", default_allow_runtime_entry)
        require_startup_hydration = payload.get("require_startup_hydration", False)
        require_managed_skill_audit = payload.get("require_managed_skill_audit", False)
        if not isinstance(allow_runtime_entry, bool):
            raise TypeError("study runtime reentry allow_runtime_entry must be bool")
        if not isinstance(require_startup_hydration, bool):
            raise TypeError("study runtime reentry require_startup_hydration must be bool")
        if not isinstance(require_managed_skill_audit, bool):
            raise TypeError("study runtime reentry require_managed_skill_audit must be bool")
        return cls(
            allow_runtime_entry=allow_runtime_entry,
            require_startup_hydration=require_startup_hydration,
            require_managed_skill_audit=require_managed_skill_audit,
            payload=dict(payload),
        )


@dataclass(frozen=True)
class StudyRuntimePublicationSupervisorState:
    supervisor_phase: str
    phase_owner: str
    upstream_scientific_anchor_ready: bool
    bundle_tasks_downstream_only: bool
    current_required_action: str
    deferred_downstream_actions: tuple[str, ...]
    controller_stage_note: str
    payload: dict[str, Any]

    def __post_init__(self) -> None:
        for field_name in ("supervisor_phase", "phase_owner", "current_required_action", "controller_stage_note"):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise TypeError(f"study runtime publication supervisor {field_name} must be non-empty str")
        if not isinstance(self.upstream_scientific_anchor_ready, bool):
            raise TypeError(
                "study runtime publication supervisor upstream_scientific_anchor_ready must be bool"
            )
        if not isinstance(self.bundle_tasks_downstream_only, bool):
            raise TypeError("study runtime publication supervisor bundle_tasks_downstream_only must be bool")
        object.__setattr__(
            self,
            "deferred_downstream_actions",
            tuple(str(item) for item in self.deferred_downstream_actions),
        )
        object.__setattr__(self, "payload", dict(self.payload))

    def to_dict(self) -> dict[str, Any]:
        return dict(self.payload)

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "StudyRuntimePublicationSupervisorState":
        if not isinstance(payload, dict):
            raise TypeError("study runtime publication supervisor payload must be a mapping")
        upstream_scientific_anchor_ready = payload.get("upstream_scientific_anchor_ready")
        if not isinstance(upstream_scientific_anchor_ready, bool):
            raise TypeError(
                "study runtime publication supervisor upstream_scientific_anchor_ready must be bool"
            )
        bundle_tasks_downstream_only = payload.get("bundle_tasks_downstream_only")
        if not isinstance(bundle_tasks_downstream_only, bool):
            raise TypeError("study runtime publication supervisor bundle_tasks_downstream_only must be bool")
        deferred_downstream_actions = payload.get("deferred_downstream_actions")
        if not isinstance(deferred_downstream_actions, list):
            raise ValueError(
                "study runtime publication supervisor deferred_downstream_actions must be a list"
            )
        return cls(
            supervisor_phase=str(payload.get("supervisor_phase") or ""),
            phase_owner=str(payload.get("phase_owner") or ""),
            upstream_scientific_anchor_ready=upstream_scientific_anchor_ready,
            bundle_tasks_downstream_only=bundle_tasks_downstream_only,
            current_required_action=str(payload.get("current_required_action") or ""),
            deferred_downstream_actions=tuple(str(item) for item in deferred_downstream_actions),
            controller_stage_note=str(payload.get("controller_stage_note") or ""),
            payload=dict(payload),
        )


@dataclass(frozen=True)
class StudyCompletionSyncResult:
    payload: dict[str, Any]
    completion_snapshot_status: str | None

    def __post_init__(self) -> None:
        object.__setattr__(self, "payload", dict(self.payload))
        if self.completion_snapshot_status == "":
            object.__setattr__(self, "completion_snapshot_status", None)

    def to_dict(self) -> dict[str, Any]:
        return dict(self.payload)

    def snapshot_status_or(self, fallback: str) -> str:
        return self.completion_snapshot_status or fallback

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "StudyCompletionSyncResult":
        if not isinstance(payload, dict):
            raise TypeError("study completion sync payload must be a mapping")
        completion_request = payload.get("completion_request")
        if completion_request is not None and not isinstance(completion_request, dict):
            raise ValueError("study completion sync payload completion_request must be a mapping")
        approval_message = payload.get("approval_message")
        if approval_message is not None and not isinstance(approval_message, dict):
            raise ValueError("study completion sync payload approval_message must be a mapping")
        completion = payload.get("completion")
        if not isinstance(completion, dict):
            raise ValueError("study completion sync payload missing completion")
        snapshot = completion.get("snapshot")
        if snapshot is not None and not isinstance(snapshot, dict):
            raise ValueError("study completion sync payload completion.snapshot must be a mapping")
        completion_status = str(completion.get("status") or "").strip() or None
        snapshot_status = (
            str(snapshot.get("status") or "").strip() or None if isinstance(snapshot, dict) else None
        )
        return cls(
            payload=dict(payload),
            completion_snapshot_status=snapshot_status or completion_status,
        )


@dataclass
class StudyRuntimeStatus(MutableMapping[str, Any]):
    schema_version: int
    study_id: str
    study_root: str
    entry_mode: str
    execution: dict[str, Any]
    quest_id: str
    quest_root: str
    quest_exists: bool
    quest_status: StudyRuntimeQuestStatus | None
    runtime_binding_path: str
    runtime_binding_exists: bool
    workspace_contracts: dict[str, Any] = field(default_factory=dict)
    startup_data_readiness: dict[str, Any] = field(default_factory=dict)
    startup_boundary_gate: dict[str, Any] = field(default_factory=dict)
    runtime_reentry_gate: dict[str, Any] = field(default_factory=dict)
    study_completion_state: StudyCompletionState = field(default_factory=_absent_study_completion_state)
    controller_first_policy_summary: str = ""
    automation_ready_summary: str = ""
    decision: StudyRuntimeDecision | None = None
    reason: StudyRuntimeReason | None = None
    extras: dict[str, Any] = field(default_factory=dict)

    _CORE_KEYS = {
        "schema_version",
        "study_id",
        "study_root",
        "entry_mode",
        "execution",
        "quest_id",
        "quest_root",
        "quest_exists",
        "quest_status",
        "runtime_binding_path",
        "runtime_binding_exists",
        "workspace_contracts",
        "startup_data_readiness",
        "startup_boundary_gate",
        "runtime_reentry_gate",
        "study_completion_contract",
        "controller_first_policy_summary",
        "automation_ready_summary",
        "decision",
        "reason",
    }

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "StudyRuntimeStatus":
        resolved_payload = dict(payload)
        extras = {key: value for key, value in resolved_payload.items() if key not in cls._CORE_KEYS}
        study_root = resolved_payload.get("study_root")
        return cls(
            schema_version=int(resolved_payload.get("schema_version") or 1),
            study_id=str(resolved_payload.get("study_id") or ""),
            study_root=str(resolved_payload.get("study_root") or ""),
            entry_mode=str(resolved_payload.get("entry_mode") or ""),
            execution=dict(resolved_payload.get("execution") or {}),
            quest_id=str(resolved_payload.get("quest_id") or ""),
            quest_root=str(resolved_payload.get("quest_root") or ""),
            quest_exists=bool(resolved_payload.get("quest_exists")),
            quest_status=cls._normalize_quest_status_field(resolved_payload.get("quest_status")),
            runtime_binding_path=str(resolved_payload.get("runtime_binding_path") or ""),
            runtime_binding_exists=bool(resolved_payload.get("runtime_binding_exists")),
            workspace_contracts=dict(resolved_payload.get("workspace_contracts") or {}),
            startup_data_readiness=dict(resolved_payload.get("startup_data_readiness") or {}),
            startup_boundary_gate=dict(resolved_payload.get("startup_boundary_gate") or {}),
            runtime_reentry_gate=dict(resolved_payload.get("runtime_reentry_gate") or {}),
            study_completion_state=cls._normalize_study_completion_state_field(
                resolved_payload.get("study_completion_contract") or {},
                study_root=study_root,
            ),
            controller_first_policy_summary=str(resolved_payload.get("controller_first_policy_summary") or ""),
            automation_ready_summary=str(resolved_payload.get("automation_ready_summary") or ""),
            decision=cls._normalize_decision_field(resolved_payload.get("decision")),
            reason=cls._normalize_reason_field(resolved_payload.get("reason")),
            extras=extras,
        )

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "schema_version": self.schema_version,
            "study_id": self.study_id,
            "study_root": self.study_root,
            "entry_mode": self.entry_mode,
            "execution": self.execution,
            "quest_id": self.quest_id,
            "quest_root": self.quest_root,
            "quest_exists": self.quest_exists,
            "quest_status": self.quest_status.value if self.quest_status is not None else None,
            "runtime_binding_path": self.runtime_binding_path,
            "runtime_binding_exists": self.runtime_binding_exists,
            "workspace_contracts": self.workspace_contracts,
            "startup_data_readiness": self.startup_data_readiness,
            "startup_boundary_gate": self.startup_boundary_gate,
            "runtime_reentry_gate": self.runtime_reentry_gate,
            "study_completion_contract": self.study_completion_state.to_dict(),
            "controller_first_policy_summary": self.controller_first_policy_summary,
            "automation_ready_summary": self.automation_ready_summary,
        }
        if self.decision is not None:
            payload["decision"] = self.decision.value
        if self.reason is not None:
            payload["reason"] = self.reason.value
        payload.update(self.extras)
        return payload

    @staticmethod
    def _normalize_decision_field(value: Any) -> StudyRuntimeDecision | None:
        if value is None or value == "":
            return None
        if isinstance(value, StudyRuntimeDecision):
            return value
        if not isinstance(value, str):
            raise TypeError("decision must be str")
        try:
            return StudyRuntimeDecision(value)
        except ValueError as exc:
            raise ValueError(f"unknown study runtime decision: {value}") from exc

    @staticmethod
    def _normalize_reason_field(value: Any) -> StudyRuntimeReason | None:
        if value is None or value == "":
            return None
        if isinstance(value, StudyRuntimeReason):
            return value
        if not isinstance(value, str):
            raise TypeError("reason must be str")
        try:
            return StudyRuntimeReason(value)
        except ValueError as exc:
            raise ValueError(f"unknown study runtime reason: {value}") from exc

    @staticmethod
    def _normalize_quest_status_field(value: Any) -> StudyRuntimeQuestStatus | None:
        if value is None:
            return None
        if value == "":
            return None
        if isinstance(value, StudyRuntimeQuestStatus):
            return value
        if not isinstance(value, str):
            raise TypeError("quest_status must be str or None")
        try:
            return StudyRuntimeQuestStatus(value)
        except ValueError as exc:
            raise ValueError(f"unknown study runtime quest status: {value}") from exc

    @staticmethod
    def _require_text_field(field_name: str, value: Any) -> str:
        if not isinstance(value, str):
            raise TypeError(f"{field_name} must be str")
        return value

    @staticmethod
    def _require_bool_field(field_name: str, value: Any) -> bool:
        if not isinstance(value, bool):
            raise TypeError(f"{field_name} must be bool")
        return value

    @staticmethod
    def _normalize_path_field(field_name: str, value: Any) -> str:
        if isinstance(value, str):
            return value
        if isinstance(value, PathLike):
            return str(value)
        raise TypeError(f"{field_name} must be str or PathLike")

    @staticmethod
    def _require_dict_field(field_name: str, value: Any) -> dict[str, Any]:
        if not isinstance(value, dict):
            raise TypeError(f"{field_name} must be dict")
        return dict(value)

    @staticmethod
    def _normalize_study_completion_state_field(
        value: Any,
        *,
        study_root: str | PathLike[str] | None,
    ) -> StudyCompletionState:
        if isinstance(value, StudyCompletionState):
            return value
        if not isinstance(value, dict):
            raise TypeError("study_completion_contract must be dict or StudyCompletionState")
        if not value:
            return _absent_study_completion_state()
        resolved_study_root = (
            Path(StudyRuntimeStatus._normalize_path_field("study_root", study_root))
            if study_root is not None and str(study_root).strip()
            else None
        )
        return StudyCompletionState.from_payload(value, study_root=resolved_study_root)

    @property
    def study_completion_contract(self) -> dict[str, Any]:
        return self.study_completion_state.to_dict()

    @property
    def workspace_contracts_summary(self) -> StudyRuntimeWorkspaceContractsSummary:
        return StudyRuntimeWorkspaceContractsSummary.from_payload(self.workspace_contracts)

    @property
    def startup_data_readiness_report(self) -> StudyRuntimeStartupDataReadinessReport:
        return StudyRuntimeStartupDataReadinessReport.from_payload(self.startup_data_readiness)

    @property
    def startup_boundary_gate_result(self) -> StudyRuntimeStartupBoundaryGate:
        return StudyRuntimeStartupBoundaryGate.from_payload(self.startup_boundary_gate)

    @property
    def runtime_reentry_gate_result(self) -> StudyRuntimeReentryGate:
        return StudyRuntimeReentryGate.from_payload(self.runtime_reentry_gate)

    @property
    def workspace_overall_ready(self) -> bool:
        return self.workspace_contracts_summary.overall_ready

    @property
    def startup_boundary_allows_compute_stage(self) -> bool:
        return self.startup_boundary_gate_result.allow_compute_stage

    @property
    def runtime_reentry_allows_runtime_entry(self) -> bool:
        return self.runtime_reentry_gate_result.allow_runtime_entry

    @property
    def runtime_reentry_requires_managed_skill_audit(self) -> bool:
        return self.runtime_reentry_gate_result.require_managed_skill_audit

    def has_unresolved_contract_for(self, study_id: str) -> bool:
        return self.startup_data_readiness_report.has_unresolved_contract_for(study_id)

    def should_refresh_startup_hydration_while_blocked(self) -> bool:
        if self.decision is not StudyRuntimeDecision.BLOCKED or not self.quest_exists:
            return False
        if self.quest_status not in {
            StudyRuntimeQuestStatus.CREATED,
            StudyRuntimeQuestStatus.IDLE,
            StudyRuntimeQuestStatus.PAUSED,
        }:
            return False
        return self.reason in {
            StudyRuntimeReason.STARTUP_BOUNDARY_NOT_READY_FOR_RESUME,
            StudyRuntimeReason.RUNTIME_REENTRY_NOT_READY_FOR_RESUME,
            StudyRuntimeReason.QUEST_PAUSED_BUT_AUTO_RESUME_DISABLED,
            StudyRuntimeReason.QUEST_INITIALIZED_BUT_AUTO_RESUME_DISABLED,
        }

    def _record_dict_extra(self, key: str, value: Any) -> None:
        self.extras[key] = self._require_dict_field(key, value)

    def set_decision(
        self,
        decision: str | StudyRuntimeDecision,
        reason: str | StudyRuntimeReason,
    ) -> None:
        resolved_decision = self._normalize_decision_field(decision)
        resolved_reason = self._normalize_reason_field(reason)
        if resolved_decision is None:
            raise ValueError("decision must not be empty")
        if resolved_reason is None:
            raise ValueError("reason must not be empty")
        self.decision = resolved_decision
        self.reason = resolved_reason

    def update_quest_runtime(
        self,
        *,
        quest_id: str | object = _UNSET,
        quest_root: str | PathLike[str] | object = _UNSET,
        quest_exists: bool | object = _UNSET,
        quest_status: str | StudyRuntimeQuestStatus | None | object = _UNSET,
    ) -> None:
        if quest_id is not _UNSET:
            self.quest_id = self._require_text_field("quest_id", quest_id)
        if quest_root is not _UNSET:
            self.quest_root = self._normalize_path_field("quest_root", quest_root)
        if quest_exists is not _UNSET:
            self.quest_exists = self._require_bool_field("quest_exists", quest_exists)
        if quest_status is not _UNSET:
            self.quest_status = self._normalize_quest_status_field(quest_status)

    def record_analysis_bundle(
        self,
        value: dict[str, Any] | StudyRuntimeAnalysisBundleResult,
    ) -> None:
        analysis_bundle = (
            value
            if isinstance(value, StudyRuntimeAnalysisBundleResult)
            else StudyRuntimeAnalysisBundleResult.from_payload(value)
        )
        self._record_dict_extra("analysis_bundle", analysis_bundle.to_dict())

    def record_runtime_overlay(
        self,
        value: dict[str, Any] | StudyRuntimeOverlayResult,
    ) -> None:
        runtime_overlay = (
            value if isinstance(value, StudyRuntimeOverlayResult) else StudyRuntimeOverlayResult.from_payload(value)
        )
        self._record_dict_extra("runtime_overlay", runtime_overlay.to_dict())

    def record_startup_contract_validation(
        self,
        value: dict[str, Any] | study_runtime_protocol.StartupContractValidation,
    ) -> None:
        startup_contract_validation = (
            value
            if isinstance(value, study_runtime_protocol.StartupContractValidation)
            else study_runtime_protocol.StartupContractValidation.from_payload(
                self._require_dict_field("startup_contract_validation", value)
            )
        )
        self._record_dict_extra("startup_contract_validation", startup_contract_validation.to_dict())

    @property
    def analysis_bundle_result(self) -> StudyRuntimeAnalysisBundleResult:
        payload = self.extras.get("analysis_bundle")
        if not isinstance(payload, dict):
            raise KeyError("analysis_bundle")
        return StudyRuntimeAnalysisBundleResult.from_payload(payload)

    @property
    def runtime_overlay_result(self) -> StudyRuntimeOverlayResult:
        payload = self.extras.get("runtime_overlay")
        if not isinstance(payload, dict):
            raise KeyError("runtime_overlay")
        return StudyRuntimeOverlayResult.from_payload(payload)

    @property
    def partial_quest_recovery_result(self) -> StudyRuntimePartialQuestRecoveryResult:
        payload = self.extras.get("partial_quest_recovery")
        if not isinstance(payload, dict):
            raise KeyError("partial_quest_recovery")
        return StudyRuntimePartialQuestRecoveryResult.from_payload(payload)

    @property
    def startup_context_sync_result(self) -> StudyRuntimeStartupContextSyncResult:
        payload = self.extras.get("startup_context_sync")
        if not isinstance(payload, dict):
            raise KeyError("startup_context_sync")
        return StudyRuntimeStartupContextSyncResult.from_payload(payload)

    @property
    def publication_supervisor_state(self) -> StudyRuntimePublicationSupervisorState:
        payload = self.extras.get("publication_supervisor_state")
        if not isinstance(payload, dict):
            raise KeyError("publication_supervisor_state")
        return StudyRuntimePublicationSupervisorState.from_payload(payload)

    def record_partial_quest_recovery(
        self,
        value: dict[str, Any] | StudyRuntimePartialQuestRecoveryResult,
    ) -> None:
        partial_quest_recovery = (
            value
            if isinstance(value, StudyRuntimePartialQuestRecoveryResult)
            else StudyRuntimePartialQuestRecoveryResult.from_payload(value)
        )
        self._record_dict_extra("partial_quest_recovery", partial_quest_recovery.to_dict())

    def record_startup_context_sync(
        self,
        value: dict[str, Any] | StudyRuntimeStartupContextSyncResult,
    ) -> None:
        startup_context_sync = (
            value
            if isinstance(value, StudyRuntimeStartupContextSyncResult)
            else StudyRuntimeStartupContextSyncResult.from_payload(value)
        )
        self._record_dict_extra("startup_context_sync", startup_context_sync.to_dict())

    def record_publication_supervisor_state(
        self,
        value: dict[str, Any] | StudyRuntimePublicationSupervisorState,
    ) -> None:
        publication_supervisor_state = (
            value
            if isinstance(value, StudyRuntimePublicationSupervisorState)
            else StudyRuntimePublicationSupervisorState.from_payload(value)
        )
        self._record_dict_extra("publication_supervisor_state", publication_supervisor_state.to_dict())

    def record_startup_hydration(
        self,
        hydration_result: dict[str, Any] | study_runtime_protocol.StartupHydrationReport,
        validation_result: dict[str, Any] | study_runtime_protocol.StartupHydrationValidationReport,
    ) -> None:
        hydration_report = (
            hydration_result
            if isinstance(hydration_result, study_runtime_protocol.StartupHydrationReport)
            else study_runtime_protocol.StartupHydrationReport.from_payload(
                self._require_dict_field("startup_hydration", hydration_result)
            )
        )
        validation_report = (
            validation_result
            if isinstance(validation_result, study_runtime_protocol.StartupHydrationValidationReport)
            else study_runtime_protocol.StartupHydrationValidationReport.from_payload(
                self._require_dict_field("startup_hydration_validation", validation_result)
            )
        )
        self._record_dict_extra("startup_hydration", hydration_report.to_dict())
        self._record_dict_extra("startup_hydration_validation", validation_report.to_dict())

    @property
    def completion_sync_result(self) -> StudyCompletionSyncResult:
        payload = self.extras.get("completion_sync")
        if not isinstance(payload, dict):
            raise KeyError("completion_sync")
        return StudyCompletionSyncResult.from_payload(payload)

    @property
    def bash_session_audit_record(self) -> StudyRuntimeAuditRecord:
        payload = self.extras.get("bash_session_audit")
        if not isinstance(payload, dict):
            raise KeyError("bash_session_audit")
        return StudyRuntimeAuditRecord.from_payload(payload)

    @property
    def runtime_liveness_audit_record(self) -> StudyRuntimeAuditRecord:
        payload = self.extras.get("runtime_liveness_audit")
        if not isinstance(payload, dict):
            raise KeyError("runtime_liveness_audit")
        return StudyRuntimeAuditRecord.from_payload(payload)

    @property
    def autonomous_runtime_notice(self) -> StudyRuntimeAutonomousRuntimeNotice:
        payload = self.extras.get("autonomous_runtime_notice")
        if not isinstance(payload, dict):
            raise KeyError("autonomous_runtime_notice")
        return StudyRuntimeAutonomousRuntimeNotice.from_payload(payload)

    @property
    def execution_owner_guard(self) -> StudyRuntimeExecutionOwnerGuard:
        payload = self.extras.get("execution_owner_guard")
        if not isinstance(payload, dict):
            raise KeyError("execution_owner_guard")
        return StudyRuntimeExecutionOwnerGuard.from_payload(payload)

    @property
    def runtime_summary_alignment(self) -> StudyRuntimeSummaryAlignment:
        payload = self.extras.get("runtime_summary_alignment")
        if not isinstance(payload, dict):
            raise KeyError("runtime_summary_alignment")
        return StudyRuntimeSummaryAlignment.from_payload(payload)

    @property
    def pending_user_interaction(self) -> StudyRuntimePendingUserInteraction:
        payload = self.extras.get("pending_user_interaction")
        if not isinstance(payload, dict):
            raise KeyError("pending_user_interaction")
        return StudyRuntimePendingUserInteraction.from_payload(payload)

    @property
    def interaction_arbitration(self) -> StudyRuntimeInteractionArbitration:
        payload = self.extras.get("interaction_arbitration")
        if not isinstance(payload, dict):
            raise KeyError("interaction_arbitration")
        return StudyRuntimeInteractionArbitration.from_payload(payload)

    @property
    def continuation_state(self) -> StudyRuntimeContinuationState:
        payload = self.extras.get("continuation_state")
        if not isinstance(payload, dict):
            raise KeyError("continuation_state")
        return StudyRuntimeContinuationState.from_payload(payload)

    def record_completion_sync(
        self,
        value: dict[str, Any] | StudyCompletionSyncResult,
    ) -> None:
        completion_sync = (
            value if isinstance(value, StudyCompletionSyncResult) else StudyCompletionSyncResult.from_payload(value)
        )
        self._record_dict_extra("completion_sync", completion_sync.to_dict())

    def record_bash_session_audit(
        self,
        value: dict[str, Any] | StudyRuntimeAuditRecord,
    ) -> None:
        bash_session_audit = (
            value if isinstance(value, StudyRuntimeAuditRecord) else StudyRuntimeAuditRecord.from_payload(value)
        )
        self._record_dict_extra("bash_session_audit", bash_session_audit.to_dict())

    def record_runtime_liveness_audit(
        self,
        value: dict[str, Any] | StudyRuntimeAuditRecord,
    ) -> None:
        runtime_liveness_audit = (
            value if isinstance(value, StudyRuntimeAuditRecord) else StudyRuntimeAuditRecord.from_payload(value)
        )
        self._record_dict_extra("runtime_liveness_audit", runtime_liveness_audit.to_dict())

    def record_supervisor_tick_audit(
        self,
        value: dict[str, Any],
    ) -> None:
        self._record_dict_extra("supervisor_tick_audit", value)

    def record_autonomous_runtime_notice(
        self,
        value: dict[str, Any] | StudyRuntimeAutonomousRuntimeNotice,
    ) -> None:
        autonomous_runtime_notice = (
            value
            if isinstance(value, StudyRuntimeAutonomousRuntimeNotice)
            else StudyRuntimeAutonomousRuntimeNotice.from_payload(value)
        )
        self._record_dict_extra("autonomous_runtime_notice", autonomous_runtime_notice.to_dict())

    def record_execution_owner_guard(
        self,
        value: dict[str, Any] | StudyRuntimeExecutionOwnerGuard,
    ) -> None:
        execution_owner_guard = (
            value
            if isinstance(value, StudyRuntimeExecutionOwnerGuard)
            else StudyRuntimeExecutionOwnerGuard.from_payload(value)
        )
        self._record_dict_extra("execution_owner_guard", execution_owner_guard.to_dict())

    def record_runtime_summary_alignment(
        self,
        value: dict[str, Any] | StudyRuntimeSummaryAlignment,
    ) -> None:
        runtime_summary_alignment = (
            value
            if isinstance(value, StudyRuntimeSummaryAlignment)
            else StudyRuntimeSummaryAlignment.from_payload(value)
        )
        self._record_dict_extra("runtime_summary_alignment", runtime_summary_alignment.to_dict())

    def record_pending_user_interaction(
        self,
        value: dict[str, Any] | StudyRuntimePendingUserInteraction,
    ) -> None:
        pending_user_interaction = (
            value
            if isinstance(value, StudyRuntimePendingUserInteraction)
            else StudyRuntimePendingUserInteraction.from_payload(value)
        )
        self._record_dict_extra("pending_user_interaction", pending_user_interaction.to_dict())

    def record_interaction_arbitration(
        self,
        value: dict[str, Any] | StudyRuntimeInteractionArbitration,
    ) -> None:
        interaction_arbitration = (
            value
            if isinstance(value, StudyRuntimeInteractionArbitration)
            else StudyRuntimeInteractionArbitration.from_payload(value)
        )
        self._record_dict_extra("interaction_arbitration", interaction_arbitration.to_dict())

    def record_continuation_state(
        self,
        value: dict[str, Any] | StudyRuntimeContinuationState,
    ) -> None:
        continuation_state = (
            value
            if isinstance(value, StudyRuntimeContinuationState)
            else StudyRuntimeContinuationState.from_payload(value)
        )
        self._record_dict_extra("continuation_state", continuation_state.to_dict())

    def record_runtime_artifacts(
        self,
        *,
        runtime_binding_path: str | PathLike[str],
        launch_report_path: str | PathLike[str],
        startup_payload_path: str | PathLike[str] | None,
    ) -> None:
        artifacts = study_runtime_protocol.StudyRuntimeArtifacts(
            runtime_binding_path=Path(self._normalize_path_field("runtime_binding_path", runtime_binding_path)),
            launch_report_path=Path(self._normalize_path_field("launch_report_path", launch_report_path)),
            startup_payload_path=(
                Path(self._normalize_path_field("startup_payload_path", startup_payload_path))
                if startup_payload_path is not None
                else None
            ),
        )
        artifact_payload = artifacts.to_dict()
        self.runtime_binding_path = str(artifacts.runtime_binding_path)
        self.runtime_binding_exists = artifacts.runtime_binding_path.exists()
        self.extras["launch_report_path"] = str(artifacts.launch_report_path)
        self.extras["startup_payload_path"] = artifact_payload["startup_payload_path"]

    def record_runtime_escalation_ref(
        self,
        value: dict[str, Any] | study_runtime_protocol.RuntimeEscalationRecordRef,
    ) -> None:
        runtime_escalation_ref = (
            value
            if isinstance(value, study_runtime_protocol.RuntimeEscalationRecordRef)
            else study_runtime_protocol.RuntimeEscalationRecordRef.from_payload(
                self._require_dict_field("runtime_escalation_ref", value)
            )
        )
        self._record_dict_extra("runtime_escalation_ref", runtime_escalation_ref.to_dict())

    def __getitem__(self, key: str) -> Any:
        payload = self.to_dict()
        if key not in payload:
            raise KeyError(key)
        return payload[key]

    def __setitem__(self, key: str, value: Any) -> None:
        if key == "schema_version":
            if not isinstance(value, int) or isinstance(value, bool):
                raise TypeError("schema_version must be int")
            self.schema_version = value
            return
        if key == "study_id":
            self.study_id = self._require_text_field("study_id", value)
            return
        if key == "study_root":
            self.study_root = self._normalize_path_field("study_root", value)
            return
        if key == "entry_mode":
            self.entry_mode = self._require_text_field("entry_mode", value)
            return
        if key == "execution":
            self.execution = self._require_dict_field("execution", value)
            return
        if key == "decision":
            self.decision = self._normalize_decision_field(value)
            return
        if key == "reason":
            self.reason = self._normalize_reason_field(value)
            return
        if key == "quest_id":
            self.update_quest_runtime(quest_id=value)
            return
        if key == "quest_root":
            self.update_quest_runtime(quest_root=value)
            return
        if key == "quest_exists":
            self.update_quest_runtime(quest_exists=value)
            return
        if key == "quest_status":
            self.update_quest_runtime(quest_status=value)
            return
        if key == "runtime_binding_path":
            self.runtime_binding_path = self._normalize_path_field("runtime_binding_path", value)
            return
        if key == "runtime_binding_exists":
            self.runtime_binding_exists = self._require_bool_field("runtime_binding_exists", value)
            return
        if key == "study_completion_contract":
            self.study_completion_state = self._normalize_study_completion_state_field(
                value,
                study_root=self.study_root,
            )
            return
        if key == "workspace_contracts":
            self.workspace_contracts = StudyRuntimeWorkspaceContractsSummary.from_payload(value).to_dict()
            return
        if key == "startup_data_readiness":
            self.startup_data_readiness = StudyRuntimeStartupDataReadinessReport.from_payload(value).to_dict()
            return
        if key == "startup_boundary_gate":
            self.startup_boundary_gate = StudyRuntimeStartupBoundaryGate.from_payload(value).to_dict()
            return
        if key == "runtime_reentry_gate":
            self.runtime_reentry_gate = StudyRuntimeReentryGate.from_payload(value).to_dict()
            return
        if key == "controller_first_policy_summary":
            self.controller_first_policy_summary = self._require_text_field("controller_first_policy_summary", value)
            return
        if key == "automation_ready_summary":
            self.automation_ready_summary = self._require_text_field("automation_ready_summary", value)
            return
        if key in self._CORE_KEYS:
            setattr(self, key, value)
            return
        self.extras[key] = value

    def __delitem__(self, key: str) -> None:
        if key in self._CORE_KEYS:
            raise KeyError(f"cannot delete core study runtime status key: {key}")
        del self.extras[key]

    def __iter__(self) -> Iterator[str]:
        yield from self.to_dict()

    def __len__(self) -> int:
        return len(self.to_dict())
