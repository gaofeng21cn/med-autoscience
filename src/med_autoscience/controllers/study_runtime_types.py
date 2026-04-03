from __future__ import annotations

from collections.abc import Iterator, MutableMapping
from dataclasses import dataclass, field
from enum import StrEnum
from os import PathLike
from pathlib import Path
from typing import Any

from med_autoscience.profiles import WorkspaceProfile
from med_autoscience.runtime_protocol import study_runtime as study_runtime_protocol
from med_autoscience.study_completion import (
    StudyCompletionState,
    StudyCompletionStateStatus,
)

__all__ = [
    "StudyCompletionSyncResult",
    "StudyRuntimeAnalysisBundleResult",
    "StudyRuntimeAuditRecord",
    "StudyRuntimeAuditStatus",
    "StudyRuntimeBindingAction",
    "StudyRuntimeDaemonStep",
    "StudyRuntimeDecision",
    "StudyRuntimeExecutionContext",
    "StudyRuntimeExecutionOutcome",
    "StudyRuntimeOverlayAudit",
    "StudyRuntimeOverlayResult",
    "StudyRuntimePartialQuestRecoveryResult",
    "StudyRuntimeQuestStatus",
    "StudyRuntimeReason",
    "StudyRuntimeReentryGate",
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
    RESUME_REQUEST_FAILED = "resume_request_failed"
    QUEST_MARKED_RUNNING_BUT_AUTO_RESUME_DISABLED = "quest_marked_running_but_auto_resume_disabled"
    QUEST_WAITING_FOR_USER = "quest_waiting_for_user"
    QUEST_WAITING_FOR_SUBMISSION_METADATA = "quest_waiting_for_submission_metadata"
    QUEST_WAITING_FOR_SUBMISSION_METADATA_BUT_AUTO_RESUME_DISABLED = (
        "quest_waiting_for_submission_metadata_but_auto_resume_disabled"
    )
    QUEST_PAUSED = "quest_paused"
    QUEST_STOPPED = "quest_stopped"
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
    StudyRuntimeQuestStatus.STOPPED,
}


_LIVE_QUEST_STATUSES = {
    StudyRuntimeQuestStatus.RUNNING,
    StudyRuntimeQuestStatus.ACTIVE,
}
_RESUMABLE_QUEST_STATUSES = {
    StudyRuntimeQuestStatus.PAUSED,
    StudyRuntimeQuestStatus.IDLE,
    StudyRuntimeQuestStatus.CREATED,
    StudyRuntimeQuestStatus.STOPPED,
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
        snapshot = payload.get("snapshot")
        if snapshot is not None and not isinstance(snapshot, dict):
            raise ValueError("study runtime startup context sync snapshot must be a mapping")
        return cls(ok=ok, payload=dict(payload))


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
