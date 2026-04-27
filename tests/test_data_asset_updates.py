from __future__ import annotations

import importlib
import json
from pathlib import Path

import yaml


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_study_manifest(path: Path, *, dataset_id: str, relative_path: str, version: str | None = None) -> None:
    payload: dict[str, object] = {
        "dataset_inputs": [
            {
                "dataset_id": dataset_id,
                "path": relative_path,
            }
        ]
    }
    if version is not None:
        payload["dataset_inputs"][0]["version"] = version
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8")


def test_apply_data_asset_update_upserts_public_dataset_and_writes_mutation_log(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.data_asset_updates")
    workspace_root = tmp_path / "workspace"

    result = module.apply_data_asset_update(
        workspace_root=workspace_root,
        payload={
            "action": "upsert_public_dataset",
            "dataset": {
                "dataset_id": "geo-gse000001",
                "source_type": "GEO",
                "accession": "GSE000001",
                "roles": ["external_validation"],
                "target_families": ["master"],
                "target_study_archetypes": ["clinical_classifier"],
                "status": "candidate",
                "rationale": "Candidate external validation cohort.",
            },
        },
    )

    registry = load_json(workspace_root / "portfolio" / "data_assets" / "public" / "registry.json")
    assert registry["schema_version"] == 2
    assert registry["discovery"]["status"] == "not_started"
    assert registry["datasets"][0]["dataset_id"] == "geo-gse000001"
    assert registry["datasets"][0]["validation"]["is_valid"] is True
    assert result["status"] == "applied"
    assert result["action"] == "upsert_public_dataset"
    assert result["refresh"]["public_validation"]["valid_dataset_count"] == 1
    mutation_log = load_json(Path(result["mutation_log_path"]))
    assert mutation_log["action"] == "upsert_public_dataset"
    assert mutation_log["mutation"]["dataset_id"] == "geo-gse000001"


def test_apply_data_asset_update_updates_public_dataset_status_and_appends_note(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.data_asset_updates")
    workspace_root = tmp_path / "workspace"
    public_registry_path = workspace_root / "portfolio" / "data_assets" / "public" / "registry.json"
    public_registry_path.parent.mkdir(parents=True, exist_ok=True)
    public_registry_path.write_text(
        json.dumps(
            {
                "schema_version": 2,
                "discovery": {
                    "status": "not_started",
                    "last_scouted_on": None,
                    "scope": "route_selection",
                    "notes": [],
                },
                "datasets": [
                    {
                        "dataset_id": "geo-gse000001",
                        "source_type": "GEO",
                        "accession": "GSE000001",
                        "roles": ["external_validation"],
                        "target_families": ["master"],
                        "target_study_archetypes": ["clinical_classifier"],
                        "status": "candidate",
                        "rationale": "Candidate cohort.",
                        "notes": ["initial import"],
                        "validation": {"is_valid": True, "errors": []},
                    }
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    result = module.apply_data_asset_update(
        workspace_root=workspace_root,
        payload={
            "action": "update_public_dataset_status",
            "dataset_id": "geo-gse000001",
            "status": "screened",
            "rationale": "Screened and kept for later benchmarking.",
            "append_notes": ["screened by codex"],
        },
    )

    registry = load_json(public_registry_path)
    dataset = registry["datasets"][0]
    assert dataset["status"] == "screened"
    assert dataset["rationale"] == "Screened and kept for later benchmarking."
    assert dataset["notes"] == ["initial import", "screened by codex"]
    assert result["mutation"]["dataset_id"] == "geo-gse000001"
    assert result["refresh"]["public_validation"]["dataset_count"] == 1


def test_apply_data_asset_update_preserves_public_dataset_discovery_when_updating_status(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.data_asset_updates")
    workspace_root = tmp_path / "workspace"
    public_registry_path = workspace_root / "portfolio" / "data_assets" / "public" / "registry.json"
    public_registry_path.parent.mkdir(parents=True, exist_ok=True)
    public_registry_path.write_text(
        json.dumps(
            {
                "schema_version": 2,
                "discovery": {
                    "status": "completed",
                    "last_scouted_on": "2026-04-08",
                    "scope": "route_selection",
                    "notes": ["seeded from prior scout"],
                },
                "datasets": [
                    {
                        "dataset_id": "geo-gse000001",
                        "source_type": "GEO",
                        "accession": "GSE000001",
                        "roles": ["external_validation"],
                        "target_families": ["master"],
                        "target_study_archetypes": ["clinical_classifier"],
                        "status": "candidate",
                        "rationale": "Candidate cohort.",
                        "notes": ["initial import"],
                        "validation": {"is_valid": True, "errors": []},
                    }
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    module.apply_data_asset_update(
        workspace_root=workspace_root,
        payload={
            "action": "update_public_dataset_status",
            "dataset_id": "geo-gse000001",
            "status": "accepted",
            "append_notes": ["promoted after audit"],
        },
    )

    registry = load_json(public_registry_path)
    assert registry["discovery"] == {
        "status": "completed",
        "last_scouted_on": "2026-04-08",
        "scope": "route_selection",
        "notes": ["seeded from prior scout"],
    }


def test_apply_data_asset_update_records_completed_public_dataset_discovery(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.data_asset_updates")
    workspace_root = tmp_path / "workspace"

    result = module.apply_data_asset_update(
        workspace_root=workspace_root,
        payload={
            "action": "record_public_dataset_discovery",
            "status": "completed",
            "last_scouted_on": "2026-04-08",
            "scope": "route_selection",
            "notes": ["searched GEO, Dryad, Figshare, and PubMed-linked resources"],
        },
    )

    registry = load_json(workspace_root / "portfolio" / "data_assets" / "public" / "registry.json")
    assert registry["discovery"] == {
        "status": "completed",
        "last_scouted_on": "2026-04-08",
        "scope": "route_selection",
        "notes": ["searched GEO, Dryad, Figshare, and PubMed-linked resources"],
    }
    assert registry["datasets"] == []
    assert result["mutation"]["kind"] == "public_registry_discovery_update"
    assert result["refresh"]["public_validation"]["dataset_count"] == 0


def test_apply_data_asset_update_upserts_private_release_manifest(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.data_asset_updates")
    workspace_root = tmp_path / "workspace"
    release_root = workspace_root / "datasets" / "master" / "v2026-04-10"
    release_root.mkdir(parents=True, exist_ok=True)
    (release_root / "analysis.csv").write_text("id\n1\n", encoding="utf-8")

    result = module.apply_data_asset_update(
        workspace_root=workspace_root,
        payload={
            "action": "upsert_private_release_manifest",
            "family_id": "master",
            "version_id": "v2026-04-10",
            "manifest": {
                "dataset_id": "nfpitnet_master",
                "raw_snapshot": "followup_refresh",
                "generated_by": "pipeline/v2.py",
                "source_release": {"family_id": "master", "version": "v2026-03-28"},
                "supersedes_versions": ["v2026-03-28"],
                "main_outputs": {"analysis_csv": "analysis.csv"},
                "notes": ["followup release"],
                "release_contract": {"update_type": ["followup_refresh"], "qc_status": "locked"},
            },
        },
    )

    manifest = yaml.safe_load((release_root / "dataset_manifest.yaml").read_text(encoding="utf-8"))
    assert manifest["dataset_id"] == "nfpitnet_master"
    assert manifest["source_release"] == {"family_id": "master", "version": "v2026-03-28"}
    assert manifest["supersedes_versions"] == ["v2026-03-28"]
    assert manifest["main_outputs"] == {"analysis_csv": "analysis.csv"}
    assert result["refresh"]["status"]["private"]["release_count"] == 1
    assert result["mutation"]["family_id"] == "master"
    assert Path(result["mutation_log_path"]).exists()


def test_apply_data_asset_update_refresh_all_returns_compound_summary(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.data_asset_updates")
    workspace_root = tmp_path / "workspace"

    result = module.apply_data_asset_update(
        workspace_root=workspace_root,
        payload={"action": "refresh_all"},
    )

    assert result["status"] == "applied"
    assert result["action"] == "refresh_all"
    assert result["refresh"]["status"]["workspace_root"] == str(workspace_root)
    assert result["refresh"]["startup_data_readiness"]["status"] in {"clear", "attention_needed"}


def test_apply_data_asset_update_rejects_incomplete_private_release_manifest(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.data_asset_updates")
    workspace_root = tmp_path / "workspace"

    try:
        module.apply_data_asset_update(
            workspace_root=workspace_root,
            payload={
                "action": "upsert_private_release_manifest",
                "family_id": "master",
                "version_id": "v2026-04-10",
                "manifest": {
                    "raw_snapshot": "followup_refresh",
                    "generated_by": "pipeline/v2.py",
                    "main_outputs": {"analysis_csv": "analysis.csv"},
                },
            },
        )
    except ValueError as exc:
        assert "dataset_id" in str(exc)
    else:
        raise AssertionError("Expected ValueError for incomplete private release manifest")


def test_apply_data_asset_update_writes_refresh_failure_audit_log(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.data_asset_updates")
    workspace_root = tmp_path / "workspace"
    release_root = workspace_root / "datasets" / "master" / "v2026-04-10"
    release_root.mkdir(parents=True, exist_ok=True)
    (release_root / "analysis.csv").write_text("id\n1\n", encoding="utf-8")
    (release_root / "dataset_manifest.yaml").write_text(
        yaml.safe_dump(
            {
                "dataset_id": "nfpitnet_master",
                "version": "v2026-04-10",
                "raw_snapshot": "followup_refresh",
                "generated_by": "pipeline/v2.py",
                "main_outputs": {"analysis_csv": "analysis.csv"},
            },
            sort_keys=False,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )
    write_study_manifest(
        workspace_root / "studies" / "002-early-risk" / "data_input" / "dataset_manifest.yaml",
        dataset_id="nfpitnet_master",
        relative_path="../../../datasets/master/v2026-03-28/analysis.csv",
        version="v2026-03-28",
    )

    try:
        module.apply_data_asset_update(
            workspace_root=workspace_root,
            payload={
                "action": "upsert_public_dataset",
                "dataset": {
                    "dataset_id": "geo-gse000001",
                    "source_type": "GEO",
                    "accession": "GSE000001",
                    "roles": ["external_validation"],
                    "target_families": ["master"],
                    "target_study_archetypes": ["clinical_classifier"],
                    "status": "candidate",
                    "rationale": "Candidate external validation cohort.",
                },
            },
        )
    except FileNotFoundError as exc:
        assert "Private release not found" in str(exc)
    else:
        raise AssertionError("Expected FileNotFoundError during refresh")

    mutation_logs = sorted((workspace_root / "portfolio" / "data_assets" / "mutations").glob("*.json"))
    assert len(mutation_logs) == 1
    mutation_log = load_json(mutation_logs[0])
    assert mutation_log["status"] == "refresh_failed"
    assert mutation_log["mutation"]["dataset_id"] == "geo-gse000001"
    assert mutation_log["refresh_error"]["type"] == "FileNotFoundError"
    registry = load_json(workspace_root / "portfolio" / "data_assets" / "public" / "registry.json")
    assert registry["datasets"][0]["dataset_id"] == "geo-gse000001"


def test_apply_data_asset_update_rejects_invalid_public_dataset_enums_and_logs_failure(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.data_asset_updates")
    workspace_root = tmp_path / "workspace"

    try:
        module.apply_data_asset_update(
            workspace_root=workspace_root,
            payload={
                "action": "upsert_public_dataset",
                "dataset": {
                    "dataset_id": "geo-gse000001",
                    "source_type": "GEO",
                    "roles": ["unknown_role"],
                    "target_families": ["master"],
                    "status": "archived",
                },
            },
        )
    except ValueError as exc:
        assert "invalid" in str(exc)
    else:
        raise AssertionError("Expected ValueError for invalid public dataset enums")

    mutation_logs = sorted((workspace_root / "portfolio" / "data_assets" / "mutations").glob("*.json"))
    assert len(mutation_logs) == 1
    mutation_log = load_json(mutation_logs[0])
    assert mutation_log["status"] == "mutation_failed"
    assert mutation_log["error"]["type"] == "ValueError"
    assert not (workspace_root / "portfolio" / "data_assets" / "public" / "registry.json").exists()


def test_apply_data_asset_update_requires_existing_release_root_before_manifest_upsert(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.data_asset_updates")
    workspace_root = tmp_path / "workspace"
    target_root = workspace_root / "datasets" / "master" / "v2026-04-10"

    try:
        module.apply_data_asset_update(
            workspace_root=workspace_root,
            payload={
                "action": "upsert_private_release_manifest",
                "family_id": "master",
                "version_id": "v2026-04-10",
                "manifest": {
                    "dataset_id": "nfpitnet_master",
                    "raw_snapshot": "followup_refresh",
                    "generated_by": "pipeline/v2.py",
                    "main_outputs": {"analysis_csv": "analysis.csv"},
                },
            },
        )
    except FileNotFoundError as exc:
        assert "Release root does not exist" in str(exc)
    else:
        raise AssertionError("Expected FileNotFoundError for missing release root")

    assert not target_root.exists()


def test_apply_data_asset_update_rejects_private_manifest_with_missing_outputs(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.data_asset_updates")
    workspace_root = tmp_path / "workspace"
    release_root = workspace_root / "datasets" / "master" / "v2026-04-10"
    release_root.mkdir(parents=True, exist_ok=True)

    try:
        module.apply_data_asset_update(
            workspace_root=workspace_root,
            payload={
                "action": "upsert_private_release_manifest",
                "family_id": "master",
                "version_id": "v2026-04-10",
                "manifest": {
                    "dataset_id": "nfpitnet_master",
                    "raw_snapshot": "followup_refresh",
                    "generated_by": "pipeline/v2.py",
                    "main_outputs": {"analysis_csv": "analysis.csv"},
                },
            },
        )
    except FileNotFoundError as exc:
        assert "Missing declared main outputs" in str(exc)
    else:
        raise AssertionError("Expected FileNotFoundError for missing declared outputs")

    assert not (release_root / "dataset_manifest.yaml").exists()


def test_apply_data_asset_update_uses_unique_log_paths_for_same_timestamp(tmp_path: Path, monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.controllers.data_asset_updates")
    workspace_root = tmp_path / "workspace"
    monkeypatch.setattr(module, "utc_now", lambda: "2026-03-29T10:39:24+00:00")

    first = module.apply_data_asset_update(workspace_root=workspace_root, payload={"action": "refresh_all"})
    second = module.apply_data_asset_update(workspace_root=workspace_root, payload={"action": "refresh_all"})

    assert first["mutation_log_path"] != second["mutation_log_path"]
    mutation_logs = sorted((workspace_root / "portfolio" / "data_assets" / "mutations").glob("*.json"))
    assert len(mutation_logs) == 2
