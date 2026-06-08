from __future__ import annotations

import importlib
import json
import os
import hashlib
import tarfile
import time
from pathlib import Path

from tests.study_runtime_test_helpers import make_profile
from tests.test_runtime_storage_maintenance_cases.runtime_storage_maintenance_helpers import _write_quest


def _write_restore_archive_triplet(quest_root: Path, *, quest_id: str, archive_id: str, body: bytes) -> Path:
    archive_root = (
        quest_root
        / "artifacts"
        / "runtime"
        / "runtime_storage_maintenance"
        / "restore_proof_archives"
        / "runtime_bucket_compaction"
    )
    archive_root.mkdir(parents=True, exist_ok=True)
    source_dir = quest_root / "_source_fixture" / archive_id
    source_dir.mkdir(parents=True, exist_ok=True)
    source_file = source_dir / "payload.txt"
    source_file.write_bytes(body)
    archive_path = archive_root / f"{archive_id}.tar.gz"
    with tarfile.open(archive_path, "w:gz") as tar:
        tar.add(source_file, arcname="runs/run-001/payload.txt", recursive=False)
    sha256 = _sha256(archive_path)
    manifest_path = archive_root / f"{archive_id}.manifest.json"
    restore_proof_path = archive_root / f"{archive_id}.restore_proof.json"
    manifest_path.write_text(
        json.dumps(
            {
                "surface_kind": "runtime_restore_source_manifest",
                "quest_id": quest_id,
                "source_files": [
                    {
                        "path": "runs/run-001/payload.txt",
                        "entry_type": "file",
                        "size_bytes": len(body),
                        "sha256": _sha256(source_file),
                    }
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    restore_proof_path.write_text(
        json.dumps(
            {
                "surface_kind": "runtime_restore_proof",
                "status": "verified",
                "archive_sha256": sha256,
                "source_file_count": 1,
                "verified_file_count": 1,
                "errors": [],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return archive_path


def test_archive_retention_moves_verified_archive_body_to_cold_object(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_storage_maintenance")
    profile = make_profile(tmp_path)
    quest_id = "quest-retention"
    quest_root = profile.runtime_root / quest_id
    _write_quest(quest_root, quest_id=quest_id, status="stopped")
    archive_path = _write_restore_archive_triplet(
        quest_root,
        quest_id=quest_id,
        archive_id="quest-retention-20260608T010203Z-0001-of-0001-runs",
        body=b"".join(hashlib.sha256(f"payload-{index}".encode("ascii")).digest() for index in range(4096)),
    )
    size_before = archive_path.stat().st_size

    planned = module.maintain_quest_runtime_storage(
        profile=profile,
        quest_root=quest_root,
        archive_retention=True,
        archive_retention_min_mb=0,
    )

    assert planned["archive_retention"]["status"] == "planned"
    assert archive_path.is_file()

    applied = module.maintain_quest_runtime_storage(
        profile=profile,
        quest_root=quest_root,
        archive_retention=True,
        archive_retention_apply=True,
        archive_retention_min_mb=0,
    )

    retention = applied["archive_retention"]
    assert retention["status"] == "applied"
    assert retention["moved_count"] == 1
    assert retention["actual_release_bytes"] > 0
    assert archive_path.is_symlink()
    cold_object_path = Path(retention["candidate_samples"][0]["cold_object_path"])
    assert cold_object_path.is_file()
    assert cold_object_path.stat().st_size == size_before
    assert Path(str(archive_path) + ".cold_ref.json").is_file()


def test_report_retention_bundles_old_timestamped_reports_and_keeps_latest(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_storage_maintenance")
    profile = make_profile(tmp_path)
    quest_id = "quest-reports"
    quest_root = profile.runtime_root / quest_id
    _write_quest(quest_root, quest_id=quest_id, status="stopped")
    family_root = quest_root / "artifacts" / "reports" / "publishability_gate"
    family_root.mkdir(parents=True, exist_ok=True)
    old_time = time.time() - 10 * 24 * 3600
    old_paths = []
    for index in range(5):
        path = family_root / f"2026-05-0{index + 1}T010203Z.json"
        path.write_text(json.dumps({"index": index}) + "\n", encoding="utf-8")
        old_paths.append(path)
        os_time = (old_time + index, old_time + index)
        os.utime(path, os_time)
    latest = family_root / "latest.json"
    latest.write_text('{"latest": true}\n', encoding="utf-8")

    planned = module.maintain_quest_runtime_storage(
        profile=profile,
        quest_root=quest_root,
        report_retention=True,
        report_retention_keep_recent_days=1,
        report_retention_daily_samples=0,
    )

    assert planned["report_retention"]["status"] == "planned"
    assert all(path.exists() for path in old_paths)

    applied = module.maintain_quest_runtime_storage(
        profile=profile,
        quest_root=quest_root,
        report_retention=True,
        report_retention_apply=True,
        report_retention_keep_recent_days=1,
        report_retention_daily_samples=0,
    )

    retention = applied["report_retention"]
    assert retention["status"] == "applied"
    assert retention["candidate_count"] == 5
    assert retention["restore_proof"]["status"] == "verified"
    assert Path(retention["bundle_path"]).is_file()
    assert not any(path.exists() for path in old_paths)
    assert latest.is_file()


def test_retention_apply_is_blocked_when_live_runtime_blocks_storage_maintenance(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_storage_maintenance")
    profile = make_profile(tmp_path)
    quest_id = "quest-live"
    quest_root = profile.runtime_root / quest_id
    _write_quest(quest_root, quest_id=quest_id, status="running", active_run_id="run-live")

    result = module.maintain_quest_runtime_storage(
        profile=profile,
        quest_root=quest_root,
        archive_retention=True,
        archive_retention_apply=True,
        report_retention=True,
        report_retention_apply=True,
    )

    assert result["status"] == "blocked_live_runtime"
    assert result["archive_retention"]["status"] == "blocked_storage_maintenance_not_maintained"
    assert result["report_retention"]["status"] == "blocked_storage_maintenance_not_maintained"


def _sha256(path: Path) -> str:
    import hashlib

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
