from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Any


MODULE_NAME = "med_autoscience.controllers.reviewer_refinement_loop"


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _minimal_payload(study_root: Path) -> dict[str, Any]:
    quest_root = study_root.parents[1] / "ops" / "med-deepscientist" / "runtime" / "quests" / "quest-001"
    return {
        "schema_version": 1,
        "eval_id": "publication-eval::001-risk::quest-001::2026-04-05T06:00:00+00:00",
        "study_id": "001-risk",
        "quest_id": "quest-001",
        "emitted_at": "2026-04-05T06:00:00+00:00",
        "evaluation_scope": "publication",
        "charter_context_ref": {
            "ref": str(study_root / "artifacts" / "controller" / "study_charter.json"),
            "charter_id": "charter::001-risk::v1",
            "publication_objective": "risk stratification external validation",
        },
        "runtime_context_refs": {
            "runtime_escalation_ref": str(quest_root / "artifacts" / "reports" / "escalation" / "runtime_escalation_record.json"),
            "main_result_ref": str(quest_root / "artifacts" / "results" / "main_result.json"),
        },
        "delivery_context_refs": {
            "paper_root_ref": str(study_root / "paper"),
            "submission_minimal_ref": str(study_root / "paper" / "submission_minimal" / "submission_manifest.json"),
        },
        "assessment_provenance": {
            "owner": "ai_reviewer",
            "source_kind": "publication_eval_ai_reviewer",
            "policy_id": "medical_publication_critique_v1",
            "source_refs": [
                str(study_root / "paper"),
                str(quest_root / "artifacts" / "results" / "main_result.json"),
            ],
            "ai_reviewer_required": False,
        },
        "verdict": {
            "overall_verdict": "promising",
            "primary_claim_status": "supported",
            "summary": "AI reviewer accepts the current manuscript line.",
            "stop_loss_pressure": "none",
        },
        "quality_assessment": _quality_assessment(study_root),
        "reviewer_operating_system": _reviewer_operating_system(study_root),
        "gaps": [
            {
                "gap_id": "optional-style-note",
                "gap_type": "delivery",
                "severity": "optional",
                "summary": "Minor cover-letter polish remains optional.",
                "evidence_refs": [str(study_root / "paper" / "cover_letter.md")],
            }
        ],
        "recommended_actions": [
            {
                "action_id": "accept-current-line",
                "action_type": "continue_same_line",
                "priority": "next",
                "reason": "Only optional submission polish remains.",
                "route_target": "finalize",
                "route_key_question": "Which optional submission polish remains?",
                "route_rationale": "Reviewer accepted the manuscript quality gate.",
                "evidence_refs": [str(study_root / "paper" / "manuscript.md")],
                "requires_controller_decision": True,
            }
        ],
    }


def _quality_assessment(study_root: Path) -> dict[str, Any]:
    quest_root = study_root.parents[1] / "ops" / "med-deepscientist" / "runtime" / "quests" / "quest-001"
    return {
        "clinical_significance": {
            "status": "ready",
            "summary": "Clinical framing is stable.",
            "evidence_refs": [str(study_root / "artifacts" / "controller" / "study_charter.json")],
        },
        "evidence_strength": {
            "status": "ready",
            "summary": "Core evidence is traceable.",
            "evidence_refs": [str(quest_root / "artifacts" / "results" / "main_result.json")],
        },
        "novelty_positioning": {
            "status": "ready",
            "summary": "Contribution boundary is defined.",
            "evidence_refs": [str(study_root / "artifacts" / "controller" / "study_charter.json")],
        },
        "medical_journal_prose_quality": {
            "status": "ready",
            "summary": "Journal-facing prose is acceptable.",
            "evidence_refs": [str(study_root / "paper" / "manuscript.md")],
            "reviewer_reason": "Reviewer found no blocking controller-style prose.",
            "reviewer_revision_advice": "Keep current finding-led sentence structure.",
            "reviewer_next_round_focus": "Final submission metadata only.",
        },
        "human_review_readiness": {
            "status": "ready",
            "summary": "Human-facing package is ready for final administrative review.",
            "evidence_refs": [str(study_root / "paper" / "submission_minimal" / "submission_manifest.json")],
        },
    }


