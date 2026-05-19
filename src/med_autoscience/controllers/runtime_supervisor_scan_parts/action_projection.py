from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.controllers import analysis_harmonization_owner_result
from med_autoscience.controllers import provenance_limited_harmonization_owner_result
from med_autoscience.controllers import source_provenance_owner_result
from med_autoscience.controllers.runtime_supervisor_scan_parts import action_decorators
from med_autoscience.controllers.runtime_supervisor_scan_parts import artifact_freshness
from med_autoscience.controllers.runtime_supervisor_scan_parts import completion_evidence
from med_autoscience.controllers.runtime_supervisor_scan_parts import current_truth_owner
from med_autoscience.controllers import study_domain_transition_guard as domain_transition_guard
from med_autoscience.controllers.runtime_supervisor_scan_parts import evidence_adoption
from med_autoscience.controllers.runtime_supervisor_scan_parts import hard_methodology_currentness
from med_autoscience.controllers.runtime_supervisor_scan_parts import methodology_reframe_actions
from med_autoscience.controllers.runtime_supervisor_scan_parts import parked_truth
from med_autoscience.controllers.runtime_supervisor_scan_parts import runtime_facts


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
    methodology_reframe_action = methodology_reframe_actions.methodology_reframe_route_decision_action(study_root)
    if methodology_reframe_action is not None:
        return [
            decorate_action(
                study_id=study_id,
                quest_id=quest_id,
                action=methodology_reframe_action,
                request_allowed_write_surfaces=request_allowed_write_surfaces,
                control_allowed_write_surfaces=control_allowed_write_surfaces,
                forbidden_actions=forbidden_actions,
            )
        ]
    provenance_limited_action = methodology_reframe_actions.provenance_limited_harmonization_audit_action(study_root)
    if provenance_limited_action is not None:
        return [
            decorate_action(
                study_id=study_id,
                quest_id=quest_id,
                action=provenance_limited_action,
                request_allowed_write_surfaces=request_allowed_write_surfaces,
                control_allowed_write_surfaces=control_allowed_write_surfaces,
                forbidden_actions=forbidden_actions,
            )
        ]
    direct_rebuild_route_action = methodology_reframe_actions.clean_rebuild_route_action(study_root)
    if direct_rebuild_route_action is not None:
        return [
            decorate_action(
                study_id=study_id,
                quest_id=quest_id,
                action=direct_rebuild_route_action,
                request_allowed_write_surfaces=request_allowed_write_surfaces,
                control_allowed_write_surfaces=control_allowed_write_surfaces,
                forbidden_actions=forbidden_actions,
            )
        ]
    rebuild_route_action = _provenance_limited_rebuild_route_action(study_root)
    if rebuild_route_action is not None:
        return [
            decorate_action(
                study_id=study_id,
                quest_id=quest_id,
                action=rebuild_route_action,
                request_allowed_write_surfaces=request_allowed_write_surfaces,
                control_allowed_write_surfaces=control_allowed_write_surfaces,
                forbidden_actions=forbidden_actions,
            )
        ]
    source_provenance_action = _source_provenance_recovery_action(study_root)
    if source_provenance_action is not None:
        return [
            decorate_action(
                study_id=study_id,
                quest_id=quest_id,
                action=source_provenance_action,
                request_allowed_write_surfaces=request_allowed_write_surfaces,
                control_allowed_write_surfaces=control_allowed_write_surfaces,
                forbidden_actions=forbidden_actions,
            )
        ]
    hard_methodology_action = _hard_methodology_quality_repair_handoff_action(study_root)
    if hard_methodology_action is not None:
        return [
            decorate_action(
                study_id=study_id,
                quest_id=quest_id,
                action=hard_methodology_action,
                request_allowed_write_surfaces=request_allowed_write_surfaces,
                control_allowed_write_surfaces=control_allowed_write_surfaces,
                forbidden_actions=forbidden_actions,
            )
        ]
    rehydrate_action = _clean_paper_authority_rehydrate_action(
        status=status,
        progress=progress,
        study_root=study_root,
        publication_eval_payload=publication_eval_payload,
    )
    if rehydrate_action is not None:
        return [
            decorate_action(
                study_id=study_id,
                quest_id=quest_id,
                action=rehydrate_action,
                request_allowed_write_surfaces=request_allowed_write_surfaces,
                control_allowed_write_surfaces=control_allowed_write_surfaces,
                forbidden_actions=forbidden_actions,
            )
        ]
    if _clean_paper_authority_cutover_ai_reviewer_required(
        publication_eval_payload=publication_eval_payload,
        ai_reviewer_assessment=ai_reviewer_assessment,
    ):
        return [
            decorate_action(
                study_id=study_id,
                quest_id=quest_id,
                action=_ai_reviewer_required_action(reason="paper_authority_clean_migration_required"),
                request_allowed_write_surfaces=request_allowed_write_surfaces,
                control_allowed_write_surfaces=control_allowed_write_surfaces,
                forbidden_actions=forbidden_actions,
            )
        ]
    if completion_evidence.completed_current_truth(status, progress):
        return []
    if parked_truth.current_truth(
        status,
        progress,
        study_root=study_root,
        publication_eval_payload=publication_eval_payload,
    ):
        return []
    ai_reviewer_freshness_action = artifact_freshness.blocked_action_from_ai_reviewer_freshness_mismatch(
        study_root=study_root,
        publication_eval_payload=publication_eval_payload,
    )
    if ai_reviewer_freshness_action is not None:
        return [
            decorate_action(
                study_id=study_id,
                quest_id=quest_id,
                action=ai_reviewer_freshness_action,
                request_allowed_write_surfaces=request_allowed_write_surfaces,
                control_allowed_write_surfaces=control_allowed_write_surfaces,
                forbidden_actions=forbidden_actions,
            )
        ]
    oracle_actions = _domain_transition_actions(status)
    if oracle_actions is not None:
        return [
            decorate_action(
                study_id=study_id,
                quest_id=quest_id,
                action=action,
                request_allowed_write_surfaces=request_allowed_write_surfaces,
                control_allowed_write_surfaces=control_allowed_write_surfaces,
                forbidden_actions=forbidden_actions,
            )
            for action in oracle_actions
        ]
    actions: list[dict[str, Any]] = []
    if (
        runtime_facts.runtime_platform_repair_required(status, progress, gate_specificity=gate_specificity)
        or runtime_facts.live_activity_timeout_current_controller_route_available(
            status,
            progress,
            study_root=study_root,
            publication_eval_payload=publication_eval_payload,
        )
        or runtime_facts.current_controller_route_redrive_required(
            status,
            progress,
            study_root=study_root,
            publication_eval_payload=publication_eval_payload,
            gate_specificity=gate_specificity,
        )
        or runtime_facts.current_controller_owner_handoff_redrive_required(
            status=status,
            progress=progress,
            study_root=study_root,
            publication_eval_payload=publication_eval_payload,
        )
        or _external_supervisor_runtime_repair_required(status, progress)
    ):
        actions.append(
            current_truth_owner.runtime_platform_repair_action(
                study_root=study_root,
                status=status,
                publication_eval_payload=publication_eval_payload,
                default_reason=_external_supervisor_runtime_repair_reason(status, progress)
                or current_truth_owner.runtime_platform_repair_reason(status, progress),
            )
        )
    owner_handoff_action = _owner_handoff_action(status)
    if owner_handoff_action is not None:
        actions.append(owner_handoff_action)
    if gate_specificity.get("required") is True:
        from med_autoscience.controllers.runtime_supervisor_scan_parts import publication_gate_actions

        actions.append(publication_gate_actions.action_payload(gate_specificity=gate_specificity))
    artifact_action = _current_package_freshness_lifecycle_action(
        progress=progress,
        study_root=study_root,
        publication_eval_payload=publication_eval_payload,
    )
    if artifact_action is not None:
        actions = [
            action
            for action in actions
            if _text(action.get("action_type")) not in {"runtime_platform_repair", artifact_freshness.ACTION_TYPE}
        ]
        actions.insert(0, artifact_action)
    if ai_reviewer_assessment.get("missing") is True:
        actions.append(_ai_reviewer_required_action(reason="ai_reviewer_assessment_required"))
    return [
        decorate_action(
            study_id=study_id,
            quest_id=quest_id,
            action=action,
            request_allowed_write_surfaces=request_allowed_write_surfaces,
            control_allowed_write_surfaces=control_allowed_write_surfaces,
            forbidden_actions=forbidden_actions,
        )
        for action in actions
    ]


