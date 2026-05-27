from __future__ import annotations

from typing import Any

from tests.reviewer_os_fixture_helpers import (
    claim_evidence_alignment_digest,
    ready_claim_evidence_alignment_gate,
)


def minimal_ai_reviewer_record(study_id: str, quest_id: str, eval_id: str) -> dict[str, Any]:
    input_bundle = {
        "manuscript": "paper/draft.md",
        "study_charter": "artifacts/controller/study_charter.json",
        "evidence_ledger": "paper/evidence_ledger.json",
        "review_ledger": "paper/review/review_ledger.json",
        "medical_manuscript_blueprint": "paper/medical_manuscript_blueprint.json",
        "claim_evidence_map": "paper/claim_evidence_map.json",
        "medical_prose_review": "artifacts/publication_eval/medical_prose_review.json",
        "publication_gate_projection": "artifacts/publication_eval/latest.json",
    }
    dimensions = (
        "clinical_significance",
        "evidence_strength",
        "novelty_positioning",
        "medical_journal_prose_quality",
        "human_review_readiness",
    )
    quality_assessment = {
        dimension: {
            "status": "underdefined" if dimension == "medical_journal_prose_quality" else "ready",
            "summary": f"{dimension} reviewer assessment.",
            "evidence_refs": [input_bundle["manuscript"]],
        }
        for dimension in dimensions
    }
    future_plan = [
        {
            "limitation": "Medication coverage is based on recorded medication fields.",
            "impact_on_claim": "Treatment-gap language must remain documentation-aware.",
            "required_future_analysis_data_or_design": "Link pharmacy or insurance dispensing data.",
            "current_manuscript_wording_must_be_restrained": True,
        }
    ]
    claim_alignment = ready_claim_evidence_alignment_gate(
        claim_evidence_map_ref=input_bundle["claim_evidence_map"],
        evidence_ledger_ref=input_bundle["evidence_ledger"],
    )
    return {
        "eval_id": eval_id,
        "study_id": study_id,
        "quest_id": quest_id,
        "evaluation_scope": "publication",
        "assessment_provenance": {
            "owner": "ai_reviewer",
            "source_kind": "publication_eval_ai_reviewer",
            "policy_id": "medical_publication_critique_v1",
            "source_refs": list(input_bundle.values()),
            "ai_reviewer_required": False,
        },
        "quality_assessment": quality_assessment,
        "future_facing_limitations_plan": future_plan,
        "recommended_actions": [
            {
                "action_id": "continue-first-draft",
                "action_type": "continue_same_line",
                "priority": "next",
                "reason": "Proceed with reviewer-bound workflow execution.",
                "evidence_refs": [input_bundle["review_ledger"]],
                "requires_controller_decision": True,
            }
        ],
        "reviewer_operating_system": _reviewer_operating_system(
            eval_id=eval_id,
            input_bundle=input_bundle,
            dimensions=dimensions,
            quality_assessment=quality_assessment,
            future_plan=future_plan,
            claim_alignment=claim_alignment,
        ),
    }


def _reviewer_operating_system(
    *,
    eval_id: str,
    input_bundle: dict[str, str],
    dimensions: tuple[str, ...],
    quality_assessment: dict[str, dict[str, Any]],
    future_plan: list[dict[str, Any]],
    claim_alignment: dict[str, Any],
) -> dict[str, Any]:
    return {
        "contract_id": "medical_publication_ai_reviewer_os_v1",
        "input_bundle": input_bundle,
        "rubric_scores": {
            dimension: {
                "status": quality_assessment[dimension]["status"],
                "rationale": quality_assessment[dimension]["summary"],
                "evidence_refs": quality_assessment[dimension]["evidence_refs"],
            }
            for dimension in dimensions
        },
        "decision_matrix": [
            {
                "dimension": dimension,
                "status": quality_assessment[dimension]["status"],
                "rationale": quality_assessment[dimension]["summary"],
            }
            for dimension in dimensions
        ],
        "currentness_checks": {
            "medical_prose_review": {
                "status": "current",
                "request_digest": "sha256:" + "a" * 64,
                "manuscript_ref": input_bundle["manuscript"],
                "manuscript_digest": "sha256:" + "c" * 64,
            },
            "current_package_freshness": {"status": "fresh", "source_eval_id": eval_id},
        },
        "claim_evidence_alignment": claim_alignment,
        "publication_quality_readiness": {
            "surface_kind": "publication_quality_authority_kernel_v1",
            "status": "ready",
            "current_manuscript_digest": "sha256:" + "c" * 64,
            "review_request_digest": "sha256:" + "a" * 64,
            "evidence_ledger_digest": "sha256:" + "d" * 64,
            "claim_evidence_alignment_digest": claim_evidence_alignment_digest(claim_alignment),
            "rubric_version": "medical_publication_critique_v1",
            "owner_attempt_id": f"ai-reviewer-publication-eval::{eval_id}",
            "fail_closed_when_missing": True,
            "missing_required_fields": [],
        },
        "future_facing_limitations_plan": future_plan,
        "provenance_checks": {
            "assessment_owner": "ai_reviewer",
            "policy_id": "medical_publication_critique_v1",
            "ai_reviewer_required": False,
            "mechanical_projection_used_as_quality_authority": False,
        },
        "route_back_decision": {
            "recommended_action": "continue_same_line",
            "rationale": "Proceed with reviewer-bound workflow execution.",
        },
    }


__all__ = ["minimal_ai_reviewer_record"]
