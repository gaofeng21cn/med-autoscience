from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from med_autoscience.policies import (
    DEFAULT_PUBLICATION_CRITIQUE_POLICY,
    build_ai_reviewer_operating_system_contract,
)
from med_autoscience.publication_eval_latest import (
    materialize_ai_reviewer_publication_eval_latest,
)
from med_autoscience.publication_eval_reviewer_os import (
    validate_ai_reviewer_operating_system_trace,
)
from med_autoscience.publication_eval_record import PublicationEvalRecord

__all__ = [
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


def _text(value: object) -> str:
    return str(value or "").strip()


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _list(value: object) -> list[object]:
    return value if isinstance(value, list) else []


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
) -> dict[str, str]:
    refs: dict[str, str] = {}
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
    actions = [item for item in _list(record_payload.get("recommended_actions")) if isinstance(item, Mapping)]
    if actions:
        recommended_action = _text(actions[0].get("action_type")) or _text(actions[0].get("action_id")) or recommended_action
        route_rationale = _text(actions[0].get("reason")) or route_rationale
    return {
        "recommended_action": recommended_action,
        "rationale": route_rationale,
    }


def build_ai_reviewer_publication_eval_workflow_trace(
    *,
    manuscript_ref: str | Path,
    evidence_ref: str | Path,
    review_ref: str | Path,
    charter_ref: str | Path,
    record: PublicationEvalRecord | Mapping[str, Any],
    additional_refs: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
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
        "provenance_checks": {
            "assessment_owner": "ai_reviewer",
            "policy_id": DEFAULT_PUBLICATION_CRITIQUE_POLICY["policy_id"],
            "ai_reviewer_required": False,
            "mechanical_projection_used_as_quality_authority": False,
        },
        "route_back_decision": _route_back_decision(record_payload),
    }
    errors = validate_ai_reviewer_operating_system_trace(trace)
    if errors:
        raise ValueError("AI reviewer publication eval workflow reviewer OS trace invalid: " + "; ".join(errors))
    return trace


def _record_with_trace(
    *,
    record: PublicationEvalRecord | Mapping[str, Any],
    trace: Mapping[str, Any],
) -> dict[str, Any]:
    payload = _record_payload(record)
    payload["reviewer_operating_system"] = dict(trace)
    provenance = dict(_mapping(payload.get("assessment_provenance")))
    provenance["owner"] = "ai_reviewer"
    provenance["policy_id"] = DEFAULT_PUBLICATION_CRITIQUE_POLICY["policy_id"]
    provenance["ai_reviewer_required"] = False
    payload["assessment_provenance"] = provenance
    return payload


def run_ai_reviewer_publication_eval_workflow(
    *,
    study_root: str | Path,
    manuscript_ref: str | Path,
    evidence_ref: str | Path,
    review_ref: str | Path,
    charter_ref: str | Path,
    record: PublicationEvalRecord | Mapping[str, Any],
    additional_refs: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    resolved_study_root = Path(study_root).expanduser().resolve()
    trace = build_ai_reviewer_publication_eval_workflow_trace(
        manuscript_ref=manuscript_ref,
        evidence_ref=evidence_ref,
        review_ref=review_ref,
        charter_ref=charter_ref,
        record=record,
        additional_refs=additional_refs,
    )
    materialized = materialize_ai_reviewer_publication_eval_latest(
        study_root=resolved_study_root,
        record=_record_with_trace(record=record, trace=trace),
    )
    return {
        "surface": _SURFACE,
        "schema_version": _SCHEMA_VERSION,
        "status": "materialized",
        "study_root": str(resolved_study_root),
        "publication_eval_surface": "artifacts/publication_eval/latest.json",
        "artifact_path": materialized["artifact_path"],
        "eval_id": materialized["eval_id"],
        "reviewer_operating_system": trace,
    }