def _domain_transition_actions(status: Mapping[str, Any]) -> list[dict[str, Any]] | None:
    if domain_transition_guard.blocks_auto_redrive(status):
        return []
    action_type = domain_transition_guard.supported_action_type(status)
    if action_type is None:
        return None
    decision_type = domain_transition_guard.decision_type(status)
    work_unit_id = domain_transition_guard.next_work_unit_id(status)
    owner = domain_transition_guard.owner(status) or _owner_for_domain_action(action_type)
    reason = domain_transition_guard.reason(status) or f"domain_transition_{decision_type or 'current'}"
    action: dict[str, Any] = {
        "action_type": action_type,
        "authority": "observability_only",
        "owner": owner,
        "request_owner": owner,
        "recommended_owner": owner,
        "reason": reason,
        "summary": "MAS domain transition oracle selected the current owner work unit.",
        "required_output_surface": "artifacts/publication_eval/latest.json",
        "next_work_unit": work_unit_id,
        "paper_package_mutation_allowed": False,
        "medical_claim_authoring_allowed": False,
    }
    if decision_type == "bundle_stage_finalize":
        action["authority"] = "observability_only"
        action["owner"] = "mas_controller"
        action["request_owner"] = "mas_controller"
        action["recommended_owner"] = "mas_controller"
        action["reason"] = current_truth_owner.RUNTIME_CONTROLLER_REDRIVE_REASON
        action["summary"] = (
            "MAS domain transition oracle selected bundle-stage finalization; redrive the current "
            "controller route instead of repeating a stale analysis or write work unit."
        )
        action["controller_route_required"] = True
        action["domain_transition_decision_type"] = decision_type
    elif decision_type == "publication_gate_blocker":
        action["summary"] = (
            "MAS domain transition oracle selected the publication gate blocker owner route."
        )
        action["controller_action"] = "run_gate_clearing_batch"
        action["domain_transition_decision_type"] = decision_type
    return [
        action
    ]


