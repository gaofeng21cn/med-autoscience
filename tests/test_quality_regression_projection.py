from __future__ import annotations

import importlib
from typing import Any

import pytest


pytestmark = pytest.mark.meta


QUALITY_DIMENSIONS = (
    "clinical_significance",
    "evidence_strength",
    "novelty_positioning",
    "medical_journal_prose_quality",
    "human_review_readiness",
)


def _quality_assessment(stage: str, statuses: dict[str, str]) -> dict[str, Any]:
    return {
        dimension: {
            "status": statuses[dimension],
            "summary": f"{stage} {dimension} quality assessment.",
            "evidence_refs": [f"paper/{stage}/{dimension}.json"],
        }
        for dimension in QUALITY_DIMENSIONS
    }


def _eval(stage: str, statuses: dict[str, str]) -> dict[str, Any]:
    eval_ref = f"artifacts/publication_eval/{stage}.json"
    return {
        "eval_ref": eval_ref,
        "package_stage": stage,
        "eval_id": f"publication-eval::{stage}",
        "assessment_provenance": {
            "owner": "ai_reviewer",
            "source_kind": "publication_eval_ai_reviewer",
            "policy_id": "medical_publication_critique_v1",
            "source_refs": [eval_ref],
            "ai_reviewer_required": False,
        },
        "quality_assessment": _quality_assessment(stage, statuses),
    }


def test_quality_regression_projection_compares_package_versions_without_publication_authority() -> None:
    module = importlib.import_module("med_autoscience.controllers.quality_regression_projection")

    projection = module.build_quality_regression_projection(
        draft_eval=_eval(
            "draft",
            {
                "clinical_significance": "partial",
                "evidence_strength": "blocked",
                "novelty_positioning": "underdefined",
                "medical_journal_prose_quality": "partial",
                "human_review_readiness": "blocked",
            },
        ),
        revision_eval=_eval(
            "revision",
            {
                "clinical_significance": "ready",
                "evidence_strength": "partial",
                "novelty_positioning": "partial",
                "medical_journal_prose_quality": "ready",
                "human_review_readiness": "partial",
            },
        ),
        final_package_eval=_eval(
            "final",
            {
                "clinical_significance": "ready",
                "evidence_strength": "ready",
                "novelty_positioning": "ready",
                "medical_journal_prose_quality": "ready",
                "human_review_readiness": "ready",
            },
        ),
        historical_repair_results=[
            {
                "repair_id": "repair-evidence-strength-001",
                "dimension": "evidence_strength",
                "result": "closed",
                "evidence_ref": "paper/review_ledger.json#repair-evidence-strength-001",
            },
            {
                "repair_id": "repair-medical-prose-001",
                "dimension": "medical_journal_prose_quality",
                "result": "closed",
                "evidence_ref": "paper/review_ledger.json#repair-medical-prose-001",
            },
        ],
        calibration_evidence_refs=[
            "docs/program/paper_orchestra_learning_intake_2026_05_02.md#paper-autoraters",
            "paper/review_ledger.json#side-by-side-regression",
        ],
        judge_scores=[
            {
                "judge_id": "side_by_side_revision_vs_final",
                "compared_stages": ["revision", "final"],
                "score": 0.82,
                "calibration_evidence_ref": "paper/review_ledger.json#side-by-side-regression",
            }
        ],
    )

    assert projection["surface"] == "quality_regression_projection"
    assert projection["schema_version"] == 1
    assert projection["authority"] == {
        "owner": "MAS Evaluation OS",
        "can_authorize_publication_quality": False,
        "can_replace_ai_reviewer": False,
        "publication_authority_surface": "artifacts/publication_eval/latest.json",
        "judge_score_role": "calibration_evidence_only",
    }
    assert projection["package_eval_refs"] == {
        "draft": "artifacts/publication_eval/draft.json",
        "revision": "artifacts/publication_eval/revision.json",
        "final": "artifacts/publication_eval/final.json",
    }

    comparisons = {item["dimension"]: item for item in projection["dimension_comparisons"]}
    assert comparisons["evidence_strength"] == {
        "dimension": "evidence_strength",
        "draft_status": "blocked",
        "revision_status": "partial",
        "final_status": "ready",
        "trajectory": "improved",
        "historical_repair_results": [
            {
                "repair_id": "repair-evidence-strength-001",
                "result": "closed",
                "evidence_ref": "paper/review_ledger.json#repair-evidence-strength-001",
            }
        ],
    }
    assert comparisons["medical_journal_prose_quality"]["trajectory"] == "improved"
    assert projection["regression_summary"] == {
        "dimensions_compared": 5,
        "dimensions_improved": 5,
        "dimensions_regressed": 0,
        "historical_repair_results_compared": 2,
        "status": "no_regression_detected",
    }
    assert projection["calibration_evidence"]["refs"] == [
        "docs/program/paper_orchestra_learning_intake_2026_05_02.md#paper-autoraters",
        "paper/review_ledger.json#side-by-side-regression",
    ]
    assert projection["calibration_evidence"]["judge_scores"] == [
        {
            "judge_id": "side_by_side_revision_vs_final",
            "compared_stages": ["revision", "final"],
            "score": 0.82,
            "calibration_evidence_ref": "paper/review_ledger.json#side-by-side-regression",
            "role": "calibration_evidence_only",
            "can_authorize_publication_quality": False,
            "can_replace_ai_reviewer": False,
        }
    ]
    assert projection["soak_matrix_evidence"] == {
        "role": "soak_proof_only",
        "can_authorize_publication_quality": False,
        "required_stages": [
            "literature_scout",
            "line_selection",
            "main_analysis",
            "bounded_analysis",
            "route_back",
            "stop_loss",
            "revision_reopen",
            "runtime_recovery",
            "finalize_rebuild",
            "final_pre_submission_audit",
        ],
        "stage_results": [],
    }


def test_quality_regression_projection_fails_closed_without_eval_or_calibration_refs() -> None:
    module = importlib.import_module("med_autoscience.controllers.quality_regression_projection")
    draft_eval = _eval("draft", {dimension: "partial" for dimension in QUALITY_DIMENSIONS})
    revision_eval = _eval("revision", {dimension: "ready" for dimension in QUALITY_DIMENSIONS})
    final_eval = _eval("final", {dimension: "ready" for dimension in QUALITY_DIMENSIONS})

    draft_eval.pop("eval_ref")
    with pytest.raises(ValueError, match="draft_eval.eval_ref"):
        module.build_quality_regression_projection(
            draft_eval=draft_eval,
            revision_eval=revision_eval,
            final_package_eval=final_eval,
            historical_repair_results=[],
            calibration_evidence_refs=["paper/review_ledger.json#regression"],
        )

    draft_eval = _eval("draft", {dimension: "partial" for dimension in QUALITY_DIMENSIONS})
    with pytest.raises(ValueError, match="calibration_evidence_refs"):
        module.build_quality_regression_projection(
            draft_eval=draft_eval,
            revision_eval=revision_eval,
            final_package_eval=final_eval,
            historical_repair_results=[],
            calibration_evidence_refs=[],
        )
