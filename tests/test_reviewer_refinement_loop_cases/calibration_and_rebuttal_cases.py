from __future__ import annotations

import importlib
from pathlib import Path

from tests.test_reviewer_refinement_loop import (
    MODULE_NAME,
    _minimal_payload,
    _write_json,
)

def test_reviewer_refinement_loop_projects_required_learning_calibration_refs(
    tmp_path: Path,
) -> None:
    module = importlib.import_module(MODULE_NAME)
    study_root = tmp_path / "workspace" / "studies" / "001-risk"
    payload = _minimal_payload(study_root)
    _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", payload)
    _write_json(study_root / "artifacts" / "publication_eval" / "ai_reviewer_calibration_learning.json", {
        "surface": "ai_reviewer_calibration_learning_read_model",
        "learning_entries": [
            {
                "entry_id": "learn::major-revision::coverage",
                "source_outcome": "major_revision",
                "failure_mode": "coverage_as_quality",
                "source_ref": "reviews/round-1.md#editor",
                "issue_summary": "Coverage was treated as quality.",
                "claim_refs": [],
                "evidence_refs": ["paper/reporting_guideline_checklist.json"],
                "reviewer_trace_refs": ["paper/review/review_ledger.json#editor"],
            },
            {
                "entry_id": "learn::major-revision::trace",
                "source_outcome": "major_revision",
                "failure_mode": "missing_reviewer_trace",
                "source_ref": "reviews/round-1.md#trace",
                "issue_summary": "Reviewer concern trace was missing.",
                "claim_refs": ["paper/claim_evidence_map.json#claim-primary"],
                "evidence_refs": ["paper/evidence_ledger.json#claim-primary"],
                "reviewer_trace_refs": ["paper/review/review_ledger.json#trace"],
            },
        ],
    })

    read_model = module.build_reviewer_refinement_loop_read_model(study_root=study_root)

    assert read_model["required_calibration_refs"] == [
        "ai_reviewer_calibration_corpus#coverage_as_quality",
        "ai_reviewer_calibration_corpus#missing_reviewer_trace",
    ]
    assert read_model["calibration_learning"]["failure_mode_counts"] == {
        "coverage_as_quality": 1,
        "missing_reviewer_trace": 1,
    }
    assert read_model["accept"]["accepted"] is False
    assert read_model["accept"]["bounded_auto_advance"] is False
    assert "required_calibration_ref_missing:coverage_as_quality" in read_model["accept"]["blockers"]
    assert "required_calibration_ref_missing:missing_reviewer_trace" in read_model["accept"]["blockers"]
    assert read_model["revert"]["strategy"] == "same_line_route_back"
    assert read_model["contract"]["read_model_only"] is True
    assert read_model["contract"]["learning_can_authorize_quality"] is False
    assert read_model["contract"]["learning_can_authorize_submission"] is False
    assert read_model["contract"]["learning_can_authorize_finalize"] is False
    assert read_model["bounded_review_repair_policy"]["status"] == "authority_blocked"


def test_revision_rebuttal_loop_projects_comment_action_matrix_and_repair_routes() -> None:
    module = importlib.import_module("med_autoscience.controllers.revision_rebuttal_loop")

    projection = module.build_revision_rebuttal_loop_projection(
        {
            "reviewer_comments": [
                {
                    "comment_id": "r1-c1",
                    "source": "reviewer_1",
                    "concern": "Sensitivity analysis is missing for the primary association.",
                    "severity": "major",
                    "requested_change": "Add additional analysis before rebuttal.",
                    "target_section": "Results",
                    "target_claim": "claim-primary",
                },
                {
                    "comment_id": "r1-c2",
                    "source": "reviewer_1",
                    "concern": "Discussion wording is too strong for observational evidence.",
                    "severity": "minor",
                    "requested_change": "Revise text to restrained association language.",
                    "target_section": "Discussion",
                    "target_claim": "claim-discussion",
                },
            ],
            "evidence_ledger_refs": ["paper/evidence_ledger.json"],
            "review_ledger_refs": ["paper/review/review_ledger.json"],
        }
    )

    assert projection["status"] == "ready"
    assert projection["comment_to_action_matrix"] == projection["action_matrix"]
    matrix_by_comment = {item["comment_id"]: item for item in projection["comment_to_action_matrix"]}
    assert matrix_by_comment["r1-c1"]["repair_routes"] == {
        "analysis_repair": {
            "required": True,
            "target_claim": "claim-primary",
            "target_section": "Results",
            "ledger_refs": ["paper/evidence_ledger.json", "paper/review/review_ledger.json"],
        },
        "text_repair": {
            "required": False,
            "target_claim": "claim-primary",
            "target_section": "Results",
            "ledger_refs": ["paper/evidence_ledger.json", "paper/review/review_ledger.json"],
        },
        "ai_reviewer_recheck": {
            "required": True,
            "reason": "analysis_repair_requires_ai_reviewer_recheck",
        },
    }
    assert matrix_by_comment["r1-c2"]["repair_routes"]["analysis_repair"]["required"] is False
    assert matrix_by_comment["r1-c2"]["repair_routes"]["text_repair"]["required"] is True
    assert matrix_by_comment["r1-c2"]["repair_routes"]["ai_reviewer_recheck"] == {
        "required": True,
        "reason": "text_repair_requires_ai_reviewer_recheck",
    }
    assert projection["repair_plan"] == {
        "analysis_repair_required": True,
        "text_repair_required": True,
        "ai_reviewer_recheck_required": True,
        "mechanical_projection_can_authorize_quality": False,
    }


