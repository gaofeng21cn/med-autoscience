from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.controllers import analysis_harmonization_owner_result
from med_autoscience.controllers import provenance_limited_harmonization_owner_result
from med_autoscience.controllers import source_provenance_owner_result
from med_autoscience.controllers.paper_mission_owner_surface import action_decorators
from med_autoscience.controllers.paper_mission_owner_surface import ai_reviewer_actions
from med_autoscience.controllers.paper_mission_owner_surface import completion_evidence
from med_autoscience.controllers.paper_mission_owner_surface import current_truth_owner
from med_autoscience.controllers.paper_mission_owner_surface import parked_truth
from med_autoscience.controllers.paper_mission_owner_surface import runtime_facts
from med_autoscience.controllers.paper_mission_owner_surface.action_projection_helpers import (
    mapping as _mapping,
    path as _path,
    text as _text,
)


def action_queue(
    status: Mapping[str, Any],
    progress: Mapping[str, Any],
    *,
    study_root: Path,
    study_id: str,
    quest_id: str | None,
    publication_eval_payload: Mapping[str, Any],
    gate_specificity: Mapping[str, Any],
    ai_reviewer_assessment: Mapping[str, Any],
    request_allowed_write_surfaces: list[str],
    control_allowed_write_surfaces: list[str],
    forbidden_actions: list[str],
) -> list[dict[str, Any]]:
    del (
        status,
        progress,
        study_root,
        study_id,
        quest_id,
        publication_eval_payload,
        gate_specificity,
        ai_reviewer_assessment,
        request_allowed_write_surfaces,
        control_allowed_write_surfaces,
        forbidden_actions,
    )
    return []


def decorate_action(
    *,
    study_id: str,
    quest_id: str | None,
    action: Mapping[str, Any],
    request_allowed_write_surfaces: list[str],
    control_allowed_write_surfaces: list[str],
    forbidden_actions: list[str],
) -> dict[str, Any]:
    return action_decorators.decorate_action(
        study_id=study_id,
        quest_id=quest_id,
        action=action,
        request_allowed_write_surfaces=request_allowed_write_surfaces,
        control_allowed_write_surfaces=control_allowed_write_surfaces,
        forbidden_actions=forbidden_actions,
    )


def why_not_applied(
    *,
    status: Mapping[str, Any],
    progress: Mapping[str, Any],
    actions: list[dict[str, Any]],
    gate_specificity: Mapping[str, Any],
    ai_reviewer_assessment: Mapping[str, Any],
) -> str | None:
    if completion_evidence.completed_current_truth(status, progress):
        return None
    study_root = _path(_text(status.get("study_root")) or _text(progress.get("study_root")))
    if study_root is not None:
        provenance_limited_state = provenance_limited_harmonization_owner_result.typed_blocker_state(
            study_root=study_root
        )
        if provenance_limited_state:
            return _text(provenance_limited_state.get("blocked_reason"))
        if any(_text(action.get("action_type")) == "provenance_limited_harmonization_audit" for action in actions):
            return "provenance_limited_harmonization_audit_required"
        methodology_decision_requests_audit = (
            provenance_limited_harmonization_owner_result.current_controller_decision_requests_audit(
                study_root=study_root
            )
        )
        source_result_state = source_provenance_owner_result.typed_blocker_state(study_root=study_root)
        if source_result_state and not methodology_decision_requests_audit:
            return _text(source_result_state.get("blocked_reason"))
        owner_result_state = analysis_harmonization_owner_result.typed_blocker_state(study_root=study_root)
        if owner_result_state:
            return _text(owner_result_state.get("blocked_reason"))
    if _has_source_provenance_handoff_action(actions):
        return "transport_model_provenance_recovery_required"
    if _has_hard_methodology_handoff_action(actions):
        return "unit_harmonized_rerun_required"
    publication_eval_payload = _mapping(status.get("publication_eval")) or _mapping(progress.get("publication_eval"))
    if parked_truth.current_truth(
        status,
        progress,
        study_root=study_root,
        publication_eval_payload=publication_eval_payload,
    ):
        return None
    lifecycle = _mapping(progress.get("ai_repair_lifecycle"))
    if gate_action := _gate_clearing_batch_action(actions):
        return _text(gate_action.get("reason")) or "run_gate_clearing_batch"
    if actions:
        return _text(actions[0].get("reason")) or _text(actions[0].get("action_type"))
    if runtime_facts.opl_stage_attempt_admission_required(status, progress):
        return current_truth_owner.OPL_STAGE_ATTEMPT_ADMISSION_REASON
    if runtime_facts.live_activity_timeout_current_controller_redrive_required(status, progress):
        return current_truth_owner.RUNTIME_CONTROLLER_REDRIVE_REASON
    if runtime_facts.retry_exhausted(status, progress):
        if gate_specificity.get("required") is True:
            return "publication_gate_specificity_required"
        return "runtime_recovery_retry_budget_exhausted"
    if text := _text(lifecycle.get("blocked_reason")):
        if text == "ai_reviewer_assessment_required" and ai_reviewer_assessment.get("missing") is not True:
            return None
        if text in {
            ai_reviewer_actions.RECORD_STALE_AFTER_CURRENT_MANUSCRIPT_REASON,
            ai_reviewer_actions.RECORD_STALE_AFTER_UNIT_HARMONIZED_RERUN_REASON,
        } and (
            ai_reviewer_assessment.get("present") is True
            and _text(ai_reviewer_assessment.get("owner")) == "ai_reviewer"
        ):
            return None
        if (
            text == "runtime_relaunch_no_live_run_started"
            and runtime_facts.active_run_id(status, progress) is not None
            and runtime_facts.worker_running(status)
        ):
            return None
        if (
            text == "runtime_recovery_not_authorized"
            and runtime_facts.runtime_recovery_lifecycle_resolved(
                status=status,
                progress=progress,
                lifecycle=lifecycle,
            )
        ):
            return None
        return text
    return None


