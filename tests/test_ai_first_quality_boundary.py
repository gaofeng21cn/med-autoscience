from __future__ import annotations

from pathlib import Path

import pytest


pytestmark = pytest.mark.meta

REPO_ROOT = Path(__file__).resolve().parents[1]


def _read(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


def test_gate_materialized_publication_eval_is_marked_as_mechanical_projection() -> None:
    source = _read("src/med_autoscience/controllers/study_runtime_decision_parts/publication_and_submission.py")

    assert 'owner="mechanical_projection"' in source
    assert 'source_kind="publication_gate_report"' in source
    assert 'policy_id="publication_gate_projection_v1"' in source
    assert "ai_reviewer_required=True" in source


def test_quality_surfaces_require_ai_reviewer_provenance_before_ready_verdicts() -> None:
    study_quality = _read("src/med_autoscience/quality/study_quality.py")
    closure_truth = _read("src/med_autoscience/evaluation_summary_parts/quality_closure_truth.py")
    revision_plan = _read("src/med_autoscience/evaluation_summary_parts/quality_revision_plan.py")

    assert 'provenance["owner"] == "ai_reviewer"' in study_quality
    assert 'not bool(provenance["ai_reviewer_required"])' in study_quality
    assert '"source": "publication_eval_projection"' in study_quality
    assert '"status": "review_required"' in study_quality
    assert "if not publication_eval_ai_reviewer_backed(publication_eval):" in closure_truth
    assert "if not publication_eval_ai_reviewer_backed(publication_eval):" in revision_plan
    assert "AI reviewer 读取 manuscript" in revision_plan


def test_mechanical_gate_controllers_do_not_claim_ai_reviewer_ownership() -> None:
    for relative_path in (
        "src/med_autoscience/controllers/medical_reporting_audit.py",
        "src/med_autoscience/controllers/publication_gate.py",
    ):
        source = _read(relative_path)
        assert "assessment_provenance" not in source
        assert "medical_publication_critique_v1" not in source
        assert "owner=\"ai_reviewer\"" not in source

    reducer = _read("src/med_autoscience/quality/publication_gate.py")
    assert "assessment_provenance" in reducer
    assert "_ai_reviewer_backed" in reducer
    assert '"owner": "ai_reviewer"' not in reducer
    assert 'owner="ai_reviewer"' not in reducer
    assert "medical_publication_critique_v1" not in reducer


def test_ai_reviewer_materializer_is_separate_from_generic_latest_writer() -> None:
    source = _read("src/med_autoscience/publication_eval_latest.py")

    assert "def materialize_ai_reviewer_publication_eval_latest" in source
    assert 'provenance["owner"] != "ai_reviewer"' in source
    assert 'DEFAULT_PUBLICATION_CRITIQUE_POLICY["policy_id"]' in source


def test_subjective_medical_prose_quality_is_ai_reviewer_owned() -> None:
    policy = _read("docs/policies/ai_first_quality_boundary.md")
    architecture = _read("docs/architecture.md")
    publication_surface = _read(
        "src/med_autoscience/controllers/medical_publication_surface_parts/reporting.py"
    )

    assert "医学论文文体" in policy
    assert "medical_prose_review" in policy
    assert "Regex / pattern / deterministic scanner" in policy
    assert "不得单独触发或清除 `medical_journal_prose_style_not_met`" in policy
    assert "regex / pattern 只作为 `mechanical_safety_flags`" in architecture
    assert 'blockers.append("medical_journal_prose_style_not_met")' in publication_surface
    assert 'medical_journal_prose_ai_verdict in {"block", "revise"}' in publication_surface
    assert 'blockers.append("figure_table_led_results_narration_present")' not in publication_surface
    assert 'blockers.append("non_formal_question_sentence_present")' not in publication_surface


def test_ai_first_prose_request_and_retrospective_audit_are_reviewer_owned() -> None:
    request_source = _read("src/med_autoscience/medical_prose_review_request.py")
    retrospective_source = _read("src/med_autoscience/retrospective_medical_prose_audit.py")
    corpus_source = _read("src/med_autoscience/medical_journal_style_corpus.py")

    assert '"review_owner": "ai_reviewer"' in request_source
    assert '"mechanical_flags_role": "evidence_snippets_only"' in request_source
    assert "validate_ai_medical_prose_review_response" in request_source
    assert "materialize_ai_medical_prose_review_from_response" in request_source
    assert '"audit_owner": "ai_reviewer"' in retrospective_source
    assert '"manual_study_patch_allowed": False' in retrospective_source
    assert "nf-pitnet-003" in retrospective_source
    assert "dpcc-003" in retrospective_source
    assert "dpcc-004" in retrospective_source
    assert "long_excerpts_allowed" in corpus_source
    assert "Use the corpus to learn voice, rhythm, and reviewer questions" in corpus_source
