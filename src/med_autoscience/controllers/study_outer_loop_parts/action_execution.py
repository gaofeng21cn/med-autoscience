from __future__ import annotations

from pathlib import Path
from typing import Any
from typing import Callable

from med_autoscience.profiles import WorkspaceProfile
from med_autoscience.study_decision_record import StudyDecisionActionType, StudyDecisionControllerAction
from med_autoscience.controllers import domain_action_requests
from med_autoscience.controllers import domain_action_request_lifecycle


RuntimeExecutionPayload = Callable[..., dict[str, Any]]
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
    execution_payload_fn: RuntimeExecutionPayload,
    load_yaml_dict_fn: Callable[[Path], dict[str, Any]],
    run_gate_clearing_batch_fn: RunGateClearingBatch,
    run_quality_repair_batch_fn: RunQualityRepairBatch,
) -> dict[str, Any]:
    if action.action_type in {
        StudyDecisionActionType.REQUEST_OPL_STAGE_ATTEMPT,
        StudyDecisionActionType.REQUEST_OPL_STAGE_ATTEMPT_RELAUNCH,
    }:
        result = {
            "ok": False,
            "status": "opl_stage_attempt_admission_required",
            "action": action.action_type.value,
            "study_id": study_id,
            "quest_id": quest_id,
            "source": source,
            "runtime_owner": "one-person-lab",
            "domain_owner": "med-autoscience",
            "mas_executes_runtime_attempt": False,
            "provider_completion_is_domain_completion": False,
            "typed_blocker": {
                "blocker_type": "opl_stage_attempt_admission_required",
                "owner": "one-person-lab",
                "domain_owner": "med-autoscience",
                "reason": "mas_runtime_attempt_execution_retired",
                "required_handoff": "DomainIntent owner route must be hydrated by OPL current_control_state.",
            },
        }
    elif action.action_type in {StudyDecisionActionType.PAUSE_RUNTIME, StudyDecisionActionType.STOP_RUNTIME}:
        result = {
            "ok": False,
            "status": "opl_runtime_human_gate_required",
            "action": action.action_type.value,
            "study_id": study_id,
            "quest_id": quest_id,
            "source": source,
            "runtime_owner": "one-person-lab",
            "domain_owner": "med-autoscience",
            "mas_executes_runtime_attempt": False,
            "typed_blocker": {
                "blocker_type": "opl_runtime_human_gate_required",
                "owner": "one-person-lab",
                "domain_owner": "med-autoscience",
                "reason": "mas_pause_stop_runtime_execution_retired",
                "required_handoff": "Pause/stop must go through OPL current_control_state human gate.",
            },
        }
    elif action.action_type is StudyDecisionActionType.RUN_GATE_CLEARING_BATCH:
        try:
            result = run_gate_clearing_batch_fn(
                profile=profile,
                study_id=study_id,
                study_root=study_root,
                quest_id=quest_id,
                source=source,
            )
        except PermissionError as exc:
            result = _permission_blocked_result(exc)
    elif action.action_type is StudyDecisionActionType.RUN_QUALITY_REPAIR_BATCH:
        try:
            result = run_quality_repair_batch_fn(
                profile=profile,
                study_id=study_id,
                study_root=study_root,
                quest_id=quest_id,
                source=source,
            )
        except PermissionError as exc:
            result = _permission_blocked_result(exc)
    elif action.action_type is StudyDecisionActionType.REQUEST_GATE_SPECIFICITY:
        result = {
            "ok": True,
            "status": "recorded",
            "action": StudyDecisionActionType.REQUEST_GATE_SPECIFICITY.value,
        }
    elif action.action_type is StudyDecisionActionType.RETURN_TO_AI_REVIEWER_WORKFLOW:
        input_refs = domain_action_request_lifecycle.default_ai_reviewer_request_input_refs(
            study_root=study_root,
        )
        packet = domain_action_requests.build_ai_reviewer_publication_eval_request(
            study_id=study_id,
            quest_id=quest_id,
            source_surface="controller_decisions/latest.json",
            workflow_state={
                "quality_authority": {
                    "owner": "ai_reviewer",
                    "state": "requested",
                },
                "route_back": {
                    "required": True,
                    "target": "publication_eval/latest.json",
                },
                "blockers": ["ai_reviewer_assessment_required"],
            },
            input_refs=input_refs,
        )
        materialized = domain_action_request_lifecycle.materialize_ai_reviewer_request(
            study_root=study_root,
            packet=packet,
        )
        result = {
            "ok": True,
            "status": "recorded",
            "action": StudyDecisionActionType.RETURN_TO_AI_REVIEWER_WORKFLOW.value,
            "request_path": materialized.get("path"),
            "paper_package_mutation_allowed": False,
            "quality_gate_relaxation_allowed": False,
            "manual_study_patch_allowed": False,
        }
    else:
        raise ValueError(f"unsupported study outer-loop controller action: {action.action_type.value}")
    return {
        "action_type": action.action_type.value,
        "payload_ref": action.payload_ref,
        "result": result,
    }


def _permission_blocked_result(exc: PermissionError) -> dict[str, Any]:
    return {
        "ok": False,
        "status": "authority_route_blocked",
        "blocked_reason": "authority_route_blocked",
        "message": str(exc),
        "next_owner": "MAS/controller",
    }


__all__ = ["execute_controller_action"]
