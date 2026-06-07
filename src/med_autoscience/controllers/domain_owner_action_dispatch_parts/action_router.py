from __future__ import annotations

from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

from med_autoscience.profiles import WorkspaceProfile

from . import action_execution

Executor = Callable[..., dict[str, Any]]


def execute_owner_dispatch_action(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    action_type: str,
    dispatch: Mapping[str, Any],
    apply: bool,
    execute_publication_gate_specificity: Executor,
    execute_ai_reviewer_workflow: Executor,
    quest_root_resolver: Callable[[WorkspaceProfile, str], Path | None],
) -> dict[str, Any]:
    executors = {
        "publication_gate_specificity_required": execute_publication_gate_specificity,
        "publication_handoff_owner_gate": action_execution.execute_publication_handoff_owner_gate,
        "complete_medical_paper_readiness_surface": action_execution.execute_complete_medical_paper_readiness_surface,
        "current_package_freshness_required": action_execution.execute_current_package_freshness,
        "run_gate_clearing_batch": action_execution.execute_gate_clearing_batch,
        "artifact_display_surface_materialization_required": action_execution.execute_artifact_display_materialization,
        "return_to_ai_reviewer_workflow": execute_ai_reviewer_workflow,
        "canonical_paper_inputs_rehydrate_required": action_execution.execute_canonical_paper_inputs_rehydrate,
        "paper_clean_room_rebuild_required": action_execution.execute_paper_clean_room_rebuild,
        "run_medical_publication_surface_from_clean_room": action_execution.execute_clean_room_publication_surface,
    }
    if action_type == "unit_harmonized_external_validation_rerun":
        return action_execution.execute_unit_harmonized_external_validation_rerun(
            profile=profile,
            study_id=study_id,
            apply=apply,
            dispatch=dispatch,
        )
    if action_type == "recover_transport_model_provenance":
        return action_execution.execute_recover_transport_model_provenance(
            profile=profile,
            study_id=study_id,
            apply=apply,
            dispatch=dispatch,
        )
    if action_type == "methodology_reframe_route_decision":
        return action_execution.execute_methodology_reframe_route_decision(
            profile=profile,
            study_id=study_id,
            apply=apply,
            dispatch=dispatch,
        )
    if action_type == "provenance_limited_harmonization_audit":
        return action_execution.execute_provenance_limited_harmonization_audit(
            profile=profile,
            study_id=study_id,
            apply=apply,
            dispatch=dispatch,
        )
    if action_type == "run_quality_repair_batch":
        return action_execution.quality_repair.execute_quality_repair_batch(
            profile=profile,
            study_id=study_id,
            apply=apply,
            dispatch=dispatch,
            quest_root=quest_root_resolver(profile, study_id),
        )
    if (executor := executors.get(action_type)) is None:
        return {
            "execution_status": "blocked",
            "blocked_reason": "unsupported_action_type",
            "owner_callable_surface": None,
        }
    return executor(profile=profile, study_id=study_id, apply=apply, dispatch=dispatch)


__all__ = ["execute_owner_dispatch_action"]
