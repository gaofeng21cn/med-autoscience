from __future__ import annotations

from pathlib import Path
from typing import Any
from typing import Callable

from med_autoscience.profiles import WorkspaceProfile
from med_autoscience.runtime_protocol import study_runtime as study_runtime_protocol
from med_autoscience.study_decision_record import StudyDecisionActionType, StudyDecisionControllerAction


EnsureStudyRuntime = Callable[..., dict[str, Any]]
RuntimeExecutionPayload = Callable[..., dict[str, Any]]
RuntimeBackendForExecution = Callable[..., Any]
DefaultRuntimeBackend = Callable[[], Any]
RunGateClearingBatch = Callable[..., dict[str, Any]]
RunQualityRepairBatch = Callable[..., dict[str, Any]]


def execute_controller_action(
    *,
    action: StudyDecisionControllerAction,
    profile: WorkspaceProfile,
    study_id: str,
    study_root: Path,
    quest_id: str,
    source: str,
    ensure_study_runtime_fn: EnsureStudyRuntime,
    execution_payload_fn: RuntimeExecutionPayload,
    load_yaml_dict_fn: Callable[[Path], dict[str, Any]],
    managed_runtime_backend_for_execution_fn: RuntimeBackendForExecution,
    default_managed_runtime_backend_fn: DefaultRuntimeBackend,
    run_gate_clearing_batch_fn: RunGateClearingBatch,
    run_quality_repair_batch_fn: RunQualityRepairBatch,
) -> dict[str, Any]:
    if action.action_type is StudyDecisionActionType.ENSURE_STUDY_RUNTIME:
        result = ensure_study_runtime_fn(
            profile=profile,
            study_id=study_id,
            study_root=study_root,
            force=False,
            source=source,
        )
    elif action.action_type is StudyDecisionActionType.ENSURE_STUDY_RUNTIME_RELAUNCH_STOPPED:
        result = ensure_study_runtime_fn(
            profile=profile,
            study_id=study_id,
            study_root=study_root,
            allow_stopped_relaunch=True,
            force=False,
            source=source,
        )
    elif action.action_type in {StudyDecisionActionType.PAUSE_RUNTIME, StudyDecisionActionType.STOP_RUNTIME}:
        execution = execution_payload_fn(
            load_yaml_dict_fn(study_root / "study.yaml"),
            profile=profile,
        )
        runtime_context = study_runtime_protocol.resolve_study_runtime_context(
            profile=profile,
            study_root=study_root,
            study_id=study_id,
            quest_id=quest_id,
        )
        managed_runtime_backend = (
            managed_runtime_backend_for_execution_fn(
                execution,
                profile=profile,
                runtime_root=runtime_context.runtime_root,
            )
            or default_managed_runtime_backend_fn()
        )
        if action.action_type is StudyDecisionActionType.PAUSE_RUNTIME:
            result = managed_runtime_backend.pause_quest(
                runtime_root=runtime_context.runtime_root,
                quest_id=quest_id,
                source=source,
            )
        else:
            result = managed_runtime_backend.stop_quest(
                runtime_root=runtime_context.runtime_root,
                quest_id=quest_id,
                source=source,
            )
    elif action.action_type is StudyDecisionActionType.RUN_GATE_CLEARING_BATCH:
        result = run_gate_clearing_batch_fn(
            profile=profile,
            study_id=study_id,
            study_root=study_root,
            quest_id=quest_id,
            source=source,
        )
    elif action.action_type is StudyDecisionActionType.RUN_QUALITY_REPAIR_BATCH:
        result = run_quality_repair_batch_fn(
            profile=profile,
            study_id=study_id,
            study_root=study_root,
            quest_id=quest_id,
            source=source,
        )
    elif action.action_type is StudyDecisionActionType.REQUEST_GATE_SPECIFICITY:
        result = {
            "ok": True,
            "status": "recorded",
            "action": StudyDecisionActionType.REQUEST_GATE_SPECIFICITY.value,
        }
    else:
        raise ValueError(f"unsupported study outer-loop controller action: {action.action_type.value}")
    return {
        "action_type": action.action_type.value,
        "payload_ref": action.payload_ref,
        "result": result,
    }


__all__ = ["execute_controller_action"]
