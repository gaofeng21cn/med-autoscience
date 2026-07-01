from __future__ import annotations

import importlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from tests.test_publication_eval_latest_cases.shared import (
    MODULE_NAME,
    _minimal_payload,
    _quality_assessment,
    _reviewer_operating_system,
    _write_cutover_receipt,
    _write_json,
)

def test_ai_reviewer_publication_eval_materializer_rejects_gate_projection_payload(tmp_path: Path) -> None:
    module = importlib.import_module(MODULE_NAME)
    study_root = tmp_path / "workspace" / "studies" / "001-risk"
    payload = _minimal_payload(study_root)
    payload["assessment_provenance"] = {
        "owner": "mechanical_projection",
        "source_kind": "publication_gate_report",
        "policy_id": "publication_gate_projection_v1",
        "source_refs": [payload["runtime_context_refs"]["runtime_escalation_ref"]],
        "ai_reviewer_required": True,
    }

    with pytest.raises(ValueError, match="owner=ai_reviewer"):
        module.materialize_ai_reviewer_publication_eval_latest(study_root=study_root, record=payload)
def test_ai_reviewer_publication_eval_materializer_rejects_gate_source_kind(tmp_path: Path) -> None:
    module = importlib.import_module(MODULE_NAME)
    study_root = tmp_path / "workspace" / "studies" / "001-risk"
    payload = _minimal_payload(study_root)
    payload["quality_assessment"] = _quality_assessment(study_root)
    payload["reviewer_operating_system"] = _reviewer_operating_system(study_root)
    payload["assessment_provenance"]["source_kind"] = "publication_gate_report"

    with pytest.raises(ValueError, match="source_kind=publication_eval_ai_reviewer"):
        module.materialize_ai_reviewer_publication_eval_latest(study_root=study_root, record=payload)
def test_ai_reviewer_publication_eval_materializer_writes_review_backed_latest(tmp_path: Path) -> None:
    module = importlib.import_module(MODULE_NAME)
    study_root = tmp_path / "workspace" / "studies" / "001-risk"
    payload = _minimal_payload(study_root)
    payload["quality_assessment"] = _quality_assessment(study_root)
    payload["reviewer_operating_system"] = _reviewer_operating_system(study_root)

    result = module.materialize_ai_reviewer_publication_eval_latest(study_root=study_root, record=payload)

    assert result["eval_id"] == payload["eval_id"]
    resolved = module.read_publication_eval_latest(study_root=study_root)
    assert resolved["assessment_provenance"]["owner"] == "ai_reviewer"
    assert resolved["assessment_provenance"]["source_kind"] == "publication_eval_ai_reviewer"
    assert resolved["assessment_provenance"]["policy_id"] == "medical_publication_critique_v1"
    assert resolved["reviewer_operating_system"]["contract_id"] == "medical_publication_ai_reviewer_os_v1"
    assert resolved["quality_assessment"]["medical_journal_prose_quality"]["reviewer_revision_advice"] == (
        "Rewrite representative figure-led sentences as finding-led sentences."
    )
def test_ai_reviewer_publication_eval_materializer_promotes_current_manuscript_record(
    tmp_path: Path,
) -> None:
    module = importlib.import_module(MODULE_NAME)
    study_root = tmp_path / "workspace" / "studies" / "001-risk"
    payload = _minimal_payload(study_root)
    payload["quality_assessment"] = _quality_assessment(study_root)
    payload["reviewer_operating_system"] = _reviewer_operating_system(study_root)
    payload["assessment_provenance"]["source_kind"] = "publication_eval_ai_reviewer_current_manuscript_record"

    result = module.materialize_ai_reviewer_publication_eval_latest(study_root=study_root, record=payload)

    assert result["eval_id"] == payload["eval_id"]
    resolved = module.read_publication_eval_latest(study_root=study_root)
    assert resolved["assessment_provenance"]["owner"] == "ai_reviewer"
    assert resolved["assessment_provenance"]["source_kind"] == "publication_eval_ai_reviewer"
def test_ai_reviewer_publication_eval_materializer_rejects_missing_reviewer_os_trace(
    tmp_path: Path,
) -> None:
    module = importlib.import_module(MODULE_NAME)
    study_root = tmp_path / "workspace" / "studies" / "001-risk"
    payload = _minimal_payload(study_root)
    payload["quality_assessment"] = _quality_assessment(study_root)

    with pytest.raises(ValueError, match="reviewer_operating_system"):
        module.materialize_ai_reviewer_publication_eval_latest(study_root=study_root, record=payload)
def test_ai_reviewer_publication_eval_materializer_rejects_missing_prose_quality_dimension(
    tmp_path: Path,
) -> None:
    module = importlib.import_module(MODULE_NAME)
    study_root = tmp_path / "workspace" / "studies" / "001-risk"
    payload = _minimal_payload(study_root)
    payload["quality_assessment"] = _quality_assessment(study_root)
    payload["reviewer_operating_system"] = _reviewer_operating_system(study_root)
    payload["quality_assessment"].pop("medical_journal_prose_quality")

    with pytest.raises(ValueError, match="quality_assessment.medical_journal_prose_quality"):
        module.materialize_ai_reviewer_publication_eval_latest(study_root=study_root, record=payload)
