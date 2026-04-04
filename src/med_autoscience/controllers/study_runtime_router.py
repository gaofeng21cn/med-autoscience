from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

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
    _build_study_completion_request_message,
    _study_completion_state,
    _sync_study_completion,
)
from med_autoscience.controllers.study_runtime_decision import (
    _record_quest_runtime_audits,
    _status_payload,
    _status_state,
)
from med_autoscience.controllers.study_runtime_execution import (
    _build_context_create_payload,
    _build_execution_context,
    _execute_blocked_refresh_runtime_decision,
    _execute_completion_runtime_decision,
    _execute_create_runtime_decision,
    _execute_pause_runtime_decision,
    _execute_resume_runtime_decision,
    _execute_runtime_decision,
    _run_runtime_preflight,
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
