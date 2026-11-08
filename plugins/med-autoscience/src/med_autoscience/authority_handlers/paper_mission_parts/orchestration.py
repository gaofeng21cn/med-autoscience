"""Evaluate exact MAS paper-mission records without transport or I/O."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .._generation_manifest import (
    EPISTEMIC_AUTHORITY_BOUNDARY,
    FIRST_DRAFT_QUALITY_ROUTE_PRIORITY,
    PROFESSIONAL_MANUSCRIPT_SKILL_INPUT_ROLES,
    PROFESSIONAL_MANUSCRIPT_SKILL_ROLES,
    REVIEW_LANE_ORDER,
    REVIEW_LANES_BY_SCOPE,
    epistemic_review_dependency_refs,
    first_draft_applicable_ref_fields,
    normalize_generation_manifest,
    require_stage_scope,
    review_scope_member_projection,
    source_input_digest,
)
from .._record_validation import (
    RequestShapeError,
    canonical_json_bytes,
    dedupe,
    enum_text,
    exact_ref as _exact_ref,
    exact_ref_list as _exact_ref_list,
    exact_keys,
    fingerprint,
    integer,
    mapping,
    optional_sha256,
    optional_text,
    optional_typed_ref as _optional_typed_ref,
    sequence,
    sha256,
    text,
    text_list,
    typed_ref as _typed_ref,
    typed_ref_list as _typed_ref_list,
)
from ..candidate_admission import normalize_candidate_admission_receipt

from .constants import (
    _HARD_GATE_KINDS,
)
from .quality import (
    _aggregate_review_status,
    _first_draft_quality_issue,
    _professional_figure_skill_quality_debt,
    _professional_manuscript_skill_quality_debt,
    _review_quality_debt,
    _reviewer_revision_generation_issue,
)
from .receipt import (
    _owner_receipt,
)
from .request import (
    _is_reviewer_revision,
    _normalize_request,
)
from .result import (
    _finalize,
    _first_draft_quality_debt_result,
    _human_gate,
    _invalid_host_input,
    _professional_skill_debt_result,
    _quality_debt,
    _route_back,
    _route_result,
    _stage_outcome,
    _typed_blocker,
)
from .validation import (
    _candidate_admission_issue,
    _review_currentness_issue,
    _revision_consumption_issue,
    _validate_cross_record_lineage,
)

def evaluate_paper_mission_authority(request: Mapping[str, Any]) -> dict[str, Any]:
    """Return a deterministic owner result over host-injected exact records."""

    try:
        normalized = _normalize_request(request)
        _validate_cross_record_lineage(normalized)
    except RequestShapeError as error:
        return _invalid_host_input(str(error))

    hard_gate = normalized["hard_gate"]
    if hard_gate["kind"] == "human_decision":
        return _finalize(
            normalized,
            status="human_gate",
            stage_outcome=_stage_outcome("human_gate", transition_allowed=False),
            human_gate=_human_gate(normalized),
        )
    if hard_gate["kind"] in _HARD_GATE_KINDS:
        return _finalize(
            normalized,
            status="typed_blocker",
            stage_outcome=_stage_outcome("typed_blocker", transition_allowed=False),
            typed_blocker=_typed_blocker(normalized),
        )

    evidence = normalized["medical_evidence"]
    if evidence["source_readiness_status"] != "ready":
        return _route_result(
            normalized,
            reason_code="source_readiness_record_required",
            next_owner="mas_source_readiness_owner",
            resume_condition="provide a current MAS source-readiness receipt",
        )
    if evidence["claim_evidence_status"] != "aligned":
        return _route_result(
            normalized,
            reason_code="claim_evidence_alignment_required",
            next_owner="mission_executor",
            resume_condition="repair claim boundaries against accepted evidence",
        )
    if not evidence["evidence_refs"] and not evidence["negative_result_refs"]:
        return _route_result(
            normalized,
            reason_code="medical_evidence_record_required",
            next_owner="mission_executor",
            resume_condition="provide accepted evidence or a negative-result record",
        )

    # Admission is a pre-authoring gate and is evaluated before hosted output state.
    candidate_issue = _candidate_admission_issue(normalized)
    if candidate_issue is not None:
        return _route_result(
            normalized,
            reason_code=candidate_issue[0],
            next_owner="mas_candidate_admission_owner",
            resume_condition=candidate_issue[1],
        )

    first_draft_issue = _first_draft_quality_issue(normalized)
    if first_draft_issue is not None:
        return _first_draft_quality_debt_result(
            normalized,
            next_owner=first_draft_issue[0],
            reason_codes=first_draft_issue[1],
            resume_condition=first_draft_issue[2],
        )

    revision_generation_issue = _reviewer_revision_generation_issue(normalized)
    if revision_generation_issue is not None:
        return _first_draft_quality_debt_result(
            normalized,
            next_owner=revision_generation_issue[0],
            reason_codes=revision_generation_issue[1],
            resume_condition=revision_generation_issue[2],
        )

    host = normalized["host_context"]
    if host["output_state"] != "consumable" or not evidence["candidate_artifact_refs"]:
        if normalized["mission"]["stage_id"] == "finalize_and_publication_handoff":
            return _route_result(
                normalized,
                reason_code="consumable_output_missing",
                next_owner="mission_executor",
                resume_condition="produce the complete publication-generation output",
            )
        route_back = _route_back(
            normalized,
            reason_code="consumable_output_missing",
            next_owner="mission_executor",
            resume_condition="produce a readable candidate output bound to the hosted attempt",
        )
        return _finalize(
            normalized,
            status="completed_with_quality_debt",
            stage_outcome=_stage_outcome(
                "completed_with_quality_debt", transition_allowed=True
            ),
            route_back=route_back,
            quality_debt=_quality_debt(
                normalized, reason_codes=["consumable_output_missing"]
            ),
        )

    professional_debt = _professional_manuscript_skill_quality_debt(normalized)
    if professional_debt:
        return _professional_skill_debt_result(
            normalized,
            reason_codes=professional_debt,
            resume_condition=(
                "consume every required manuscript, statistical, table, and submission "
                "Skill and bind its receipt to the exact generation artifacts"
            ),
        )
    professional_figure_debt = _professional_figure_skill_quality_debt(normalized)
    if professional_figure_debt:
        return _professional_skill_debt_result(
            normalized,
            reason_codes=professional_figure_debt,
            resume_condition=(
                "consume the required professional Figure Skills and bind their "
                "receipts to the exact final figure bytes"
            ),
        )

    review_issue = _review_currentness_issue(normalized)
    if review_issue is not None:
        affected_lanes = review_issue[2]
        reason_codes = (
            dedupe([item["reason_code"] for item in affected_lanes])
            if affected_lanes
            else [review_issue[0]]
        )
        if normalized["generation_manifest"]["manifest_scope"] == (
            "manuscript_generation"
        ):
            reason_codes = dedupe(
                ["first_draft_cross_domain_pre_review_missing_or_stale", *reason_codes]
            )
        if _is_reviewer_revision(normalized):
            route_back = _route_back(
                normalized,
                reason_code=review_issue[0],
                next_owner="independent_reviewer",
                resume_condition=review_issue[1],
                affected_review_lanes=affected_lanes,
            )
            repair = normalized["repair_state"]
            if repair["attempts_used"] < repair["max_attempts"]:
                return _finalize(
                    normalized,
                    status="route_back",
                    stage_outcome=_stage_outcome(
                        "route_back", transition_allowed=False
                    ),
                    route_back=route_back,
                )
            return _finalize(
                normalized,
                status="completed_with_quality_debt",
                stage_outcome=_stage_outcome(
                    "completed_with_quality_debt", transition_allowed=True
                ),
                route_back=route_back,
                quality_debt=_quality_debt(
                    normalized,
                    reason_codes=dedupe(
                        [*reason_codes, "review_scope_budget_exhausted"]
                    ),
                ),
            )
        if normalized["mission"]["stage_id"] == "finalize_and_publication_handoff":
            return _route_result(
                normalized,
                reason_code=review_issue[0],
                next_owner="independent_reviewer",
                resume_condition=review_issue[1],
                affected_review_lanes=affected_lanes,
            )
        route_back = _route_back(
            normalized,
            reason_code=review_issue[0],
            next_owner="independent_reviewer",
            resume_condition=review_issue[1],
            affected_review_lanes=affected_lanes,
        )
        return _finalize(
            normalized,
            status="completed_with_quality_debt",
            stage_outcome=_stage_outcome(
                "completed_with_quality_debt", transition_allowed=True
            ),
            route_back=route_back,
            quality_debt=_quality_debt(
                normalized,
                reason_codes=reason_codes,
            ),
        )

    revision_issue = _revision_consumption_issue(normalized)
    if revision_issue is not None:
        if normalized["mission"]["stage_id"] == "finalize_and_publication_handoff":
            return _route_result(
                normalized,
                reason_code=revision_issue[0],
                next_owner="mas_revision_consumption_owner",
                resume_condition=revision_issue[1],
            )
        route_back = _route_back(
            normalized,
            reason_code=revision_issue[0],
            next_owner="mas_revision_consumption_owner",
            resume_condition=revision_issue[1],
        )
        return _finalize(
            normalized,
            status="completed_with_quality_debt",
            stage_outcome=_stage_outcome(
                "completed_with_quality_debt", transition_allowed=True
            ),
            route_back=route_back,
            quality_debt=_quality_debt(
                normalized,
                reason_codes=[revision_issue[0]],
            ),
        )

    review_status = _aggregate_review_status(normalized)
    repair = normalized["repair_state"]
    if review_status in {"revision_required", "rejected"}:
        reason_code = (
            "independent_review_rejected_output"
            if review_status == "rejected"
            else "independent_review_requires_repair"
        )
        route_back = _route_back(
            normalized,
            reason_code=reason_code,
            next_owner="mission_repairer",
            resume_condition="repair the exact manifest and obtain fresh review receipts",
        )
        if (
            repair["attempts_used"] < repair["max_attempts"]
            or normalized["mission"]["stage_id"] == "finalize_and_publication_handoff"
        ):
            return _finalize(
                normalized,
                status="route_back",
                stage_outcome=_stage_outcome("route_back", transition_allowed=False),
                route_back=route_back,
            )
        return _finalize(
            normalized,
            status="completed_with_quality_debt",
            stage_outcome=_stage_outcome(
                "completed_with_quality_debt", transition_allowed=True
            ),
            route_back=route_back,
            quality_debt=_quality_debt(
                normalized,
                reason_codes=[reason_code, "repair_budget_exhausted"],
            ),
        )

    debt_codes, defect_refs = _review_quality_debt(normalized)
    if debt_codes or defect_refs:
        if normalized["mission"]["stage_id"] == "finalize_and_publication_handoff":
            return _route_result(
                normalized,
                reason_code="independent_review_quality_debt_open",
                next_owner="mission_repairer",
                resume_condition="close every review defect and obtain fresh passed receipts",
            )
        reason_codes = [*debt_codes]
        if defect_refs:
            reason_codes.append("independent_review_open_defects")
        return _finalize(
            normalized,
            status="completed_with_quality_debt",
            stage_outcome=_stage_outcome(
                "completed_with_quality_debt", transition_allowed=True
            ),
            quality_debt=_quality_debt(normalized, reason_codes=dedupe(reason_codes)),
        )

    return _finalize(
        normalized,
        status="owner_receipt",
        stage_outcome=_stage_outcome("completed", transition_allowed=True),
        owner_receipt=_owner_receipt(normalized),
    )