def _reviewer_operating_system(study_root: Path) -> dict[str, Any]:
    quest_root = study_root.parents[1] / "ops" / "med-deepscientist" / "runtime" / "quests" / "quest-001"
    input_bundle = {
        "manuscript": str(study_root / "paper" / "manuscript.md"),
        "study_charter": str(study_root / "artifacts" / "controller" / "study_charter.json"),
        "evidence_ledger": str(study_root / "paper" / "evidence_ledger.json"),
        "review_ledger": str(study_root / "paper" / "review" / "review_ledger.json"),
        "medical_manuscript_blueprint": str(study_root / "paper" / "medical_manuscript_blueprint.json"),
        "claim_evidence_map": str(study_root / "paper" / "claim_evidence_map.json"),
        "medical_prose_review": str(study_root / "artifacts" / "publication_eval" / "medical_prose_review.json"),
        "publication_gate_projection": str(study_root / "artifacts" / "publication_eval" / "latest.json"),
    }
    rubric_scores = {
        dimension: {
            "status": "ready",
            "rationale": f"{dimension} was judged from manuscript and ledger evidence.",
            "evidence_refs": [
                str(study_root / "paper" / "manuscript.md"),
                str(quest_root / "artifacts" / "results" / "main_result.json"),
            ],
        }
        for dimension in (
            "clinical_significance",
            "evidence_strength",
            "novelty_positioning",
            "medical_journal_prose_quality",
            "human_review_readiness",
        )
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
            "recommended_action": "accept_current_line",
            "rationale": "No blocking reviewer refinement remains.",
        },
    }


def test_reviewer_refinement_loop_accepts_only_ai_reviewer_backed_publication_eval(tmp_path: Path) -> None:
    module = importlib.import_module(MODULE_NAME)
    study_root = tmp_path / "workspace" / "studies" / "001-risk"
    payload = _minimal_payload(study_root)
    _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", payload)

    read_model = module.build_reviewer_refinement_loop_read_model(study_root=study_root)

    assert read_model["surface"] == "reviewer_refinement_loop"
    assert read_model["snapshot"]["source_eval_id"] == payload["eval_id"]
    assert read_model["snapshot"]["authority_blockers"] == []
    assert read_model["accept"] == {
        "accepted": True,
        "status": "accepted",
        "source": "ai_reviewer_backed_publication_eval_latest",
        "blockers": [],
        "package_mutation_allowed": False,
    }
    assert read_model["revert"] == {
        "required": False,
        "strategy": "none",
        "direct_package_mutation_allowed": False,
        "route_back": None,
    }
    assert read_model["worklog"][0]["concern_id"] == "publication_gap:optional-style-note"
    assert read_model["worklog"][0]["reviewer_concern"] == "Minor cover-letter polish remains optional."
    assert read_model["worklog"][0]["section"] == "delivery"
    assert read_model["worklog"][0]["artifact_refs"] == [str(study_root / "paper" / "cover_letter.md")]
    assert read_model["worklog"][0]["snapshot_refs"] == [
        {
            "source_surface": "publication_eval/latest.json",
            "source_eval_id": payload["eval_id"],
            "source_artifact_path": str(study_root / "artifacts" / "publication_eval" / "latest.json"),
        }
    ]
    assert read_model["worklog"][0]["lifecycle"] == {
        "state": "accepted",
        "route": "accepted",
        "accepted": True,
        "reverted": False,
        "source": "ai_reviewer_backed_publication_eval_latest",
    }
    assert read_model["contract"]["read_model_only"] is True


