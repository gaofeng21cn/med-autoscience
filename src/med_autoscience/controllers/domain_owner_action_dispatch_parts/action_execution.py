from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.profiles import WorkspaceProfile

from med_autoscience import medical_manuscript_blueprint
from med_autoscience.controllers import gate_clearing_batch, publication_gate

from .. import (
    ai_reviewer_publication_eval_workflow,
    analysis_harmonization_owner,
    paper_authority_migration,
    quest_hydration,
    domain_status_projection,
)
from .action_execution_parts import methodology_reframe_decision
from .action_execution_parts import publication_gate_actions
from .action_execution_parts import provenance_limited_harmonization
from .action_execution_parts import quality_repair
from .action_execution_parts import source_provenance
from .action_execution_parts import claim_evidence_alignment
from .action_execution_parts import ai_reviewer_request_refs
from .action_execution_parts.ai_reviewer_medical_prose_review_production import (
    currentness_blocker_or_handoff,
    try_rehydrate_medical_prose_review_request,
)
from .action_execution_parts.ai_reviewer_clean_migration_record import build_clean_migration_request_record
from .action_execution_parts.ai_reviewer_record_validation import (
    ai_reviewer_owned_record,
    ai_reviewer_record_blocker,
    ai_reviewer_record_requirements,
    missing_ai_reviewer_record_fields,
)
from .action_execution_parts.ai_reviewer_record_production import (
    attach_invalid_ai_reviewer_record_handoff,
    record_production_handoff_execution,
)
from .action_execution_parts.ai_reviewer_routeback_record import build_current_medical_prose_routeback_record
from .action_execution_parts.ai_reviewer_stale_record_handoff import stale_ai_reviewer_record_handoff
from ..ai_reviewer_story_provenance_guard import ai_reviewer_record_story_provenance_leakage_dispatch_blocker
from ..domain_action_request_lifecycle import stable_ai_reviewer_request_path


