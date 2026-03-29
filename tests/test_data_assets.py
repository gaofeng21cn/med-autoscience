from __future__ import annotations

import importlib
import json
from pathlib import Path


def write_dataset_manifest(path: Path, *, dataset_id: str, relative_path: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "dataset_inputs:",
                f"  - dataset_id: {dataset_id}",
                f"    path: {relative_path}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def test_init_data_assets_creates_private_public_and_impact_layout(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.data_assets")
    workspace_root = tmp_path / "workspace"
    (workspace_root / "datasets" / "master" / "v2026-03-28").mkdir(parents=True, exist_ok=True)
    (workspace_root / "datasets" / "master" / "v2026-03-28" / "nfpitnet_analysis_deidentified.csv").write_text(
        "id\n1\n",
        encoding="utf-8",
    )

    result = module.init_data_assets(workspace_root=workspace_root)

    assert result["private"]["release_count"] == 1
    assert result["public"]["dataset_count"] == 0
    assert result["impact"]["report_exists"] is False

    private_registry = json.loads(
        (workspace_root / "portfolio" / "data_assets" / "private" / "registry.json").read_text(encoding="utf-8")
    )
    assert private_registry["schema_version"] == 1
    assert private_registry["releases"][0]["family_id"] == "master"
    assert private_registry["releases"][0]["version_id"] == "v2026-03-28"

    public_registry = json.loads(
        (workspace_root / "portfolio" / "data_assets" / "public" / "registry.json").read_text(encoding="utf-8")
    )
    assert public_registry == {"schema_version": 1, "datasets": []}


def test_assess_data_asset_impact_marks_studies_with_newer_private_release_and_public_support(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.data_assets")
    workspace_root = tmp_path / "workspace"
    (workspace_root / "datasets" / "master" / "v2026-03-28").mkdir(parents=True, exist_ok=True)
    (workspace_root / "datasets" / "master" / "v2026-04-10").mkdir(parents=True, exist_ok=True)
    write_dataset_manifest(
        workspace_root / "studies" / "002-early-risk" / "data_input" / "dataset_manifest.yaml",
        dataset_id="nfpitnet_master",
        relative_path="../../../datasets/master/v2026-03-28/nfpitnet_analysis_deidentified.csv",
    )
    module.init_data_assets(workspace_root=workspace_root)

    public_registry_path = workspace_root / "portfolio" / "data_assets" / "public" / "registry.json"
    public_registry_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "datasets": [
                    {
                        "dataset_id": "geo-gse000001",
                        "source_type": "GEO",
                        "accession": "GSE000001",
                        "roles": ["external_validation"],
                        "target_families": ["master"],
                        "target_dataset_ids": ["nfpitnet_master"],
                        "status": "candidate",
                        "rationale": "Can be used for external validation.",
                    }
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    result = module.assess_data_asset_impact(workspace_root=workspace_root)

    assert result["study_count"] == 1
    study = result["studies"][0]
    assert study["study_id"] == "002-early-risk"
    assert study["status"] == "review_needed"
    dataset = study["dataset_inputs"][0]
    assert dataset["private_version_status"] == "older_than_latest"
    assert dataset["latest_private_version"] == "v2026-04-10"
    assert dataset["public_support_count"] == 1

    report_path = workspace_root / "portfolio" / "data_assets" / "impact" / "latest_impact_report.json"
    assert report_path.exists()

