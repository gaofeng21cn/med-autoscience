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

from .enums_and_audits import (
    __all__,
    _UNSET,
    _absent_study_completion_state,
    StudyRuntimeDecision,
    StudyRuntimeReason,
    StudyRuntimeQuestStatus,
    StudyRuntimeBindingAction,
    StudyRuntimeDaemonStep,
    StudyRuntimeAuditStatus,
    _LIVE_QUEST_STATUSES,
    _RESUMABLE_QUEST_STATUSES,
    StudyRuntimeAuditRecord,
)
from .enums_and_audits import (
    StudyRuntimeAutonomousRuntimeNotice,
    StudyRuntimeSummaryAlignment,
    StudyRuntimeExecutionOwnerGuard,
    StudyRuntimePendingUserInteraction,
    StudyRuntimeInteractionArbitration,
    StudyRuntimeContinuationState,
)
from .runtime_result_types import (
    StudyRuntimeAnalysisBundleResult,
    StudyRuntimeOverlayAudit,
    StudyRuntimeOverlayResult,
    StudyRuntimeStartupContextSyncResult,
    StudyRuntimePartialQuestRecoveryResult,
    StudyRuntimeWorkspaceContractsSummary,
    StudyRuntimeStartupDataReadinessReport,
    StudyRuntimeStartupBoundaryGate,
    StudyRuntimeReentryGate,
    StudyRuntimePublicationSupervisorState,
    StudyRuntimeProgressProjection,
    StudyCompletionSyncResult,
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

    @property
    def progress_projection_result(self) -> StudyRuntimeProgressProjection | None:
        payload = self.extras.get("progress_projection")
        if payload is None:
            return None
        if not isinstance(payload, dict):
            raise TypeError("progress_projection must be dict")
        return StudyRuntimeProgressProjection.from_payload(payload)

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

    def record_progress_projection(
        self,
        value: dict[str, Any] | StudyRuntimeProgressProjection,
    ) -> None:
        progress_projection = (
            value
            if isinstance(value, StudyRuntimeProgressProjection)
            else StudyRuntimeProgressProjection.from_payload(value)
        )
        self._record_dict_extra("progress_projection", progress_projection.to_dict())

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

    def record_runtime_event_ref(
        self,
        value: dict[str, Any] | study_runtime_protocol.RuntimeEventRecordRef,
    ) -> None:
        runtime_event_ref = (
            value
            if isinstance(value, study_runtime_protocol.RuntimeEventRecordRef)
            else study_runtime_protocol.RuntimeEventRecordRef.from_payload(
                self._require_dict_field("runtime_event_ref", value)
            )
        )
        self._record_dict_extra("runtime_event_ref", runtime_event_ref.to_dict())

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
