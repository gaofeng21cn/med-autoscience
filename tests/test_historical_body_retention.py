from __future__ import annotations

import hashlib
import importlib
import json
from pathlib import Path


def test_historical_body_retention_replaces_legacy_storage_audit_json_with_ref(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.historical_body_retention")
    workspace = tmp_path / "Study"
    audit_root = workspace / "archive" / "legacy_root_surfaces" / "20260607T000000Z" / "storage_audit"
    audit_path = audit_root / "20260505T090041Z.json"
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    audit_payload = {
        "surface_kind": "workspace_storage_audit",
        "files": [{"path": f"file-{index}", "payload": "x" * 1024} for index in range(256)],
    }
    audit_path.write_text(json.dumps(audit_payload, ensure_ascii=False) + "\n", encoding="utf-8")
    latest_path = audit_root / "latest.json"
    latest_path.write_text('{"status": "current"}\n', encoding="utf-8")
    original_sha = _sha256(audit_path)
    original_bytes = audit_path.stat().st_size

    planned = module.run_historical_body_retention(
        root=workspace,
        apply=False,
        cold_store_root=tmp_path / "cold-store",
        min_mb=0,
    )

    assert planned["status"] == "planned"
    assert planned["candidate_count"] == 1
    assert json.loads(audit_path.read_text(encoding="utf-8")) == audit_payload

    applied = module.run_historical_body_retention(
        root=workspace,
        apply=True,
        cold_store_root=tmp_path / "cold-store",
        min_mb=0,
    )

    assert applied["status"] == "applied"
    assert applied["moved_count"] == 1
    assert applied["actual_release_bytes"] > 0
    slim = json.loads(audit_path.read_text(encoding="utf-8"))
    assert slim["surface_kind"] == "historical_body_retention_ref"
    assert slim["body_included"] is False
    assert slim["original_sha256"] == original_sha
    assert slim["original_bytes"] == original_bytes
    assert latest_path.read_text(encoding="utf-8") == '{"status": "current"}\n'
    ref = json.loads(Path(str(audit_path) + ".cold_ref.json").read_text(encoding="utf-8"))
    cold_object = Path(ref["cold_object_path"])
    assert cold_object.is_file()
    assert _sha256(cold_object) == original_sha


def test_historical_body_retention_moves_quest_git_archive_to_cold_object_symlink(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.historical_body_retention")
    workspace = tmp_path / "Study"
    archive_path = (
        workspace
        / "runtime"
        / "artifacts"
        / "lifecycle_migration"
        / "quest-git-cutover"
        / "quest_git_archives"
        / "002-study.git.tar.gz"
    )
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    archive_path.write_bytes(b"git-archive-body" * 1024)
    data_asset = workspace / "data" / "datasets" / "raw" / "source.zip"
    data_asset.parent.mkdir(parents=True, exist_ok=True)
    data_asset.write_bytes(b"do-not-touch" * 1024)
    original_sha = _sha256(archive_path)
    original_bytes = archive_path.stat().st_size

    applied = module.run_historical_body_retention(
        root=workspace,
        apply=True,
        cold_store_root=tmp_path / "cold-store",
        min_mb=0,
    )

    assert applied["status"] == "applied"
    assert applied["candidate_count"] == 1
    assert archive_path.is_symlink()
    ref = json.loads(Path(str(archive_path) + ".cold_ref.json").read_text(encoding="utf-8"))
    assert ref["surface_kind"] == "historical_body_cold_ref"
    assert ref["body_included"] is False
    assert ref["original_sha256"] == original_sha
    assert ref["original_bytes"] == original_bytes
    assert Path(ref["cold_object_path"]).is_file()
    assert data_asset.is_file()


def test_historical_body_retention_classifies_legacy_mds_from_runtime_archives_root(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.historical_body_retention")
    workspace = tmp_path / "Study"
    workspace.mkdir(parents=True)
    (workspace / "workspace.yaml").write_text("workspace_id: Study\n", encoding="utf-8")
    archive_root = workspace / "runtime" / "archives"
    legacy_body = archive_root / "legacy_mds" / "20260516T123324Z" / "med-deepscientist" / "events.jsonl.gz"
    legacy_body.parent.mkdir(parents=True, exist_ok=True)
    legacy_body.write_bytes(b"legacy-mds-body" * 1024)
    original_sha = _sha256(legacy_body)

    applied = module.run_historical_body_retention(
        root=archive_root,
        apply=True,
        cold_store_root=tmp_path / "cold-store",
        min_mb=0,
    )

    assert applied["status"] == "applied"
    assert applied["candidate_count"] == 1
    assert applied["latest_receipt_path"] == str(workspace / "runtime" / "artifacts" / "historical_body_retention" / "latest.json")
    assert legacy_body.is_symlink()
    ref = json.loads(Path(str(legacy_body) + ".cold_ref.json").read_text(encoding="utf-8"))
    assert ref["historical_surface_kind"] == "legacy_mds_archive_body"
    assert ref["original_sha256"] == original_sha


def test_historical_body_retention_moves_oversized_jsonl_archive_body_to_cold_object(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.historical_body_retention")
    workspace = tmp_path / "Study"
    workspace.mkdir(parents=True)
    (workspace / "workspace.yaml").write_text("workspace_id: Study\n", encoding="utf-8")
    archive_path = (
        workspace
        / "runtime"
        / "quests"
        / "002-study"
        / "artifacts"
        / "runtime"
        / "runtime_storage_maintenance"
        / "oversized_jsonl"
        / "20260603T113138Z_artifacts__runtime__mas_runtime_events.jsonl_48515ca9025f.jsonl.gz"
    )
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    archive_path.write_bytes(b"jsonl-gzip-body" * 1024)
    original_sha = _sha256(archive_path)

    applied = module.run_historical_body_retention(
        root=workspace,
        apply=True,
        cold_store_root=tmp_path / "cold-store",
        min_mb=0,
    )

    assert applied["status"] == "applied"
    assert applied["candidate_count"] == 1
    assert archive_path.is_symlink()
    ref = json.loads(Path(str(archive_path) + ".cold_ref.json").read_text(encoding="utf-8"))
    assert ref["historical_surface_kind"] == "oversized_runtime_jsonl_archive_body"
    assert ref["original_sha256"] == original_sha
    assert Path(ref["cold_object_path"]).is_file()


def test_historical_body_retention_replaces_legacy_physical_cleanup_history_with_ref(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.historical_body_retention")
    workspace = tmp_path / "Study"
    workspace.mkdir(parents=True)
    (workspace / "workspace.yaml").write_text("workspace_id: Study\n", encoding="utf-8")
    history_path = (
        workspace
        / "runtime"
        / "artifacts"
        / "legacy_physical_cleanup"
        / "history"
        / "20260516T125122543182Z.json"
    )
    history_path.parent.mkdir(parents=True, exist_ok=True)
    history_path.write_text(
        json.dumps(
            {
                "surface_kind": "workspace_legacy_physical_cleanup_apply",
                "mode": "apply",
                "reference_events": [{"path": f"legacy-ref-{index}", "body": "x" * 1024} for index in range(128)],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    original_sha = _sha256(history_path)

    applied = module.run_historical_body_retention(
        root=history_path,
        apply=True,
        cold_store_root=tmp_path / "cold-store",
        min_mb=0,
    )

    assert applied["status"] == "applied"
    assert applied["candidate_count"] == 1
    assert applied["candidate_samples"][0]["historical_surface_kind"] == "legacy_physical_cleanup_history_body"
    slim = json.loads(history_path.read_text(encoding="utf-8"))
    assert slim["surface_kind"] == "historical_body_retention_ref"
    assert slim["historical_surface_kind"] == "legacy_physical_cleanup_history_body"
    ref = json.loads(Path(str(history_path) + ".cold_ref.json").read_text(encoding="utf-8"))
    assert ref["original_sha256"] == original_sha
    assert Path(ref["cold_object_path"]).is_file()


def test_historical_body_retention_scoped_root_still_uses_workspace_receipt_and_cold_namespace(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.historical_body_retention")
    workspace = tmp_path / "Study"
    workspace.mkdir(parents=True)
    (workspace / "workspace.yaml").write_text("workspace_id: Study\n", encoding="utf-8")
    archive_path = (
        workspace
        / "runtime"
        / "quests"
        / "002-study"
        / "artifacts"
        / "runtime"
        / "runtime_storage_maintenance"
        / "oversized_jsonl"
        / "events.jsonl.gz"
    )
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    archive_path.write_bytes(b"jsonl-gzip-body" * 1024)

    applied = module.run_historical_body_retention(
        root=workspace / "runtime" / "quests",
        apply=True,
        cold_store_root=tmp_path / "cold-store",
        min_mb=0,
    )

    assert applied["status"] == "applied"
    assert applied["latest_receipt_path"] == str(workspace / "runtime" / "artifacts" / "historical_body_retention" / "latest.json")
    assert applied["cold_store_root"] == str(tmp_path / "cold-store" / "Study" / "historical_body_retention")
    assert applied["candidate_samples"][0]["workspace_relative_path"].startswith("runtime/quests/")
    ref = json.loads(Path(str(archive_path) + ".cold_ref.json").read_text(encoding="utf-8"))
    assert Path(ref["cold_object_path"]).is_relative_to(tmp_path / "cold-store" / "Study" / "historical_body_retention")


def test_historical_body_retention_moves_legacy_inbox_zip_without_touching_dataset_zip(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.historical_body_retention")
    workspace = tmp_path / "Study"
    inbox_zip = workspace / "archive" / "legacy_root_surfaces" / "20260607T064130Z" / "inbox" / "source.zip"
    inbox_zip.parent.mkdir(parents=True, exist_ok=True)
    inbox_zip.write_bytes(b"legacy-inbox-raw" * 1024)
    dataset_zip = workspace / "data" / "datasets" / "raw" / "source.zip"
    dataset_zip.parent.mkdir(parents=True, exist_ok=True)
    dataset_zip.write_bytes(b"dataset-asset" * 1024)
    original_sha = _sha256(inbox_zip)
    dataset_sha = _sha256(dataset_zip)

    applied = module.run_historical_body_retention(
        root=workspace,
        apply=True,
        cold_store_root=tmp_path / "cold-store",
        min_mb=0,
    )

    assert applied["status"] == "applied"
    assert applied["candidate_count"] == 1
    assert inbox_zip.is_symlink()
    assert dataset_zip.is_file()
    assert _sha256(dataset_zip) == dataset_sha
    ref = json.loads(Path(str(inbox_zip) + ".cold_ref.json").read_text(encoding="utf-8"))
    assert ref["historical_surface_kind"] == "legacy_root_inbox_raw_archive_body"
    assert ref["original_sha256"] == original_sha


def test_historical_body_retention_file_root_keeps_workspace_receipt_and_can_rewrite_symlink_ref(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.historical_body_retention")
    workspace = tmp_path / "Study"
    workspace.mkdir(parents=True)
    (workspace / "workspace.yaml").write_text("workspace_id: Study\n", encoding="utf-8")
    (workspace / "runtime" / "quests").mkdir(parents=True)
    inbox_zip = workspace / "archive" / "legacy_root_surfaces" / "20260607T064130Z" / "inbox" / "source.zip"
    inbox_zip.parent.mkdir(parents=True, exist_ok=True)
    inbox_zip.write_bytes(b"legacy-inbox-raw" * 1024)

    first = module.run_historical_body_retention(
        root=inbox_zip,
        apply=True,
        cold_store_root=tmp_path / "cold-store",
        min_mb=0,
    )
    second = module.run_historical_body_retention(
        root=inbox_zip,
        apply=True,
        cold_store_root=tmp_path / "cold-store",
        min_mb=0,
    )

    assert first["status"] == "applied"
    assert first["latest_receipt_path"] == str(workspace / "runtime" / "artifacts" / "historical_body_retention" / "latest.json")
    assert first["candidate_samples"][0]["workspace_relative_path"] == (
        "archive/legacy_root_surfaces/20260607T064130Z/inbox/source.zip"
    )
    assert first["moved_count"] == 1
    assert second["status"] == "applied"
    assert second["already_retained_count"] == 1
    assert second["latest_receipt_path"] == str(workspace / "runtime" / "artifacts" / "historical_body_retention" / "latest.json")
    assert second["candidate_samples"][0]["workspace_relative_path"] == (
        "archive/legacy_root_surfaces/20260607T064130Z/inbox/source.zip"
    )
    ref = json.loads(Path(str(inbox_zip) + ".cold_ref.json").read_text(encoding="utf-8"))
    assert ref["workspace_relative_path"] == "archive/legacy_root_surfaces/20260607T064130Z/inbox/source.zip"


def test_historical_body_retention_cli_dispatches_controller(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    called: dict[str, object] = {}

    def fake_run_historical_body_retention(
        *,
        root: Path,
        apply: bool,
        cold_store_root: Path,
        min_mb: int,
        max_files: int | None,
    ) -> dict[str, object]:
        called["root"] = root
        called["apply"] = apply
        called["cold_store_root"] = cold_store_root
        called["min_mb"] = min_mb
        called["max_files"] = max_files
        return {"surface_kind": "historical_body_retention", "status": "applied"}

    monkeypatch.setattr(
        cli.historical_body_retention,
        "run_historical_body_retention",
        fake_run_historical_body_retention,
    )

    exit_code = cli.main(
        [
            "historical-body-retention",
            "--root",
            str(tmp_path / "workspace"),
            "--apply",
            "--cold-store-root",
            str(tmp_path / "cold-store"),
            "--min-mb",
            "3",
            "--max-files",
            "9",
        ]
    )

    assert exit_code == 0
    assert called == {
        "root": tmp_path / "workspace",
        "apply": True,
        "cold_store_root": tmp_path / "cold-store",
        "min_mb": 3,
        "max_files": 9,
    }
    assert json.loads(capsys.readouterr().out)["status"] == "applied"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
