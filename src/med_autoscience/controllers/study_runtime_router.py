from __future__ import annotations

from collections.abc import Iterator, MutableMapping
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from os import PathLike
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
    StudyCompletionContractStatus,
    StudyCompletionState,
    StudyCompletionStateStatus,
    resolve_study_completion_state,
)
from med_autoscience import study_runtime_analysis_bundle as analysis_bundle_controller
from med_autoscience.submission_targets import resolve_submission_target_contract
from med_autoscience.workspace_contracts import inspect_workspace_contracts


SUPPORTED_STARTUP_CONTRACT_PROFILES = {"paper_required_autonomous"}
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
    RUNTIME_REENTRY_NOT_READY_FOR_AUTO_START = "runtime_reentry_not_ready_for_auto_start"
    STARTUP_BOUNDARY_NOT_READY_FOR_AUTO_START = "startup_boundary_not_ready_for_auto_start"
    RUNNING_QUEST_LIVE_SESSION_AUDIT_FAILED = "running_quest_live_session_audit_failed"
    STARTUP_BOUNDARY_NOT_READY_FOR_RUNNING_QUEST = "startup_boundary_not_ready_for_running_quest"
    RUNTIME_REENTRY_NOT_READY_FOR_RUNNING_QUEST = "runtime_reentry_not_ready_for_running_quest"
    QUEST_ALREADY_RUNNING = "quest_already_running"
    STARTUP_BOUNDARY_NOT_READY_FOR_RESUME = "startup_boundary_not_ready_for_resume"
    RUNTIME_REENTRY_NOT_READY_FOR_RESUME = "runtime_reentry_not_ready_for_resume"
    QUEST_MARKED_RUNNING_BUT_NO_LIVE_SESSION = "quest_marked_running_but_no_live_session"
    QUEST_MARKED_RUNNING_BUT_AUTO_RESUME_DISABLED = "quest_marked_running_but_auto_resume_disabled"
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
    def workspace_overall_ready(self) -> bool:
        return bool(self.workspace_contracts.get("overall_ready"))

    @property
    def startup_boundary_allows_compute_stage(self) -> bool:
        return bool(self.startup_boundary_gate.get("allow_compute_stage"))

    @property
    def runtime_reentry_allows_runtime_entry(self) -> bool:
        return bool(self.runtime_reentry_gate.get("allow_runtime_entry"))

    @property
    def runtime_reentry_requires_managed_skill_audit(self) -> bool:
        return _runtime_reentry_requires_managed_skill_audit(self.runtime_reentry_gate)

    def has_unresolved_contract_for(self, study_id: str) -> bool:
        study_summary = self.startup_data_readiness.get("study_summary")
        if not isinstance(study_summary, dict):
            return False
        unresolved_contract_study_ids = study_summary.get("unresolved_contract_study_ids")
        return isinstance(unresolved_contract_study_ids, list) and study_id in unresolved_contract_study_ids

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


def _read_optional_text(path: Path | None) -> str:
    if path is None or not path.exists():
        return ""
    return path.read_text(encoding="utf-8").strip()


def _resolve_optional_path(*, anchor: Path, raw_path: object) -> Path | None:
    if not isinstance(raw_path, str) or not raw_path.strip():
        return None
    candidate = Path(raw_path).expanduser()
    if not candidate.is_absolute():
        candidate = (anchor / candidate).resolve()
    return candidate


def _serialize_submission_targets(profile: WorkspaceProfile, study_root: Path) -> list[dict[str, Any]]:
    contract = resolve_submission_target_contract(profile=profile, study_root=study_root)
    return [asdict(target) for target in contract.targets]


def _has_explicit_submission_targets(study_payload: dict[str, Any]) -> bool:
    raw_targets = study_payload.get("submission_targets")
    return isinstance(raw_targets, list) and bool(raw_targets)


