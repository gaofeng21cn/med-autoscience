from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from med_autoscience import runtime_backend as runtime_backend_contract
from med_autoscience import study_runtime_analysis_bundle as analysis_bundle_controller
from med_autoscience.controllers import (
    journal_shortlist as journal_shortlist_controller,
    medical_analysis_contract as medical_analysis_contract_controller,
    medical_reporting_contract as medical_reporting_contract_controller,
    quest_hydration as quest_hydration_controller,
    runtime_reentry_gate as runtime_reentry_gate_controller,
    startup_boundary_gate as startup_boundary_gate_controller,
    startup_data_readiness as startup_data_readiness_controller,
    startup_hydration_validation as startup_hydration_validation_controller,
)
from med_autoscience.controllers.study_runtime_completion import (
    _study_completion_state,
    _sync_study_completion,
)
from med_autoscience.controllers.study_runtime_decision import (
    _record_quest_runtime_audits,
    _status_payload,
    _status_state,
)
from med_autoscience.controllers.study_runtime_execution import (
    _record_autonomous_runtime_notice_if_required,
    _build_context_create_payload,
    _build_execution_context,
    _enable_explicit_stopped_relaunch_if_requested,
    _execute_blocked_refresh_runtime_decision,
    _execute_completion_runtime_decision,
    _execute_create_runtime_decision,
    _execute_pause_runtime_decision,
    _execute_resume_runtime_decision,
    _execute_runtime_decision,
    _persist_runtime_artifacts,
    _run_runtime_preflight,
)
from med_autoscience.controllers.study_runtime_resolution import (
    _execution_payload,
    _load_yaml_dict,
    _resolve_study,
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
from med_autoscience.controllers.study_runtime_transport import (
    _create_quest,
    _inspect_quest_live_execution,
    _pause_quest,
    _resume_quest,
    _update_quest_startup_context,
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
    StudyRuntimeInteractionArbitration,
    StudyRuntimeOverlayAudit,
    StudyRuntimeOverlayResult,
    StudyRuntimePendingUserInteraction,
    StudyRuntimePartialQuestRecoveryResult,
    StudyRuntimePublicationSupervisorState,
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
from med_autoscience.overlay import installer as overlay_installer
from med_autoscience.policies.automation_ready import render_automation_ready_summary
from med_autoscience.policies.controller_first import render_controller_first_summary
from med_autoscience.profiles import WorkspaceProfile
from med_autoscience.runtime_protocol import quest_state
from med_autoscience.runtime_protocol import study_runtime as study_runtime_protocol
from med_autoscience.study_completion import (
    StudyCompletionState,
    StudyCompletionStateStatus,
    resolve_study_completion_state,
)
from med_autoscience.workspace_contracts import inspect_workspace_contracts

managed_runtime_backend = runtime_backend_contract.get_managed_runtime_backend(
    runtime_backend_contract.DEFAULT_MANAGED_RUNTIME_BACKEND_ID
)
# 兼容旧测试与旧内部入口；当前主线代码应优先通过 managed_runtime_backend contract 访问 backend。
med_deepscientist_transport = managed_runtime_backend


def _default_managed_runtime_backend():
    backend = globals().get("managed_runtime_backend")
    if backend is not None:
        return backend
    return globals()["med_deepscientist_transport"]


def _managed_runtime_backend_for_execution(execution: dict[str, Any] | None):
    default_backend = _default_managed_runtime_backend()
    explicit_backend_id = runtime_backend_contract.explicit_runtime_backend_id(execution)
    if explicit_backend_id is not None:
        if explicit_backend_id == getattr(default_backend, "BACKEND_ID", None):
            return default_backend
        return runtime_backend_contract.try_get_managed_runtime_backend(explicit_backend_id)
    backend = runtime_backend_contract.resolve_managed_runtime_backend(execution)
    if backend is None:
        return None
    if getattr(backend, "BACKEND_ID", None) == getattr(default_backend, "BACKEND_ID", None):
        return default_backend
    return backend


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _timestamp_slug() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def study_runtime_status(
    *,
    profile: WorkspaceProfile,
    study_id: str | None = None,
    study_root: Path | None = None,
    entry_mode: str | None = None,
    sync_runtime_summary: bool = True,
    include_progress_projection: bool = True,
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
        sync_runtime_summary=sync_runtime_summary,
        include_progress_projection=include_progress_projection,
    )


def ensure_study_runtime(
    *,
    profile: WorkspaceProfile,
    study_id: str | None = None,
    study_root: Path | None = None,
    entry_mode: str | None = None,
    allow_stopped_relaunch: bool = False,
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
        sync_runtime_summary=False,
    )
    if allow_stopped_relaunch:
        _enable_explicit_stopped_relaunch_if_requested(status=status)
    _run_runtime_preflight(status=status, context=context)
    outcome = _execute_runtime_decision(status=status, context=context)
    _persist_runtime_artifacts(
        status=status,
        context=context,
        outcome=outcome,
        force=force,
        source=source,
    )
    return status.to_dict()


def study_outer_loop_tick(**kwargs: Any) -> dict[str, Any]:
    from med_autoscience.controllers import study_outer_loop

    return study_outer_loop.study_outer_loop_tick(**kwargs)
