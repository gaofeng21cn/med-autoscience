from __future__ import annotations

from pathlib import Path

from med_autoscience.controllers import study_domain_transition_table
from tests.reviewer_os_fixture_helpers import current_manuscript_routeback_record
from tests.test_domain_transition_table_ai_reviewer_routeback import (
    _current_ai_reviewer_route_back_eval,
    _write_json,
)


def test_materialized_controller_ai_reviewer_route_has_own_next_action(
    tmp_path: Path,
) -> None:
    study_root = tmp_path / "study"
    publication_eval = _current_ai_reviewer_route_back_eval(study_root)
    publication_eval["recommended_actions"] = []
    _write_json(study_root / study_domain_transition_table.PUBLICATION_EVAL_RELATIVE_PATH, publication_eval)
    _write_json(
        study_root / study_domain_transition_table.CONTROLLER_DECISION_RELATIVE_PATH,
        {
            "schema_version": 1,
            "decision_id": "dm003-controller-ai-reviewer-re-eval",
            "decision_type": "continue_same_line",
            "study_id": "dm003",
            "quest_id": "dm003",
            "requires_human_confirmation": False,
            "controller_actions": [{"action_type": "return_to_ai_reviewer_workflow"}],
            "route_target": "review",
            "work_unit_fingerprint": (
                "domain-transition::ai_reviewer_re_eval::ai_reviewer_medical_prose_quality_review"
            ),
            "next_work_unit": {
                "unit_id": "ai_reviewer_medical_prose_quality_review",
                "lane": "review",
                "summary": "Continue the current MAS controller-authorized domain route.",
            },
        },
    )

    transition = study_domain_transition_table.project_domain_transition(
        study_id="dm003",
        study_root=study_root,
        status={},
        macro_state={},
        active_run_id=None,
    )

    assert transition["decision_type"] == "ai_reviewer_re_eval"
    assert transition["controller_action"] == "return_to_ai_reviewer_workflow"
    assert transition["owner"] == "ai_reviewer"
    assert transition["guard_boundary"]["opl_generic_runner_may_resume"] is True
    assert transition["next_action"]["action_family"] == "paper.review.ai_reviewer"
    assert transition["next_action"]["action_kind"] == "owner_review"
    assert transition["next_action"]["owner"] == "ai_reviewer"
    assert transition["next_action"]["work_unit_id"] == "ai_reviewer_medical_prose_quality_review"


def test_materialized_controller_write_route_preempts_stale_ai_reviewer_projection(
    tmp_path: Path,
) -> None:
    study_root = tmp_path / "study"
    manuscript_path = study_root / "paper" / "draft.md"
    manuscript_text = "# Draft\n\nCurrent manuscript still needs medical prose repair.\n"
    manuscript_path.parent.mkdir(parents=True, exist_ok=True)
    manuscript_path.write_text(manuscript_text, encoding="utf-8")
    old_eval = _current_ai_reviewer_route_back_eval(study_root)
    old_eval["eval_id"] = "publication-eval::dm003::old-readiness-blocker"
    _write_json(study_root / study_domain_transition_table.PUBLICATION_EVAL_RELATIVE_PATH, old_eval)
    current_record_path = (
        study_root
        / "artifacts"
        / "publication_eval"
        / "ai_reviewer_responses"
        / "20260616T015951Z_publication_eval_record.json"
    )
    current_record = current_manuscript_routeback_record(
        study_root=study_root,
        manuscript_path=manuscript_path,
        manuscript_text=manuscript_text,
        study_id="dm003",
        quest_id="dm003",
        eval_id="publication-eval::dm003::current-ai-reviewer-no-routeback-action",
        emitted_at="2026-06-16T01:59:51+00:00",
    )
    current_record["recommended_actions"] = []
    _write_json(current_record_path, current_record)
    _write_json(
        study_root / study_domain_transition_table.CONTROLLER_DECISION_RELATIVE_PATH,
        {
            "schema_version": 1,
            "decision_id": "dm003-controller-route-back-write",
            "decision_type": "route_back_same_line",
            "study_id": "dm003",
            "quest_id": "dm003",
            "requires_human_confirmation": False,
            "controller_actions": [{"action_type": "run_quality_repair_batch"}],
            "route_target": "write",
            "work_unit_fingerprint": "domain-transition::route_back_same_line::medical_prose_write_repair",
            "next_work_unit": {
                "unit_id": "medical_prose_write_repair",
                "lane": "write",
                "summary": "Repair medical prose against the current AI reviewer record.",
            },
        },
    )

    transition = study_domain_transition_table.project_domain_transition(
        study_id="dm003",
        study_root=study_root,
        status={},
        macro_state={},
        active_run_id=None,
    )

    assert transition["decision_type"] == "route_back_same_line"
    assert transition["route_target"] == "write"
    assert transition["owner"] == "write"
    assert transition["controller_action"] == "request_opl_stage_attempt"
    assert transition["next_work_unit"]["unit_id"] == "medical_prose_write_repair"
    assert str(current_record_path.resolve()) in transition["source_refs"]
    assert str((study_root / study_domain_transition_table.CONTROLLER_DECISION_RELATIVE_PATH).resolve()) in transition[
        "source_refs"
    ]


