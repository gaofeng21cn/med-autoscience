from __future__ import annotations

from pathlib import Path

from med_autoscience.controllers.stage_artifact_index import build_stage_artifact_index

from tests.stage_artifact_index_cases.shared import (
    STUDY_INTAKE_REFS,
    write_json,
    write_stage_native_contract,
)


def test_stage_artifact_index_keeps_canonical_stage_current_with_legacy_contract_residue(
    tmp_path: Path,
) -> None:
    study_root = tmp_path / "studies" / "001-risk"
    for ref in STUDY_INTAKE_REFS:
        write_json(study_root / ref, {"status": "ready"})
    write_stage_native_contract(
        study_root,
        stage_id="01-study_intake",
        refs=STUDY_INTAKE_REFS,
    )
    stage_root = study_root / "artifacts" / "stage_outputs" / "01-study_intake"
    write_json(stage_root / "stage_artifact_manifest.json", {"legacy": True})
    write_json(stage_root / "owner_receipt.json", {"legacy": True})

    index = build_stage_artifact_index(study_id="001-risk", study_root=study_root)

    study_intake = index["stages"][0]
    classification = study_intake["artifact_classification"]
    assert study_intake["artifact_status"] == "artifact_delta_present"
    assert study_intake["stage_progress_status"] == "artifact_delta_present"
    assert study_intake["observed_artifact_refs"]
    assert classification["status"] == "current"
    assert classification["current"] == sorted(STUDY_INTAKE_REFS)
    assert classification["fail_closed"] is False
    assert classification["legacy_orphan_residue"] == [
        "artifacts/stage_outputs/01-study_intake/owner_receipt.json",
        "artifacts/stage_outputs/01-study_intake/stage_artifact_manifest.json",
    ]
    assert classification["orphan"] == []
    assert study_intake["current_pointer"]["promotion_state"] == "current_pointer_promoted"
