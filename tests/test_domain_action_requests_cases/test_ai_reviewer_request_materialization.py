from __future__ import annotations

import json

from med_autoscience.controllers.domain_action_requests import build_ai_reviewer_publication_eval_request
from med_autoscience.controllers.domain_action_request_lifecycle import (
    materialize_ai_reviewer_request,
    read_ai_reviewer_request,
)
from tests.reviewer_os_fixture_helpers import current_manuscript_routeback_reviewer_os


QUALITY_DIMENSIONS = (
    "clinical_significance",
    "evidence_strength",
    "novelty_positioning",
    "medical_journal_prose_quality",
    "human_review_readiness",
)


def _quality_assessment(*, partial_dimension: str = "medical_journal_prose_quality") -> dict[str, dict[str, str]]:
    return {
        dimension: {
            "status": "partial" if dimension == partial_dimension else "ready",
            "summary": f"{dimension} reviewer assessment.",
        }
        for dimension in QUALITY_DIMENSIONS
    }


def _future_plan(*, limitation: str = "Current review is bound to the active manuscript digest.") -> list[dict[str, object]]:
    return [
        {
            "limitation": limitation,
            "impact_on_claim": "Claims remain supported with limitations until write repair and re-review.",
            "required_future_analysis_data_or_design": "Rerun AI reviewer after canonical manuscript repair.",
            "current_manuscript_wording_must_be_restrained": True,
        }
    ]


def _reviewer_operating_system(*, study_root, eval_id: str) -> dict[str, object]:
    manuscript_path = study_root / "paper" / "draft.md"
    manuscript_text = "# Draft\n\nCurrent canonical manuscript.\n"
    manuscript_path.parent.mkdir(parents=True, exist_ok=True)
    manuscript_path.write_text(manuscript_text, encoding="utf-8")
    return current_manuscript_routeback_reviewer_os(
        study_root=study_root,
        manuscript_path=manuscript_path,
        manuscript_text=manuscript_text,
        eval_id=eval_id,
    )


