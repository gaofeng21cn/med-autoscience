from __future__ import annotations

import hashlib
import importlib
import json
import os
from pathlib import Path

import pytest


def _workspace(tmp_path: Path) -> Path:
    workspace = tmp_path / "Study"
    workspace.mkdir()
    (workspace / "workspace.yaml").write_text("workspace_id: Study\n", encoding="utf-8")
    (workspace / "runtime" / "archives").mkdir(parents=True)
    return workspace


def test_historical_directory_retention_archives_capsule_with_verified_hardlinks(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.historical_directory_retention")
    workspace = _workspace(tmp_path)
    capsule = (
        workspace
        / "runtime"
        / "archives"
        / "legacy_mds"
        / "20260516T123324Z"
        / "med-deepscientist"
    )
    pack_root = capsule / "runtime" / "uv-cache" / ".git" / "objects" / "pack"
    pack_root.mkdir(parents=True)
    source = pack_root / "pack-a.pack"
    linked = pack_root / "pack-b.pack"
    source.write_bytes(b"pack-body" * 1024)
    os.link(source, linked)
    data_asset = workspace / "data" / "datasets" / "source.csv"
    data_asset.parent.mkdir(parents=True)
    data_asset.write_text("do,not,touch\n", encoding="utf-8")

    planned = module.run_historical_directory_retention(
        root=workspace / "runtime" / "archives",
        apply=False,
        cold_store_root=tmp_path / "cold-store",
        min_mb=0,
    )
    applied = module.run_historical_directory_retention(
        root=workspace / "runtime" / "archives",
        apply=True,
        cold_store_root=tmp_path / "cold-store",
        min_mb=0,
    )

    assert planned["status"] == "planned"
    assert applied["status"] == "applied"
    assert applied["moved_count"] == 1
    assert applied["latest_receipt_path"] == str(
        workspace / "runtime" / "artifacts" / "historical_directory_retention" / "latest.json"
    )
    ref = json.loads((capsule / "capsule.cold_ref.json").read_text(encoding="utf-8"))
    archive = Path(ref["cold_archive_path"])
    assert archive.is_file()
    with archive.open("rb") as handle:
        assert hashlib.file_digest(handle, "sha256").hexdigest() == ref["archive_sha256"]
    restore = json.loads(Path(ref["restore_proof_path"]).read_text(encoding="utf-8"))
    assert restore["status"] == "verified"
    verified = {entry["path"] for entry in restore["verified_entries"]}
    assert {
        "med-deepscientist/runtime/uv-cache/.git/objects/pack/pack-a.pack",
        "med-deepscientist/runtime/uv-cache/.git/objects/pack/pack-b.pack",
    } <= verified
    assert data_asset.is_file()


def test_historical_directory_retention_blocks_data_assets(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.historical_directory_retention")
    data_root = (
        tmp_path
        / "Study"
        / "data"
        / "datasets"
        / "legacy_mds"
        / "20260516T123324Z"
        / "med-deepscientist"
    )
    data_root.mkdir(parents=True)
    (data_root / "source.csv").write_text("do,not,touch\n", encoding="utf-8")

    result = module.run_historical_directory_retention(
        root=data_root,
        apply=True,
        cold_store_root=tmp_path / "cold-store",
        min_mb=0,
    )

    assert result["status"] == "nothing_to_retain"
    assert (data_root / "source.csv").is_file()


def test_historical_directory_retention_archives_repo_compare_once(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.historical_directory_retention")
    workspace = _workspace(tmp_path)
    repo_compare = (
        workspace
        / "archive"
        / "legacy_ops_surfaces"
        / "20260607T090435Z"
        / "framework_refs"
        / "_repo_compare"
    )
    pack = repo_compare / "one-person-lab" / ".git" / "objects" / "pack" / "pack-a.pack"
    pack.parent.mkdir(parents=True)
    pack.write_bytes(b"git-pack-body" * 1024)

    applied = module.run_historical_directory_retention(
        root=repo_compare,
        apply=True,
        cold_store_root=tmp_path / "cold-store",
        min_mb=0,
    )
    rerun = module.run_historical_directory_retention(
        root=repo_compare,
        apply=True,
        cold_store_root=tmp_path / "cold-store",
        min_mb=0,
    )

    assert applied["status"] == "applied"
    assert applied["candidate_samples"][0]["historical_surface_kind"] == (
        "legacy_ops_repo_compare_directory_capsule"
    )
    assert (repo_compare / "capsule.cold_ref.json").is_file()
    assert not pack.exists()
    assert rerun["status"] == "nothing_to_retain"
    assert rerun["candidate_count"] == 0


def test_historical_directory_retention_cli_dispatches_controller(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    called: dict[str, object] = {}

    def fake_run(**kwargs: object) -> dict[str, object]:
        called.update(kwargs)
        return {"surface_kind": "historical_directory_retention", "status": "applied"}

    monkeypatch.setattr(cli.historical_directory_retention, "run_historical_directory_retention", fake_run)
    root = tmp_path / "workspace"
    cold_store = tmp_path / "cold-store"

    exit_code = cli.main(
        [
            "historical-directory-retention",
            "--root",
            str(root),
            "--apply",
            "--cold-store-root",
            str(cold_store),
            "--min-mb",
            "3",
            "--max-directories",
            "9",
        ]
    )

    assert exit_code == 0
    assert called == {
        "root": root,
        "apply": True,
        "cold_store_root": cold_store,
        "min_mb": 3,
        "max_directories": 9,
    }
    assert json.loads(capsys.readouterr().out)["status"] == "applied"
