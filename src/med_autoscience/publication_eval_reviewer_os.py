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
        "claim_evidence_alignment",
        "publication_quality_readiness",
        "future_facing_limitations_plan",
        "provenance_checks",
        "route_back_decision",
    }
)
_ROUTE_TARGET_ALIASES = {
    "analysis": "analysis-campaign",
    "analysis_campaign": "analysis-campaign",
    "bounded_analysis": "analysis-campaign",
}
_ACTION_TYPES_THAT_ROUTE_BACK = frozenset({"route_back_same_line", "bounded_analysis", "stop_loss"})
_ROUTE_BACK_TARGETS = frozenset({"write", "analysis-campaign", "finalize", "publication_eval", "stop"})


def _text(value: object) -> str:
    return str(value or "").strip()


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _list_of_mappings(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [dict(item) for item in value if isinstance(item, dict)]


def _normalized_route_target(value: object) -> str:
    text = _text(value)
    return _ROUTE_TARGET_ALIASES.get(text, text)


def _list_has_items(value: object) -> bool:
    return isinstance(value, list) and bool(value)


def current_ai_reviewer_route_back_action(publication_eval_payload: object) -> dict[str, Any] | None:
    if not isinstance(publication_eval_payload, dict):
        return None
    reviewer_os = _mapping(publication_eval_payload.get("reviewer_operating_system"))
    currentness_checks = _mapping(reviewer_os.get("currentness_checks"))
    medical_prose_review = _mapping(currentness_checks.get("medical_prose_review"))
    prose_current = _text(medical_prose_review.get("status")) == "current"
    current_manuscript = _mapping(currentness_checks.get("current_manuscript"))
    manuscript_current = _text(current_manuscript.get("status")) == "current"
    if not prose_current and not manuscript_current:
        return None
    if prose_current and medical_prose_review.get("route_back_required") is not True:
        return None
    if prose_current:
        for field in ("request_digest", "manuscript_ref", "manuscript_digest"):
            if not _text(medical_prose_review.get(field)):
                return None
    if manuscript_current:
        for field in ("manuscript_ref", "manuscript_digest"):
            if not _text(current_manuscript.get(field)):
                return None
    prose_route_target = _normalized_route_target(medical_prose_review.get("route_target"))
    if prose_route_target == "review":
        return None
    actions = publication_eval_payload.get("recommended_actions")
    if not isinstance(actions, list):
        return None
    for action in actions:
        if not isinstance(action, dict):
            continue
        if action.get("requires_controller_decision") is not True:
            continue
        if _text(action.get("action_type")) not in _ACTION_TYPES_THAT_ROUTE_BACK:
            continue
        action_route_target = _normalized_route_target(action.get("route_target"))
        if not action_route_target or action_route_target == "review":
            continue
        if manuscript_current and not prose_route_target:
            payload = dict(action)
            payload["route_target"] = action_route_target
            return payload
        if action_route_target == prose_route_target or prose_route_target in {"", "analysis-campaign"}:
            payload = dict(action)
            payload["route_target"] = action_route_target
            return payload
    return None


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
    if medical_prose_review.get("route_back_required") is True:
        route_target = _normalized_route_target(medical_prose_review.get("route_target"))
        if route_target not in _ROUTE_BACK_TARGETS:
            errors.append(
                "reviewer_operating_system.currentness_checks.medical_prose_review.route_target "
                "must name the current route target when route_back_required is true"
            )
    current_manuscript = _mapping(currentness_checks.get("current_manuscript"))
    if not current_manuscript:
        errors.append("reviewer_operating_system.currentness_checks.current_manuscript must be non-empty")
    else:
        if _text(current_manuscript.get("status")) != "current":
            errors.append("reviewer_operating_system.currentness_checks.current_manuscript.status must be current")
        for field in ("manuscript_ref", "manuscript_digest"):
            if not _text(current_manuscript.get(field)):
                errors.append(
                    f"reviewer_operating_system.currentness_checks.current_manuscript.{field} must be non-empty"
                )
        prose_digest = _text(medical_prose_review.get("manuscript_digest"))
        current_digest = _text(current_manuscript.get("manuscript_digest"))
        if prose_digest and current_digest and prose_digest != current_digest:
            errors.append(
                "reviewer_operating_system.currentness_checks.current_manuscript.manuscript_digest "
                "must match medical_prose_review.manuscript_digest"
            )
    source_eval = _mapping(currentness_checks.get("source_eval"))
    if not source_eval:
        errors.append("reviewer_operating_system.currentness_checks.source_eval must be non-empty")
    else:
        if _text(source_eval.get("status")) != "current":
            errors.append("reviewer_operating_system.currentness_checks.source_eval.status must be current")
        if not _text(source_eval.get("eval_id")):
            errors.append("reviewer_operating_system.currentness_checks.source_eval.eval_id must be non-empty")
    package_freshness = _mapping(currentness_checks.get("current_package_freshness"))
    if not package_freshness:
        errors.append("reviewer_operating_system.currentness_checks.current_package_freshness must be non-empty")
    elif _text(package_freshness.get("status")) not in {"fresh", "downstream_pending"}:
        errors.append(
            "reviewer_operating_system.currentness_checks.current_package_freshness.status must be fresh or downstream_pending"
        )
    elif not _text(package_freshness.get("source_eval_id")):
        errors.append(
            "reviewer_operating_system.currentness_checks.current_package_freshness.source_eval_id must be non-empty"
        )
    source_eval_id = _text(source_eval.get("eval_id"))
    package_source_eval_id = _text(package_freshness.get("source_eval_id"))
    if source_eval_id and package_source_eval_id and source_eval_id != package_source_eval_id:
        errors.append(
            "reviewer_operating_system.currentness_checks.current_package_freshness.source_eval_id "
            "must match source_eval.eval_id"
        )

    claim_alignment = _mapping(payload.get("claim_evidence_alignment"))
    if claim_alignment.get("surface_kind") != "claim_evidence_alignment_gate_v1":
        errors.append(
            "reviewer_operating_system.claim_evidence_alignment.surface_kind must be claim_evidence_alignment_gate_v1"
        )
    if _text(claim_alignment.get("source_project")) != "academic-research-skills":
        errors.append("reviewer_operating_system.claim_evidence_alignment.source_project must be academic-research-skills")
    if _text(claim_alignment.get("absorbed_as")) != "mas_native_claim_evidence_alignment_gate":
        errors.append(
            "reviewer_operating_system.claim_evidence_alignment.absorbed_as must be mas_native_claim_evidence_alignment_gate"
        )
    claim_alignment_status = _text(claim_alignment.get("status"))
    if claim_alignment_status not in {"ready", "blocked"}:
        errors.append("reviewer_operating_system.claim_evidence_alignment.status must be ready or blocked")
    if claim_alignment.get("fail_closed_when_missing") is not True:
        errors.append("reviewer_operating_system.claim_evidence_alignment.fail_closed_when_missing must be true")
    if claim_alignment.get("body_included") is not False:
        errors.append("reviewer_operating_system.claim_evidence_alignment.body_included must be false")
    if claim_alignment.get("may_authorize_publication_readiness") is not False:
        errors.append(
            "reviewer_operating_system.claim_evidence_alignment.may_authorize_publication_readiness must be false"
        )
    if claim_alignment.get("may_authorize_quality_verdict") is not False:
        errors.append("reviewer_operating_system.claim_evidence_alignment.may_authorize_quality_verdict must be false")
    if claim_alignment.get("can_write_domain_truth") is not False:
        errors.append("reviewer_operating_system.claim_evidence_alignment.can_write_domain_truth must be false")
    if not isinstance(claim_alignment.get("claim_count"), int) or claim_alignment.get("claim_count") < 1:
        errors.append("reviewer_operating_system.claim_evidence_alignment.claim_count must be positive")
    if not isinstance(claim_alignment.get("aligned_claim_count"), int) or claim_alignment.get("aligned_claim_count") < 0:
        errors.append("reviewer_operating_system.claim_evidence_alignment.aligned_claim_count must be non-negative")
    elif isinstance(claim_alignment.get("claim_count"), int) and claim_alignment.get("aligned_claim_count") > claim_alignment.get("claim_count"):
        errors.append("reviewer_operating_system.claim_evidence_alignment.aligned_claim_count must not exceed claim_count")
    if claim_alignment_status == "ready":
        if claim_alignment.get("missing_required_fields") not in ([], ()):
            errors.append("reviewer_operating_system.claim_evidence_alignment.missing_required_fields must be empty when ready")
        if claim_alignment.get("blockers") not in ([], ()):
            errors.append("reviewer_operating_system.claim_evidence_alignment.blockers must be empty when ready")
        if claim_alignment.get("aligned_claim_count") != claim_alignment.get("claim_count"):
            errors.append("reviewer_operating_system.claim_evidence_alignment.aligned_claim_count must equal claim_count when ready")
    elif claim_alignment_status == "blocked" and not (
        _list_has_items(claim_alignment.get("missing_required_fields"))
        or _list_has_items(claim_alignment.get("blockers"))
    ):
        errors.append(
            "reviewer_operating_system.claim_evidence_alignment blocked status requires missing_required_fields or blockers"
        )

    readiness = _mapping(payload.get("publication_quality_readiness"))
    if readiness.get("surface_kind") != "publication_quality_authority_kernel_v1":
        errors.append(
            "reviewer_operating_system.publication_quality_readiness.surface_kind must be publication_quality_authority_kernel_v1"
        )
    readiness_status = _text(readiness.get("status"))
    if readiness_status not in {"ready", "blocked"}:
        errors.append("reviewer_operating_system.publication_quality_readiness.status must be ready or blocked")
    if not _text(readiness.get("current_manuscript_digest")):
        errors.append(
            "reviewer_operating_system.publication_quality_readiness.current_manuscript_digest must be non-empty"
        )
    if not _text(readiness.get("review_request_digest")):
        errors.append(
            "reviewer_operating_system.publication_quality_readiness.review_request_digest must be non-empty"
        )
    if not _text(readiness.get("evidence_ledger_digest")):
        errors.append(
            "reviewer_operating_system.publication_quality_readiness.evidence_ledger_digest must be non-empty"
        )
    if not _text(readiness.get("claim_evidence_alignment_digest")):
        errors.append(
            "reviewer_operating_system.publication_quality_readiness.claim_evidence_alignment_digest must be non-empty"
        )
    if _text(readiness.get("rubric_version")) != DEFAULT_PUBLICATION_CRITIQUE_POLICY["policy_id"]:
        errors.append(
            "reviewer_operating_system.publication_quality_readiness.rubric_version must be medical_publication_critique_v1"
        )
    if not _text(readiness.get("owner_attempt_id")):
        errors.append(
            "reviewer_operating_system.publication_quality_readiness.owner_attempt_id must be non-empty"
        )
    if readiness.get("fail_closed_when_missing") is not True:
        errors.append(
            "reviewer_operating_system.publication_quality_readiness.fail_closed_when_missing must be true"
        )
    if readiness_status == "ready" and readiness.get("missing_required_fields") not in ([], ()):
        errors.append(
            "reviewer_operating_system.publication_quality_readiness.missing_required_fields must be empty when ready"
        )
    if readiness_status == "blocked" and not _list_has_items(readiness.get("missing_required_fields")):
        errors.append(
            "reviewer_operating_system.publication_quality_readiness blocked status requires missing_required_fields"
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
    decision_route_target = _normalized_route_target(route_back_decision.get("route_target"))
    prose_route_target = _normalized_route_target(medical_prose_review.get("route_target"))
    if _text(route_back_decision.get("recommended_action")) in _ACTION_TYPES_THAT_ROUTE_BACK:
        if decision_route_target not in _ROUTE_BACK_TARGETS:
            errors.append("reviewer_operating_system.route_back_decision.route_target must name the current route target")
        elif prose_route_target and prose_route_target != decision_route_target:
            errors.append(
                "reviewer_operating_system.route_back_decision.route_target must match "
                "currentness_checks.medical_prose_review.route_target"
            )
    if (
        claim_alignment_status == "blocked" or readiness_status == "blocked"
    ) and _text(route_back_decision.get("recommended_action")) not in _ACTION_TYPES_THAT_ROUTE_BACK:
        errors.append(
            "reviewer_operating_system.route_back_decision.recommended_action must route back when readiness is blocked"
        )

    return errors


__all__ = ["validate_ai_reviewer_operating_system_trace"]