def test_current_ai_reviewer_write_routeback_preempts_consumed_story_recheck_request(
    tmp_path: Path,
) -> None:
    study_root = tmp_path / "study"
    publication_eval = _current_ai_reviewer_route_back_eval(study_root)
    publication_eval["eval_id"] = "publication-eval::dm002::current-ai-reviewer-write-repair"
    publication_eval["recommended_actions"] = [
        {
            "action_id": "dm002-current-ai-reviewer-write-repair",
            "action_type": "route_back_same_line",
            "requires_controller_decision": True,
            "route_target": "write",
            "work_unit_fingerprint": "dm002_same_line_publication_paper_repair_20260521",
            "next_work_unit": {
                "unit_id": "dm002_same_line_publication_paper_repair",
                "lane": "write",
                "summary": "Repair current AI reviewer paper-surface findings.",
            },
        }
    ]
    _write_json(
        study_root / study_domain_transition_table.PUBLICATION_EVAL_RELATIVE_PATH,
        publication_eval,
    )
    _write_json(
        study_root / "artifacts" / "controller" / "publication_work_unit_lifecycle" / "latest.json",
        {
            "schema_version": 1,
            "source_eval_id": publication_eval["eval_id"],
            "status": "blocked",
            "work_unit": {"unit_id": "manuscript_story_repair"},
            "unit_statuses": [
                {"unit_id": "repair_paper_live_paths", "status": "current"},
                {"unit_id": "materialize_display_surface", "status": "materialized"},
            ],
            "gate_replay_status": "blocked",
        },
    )
    ai_reviewer_request_path = (
        study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json"
    )
    _write_json(ai_reviewer_request_path, {"request_id": "ai-reviewer-recheck::dm002"})
    publication_eval["assessment_provenance"]["source_refs"] = [str(ai_reviewer_request_path)]
    _write_json(
        study_root / study_domain_transition_table.PUBLICATION_EVAL_RELATIVE_PATH,
        publication_eval,
    )
    _write_json(
        study_root / study_domain_transition_table.REPAIR_EXECUTION_EVIDENCE_RELATIVE_PATH,
        {
            "schema_version": 1,
            "status": "progress_delta_candidate",
            "review_finding": {"source_eval_id": publication_eval["eval_id"]},
            "repair_work_unit": {"unit_id": "manuscript_story_repair"},
            "ai_reviewer_recheck_required": True,
            "ai_reviewer_recheck_done": True,
            "ai_reviewer_recheck_request_ref": str(ai_reviewer_request_path),
            "manuscript_surface_hygiene": {
                "status": "clear",
                "blockers": [],
                "story_surface_delta_required": True,
                "story_surface_delta_present": True,
                "story_surface_delta_refs": [
                    {
                        "path": str(study_root / "paper" / "draft.md"),
                        "artifact_role": "canonical_manuscript_story_surface",
                    }
                ],
            },
            "blockers": [],
        },
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
    assert transition["controller_action"] == "request_opl_stage_attempt"
    assert transition["next_work_unit"]["unit_id"] == "dm002_same_line_publication_paper_repair"


def test_current_ai_reviewer_write_routeback_preempts_unconsumed_story_recheck_request(
    tmp_path: Path,
) -> None:
    study_root = tmp_path / "study"
    publication_eval = _current_ai_reviewer_route_back_eval(study_root)
    publication_eval["eval_id"] = "publication-eval::dm003::current-ai-reviewer-write-repair"
    publication_eval["recommended_actions"][0]["next_work_unit"] = {
        "unit_id": "dm003_bounded_prose_repair_after_post_sync_reviewer_record",
        "lane": "write",
        "summary": "Apply bounded prose repair from current medical prose review.",
    }
    _write_json(
        study_root / study_domain_transition_table.PUBLICATION_EVAL_RELATIVE_PATH,
        publication_eval,
    )
    _write_json(
        study_root / "artifacts" / "controller" / "publication_work_unit_lifecycle" / "latest.json",
        {
            "schema_version": 1,
            "source_eval_id": publication_eval["eval_id"],
            "status": "blocked",
            "work_unit": {"unit_id": "manuscript_story_repair"},
            "unit_statuses": [],
            "gate_replay_status": "blocked",
        },
    )
    ai_reviewer_request_path = (
        study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json"
    )
    _write_json(ai_reviewer_request_path, {"request_id": "ai-reviewer-recheck::dm003"})
    _write_json(
        study_root / study_domain_transition_table.REPAIR_EXECUTION_EVIDENCE_RELATIVE_PATH,
        {
            "schema_version": 1,
            "status": "progress_delta_candidate",
            "review_finding": {"source_eval_id": publication_eval["eval_id"]},
            "repair_work_unit": {"unit_id": "manuscript_story_repair"},
            "ai_reviewer_recheck_required": True,
            "ai_reviewer_recheck_done": True,
            "ai_reviewer_recheck_request_ref": str(ai_reviewer_request_path),
            "manuscript_surface_hygiene": {
                "status": "clear",
                "blockers": [],
                "story_surface_delta_present": True,
                "story_surface_delta_refs": [
                    {
                        "path": str(study_root / "paper" / "draft.md"),
                        "artifact_role": "canonical_manuscript_story_surface",
                    }
                ],
            },
            "blockers": [],
        },
    )

    transition = study_domain_transition_table.project_domain_transition(
        study_id="dm003",
        study_root=study_root,
        status={},
        macro_state={},
        active_run_id=None,
    )

    assert transition["decision_type"] == "route_back_same_line"
    assert transition["route_target"] == "write"
    assert transition["owner"] == "write"
    assert transition["controller_action"] == "request_opl_stage_attempt"
    assert transition["next_work_unit"]["unit_id"] == (
        "dm003_bounded_prose_repair_after_post_sync_reviewer_record"
    )