def _has_hard_methodology_handoff_action(actions: list[dict[str, Any]]) -> bool:
    return any(
        _text(action.get("action_type")) == "unit_harmonized_external_validation_rerun"
        and _text(action.get("reason")) == "unit_harmonized_rerun_required"
        and _text(action.get("owner")) == "analysis_harmonization_owner"
        for action in actions
    )


def _has_source_provenance_handoff_action(actions: list[dict[str, Any]]) -> bool:
    return any(
        _text(action.get("action_type")) == "recover_transport_model_provenance"
        and _text(action.get("reason")) == "transport_model_provenance_recovery_required"
        and _text(action.get("owner")) == "source_provenance_owner"
        for action in actions
    )


def _has_gate_clearing_batch_action(actions: list[dict[str, Any]]) -> bool:
    return _gate_clearing_batch_action(actions) is not None


def _gate_clearing_batch_action(actions: list[dict[str, Any]]) -> dict[str, Any] | None:
    for action in actions:
        if (
            _text(action.get("action_type")) == "run_gate_clearing_batch"
            and _text(action.get("owner")) == "gate_clearing_batch"
        ):
            return action
    return None


def blocked_reason_from_scan(
    *,
    actions: list[dict[str, Any]],
    gate_specificity: Mapping[str, Any],
    ai_reviewer_assessment: Mapping[str, Any],
) -> str | None:
    for action in actions:
        if _text(action.get("action_type")) in {
            "publication_gate_specificity_required",
            "publication_handoff_owner_gate",
            "current_package_freshness_required",
            "return_to_ai_reviewer_workflow",
            "canonical_paper_inputs_rehydrate_required",
            "run_quality_repair_batch",
            "run_gate_clearing_batch",
            "unit_harmonized_external_validation_rerun",
            "recover_transport_model_provenance",
            "methodology_reframe_route_decision",
            "provenance_limited_harmonization_audit",
        }:
            return _text(action.get("reason")) or _text(action.get("action_type"))
    if gate_specificity.get("required") is True:
        return "publication_gate_specificity_required"
    if ai_reviewer_assessment.get("missing") is True:
        return "ai_reviewer_assessment_required"
    return None


__all__ = [
    "action_queue",
    "blocked_reason_from_scan",
    "decorate_action",
    "why_not_applied",
]
