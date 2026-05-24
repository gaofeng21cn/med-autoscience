from __future__ import annotations

from pathlib import Path


def ready_reviewer_operating_system(
    study_root: Path,
    publication_eval_path: Path,
    eval_id: str,
) -> dict[str, object]:
    refs = {
        "manuscript": str(study_root / "paper" / "manuscript.md"),
        "study_charter": str(study_root / "artifacts" / "controller" / "study_charter.json"),
        "evidence_ledger": str(study_root / "paper" / "evidence_ledger.json"),
        "review_ledger": str(study_root / "paper" / "review" / "review_ledger.json"),
        "medical_manuscript_blueprint": str(study_root / "paper" / "medical_manuscript_blueprint.json"),
        "claim_evidence_map": str(study_root / "paper" / "claim_evidence_map.json"),
        "medical_prose_review": str(study_root / "artifacts" / "publication_eval" / "medical_prose_review.json"),
        "publication_gate_projection": str(publication_eval_path),
    }
    dimensions = (
        "clinical_significance",
        "evidence_strength",
        "novelty_positioning",
        "medical_journal_prose_quality",
        "human_review_readiness",
    )
    return {
        "contract_id": "medical_publication_ai_reviewer_os_v1",
        "input_bundle": refs,
        "rubric_scores": {
            dimension: {
                "status": "ready",
                "rationale": f"{dimension} is closed by AI reviewer currentness evidence.",
                "evidence_refs": [refs["manuscript"], refs["evidence_ledger"], refs["review_ledger"]],
            }
            for dimension in dimensions
        },
        "decision_matrix": [
            {
                "dimension": dimension,
                "status": "ready",
                "rationale": f"{dimension} is closed by AI reviewer currentness evidence.",
            }
            for dimension in dimensions
        ],
        "currentness_checks": {
            "medical_prose_review": {
                "status": "current",
                "request_digest": "sha256:event-scan-medical-prose-review-request",
                "manuscript_ref": refs["manuscript"],
                "manuscript_digest": "sha256:event-scan-manuscript",
            },
            "current_package_freshness": {
                "status": "fresh",
                "source_eval_id": eval_id,
            },
        },
        "claim_evidence_alignment": {
            "surface_kind": "claim_evidence_alignment_gate_v1",
            "source_project": "academic-research-skills",
            "absorbed_as": "mas_native_claim_evidence_alignment_gate",
            "status": "ready",
            "fail_closed_when_missing": True,
            "body_included": False,
            "may_authorize_publication_readiness": False,
            "may_authorize_quality_verdict": False,
            "can_write_domain_truth": False,
            "missing_required_fields": [],
            "blockers": [],
            "claim_count": 1,
            "aligned_claim_count": 1,
        },
        "publication_quality_readiness": {
            "surface_kind": "publication_quality_authority_kernel_v1",
            "status": "ready",
            "current_manuscript_digest": "sha256:event-scan-manuscript",
            "review_request_digest": "sha256:event-scan-medical-prose-review-request",
            "evidence_ledger_digest": "sha256:event-scan-evidence-ledger",
            "claim_evidence_alignment_digest": "sha256:event-scan-claim-evidence-alignment",
            "rubric_version": "medical_publication_critique_v1",
            "owner_attempt_id": "ai-reviewer-attempt::event-scan-ready",
            "fail_closed_when_missing": True,
            "missing_required_fields": [],
        },
        "future_facing_limitations_plan": [
            {
                "limitation": "Finalize authorization is limited to the reviewed manuscript snapshot.",
                "impact_on_claim": "Paper claims must remain restrained to the reviewed evidence support.",
                "required_future_analysis_data_or_design": "Refresh AI reviewer currentness after substantive changes.",
                "current_manuscript_wording_must_be_restrained": True,
            }
        ],
        "provenance_checks": {
            "assessment_owner": "ai_reviewer",
            "policy_id": "medical_publication_critique_v1",
            "ai_reviewer_required": False,
            "mechanical_projection_used_as_quality_authority": False,
        },
        "route_back_decision": {
            "recommended_action": "continue_finalize",
            "rationale": "AI reviewer currentness evidence is closed for this submission milestone fixture.",
        },
    }
