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


def write_private_release_manifest(
    path: Path,
    *,
    dataset_id: str,
    version: str,
    raw_snapshot: str,
    generated_by: str,
    main_outputs: dict[str, str],
    notes: list[str] | None = None,
    release_contract: dict[str, object] | None = None,
) -> None:
    payload: dict[str, object] = {
        "dataset_id": dataset_id,
        "version": version,
        "raw_snapshot": raw_snapshot,
        "generated_by": generated_by,
        "main_outputs": main_outputs,
        "notes": notes or [],
    }
    if release_contract is not None:
        payload["release_contract"] = release_contract
    import yaml

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")


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
    assert private_registry["schema_version"] == 2
    assert private_registry["releases"][0]["family_id"] == "master"
    assert private_registry["releases"][0]["version_id"] == "v2026-03-28"
    assert private_registry["releases"][0]["inventory_summary"]["file_count"] == 1

    public_registry = json.loads(
        (workspace_root / "portfolio" / "data_assets" / "public" / "registry.json").read_text(encoding="utf-8")
    )
    assert public_registry == {
        "schema_version": 2,
        "discovery": {
            "status": "not_started",
            "last_scouted_on": None,
            "scope": "route_selection",
            "notes": [],
        },
        "datasets": [],
    }


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


def test_assess_data_asset_impact_ignores_rejected_public_datasets(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.data_assets")
    workspace_root = tmp_path / "workspace"
    version_root = workspace_root / "datasets" / "master" / "v2026-03-28"
    version_root.mkdir(parents=True, exist_ok=True)
    (version_root / "analysis.csv").write_text("id\n1\n", encoding="utf-8")
    write_private_release_manifest(
        version_root / "dataset_manifest.yaml",
        dataset_id="nfpitnet_master",
        version="v2026-03-28",
        raw_snapshot="baseline",
        generated_by="pipeline/v1.py",
        main_outputs={"analysis_csv": "analysis.csv"},
    )
    write_dataset_manifest(
        workspace_root / "studies" / "002-early-risk" / "data_input" / "dataset_manifest.yaml",
        dataset_id="nfpitnet_master",
        relative_path="../../../datasets/master/v2026-03-28/analysis.csv",
    )
    module.init_data_assets(workspace_root=workspace_root)

    public_registry_path = workspace_root / "portfolio" / "data_assets" / "public" / "registry.json"
    public_registry_path.write_text(
        json.dumps(
            {
                "schema_version": 2,
                "discovery": {
                    "status": "completed",
                    "last_scouted_on": "2026-04-08",
                    "scope": "route_selection",
                    "notes": ["screened and rejected"],
                },
                "datasets": [
                    {
                        "dataset_id": "geo-gse000009",
                        "source_type": "GEO",
                        "accession": "GSE000009",
                        "roles": ["external_validation"],
                        "target_families": ["master"],
                        "target_dataset_ids": ["nfpitnet_master"],
                        "status": "rejected",
                        "rationale": "Rejected after screening.",
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
    assert study["status"] == "clear"
    dataset = study["dataset_inputs"][0]
    assert dataset["public_support_count"] == 0
    assert dataset["public_support_dataset_ids"] == []


def test_validate_public_registry_normalizes_discovery_metadata_defaults(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.data_assets")
    workspace_root = tmp_path / "workspace"
    registry_path = workspace_root / "portfolio" / "data_assets" / "public" / "registry.json"
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    registry_path.write_text(
        json.dumps({"schema_version": 2, "datasets": []}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    result = module.validate_public_registry(workspace_root=workspace_root)
    registry = json.loads(registry_path.read_text(encoding="utf-8"))

    assert result["schema_version"] == 2
    assert registry["discovery"]["status"] == "not_started"
    assert registry["discovery"]["scope"] == "route_selection"
    assert registry["datasets"] == []


def test_assess_data_asset_impact_supports_locked_inputs_manifest_shape(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.data_assets")
    workspace_root = tmp_path / "workspace"
    (workspace_root / "datasets" / "master" / "v2026-03-28").mkdir(parents=True, exist_ok=True)
    manifest_path = workspace_root / "studies" / "001-lineage-pfs" / "data_input" / "dataset_manifest.yaml"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        "\n".join(
            [
                "study_id: 001-lineage-pfs",
                "locked_inputs:",
                "  - dataset_id: nfpitnet_master",
                "    version: v2026-03-28",
                "    path: ../../../datasets/master/v2026-03-28/nfpitnet_analysis_deidentified.csv",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    result = module.assess_data_asset_impact(workspace_root=workspace_root)

    assert result["study_count"] == 1
    assert result["studies"][0]["dataset_inputs"][0]["dataset_id"] == "nfpitnet_master"
    assert result["studies"][0]["dataset_inputs"][0]["private_version_status"] == "up_to_date"


def test_assess_data_asset_impact_marks_directory_scan_release_as_unresolved_contract(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.data_assets")
    workspace_root = tmp_path / "workspace"
    version_root = workspace_root / "datasets" / "master" / "v2026-03-28"
    version_root.mkdir(parents=True, exist_ok=True)
    (version_root / "analysis.csv").write_text("id\n1\n", encoding="utf-8")
    write_dataset_manifest(
        workspace_root / "studies" / "002-early-risk" / "data_input" / "dataset_manifest.yaml",
        dataset_id="nfpitnet_master",
        relative_path="../../../datasets/master/v2026-03-28/analysis.csv",
    )

    result = module.assess_data_asset_impact(workspace_root=workspace_root)

    assert result["study_count"] == 1
    study = result["studies"][0]
    assert study["status"] == "review_needed"
    dataset = study["dataset_inputs"][0]
    assert dataset["private_version_status"] == "up_to_date"
    assert dataset["private_contract_status"] == "directory_scan_only"


def test_init_data_assets_extracts_manifest_backed_private_release_contract(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.data_assets")
    workspace_root = tmp_path / "workspace"
    version_root = workspace_root / "datasets" / "master" / "v2026-03-28"
    version_root.mkdir(parents=True, exist_ok=True)
    write_private_release_manifest(
        version_root / "dataset_manifest.yaml",
        dataset_id="nfpitnet_master",
        version="v2026-03-28",
        raw_snapshot="2026-03-28_baseline",
        generated_by="pipeline/src/clean_nfpitnet_dataset.py",
        main_outputs={"analysis_csv": "nfpitnet_analysis.csv"},
        notes=["baseline freeze"],
        release_contract={
            "update_type": ["baseline_refresh"],
            "qc_status": "locked",
            "change_summary": "Baseline analysis release.",
        },
    )
    (version_root / "nfpitnet_analysis.csv").write_text("id\n1\n", encoding="utf-8")

    module.init_data_assets(workspace_root=workspace_root)

    private_registry = json.loads(
        (workspace_root / "portfolio" / "data_assets" / "private" / "registry.json").read_text(encoding="utf-8")
    )
    release = private_registry["releases"][0]
    assert release["contract_status"] == "manifest_backed"
    assert release["dataset_id"] == "nfpitnet_master"
    assert release["raw_snapshot"] == "2026-03-28_baseline"
    assert release["generated_by"] == "pipeline/src/clean_nfpitnet_dataset.py"
    assert release["main_outputs"] == {"analysis_csv": "nfpitnet_analysis.csv"}
    assert release["declared_release_contract"]["qc_status"] == "locked"
    assert release["inventory_summary"]["file_count"] == 2
    assert release["inventory_summary"]["declared_outputs_present"] == {"analysis_csv": True}


def test_build_private_release_diff_writes_delta_report(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.data_assets")
    workspace_root = tmp_path / "workspace"
    from_root = workspace_root / "datasets" / "master" / "v2026-03-28"
    to_root = workspace_root / "datasets" / "master" / "v2026-04-10"
    from_root.mkdir(parents=True, exist_ok=True)
    to_root.mkdir(parents=True, exist_ok=True)

    write_private_release_manifest(
        from_root / "dataset_manifest.yaml",
        dataset_id="nfpitnet_master",
        version="v2026-03-28",
        raw_snapshot="baseline",
        generated_by="pipeline/v1.py",
        main_outputs={"analysis_csv": "analysis.csv"},
        notes=["baseline"],
    )
    write_private_release_manifest(
        to_root / "dataset_manifest.yaml",
        dataset_id="nfpitnet_master",
        version="v2026-04-10",
        raw_snapshot="followup_refresh",
        generated_by="pipeline/v2.py",
        main_outputs={"analysis_csv": "analysis_followup.csv"},
        notes=["follow-up refreshed"],
        release_contract={"update_type": ["followup_refresh"]},
    )
    (from_root / "analysis.csv").write_text("id\n1\n", encoding="utf-8")
    (to_root / "analysis_followup.csv").write_text("id\n1\n2\n", encoding="utf-8")
    (to_root / "new_dictionary.csv").write_text("name\nvalue\n", encoding="utf-8")
    write_dataset_manifest(
        workspace_root / "studies" / "003-followup-risk" / "study.yaml",
        dataset_id="nfpitnet_master",
        relative_path="../../datasets/master/v2026-03-28/analysis.csv",
    )

    result = module.build_private_release_diff(
        workspace_root=workspace_root,
        family_id="master",
        from_version="v2026-03-28",
        to_version="v2026-04-10",
    )

    assert result["family_id"] == "master"
    assert result["from_version"] == "v2026-03-28"
    assert result["to_version"] == "v2026-04-10"
    assert Path(result["report_path"]).exists()
    assert result["summary"]["inventory"]["added_files"] == ["analysis_followup.csv", "new_dictionary.csv"]
    assert result["summary"]["inventory"]["removed_files"] == ["analysis.csv"]
    assert result["summary"]["contract"]["changed_fields"][0]["field"] == "generated_by"
    assert result["summary"]["main_outputs"]["changed_outputs"][0]["output_name"] == "analysis_csv"
    assert result["summary"]["study_impact"]["affected_studies"] == ["003-followup-risk"]
    assert result["summary"]["study_impact"]["affected_dataset_ids"] == ["nfpitnet_master"]


def test_assess_data_asset_impact_links_private_diff_report_for_outdated_release(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.data_assets")
    workspace_root = tmp_path / "workspace"
    from_root = workspace_root / "datasets" / "master" / "v2026-03-28"
    to_root = workspace_root / "datasets" / "master" / "v2026-04-10"
    from_root.mkdir(parents=True, exist_ok=True)
    to_root.mkdir(parents=True, exist_ok=True)
    write_private_release_manifest(
        from_root / "dataset_manifest.yaml",
        dataset_id="nfpitnet_master",
        version="v2026-03-28",
        raw_snapshot="baseline",
        generated_by="pipeline/v1.py",
        main_outputs={"analysis_csv": "analysis.csv"},
    )
    write_private_release_manifest(
        to_root / "dataset_manifest.yaml",
        dataset_id="nfpitnet_master",
        version="v2026-04-10",
        raw_snapshot="followup",
        generated_by="pipeline/v2.py",
        main_outputs={"analysis_csv": "analysis.csv"},
    )
    (from_root / "analysis.csv").write_text("id\n1\n", encoding="utf-8")
    (to_root / "analysis.csv").write_text("id\n1\n2\n", encoding="utf-8")
    write_dataset_manifest(
        workspace_root / "studies" / "002-early-risk" / "data_input" / "dataset_manifest.yaml",
        dataset_id="nfpitnet_master",
        relative_path="../../../datasets/master/v2026-03-28/analysis.csv",
    )

    result = module.assess_data_asset_impact(workspace_root=workspace_root)

    dataset = result["studies"][0]["dataset_inputs"][0]
    assert dataset["private_version_status"] == "older_than_latest"
    assert dataset["upgrade_diff_report_exists"] is True
    assert dataset["upgrade_diff_report_path"].endswith("master/v2026-03-28__v2026-04-10.json")


def test_init_data_assets_upgrades_public_registry_to_schema_v2(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.data_assets")
    workspace_root = tmp_path / "workspace"
    public_registry_path = workspace_root / "portfolio" / "data_assets" / "public" / "registry.json"
    public_registry_path.parent.mkdir(parents=True, exist_ok=True)
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

    module.init_data_assets(workspace_root=workspace_root)

    public_registry = json.loads(public_registry_path.read_text(encoding="utf-8"))
    assert public_registry["schema_version"] == 2
    dataset = public_registry["datasets"][0]
    assert dataset["roles"] == ["external_validation"]
    assert dataset["target_study_archetypes"] == []
    assert dataset["modality"] == []
    assert dataset["validation"]["is_valid"] is True


def test_validate_public_registry_reports_invalid_entries(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.data_assets")
    workspace_root = tmp_path / "workspace"
    public_registry_path = workspace_root / "portfolio" / "data_assets" / "public" / "registry.json"
    public_registry_path.parent.mkdir(parents=True, exist_ok=True)
    public_registry_path.write_text(
        json.dumps(
            {
                "schema_version": 2,
                "datasets": [
                    {
                        "dataset_id": "bad-public-dataset",
                        "source_type": "GEO",
                        "roles": [],
                        "target_families": [],
                        "target_dataset_ids": [],
                        "target_study_archetypes": [],
                        "status": "candidate",
                    }
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    result = module.validate_public_registry(workspace_root=workspace_root)

    assert result["schema_version"] == 2
    assert result["dataset_count"] == 1
    assert result["invalid_dataset_count"] == 1
    assert result["datasets"][0]["validation"]["is_valid"] is False
    assert "missing_roles" in result["datasets"][0]["validation"]["errors"]
    assert "missing_target_scope" in result["datasets"][0]["validation"]["errors"]
