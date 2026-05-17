from __future__ import annotations

from typing import Any

from med_autoscience.policies import (
    DEFAULT_PUBLICATION_CRITIQUE_POLICY,
    build_ai_reviewer_operating_system_contract,
)


_ALLOWED_REVIEWER_OS_FIELDS = frozenset(
    {
        "contract_id",
        "input_bundle",
        "rubric_scores",
        "decision_matrix",
        "currentness_checks",
        "future_facing_limitations_plan",
        "provenance_checks",
        "route_back_decision",
    }
)


def _text(value: object) -> str:
    return str(value or "").strip()


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _list_of_mappings(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [dict(item) for item in value if isinstance(item, dict)]


def validate_ai_reviewer_operating_system_trace(payload: object) -> list[str]:
    if not isinstance(payload, dict):
        return ["reviewer_operating_system must be an object"]

    errors: list[str] = []
    unknown_fields = sorted(set(payload) - _ALLOWED_REVIEWER_OS_FIELDS)
    if unknown_fields:
        errors.append("reviewer_operating_system contains unknown fields: " + ", ".join(unknown_fields))

    contract = build_ai_reviewer_operating_system_contract(DEFAULT_PUBLICATION_CRITIQUE_POLICY)
    if _text(payload.get("contract_id")) != contract["contract_id"]:
        errors.append(f"reviewer_operating_system.contract_id must be {contract['contract_id']}")

    input_bundle = _mapping(payload.get("input_bundle"))
    present_inputs = {key for key, value in input_bundle.items() if value}
    for surface in contract["required_input_surfaces"]:
        if surface not in present_inputs:
            errors.append(f"reviewer_operating_system.input_bundle missing {surface}")

    rubric_scores = _mapping(payload.get("rubric_scores"))
    for dimension in contract["rubric_dimensions"]:
        score = rubric_scores.get(dimension)
        if not isinstance(score, dict):
            errors.append(f"reviewer_operating_system.rubric_scores missing {dimension}")
            continue
        if not _text(score.get("status")):
            errors.append(f"reviewer_operating_system.rubric_scores.{dimension}.status must be non-empty")
        if not _text(score.get("rationale")):
            errors.append(f"reviewer_operating_system.rubric_scores.{dimension}.rationale must be non-empty")
        if not score.get("evidence_refs"):
            errors.append(f"reviewer_operating_system.rubric_scores.{dimension}.evidence_refs must not be empty")

    decision_matrix = _list_of_mappings(payload.get("decision_matrix"))
    if not decision_matrix:
        errors.append("reviewer_operating_system.decision_matrix must not be empty")
    covered_dimensions = {_text(item.get("dimension")) for item in decision_matrix}
    for dimension in contract["rubric_dimensions"]:
        if dimension not in covered_dimensions:
            errors.append(f"reviewer_operating_system.decision_matrix missing {dimension}")

    currentness_checks = _mapping(payload.get("currentness_checks"))
    if not currentness_checks:
        errors.append("reviewer_operating_system.currentness_checks must be non-empty")
    medical_prose_review = _mapping(currentness_checks.get("medical_prose_review"))
    for field in ("request_digest", "manuscript_ref", "manuscript_digest"):
        if not _text(medical_prose_review.get(field)):
            errors.append(f"reviewer_operating_system.currentness_checks.medical_prose_review.{field} must be non-empty")
    medical_prose_review_status = _text(medical_prose_review.get("status"))
    if medical_prose_review_status not in {"current", "ready", "requested"}:
        errors.append("reviewer_operating_system.currentness_checks.medical_prose_review.status must be current or requested")
    if medical_prose_review_status == "requested":
        if _text(medical_prose_review.get("authority_source_signature")) != "paper_authority_clean_migration":
            errors.append(
                "reviewer_operating_system.currentness_checks.medical_prose_review.requested status "
                "requires paper_authority_clean_migration authority_source_signature"
            )
        if not _text(medical_prose_review.get("request_ref")):
            errors.append(
                "reviewer_operating_system.currentness_checks.medical_prose_review.request_ref must be non-empty "
                "when status is requested"
            )
        if medical_prose_review.get("route_back_required") is not True:
            errors.append(
                "reviewer_operating_system.currentness_checks.medical_prose_review.route_back_required must be true "
                "when status is requested"
            )
    package_freshness = _mapping(currentness_checks.get("current_package_freshness"))
    if not package_freshness:
        errors.append("reviewer_operating_system.currentness_checks.current_package_freshness must be non-empty")
    elif _text(package_freshness.get("status")) != "fresh":
        errors.append("reviewer_operating_system.currentness_checks.current_package_freshness.status must be fresh")
    elif not _text(package_freshness.get("source_eval_id")):
        errors.append(
            "reviewer_operating_system.currentness_checks.current_package_freshness.source_eval_id must be non-empty"
        )

    future_limitations_plan = _list_of_mappings(payload.get("future_facing_limitations_plan"))
    future_limitations_contract = _mapping(contract.get("future_facing_limitations_plan"))
    required_future_limitations_fields = tuple(
        _text(item) for item in future_limitations_contract.get("required_fields", []) if _text(item)
    )
    if not future_limitations_plan:
        errors.append("reviewer_operating_system.future_facing_limitations_plan must not be empty")
    for index, item in enumerate(future_limitations_plan):
        for field in required_future_limitations_fields:
            if field == "current_manuscript_wording_must_be_restrained":
                if field not in item or item.get(field) is None:
                    errors.append(
                        "reviewer_operating_system.future_facing_limitations_plan"
                        f"[{index}].{field} must be present"
                    )
                continue
            if not _text(item.get(field)):
                errors.append(
                    "reviewer_operating_system.future_facing_limitations_plan"
                    f"[{index}].{field} must be non-empty"
                )

    provenance_checks = _mapping(payload.get("provenance_checks"))
    required_provenance = _mapping(contract.get("required_provenance"))
    if provenance_checks.get("assessment_owner") != required_provenance.get("assessment_owner"):
        errors.append("reviewer_operating_system.provenance_checks.assessment_owner must be ai_reviewer")
    if provenance_checks.get("policy_id") != required_provenance.get("policy_id"):
        errors.append("reviewer_operating_system.provenance_checks.policy_id must be medical_publication_critique_v1")
    if provenance_checks.get("ai_reviewer_required") is not False:
        errors.append("reviewer_operating_system.provenance_checks.ai_reviewer_required must be false")
    if provenance_checks.get("mechanical_projection_used_as_quality_authority") is not False:
        errors.append(
            "reviewer_operating_system.provenance_checks.mechanical_projection_used_as_quality_authority must be false"
        )

    route_back_decision = _mapping(payload.get("route_back_decision"))
    if not _text(route_back_decision.get("recommended_action")):
        errors.append("reviewer_operating_system.route_back_decision.recommended_action must be non-empty")
    if not _text(route_back_decision.get("rationale")):
        errors.append("reviewer_operating_system.route_back_decision.rationale must be non-empty")

    return errors


__all__ = ["validate_ai_reviewer_operating_system_trace"]