def _overlay_request_kwargs(profile: WorkspaceProfile) -> dict[str, Any]:
    return {
        "skill_ids": profile.medical_overlay_skills,
        "policy_id": profile.research_route_bias_policy,
        "archetype_ids": profile.preferred_study_archetypes,
        "default_submission_targets": profile.default_submission_targets,
        "default_publication_profile": profile.default_publication_profile,
        "default_citation_style": profile.default_citation_style,
    }


def _prepare_runtime_overlay(*, profile: WorkspaceProfile, quest_root: Path) -> dict[str, Any]:
    overlay_kwargs = _overlay_request_kwargs(profile)
    authority = overlay_installer.ensure_medical_overlay(
        quest_root=profile.workspace_root,
        mode="ensure_ready",
        **overlay_kwargs,
    )
    materialization = overlay_installer.materialize_runtime_medical_overlay(
        quest_root=quest_root,
        authoritative_root=profile.workspace_root,
        **overlay_kwargs,
    )
    audit = overlay_installer.audit_runtime_medical_overlay(
        quest_root=quest_root,
        **overlay_kwargs,
    )
    return {
        "authority": authority,
        "materialization": materialization,
        "audit": audit,
    }


def _audit_runtime_overlay(*, profile: WorkspaceProfile, quest_root: Path) -> dict[str, Any]:
    return overlay_installer.audit_runtime_medical_overlay(
        quest_root=quest_root,
        **_overlay_request_kwargs(profile),
    )


def _build_startup_contract(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    study_root: Path,
    study_payload: dict[str, Any],
    execution: dict[str, Any],
) -> dict[str, Any]:
    startup_contract_profile = str(execution.get("startup_contract_profile") or "").strip()
    if startup_contract_profile not in SUPPORTED_STARTUP_CONTRACT_PROFILES:
        raise ValueError(f"unsupported startup_contract_profile: {startup_contract_profile}")

    startup_brief_path = _resolve_optional_path(anchor=study_root, raw_path=study_payload.get("startup_brief"))
    primary_question = str(study_payload.get("primary_question") or "").strip()
    title = str(study_payload.get("title") or study_id).strip()
    objectives = [primary_question] if primary_question else [f"advance study {study_id} toward submission"]
    boundary_gate = startup_boundary_gate_controller.evaluate_startup_boundary(
        profile=profile,
        study_root=study_root,
        study_payload=study_payload,
        execution=execution,
    )
    runtime_reentry_gate = runtime_reentry_gate_controller.evaluate_runtime_reentry(
        study_root=study_root,
        study_payload=study_payload,
        execution=execution,
    )
    journal_shortlist = journal_shortlist_controller.resolve_journal_shortlist(study_root=study_root)
    requested_launch_profile = str(execution.get("launch_profile") or "continue_existing_state").strip()
    requested_launch_profile = requested_launch_profile or "continue_existing_state"
    existing_brief = _read_optional_text(startup_brief_path)
    medical_analysis_contract_summary = medical_analysis_contract_controller.resolve_medical_analysis_contract_for_study(
        study_root=study_root,
        study_payload=study_payload,
        profile=profile,
    )
    medical_reporting_contract_summary = medical_reporting_contract_controller.resolve_medical_reporting_contract_for_study(
        study_root=study_root,
        study_payload=study_payload,
        profile=profile,
    )

    if not boundary_gate["allow_compute_stage"]:
        scope = "full_research"
        baseline_mode = "stop_if_insufficient"
        baseline_execution_policy = "skip_unless_blocking"
        resource_policy = "conservative"
        research_intensity = "light"
        time_budget_hours = 8
        runtime_constraints = (
            "Honor workspace data contracts. Treat the startup boundary as a hard gate: do not enter baseline, "
            "experiment, or analysis-campaign until paper framing, journal shortlist, and the minimum SCI-ready "
            "evidence package are explicit."
        )
    elif requested_launch_profile == "continue_existing_state":
        scope = "full_research"
        baseline_mode = "reuse_existing_only"
        baseline_execution_policy = "reuse_existing_only"
        resource_policy = "balanced"
        research_intensity = "balanced"
        time_budget_hours = 24
        runtime_constraints = (
            "Honor workspace data contracts and only reuse existing baseline assets after paper framing is explicit."
        )
    else:
        scope = "baseline_plus_direction"
        baseline_mode = "existing"
        baseline_execution_policy = "auto"
        resource_policy = "balanced"
        research_intensity = "balanced"
        time_budget_hours = 24
        runtime_constraints = "Honor workspace data contracts and prepare a submission-ready study."

    return {
        "schema_version": 4,
        "user_language": str(study_payload.get("user_language") or "zh").strip() or "zh",
        "need_research_paper": True,
        "research_intensity": research_intensity,
        "decision_policy": str(execution.get("decision_policy") or "autonomous").strip() or "autonomous",
        "launch_mode": "custom",
        "custom_profile": boundary_gate["effective_custom_profile"],
        "scope": scope,
        "baseline_mode": baseline_mode,
        "baseline_execution_policy": baseline_execution_policy,
        "resource_policy": resource_policy,
        "time_budget_hours": time_budget_hours,
        "git_strategy": "semantic_head_plus_controlled_integration",
        "runtime_constraints": runtime_constraints,
        "objectives": objectives,
        "baseline_urls": [],
        "paper_urls": list(study_payload.get("paper_urls") or []),
        "entry_state_summary": f"Study root: {study_root}",
        "review_summary": "",
        "controller_first_policy_summary": render_controller_first_summary(),
        "automation_ready_summary": render_automation_ready_summary(),
        "custom_brief": startup_boundary_gate_controller.render_boundary_custom_brief(
            existing_brief=existing_brief,
            boundary_gate=boundary_gate,
        ),
        "required_first_anchor": boundary_gate["required_first_anchor"],
        "legacy_code_execution_allowed": boundary_gate["legacy_code_execution_allowed"],
        "startup_boundary_gate": boundary_gate,
        "runtime_reentry_gate": runtime_reentry_gate,
        "journal_shortlist": journal_shortlist,
        "medical_analysis_contract_summary": medical_analysis_contract_summary,
        "medical_reporting_contract_summary": medical_reporting_contract_summary,
        "reporting_guideline_family": medical_reporting_contract_summary.get("reporting_guideline_family")
        if medical_reporting_contract_summary.get("status") == "resolved"
        else None,
        "submission_targets": _serialize_submission_targets(profile, study_root)
        if _has_explicit_submission_targets(study_payload)
        else [],
    }


