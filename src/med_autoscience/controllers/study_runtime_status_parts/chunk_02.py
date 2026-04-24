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

from .chunk_01 import (
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
from .chunk_01 import (
    StudyRuntimeAutonomousRuntimeNotice,
    StudyRuntimeSummaryAlignment,
    StudyRuntimeExecutionOwnerGuard,
    StudyRuntimePendingUserInteraction,
    StudyRuntimeInteractionArbitration,
    StudyRuntimeContinuationState,
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
class StudyRuntimeProgressProjection:
    study_id: str
    current_stage: str
    current_stage_summary: str
    paper_stage: str | None
    paper_stage_summary: str
    next_system_action: str
    needs_physician_decision: bool
    payload: dict[str, Any]

    def __post_init__(self) -> None:
        for field_name in ("study_id", "current_stage", "current_stage_summary", "paper_stage_summary", "next_system_action"):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise TypeError(f"study runtime progress projection {field_name} must be non-empty str")
        if self.paper_stage is not None and not isinstance(self.paper_stage, str):
            raise TypeError("study runtime progress projection paper_stage must be str or None")
        if not isinstance(self.needs_physician_decision, bool):
            raise TypeError("study runtime progress projection needs_physician_decision must be bool")
        object.__setattr__(self, "payload", dict(self.payload))

    def to_dict(self) -> dict[str, Any]:
        return dict(self.payload)

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "StudyRuntimeProgressProjection":
        if not isinstance(payload, dict):
            raise TypeError("study runtime progress projection payload must be a mapping")
        latest_events = payload.get("latest_events")
        if latest_events is not None and not isinstance(latest_events, list):
            raise ValueError("study runtime progress projection latest_events must be a list")
        current_blockers = payload.get("current_blockers")
        if current_blockers is not None and not isinstance(current_blockers, list):
            raise ValueError("study runtime progress projection current_blockers must be a list")
        supervision = payload.get("supervision")
        if supervision is not None and not isinstance(supervision, dict):
            raise ValueError("study runtime progress projection supervision must be a mapping")
        refs = payload.get("refs")
        if refs is not None and not isinstance(refs, dict):
            raise ValueError("study runtime progress projection refs must be a mapping")
        needs_physician_decision = payload.get("needs_physician_decision")
        if not isinstance(needs_physician_decision, bool):
            raise TypeError("study runtime progress projection needs_physician_decision must be bool")
        paper_stage = str(payload.get("paper_stage") or "").strip() or None
        return cls(
            study_id=str(payload.get("study_id") or ""),
            current_stage=str(payload.get("current_stage") or ""),
            current_stage_summary=str(payload.get("current_stage_summary") or ""),
            paper_stage=paper_stage,
            paper_stage_summary=str(payload.get("paper_stage_summary") or ""),
            next_system_action=str(payload.get("next_system_action") or ""),
            needs_physician_decision=needs_physician_decision,
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
