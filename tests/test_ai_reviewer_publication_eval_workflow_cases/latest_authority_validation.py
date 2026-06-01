from __future__ import annotations

from pathlib import Path

from tests.test_ai_reviewer_publication_eval_workflow import (
    _publication_eval_record,
    _reviewer_operating_system,
)


def test_ai_reviewer_publication_eval_latest_rejects_trace_without_currentness_checks(
    tmp_path: Path,
) -> None:
    from med_autoscience.publication_eval_latest import materialize_ai_reviewer_publication_eval_latest

    study_root = tmp_path / "study"
    record = _publication_eval_record(study_root)
    record.pop("future_facing_limitations_plan")
    trace = _reviewer_operating_system(study_root)
    trace.pop("currentness_checks", None)
    record["reviewer_operating_system"] = trace

    try:
        materialize_ai_reviewer_publication_eval_latest(study_root=study_root, record=record)
    except ValueError as exc:
        assert "currentness_checks" in str(exc)
    else:
        raise AssertionError("publication eval latest accepted AI reviewer trace without currentness checks")

    assert not (study_root / "artifacts" / "publication_eval" / "latest.json").exists()


def test_ai_reviewer_publication_eval_latest_rejects_ready_without_quality_readiness_kernel(
    tmp_path: Path,
) -> None:
    from med_autoscience.publication_eval_latest import materialize_ai_reviewer_publication_eval_latest

    study_root = tmp_path / "study"
    record = _publication_eval_record(study_root)
    record["reviewer_operating_system"] = _reviewer_operating_system(study_root)

    try:
        materialize_ai_reviewer_publication_eval_latest(study_root=study_root, record=record)
    except ValueError as exc:
        assert "publication_quality_readiness" in str(exc)
    else:
        raise AssertionError("publication eval latest accepted ready AI reviewer trace without quality readiness kernel")

    assert not (study_root / "artifacts" / "publication_eval" / "latest.json").exists()


def test_ai_reviewer_publication_eval_latest_rejects_requested_prose_currentness_without_clean_migration(
    tmp_path: Path,
) -> None:
    from med_autoscience.publication_eval_latest import materialize_ai_reviewer_publication_eval_latest

    study_root = tmp_path / "study"
    record = _publication_eval_record(study_root)
    trace = _reviewer_operating_system(study_root)
    trace["currentness_checks"]["medical_prose_review"] = {
        "status": "requested",
        "request_ref": str(study_root / "artifacts" / "publication_eval" / "medical_prose_review_request.json"),
        "request_digest": "sha256:" + "a" * 64,
        "manuscript_ref": str(study_root / "paper" / "manuscript.md"),
        "manuscript_digest": "sha256:" + "c" * 64,
        "route_back_required": True,
    }
    record["reviewer_operating_system"] = trace

    try:
        materialize_ai_reviewer_publication_eval_latest(study_root=study_root, record=record)
    except ValueError as exc:
        assert "paper_authority_clean_migration" in str(exc)
    else:
        raise AssertionError("publication eval latest accepted requested prose currentness without clean migration")

    assert not (study_root / "artifacts" / "publication_eval" / "latest.json").exists()