def test_reviewer_refinement_loop_maps_revert_to_same_line_route_back_without_package_mutation(
    tmp_path: Path,
) -> None:
    module = importlib.import_module(MODULE_NAME)
    study_root = tmp_path / "workspace" / "studies" / "001-risk"
    payload = _minimal_payload(study_root)
    payload["verdict"] = {
        "overall_verdict": "blocked",
        "primary_claim_status": "partial",
        "summary": "Evidence strength still needs same-line repair.",
        "stop_loss_pressure": "watch",
    }
    payload["quality_assessment"]["evidence_strength"] = {
        "status": "partial",
        "summary": "Main result supports direction but not final claim strength.",
        "evidence_refs": [payload["runtime_context_refs"]["main_result_ref"]],
        "reviewer_revision_advice": "Add the bounded sensitivity paragraph before acceptance.",
        "reviewer_next_round_focus": "Evidence strength and claim wording.",
    }
    payload["quality_assessment"]["medical_journal_prose_quality"] = {
        "status": "partial",
        "summary": "Discussion wording is too strong for observational evidence.",
        "evidence_refs": [str(study_root / "paper" / "manuscript.md")],
        "reviewer_revision_advice": "Revise text to restrained association language.",
        "reviewer_next_round_focus": "Discussion claim wording.",
    }
    payload["gaps"] = [
        {
            "gap_id": "claim-strength",
            "gap_type": "claim",
            "severity": "must_fix",
            "summary": "Claim strength exceeds the current evidence ledger.",
            "evidence_refs": [payload["runtime_context_refs"]["main_result_ref"]],
        }
    ]
    payload["recommended_actions"] = [
        {
            "action_id": "route-back-claim-strength",
            "action_type": "route_back_same_line",
            "priority": "now",
            "reason": "Repair claim wording within the same paper line.",
            "route_target": "write",
            "route_key_question": "Which claim sentence exceeds evidence strength?",
            "route_rationale": "AI reviewer requires same-line manuscript repair before package advance.",
            "evidence_refs": [payload["runtime_context_refs"]["main_result_ref"]],
            "requires_controller_decision": True,
        }
    ]
    _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", payload)

    read_model = module.build_reviewer_refinement_loop_read_model(study_root=study_root)

    assert read_model["accept"]["accepted"] is False
    assert read_model["accept"]["package_mutation_allowed"] is False
    assert read_model["revert"]["required"] is True
    assert read_model["revert"]["strategy"] == "same_line_route_back"
    assert read_model["revert"]["direct_package_mutation_allowed"] is False
    assert read_model["revert"]["route_back"] == {
        "action_id": "route-back-claim-strength",
        "action_type": "route_back_same_line",
        "priority": "now",
        "route_target": "write",
        "route_key_question": "Which claim sentence exceeds evidence strength?",
        "route_rationale": "AI reviewer requires same-line manuscript repair before package advance.",
        "requires_controller_decision": True,
        "artifact_refs": [payload["runtime_context_refs"]["main_result_ref"]],
        "snapshot_refs": [
            {
                "source_surface": "publication_eval/latest.json",
                "source_eval_id": payload["eval_id"],
                "source_artifact_path": str(study_root / "artifacts" / "publication_eval" / "latest.json"),
            }
        ],
    }
    assert {
        (item["kind"], item.get("dimension") or item.get("gap_id"))
        for item in read_model["worklog"]
    } == {
        ("quality_dimension", "evidence_strength"),
        ("quality_dimension", "medical_journal_prose_quality"),
        ("publication_gap", "claim-strength"),
    }
    worklog_by_concern = {item["concern_id"]: item for item in read_model["worklog"]}
    assert worklog_by_concern["quality_dimension:evidence_strength"]["section"] == "evidence_strength"
    assert worklog_by_concern["quality_dimension:evidence_strength"]["reviewer_concern"] == (
        "Main result supports direction but not final claim strength."
    )
    assert worklog_by_concern["quality_dimension:evidence_strength"]["artifact_refs"] == [
        payload["runtime_context_refs"]["main_result_ref"]
    ]
    assert worklog_by_concern["publication_gap:claim-strength"]["section"] == "claim"
    assert worklog_by_concern["publication_gap:claim-strength"]["snapshot_refs"] == [
        {
            "source_surface": "publication_eval/latest.json",
            "source_eval_id": payload["eval_id"],
            "source_artifact_path": str(study_root / "artifacts" / "publication_eval" / "latest.json"),
        }
    ]
    assert worklog_by_concern["publication_gap:claim-strength"]["lifecycle"] == {
        "state": "reverted",
        "route": "same_line_route_back",
        "accepted": False,
        "reverted": True,
        "source": "ai_reviewer_backed_publication_eval_latest",
        "route_back_action_id": "route-back-claim-strength",
        "route_target": "write",
        "direct_package_mutation_allowed": False,
    }
    assert read_model["comment_to_action_matrix"] == read_model["repair_loop"][
        "comment_to_action_matrix"
    ]
    matrix_by_comment = {item["comment_id"]: item for item in read_model["comment_to_action_matrix"]}
    assert matrix_by_comment["publication_gap:claim-strength"]["repair_routes"]["analysis_repair"] == {
        "required": True,
        "target_claim": None,
        "target_section": "claim",
        "ledger_refs": [
            payload["runtime_context_refs"]["main_result_ref"],
            str(study_root / "paper" / "review" / "review_ledger.json"),
        ],
    }
    assert matrix_by_comment["publication_gap:claim-strength"]["action_type"] == "analysis_repair"
    assert matrix_by_comment["publication_gap:claim-strength"]["work_units"]["analysis_repair"] == {
        "work_unit_type": "analysis_repair",
        "required": True,
        "target_claim": None,
        "target_section": "claim",
        "ledger_refs": [
            payload["runtime_context_refs"]["main_result_ref"],
            str(study_root / "paper" / "review" / "review_ledger.json"),
        ],
    }
    assert matrix_by_comment["publication_gap:claim-strength"]["work_units"][
        "ai_reviewer_recheck"
    ] == {
        "work_unit_type": "ai_reviewer_recheck",
        "required": True,
        "reason": "analysis_repair_requires_ai_reviewer_recheck",
        "ledger_refs": [
            payload["runtime_context_refs"]["main_result_ref"],
            str(study_root / "paper" / "review" / "review_ledger.json"),
        ],
    }
    assert matrix_by_comment["publication_gap:claim-strength"]["repair_routes"]["text_repair"][
        "required"
    ] is False
    assert matrix_by_comment["publication_gap:claim-strength"]["repair_routes"][
        "ai_reviewer_recheck"
    ] == {
        "required": True,
        "reason": "analysis_repair_requires_ai_reviewer_recheck",
    }
    assert matrix_by_comment["quality_dimension:medical_journal_prose_quality"]["repair_routes"][
        "analysis_repair"
    ]["required"] is False
    assert matrix_by_comment["quality_dimension:medical_journal_prose_quality"]["repair_routes"][
        "text_repair"
    ] == {
        "required": True,
        "target_claim": None,
        "target_section": "medical_journal_prose_quality",
        "ledger_refs": [
            str(study_root / "paper" / "manuscript.md"),
            str(study_root / "paper" / "review" / "review_ledger.json"),
        ],
    }
    assert read_model["repair_loop"]["repair_plan"] == {
        "analysis_repair_required": True,
        "text_repair_required": True,
        "ai_reviewer_recheck_required": True,
        "mechanical_projection_can_authorize_quality": False,
    }
    assert read_model["repair_loop"]["mode"] == "repair_planning_only"
    assert read_model["repair_loop"]["blockers"] == []


