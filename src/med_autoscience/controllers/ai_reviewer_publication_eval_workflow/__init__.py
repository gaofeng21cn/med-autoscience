from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from med_autoscience.claim_evidence_alignment import (
    build_claim_evidence_alignment_gate,
)
from med_autoscience.policies import (
    DEFAULT_PUBLICATION_CRITIQUE_POLICY,
    build_ai_reviewer_operating_system_contract,
)
from med_autoscience.publication_eval_latest import (
    materialize_ai_reviewer_publication_eval_latest,
)
from med_autoscience.controllers import paper_authority_migration
from med_autoscience.controllers.ai_reviewer_publication_eval_workflow.currentness import (
    _currentness_checks,
    _future_facing_limitations_plan,
    _publication_quality_readiness,
    _sci_clinical_registry_review,
    _sci_registry_review_blockers,
    _sha256_file,
)
from med_autoscience.controllers.ai_reviewer_story_provenance_guard import (
    MANUSCRIPT_STORY_SENSITIVE_DIMENSIONS,
    reject_manuscript_story_provenance_leakage,
)
from med_autoscience.publication_eval_record.validation import _RECORD_ALLOWED_FIELDS
from med_autoscience.publication_eval_record_provenance import _ASSESSMENT_PROVENANCE_ALLOWED_FIELDS
from med_autoscience.publication_eval_reviewer_os import (
    validate_ai_reviewer_operating_system_trace,
)
from med_autoscience.publication_eval_record import PublicationEvalRecord

__all__ = [
    "build_ai_reviewer_publication_eval_record_with_workflow_trace",
    "build_ai_reviewer_publication_eval_workflow_trace",
    "run_ai_reviewer_publication_eval_workflow",
]


_SURFACE = "ai_reviewer_publication_eval_workflow"
_SCHEMA_VERSION = 1
_REF_ALIASES = {
    "manuscript_ref": "manuscript",
    "evidence_ref": "evidence_ledger",
    "review_ref": "review_ledger",
    "charter_ref": "study_charter",
}
_REQUIRED_TRACE_INPUTS = (
    "manuscript",
    "study_charter",
    "evidence_ledger",
    "review_ledger",
)
_MANUSCRIPT_STORY_SENSITIVE_DIMENSIONS = MANUSCRIPT_STORY_SENSITIVE_DIMENSIONS


def _text(value: object) -> str:
    return str(value or "").strip()


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _list(value: object) -> list[object]:
    return value if isinstance(value, list) else []


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _record_payload(record: PublicationEvalRecord | Mapping[str, Any]) -> dict[str, Any]:
    if isinstance(record, PublicationEvalRecord):
        return record.to_dict()
    if isinstance(record, Mapping):
        return dict(record)
    raise TypeError("AI reviewer publication eval workflow record must be a mapping or PublicationEvalRecord")


