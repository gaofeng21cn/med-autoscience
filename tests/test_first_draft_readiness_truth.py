from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Any

from tests.test_medical_paper_readiness import _materialize_complete_readiness_inputs


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_first_draft_inputs(study_root: Path) -> None:
    _write_json(
        study_root / "paper" / "medical_manuscript_blueprint.json",
        {
            "schema_version": 1,
            "surface": "medical_manuscript_blueprint",
            "status": "closed",
            "canonical_ready": True,
            "authoring_provenance": {
                "owner": "ai_author",
                "source_kind": "medical_manuscript_blueprint",
                "policy_id": "medical_manuscript_blueprint_v1",
                "ai_reviewer_required": False,
            },
        },
    )
    _write_json(
        study_root / "artifacts" / "publication_eval" / "medical_prose_review.json",
        {
            "schema_version": 1,
            "surface": "medical_prose_review",
            "medical_journal_prose_quality": {
                "status": "ready",
                "overall_style_verdict": "clear",
                "summary": "Medical prose review is clear.",
                "route_back_recommendation": {
                    "required": False,
                    "route_target": "none",
                    "reason": "No route back required.",
                },
            },
        },
    )
    _write_json(
        study_root / "paper" / "review" / "review_ledger.json",
        {
            "schema_version": 1,
            "surface": "review_ledger",
            "status": "closed",
            "charter_expectation_closures": [
                {
                    "expectation_key": "scientific_followup_questions",
                    "status": "closed",
                }
            ],
        },
    )
    _write_json(
        study_root / "artifacts" / "real_study_soak_matrix" / "evidence.json",
        {
            "stage_evidence": {
                "literature_scout": ["artifacts/medical_paper/literature_scout.json"],
                "line_selection": ["artifacts/medical_paper/study_line_selection.json"],
                "main_analysis": ["paper/medical_analysis_contract.json"],
                "bounded_analysis": ["artifacts/medical_paper/bounded_analysis_candidate_board.json"],
                "route_back": ["artifacts/controller_decisions/latest.json"],
                "stop_loss": ["artifacts/medical_paper/stop_loss_memo.json"],
                "revision_reopen": ["artifacts/task_intake/latest.json"],
                "runtime_recovery": ["artifacts/runtime/runtime_supervision/latest.json"],
                "finalize_rebuild": ["paper/submission_minimal/current_package.zip"],
                "final_pre_submission_audit": ["artifacts/publication_eval/latest.json"],
            }
        },
    )


def test_first_draft_readiness_truth_marks_single_study_ready_when_inputs_are_closed(
    tmp_path: Path,
) -> None:
    readiness_module = importlib.import_module("med_autoscience.controllers.medical_paper_readiness")
    truth_module = importlib.import_module("med_autoscience.controllers.first_draft_readiness_truth")
    study_root = tmp_path / "study"
    _materialize_complete_readiness_inputs(readiness_module, study_root)
    _write_first_draft_inputs(study_root)

    result = truth_module.build_first_draft_readiness_truth(study_root=study_root)
    persisted = truth_module.read_first_draft_readiness_truth(study_root=study_root)

    assert result == persisted
    assert result["surface"] == "first_draft_readiness_truth"
    assert result["status"] == "first_draft_ready"
    assert result["first_draft_ready"] is True
    assert result["single_study"] is True
    assert result["quality_claim_authorized"] is False
    assert result["mechanical_projection_can_authorize_quality"] is False
    assert result["blockers"] == []
    assert result["readiness_inputs"]["medical_paper_readiness"]["overall_status"] == "ready"
    assert result["readiness_inputs"]["medical_manuscript_blueprint"]["ready"] is True
    assert result["readiness_inputs"]["medical_prose_review"]["ready"] is True
    assert result["readiness_inputs"]["review_ledger"]["ready"] is True


def test_first_draft_readiness_truth_blocks_when_blueprint_prose_or_ledger_are_open(
    tmp_path: Path,
) -> None:
    readiness_module = importlib.import_module("med_autoscience.controllers.medical_paper_readiness")
    truth_module = importlib.import_module("med_autoscience.controllers.first_draft_readiness_truth")
    study_root = tmp_path / "study"
    _materialize_complete_readiness_inputs(readiness_module, study_root)
    _write_first_draft_inputs(study_root)
    _write_json(
        study_root / "artifacts" / "publication_eval" / "medical_prose_review.json",
        {
            "schema_version": 1,
            "surface": "medical_prose_review",
            "medical_journal_prose_quality": {
                "status": "partial",
                "route_back_recommendation": {
                    "required": True,
                    "route_target": "write",
                    "reason": "Rewrite Results prose.",
                },
            },
        },
    )

    result = truth_module.build_first_draft_readiness_truth(study_root=study_root)

    assert result["status"] == "blocked"
    assert result["first_draft_ready"] is False
    assert "medical_prose_review_not_ready" in result["blockers"]
    assert result["readiness_inputs"]["medical_paper_readiness"]["overall_status"] == "ready"
    assert result["readiness_inputs"]["medical_prose_review"]["ready"] is False