def _owner_for_domain_action(action_type: str) -> str:
    if action_type == "return_to_ai_reviewer_workflow":
        return "ai_reviewer"
    if action_type == "publication_gate_specificity_required":
        return "publication_gate"
    if action_type == "runtime_platform_repair":
        return "mas_controller"
    return "med-autoscience"


def _owner_handoff_action(status: Mapping[str, Any]) -> dict[str, Any] | None:
    next_route = _mapping(status.get("controller_work_unit_next_route"))
    if _text(next_route.get("recommended_next_route")) != "handoff_to_next_owner":
        return None
    if next_route.get("runtime_relaunch_required") is not False:
        return None
    owner = _text(next_route.get("owner"))
    next_work_unit = _text(next_route.get("next_work_unit"))
    if owner is None or next_work_unit is None:
        return None
    return {
        "action_type": "return_to_ai_reviewer_workflow",
        "authority": "observability_only",
        "owner": owner,
        "request_owner": owner,
        "recommended_owner": owner,
        "reason": evidence_adoption.OWNER_HANDOFF_REASON,
        "summary": "Advance the exhausted analysis work unit to the next owner without redriving the same fingerprint.",
        "required_output_surface": "artifacts/publication_eval/latest.json",
        "next_work_unit": next_work_unit,
        "paper_package_mutation_allowed": False,
        "medical_claim_authoring_allowed": False,
    }


def _current_package_freshness_lifecycle_action(
    *,
    progress: Mapping[str, Any],
    study_root: Path,
    publication_eval_payload: Mapping[str, Any],
) -> dict[str, Any] | None:
    lifecycle = _mapping(progress.get("ai_repair_lifecycle"))
    if _text(lifecycle.get("state")) not in {"blocked", "external_supervisor_required"}:
        return None
    top_action = _mapping(lifecycle.get("top_action"))
    if top_action.get("auto_apply_allowed") is not True and lifecycle.get("auto_apply_allowed") is not True:
        return None
    blocked_reason = _text(lifecycle.get("blocked_reason"))
    if blocked_reason == artifact_freshness.ACTION_TYPE:
        source_blocked_reason = blocked_reason
    elif blocked_reason in {
        "controller_decision_not_superseded",
        "stale_specificity_terminal_gate_not_found",
    } and _text(top_action.get("action_type")) == "runtime_platform_repair":
        source_blocked_reason = blocked_reason
    else:
        return None
    controller_route = current_truth_owner.current_controller_runtime_route(
        study_root=study_root,
        publication_eval_payload=publication_eval_payload,
    )
    if controller_route is None:
        return None
    if _text(controller_route.get("work_unit_id")) != "submission_minimal_refresh":
        return None
    if "run_gate_clearing_batch" not in set(_string_items(controller_route.get("controller_actions"))):
        return None
    return artifact_freshness.action_payload(
        reason=artifact_freshness.ACTION_TYPE,
        controller_route=controller_route,
        source_blocked_reason=source_blocked_reason,
    )


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


