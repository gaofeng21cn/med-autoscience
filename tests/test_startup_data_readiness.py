from __future__ import annotations

import importlib
import json
from pathlib import Path

import yaml


def write_study_manifest(
    path: Path,
    *,
    dataset_id: str,
    relative_path: str | None = None,
    version: str | None = None,
) -> None:
    payload: dict[str, object] = {
        "dataset_inputs": [
            {
                "dataset_id": dataset_id,
            }
        ]
    }
    if relative_path is not None:
        payload["dataset_inputs"][0]["path"] = relative_path
    if version is not None:
        payload["dataset_inputs"][0]["version"] = version
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")


def write_private_release_manifest(
    path: Path,
    *,
    dataset_id: str,
    version: str,
    raw_snapshot: str,
    generated_by: str,
    main_outputs: dict[str, str],
) -> None:
    payload = {
        "dataset_id": dataset_id,
        "version": version,
        "raw_snapshot": raw_snapshot,
        "generated_by": generated_by,
        "main_outputs": main_outputs,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")


def test_startup_data_readiness_summarizes_private_and_public_opportunities(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.startup_data_readiness")
    workspace_root = tmp_path / "workspace"
    release_v1 = workspace_root / "datasets" / "master" / "v2026-03-28"
    release_v2 = workspace_root / "datasets" / "master" / "v2026-04-10"
    release_v1.mkdir(parents=True, exist_ok=True)
    release_v2.mkdir(parents=True, exist_ok=True)
    write_private_release_manifest(
        release_v1 / "dataset_manifest.yaml",
        dataset_id="nfpitnet_master",
        version="v2026-03-28",
        raw_snapshot="baseline",
        generated_by="pipeline/v1.py",
        main_outputs={"analysis_csv": "analysis.csv"},
    )
    write_private_release_manifest(
        release_v2 / "dataset_manifest.yaml",
        dataset_id="nfpitnet_master",
        version="v2026-04-10",
        raw_snapshot="followup_refresh",
        generated_by="pipeline/v2.py",
        main_outputs={"analysis_csv": "analysis_followup.csv"},
    )
    (release_v1 / "analysis.csv").write_text("id\n1\n", encoding="utf-8")
    (release_v2 / "analysis_followup.csv").write_text("id\n1\n2\n", encoding="utf-8")

    write_study_manifest(
        workspace_root / "studies" / "002-early-risk" / "data_input" / "dataset_manifest.yaml",
        dataset_id="nfpitnet_master",
        relative_path="../../../datasets/master/v2026-03-28/analysis.csv",
        version="v2026-03-28",
    )
    write_study_manifest(
        workspace_root / "studies" / "003-current" / "data_input" / "dataset_manifest.yaml",
        dataset_id="nfpitnet_master",
        relative_path="../../../datasets/master/v2026-04-10/analysis_followup.csv",
        version="v2026-04-10",
    )

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
                        "disease": "NF-PitNET",
                        "modality": ["transcriptome"],
                        "endpoints": ["recurrence"],
                        "roles": ["external_validation", "mechanistic_extension"],
                        "target_families": ["master"],
                        "target_dataset_ids": ["nfpitnet_master"],
                        "target_study_archetypes": ["clinical_classifier", "mechanistic_sidecar_extension"],
                        "status": "candidate",
                        "rationale": "Useful for extension.",
                    },
                    {
                        "dataset_id": "invalid-dataset",
                        "source_type": "GEO",
                        "roles": [],
                        "target_families": [],
                    },
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    result = module.startup_data_readiness(workspace_root=workspace_root)

    assert result["status"] == "attention_needed"
    assert result["private_release_count"] == 2
    assert result["latest_private_releases_by_family"] == [
        {
            "family_id": "master",
            "version_id": "v2026-04-10",
            "dataset_id": "nfpitnet_master",
            "raw_snapshot": "followup_refresh",
            "generated_by": "pipeline/v2.py",
            "contract_status": "manifest_backed",
        }
    ]
    assert result["study_summary"]["study_count"] == 2
    assert result["study_summary"]["review_needed_count"] == 1
    assert result["study_summary"]["review_needed_study_ids"] == ["002-early-risk"]
    assert result["study_summary"]["clear_study_ids"] == ["003-current"]
    assert result["public_summary"]["dataset_count"] == 2
    assert result["public_summary"]["valid_dataset_count"] == 1
    assert result["public_summary"]["actionable_dataset_count"] == 1
    assert result["public_opportunities"]["by_family"] == [
        {
            "family_id": "master",
            "dataset_count": 1,
            "dataset_ids": ["geo-gse000001"],
            "roles": ["external_validation", "mechanistic_extension"],
            "study_archetypes": ["clinical_classifier", "mechanistic_sidecar_extension"],
        }
    ]
    assert result["public_opportunities"]["by_role"] == [
        {"role": "external_validation", "dataset_count": 1, "dataset_ids": ["geo-gse000001"]},
        {"role": "mechanistic_extension", "dataset_count": 1, "dataset_ids": ["geo-gse000001"]},
    ]
    assert result["recommendations"] == [
        "reassess_studies_against_latest_private_release",
        "screen_valid_public_datasets_for_extension",
    ]
    assert Path(result["report_path"]).exists()


def test_startup_data_readiness_excludes_rejected_public_datasets_from_opportunities(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.startup_data_readiness")
    workspace_root = tmp_path / "workspace"
    release_root = workspace_root / "datasets" / "master" / "v2026-03-28"
    release_root.mkdir(parents=True, exist_ok=True)
    write_private_release_manifest(
        release_root / "dataset_manifest.yaml",
        dataset_id="nfpitnet_master",
        version="v2026-03-28",
        raw_snapshot="baseline",
        generated_by="pipeline/v1.py",
        main_outputs={"analysis_csv": "analysis.csv"},
    )
    (release_root / "analysis.csv").write_text("id\n1\n", encoding="utf-8")
    write_study_manifest(
        workspace_root / "studies" / "002-early-risk" / "data_input" / "dataset_manifest.yaml",
        dataset_id="nfpitnet_master",
        relative_path="../../../datasets/master/v2026-03-28/analysis.csv",
        version="v2026-03-28",
    )

    public_registry_path = workspace_root / "portfolio" / "data_assets" / "public" / "registry.json"
    public_registry_path.parent.mkdir(parents=True, exist_ok=True)
    public_registry_path.write_text(
        json.dumps(
            {
                "schema_version": 2,
                "datasets": [
                    {
                        "dataset_id": "geo-gse000002",
                        "source_type": "GEO",
                        "accession": "GSE000002",
                        "roles": ["external_validation"],
                        "target_families": ["master"],
                        "target_study_archetypes": ["clinical_classifier"],
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

    result = module.startup_data_readiness(workspace_root=workspace_root)

    assert result["public_summary"]["dataset_count"] == 1
    assert result["public_summary"]["valid_dataset_count"] == 1
    assert result["public_summary"]["actionable_dataset_count"] == 0
    assert result["public_opportunities"]["by_family"] == []
    assert result["public_opportunities"]["by_role"] == []
    assert result["study_summary"]["public_extension_study_ids"] == []
    assert result["recommendations"] == ["startup_data_ready"]


def test_startup_data_readiness_flags_unresolved_private_contracts(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.startup_data_readiness")
    workspace_root = tmp_path / "workspace"
    release_root = workspace_root / "datasets" / "master" / "v2026-03-28"
    release_root.mkdir(parents=True, exist_ok=True)
    (release_root / "analysis.csv").write_text("id\n1\n", encoding="utf-8")
    write_study_manifest(
        workspace_root / "studies" / "002-early-risk" / "data_input" / "dataset_manifest.yaml",
        dataset_id="nfpitnet_master",
        relative_path="../../../datasets/master/v2026-03-28/analysis.csv",
        version="v2026-03-28",
    )

    result = module.startup_data_readiness(workspace_root=workspace_root)

    assert result["status"] == "attention_needed"
    assert result["study_summary"]["unresolved_contract_study_ids"] == ["002-early-risk"]
    assert result["recommendations"] == ["repair_study_dataset_contracts"]


def test_startup_data_readiness_includes_study_yaml_dataset_inputs_when_manifest_is_absent(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.startup_data_readiness")
    workspace_root = tmp_path / "workspace"
    release_root = workspace_root / "datasets" / "master" / "v2026-03-28"
    release_root.mkdir(parents=True, exist_ok=True)
    write_private_release_manifest(
        release_root / "dataset_manifest.yaml",
        dataset_id="nfpitnet_master",
        version="v2026-03-28",
        raw_snapshot="baseline",
        generated_by="pipeline/v1.py",
        main_outputs={"analysis_csv": "analysis.csv"},
    )
    (release_root / "analysis.csv").write_text("id\n1\n", encoding="utf-8")
    write_study_manifest(
        workspace_root / "studies" / "003-followup-risk" / "study.yaml",
        dataset_id="nfpitnet_master",
        relative_path="../../datasets/master/v2026-03-28/analysis.csv",
        version="v2026-03-28",
    )

    result = module.startup_data_readiness(workspace_root=workspace_root)

    assert result["status"] == "clear"
    assert result["study_summary"]["study_count"] == 1
    assert result["study_summary"]["clear_study_ids"] == ["003-followup-risk"]
    assert result["study_summary"]["unresolved_contract_study_ids"] == []


def test_startup_data_readiness_resolves_study_yaml_dataset_inputs_without_path_when_version_is_declared(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.startup_data_readiness")
    workspace_root = tmp_path / "workspace"
    release_root = workspace_root / "datasets" / "master" / "v2026-03-28"
    release_root.mkdir(parents=True, exist_ok=True)
    write_private_release_manifest(
        release_root / "dataset_manifest.yaml",
        dataset_id="nfpitnet_master",
        version="v2026-03-28",
        raw_snapshot="baseline",
        generated_by="pipeline/v1.py",
        main_outputs={"analysis_csv": "analysis.csv"},
    )
    (release_root / "analysis.csv").write_text("id\n1\n", encoding="utf-8")
    write_study_manifest(
        workspace_root / "studies" / "003-followup-risk" / "study.yaml",
        dataset_id="nfpitnet_master",
        version="v2026-03-28",
    )

    result = module.startup_data_readiness(workspace_root=workspace_root)

    assert result["status"] == "clear"
    assert result["study_summary"]["study_count"] == 1
    assert result["study_summary"]["clear_study_ids"] == ["003-followup-risk"]
    assert result["study_summary"]["unresolved_contract_study_ids"] == []