def _ai_reviewer_record(
    *,
    study_root,
    eval_id: str,
    quality_assessment: dict[str, object] | None = None,
    future_plan: list[dict[str, object]] | None = None,
    emitted_at: str | None = None,
    source_refs: list[str] | None = None,
    recommended_actions: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    provenance = {
        "owner": "ai_reviewer",
        "source_kind": "publication_eval_ai_reviewer",
        "policy_id": "medical_publication_critique_v1",
        "ai_reviewer_required": False,
    }
    if source_refs is not None:
        provenance["source_refs"] = source_refs
    record: dict[str, object] = {
        "eval_id": eval_id,
        "study_id": "002-risk",
        "quest_id": "quest-002",
        "assessment_provenance": provenance,
        "quality_assessment": quality_assessment or _quality_assessment(),
        "future_facing_limitations_plan": future_plan or _future_plan(),
        "reviewer_operating_system": _reviewer_operating_system(
            study_root=study_root,
            eval_id=eval_id,
        ),
    }
    if emitted_at is not None:
        record["emitted_at"] = emitted_at
    if recommended_actions is not None:
        record["recommended_actions"] = recommended_actions
    return record


def test_ai_reviewer_request_materialization_attaches_latest_owner_record(tmp_path) -> None:
    study_root = tmp_path / "workspace" / "studies" / "002-risk"
    response_root = study_root / "artifacts" / "publication_eval" / "ai_reviewer_responses"
    stale_record_path = response_root / "20260517T070000Z_publication_eval_record.json"
    current_record_path = response_root / "20260517T074205Z_publication_eval_record.json"
    current_record = _ai_reviewer_record(
        study_root=study_root,
        eval_id="publication-eval::002-risk::quest-002::2026-05-17T07:42:05+00:00",
    )
    stale_record_path.parent.mkdir(parents=True)
    stale_record_path.write_text(
        '{"eval_id":"stale","assessment_provenance":{"owner":"mechanical_projection"}}\n',
        encoding="utf-8",
    )
    current_record_path.write_text(json.dumps(current_record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    packet = build_ai_reviewer_publication_eval_request(
        study_id="002-risk",
        quest_id="quest-002",
        source_surface="owner_route_reconcile",
        workflow_state={
            "quality_authority": {"owner": "mechanical_projection", "state": "projection_only"},
            "route_back": {"required": True, "target": "ai_reviewer"},
        },
    )

    materialized = materialize_ai_reviewer_request(study_root=study_root, packet=packet)
    persisted = read_ai_reviewer_request(study_root=study_root)

    assert materialized["ai_reviewer_record"] == current_record
    assert persisted is not None
    assert persisted["publication_eval_record_ref"] == str(current_record_path.resolve())
    assert persisted["ai_reviewer_record"]["eval_id"] == current_record["eval_id"]
    assert persisted["request_lifecycle"]["state"] == "requested"
    assert persisted["request_lifecycle"]["assessment_ref"] == str(current_record_path.resolve())
    assert persisted["request_lifecycle"]["blocked_reason"] is None
    assert "stale_record_ref" not in persisted["request_lifecycle"]
    assert "required_currentness_refs" not in persisted["request_lifecycle"]


def test_ai_reviewer_request_materialization_rejects_record_with_manuscript_story_provenance_leakage(
    tmp_path,
) -> None:
    study_root = tmp_path / "workspace" / "studies" / "002-risk"
    response_root = study_root / "artifacts" / "publication_eval" / "ai_reviewer_responses"
    record_path = response_root / "20260517T074205Z_publication_eval_record.json"
    quality_assessment = _quality_assessment()
    quality_assessment["novelty_positioning"][
        "summary"
    ] = "The defensible contribution is now a harmonization-sensitive external validation."
    record = _ai_reviewer_record(
        study_root=study_root,
        eval_id="publication-eval::002-risk::quest-002::2026-05-17T07:42:05+00:00",
        quality_assessment=quality_assessment,
    )
    record_path.parent.mkdir(parents=True)
    record_path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    packet = build_ai_reviewer_publication_eval_request(
        study_id="002-risk",
        quest_id="quest-002",
        source_surface="owner_route_reconcile",
        workflow_state={
            "quality_authority": {"owner": "mechanical_projection", "state": "projection_only"},
            "route_back": {"required": True, "target": "ai_reviewer"},
        },
    )

    materialized = materialize_ai_reviewer_request(study_root=study_root, packet=packet)
    persisted = read_ai_reviewer_request(study_root=study_root)

    assert "ai_reviewer_record" not in materialized
    assert "publication_eval_record_ref" not in materialized
    assert persisted is not None
    assert "ai_reviewer_record" not in persisted
    assert (
        persisted["request_lifecycle"]["blocked_reason"]
        == "ai_reviewer_record_manuscript_story_provenance_leakage"
    )
    assert persisted["request_lifecycle"]["stale_record_ref"] == str(record_path.resolve())
    assert persisted["request_lifecycle"]["leakage_reason"] == "manuscript_story_provenance_leakage"
    assert persisted["request_lifecycle"]["leakage_field_path"] == "quality_assessment.novelty_positioning.summary"
    assert persisted["request_lifecycle"]["next_required_actions"] == [
        "produce_ai_reviewer_publication_eval_record_against_current_medical_prose_style_v3",
        "rematerialize_ai_reviewer_request",
        "return_to_ai_reviewer_workflow",
    ]


def test_ai_reviewer_request_materialization_rejects_record_stale_after_unit_harmonized_rerun(
    tmp_path,
) -> None:
    study_root = tmp_path / "workspace" / "studies" / "002-risk"
    response_root = study_root / "artifacts" / "publication_eval" / "ai_reviewer_responses"
    current_record_path = response_root / "20260517T074205Z_publication_eval_record.json"
    analysis_root = study_root / "artifacts" / "controller" / "analysis_harmonization"
    analysis_path = analysis_root / "latest.json"
    rerun_path = analysis_root / "unit_harmonized_external_validation_rerun.json"
    current_record = _ai_reviewer_record(
        study_root=study_root,
        eval_id="publication-eval::002-risk::quest-002::2026-05-17T07:42:05+00:00",
    )
    analysis_path.parent.mkdir(parents=True)
    analysis_path.write_text(
        json.dumps(
            {
                "surface": "analysis_harmonization_owner_result",
                "owner": "analysis_harmonization_owner",
                "work_unit": "unit_harmonized_external_validation_rerun",
                "status": "completed",
                "unit_harmonized_rerun_completed": True,
                "rerun_evidence_ref": str(rerun_path),
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    current_record_path.parent.mkdir(parents=True)
    current_record_path.write_text(json.dumps(current_record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    packet = build_ai_reviewer_publication_eval_request(
        study_id="002-risk",
        quest_id="quest-002",
        source_surface="runtime_supervisor_scan",
        workflow_state={
            "quality_authority": {"owner": "mechanical_projection", "state": "projection_only"},
            "route_back": {"required": True, "target": "ai_reviewer"},
        },
    )

    materialized = materialize_ai_reviewer_request(study_root=study_root, packet=packet)
    persisted = read_ai_reviewer_request(study_root=study_root)

    assert "ai_reviewer_record" not in materialized
    assert "publication_eval_record_ref" not in materialized
    assert persisted is not None
    assert "ai_reviewer_record" not in persisted
    assert persisted["request_lifecycle"]["blocked_reason"] == "ai_reviewer_record_stale_after_unit_harmonized_rerun"
    assert persisted["request_lifecycle"]["stale_record_ref"] == str(current_record_path.resolve())
    assert persisted["request_lifecycle"]["required_currentness_refs"] == [
        str(analysis_path.resolve()),
        str(rerun_path.resolve()),
    ]


def test_ai_reviewer_request_materialization_rejects_record_that_mentions_but_predates_unit_harmonized_rerun(
    tmp_path,
) -> None:
    study_root = tmp_path / "workspace" / "studies" / "002-risk"
    response_root = study_root / "artifacts" / "publication_eval" / "ai_reviewer_responses"
    stale_record_path = response_root / "20260520T181412Z_publication_eval_record.json"
    analysis_root = study_root / "artifacts" / "controller" / "analysis_harmonization"
    analysis_path = analysis_root / "latest.json"
    rerun_path = analysis_root / "unit_harmonized_external_validation_rerun.json"
    stale_record = _ai_reviewer_record(
        study_root=study_root,
        eval_id="publication-eval::002-risk::quest-002::2026-05-20T18:14:12+00:00",
        emitted_at="2026-05-20T18:14:12+00:00",
        source_refs=[str(analysis_path), str(rerun_path)],
        quality_assessment=_quality_assessment(partial_dimension="evidence_strength"),
        future_plan=_future_plan(
            limitation="Current review predates the completed unit-harmonized evidence.",
        ),
    )
    analysis_path.parent.mkdir(parents=True)
    analysis_path.write_text(
        json.dumps(
            {
                "surface": "analysis_harmonization_owner_result",
                "owner": "analysis_harmonization_owner",
                "work_unit": "unit_harmonized_external_validation_rerun",
                "status": "completed",
                "generated_at": "2026-05-21T20:49:54+00:00",
                "unit_harmonized_rerun_completed": True,
                "rerun_evidence_ref": str(rerun_path),
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    rerun_path.write_text(
        json.dumps(
            {
                "surface": "unit_harmonized_external_validation_rerun_evidence",
                "status": "completed",
                "generated_at": "2026-05-21T20:49:54+00:00",
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    response_root.mkdir(parents=True)
    stale_record_path.write_text(json.dumps(stale_record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    packet = build_ai_reviewer_publication_eval_request(
        study_id="002-risk",
        quest_id="quest-002",
        source_surface="runtime_supervisor_scan",
        workflow_state={
            "quality_authority": {"owner": "mechanical_projection", "state": "projection_only"},
            "route_back": {"required": True, "target": "ai_reviewer"},
        },
    )

    materialized = materialize_ai_reviewer_request(study_root=study_root, packet=packet)
    persisted = read_ai_reviewer_request(study_root=study_root)

    assert "ai_reviewer_record" not in materialized
    assert "publication_eval_record_ref" not in materialized
    assert persisted is not None
    assert "ai_reviewer_record" not in persisted
    assert persisted["request_lifecycle"]["blocked_reason"] == "ai_reviewer_record_stale_after_unit_harmonized_rerun"
    assert persisted["request_lifecycle"]["stale_record_ref"] == str(stale_record_path.resolve())
    assert persisted["request_lifecycle"]["required_currentness_refs"] == [
        str(analysis_path.resolve()),
        str(rerun_path.resolve()),
    ]


def test_ai_reviewer_request_materialization_rejects_prepopulated_record_stale_after_unit_harmonized_rerun(
    tmp_path,
) -> None:
    study_root = tmp_path / "workspace" / "studies" / "002-risk"
    record_path = study_root / "artifacts" / "publication_eval" / "ai_reviewer_responses" / "record.json"
    analysis_root = study_root / "artifacts" / "controller" / "analysis_harmonization"
    analysis_path = analysis_root / "latest.json"
    rerun_path = analysis_root / "unit_harmonized_external_validation_rerun.json"
    prepopulated_record = _ai_reviewer_record(
        study_root=study_root,
        eval_id="publication-eval::002-risk::quest-002::prepopulated",
    )
    analysis_path.parent.mkdir(parents=True)
    analysis_path.write_text(
        json.dumps(
            {
                "surface": "analysis_harmonization_owner_result",
                "owner": "analysis_harmonization_owner",
                "work_unit": "unit_harmonized_external_validation_rerun",
                "status": "completed",
                "unit_harmonized_rerun_completed": True,
                "rerun_evidence_ref": str(rerun_path),
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    packet = build_ai_reviewer_publication_eval_request(
        study_id="002-risk",
        quest_id="quest-002",
        source_surface="runtime_supervisor_scan",
        workflow_state={
            "quality_authority": {"owner": "mechanical_projection", "state": "projection_only"},
            "route_back": {"required": True, "target": "ai_reviewer"},
        },
    )
    packet["ai_reviewer_record"] = prepopulated_record
    packet["publication_eval_record_ref"] = str(record_path)

    materialized = materialize_ai_reviewer_request(study_root=study_root, packet=packet)
    persisted = read_ai_reviewer_request(study_root=study_root)

    assert "ai_reviewer_record" not in materialized
    assert "publication_eval_record_ref" not in materialized
    assert persisted is not None
    assert "ai_reviewer_record" not in persisted
    assert persisted["request_lifecycle"]["blocked_reason"] == "ai_reviewer_record_stale_after_unit_harmonized_rerun"
    assert persisted["request_lifecycle"]["stale_record_ref"] == str(record_path)
    assert persisted["request_lifecycle"]["required_currentness_refs"] == [
        str(analysis_path.resolve()),
        str(rerun_path.resolve()),
    ]


def test_ai_reviewer_request_materialization_replaces_prepopulated_record_with_newer_owner_record(
    tmp_path,
) -> None:
    study_root = tmp_path / "workspace" / "studies" / "002-risk"
    response_root = study_root / "artifacts" / "publication_eval" / "ai_reviewer_responses"
    old_record_path = response_root / "20260519T202816Z_publication_eval_record.json"
    new_record_path = response_root / "20260520T181412Z_publication_eval_record.json"
    old_record = _ai_reviewer_record(
        study_root=study_root,
        eval_id="publication-eval::002-risk::quest-002::2026-05-19T20:28:16+00:00",
        future_plan=_future_plan(limitation="Old reviewer record remains only as provenance."),
    )
    new_record = _ai_reviewer_record(
        study_root=study_root,
        eval_id="publication-eval::002-risk::quest-002::2026-05-20T18:14:12+00:00",
        future_plan=_future_plan(limitation="Current reviewer record routes the study to bounded analysis."),
        recommended_actions=[
            {
                "action_id": "ai-reviewer-action::return-to-analysis-campaign",
                "action_type": "route_back_same_line",
                "requires_controller_decision": True,
                "route_target": "analysis-campaign",
                "next_work_unit": {
                    "unit_id": "unit_harmonized_validation_uncertainty_and_grouped_calibration",
                    "lane": "analysis-campaign",
                    "summary": "Close uncertainty intervals and grouped calibration for the unit-harmonized validation.",
                },
            }
        ],
    )
    response_root.mkdir(parents=True)
    old_record_path.write_text(json.dumps(old_record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    new_record_path.write_text(json.dumps(new_record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    packet = build_ai_reviewer_publication_eval_request(
        study_id="002-risk",
        quest_id="quest-002",
        source_surface="runtime_supervisor_scan",
        workflow_state={
            "quality_authority": {"owner": "mechanical_projection", "state": "projection_only"},
            "route_back": {"required": True, "target": "ai_reviewer"},
        },
    )
    packet["ai_reviewer_record"] = old_record
    packet["publication_eval_record_ref"] = str(old_record_path.resolve())
    packet["request_lifecycle"]["assessment_ref"] = str(old_record_path.resolve())

    materialized = materialize_ai_reviewer_request(study_root=study_root, packet=packet)
    persisted = read_ai_reviewer_request(study_root=study_root)

    assert materialized["ai_reviewer_record"] == new_record
    assert materialized["publication_eval_record_ref"] == str(new_record_path.resolve())
    assert persisted is not None
    assert persisted["ai_reviewer_record"]["eval_id"] == new_record["eval_id"]
    assert persisted["publication_eval_record_ref"] == str(new_record_path.resolve())
    assert persisted["request_lifecycle"]["assessment_ref"] == str(new_record_path.resolve())
    assert persisted["request_lifecycle"]["blocked_reason"] is None
    assert "stale_record_ref" not in persisted["request_lifecycle"]
    assert "required_currentness_refs" not in persisted["request_lifecycle"]