def _clean_paper_authority_cutover_ai_reviewer_required(
    *,
    publication_eval_payload: Mapping[str, Any],
    ai_reviewer_assessment: Mapping[str, Any],
) -> bool:
    if ai_reviewer_assessment.get("missing") is not True:
        return False
    provenance = _mapping(publication_eval_payload.get("assessment_provenance"))
    return (
        _text(provenance.get("owner")) == "paper_authority_cutover"
        and _text(provenance.get("source_kind")) == "clean_migration_receipt"
    )


def _clean_paper_authority_rehydrate_action(
    *,
    status: Mapping[str, Any],
    progress: Mapping[str, Any],
    study_root: Path,
    publication_eval_payload: Mapping[str, Any],
) -> dict[str, Any] | None:
    if not _clean_migration_receipt_publication_eval(publication_eval_payload):
        return None
    execution = _latest_clean_migration_rehydrate_execution(study_root) or _latest_clean_migration_quality_repair_blocker(
        study_root
    )
    if execution is None:
        return None
    if _scientific_anchor_missing(status=status, progress=progress, study_root=study_root):
        from med_autoscience.controllers.runtime_supervisor_scan_parts import publication_gate_actions

        action = publication_gate_actions.action_payload(
            gate_specificity={
                "missing_target_kinds": ["claim", "figure", "table", "metric", "source_path"],
                "gate_owner": "publication_gate",
                "next_controller_write": {
                    "surface": "publication_eval/latest.json",
                    "writer": "publication_gate_controller",
                    "materialization_mode": "controller_request_only",
                    "required_target_kinds": ["claim", "figure", "table", "metric", "source_path"],
                },
            }
        )
        action.update(
            {
                "summary": (
                    "Clean paper-authority migration cannot rehydrate manuscript inputs while the "
                    "publication gate still reports a missing scientific anchor."
                ),
                "scientific_anchor_required": True,
                "write_rehydrate_deferred": True,
                "deferred_action_type": "canonical_paper_inputs_rehydrate_required",
                "required_anchor_surface": "runtime/quest/artifacts/reports/publishability_gate/latest.json",
                "paper_package_mutation_allowed": False,
                "medical_claim_authoring_allowed": False,
            }
        )
        return action
    required_input_surface = _text(execution.get("required_input_surface")) or str(
        study_root / "paper" / "medical_manuscript_blueprint.json"
    )
    required_output_surface = str(study_root / "paper" / "medical_manuscript_blueprint_source.json")
    owner_callable_surface = _text(execution.get("owner_callable_surface")) or (
        "medical_manuscript_blueprint.materialize_medical_manuscript_blueprint"
    )
    return {
        "action_type": "canonical_paper_inputs_rehydrate_required",
        "authority": "observability_only",
        "owner": "write",
        "request_owner": "write",
        "recommended_owner": "write",
        "reason": "canonical_paper_inputs_rehydrate_required",
        "summary": (
            "Clean paper-authority migration requires the write owner to rehydrate canonical paper "
            "inputs before the AI reviewer can evaluate the manuscript."
        ),
        "required_input_surface": required_input_surface,
        "required_output_surface": required_output_surface,
        "owner_callable_surface": owner_callable_surface,
        "paper_package_mutation_allowed": False,
        "medical_claim_authoring_allowed": False,
        "legacy_artifact_reader_allowed": False,
        "mechanical_blueprint_as_canonical_allowed": False,
    }


def _clean_migration_receipt_publication_eval(publication_eval_payload: Mapping[str, Any]) -> bool:
    provenance = _mapping(publication_eval_payload.get("assessment_provenance"))
    return (
        _text(provenance.get("owner")) == "paper_authority_cutover"
        and _text(provenance.get("source_kind")) == "clean_migration_receipt"
    )