def _build_create_payload(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    study_root: Path,
    study_payload: dict[str, Any],
    execution: dict[str, Any],
) -> dict[str, Any]:
    title = str(study_payload.get("title") or study_id).strip() or study_id
    goal = str(study_payload.get("primary_question") or title).strip() or title
    startup_contract = _build_startup_contract(
        profile=profile,
        study_id=study_id,
        study_root=study_root,
        study_payload=study_payload,
        execution=execution,
    )
    return {
        "title": title,
        "goal": goal,
        "quest_id": str(execution.get("quest_id") or study_id).strip() or study_id,
        "source": "med_autoscience.study_runtime_router",
        "auto_start": bool(
            (
                (
                    startup_contract.get("startup_boundary_gate")
                    if isinstance(startup_contract.get("startup_boundary_gate"), dict)
                    else {}
                ).get("allow_compute_stage")
            )
            and (
                (
                    startup_contract.get("runtime_reentry_gate")
                    if isinstance(startup_contract.get("runtime_reentry_gate"), dict)
                    else {}
                ).get("allow_runtime_entry", True)
            )
        ),
        "startup_contract": startup_contract,
    }


def _runtime_reentry_requires_startup_hydration(runtime_reentry_gate: dict[str, Any]) -> bool:
    return runtime_reentry_gate.get("require_startup_hydration") is True


def _runtime_reentry_requires_managed_skill_audit(runtime_reentry_gate: dict[str, Any]) -> bool:
    return runtime_reentry_gate.get("require_managed_skill_audit") is True


