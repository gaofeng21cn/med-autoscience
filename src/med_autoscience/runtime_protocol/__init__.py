from __future__ import annotations

from importlib import import_module
from typing import Any

from med_autoscience.runtime_event_record import (
    RuntimeEventRecord,
    RuntimeEventRecordRef,
)
from med_autoscience.runtime_escalation_record import (
    RuntimeEscalationRecord,
    RuntimeEscalationRecordRef,
    RuntimeEscalationTrigger,
)
from .layout import (
    WorkspaceRuntimeLayout,
    build_workspace_runtime_layout,
    build_workspace_runtime_layout_for_profile,
    resolve_runtime_root_from_quest_root,
)

_LAZY_EXPORTS = {
    "PaperRootContext": ".topology",
    "QuestRuntimeSnapshot": ".quest_state",
    "StartupContractValidation": ".study_runtime",
    "StartupContractValidationStatus": ".study_runtime",
    "StartupHydrationReport": ".study_runtime",
    "StartupHydrationStatus": ".study_runtime",
    "StartupHydrationValidationReport": ".study_runtime",
    "StartupHydrationValidationStatus": ".study_runtime",
    "StudyRuntimeArtifacts": ".study_runtime",
    "StudyRuntimeContext": ".study_runtime",
    "archive_invalid_partial_quest_root": ".study_runtime",
    "build_hydration_payload": ".study_runtime",
    "find_latest": ".quest_state",
    "find_latest_main_result": ".quest_state",
    "find_latest_main_result_path": ".quest_state",
    "inspect_quest_runtime": ".quest_state",
    "iter_active_quests": ".quest_state",
    "load_runtime_state": ".quest_state",
    "persist_runtime_artifacts": ".study_runtime",
    "quest_status": ".quest_state",
    "read_recent_stdout_lines": ".quest_state",
    "read_runtime_escalation_record_ref": ".study_runtime",
    "read_runtime_event_record_ref": ".study_runtime",
    "resolve_active_stdout_path": ".quest_state",
    "resolve_artifact_manifest": ".paper_artifacts",
    "resolve_artifact_manifest_from_main_result": ".paper_artifacts",
    "resolve_latest_paper_root": ".paper_artifacts",
    "resolve_paper_bundle_manifest": ".paper_artifacts",
    "resolve_paper_root_context": ".topology",
    "resolve_quest_root_from_worktree_root": ".topology",
    "resolve_study_id_from_worktree_root": ".topology",
    "resolve_study_root_from_paper_root": ".topology",
    "resolve_study_root_from_quest_root": ".topology",
    "resolve_study_runtime_context": ".study_runtime",
    "resolve_study_runtime_paths": ".study_runtime",
    "resolve_submission_minimal_artifact_authority": ".paper_artifacts",
    "resolve_submission_minimal_manifest": ".paper_artifacts",
    "resolve_submission_minimal_output_paths": ".paper_artifacts",
    "resolve_worktree_root_from_paper_root": ".topology",
    "should_refresh_startup_hydration_for_runtime_hold": ".study_runtime",
    "validate_startup_contract_resolution": ".study_runtime",
    "write_launch_report": ".study_runtime",
    "write_runtime_binding": ".study_runtime",
    "write_runtime_escalation_record": ".study_runtime",
    "write_runtime_event_record": ".study_runtime",
    "write_startup_hydration_report": ".study_runtime",
    "write_startup_hydration_validation_report": ".study_runtime",
    "write_startup_payload": ".study_runtime",
    "write_study_decision_record": ".study_runtime",
}

__all__ = [
    "RuntimeEscalationRecord",
    "RuntimeEscalationRecordRef",
    "RuntimeEscalationTrigger",
    "RuntimeEventRecord",
    "RuntimeEventRecordRef",
    "WorkspaceRuntimeLayout",
    "build_workspace_runtime_layout",
    "build_workspace_runtime_layout_for_profile",
    "resolve_runtime_root_from_quest_root",
    *_LAZY_EXPORTS,
]


def __getattr__(name: str) -> Any:
    module_name = _LAZY_EXPORTS.get(name)
    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    value = getattr(import_module(module_name, __name__), name)
    globals()[name] = value
    return value
