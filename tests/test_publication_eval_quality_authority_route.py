from __future__ import annotations

import importlib

import pytest


def _no_specificity_targets(report: dict[str, object]) -> tuple[dict[str, str], ...]:
    return ()


@pytest.mark.parametrize("prose_status", [None, "underdefined", "partial", "blocked"])
@pytest.mark.parametrize("current_required_action", ["continue_write_stage", "continue_bundle_stage"])
def test_clear_gate_routes_back_to_review_when_medical_prose_quality_is_not_ready(
    prose_status: str | None,
    current_required_action: str,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_runtime_decision_parts.publication_decision"
    )
    report = {
        "status": "clear",
        "current_required_action": current_required_action,
        "controller_stage_note": "Publication bundle stage is unlocked.",
        "medical_prose_review_summary": "AI reviewer has not closed manuscript-native medical journal prose quality.",
        "medical_prose_review_path": "/tmp/study/artifacts/publication_eval/medical_prose_review.json",
    }
    if prose_status is not None:
        report["medical_prose_review_status"] = prose_status

    action = module.publication_eval_action(
        report=report,
        generated_at="2026-05-15T00:00:00+00:00",
        evidence_refs=("/tmp/study/artifacts/publication_eval/latest.json",),
        specificity_targets=_no_specificity_targets,
    )

    assert action.action_type == "route_back_same_line"
    assert action.route_target == "review"
    assert (
        action.route_key_question
        == "Which AI-reviewer manuscript-quality issue must close before the manuscript can advance?"
    )
    assert action.next_work_unit == {
        "unit_id": "ai_reviewer_medical_prose_quality_review",
        "lane": "review",
        "summary": "Re-run AI reviewer manuscript-quality review and close medical_journal_prose_quality before draft advancement.",
    }
    expected_status = prose_status or "underdefined"
    assert action.work_unit_fingerprint == f"medical-prose-quality::{expected_status}"
    assert action.reason == (
        f"AI reviewer medical_journal_prose_quality is {expected_status}; "
        "a clear publication gate cannot authorize draft advancement until that quality dimension is ready."
    )


def test_clear_bundle_gate_can_continue_to_finalize_when_medical_prose_quality_is_ready() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_runtime_decision_parts.publication_decision"
    )

    action = module.publication_eval_action(
        report={
            "status": "clear",
            "current_required_action": "continue_bundle_stage",
            "controller_stage_note": "Publication bundle stage is unlocked.",
            "medical_prose_review_status": "ready",
            "medical_prose_review_summary": "AI reviewer closed manuscript-native medical journal prose quality.",
            "medical_prose_review_path": "/tmp/study/artifacts/publication_eval/medical_prose_review.json",
        },
        generated_at="2026-05-15T00:00:00+00:00",
        evidence_refs=("/tmp/study/artifacts/publication_eval/latest.json",),
        specificity_targets=_no_specificity_targets,
    )

    assert action.action_type == "continue_same_line"
    assert action.route_target == "finalize"
    assert action.reason == "Publication bundle stage is unlocked."