def _run_startup_hydration(
    *,
    quest_root: Path,
    create_payload: dict[str, Any],
) -> tuple[
    study_runtime_protocol.StartupHydrationReport,
    study_runtime_protocol.StartupHydrationValidationReport,
]:
    hydration_payload = study_runtime_protocol.build_hydration_payload(create_payload=create_payload)
    hydration_result = quest_hydration_controller.run_hydration(
        quest_root=quest_root,
        hydration_payload=hydration_payload,
    )
    validation_result = startup_hydration_validation_controller.run_validation(quest_root=quest_root)
    return (
        study_runtime_protocol.StartupHydrationReport.from_payload(
            StudyRuntimeStatus._require_dict_field("startup_hydration", hydration_result)
        ),
        study_runtime_protocol.StartupHydrationValidationReport.from_payload(
            StudyRuntimeStatus._require_dict_field("startup_hydration_validation", validation_result)
        ),
    )


def _sync_existing_quest_startup_context(
    *,
    runtime_root: Path,
    quest_id: str,
    create_payload: dict[str, Any],
) -> dict[str, Any]:
    startup_contract = create_payload.get("startup_contract")
    if not isinstance(startup_contract, dict):
        raise ValueError("create payload missing startup_contract")
    return med_deepscientist_transport.update_quest_startup_context(
        runtime_root=runtime_root,
        quest_id=quest_id,
        startup_contract=dict(startup_contract),
    )


def _study_completion_state(*, study_root: Path) -> StudyCompletionState:
    return resolve_study_completion_state(study_root=study_root)


def _record_quest_runtime_audits(
    *,
    status: StudyRuntimeStatus,
    quest_runtime: quest_state.QuestRuntimeSnapshot,
) -> quest_state.QuestRuntimeLivenessStatus:
    runtime_liveness_audit = StudyRuntimeAuditRecord.from_payload(dict(quest_runtime.runtime_liveness_audit or {}))
    bash_session_audit = StudyRuntimeAuditRecord.from_payload(dict(quest_runtime.bash_session_audit or {}))
    status.record_runtime_liveness_audit(runtime_liveness_audit)
    status.record_bash_session_audit(bash_session_audit)
    return quest_runtime.runtime_liveness_status


def _build_study_completion_request_message(
    *,
    study_id: str,
    study_root: Path,
    completion_state: StudyCompletionState,
) -> str:
    contract = completion_state.contract
    summary = contract.summary.strip() if contract is not None else ""
    evidence_paths = list(contract.evidence_paths) if contract is not None else []
    lines = [
        f"Managed study `{study_id}` already has an explicit study-level completion contract.",
        f"Study root: `{study_root}`",
        f"Completion summary: {summary}",
    ]
    if evidence_paths:
        lines.append("Evidence paths:")
        lines.extend(f"- `{item}`" for item in evidence_paths[:12])
    lines.append("Please record explicit quest-completion approval so the managed runtime can close this study cleanly.")
    return "\n".join(lines)


def _sync_study_completion(
    *,
    runtime_root: Path,
    quest_id: str,
    study_id: str,
    study_root: Path,
    completion_state: StudyCompletionState,
    source: str,
) -> dict[str, Any]:
    contract = completion_state.contract
    summary = contract.summary.strip() if contract is not None else ""
    approval_text = contract.user_approval_text.strip() if contract is not None else ""
    if not summary or not approval_text:
        raise ValueError("study completion sync requires summary and user approval text")
    return med_deepscientist_transport.sync_completion_with_approval(
        runtime_root=runtime_root,
        quest_id=quest_id,
        decision_request_payload={
            "kind": "decision_request",
            "message": _build_study_completion_request_message(
                study_id=study_id,
                study_root=study_root,
                completion_state=completion_state,
            ),
            "reply_mode": "blocking",
            "deliver_to_bound_conversations": False,
            "include_recent_inbound_messages": False,
            "reply_schema": {"decision_type": "quest_completion_approval"},
        },
        approval_text=approval_text,
        summary=summary,
        source=source,
    )


