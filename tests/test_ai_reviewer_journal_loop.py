from __future__ import annotations

import importlib
from copy import deepcopy
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


def _reviewer_operating_system() -> dict[str, Any]:
    input_bundle = {
        "manuscript": "paper/manuscript.md",
        "study_charter": "artifacts/controller/study_charter.json",
        "evidence_ledger": "paper/evidence_ledger.json",
        "review_ledger": "paper/review/review_ledger.json",
        "medical_manuscript_blueprint": "paper/medical_manuscript_blueprint.json",
        "claim_evidence_map": "paper/claim_evidence_map.json",
        "medical_prose_review": "artifacts/publication_eval/medical_prose_review.json",
        "publication_gate_projection": "artifacts/publication_eval/latest.json",
    }
    rubric_scores = {
        dimension: {
            "status": "ready",
            "rationale": f"{dimension} is supported by AI reviewer evidence.",
            "evidence_refs": ["paper/evidence_ledger.json", "paper/review/review_ledger.json"],
        }
        for dimension in QUALITY_DIMENSIONS
    }
    return {
        "contract_id": "medical_publication_ai_reviewer_os_v1",
        "input_bundle": input_bundle,
        "rubric_scores": rubric_scores,
        "decision_matrix": [
            {
                "dimension": dimension,
                "status": score["status"],
                "rationale": score["rationale"],
            }
            for dimension, score in rubric_scores.items()
        ],
        "provenance_checks": {
            "assessment_owner": "ai_reviewer",
            "policy_id": "medical_publication_critique_v1",
            "ai_reviewer_required": False,
            "mechanical_projection_used_as_quality_authority": False,
        },
        "route_back_decision": {
            "recommended_action": "authorize_full_manuscript_drafting",
            "rationale": "The target-journal writing layer and claim evidence trace are ready.",
        },
    }


def _publication_eval() -> dict[str, Any]:
    return {
        "assessment_provenance": {
            "owner": "ai_reviewer",
            "source_kind": "publication_eval_ai_reviewer",
            "policy_id": "medical_publication_critique_v1",
            "source_refs": ["artifacts/publication_eval/latest.json"],
            "ai_reviewer_required": False,
        },
        "reviewer_operating_system": _reviewer_operating_system(),
        "quality_claim_authorized": True,
        "quality_assessment": {
            dimension: {
                "status": "ready",
                "summary": f"{dimension} is ready for full drafting.",
                "evidence_refs": ["paper/evidence_ledger.json"],
            }
            for dimension in QUALITY_DIMENSIONS
        },
    }


def _complete_inputs() -> dict[str, Any]:
    return {
        "target_journal_writing_layer": {
            "target_journal_family": "clinical epidemiology",
            "section_plan": [
                {"section": "Introduction", "writing_role": "bounded clinical rationale"},
                {"section": "Results", "writing_role": "finding-led paragraphs"},
                {"section": "Discussion", "writing_role": "restrained interpretation"},
            ],
        },
        "claim_to_paragraph_map": {
            "claims": [
                {
                    "claim_id": "claim-primary",
                    "paragraph_id": "results-p1",
                    "evidence_refs": ["paper/evidence_ledger.json#claim-primary"],
                }
            ]
        },
        "display_to_claim_map": {
            "links": [
                {
                    "display_id": "figure-1",
                    "claim_ids": ["claim-primary"],
                    "evidence_refs": ["paper/evidence_ledger.json#figure-1"],
                }
            ]
        },
        "restrained_language_strategy": {
            "strategy_id": "restrained-clinical-language-v1",
            "overstrong_claim_controls": [
                {
                    "case_ref": "ai_reviewer_calibration_corpus#overstrong_claim",
                    "rewrite_rule": "association, not causal effect",
                }
            ],
        },
        "evidence_ledger_ref": "paper/evidence_ledger.json",
        "review_ledger_ref": "paper/review/review_ledger.json",
        "publication_eval": _publication_eval(),
        "calibration_case_refs": [
            "ai_reviewer_calibration_corpus#thin_first_draft",
            "ai_reviewer_calibration_corpus#overstrong_claim",
        ],
    }


def _projection(**overrides: Any) -> dict[str, Any]:
    module = importlib.import_module("med_autoscience.controllers.ai_reviewer_journal_loop")
    inputs = _complete_inputs()
    inputs.update(overrides)
    return module.build_ai_reviewer_journal_writing_authorization(**inputs)