def _latest_clean_migration_rehydrate_execution(study_root: Path) -> dict[str, Any] | None:
    payload = _read_json_object(study_root / "artifacts" / "supervision" / "consumer" / "default_executor_execution" / "latest.json")
    executions = payload.get("executions") if isinstance(payload, Mapping) else None
    if not isinstance(executions, list):
        return None
    for item in reversed(executions):
        execution = _mapping(item)
        if _text(execution.get("execution_status")) != "blocked":
            continue
        if _clean_migration_ai_reviewer_rehydrate_blocker(execution):
            return execution
        if _clean_migration_rehydrate_execution_blocker(execution):
            return execution
    return None


def _latest_clean_migration_quality_repair_blocker(study_root: Path) -> dict[str, Any] | None:
    payload = _read_json_object(study_root / "artifacts" / "controller" / "quality_repair_batch" / "latest.json")
    if not payload:
        return None
    if _text(payload.get("status")) != "blocked_no_paper_root":
        return None
    if _text(payload.get("blocked_reason")) != "canonical_paper_inputs_rehydrate_required":
        return None
    if _text(payload.get("next_owner")) != "write":
        return None
    prepare = _mapping(payload.get("paper_owner_surface_prepare"))
    if prepare and _text(prepare.get("status")) not in {
        "blocked_missing_authorized_canonical_inputs",
        "blocked_missing_projection",
    }:
        return None
    return {
        "action_type": "run_quality_repair_batch",
        "execution_status": "blocked",
        "blocked_reason": "canonical_paper_inputs_rehydrate_required",
        "next_owner": "write",
        "owner_callable_surface": "medical_manuscript_blueprint.materialize_medical_manuscript_blueprint",
        "required_input_surface": str(study_root / "paper" / "medical_manuscript_blueprint.json"),
        "source_ref": str(study_root / "artifacts" / "controller" / "quality_repair_batch" / "latest.json"),
    }


def _hard_methodology_quality_repair_handoff_action(study_root: Path) -> dict[str, Any] | None:
    source_ref = study_root / "artifacts" / "controller" / "quality_repair_batch" / "latest.json"
    payload = hard_methodology_currentness.quality_repair_handoff_payload(source_ref)
    if payload is None:
        return None
    if analysis_harmonization_owner_result.required_output_satisfied(
        study_root=study_root
    ) and not _hard_methodology_handoff_supersedes_consumers(study_root=study_root, source_ref=source_ref):
        return None
    target = _mapping(payload.get("hard_methodology_target"))
    target_id = _text(target.get("target_id")) or "unit_harmonized_external_validation_rerun"
    return {
        "action_type": "unit_harmonized_external_validation_rerun",
        "authority": "observability_only",
        "owner": "analysis_harmonization_owner",
        "request_owner": "analysis_harmonization_owner",
        "recommended_owner": "analysis_harmonization_owner",
        "reason": "unit_harmonized_rerun_required",
        "summary": (
            "HDL/unit harmonization is a hard methodology blocker; route to the analysis "
            "harmonization owner for a unit-harmonized external-validation rerun or a typed blocker."
        ),
        "next_work_unit": "unit_harmonized_external_validation_rerun",
        "work_unit_fingerprint": f"hard-methodology::unit_harmonized_external_validation_rerun::{target_id}",
        "required_output_surface": (
            "unit-harmonized external-validation rerun evidence or "
            "typed blocker:unit_harmonized_rerun_required"
        ),
        "source_ref": str(source_ref),
        "hard_methodology_target": dict(target),
        "quality_gate_relaxation_allowed": False,
        "current_package_write_allowed": False,
        "paper_package_mutation_allowed": False,
        "manual_study_patch_allowed": False,
        "medical_claim_authoring_allowed": False,
    }


