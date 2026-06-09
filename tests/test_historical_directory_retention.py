from __future__ import annotations

import hashlib
import importlib
import json
from pathlib import Path
import os
import tarfile


def test_historical_directory_retention_archives_legacy_mds_capsule(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.historical_directory_retention")
    workspace = tmp_path / "Study"
    (workspace / "runtime" / "archives").mkdir(parents=True)
    (workspace / "workspace.yaml").write_text("workspace_id: Study\n", encoding="utf-8")
    capsule = (
        workspace
        / "runtime"
        / "archives"
        / "legacy_mds"
        / "20260516T123324Z"
        / "med-deepscientist"
    )
    log_path = capsule / "runtime" / "logs" / "daemon.log"
    state_path = capsule / "runtime" / "quests" / "001-study" / "artifacts" / "runtime" / "runtime_lifecycle.sqlite"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_bytes(b"log-body" * 1024)
    state_path.write_bytes(b"sqlite-body" * 1024)
    data_asset = workspace / "data" / "datasets" / "source.csv"
    data_asset.parent.mkdir(parents=True)
    data_asset.write_text("do,not,touch\n", encoding="utf-8")

    planned = module.run_historical_directory_retention(
        root=workspace / "runtime" / "archives",
        apply=False,
        cold_store_root=tmp_path / "cold-store",
        min_mb=0,
    )

    assert planned["status"] == "planned"
    assert planned["candidate_count"] == 1
    assert planned["candidate_samples"][0]["historical_surface_kind"] == "legacy_mds_directory_capsule"

    applied = module.run_historical_directory_retention(
        root=workspace / "runtime" / "archives",
        apply=True,
        cold_store_root=tmp_path / "cold-store",
        min_mb=0,
    )

    assert applied["status"] == "applied"
    assert applied["moved_count"] == 1
    assert applied["actual_release_bytes"] > 0
    assert applied["latest_receipt_path"] == str(
        workspace / "runtime" / "artifacts" / "historical_directory_retention" / "latest.json"
    )
    ref_path = capsule / "capsule.cold_ref.json"
    assert ref_path.is_file()
    assert not log_path.exists()
    ref = json.loads(ref_path.read_text(encoding="utf-8"))
    archive_path = Path(ref["cold_archive_path"])
    assert archive_path.is_file()
    assert _sha256(archive_path) == ref["archive_sha256"]
    with tarfile.open(archive_path, "r:gz") as tar:
        names = set(tar.getnames())
    assert "med-deepscientist/runtime/logs/daemon.log" in names
    assert "med-deepscientist/runtime/quests/001-study/artifacts/runtime/runtime_lifecycle.sqlite" in names
    restore_proof = json.loads(Path(ref["restore_proof_path"]).read_text(encoding="utf-8"))
    assert restore_proof["status"] == "verified"
    assert data_asset.is_file()


def test_historical_directory_retention_blocks_data_assets(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.historical_directory_retention")
    data_root = tmp_path / "Study" / "data" / "datasets" / "legacy_mds" / "20260516T123324Z" / "med-deepscientist"
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


def test_historical_directory_retention_archives_legacy_ops_repo_compare(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.historical_directory_retention")
    workspace = tmp_path / "Study"
    workspace.mkdir(parents=True)
    (workspace / "workspace.yaml").write_text("workspace_id: Study\n", encoding="utf-8")
    (workspace / "runtime" / "quests").mkdir(parents=True)
    repo_compare = (
        workspace
        / "archive"
        / "legacy_ops_surfaces"
        / "20260607T090435Z"
        / "framework_refs"
        / "_repo_compare"
    )
    pack_path = repo_compare / "one-person-lab" / ".git" / "objects" / "pack" / "pack-a.pack"
    pack_path.parent.mkdir(parents=True, exist_ok=True)
    pack_path.write_bytes(b"git-pack-body" * 1024)

    applied = module.run_historical_directory_retention(
        root=repo_compare,
        apply=True,
        cold_store_root=tmp_path / "cold-store",
        min_mb=0,
    )

    assert applied["status"] == "applied"
    assert applied["candidate_count"] == 1
    assert applied["candidate_samples"][0]["historical_surface_kind"] == "legacy_ops_repo_compare_directory_capsule"
    assert applied["candidate_samples"][0]["workspace_relative_path"] == (
        "archive/legacy_ops_surfaces/20260607T090435Z/framework_refs/_repo_compare"
    )
    assert applied["latest_receipt_path"] == str(
        workspace / "runtime" / "artifacts" / "historical_directory_retention" / "latest.json"
    )
    ref_path = repo_compare / "capsule.cold_ref.json"
    assert ref_path.is_file()
    assert not pack_path.exists()
    ref = json.loads(ref_path.read_text(encoding="utf-8"))
    assert ref["historical_surface_kind"] == "legacy_ops_repo_compare_directory_capsule"
    assert ref["workspace_relative_path"] == "archive/legacy_ops_surfaces/20260607T090435Z/framework_refs/_repo_compare"
    assert Path(ref["cold_archive_path"]).is_file()

    rerun = module.run_historical_directory_retention(
        root=repo_compare,
        apply=True,
        cold_store_root=tmp_path / "cold-store",
        min_mb=0,
    )

    assert rerun["status"] == "nothing_to_retain"
    assert rerun["candidate_count"] == 0
    assert (repo_compare / "capsule.cold_ref.json").is_file()


def test_historical_directory_retention_restore_proof_accepts_hardlinks(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.historical_directory_retention")
    workspace = tmp_path / "Study"
    (workspace / "runtime" / "archives").mkdir(parents=True)
    (workspace / "workspace.yaml").write_text("workspace_id: Study\n", encoding="utf-8")
    capsule = (
        workspace
        / "runtime"
        / "archives"
        / "legacy_mds"
        / "20260516T123324Z"
        / "med-deepscientist"
    )
    pack_path = capsule / "runtime" / "runtime" / "uv-cache" / "git-v0" / "db" / "repo" / ".git" / "objects" / "pack"
    pack_path.mkdir(parents=True)
    source = pack_path / "pack-a.pack"
    linked = pack_path / "pack-b.pack"
    source.write_bytes(b"pack-body" * 1024)
    os.link(source, linked)

    applied = module.run_historical_directory_retention(
        root=workspace / "runtime" / "archives",
        apply=True,
        cold_store_root=tmp_path / "cold-store",
        min_mb=0,
    )

    assert applied["status"] == "applied"
    ref = json.loads((capsule / "capsule.cold_ref.json").read_text(encoding="utf-8"))
    restore_proof = json.loads(Path(ref["restore_proof_path"]).read_text(encoding="utf-8"))
    assert restore_proof["status"] == "verified"
    verified_paths = {entry["path"] for entry in restore_proof["verified_entries"]}
    assert "med-deepscientist/runtime/runtime/uv-cache/git-v0/db/repo/.git/objects/pack/pack-a.pack" in verified_paths
    assert "med-deepscientist/runtime/runtime/uv-cache/git-v0/db/repo/.git/objects/pack/pack-b.pack" in verified_paths


def test_historical_directory_retention_cli_dispatches_controller(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    called: dict[str, object] = {}

    def fake_run_historical_directory_retention(
        *,
        root: Path,
        apply: bool,
        cold_store_root: Path,
        min_mb: int,
        max_directories: int | None,
    ) -> dict[str, object]:
        called["root"] = root
        called["apply"] = apply
        called["cold_store_root"] = cold_store_root
        called["min_mb"] = min_mb
        called["max_directories"] = max_directories
        return {"surface_kind": "historical_directory_retention", "status": "applied"}

    monkeypatch.setattr(
        cli.historical_directory_retention,
        "run_historical_directory_retention",
        fake_run_historical_directory_retention,
    )

    exit_code = cli.main(
        [
            "historical-directory-retention",
            "--root",
            str(tmp_path / "workspace"),
            "--apply",
            "--cold-store-root",
            str(tmp_path / "cold-store"),
            "--min-mb",
            "3",
            "--max-directories",
            "9",
        ]
    )

    assert exit_code == 0
    assert called == {
        "root": tmp_path / "workspace",
        "apply": True,
        "cold_store_root": tmp_path / "cold-store",
        "min_mb": 3,
        "max_directories": 9,
    }
    assert json.loads(capsys.readouterr().out)["status"] == "applied"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
