from __future__ import annotations

import json
from pathlib import Path

from med_autoscience.controllers import study_domain_transition_table


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _current_ai_reviewer_route_back_eval(study_root: Path) -> dict:
    return {
        "eval_id": "publication-eval::dm002::current-route-back",
        "assessment_provenance": {
            "owner": "ai_reviewer",
            "ai_reviewer_required": False,
        },
        "verdict": {"overall_verdict": "blocked"},
        "quality_assessment": {
            "medical_journal_prose_quality": {
                "status": "blocked",
                "summary": "The manuscript needs same-line story repair.",
            }
        },
        "reviewer_operating_system": {
            "currentness_checks": {
                "medical_prose_review": {
                    "status": "current",
                    "request_digest": "sha256:request",
                    "manuscript_ref": str(study_root / "paper" / "manuscript.md"),
                    "manuscript_digest": "sha256:manuscript",
                    "route_back_required": True,
                    "route_target": "write",
                }
            }
        },
        "recommended_actions": [
            {
                "action_id": "ai-reviewer-action::return-to-write",
                "action_type": "route_back_same_line",
                "requires_controller_decision": True,
                "route_target": "write",
                "work_unit_fingerprint": "ai_reviewer_story_clean_external_validation_v3",
                "next_work_unit": {
                    "unit_id": "manuscript_story_repair",
                    "lane": "write",
                    "summary": "Rewrite the manuscript as a clean external-validation paper.",
                },
            }
        ],
    }


def test_current_ai_reviewer_write_routeback_does_not_project_reviewer_redrive_for_live_run(
    tmp_path: Path,
) -> None:
    study_root = tmp_path / "study"
    _write_json(
        study_root / study_domain_transition_table.PUBLICATION_EVAL_RELATIVE_PATH,
        _current_ai_reviewer_route_back_eval(study_root),
    )
    _write_json(
        study_root / study_domain_transition_table.CONTROLLER_DECISION_RELATIVE_PATH,
        {
            "decision_type": "continue_same_line",
            "route_target": "review",
            "next_work_unit": {"unit_id": "ai_reviewer_medical_prose_quality_review"},
        },
    )

    transition = study_domain_transition_table.project_domain_transition(
        study_id="dm002",
        study_root=study_root,
        status={},
        macro_state={},
        active_run_id="mas-run-dm002",
    )

    assert transition["decision_type"] == "active_runtime_watch"
    assert transition["owner"] == "mas_runtime"
    assert transition["controller_action"] == "runtime_watch"


def test_current_ai_reviewer_write_routeback_projects_same_line_write_handoff_when_not_live(
    tmp_path: Path,
) -> None:
    study_root = tmp_path / "study"
    _write_json(
        study_root / study_domain_transition_table.PUBLICATION_EVAL_RELATIVE_PATH,
        _current_ai_reviewer_route_back_eval(study_root),
    )

    transition = study_domain_transition_table.project_domain_transition(
        study_id="dm002",
        study_root=study_root,
        status={},
        macro_state={},
        active_run_id=None,
    )

    assert transition["decision_type"] == "route_back_same_line"
    assert transition["route_target"] == "write"
    assert transition["owner"] == "write"
    assert transition["next_work_unit"]["unit_id"] == "manuscript_story_repair"


def test_current_ai_reviewer_analysis_routeback_projects_analysis_campaign_handoff_when_not_live(
    tmp_path: Path,
) -> None:
    study_root = tmp_path / "study"
    publication_eval = _current_ai_reviewer_route_back_eval(study_root)
    prose_check = publication_eval["reviewer_operating_system"]["currentness_checks"]["medical_prose_review"]
    prose_check["route_target"] = "analysis-campaign"
    publication_eval["recommended_actions"] = [
        {
            "action_id": "ai-reviewer-action::return-to-analysis-campaign",
            "action_type": "route_back_same_line",
            "requires_controller_decision": True,
            "route_target": "analysis-campaign",
            "work_unit_fingerprint": "unit_harmonized_validation_uncertainty_and_grouped_calibration",
            "next_work_unit": {
                "unit_id": "unit_harmonized_validation_uncertainty_and_grouped_calibration",
                "lane": "analysis-campaign",
                "summary": "Close uncertainty intervals and grouped calibration for the unit-harmonized validation.",
            },
        }
    ]
    _write_json(
        study_root / study_domain_transition_table.PUBLICATION_EVAL_RELATIVE_PATH,
        publication_eval,
    )

    transition = study_domain_transition_table.project_domain_transition(
        study_id="dm002",
        study_root=study_root,
        status={},
        macro_state={},
        active_run_id=None,
    )

    assert transition["decision_type"] == "route_back_same_line"
    assert transition["route_target"] == "analysis-campaign"
    assert transition["owner"] == "analysis-campaign"
    assert transition["next_work_unit"]["unit_id"] == "unit_harmonized_validation_uncertainty_and_grouped_calibration"
