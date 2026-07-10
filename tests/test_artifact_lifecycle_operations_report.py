from __future__ import annotations

import json
from pathlib import Path

from med_autoscience.controllers import artifact_lifecycle_operations_report
from med_autoscience.domain_entry_contract import SERVICE_SAFE_DOMAIN_COMMANDS


RECEIPT_REF_FAMILIES = (
    "artifact_lifecycle_receipt_refs",
    "artifact_authority_receipt_refs",
    "cleanup_receipt_refs",
    "restore_proof_refs",
    "retention_receipt_refs",
)


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _workspace_with_lifecycle_index(tmp_path: Path, *, ref_count: int) -> Path:
    workspace_root = tmp_path / "workspace"
    study_root = workspace_root / "studies" / "001-risk"
    _write_json(
        workspace_root / "workspace_index.json",
        {
            "surface_kind": "opl_workspace_index",
            "version": "workspace-index.v1",
            "projects": [
                {
                    "project_id": "001-risk",
                    "project_root": "studies/001-risk",
                }
            ],
        },
    )
    refs = {
        key: [f"{key}:{index}" for index in range(ref_count)]
        for key in RECEIPT_REF_FAMILIES
    }
    for key in RECEIPT_REF_FAMILIES:
        refs[key.removesuffix("_refs") + "_ref_count"] = ref_count + 5
    refs["artifact_manifest_ref"] = "artifacts/manifest.json"
    _write_json(
        study_root / artifact_lifecycle_operations_report.OPL_ARTIFACT_LIFECYCLE_INDEX,
        {
            "surface_kind": "opl_artifact_lifecycle_index",
            "status": "current",
            "refs": refs,
        },
    )
    return workspace_root


def test_lifecycle_report_bounds_receipt_ref_families(tmp_path: Path) -> None:
    workspace_root = _workspace_with_lifecycle_index(tmp_path, ref_count=60)

    report = artifact_lifecycle_operations_report.run_lifecycle_operations_report(
        workspace_roots=[workspace_root],
        deep=True,
        max_files=1,
        max_seconds=0.1,
    )

    project = report["workspaces"][0]["projects"][0]
    refs = project["refs"]
    for key in RECEIPT_REF_FAMILIES:
        count_key = key.removesuffix("_refs") + "_ref_count"
        assert refs[key] == [
            f"{key}:{index}"
            for index in range(artifact_lifecycle_operations_report.RECEIPT_REF_SAMPLE_LIMIT)
        ]
        assert refs[count_key] == 65
        assert refs[f"{key}_truncated"] is True
    assert refs["artifact_manifest_ref"] == "artifacts/manifest.json"
    assert report["requested_options"]["options_affect_inventory"] is False
    assert project["authority_boundary"]["mas_can_authorize_artifact_mutation_from_projection"] is False


def test_lifecycle_report_stays_refs_only_without_reentering_public_actions(
    tmp_path: Path,
) -> None:
    workspace_root = _workspace_with_lifecycle_index(tmp_path, ref_count=1)

    payload = artifact_lifecycle_operations_report.run_lifecycle_operations_report(
        workspace_roots=[workspace_root]
    )

    assert payload["surface"] == "artifact_lifecycle_report"
    assert payload["surface_kind"] == "mas_artifact_lifecycle_refs_report"
    assert payload["report_kind"] == "opl_lifecycle_index_domain_projection"
    assert payload["status"] == "available"
    assert payload["workspaces"][0]["projects"][0]["status"] == "available"
    assert payload["authority_boundary"] == {
        "opl_owner_surface_ref": "one-person-lab:src/modules/workspace/workspace-artifact-lifecycle.ts",
        "mas_projection_is_refs_only": True,
        "mas_scans_workspace_for_lifecycle": False,
        "mas_can_claim_artifact_ready": False,
        "mas_can_claim_package_ready": False,
        "mas_can_claim_publication_ready": False,
    }
    assert "artifact-lifecycle-report" not in SERVICE_SAFE_DOMAIN_COMMANDS
