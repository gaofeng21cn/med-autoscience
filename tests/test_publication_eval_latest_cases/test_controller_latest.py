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

def test_ai_reviewer_publication_eval_controller_materializes_runtime_checked_latest(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    controller = importlib.import_module("med_autoscience.controllers.ai_reviewer_publication_eval")
    study_root = tmp_path / "workspace" / "studies" / "001-risk"
    payload = _minimal_payload(study_root)
    payload["quality_assessment"] = _quality_assessment(study_root)
    payload["reviewer_operating_system"] = _reviewer_operating_system(study_root)
    called: dict[str, object] = {}

    def fake_status(*, profile, study_id: str | None, study_root: Path | None, entry_mode: str | None) -> dict:
        called["profile"] = profile
        called["study_id"] = study_id
        called["study_root"] = study_root
        called["entry_mode"] = entry_mode
        return {
            "study_id": "001-risk",
            "study_root": str(study_root),
            "quest_id": "quest-001",
        }

    monkeypatch.setattr(controller.domain_status_projection, "progress_projection", fake_status)

    result = controller.materialize_ai_reviewer_publication_eval(
        profile=SimpleNamespace(name="nfpitnet"),
        study_id=None,
        study_root=study_root,
        entry_mode=None,
        record=payload,
        source="pytest",
    )

    assert called["study_root"] == study_root
    assert result["status"] == "materialized"
    assert result["study_id"] == "001-risk"
    assert result["quest_id"] == "quest-001"
    assert result["assessment_owner"] == "ai_reviewer"
    latest = importlib.import_module(MODULE_NAME).read_publication_eval_latest(study_root=study_root)
    assert latest["eval_id"] == payload["eval_id"]
    record_ref = Path(result["publication_eval_record_ref"])
    assert record_ref.name == "20260405T060000Z_publication_eval_record.json"
    assert record_ref.parent == (study_root / "artifacts" / "publication_eval" / "ai_reviewer_responses").resolve()
    archived = json.loads(record_ref.read_text(encoding="utf-8"))
    assert archived == latest
def test_ai_reviewer_publication_eval_controller_promotes_current_manuscript_record(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    controller = importlib.import_module("med_autoscience.controllers.ai_reviewer_publication_eval")
    study_root = tmp_path / "workspace" / "studies" / "001-risk"
    payload = _minimal_payload(study_root)
    payload["quality_assessment"] = _quality_assessment(study_root)
    payload["reviewer_operating_system"] = _reviewer_operating_system(study_root)
    payload["assessment_provenance"]["source_kind"] = "publication_eval_ai_reviewer_current_manuscript_record"

    monkeypatch.setattr(
        controller.domain_status_projection,
        "progress_projection",
        lambda **_: {
            "study_id": "001-risk",
            "study_root": str(study_root),
            "quest_id": "quest-001",
        },
    )

    result = controller.materialize_ai_reviewer_publication_eval(
        profile=SimpleNamespace(name="nfpitnet"),
        study_id="001-risk",
        study_root=None,
        entry_mode=None,
        record=payload,
        source="pytest",
    )

    assert result["status"] == "materialized"
    latest = importlib.import_module(MODULE_NAME).read_publication_eval_latest(study_root=study_root)
    assert latest["eval_id"] == payload["eval_id"]
    assert latest["assessment_provenance"]["source_kind"] == "publication_eval_ai_reviewer"
    record_ref = Path(result["publication_eval_record_ref"])
    archived = json.loads(record_ref.read_text(encoding="utf-8"))
    assert archived == latest
def test_ai_reviewer_publication_eval_controller_closes_clean_migration_cutover(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    controller = importlib.import_module("med_autoscience.controllers.ai_reviewer_publication_eval")
    migration = importlib.import_module("med_autoscience.controllers.paper_authority_migration")
    study_root = tmp_path / "workspace" / "studies" / "001-risk"
    payload = _minimal_payload(study_root)
    payload["quality_assessment"] = _quality_assessment(study_root)
    payload["reviewer_operating_system"] = _reviewer_operating_system(study_root)
    cutover_path = _write_cutover_receipt(study_root)

    monkeypatch.setattr(
        controller.domain_status_projection,
        "progress_projection",
        lambda **_: {
            "study_id": "001-risk",
            "study_root": str(study_root),
            "quest_id": "quest-001",
        },
    )

    result = controller.materialize_ai_reviewer_publication_eval(
        profile=SimpleNamespace(name="nfpitnet"),
        study_id="001-risk",
        study_root=None,
        entry_mode=None,
        record=payload,
        source="pytest",
    )

    receipt = json.loads(cutover_path.read_text(encoding="utf-8"))
    assert result["publication_eval_surface"] == "artifacts/publication_eval/latest.json"
    assert result["paper_authority_cutover_status"] == "new_mas_authority_established"
    assert result["paper_authority_cutover_ref"] == str(cutover_path)
    assert receipt["status"] == "new_mas_authority_established"
    assert receipt["new_mas_authority"] == {
        "owner": "ai_reviewer",
        "publication_eval_ref": result["artifact_path"],
        "eval_id": payload["eval_id"],
        "established_at": receipt["new_mas_authority"]["established_at"],
    }
    assert receipt["authority_boundary"]["quality_verdict_written"] is True
    assert receipt["authority_boundary"]["submission_package_regenerated"] is False
    assert receipt["required_next_actions"] == ["publication_gate", "sync_study_delivery"]
    assert migration.new_mas_authority_eval_current(study_root=study_root) is True
