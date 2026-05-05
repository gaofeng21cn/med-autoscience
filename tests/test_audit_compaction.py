from __future__ import annotations

import hashlib
import importlib
import json
from datetime import UTC, datetime
from pathlib import Path

import pytest


pytestmark = pytest.mark.meta


def test_audit_compaction_dry_run_keeps_source_and_writes_nothing(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.audit_compaction")
    bucket = tmp_path / "audit_bucket"
    archive_dir = tmp_path / "archive"
    (bucket / "nested").mkdir(parents=True)
    source_file = bucket / "nested" / "trace.json"
    source_file.write_bytes(b'{"ok": true}\n')

    result = module.compact_audit_bucket(
        bucket,
        archive_dir=archive_dir,
        workspace_classification="stopped_cold",
        bucket_classification="cold_bucket",
    )

    assert result["ok"] is True
    assert result["apply"] is False
    assert result["source_removed"] is False
    assert bucket.exists()
    assert not archive_dir.exists()
    assert result["archive_path"].endswith("audit_bucket.tar.gz")
    assert result["entries"] == [
        {
            "source_path": str(source_file),
            "relative_path": "nested/trace.json",
            "original_sha256": hashlib.sha256(b'{"ok": true}\n').hexdigest(),
            "bytes": len(b'{"ok": true}\n'),
        }
    ]


def test_audit_compaction_apply_archives_indexes_ledgers_and_restores_bytes(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.audit_compaction")
    bucket = tmp_path / "audit_bucket"
    archive_dir = tmp_path / "archive"
    (bucket / "nested").mkdir(parents=True)
    first = bucket / "a.txt"
    second = bucket / "nested" / "payload.bin"
    first_bytes = b"cold audit record\n"
    second_bytes = bytes(range(32))
    first.write_bytes(first_bytes)
    second.write_bytes(second_bytes)

    result = module.compact_audit_bucket(
        bucket,
        archive_dir=archive_dir,
        workspace_classification="archived_workspace",
        bucket_classification="stopped_cold",
        compatibility_export_ref="artifact://lifecycle/compat_exports/workspace_storage_audit.latest.json",
        apply=True,
        timestamp=datetime(2026, 5, 5, 1, 2, 3, tzinfo=UTC),
    )

    assert result["ok"] is True
    assert result["source_removed"] is True
    assert not bucket.exists()
    archive_path = Path(result["archive_path"])
    restore_index_path = Path(result["restore_index_path"])
    provenance_ledger_path = Path(result["provenance_ledger_path"])
    assert archive_path.exists()
    assert restore_index_path.exists()
    assert provenance_ledger_path.exists()

    restore_index = json.loads(restore_index_path.read_text(encoding="utf-8"))
    archive_sha256 = _sha256(archive_path)
    assert restore_index["archive_sha256"] == archive_sha256
    assert restore_index["timestamp"] == "2026-05-05T01:02:03Z"
    assert {entry["relative_path"] for entry in restore_index["entries"]} == {"a.txt", "nested/payload.bin"}
    assert all(entry["archive_sha256"] == archive_sha256 for entry in restore_index["entries"])
    assert all(entry["timestamp"] == "2026-05-05T01:02:03Z" for entry in restore_index["entries"])

    ledger_records = [
        json.loads(line) for line in provenance_ledger_path.read_text(encoding="utf-8").splitlines()
    ]
    assert {record["source_path"] for record in ledger_records} == {str(first), str(second)}
    assert {record["original_sha256"] for record in ledger_records} == {
        hashlib.sha256(first_bytes).hexdigest(),
        hashlib.sha256(second_bytes).hexdigest(),
    }
    assert {record["archive_sha256"] for record in ledger_records} == {archive_sha256}
    assert {record["timestamp"] for record in ledger_records} == {"2026-05-05T01:02:03Z"}
    assert {record["bytes"] for record in ledger_records} == {len(first_bytes), len(second_bytes)}
    assert result["audit_compaction_contract"] == {
        "gates": [
            {"gate_id": "restore", "status": "passed"},
            {"gate_id": "index", "status": "passed"},
            {"gate_id": "provenance", "status": "passed"},
        ],
        "restore_index_ref": str(restore_index_path),
        "provenance_ref": str(provenance_ledger_path),
        "compatibility_export_ref": "artifact://lifecycle/compat_exports/workspace_storage_audit.latest.json",
    }

    restore_root = tmp_path / "restore"
    restore_result = module.restore_audit_bucket(restore_index_path, restore_root=restore_root)

    restored_bucket = restore_root / "audit_bucket"
    assert restore_result["ok"] is True
    assert (restored_bucket / "a.txt").read_bytes() == first_bytes
    assert (restored_bucket / "nested" / "payload.bin").read_bytes() == second_bytes


def test_audit_compaction_file_bucket_uses_gzip_and_restores_bytes(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.audit_compaction")
    bucket_file = tmp_path / "audit.log"
    bucket_file.write_bytes(b"log bytes\n")

    result = module.compact_audit_bucket(
        bucket_file,
        archive_dir=tmp_path / "archive",
        workspace_classification="stopped_cold",
        bucket_classification="cold_bucket",
        apply=True,
    )

    restore_index_path = Path(result["restore_index_path"])
    restore_index = json.loads(restore_index_path.read_text(encoding="utf-8"))
    assert restore_index["archive_format"] == "gzip"
    assert Path(result["archive_path"]).name == "audit.log.gz"

    restore_root = tmp_path / "restore-file"
    module.restore_audit_bucket(restore_index_path, restore_root=restore_root)

    assert (restore_root / "audit.log").read_bytes() == b"log bytes\n"


def test_audit_compaction_fails_closed_when_archive_dir_is_inside_source(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.audit_compaction")
    bucket = tmp_path / "audit_bucket"
    bucket.mkdir()
    (bucket / "payload.json").write_text("{}", encoding="utf-8")

    result = module.compact_audit_bucket(
        bucket,
        archive_dir=bucket / "cold_archive",
        workspace_classification="stopped_cold",
        bucket_classification="cold_bucket",
        apply=True,
    )

    assert result["ok"] is False
    assert result["source_removed"] is False
    assert bucket.exists()
    assert "archive_dir_inside_source_path" in result["blockers"]


@pytest.mark.parametrize("bucket_classification", ["live_active", "pinned", "unknown"])
def test_audit_compaction_fails_closed_for_live_pinned_and_unknown_buckets(
    tmp_path: Path,
    bucket_classification: str,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.audit_compaction")
    bucket = tmp_path / "audit_bucket"
    bucket.mkdir()
    (bucket / "payload.json").write_text("{}", encoding="utf-8")

    result = module.compact_audit_bucket(
        bucket,
        archive_dir=tmp_path / "archive",
        workspace_classification="stopped_cold",
        bucket_classification=bucket_classification,
        apply=True,
    )

    assert result["ok"] is False
    assert result["archive_path"] is None
    assert result["source_removed"] is False
    assert bucket.exists()
    assert f"bucket_classification_fail_closed:{bucket_classification}" in result["blockers"]


@pytest.mark.parametrize("workspace_classification", ["live_active", "pinned", "unknown"])
def test_audit_compaction_fails_closed_for_non_cold_workspaces(
    tmp_path: Path,
    workspace_classification: str,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.audit_compaction")
    bucket = tmp_path / "audit_bucket"
    bucket.mkdir()
    (bucket / "payload.json").write_text("{}", encoding="utf-8")

    result = module.compact_audit_bucket(
        bucket,
        archive_dir=tmp_path / "archive",
        workspace_classification=workspace_classification,
        bucket_classification="cold_bucket",
        apply=True,
    )

    assert result["ok"] is False
    assert result["archive_path"] is None
    assert result["source_removed"] is False
    assert bucket.exists()
    assert "workspace_not_stopped_cold_or_archived" in result["blockers"]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()