def test_reviewer_refinement_loop_fails_closed_for_non_ai_reviewer_projection(
    tmp_path: Path,
) -> None:
    module = importlib.import_module(MODULE_NAME)
    study_root = tmp_path / "workspace" / "studies" / "001-risk"
    payload = _minimal_payload(study_root)
    payload["assessment_provenance"] = {
        "owner": "mechanical_projection",
        "source_kind": "publication_gate_projection",
        "policy_id": "publication_gate_projection_v1",
        "source_refs": [payload["runtime_context_refs"]["main_result_ref"]],
        "ai_reviewer_required": True,
    }
    _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", payload)

    read_model = module.build_reviewer_refinement_loop_read_model(study_root=study_root)

    assert read_model["accept"]["accepted"] is False
    assert "publication_eval_not_ai_reviewer_backed" in read_model["accept"]["blockers"]
    assert "publication_eval_still_requires_ai_reviewer" in read_model["accept"]["blockers"]
    assert "publication_eval_policy_not_ai_reviewer_critique" in read_model["accept"]["blockers"]
    assert read_model["revert"]["strategy"] == "same_line_route_back"
    assert read_model["revert"]["direct_package_mutation_allowed"] is False
    assert read_model["revert"]["route_back"]["route_target"] == "review"
    assert read_model["revert"]["route_back"]["action_type"] == "route_back_same_line"


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
    assert "required_calibration_ref_missing:coverage_as_quality" in read_model["accept"]["blockers"]
    assert "required_calibration_ref_missing:missing_reviewer_trace" in read_model["accept"]["blockers"]
    assert read_model["revert"]["strategy"] == "same_line_route_back"
    assert read_model["contract"]["read_model_only"] is True
    assert read_model["contract"]["learning_can_authorize_quality"] is False
    assert read_model["contract"]["learning_can_authorize_submission"] is False
    assert read_model["contract"]["learning_can_authorize_finalize"] is False


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
