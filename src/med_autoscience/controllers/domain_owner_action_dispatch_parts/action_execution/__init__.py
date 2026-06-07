from __future__ import annotations

import os
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.profiles import WorkspaceProfile

from med_autoscience.controllers import gate_clearing_batch, publication_gate

from ... import (
    analysis_harmonization_owner,
    quest_hydration,
    domain_status_projection,
)
from . import methodology_reframe_decision
from . import medical_paper_readiness
from . import publication_handoff
from . import publication_gate_actions
from . import provenance_limited_harmonization
from . import quality_repair
from . import source_provenance
from .ai_reviewer_execution import execute_ai_reviewer_workflow, execute_canonical_paper_inputs_rehydrate

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

def _study_root(profile: WorkspaceProfile, study_id: str) -> Path:
    return profile.studies_root / study_id

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

def execute_publication_handoff_owner_gate(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    apply: bool,
    dispatch: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    return publication_handoff.execute_publication_handoff_owner_gate(
        profile=profile,
        study_id=study_id,
        apply=apply,
        dispatch=dispatch,
    )

def execute_complete_medical_paper_readiness_surface(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    apply: bool,
    dispatch: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    return medical_paper_readiness.execute_complete_medical_paper_readiness_surface(
        profile=profile,
        study_id=study_id,
        apply=apply,
        dispatch=dispatch,
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
