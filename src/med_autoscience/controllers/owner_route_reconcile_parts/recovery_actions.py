from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.controllers import analysis_harmonization_owner_result
from med_autoscience.controllers import provenance_limited_harmonization_owner_result
from med_autoscience.controllers import source_provenance_owner_result
from med_autoscience.controllers.owner_route_reconcile_parts import hard_methodology_currentness
from med_autoscience.controllers.owner_route_reconcile_parts import methodology_reframe_actions
from med_autoscience.controllers.study_transition_receipt_consumption_parts.default_executor_candidates import (
    latest_owner_callable_adapter_receipt_payload,
)


def clean_paper_authority_cutover_ai_reviewer_required(
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


def clean_paper_authority_rehydrate_action(
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
        from med_autoscience.controllers.owner_route_reconcile_parts import publication_gate_actions

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


def hard_methodology_quality_repair_handoff_action(study_root: Path) -> dict[str, Any] | None:
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


def provenance_limited_rebuild_route_action(study_root: Path) -> dict[str, Any] | None:
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


def source_provenance_recovery_action(study_root: Path) -> dict[str, Any] | None:
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


def _clean_migration_receipt_publication_eval(publication_eval_payload: Mapping[str, Any]) -> bool:
    provenance = _mapping(publication_eval_payload.get("assessment_provenance"))
    return (
        _text(provenance.get("owner")) == "paper_authority_cutover"
        and _text(provenance.get("source_kind")) == "clean_migration_receipt"
    )


def _latest_clean_migration_rehydrate_execution(study_root: Path) -> dict[str, Any] | None:
    payload, receipt_ref = latest_owner_callable_adapter_receipt_payload(study_root=study_root)
    executions = (
        [
            *list(payload.get("executions") or []),
            *list(payload.get("execution_ledger") or []),
        ]
        if isinstance(payload, Mapping)
        else None
    )
    if not isinstance(executions, list):
        return None
    for item in reversed(executions):
        execution = {**_mapping(item), "source_ref": receipt_ref}
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


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _read_json_object(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return dict(payload) if isinstance(payload, Mapping) else {}


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
    "clean_paper_authority_cutover_ai_reviewer_required",
    "clean_paper_authority_rehydrate_action",
    "hard_methodology_quality_repair_handoff_action",
    "provenance_limited_rebuild_route_action",
    "source_provenance_recovery_action",
]