def _provenance_limited_rebuild_route_action(study_root: Path) -> dict[str, Any] | None:
    provenance_limited_state = provenance_limited_harmonization_owner_result.typed_blocker_state(
        study_root=study_root
    )
    if not provenance_limited_state:
        return None
    if _text(provenance_limited_state.get("blocked_reason")) != "unit_harmonized_rerun_required":
        return None
    if _text(provenance_limited_state.get("next_owner")) != "analysis_harmonization_owner":
        return None
    source_ref = provenance_limited_harmonization_owner_result.result_path(study_root=study_root)
    analysis_ref = analysis_harmonization_owner_result.result_path(study_root=study_root)
    if analysis_harmonization_owner_result.required_output_satisfied(
        study_root=study_root
    ) and not methodology_reframe_actions.artifact_supersedes(newer_ref=source_ref, older_ref=analysis_ref):
        return None
    return {
        "action_type": "unit_harmonized_external_validation_rerun",
        "authority": "observability_only",
        "owner": "analysis_harmonization_owner",
        "request_owner": "analysis_harmonization_owner",
        "recommended_owner": "analysis_harmonization_owner",
        "reason": "unit_harmonized_rerun_required",
        "summary": (
            "Human-gate authorization converted the provenance-limited audit into a clean "
            "reproducible-model rebuild route; rerun or type-block unit-harmonized external validation."
        ),
        "next_work_unit": "unit_harmonized_external_validation_rerun",
        "work_unit_fingerprint": "clean-rebuild::unit_harmonized_external_validation_rerun::provenance_limited_authorization",
        "required_output_surface": (
            "unit-harmonized external-validation rerun evidence or "
            "typed blocker:unit_harmonized_rerun_required"
        ),
        "source_ref": str(source_ref),
        "rebuild_authorization_consumed": True,
        "quality_gate_relaxation_allowed": False,
        "current_package_write_allowed": False,
        "paper_package_mutation_allowed": False,
        "manual_study_patch_allowed": False,
        "medical_claim_authoring_allowed": False,
    }


def _hard_methodology_handoff_supersedes_consumers(*, study_root: Path, source_ref: Path) -> bool:
    consumer_paths = (
        analysis_harmonization_owner_result.result_path(study_root=study_root),
        source_provenance_owner_result.result_path(study_root=study_root),
        provenance_limited_harmonization_owner_result.result_path(study_root=study_root),
        Path(study_root).expanduser().resolve() / "artifacts" / "controller_decisions" / "latest.json",
    )
    return hard_methodology_currentness.handoff_supersedes_paths(
        source_ref=source_ref,
        consumer_paths=consumer_paths,
    )


def _current_hard_methodology_handoff_supersedes_consumers(study_root: Path) -> bool:
    return _hard_methodology_handoff_supersedes_consumers(
        study_root=study_root,
        source_ref=Path(study_root).expanduser().resolve()
        / "artifacts"
        / "controller"
        / "quality_repair_batch"
        / "latest.json",
    )


def _source_provenance_recovery_action(study_root: Path) -> dict[str, Any] | None:
    if _current_hard_methodology_handoff_supersedes_consumers(study_root):
        return None
    if source_provenance_owner_result.required_output_satisfied(study_root=study_root):
        return None
    owner_result_state = analysis_harmonization_owner_result.typed_blocker_state(study_root=study_root)
    if not owner_result_state:
        return None
    if _text(owner_result_state.get("blocked_reason")) != "transport_model_provenance_recovery_required":
        return None
    if _text(owner_result_state.get("next_owner")) != "source_provenance_owner":
        return None
    source_ref = analysis_harmonization_owner_result.result_path(study_root=study_root)
    return {
        "action_type": "recover_transport_model_provenance",
        "authority": "observability_only",
        "owner": "source_provenance_owner",
        "request_owner": "source_provenance_owner",
        "recommended_owner": "source_provenance_owner",
        "reason": "transport_model_provenance_recovery_required",
        "summary": (
            "The unit-harmonized external-validation rerun requires the original transported Cox "
            "model provenance before any renewed medical transportability claim can be authored."
        ),
        "next_work_unit": "recover_transport_model_provenance",
        "work_unit_fingerprint": "source-provenance::recover_transport_model_provenance",
        "required_output_surface": (
            "canonical transport model provenance bundle or "
            "typed blocker:transport_model_provenance_recovery_required"
        ),
        "source_ref": str(source_ref),
        "quality_gate_relaxation_allowed": False,
        "current_package_write_allowed": False,
        "paper_package_mutation_allowed": False,
        "manual_study_patch_allowed": False,
        "medical_claim_authoring_allowed": False,
    }


def _scientific_anchor_missing(
    *,
    status: Mapping[str, Any],
    progress: Mapping[str, Any],
    study_root: Path,
) -> bool:
    supervisor = _mapping(status.get("publication_supervisor_state")) or _mapping(
        progress.get("publication_supervisor_state")
    )
    if _supervisor_scientific_anchor_missing(supervisor):
        return True
    if _text(progress.get("paper_stage")) == "scientific_anchor_missing":
        return True
    gate_report = _current_publishability_gate_report(status=status, progress=progress, study_root=study_root)
    if _gate_report_scientific_anchor_missing(gate_report):
        return True
    return False