def _status_state(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    study_root: Path,
    study_payload: dict[str, Any],
    entry_mode: str | None,
) -> StudyRuntimeStatus:
    execution = _execution_payload(study_payload)
    selected_entry_mode = str(entry_mode or execution.get("default_entry_mode") or "full_research").strip() or "full_research"
    quest_id = str(execution.get("quest_id") or study_id).strip() or study_id
    runtime_context = study_runtime_protocol.resolve_study_runtime_context(
        profile=profile,
        study_root=study_root,
        study_id=study_id,
        quest_id=quest_id,
    )
    runtime_root = runtime_context.runtime_root
    quest_root = runtime_context.quest_root
    runtime_binding_path = runtime_context.runtime_binding_path
    quest_runtime = quest_state.inspect_quest_runtime(quest_root)
    quest_exists = quest_runtime.quest_exists
    quest_status = StudyRuntimeStatus._normalize_quest_status_field(quest_runtime.quest_status)
    if quest_status in _LIVE_QUEST_STATUSES:
        runtime_liveness_audit = med_deepscientist_transport.inspect_quest_live_execution(
            runtime_root=runtime_root,
            quest_id=quest_id,
        )
        quest_runtime = quest_runtime.with_runtime_liveness_audit(runtime_liveness_audit).with_bash_session_audit(
            dict(runtime_liveness_audit.get("bash_session_audit") or {})
        )
    contracts = inspect_workspace_contracts(profile)
    readiness = startup_data_readiness_controller.startup_data_readiness(workspace_root=profile.workspace_root)
    startup_boundary_gate = startup_boundary_gate_controller.evaluate_startup_boundary(
        profile=profile,
        study_root=study_root,
        study_payload=study_payload,
        execution=execution,
    )
    runtime_reentry_gate = runtime_reentry_gate_controller.evaluate_runtime_reentry(
        study_root=study_root,
        study_payload=study_payload,
        execution=execution,
        quest_root=quest_root if quest_exists else None,
        enforce_startup_hydration=quest_status in _LIVE_QUEST_STATUSES,
    )
    completion_state = _study_completion_state(study_root=study_root)

    result = StudyRuntimeStatus(
        schema_version=1,
        study_id=study_id,
        study_root=str(study_root),
        entry_mode=selected_entry_mode,
        execution=execution,
        quest_id=quest_id,
        quest_root=str(quest_root),
        quest_exists=quest_exists,
        quest_status=quest_status,
        runtime_binding_path=str(runtime_binding_path),
        runtime_binding_exists=runtime_binding_path.exists(),
        workspace_contracts=contracts,
        startup_data_readiness=readiness,
        startup_boundary_gate=startup_boundary_gate,
        runtime_reentry_gate=runtime_reentry_gate,
        study_completion_state=completion_state,
        controller_first_policy_summary=render_controller_first_summary(),
        automation_ready_summary=render_automation_ready_summary(),
    )

    if str(execution.get("engine") or "").strip() != "med-deepscientist":
        result.set_decision(
            StudyRuntimeDecision.LIGHTWEIGHT,
            StudyRuntimeReason.STUDY_EXECUTION_NOT_MED_DEEPSCIENTIST,
        )
        return result

    auto_entry = str(execution.get("auto_entry") or "").strip()
    default_entry_mode = str(execution.get("default_entry_mode") or "full_research").strip() or "full_research"
    if auto_entry != "on_managed_research_intent":
        result.set_decision(
            StudyRuntimeDecision.LIGHTWEIGHT,
            StudyRuntimeReason.STUDY_EXECUTION_NOT_MANAGED,
        )
        return result
    if selected_entry_mode != default_entry_mode:
        result.set_decision(
            StudyRuntimeDecision.LIGHTWEIGHT,
            StudyRuntimeReason.ENTRY_MODE_NOT_MANAGED,
        )
        return result

    completion_contract_status = completion_state.status
    if completion_contract_status in {
        StudyCompletionStateStatus.INVALID,
        StudyCompletionStateStatus.INCOMPLETE,
    }:
        result.set_decision(
            StudyRuntimeDecision.BLOCKED,
            StudyRuntimeReason.STUDY_COMPLETION_CONTRACT_NOT_READY,
        )
        return result
    if completion_state.ready:
        if not quest_exists:
            result.set_decision(
                StudyRuntimeDecision.COMPLETED,
                StudyRuntimeReason.STUDY_COMPLETION_DECLARED_WITHOUT_MANAGED_QUEST,
            )
            return result
        if quest_status == StudyRuntimeQuestStatus.COMPLETED:
            result.set_decision(
                StudyRuntimeDecision.COMPLETED,
                StudyRuntimeReason.QUEST_ALREADY_COMPLETED,
            )
            return result
        if quest_status in _LIVE_QUEST_STATUSES:
            audit_status = _record_quest_runtime_audits(status=result, quest_runtime=quest_runtime)
            if audit_status is quest_state.QuestRuntimeLivenessStatus.UNKNOWN:
                result.set_decision(
                    StudyRuntimeDecision.BLOCKED,
                    StudyRuntimeReason.STUDY_COMPLETION_LIVE_RUNTIME_AUDIT_FAILED,
                )
            elif audit_status is quest_state.QuestRuntimeLivenessStatus.LIVE:
                result.set_decision(
                    StudyRuntimeDecision.PAUSE_AND_COMPLETE,
                    StudyRuntimeReason.STUDY_COMPLETION_READY,
                )
            else:
                result.set_decision(
                    StudyRuntimeDecision.SYNC_COMPLETION,
                    StudyRuntimeReason.STUDY_COMPLETION_READY,
                )
            return result
        result.set_decision(
            StudyRuntimeDecision.SYNC_COMPLETION,
            StudyRuntimeReason.STUDY_COMPLETION_READY,
        )
        return result

    if not result.workspace_overall_ready:
        result.set_decision(
            StudyRuntimeDecision.BLOCKED,
            StudyRuntimeReason.WORKSPACE_CONTRACT_NOT_READY,
        )
        return result

    if result.has_unresolved_contract_for(study_id):
        result.set_decision(
            StudyRuntimeDecision.BLOCKED,
            StudyRuntimeReason.STUDY_DATA_READINESS_BLOCKED,
        )
        return result

    startup_contract_validation = study_runtime_protocol.validate_startup_contract_resolution(
        startup_contract=_build_startup_contract(
            profile=profile,
            study_id=study_id,
            study_root=study_root,
            study_payload=study_payload,
            execution=execution,
        )
    )
    result.record_startup_contract_validation(startup_contract_validation.to_dict())
    if startup_contract_validation.status is not study_runtime_protocol.StartupContractValidationStatus.CLEAR:
        result.set_decision(
            StudyRuntimeDecision.BLOCKED,
            StudyRuntimeReason.STARTUP_CONTRACT_RESOLUTION_FAILED,
        )
        return result

    if not quest_exists:
        if result.startup_boundary_allows_compute_stage:
            if result.runtime_reentry_allows_runtime_entry:
                result.set_decision(
                    StudyRuntimeDecision.CREATE_AND_START,
                    StudyRuntimeReason.QUEST_MISSING,
                )
            else:
                result.set_decision(
                    StudyRuntimeDecision.BLOCKED,
                    StudyRuntimeReason.RUNTIME_REENTRY_NOT_READY_FOR_AUTO_START,
                )
        else:
            result.set_decision(
                StudyRuntimeDecision.CREATE_ONLY,
                StudyRuntimeReason.STARTUP_BOUNDARY_NOT_READY_FOR_AUTO_START,
            )
        return result

    if quest_status in _LIVE_QUEST_STATUSES:
        audit_status = _record_quest_runtime_audits(status=result, quest_runtime=quest_runtime)
        if audit_status is quest_state.QuestRuntimeLivenessStatus.UNKNOWN:
            result.set_decision(
                StudyRuntimeDecision.BLOCKED,
                StudyRuntimeReason.RUNNING_QUEST_LIVE_SESSION_AUDIT_FAILED,
            )
        elif audit_status is quest_state.QuestRuntimeLivenessStatus.LIVE:
            if not result.startup_boundary_allows_compute_stage:
                result.set_decision(
                    StudyRuntimeDecision.PAUSE,
                    StudyRuntimeReason.STARTUP_BOUNDARY_NOT_READY_FOR_RUNNING_QUEST,
                )
            elif not result.runtime_reentry_allows_runtime_entry:
                result.set_decision(
                    StudyRuntimeDecision.PAUSE,
                    StudyRuntimeReason.RUNTIME_REENTRY_NOT_READY_FOR_RUNNING_QUEST,
                )
            else:
                result.set_decision(
                    StudyRuntimeDecision.NOOP,
                    StudyRuntimeReason.QUEST_ALREADY_RUNNING,
                )
        elif not result.startup_boundary_allows_compute_stage:
            result.set_decision(
                StudyRuntimeDecision.BLOCKED,
                StudyRuntimeReason.STARTUP_BOUNDARY_NOT_READY_FOR_RESUME,
            )
        elif not result.runtime_reentry_allows_runtime_entry:
            result.set_decision(
                StudyRuntimeDecision.BLOCKED,
                StudyRuntimeReason.RUNTIME_REENTRY_NOT_READY_FOR_RESUME,
            )
        elif execution.get("auto_resume") is True:
            result.set_decision(
                StudyRuntimeDecision.RESUME,
                StudyRuntimeReason.QUEST_MARKED_RUNNING_BUT_NO_LIVE_SESSION,
            )
        else:
            result.set_decision(
                StudyRuntimeDecision.BLOCKED,
                StudyRuntimeReason.QUEST_MARKED_RUNNING_BUT_AUTO_RESUME_DISABLED,
            )
        return result

    if quest_status in _RESUMABLE_QUEST_STATUSES:
        if not result.startup_boundary_allows_compute_stage:
            result.set_decision(
                StudyRuntimeDecision.BLOCKED,
                StudyRuntimeReason.STARTUP_BOUNDARY_NOT_READY_FOR_RESUME,
            )
            return result
        if not result.runtime_reentry_allows_runtime_entry:
            result.set_decision(
                StudyRuntimeDecision.BLOCKED,
                StudyRuntimeReason.RUNTIME_REENTRY_NOT_READY_FOR_RESUME,
            )
            return result
        if execution.get("auto_resume") is True:
            resumable_reason = {
                StudyRuntimeQuestStatus.PAUSED: StudyRuntimeReason.QUEST_PAUSED,
                StudyRuntimeQuestStatus.STOPPED: StudyRuntimeReason.QUEST_STOPPED,
            }.get(quest_status, StudyRuntimeReason.QUEST_INITIALIZED_WAITING_TO_START)
            result.set_decision(
                StudyRuntimeDecision.RESUME,
                resumable_reason,
            )
        else:
            blocked_reason = {
                StudyRuntimeQuestStatus.PAUSED: StudyRuntimeReason.QUEST_PAUSED_BUT_AUTO_RESUME_DISABLED,
                StudyRuntimeQuestStatus.STOPPED: StudyRuntimeReason.QUEST_STOPPED_BUT_AUTO_RESUME_DISABLED,
            }.get(quest_status, StudyRuntimeReason.QUEST_INITIALIZED_BUT_AUTO_RESUME_DISABLED)
            result.set_decision(
                StudyRuntimeDecision.BLOCKED,
                blocked_reason,
            )
        return result

    result.set_decision(
        StudyRuntimeDecision.BLOCKED,
        StudyRuntimeReason.QUEST_EXISTS_WITH_NON_RESUMABLE_STATE,
    )
    return result


def _status_payload(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    study_root: Path,
    study_payload: dict[str, Any],
    entry_mode: str | None,
) -> dict[str, Any]:
    return _status_state(
        profile=profile,
        study_id=study_id,
        study_root=study_root,
        study_payload=study_payload,
        entry_mode=entry_mode,
    ).to_dict()


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
