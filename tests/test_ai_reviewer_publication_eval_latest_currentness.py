from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from med_autoscience.publication_eval_latest import materialize_ai_reviewer_publication_eval_latest
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
