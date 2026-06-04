from __future__ import annotations

import json
from pathlib import Path


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_medical_writing_surfaces_use_stage_native_blueprint_after_cutover(tmp_path: Path) -> None:
    from med_autoscience.controllers.study_progress_parts.medical_writing_surfaces import (
        medical_writing_quality_surface_status,
    )

    study_root = tmp_path / "study"
    stage_native_blueprint_path = (
        study_root
        / "artifacts"
        / "stage_outputs"
        / "_body_authority"
        / "paper_authority_cutover"
        / "current_body"
        / "paper"
        / "medical_manuscript_blueprint.json"
    )
    _write_json(
        stage_native_blueprint_path,
        {
            "schema_version": 1,
            "surface": "medical_manuscript_blueprint",
            "argument_sequence": ["clinical_problem"],
        },
    )

    result = medical_writing_quality_surface_status(study_root=study_root)

    assert result["blueprint"]["present"] is True
    assert result["blueprint"]["valid"] is True
    assert result["blueprint"]["path"] == str(stage_native_blueprint_path.resolve())
    assert not (study_root / "paper" / "medical_manuscript_blueprint.json").exists()