def test_revision_rebuttal_loop_projects_response_package_planning_surfaces() -> None:
    module = importlib.import_module("med_autoscience.controllers.revision_rebuttal_loop")

    projection = module.build_revision_rebuttal_loop_projection(
        {
            "reviewer_comments": [
                {
                    "comment_id": "r1-c1",
                    "source": "reviewer_1",
                    "concern": "Sensitivity analysis is missing for the primary association.",
                    "severity": "major",
                    "requested_change": "Add additional analysis before rebuttal.",
                    "target_section": "Results",
                    "target_claim": "claim-primary",
                    "line_number": "142",
                    "statistical_result": "Adjusted OR 1.42, 95% CI 1.10-1.84.",
                    "citation_ref": "paper/references.json#smith-2024",
                },
                {
                    "comment_id": "r1-c2",
                    "source": "reviewer_1",
                    "concern": "Discussion wording is too strong for observational evidence.",
                    "severity": "minor",
                    "requested_change": "Revise text to restrained association language.",
                    "target_section": "Discussion",
                    "target_claim": "claim-discussion",
                    "line_number": "231",
                    "citation_ref": "paper/references.json#jones-2023",
                },
                {
                    "comment_id": "r2-c1",
                    "source": "reviewer_2",
                    "concern": "The authors should explain why no external validation cohort is available.",
                    "severity": "major",
                    "requested_change": "Provide author rationale for the missing external cohort.",
                    "target_section": "Methods",
                    "target_claim": "claim-cohort",
                    "line_number": "88",
                },
            ],
            "evidence_ledger_refs": ["paper/evidence_ledger.json"],
            "review_ledger_refs": ["paper/review/review_ledger.json"],
        }
    )

    matrix_by_comment = {item["comment_id"]: item for item in projection["comment_to_action_matrix"]}
    assert matrix_by_comment["r1-c1"]["stable_concern_id"] == "reviewer_1:r1-c1"
    assert matrix_by_comment["r1-c1"]["action_label"] == "ACCEPT_ANALYSIS"
    assert matrix_by_comment["r1-c2"]["action_label"] == "SOFTEN_CLAIM"
    assert matrix_by_comment["r2-c1"]["action_label"] == "AUTHOR_INPUT_NEEDED"

    tracker_by_comment = {
        item["comment_id"]: item for item in projection["comment_response_tracker"]
    }
    assert tracker_by_comment["r1-c1"]["response_status"] == "planned"
    assert tracker_by_comment["r1-c1"]["response_letter_point"].startswith("Response to r1-c1")
    assert tracker_by_comment["r2-c1"]["response_status"] == "author_input_needed"
    assert tracker_by_comment["r2-c1"]["blocking_missing_fields"] == [
        "citation_ref",
        "statistical_result",
    ]

    checklist = projection["manuscript_change_checklist"]
    assert checklist == [
        {
            "stable_concern_id": "reviewer_1:r1-c1",
            "comment_id": "r1-c1",
            "action_label": "ACCEPT_ANALYSIS",
            "target_section": "Results",
            "target_claim": "claim-primary",
            "change_required": True,
            "check_item": "Update Results for reviewer_1:r1-c1 before response closure.",
            "read_model_only": True,
        },
        {
            "stable_concern_id": "reviewer_1:r1-c2",
            "comment_id": "r1-c2",
            "action_label": "SOFTEN_CLAIM",
            "target_section": "Discussion",
            "target_claim": "claim-discussion",
            "change_required": True,
            "check_item": "Update Discussion for reviewer_1:r1-c2 before response closure.",
            "read_model_only": True,
        },
        {
            "stable_concern_id": "reviewer_2:r2-c1",
            "comment_id": "r2-c1",
            "action_label": "AUTHOR_INPUT_NEEDED",
            "target_section": "Methods",
            "target_claim": "claim-cohort",
            "change_required": False,
            "check_item": "Collect author input for reviewer_2:r2-c1 before drafting a rebuttal.",
            "read_model_only": True,
        },
    ]
    assert projection["missing_author_input_list"] == [
        {
            "stable_concern_id": "reviewer_2:r2-c1",
            "comment_id": "r2-c1",
            "source": "reviewer_2",
            "missing_fields": ["citation_ref", "statistical_result"],
            "reason": "rebuttal_context_incomplete",
        }
    ]
    assert projection["response_package_readiness"] == {
        "status": "blocked",
        "ready": False,
        "blockers": [
            "author_input_needed:reviewer_2:r2-c1",
            "reviewer_comment_missing_citation_ref:r2-c1",
            "reviewer_comment_missing_statistical_result:r2-c1",
        ],
        "read_model_only": True,
        "publication_readiness_authorized": False,
        "current_package_mutation_allowed": False,
    }
    assert projection["publication_readiness_authorized"] is False
    assert projection["current_package_mutation_allowed"] is False