def test_complete_ai_reviewer_authorizes_full_manuscript_drafting() -> None:
    projection = _projection()

    assert projection["surface"] == "ai_reviewer_journal_writing_authorization"
    assert projection["full_drafting_authorized"] is True
    assert projection["mode"] == "full_manuscript_drafting"
    assert projection["blockers"] == []
    assert projection["quality_claim_authorized"] is True
    assert [case["case_id"] for case in projection["calibration_cases_applied"]] == [
        "thin_first_draft",
        "overstrong_claim",
    ]


@pytest.mark.parametrize(
    ("override_key", "override_value", "blocker"),
    [
        ("target_journal_writing_layer", {}, "target_journal_writing_layer_missing"),
        ("claim_to_paragraph_map", {}, "claim_to_paragraph_map_missing"),
        ("display_to_claim_map", {}, "display_to_claim_map_missing"),
        ("restrained_language_strategy", {}, "restrained_language_strategy_missing"),
        ("evidence_ledger_ref", "", "evidence_ledger_ref_missing"),
        ("review_ledger_ref", "", "review_ledger_ref_missing"),
        ("calibration_case_refs", [], "calibration_refs_missing"),
    ],
)
def test_required_inputs_fail_closed_to_pre_draft_planning_only(
    override_key: str,
    override_value: Any,
    blocker: str,
) -> None:
    projection = _projection(**{override_key: override_value})

    assert projection["full_drafting_authorized"] is False
    assert projection["mode"] == "pre_draft_planning_only"
    assert blocker in projection["blockers"]


def test_publication_eval_must_be_ai_reviewer_owned() -> None:
    publication_eval = _publication_eval()
    publication_eval["assessment_provenance"]["owner"] = "mechanical_projection"
    publication_eval["assessment_provenance"]["ai_reviewer_required"] = True

    projection = _projection(publication_eval=publication_eval)

    assert projection["full_drafting_authorized"] is False
    assert projection["mode"] == "pre_draft_planning_only"
    assert "publication_eval_not_ai_reviewer_owned" in projection["blockers"]
    assert "mechanical_projection_cannot_authorize_quality" in projection["blockers"]


def test_missing_reviewer_operating_system_trace_blocks_full_drafting() -> None:
    publication_eval = _publication_eval()
    publication_eval.pop("reviewer_operating_system")

    projection = _projection(publication_eval=publication_eval)

    assert projection["full_drafting_authorized"] is False
    assert projection["mode"] == "pre_draft_planning_only"
    assert "reviewer_operating_system_trace_missing_or_invalid" in projection["blockers"]


def test_overstrong_claim_calibration_case_is_applied() -> None:
    projection = _projection(
        calibration_case_refs=["ai_reviewer_calibration_corpus#overstrong_claim"],
    )

    assert projection["full_drafting_authorized"] is True
    assert projection["calibration_cases_applied"] == [
        {
            "case_id": "overstrong_claim",
            "expected_route": "return_to_ai_reviewer",
            "mechanical_facts_role": "evidence_only",
            "quality_gate_relaxation_allowed": False,
        }
    ]


def test_quality_claim_authorized_false_blocks_full_drafting() -> None:
    publication_eval = deepcopy(_publication_eval())
    publication_eval["quality_claim_authorized"] = False

    projection = _projection(publication_eval=publication_eval)

    assert projection["full_drafting_authorized"] is False
    assert projection["mode"] == "pre_draft_planning_only"
    assert projection["quality_claim_authorized"] is False
    assert "quality_claim_not_authorized_by_ai_reviewer" in projection["blockers"]


def test_mechanical_projection_fields_cannot_authorize_quality() -> None:
    publication_eval = _publication_eval()
    publication_eval["assessment_provenance"] = {
        "owner": "mechanical_projection",
        "source_kind": "publication_gate_projection",
        "policy_id": "publication_gate_projection_v1",
        "source_refs": ["artifacts/publication_eval/latest.json"],
        "ai_reviewer_required": True,
    }
    publication_eval["mechanical_projection"] = {"coverage_complete": True, "ready": True}

    projection = _projection(publication_eval=publication_eval)

    assert projection["full_drafting_authorized"] is False
    assert projection["mode"] == "pre_draft_planning_only"
    assert "mechanical_projection_cannot_authorize_quality" in projection["blockers"]
