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
        "src/med_autoscience/quality/publication_gate.py",
    ):
        source = _read(relative_path)
        assert "assessment_provenance" not in source
        assert "medical_publication_critique_v1" not in source
        assert "owner=\"ai_reviewer\"" not in source


def test_ai_reviewer_materializer_is_separate_from_generic_latest_writer() -> None:
    source = _read("src/med_autoscience/publication_eval_latest.py")

    assert "def materialize_ai_reviewer_publication_eval_latest" in source
    assert 'provenance["owner"] != "ai_reviewer"' in source
    assert 'DEFAULT_PUBLICATION_CRITIQUE_POLICY["policy_id"]' in source
