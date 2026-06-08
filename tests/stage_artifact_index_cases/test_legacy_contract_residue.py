from __future__ import annotations

from pathlib import Path

from med_autoscience.controllers.stage_artifact_index import build_stage_artifact_index
from med_autoscience.controllers.stage_artifact_materializer import (
    materialize_stage_artifact_delta,
)

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


def test_stage_artifact_index_keeps_publication_handoff_current_with_sidecar_residue(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / "workspace"
    study_root = workspace_root / "studies" / "001-risk"
    write_json(study_root / "study.yaml", {"study_id": "001-risk", "title": "Risk"})
    materialize_stage_artifact_delta(
        study_id="001-risk",
        study_root=study_root,
        workspace_root=workspace_root,
        apply=True,
    )
    refs = [
        (
            "artifacts/stage_outputs/08-publication_package_handoff/"
            "publication_package_manifest.json"
        ),
        (
            "artifacts/stage_outputs/08-publication_package_handoff/"
            "publication_gate_receipt.json"
        ),
        (
            "artifacts/stage_outputs/08-publication_package_handoff/"
            "handoff_owner_receipt.json"
        ),
    ]
    stage_root = (
        study_root / "artifacts" / "stage_outputs" / "08-publication_package_handoff"
    )
    write_json(
        stage_root / "current.json",
        {
            "surface_kind": "stage_artifact_current_pointer",
            "stage_id": "08-publication_package_handoff",
        },
    )
    write_json(
        stage_root / "projection" / "current_owner_delta.json",
        {
            "owner": "publication_gate_owner",
            "action": "publication_handoff_owner_gate",
            "reason": "legacy_materializer_projection",
        },
    )
    write_json(
        stage_root / "receipts" / "typed_blocker.json",
        {
            "surface_kind": "mas_stage_owner_receipt",
            "schema_version": 1,
            "stage_id": "08-publication_package_handoff",
            "owner": "MedAutoScience",
            "receipt_kind": "typed_blocker",
            "artifact_refs": refs,
        },
    )

    index = build_stage_artifact_index(study_id="001-risk", study_root=study_root)

    publication_handoff = index["stages"][-1]
    classification = publication_handoff["artifact_classification"]
    assert publication_handoff["artifact_status"] == "artifact_delta_present"
    assert publication_handoff["stage_progress_status"] == "artifact_delta_present"
    assert publication_handoff["next_missing_surface"] is None
    assert classification["status"] == "current"
    assert classification["current"] == sorted(refs)
    assert classification["orphan"] == []
    assert classification["legacy_orphan_residue"] == [
        "artifacts/stage_outputs/08-publication_package_handoff/current.json",
        (
            "artifacts/stage_outputs/08-publication_package_handoff/"
            "projection/current_owner_delta.json"
        ),
        (
            "artifacts/stage_outputs/08-publication_package_handoff/"
            "receipts/typed_blocker.json"
        ),
    ]
    assert index["next_owner_action"]["action_type"] == "publication_handoff_owner_gate"