PUBLICATION_EVAL_LATEST_RELATIVE_PATH = Path("artifacts/publication_eval/latest.json")
ANALYSIS_HARMONIZATION_REQUEST_RELATIVE_PATH = Path("artifacts/supervision/requests/analysis_harmonization/latest.json")
SOURCE_PROVENANCE_REQUEST_RELATIVE_PATH = source_provenance.REQUEST_RELATIVE_PATH
PROVENANCE_LIMITED_HARMONIZATION_REQUEST_RELATIVE_PATH = (
    provenance_limited_harmonization.REQUEST_RELATIVE_PATH
)
DECISION_REQUEST_RELATIVE_PATH = methodology_reframe_decision.DECISION_REQUEST_RELATIVE_PATH


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _string_items(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    items: list[str] = []
    for item in value:
        text = _text(item)
        if text is not None:
            items.append(text)
    return items


def _read_json_object(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return dict(payload) if isinstance(payload, Mapping) else None


def _study_root(profile: WorkspaceProfile, study_id: str) -> Path:
    return profile.studies_root / study_id


def _publication_eval_latest_path(study_root: Path) -> Path:
    return study_root / PUBLICATION_EVAL_LATEST_RELATIVE_PATH


def _ai_reviewer_workflow_output_error(*, study_root: Path, owner_result: object) -> str | None:
    if not isinstance(owner_result, Mapping):
        return "owner_result_missing_or_invalid"
    latest_path = _publication_eval_latest_path(study_root)
    artifact_path_text = _text(owner_result.get("artifact_path"))
    if artifact_path_text is None:
        return "artifact_path_missing"
    artifact_path = Path(artifact_path_text).expanduser()
    if not artifact_path.is_absolute():
        artifact_path = study_root / artifact_path
    if artifact_path.resolve() != latest_path.resolve():
        return "artifact_path_not_publication_eval_latest"
    if not artifact_path.is_file():
        return "artifact_path_not_written"
    surface = _text(owner_result.get("publication_eval_surface"))
    if surface is not None and surface != str(PUBLICATION_EVAL_LATEST_RELATIVE_PATH):
        return "publication_eval_surface_mismatch"
    return None


def quest_root_from_status(profile: WorkspaceProfile, study_id: str) -> Path | None:
    try:
        status = domain_status_projection.progress_projection(profile=profile, study_id=study_id, study_root=None, entry_mode=None)
    except Exception:
        return None
    status_payload = dict(status) if isinstance(status, Mapping) else status.to_dict()
    quest_root = _text(status_payload.get("quest_root"))
    return Path(quest_root).expanduser().resolve() if quest_root is not None else None


def execute_publication_gate_specificity(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    apply: bool,
    dispatch: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    return publication_gate_actions.execute_publication_gate_specificity(
        profile=profile,
        study_id=study_id,
        apply=apply,
        quest_root=quest_root_from_status(profile, study_id),
    )


def execute_current_package_freshness(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    apply: bool,
    dispatch: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    return publication_gate_actions.execute_current_package_freshness(
        profile=profile,
        study_id=study_id,
        apply=apply,
        quest_root=quest_root_from_status(profile, study_id),
    )


def execute_gate_clearing_batch(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    apply: bool,
    dispatch: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    return publication_gate_actions.execute_gate_clearing_batch(
        profile=profile,
        study_id=study_id,
        apply=apply,
        quest_root=quest_root_from_status(profile, study_id),
        dispatch=dispatch,
    )


def _paper_authority_clean_migration_blocker(*, study_root: Path, exc: Exception, request_path: Path) -> dict[str, Any] | None:
    if not paper_authority_migration.cutover_requires_ai_reviewer(study_root=study_root):
        return None
    error = str(exc)
    if "medical_manuscript_blueprint" in error:
        return _blocked_ai_reviewer_execution(
            apply=True,
            reason="canonical_paper_inputs_rehydrate_required",
            request_path=request_path,
            next_owner="write",
            owner_callable_surface="medical_manuscript_blueprint.materialize_medical_manuscript_blueprint",
            required_input_surface=str(study_root / "paper" / "medical_manuscript_blueprint.json"),
            error=error,
            owner_result={
                "surface_kind": "canonical_paper_inputs_rehydrate_blocker",
                "authority_source_signature": "paper_authority_clean_migration",
                "canonical_surface": "paper/medical_manuscript_blueprint.json",
                "mechanical_blueprint_as_canonical_allowed": False,
                "legacy_artifact_reader_allowed": False,
                "quality_verdict_written": False,
                "submission_package_regenerated": False,
                "next_owner": "write",
                "next_required_actions": [
                    "materialize_or_authorize_medical_manuscript_blueprint",
                    "materialize_medical_prose_review_request",
                    "return_to_ai_reviewer_workflow",
                ],
            },
        )
    if "medical_prose_review_request" in error:
        rehydrate = try_rehydrate_medical_prose_review_request(study_root=study_root)
        return _blocked_ai_reviewer_execution(
            apply=True,
            reason="medical_prose_review_request_rehydrate_required",
            request_path=request_path,
            next_owner="ai_reviewer",
            required_input_surface=str(study_root / "artifacts" / "publication_eval" / "medical_prose_review_request.json"),
            error=error,
            owner_result={
                "surface_kind": "medical_prose_review_currentness_blocker",
                "authority_source_signature": "paper_authority_clean_migration",
                "currentness_error": error,
                "stale_medical_prose_review_reuse_allowed": False,
                "medical_prose_review_request_rehydrated": rehydrate["status"] == "materialized",
                "rehydrated_request_ref": rehydrate.get("artifact_path"),
                "quality_verdict_written": False,
                "submission_package_regenerated": False,
                "next_owner": "ai_reviewer",
                "next_required_actions": [
                    "produce_ai_reviewer_medical_prose_review_against_current_manuscript",
                    "produce_ai_reviewer_medical_prose_review_against_current_request",
                    "return_to_ai_reviewer_workflow",
                ],
                "rehydrate_result": rehydrate,
            },
        )
    return None


def _medical_prose_review_currentness_blocker(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    study_root: Path,
    exc: Exception,
    request_path: Path,
    dispatch: Mapping[str, Any] | None,
    apply: bool,
) -> dict[str, Any] | None:
    return currentness_blocker_or_handoff(
        profile=profile,
        study_id=study_id,
        study_root=study_root,
        error=str(exc),
        request_path=request_path,
        dispatch=dispatch,
        apply=apply,
        blocked_execution_builder=_blocked_ai_reviewer_execution,
    )


def _claim_evidence_alignment_blocker(*, study_root: Path, exc: Exception, request_path: Path) -> dict[str, Any] | None:
    owner_result = claim_evidence_alignment.blocker_from_workflow_exception(
        study_root=study_root,
        error=str(exc),
    )
    if owner_result is None:
        return None
    return _blocked_ai_reviewer_execution(
        apply=True,
        reason=claim_evidence_alignment.BLOCKED_REASON,
        request_path=request_path,
        next_owner="write",
        owner_callable_surface=claim_evidence_alignment.OWNER_CALLABLE_SURFACE,
        required_input_surface=claim_evidence_alignment.REQUIRED_INPUT_SURFACE,
        error=str(exc),
        owner_result=owner_result,
    )


def execute_artifact_display_materialization(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    apply: bool,
    dispatch: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    study_root = _study_root(profile, study_id)
    paper_root = study_root / "paper"
    reporting_contract_path = paper_root / "medical_reporting_contract.json"
    if not reporting_contract_path.exists():
        return {
            "execution_status": "blocked" if apply else "dry_run",
            "blocked_reason": "medical_reporting_contract_missing",
            "owner_callable_surface": "quest_hydration.materialize_display_contract_stubs",
            "next_owner": "artifact_os",
            "required_input_surface": str(reporting_contract_path),
        }
    if not apply:
        return {
            "execution_status": "dry_run",
            "blocked_reason": None,
            "owner_callable_surface": "quest_hydration.materialize_display_contract_stubs+gate_clearing_batch.run_gate_clearing_batch",
            "paper_root": str(paper_root),
        }
    try:
        stub_result = quest_hydration.materialize_display_contract_stubs(paper_root=paper_root)
    except (OSError, TypeError, ValueError, RuntimeError) as exc:
        return _blocked_display_materialization(exc=exc, paper_root=paper_root)
    gate_result = execute_current_package_freshness(profile=profile, study_id=study_id, apply=apply)
    owner_result = _mapping(gate_result.get("owner_result"))
    executed = gate_result.get("execution_status") == "executed"
    return _display_materialization_result(
        gate_result=gate_result,
        owner_result=owner_result,
        stub_result=stub_result,
        executed=executed,
        paper_root=paper_root,
    )


def _blocked_display_materialization(*, exc: Exception, paper_root: Path) -> dict[str, Any]:
    return {
        "execution_status": "blocked",
        "blocked_reason": "display_contract_stub_materialization_failed",
        "owner_callable_surface": "quest_hydration.materialize_display_contract_stubs",
        "next_owner": "artifact_os",
        "error": str(exc),
        "paper_root": str(paper_root),
    }


def _display_materialization_result(
    *,
    gate_result: Mapping[str, Any],
    owner_result: Mapping[str, Any],
    stub_result: Mapping[str, Any],
    executed: bool,
    paper_root: Path,
) -> dict[str, Any]:
    return {
        **gate_result,
        "execution_status": "executed" if executed else "blocked",
        "blocked_reason": None if executed else gate_result.get("blocked_reason"),
        "owner_callable_surface": "quest_hydration.materialize_display_contract_stubs+gate_clearing_batch.run_gate_clearing_batch",
        "owner_result": {
            "display_contract_stubs": stub_result,
            "gate_clearing_batch": owner_result or gate_result.get("owner_result"),
        },
        "paper_root": str(paper_root),
    }



def execute_ai_reviewer_workflow(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    apply: bool,
    dispatch: Mapping[str, Any] | None = None,
    controller_decision_refresh,
) -> dict[str, Any]:
    study_root = _study_root(profile, study_id)
    request_path = stable_ai_reviewer_request_path(study_root=study_root)
    request = _read_json_object(request_path)
    if request is None or _text(_mapping(request).get("surface_kind")) == "legacy_control_surface_tombstone":
        return _blocked_ai_reviewer_execution(apply=apply, reason="ai_reviewer_request_missing", request_path=request_path)
    request = _complete_ai_reviewer_request_packet(study_root=study_root, request=request, request_path=request_path)
    record, record_blocker = _ai_reviewer_record_for_execution(request=request, study_root=study_root)
    if record_blocker:
        handoff = record_production_handoff_execution(
            profile=profile,
            study_id=study_id,
            request=request,
            dispatch=dispatch,
            record_blocker=record_blocker,
            apply=apply,
        )
        if handoff is not None:
            return handoff
        payload = _blocked_ai_reviewer_execution(apply=apply, reason=record_blocker["reason"], request_path=request_path)
        payload.update(record_blocker["payload"])
        return payload
    if not record:
        return _blocked_ai_reviewer_execution(apply=apply, reason="ai_reviewer_record_missing", request_path=request_path)
    required_refs = ai_reviewer_request_refs.required_refs(request)
    missing_refs = [surface for surface, ref in required_refs.items() if ref is None]
    if missing_refs:
        payload = _blocked_ai_reviewer_execution(apply=apply, reason="ai_reviewer_required_refs_missing", request_path=request_path)
        payload["missing_refs"] = missing_refs
        return payload
    if not apply:
        return {
            "execution_status": "dry_run",
            "blocked_reason": None,
            "owner_callable_surface": "ai_reviewer_publication_eval_workflow.run_ai_reviewer_publication_eval_workflow",
            "request_path": str(request_path),
        }
    additional_refs = {
        surface: ref
        for surface, ref in {**required_refs, **ai_reviewer_request_refs.optional_refs(request)}.items()
        if surface not in {"manuscript", "evidence_ledger", "review_ledger", "study_charter"}
        and ref is not None
    }
    try:
        owner_result = ai_reviewer_publication_eval_workflow.run_ai_reviewer_publication_eval_workflow(
            study_root=study_root,
            manuscript_ref=required_refs["manuscript"],
            evidence_ref=required_refs["evidence_ledger"],
            review_ref=required_refs["review_ledger"],
            charter_ref=required_refs["study_charter"],
            record=record,
            additional_refs=additional_refs,
            workflow_currentness_mode="request_bound_ai_reviewer_record",
        )
    except (OSError, TypeError, ValueError, RuntimeError) as exc:
        clean_migration_blocker = _paper_authority_clean_migration_blocker(
            study_root=study_root,
            exc=exc,
            request_path=request_path,
        )
        if clean_migration_blocker is not None:
            return clean_migration_blocker
        currentness_blocker = _medical_prose_review_currentness_blocker(
            profile=profile,
            study_id=study_id,
            study_root=study_root,
            exc=exc,
            request_path=request_path,
            dispatch=dispatch,
            apply=apply,
        )
        if currentness_blocker is not None:
            return currentness_blocker
        alignment_blocker = _claim_evidence_alignment_blocker(
            study_root=study_root,
            exc=exc,
            request_path=request_path,
        )
        if alignment_blocker is not None:
            return alignment_blocker
        payload = _blocked_ai_reviewer_execution(apply=True, reason="ai_reviewer_workflow_failed", request_path=request_path)
        payload["error"] = str(exc)
        return payload
    output_error = _ai_reviewer_workflow_output_error(study_root=study_root, owner_result=owner_result)
    if output_error is not None:
        payload = _blocked_ai_reviewer_execution(
            apply=True,
            reason="ai_reviewer_workflow_output_missing",
            request_path=request_path,
        )
        payload["error"] = output_error
        if isinstance(owner_result, Mapping):
            payload["owner_result"] = dict(owner_result)
        return payload
    refresh = controller_decision_refresh(profile=profile, study_id=study_id, study_root=study_root)
    if isinstance(owner_result, Mapping):
        owner_result = {**dict(owner_result), "controller_decision_refresh": refresh}
    return {
        "execution_status": "executed",
        "blocked_reason": None,
        "owner_callable_surface": "ai_reviewer_publication_eval_workflow.run_ai_reviewer_publication_eval_workflow",
        "owner_result": owner_result,
        "request_path": str(request_path),
    }


def _complete_ai_reviewer_request_packet(
    *,
    study_root: Path,
    request: Mapping[str, Any],
    request_path: Path,
) -> dict[str, Any]:
    completed = {**dict(request)}
    input_contract = _mapping(completed.get("input_contract"))
    required_refs = _mapping(input_contract.get("required_refs"))
    changed = False
    for surface, path in _canonical_ai_reviewer_ref_paths(study_root=study_root).items():
        existing = _mapping(required_refs.get(surface))
        existing_path = _text(existing.get("path")) or _text(existing.get("ref")) or _text(existing.get("relative_path"))
        if existing_path:
            continue
        if not path.is_file():
            continue
        required_refs[surface] = {"path": str(path.resolve()), "present": True, "valid": True}
        changed = True
    if not changed:
        return completed
    input_contract["required_refs"] = required_refs
    completed["input_contract"] = input_contract
    lifecycle = _mapping(completed.get("request_lifecycle"))
    lifecycle["request_packet_materialized"] = True
    lifecycle["all_required_refs_present"] = all(
        ref is not None for ref in ai_reviewer_request_refs.required_refs(completed).values()
    )
    completed["request_lifecycle"] = lifecycle
    request_path.parent.mkdir(parents=True, exist_ok=True)
    request_path.write_text(json.dumps(completed, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return completed


def _canonical_ai_reviewer_ref_paths(*, study_root: Path) -> dict[str, Path]:
    return {
        "manuscript": study_root / "paper" / "draft.md",
        "evidence_ledger": study_root / "paper" / "evidence_ledger.json",
        "review_ledger": study_root / "paper" / "review" / "review_ledger.json",
        "study_charter": study_root / "artifacts" / "controller" / "study_charter.json",
        "medical_manuscript_blueprint": study_root / "paper" / "medical_manuscript_blueprint.json",
        "claim_evidence_map": study_root / "paper" / "claim_evidence_map.json",
        "medical_prose_review": study_root / "artifacts" / "publication_eval" / "medical_prose_review.json",
        "publication_gate_projection": study_root / "artifacts" / "publication_eval" / "latest.json",
    }


def execute_canonical_paper_inputs_rehydrate(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    apply: bool,
    dispatch: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    study_root = _study_root(profile, study_id)
    if not paper_authority_migration.cutover_requires_ai_reviewer(study_root=study_root):
        return {
            "execution_status": "blocked" if apply else "dry_run",
            "blocked_reason": "paper_authority_clean_migration_not_pending",
            "owner_callable_surface": "medical_manuscript_blueprint.materialize_medical_manuscript_blueprint",
            "next_owner": "ai_reviewer",
            "required_input_surface": str(study_root / "artifacts" / "migration" / "paper_authority_cutover" / "latest.json"),
        }
    if not apply:
        return {
            "execution_status": "dry_run",
            "blocked_reason": None,
            "owner_callable_surface": "medical_manuscript_blueprint.materialize_medical_manuscript_blueprint",
            "required_output_surface": str(study_root / "paper" / "medical_manuscript_blueprint_source.json"),
            "next_owner": "write",
        }
    try:
        owner_result = medical_manuscript_blueprint.materialize_medical_manuscript_blueprint(study_root=study_root)
    except (OSError, TypeError, ValueError, RuntimeError) as exc:
        return {
            "execution_status": "blocked",
            "blocked_reason": "canonical_paper_inputs_rehydrate_failed",
            "owner_callable_surface": "medical_manuscript_blueprint.materialize_medical_manuscript_blueprint",
            "next_owner": "write",
            "error": str(exc),
            "required_output_surface": str(study_root / "paper" / "medical_manuscript_blueprint_source.json"),
        }
    return {
        "execution_status": "executed",
        "blocked_reason": None,
        "owner_callable_surface": "medical_manuscript_blueprint.materialize_medical_manuscript_blueprint",
        "next_owner": "write",
        "owner_result": {
            **dict(owner_result),
            "canonical_ready": False,
            "canonical_surface_written": False,
            "next_required_actions": [
                "AI author/reviewer must authorize paper/medical_manuscript_blueprint.json",
                "materialize medical prose review request",
                "return to AI reviewer workflow",
            ],
        },
    }


def execute_unit_harmonized_external_validation_rerun(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    apply: bool,
    dispatch: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    study_root = _study_root(profile, study_id)
    request_path = study_root / ANALYSIS_HARMONIZATION_REQUEST_RELATIVE_PATH
    request = _analysis_harmonization_request(study_id=study_id, dispatch=dispatch or {})
    if not apply:
        return {
            "execution_status": "dry_run",
            "blocked_reason": None,
            "owner_callable_surface": "analysis_harmonization_owner.unit_harmonized_external_validation_rerun_or_typed_blocker",
            "request_path": str(request_path),
            "next_owner": "analysis_harmonization_owner",
        }
    request_path.parent.mkdir(parents=True, exist_ok=True)
    request["path"] = str(request_path)
    request_path.write_text(json.dumps(request, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    owner_execution = analysis_harmonization_owner.unit_harmonized_external_validation_rerun_or_typed_blocker(
        profile=profile,
        study_id=study_id,
        dispatch=dispatch,
        request=request,
        apply=True,
    )
    owner_result = _mapping(owner_execution.get("owner_result"))
    owner_result["request_path"] = str(request_path)
    owner_result["request_kind"] = "unit_harmonized_external_validation_rerun"
    return {**owner_execution, "owner_result": owner_result, "request_path": str(request_path)}


def execute_recover_transport_model_provenance(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    apply: bool,
    dispatch: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    return source_provenance.execute(
        profile=profile,
        study_id=study_id,
        apply=apply,
        dispatch=dispatch,
    )


def execute_methodology_reframe_route_decision(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    apply: bool,
    dispatch: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    return methodology_reframe_decision.execute(
        profile=profile,
        study_id=study_id,
        apply=apply,
        dispatch=dispatch,
    )


def execute_provenance_limited_harmonization_audit(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    apply: bool,
    dispatch: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    return provenance_limited_harmonization.execute(
        profile=profile,
        study_id=study_id,
        apply=apply,
        dispatch=dispatch,
    )


def _analysis_harmonization_request(*, study_id: str, dispatch: Mapping[str, Any]) -> dict[str, Any]:
    prompt_contract = _mapping(dispatch.get("prompt_contract"))
    source_action = _mapping(dispatch.get("source_action"))
    owner_route = _mapping(dispatch.get("owner_route")) or _mapping(prompt_contract.get("owner_route"))
    required_output_surface = _text(dispatch.get("required_output_surface")) or _text(
        prompt_contract.get("required_output_surface")
    )
    if required_output_surface is None:
        required_output_surface = (
            "unit-harmonized external-validation rerun evidence or "
            "typed blocker:unit_harmonized_rerun_required"
        )
    return {
        "surface": "domain_action_request",
        "schema_version": 1,
        "study_id": study_id,
        "quest_id": _text(dispatch.get("quest_id")) or _text(prompt_contract.get("quest_id")) or study_id,
        "request_kind": "unit_harmonized_external_validation_rerun",
        "request_owner": "analysis_harmonization_owner",
        "assigned_to": "analysis_harmonization_owner",
        "status": "requested",
        "blocked_reason": "unit_harmonized_rerun_required",
        "next_owner": "analysis_harmonization_owner",
        "next_work_unit": "unit_harmonized_external_validation_rerun",
        "required_output_surface": required_output_surface,
        "owner_route": owner_route,
        "idempotency_key": _text(dispatch.get("idempotency_key")) or _text(prompt_contract.get("idempotency_key")),
        "work_unit_fingerprint": _text(owner_route.get("work_unit_fingerprint"))
        or _text(dispatch.get("repeat_suppression_key"))
        or _text(prompt_contract.get("repeat_suppression_key")),
        "hard_methodology_target": _mapping(source_action.get("hard_methodology_target"))
        or _mapping(_mapping(source_action.get("handoff_packet")).get("hard_methodology_target")),
        "source_action_ref": {
            "action_type": _text(dispatch.get("action_type")),
            "action_id": _text(dispatch.get("action_id")),
            "dispatch_authority": _text(dispatch.get("dispatch_authority")),
            "dispatch_path": _text(_mapping(dispatch.get("refs")).get("dispatch_path")),
        },
        "input_contract": {
            "required_refs": {
                "controller_decision": {"relative_path": "artifacts/controller_decisions/latest.json"},
                "publication_eval": {"relative_path": "artifacts/publication_eval/latest.json"},
                "claim_evidence_map": {"relative_path": "paper/claim_evidence_map.json"},
            },
            "analysis_requirements": [
                "verify HDL-C source units and assay fields in both cohorts",
                "apply the transported model on unit-harmonized predictors or produce a typed blocker",
                "check sex/smoking coding and continuous predictor transformations against the development model",
                "report rerun discrimination, calibration, risk distribution, and uncertainty evidence when available",
            ],
        },
        "required_output": {
            "accepted_evidence": "unit-harmonized external-validation rerun evidence",
            "accepted_typed_blocker": "unit_harmonized_rerun_required",
        },
        "paper_package_mutation_allowed": False,
        "quality_gate_relaxation_allowed": False,
        "manual_study_patch_allowed": False,
        "medical_claim_authoring_allowed": False,
    }


def _blocked_ai_reviewer_execution(
    *,
    apply: bool,
    reason: str,
    request_path: Path,
    next_owner: str = "ai_reviewer",
    owner_callable_surface: str = "ai_reviewer_publication_eval_workflow.run_ai_reviewer_publication_eval_workflow",
    required_input_surface: str | None = None,
    error: str | None = None,
    owner_result: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "execution_status": "blocked" if apply else "dry_run",
        "blocked_reason": reason,
        "owner_callable_surface": owner_callable_surface,
        "next_owner": next_owner,
        "required_input_surface": required_input_surface or str(request_path),
    }
    if error is not None:
        payload["error"] = error
    if owner_result is not None:
        payload["owner_result"] = dict(owner_result)
    return payload


def _ai_reviewer_record_for_execution(
    *,
    request: Mapping[str, Any],
    study_root: Path,
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    current_record = _mapping(_read_json_object(_publication_eval_latest_path(study_root)))
    request_record = _mapping(request.get("ai_reviewer_record") or request.get("publication_eval_record") or request.get("record"))
    lifecycle = _mapping(request.get("request_lifecycle"))
    stale_record_handoff = stale_ai_reviewer_record_handoff(
        request=request,
        required_refs=ai_reviewer_request_refs.required_refs(request),
        lifecycle=lifecycle,
    )
    if stale_record_handoff is not None:
        return {}, stale_record_handoff
    story_leakage_blocker = ai_reviewer_record_story_provenance_leakage_dispatch_blocker(lifecycle)
    if story_leakage_blocker is not None:
        return {}, story_leakage_blocker

    if request_record:
        record_blocker = ai_reviewer_record_blocker(request_record)
        if record_blocker:
            attach_invalid_ai_reviewer_record_handoff(
                record_blocker=record_blocker,
                request=request,
                required_refs=ai_reviewer_request_refs.required_refs(request),
                record=request_record,
            )
            return {}, record_blocker
        return request_record, None

    request_record = build_current_medical_prose_routeback_record(
        study_root=study_root,
        request=request,
        required_refs=ai_reviewer_request_refs.required_refs(request),
    )
    if request_record:
        record_blocker = ai_reviewer_record_blocker(request_record)
        if record_blocker:
            attach_invalid_ai_reviewer_record_handoff(
                record_blocker=record_blocker,
                request=request,
                required_refs=ai_reviewer_request_refs.required_refs(request),
                record=request_record,
            )
            return {}, record_blocker
        return request_record, None

    if paper_authority_migration.cutover_requires_ai_reviewer(study_root=study_root) and not request_record:
        request_record = _clean_migration_request_record(study_root=study_root, request=request)

    if (
        current_record
        and ai_reviewer_owned_record(current_record)
        and not paper_authority_migration.cutover_requires_ai_reviewer(study_root=study_root)
    ):
        missing_fields = missing_ai_reviewer_record_fields(current_record)
        if missing_fields:
            return {}, {
                "reason": "ai_reviewer_record_incomplete",
                "payload": {
                    "missing_record_fields": missing_fields,
                    "owner_record_requirements": ai_reviewer_record_requirements(),
                },
            }
        return current_record, None

    if request_record:
        record_blocker = ai_reviewer_record_blocker(request_record)
        if record_blocker:
            attach_invalid_ai_reviewer_record_handoff(
                record_blocker=record_blocker,
                request=request,
                required_refs=ai_reviewer_request_refs.required_refs(request),
                record=request_record,
            )
            return {}, record_blocker
        return request_record, None

    return {}, {
        "reason": "ai_reviewer_record_missing",
        "payload": {
            "owner_record_requirements": ai_reviewer_record_requirements(),
        },
    }

def _clean_migration_request_record(*, study_root: Path, request: Mapping[str, Any]) -> dict[str, Any]:
    refs = ai_reviewer_request_refs.required_refs(request)
    return build_clean_migration_request_record(study_root=study_root, request=request, refs=refs)


__all__ = [
    "ANALYSIS_HARMONIZATION_REQUEST_RELATIVE_PATH",
    "DECISION_REQUEST_RELATIVE_PATH",
    "PROVENANCE_LIMITED_HARMONIZATION_REQUEST_RELATIVE_PATH",
    "SOURCE_PROVENANCE_REQUEST_RELATIVE_PATH",
    "execute_ai_reviewer_workflow",
    "execute_artifact_display_materialization",
    "execute_canonical_paper_inputs_rehydrate",
    "execute_current_package_freshness",
    "execute_gate_clearing_batch",
    "execute_methodology_reframe_route_decision",
    "execute_publication_gate_specificity",
    "execute_provenance_limited_harmonization_audit",
    "execute_recover_transport_model_provenance",
    "execute_unit_harmonized_external_validation_rerun",
    "quest_root_from_status",
]