def _normalize_ref_bundle(
    *,
    manuscript_ref: str | Path,
    evidence_ref: str | Path,
    review_ref: str | Path,
    charter_ref: str | Path,
    additional_refs: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    refs: dict[str, Any] = {}
    for field_name, surface in _REF_ALIASES.items():
        raw_value = {
            "manuscript_ref": manuscript_ref,
            "evidence_ref": evidence_ref,
            "review_ref": review_ref,
            "charter_ref": charter_ref,
        }[field_name]
        value = _text(raw_value)
        if not value:
            raise ValueError(f"AI reviewer publication eval workflow missing {field_name}")
        refs[surface] = value
    for key, value in _mapping(additional_refs).items():
        surface = _text(key)
        if surface == "owner_route_currentness_basis" and isinstance(value, Mapping):
            refs[surface] = dict(value)
            continue
        ref = _text(value)
        if surface and ref:
            refs[surface] = ref
    return refs


def _quality_assessment(payload: Mapping[str, Any]) -> Mapping[str, Any]:
    quality_assessment = payload.get("quality_assessment")
    if not isinstance(quality_assessment, Mapping):
        raise ValueError("AI reviewer publication eval workflow record missing quality_assessment")
    return quality_assessment


def _dimension_payloads(record_payload: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    quality_assessment = _quality_assessment(record_payload)
    contract = build_ai_reviewer_operating_system_contract(DEFAULT_PUBLICATION_CRITIQUE_POLICY)
    dimensions: dict[str, Mapping[str, Any]] = {}
    for dimension in contract["rubric_dimensions"]:
        payload = quality_assessment.get(dimension)
        if not isinstance(payload, Mapping):
            raise ValueError(f"AI reviewer publication eval workflow record missing quality dimension {dimension}")
        dimensions[dimension] = payload
    return dimensions


def _dimension_evidence_refs(
    *,
    dimension_payload: Mapping[str, Any],
    ref_bundle: Mapping[str, str],
) -> list[str]:
    refs = [_text(item) for item in _list(dimension_payload.get("evidence_refs")) if _text(item)]
    if refs:
        return refs
    return [ref_bundle[surface] for surface in _REQUIRED_TRACE_INPUTS if surface in ref_bundle]


def _reject_manuscript_story_provenance_leakage(*, field_path: str, text: str) -> None:
    reject_manuscript_story_provenance_leakage(field_path=field_path, text=text)


def _rubric_scores_and_decision_matrix(
    *,
    dimensions: Mapping[str, Mapping[str, Any]],
    ref_bundle: Mapping[str, str],
) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    rubric_scores: dict[str, dict[str, Any]] = {}
    decision_matrix: list[dict[str, Any]] = []
    for dimension, payload in dimensions.items():
        status = _text(payload.get("status"))
        summary = _text(payload.get("summary"))
        rationale = _text(payload.get("reviewer_reason")) or summary
        if not status:
            raise ValueError(f"AI reviewer publication eval workflow quality dimension {dimension} missing status")
        if not rationale:
            raise ValueError(f"AI reviewer publication eval workflow quality dimension {dimension} missing rationale")
        if dimension in _MANUSCRIPT_STORY_SENSITIVE_DIMENSIONS:
            _reject_manuscript_story_provenance_leakage(
                field_path=f"quality_assessment.{dimension}.summary",
                text=summary,
            )
            _reject_manuscript_story_provenance_leakage(
                field_path=f"quality_assessment.{dimension}.reviewer_reason",
                text=rationale,
            )
            _reject_manuscript_story_provenance_leakage(
                field_path=f"quality_assessment.{dimension}.reviewer_revision_advice",
                text=_text(payload.get("reviewer_revision_advice")),
            )
        evidence_refs = _dimension_evidence_refs(dimension_payload=payload, ref_bundle=ref_bundle)
        rubric_scores[dimension] = {
            "status": status,
            "rationale": rationale,
            "evidence_refs": evidence_refs,
        }
        decision_matrix.append(
            {
                "dimension": dimension,
                "status": status,
                "rationale": rationale,
            }
        )
    return rubric_scores, decision_matrix


def _route_back_decision(record_payload: Mapping[str, Any]) -> dict[str, str]:
    recommended_action = "continue_same_line"
    route_rationale = "AI reviewer publication eval workflow trace is complete."
    route_target: str | None = None
    reviewer_os = _mapping(record_payload.get("reviewer_operating_system"))
    sci_review = record_payload.get("sci_clinical_registry_review") or reviewer_os.get("sci_clinical_registry_review")
    if isinstance(sci_review, list):
        sci_blockers = _sci_registry_review_blockers([item for item in sci_review if isinstance(item, Mapping)])
        if sci_blockers:
            route_target = "analysis-campaign"
            for item in sci_review:
                if not isinstance(item, Mapping):
                    continue
                disposition = _text(item.get("required_disposition"))
                if disposition in {"route_back_write", "downgrade_claim", "repair_citation"}:
                    route_target = "write"
                    break
                if disposition == "route_back_review":
                    route_target = "review"
                    break
            return {
                "recommended_action": "route_back_same_line",
                "route_target": route_target,
                "rationale": "SCI clinical registry review has major or blocker concerns requiring same-line repair.",
            }
    actions = [item for item in _list(record_payload.get("recommended_actions")) if isinstance(item, Mapping)]
    if actions:
        recommended_action = _text(actions[0].get("action_type")) or _text(actions[0].get("action_id")) or recommended_action
        route_rationale = _text(actions[0].get("reason")) or route_rationale
        route_target = _text(actions[0].get("route_target")) or None
    decision = {
        "recommended_action": recommended_action,
        "rationale": route_rationale,
    }
    if route_target and recommended_action in {"route_back_same_line", "bounded_analysis", "stop_loss"}:
        decision["route_target"] = route_target
    return decision



def _record_payload_without_workflow_only_fields(record_payload: Mapping[str, Any]) -> dict[str, Any]:
    payload = {key: value for key, value in record_payload.items() if key in _RECORD_ALLOWED_FIELDS}
    provenance = payload.get("assessment_provenance")
    if isinstance(provenance, Mapping):
        payload["assessment_provenance"] = {
            key: value for key, value in provenance.items() if key in _ASSESSMENT_PROVENANCE_ALLOWED_FIELDS
        }
    return payload


def build_ai_reviewer_publication_eval_workflow_trace(
    *,
    study_root: str | Path,
    manuscript_ref: str | Path,
    evidence_ref: str | Path,
    review_ref: str | Path,
    charter_ref: str | Path,
    record: PublicationEvalRecord | Mapping[str, Any],
    additional_refs: Mapping[str, Any] | None = None,
    workflow_currentness_mode: str | None = None,
) -> dict[str, Any]:
    resolved_study_root = Path(study_root).expanduser().resolve()
    record_payload = _record_payload(record)
    ref_bundle = _normalize_ref_bundle(
        manuscript_ref=manuscript_ref,
        evidence_ref=evidence_ref,
        review_ref=review_ref,
        charter_ref=charter_ref,
        additional_refs=additional_refs,
    )
    contract = build_ai_reviewer_operating_system_contract(DEFAULT_PUBLICATION_CRITIQUE_POLICY)
    dimensions = _dimension_payloads(record_payload)
    for surface in contract["required_input_surfaces"]:
        if surface not in ref_bundle:
            raise ValueError(f"AI reviewer publication eval workflow missing input ref for {surface}")

    rubric_scores, decision_matrix = _rubric_scores_and_decision_matrix(
        dimensions=dimensions,
        ref_bundle=ref_bundle,
    )

    trace = {
        "contract_id": contract["contract_id"],
        "input_bundle": ref_bundle,
        "rubric_scores": rubric_scores,
        "decision_matrix": decision_matrix,
        "currentness_checks": _currentness_checks(
            study_root=resolved_study_root,
            record_payload=record_payload,
            ref_bundle=ref_bundle,
            workflow_currentness_mode=workflow_currentness_mode,
        ),
        "claim_evidence_alignment": build_claim_evidence_alignment_gate(
            study_root=resolved_study_root,
            claim_evidence_map_ref=ref_bundle["claim_evidence_map"],
            evidence_ledger_ref=ref_bundle["evidence_ledger"],
        ),
        "sci_clinical_registry_review": _sci_clinical_registry_review(record_payload),
        "future_facing_limitations_plan": _future_facing_limitations_plan(record_payload),
        "provenance_checks": {
            "assessment_owner": "ai_reviewer",
            "policy_id": DEFAULT_PUBLICATION_CRITIQUE_POLICY["policy_id"],
            "ai_reviewer_required": False,
            "mechanical_projection_used_as_quality_authority": False,
        },
        "route_back_decision": _route_back_decision(record_payload),
    }
    trace["publication_quality_readiness"] = _publication_quality_readiness(
        study_root=resolved_study_root,
        record_payload=record_payload,
        trace=trace,
    )
    errors = validate_ai_reviewer_operating_system_trace(trace)
    if errors:
        raise ValueError("AI reviewer publication eval workflow reviewer OS trace invalid: " + "; ".join(errors))
    return trace


def _record_with_trace(
    *,
    record: PublicationEvalRecord | Mapping[str, Any],
    trace: Mapping[str, Any],
    emitted_at: str | None = None,
) -> dict[str, Any]:
    payload = _record_payload_without_workflow_only_fields(_record_payload(record))
    if emitted_at is not None:
        payload["emitted_at"] = emitted_at
    payload["reviewer_operating_system"] = dict(trace)
    provenance = dict(_mapping(payload.get("assessment_provenance")))
    provenance["owner"] = "ai_reviewer"
    provenance["source_kind"] = "publication_eval_ai_reviewer"
    provenance["policy_id"] = DEFAULT_PUBLICATION_CRITIQUE_POLICY["policy_id"]
    provenance["ai_reviewer_required"] = False
    owner_route_currentness_basis = _mapping(_mapping(trace.get("input_bundle")).get("owner_route_currentness_basis"))
    if owner_route_currentness_basis:
        provenance["owner_route_currentness_basis"] = dict(owner_route_currentness_basis)
        provenance["work_unit_id"] = _text(owner_route_currentness_basis.get("work_unit_id"))
        provenance["work_unit_fingerprint"] = _text(owner_route_currentness_basis.get("work_unit_fingerprint"))
    payload["assessment_provenance"] = provenance
    workflow_ref = _mapping(payload.get("reviewer_operating_system")).get("input_bundle")
    publication_gate_projection_ref = _text(_mapping(workflow_ref).get("publication_gate_projection"))
    if publication_gate_projection_ref:
        provenance["source_refs"] = list(
            dict.fromkeys([*(_list(provenance.get("source_refs"))), publication_gate_projection_ref])
        )
    return payload


def build_ai_reviewer_publication_eval_record_with_workflow_trace(
    *,
    study_root: str | Path,
    manuscript_ref: str | Path,
    evidence_ref: str | Path,
    review_ref: str | Path,
    charter_ref: str | Path,
    record: PublicationEvalRecord | Mapping[str, Any],
    additional_refs: Mapping[str, Any] | None = None,
    workflow_currentness_mode: str | None = None,
    emitted_at: str | None = None,
) -> dict[str, Any]:
    resolved_study_root = Path(study_root).expanduser().resolve()
    trace = build_ai_reviewer_publication_eval_workflow_trace(
        study_root=resolved_study_root,
        manuscript_ref=manuscript_ref,
        evidence_ref=evidence_ref,
        review_ref=review_ref,
        charter_ref=charter_ref,
        record=record,
        additional_refs=additional_refs,
        workflow_currentness_mode=workflow_currentness_mode,
    )
    return _record_with_trace(
        record=record,
        trace=trace,
        emitted_at=emitted_at or _utc_now(),
    )


def run_ai_reviewer_publication_eval_workflow(
    *,
    study_root: str | Path,
    manuscript_ref: str | Path,
    evidence_ref: str | Path,
    review_ref: str | Path,
    charter_ref: str | Path,
    record: PublicationEvalRecord | Mapping[str, Any],
    additional_refs: Mapping[str, Any] | None = None,
    workflow_currentness_mode: str | None = None,
) -> dict[str, Any]:
    resolved_study_root = Path(study_root).expanduser().resolve()
    record_with_trace = build_ai_reviewer_publication_eval_record_with_workflow_trace(
        study_root=resolved_study_root,
        manuscript_ref=manuscript_ref,
        evidence_ref=evidence_ref,
        review_ref=review_ref,
        charter_ref=charter_ref,
        record=record,
        additional_refs=additional_refs,
        workflow_currentness_mode=workflow_currentness_mode,
    )
    trace = _mapping(record_with_trace.get("reviewer_operating_system"))
    materialized = materialize_ai_reviewer_publication_eval_latest(
        study_root=resolved_study_root,
        record=record_with_trace,
    )
    paper_authority_migration.mark_cutover_new_mas_authority_established(
        study_root=resolved_study_root,
        publication_eval_ref=materialized["artifact_path"],
        eval_id=materialized["eval_id"],
    )
    return {
        "surface": _SURFACE,
        "schema_version": _SCHEMA_VERSION,
        "status": "materialized",
        "study_root": str(resolved_study_root),
        "publication_eval_surface": "artifacts/publication_eval/latest.json",
        "artifact_path": materialized["artifact_path"],
        "eval_id": materialized["eval_id"],
        "record": record_with_trace,
        "reviewer_operating_system": trace,
    }
