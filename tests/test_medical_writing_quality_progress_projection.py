from __future__ import annotations

import json
from pathlib import Path

from tests.study_runtime_test_helpers import make_profile, write_study


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_study_progress_projects_medical_writing_quality_surfaces(tmp_path: Path) -> None:
    from med_autoscience.controllers import study_progress

    profile = make_profile(tmp_path)
    workspace_root = profile.workspace_root
    study_root = workspace_root / "studies" / "001-risk"
    quest_root = profile.runtime_root / "quest-001"
    write_study(workspace_root, "001-risk", quest_id="quest-001")
    _write_json(
        study_root / "artifacts" / "runtime" / "last_launch_report.json",
        {
            "schema_version": 1,
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "quest_root": str(quest_root),
            "status": "active",
        },
    )
    _write_json(
        study_root / "paper" / "medical_manuscript_blueprint.json",
        {
            "schema_version": 1,
            "surface": "medical_manuscript_blueprint",
            "argument_sequence": ["clinical_problem"],
        },
    )
    _write_json(
        study_root / "paper" / "medical_journal_style_corpus.json",
        {
            "schema_version": 1,
            "surface": "medical_journal_style_corpus",
            "corpus_id": "general_medical_journal_style_corpus_v1",
        },
    )
    _write_json(
        study_root / "artifacts" / "publication_eval" / "medical_prose_review_request.json",
        {
            "schema_version": 1,
            "surface": "medical_prose_review_request",
            "review_owner": "ai_reviewer",
        },
    )
    _write_json(
        study_root / "artifacts" / "publication_eval" / "medical_prose_review.json",
        {
            "schema_version": 1,
            "surface": "medical_prose_review",
            "assessment_provenance": {"owner": "ai_reviewer", "ai_reviewer_required": False},
            "medical_journal_prose_quality": {
                "overall_style_verdict": "clear",
                "summary": "AI reviewer cleared medical journal prose.",
            },
        },
    )
    _write_json(
        study_root / "artifacts" / "publication_eval" / "retrospective_medical_prose_audit.json",
        {
            "schema_version": 1,
            "surface": "retrospective_medical_prose_audit",
            "assessment_provenance": {"owner": "ai_reviewer", "ai_reviewer_required": False},
            "samples": [{"sample_id": "nf-pitnet-003"}, {"sample_id": "dpcc-003"}, {"sample_id": "dpcc-004"}],
        },
    )

    result = study_progress.read_study_progress(profile=profile, study_id="001-risk")

    surfaces = result["medical_writing_quality_surfaces"]
    assert surfaces["blueprint"]["present"] is True
    assert surfaces["style_corpus"]["corpus_id"] == "general_medical_journal_style_corpus_v1"
    assert surfaces["prose_review_request"]["review_owner"] == "ai_reviewer"
    assert surfaces["prose_review"]["owner"] == "ai_reviewer"
    assert surfaces["prose_review"]["verdict"] == "clear"
    assert surfaces["retrospective_audit"]["sample_ids"] == ["nf-pitnet-003", "dpcc-003", "dpcc-004"]
    assert result["refs"]["medical_manuscript_blueprint_path"].endswith("paper/medical_manuscript_blueprint.json")
    assert result["refs"]["medical_journal_style_corpus_path"].endswith("paper/medical_journal_style_corpus.json")
    assert result["refs"]["medical_prose_review_request_path"].endswith("medical_prose_review_request.json")
    assert result["refs"]["retrospective_medical_prose_audit_path"].endswith(
        "retrospective_medical_prose_audit.json"
    )
