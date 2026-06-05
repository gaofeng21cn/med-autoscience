from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from med_autoscience.controllers.ai_reviewer_publication_eval_records import (
    current_manuscript_binding,
    latest_current_ai_reviewer_publication_eval_record,
)
from med_autoscience.publication_eval_latest import materialize_ai_reviewer_publication_eval_latest
from tests.reviewer_os_fixture_helpers import current_manuscript_routeback_record
from tests.test_ai_reviewer_publication_eval_workflow import (
    _publication_eval_record,
    _reviewer_operating_system,
)


pytestmark = pytest.mark.meta


def _ready_claim_evidence_alignment() -> dict[str, Any]:
    return {
        "surface_kind": "claim_evidence_alignment_gate_v1",
        "source_project": "academic-research-skills",
        "absorbed_as": "mas_native_claim_evidence_alignment_gate",
        "status": "ready",
        "fail_closed_when_missing": True,
        "body_included": False,
        "may_authorize_publication_readiness": False,
        "may_authorize_quality_verdict": False,
        "can_write_domain_truth": False,
        "claim_count": 1,
        "aligned_claim_count": 1,
        "missing_required_fields": [],
        "blockers": [],
    }


def _ready_publication_quality_readiness() -> dict[str, Any]:
    return {
        "surface_kind": "publication_quality_authority_kernel_v1",
        "status": "ready",
        "current_manuscript_digest": "sha256:" + "c" * 64,
        "review_request_digest": "sha256:" + "a" * 64,
        "evidence_ledger_digest": "sha256:" + "d" * 64,
        "claim_evidence_alignment_digest": "sha256:" + "e" * 64,
        "rubric_version": "medical_publication_critique_v1",
        "owner_attempt_id": "ai-reviewer-publication-eval::001",
        "fail_closed_when_missing": True,
        "missing_required_fields": [],
    }


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_current_ai_reviewer_record_binds_stage_native_current_body_before_root_paper(
    tmp_path: Path,
) -> None:
    study_root = tmp_path / "study"
    root_manuscript = study_root / "paper" / "draft.md"
    stage_native_manuscript = (
        study_root
        / "artifacts"
        / "stage_outputs"
        / "_body_authority"
        / "paper_authority_cutover"
        / "current_body"
        / "paper"
        / "draft.md"
    )
    root_text = "# Draft\n\nOld root manuscript snapshot.\n"
    stage_native_text = "# Draft\n\nStage-native current body is the current manuscript.\n"
    root_manuscript.parent.mkdir(parents=True, exist_ok=True)
    root_manuscript.write_text(root_text, encoding="utf-8")
    stage_native_manuscript.parent.mkdir(parents=True, exist_ok=True)
    stage_native_manuscript.write_text(stage_native_text, encoding="utf-8")

    response_root = study_root / "artifacts" / "publication_eval" / "ai_reviewer_responses"
    stale_root_record = current_manuscript_routeback_record(
        study_root=study_root,
        manuscript_path=root_manuscript,
        manuscript_text=root_text,
        study_id="002-dm-china-us-mortality-attribution",
        quest_id="002-dm-china-us-mortality-attribution",
        eval_id="publication-eval::dm002::2026-06-01T00:00:00Z::stale-root",
        emitted_at="2026-06-01T00:00:00Z",
    )
    current_stage_record = current_manuscript_routeback_record(
        study_root=study_root,
        manuscript_path=stage_native_manuscript,
        manuscript_text=stage_native_text,
        study_id="002-dm-china-us-mortality-attribution",
        quest_id="002-dm-china-us-mortality-attribution",
        eval_id="publication-eval::dm002::2026-05-29T09:54:14Z::stage-current",
        emitted_at="2026-05-29T09:54:14Z",
    )
    _write_json(response_root / "20260601T000000Z_publication_eval_record.json", stale_root_record)
    _write_json(response_root / "20260529T095414Z_publication_eval_record.json", current_stage_record)

    manuscript = current_manuscript_binding(study_root=study_root)
    latest = latest_current_ai_reviewer_publication_eval_record(study_root=study_root)

    assert manuscript is not None
    assert manuscript["ref"] == str(stage_native_manuscript.resolve())
    assert latest is not None
    latest_record, latest_path = latest
    assert latest_path.name == "20260529T095414Z_publication_eval_record.json"
    assert latest_record["eval_id"] == "publication-eval::dm002::2026-05-29T09:54:14Z::stage-current"


def test_ai_reviewer_publication_eval_latest_rejects_trace_without_current_manuscript(
    tmp_path: Path,
) -> None:
    study_root = tmp_path / "study"
    record = _publication_eval_record(study_root)
    trace = _reviewer_operating_system(study_root)
    trace["currentness_checks"]["source_eval"] = {
        "status": "current",
        "eval_id": record["eval_id"],
    }
    trace["claim_evidence_alignment"] = _ready_claim_evidence_alignment()
    trace["publication_quality_readiness"] = _ready_publication_quality_readiness()
    record["reviewer_operating_system"] = trace

    try:
        materialize_ai_reviewer_publication_eval_latest(study_root=study_root, record=record)
    except ValueError as exc:
        assert "currentness_checks.current_manuscript must be non-empty" in str(exc)
    else:
        raise AssertionError("publication eval latest accepted AI reviewer trace without current manuscript currentness")

    assert not (study_root / "artifacts" / "publication_eval" / "latest.json").exists()