def _supervisor_scientific_anchor_missing(supervisor: Mapping[str, Any]) -> bool:
    if not supervisor:
        return False
    blockers = set(_string_items(supervisor.get("blockers")))
    return bool(
        "missing_publication_anchor" in blockers
        or _text(supervisor.get("supervisor_phase")) == "scientific_anchor_missing"
        or supervisor.get("upstream_scientific_anchor_ready") is False
        or _text(supervisor.get("anchor_kind")) == "missing"
    )


def _gate_report_scientific_anchor_missing(gate_report: Mapping[str, Any]) -> bool:
    if not gate_report:
        return False
    blockers = set(_string_items(gate_report.get("blockers")))
    return bool(
        "missing_publication_anchor" in blockers
        or _text(gate_report.get("anchor_kind")) == "missing"
        or _text(gate_report.get("supervisor_phase")) == "scientific_anchor_missing"
    )


def _current_publishability_gate_report(
    *,
    status: Mapping[str, Any],
    progress: Mapping[str, Any],
    study_root: Path,
) -> dict[str, Any]:
    for path in _publishability_gate_candidate_paths(status=status, progress=progress, study_root=study_root):
        payload = _read_json_object(path)
        if payload:
            return payload
    return {}


def _publishability_gate_candidate_paths(
    *,
    status: Mapping[str, Any],
    progress: Mapping[str, Any],
    study_root: Path,
) -> list[Path]:
    paths: list[Path] = []
    for source in (status, progress):
        if quest_root := _path(_text(source.get("quest_root"))):
            paths.append(quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.json")
    runtime_context_refs = _mapping(status.get("runtime_context_refs")) or _mapping(progress.get("runtime_context_refs"))
    for key in ("publishability_gate_report_ref", "publication_gate_report_ref", "latest_gate_path"):
        if path := _path(_text(runtime_context_refs.get(key))):
            paths.append(path)
    return list(dict.fromkeys(_resolve_gate_candidate_path(study_root=study_root, path=path) for path in paths))


def _resolve_gate_candidate_path(*, study_root: Path, path: Path) -> Path:
    if path.is_absolute():
        return path.expanduser().resolve()
    return (study_root / path).resolve()


def _clean_migration_ai_reviewer_rehydrate_blocker(execution: Mapping[str, Any]) -> bool:
    if _text(execution.get("action_type")) != "return_to_ai_reviewer_workflow":
        return False
    if _text(execution.get("blocked_reason")) != "canonical_paper_inputs_rehydrate_required":
        return False
    if _text(execution.get("next_owner")) != "write":
        return False
    owner_result = _mapping(execution.get("owner_result"))
    if _text(owner_result.get("authority_source_signature")) != "paper_authority_clean_migration":
        return False
    if owner_result.get("legacy_artifact_reader_allowed") is not False:
        return False
    return owner_result.get("mechanical_blueprint_as_canonical_allowed") is False


def _clean_migration_rehydrate_execution_blocker(execution: Mapping[str, Any]) -> bool:
    if _text(execution.get("action_type")) != "canonical_paper_inputs_rehydrate_required":
        return False
    if _text(execution.get("blocked_reason")) != "canonical_paper_inputs_rehydrate_failed":
        return False
    if _text(execution.get("next_owner")) != "write":
        return False
    owner_callable_surface = _text(execution.get("owner_callable_surface"))
    if owner_callable_surface != "medical_manuscript_blueprint.materialize_medical_manuscript_blueprint":
        return False
    required_output_surface = _text(execution.get("required_output_surface"))
    return required_output_surface is not None and required_output_surface.endswith(
        "paper/medical_manuscript_blueprint_source.json"
    )


def _ai_reviewer_required_action(*, reason: str) -> dict[str, Any]:
    return {
        "action_type": "return_to_ai_reviewer_workflow",
        "authority": "observability_only",
        "owner": "ai_reviewer",
        "request_owner": "ai_reviewer",
        "recommended_owner": "ai_reviewer",
        "reason": reason,
        "summary": "Request an AI reviewer-owned publication_eval assessment.",
        "required_output_surface": "artifacts/publication_eval/latest.json",
        "paper_package_mutation_allowed": False,
    }


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
    if reason := evidence_adoption.why_not_applied(status):
        if not _has_controller_redrive_action(actions):
            return reason
    if runtime_facts.runtime_platform_repair_required(status, progress, gate_specificity=gate_specificity):
        for action in actions:
            if _text(action.get("action_type")) == "runtime_platform_repair":
                return _text(action.get("reason")) or current_truth_owner.runtime_platform_repair_reason(status, progress)
        return current_truth_owner.runtime_platform_repair_reason(status, progress)
    if runtime_facts.live_activity_timeout_current_controller_redrive_required(status, progress):
        for action in actions:
            if _text(action.get("action_type")) == "runtime_platform_repair":
                return _text(action.get("reason")) or current_truth_owner.RUNTIME_CONTROLLER_REDRIVE_REASON
    if any(
        _text(action.get("action_type")) == "runtime_platform_repair"
        and _text(action.get("reason")) == current_truth_owner.RUNTIME_CONTROLLER_REDRIVE_REASON
        for action in actions
    ):
        return current_truth_owner.RUNTIME_CONTROLLER_REDRIVE_REASON
    if runtime_facts.retry_exhausted(status, progress):
        if gate_specificity.get("required") is True:
            return "publication_gate_specificity_required"
        return "runtime_recovery_retry_budget_exhausted"
    if actions:
        return _text(actions[0].get("reason")) or _text(actions[0].get("action_type"))
    if text := _text(lifecycle.get("blocked_reason")):
        if text == "ai_reviewer_assessment_required" and ai_reviewer_assessment.get("missing") is not True:
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


def _has_controller_redrive_action(actions: list[dict[str, Any]]) -> bool:
    return any(
        _text(action.get("action_type")) == "runtime_platform_repair"
        and _text(action.get("reason")) == current_truth_owner.RUNTIME_CONTROLLER_REDRIVE_REASON
        for action in actions
    )


def blocked_reason_from_scan(
    *,
    actions: list[dict[str, Any]],
    gate_specificity: Mapping[str, Any],
    ai_reviewer_assessment: Mapping[str, Any],
) -> str | None:
    for action in actions:
        if _text(action.get("action_type")) in {
            "runtime_platform_repair",
            "publication_gate_specificity_required",
            "current_package_freshness_required",
            "return_to_ai_reviewer_workflow",
            "canonical_paper_inputs_rehydrate_required",
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


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _read_json_object(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return dict(payload) if isinstance(payload, Mapping) else {}


def _path_mtime(path: Path) -> float | None:
    try:
        return Path(path).expanduser().resolve().stat().st_mtime
    except OSError:
        return None


def _external_supervisor_runtime_repair_required(status: Mapping[str, Any], progress: Mapping[str, Any]) -> bool:
    return _external_supervisor_runtime_repair_reason(status, progress) is not None


def _external_supervisor_runtime_repair_reason(status: Mapping[str, Any], progress: Mapping[str, Any]) -> str | None:
    if runtime_facts.active_run_id(status, progress) is not None and runtime_facts.worker_running(status):
        return None
    lifecycle = _mapping(progress.get("ai_repair_lifecycle"))
    if _text(lifecycle.get("state")) not in {"blocked", "external_supervisor_required"}:
        return None
    if lifecycle.get("external_supervisor_required") is not True:
        return None
    blocked_reason = _text(lifecycle.get("blocked_reason"))
    if blocked_reason != "runtime_recovery_not_authorized":
        return None
    top_action = _mapping(lifecycle.get("top_action"))
    if (
        _text(top_action.get("action_type")) == "controller_repair"
        and _text(top_action.get("repair_kind")) == "bounded_work_unit_redrive"
        and top_action.get("auto_apply_allowed") is True
    ):
        return blocked_reason
    return None


def _string_items(value: object) -> list[str]:
    if isinstance(value, str):
        text = value.strip()
        return [text] if text else []
    if not isinstance(value, list | tuple | set):
        return []
    return list(dict.fromkeys(text for item in value if (text := _text(item)) is not None))


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _path(value: str | None) -> Path | None:
    return Path(value) if value is not None else None


__all__ = [
    "action_queue",
    "blocked_reason_from_scan",
    "decorate_action",
    "why_not_applied",
]
