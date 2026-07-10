from __future__ import annotations

import hashlib
import importlib
import json
from pathlib import Path

import pytest


def _workspace(tmp_path: Path) -> Path:
    workspace = tmp_path / "Study"
    workspace.mkdir()
    (workspace / "workspace.yaml").write_text("workspace_id: Study\n", encoding="utf-8")
    (workspace / "runtime" / "quests").mkdir(parents=True)
    return workspace


def test_historical_body_retention_preserves_hash_ref_and_latest_alias(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.historical_body_retention")
    workspace = _workspace(tmp_path)
    audit_root = workspace / "archive" / "legacy_root_surfaces" / "20260607T000000Z" / "storage_audit"
    audit_path = audit_root / "20260505T090041Z.json"
    audit_path.parent.mkdir(parents=True)
    audit_path.write_text(
        json.dumps({"surface_kind": "workspace_storage_audit", "files": ["x" * 1024] * 64}),
        encoding="utf-8",
    )
    latest_path = audit_root / "latest.json"
    latest_path.write_text('{"status": "current"}\n', encoding="utf-8")
    original_sha = _sha256(audit_path)

    planned = module.run_historical_body_retention(
        root=workspace,
        apply=False,
        cold_store_root=tmp_path / "cold-store",
        min_mb=0,
    )
    applied = module.run_historical_body_retention(
        root=workspace,
        apply=True,
        cold_store_root=tmp_path / "cold-store",
        min_mb=0,
    )

    assert planned["status"] == "planned"
    assert applied["status"] == "applied"
    assert applied["moved_count"] == 1
    slim = json.loads(audit_path.read_text(encoding="utf-8"))
    assert slim["surface_kind"] == "historical_body_retention_ref"
    assert slim["original_sha256"] == original_sha
    assert latest_path.read_text(encoding="utf-8") == '{"status": "current"}\n'
    ref = json.loads(Path(f"{audit_path}.cold_ref.json").read_text(encoding="utf-8"))
    assert _sha256(Path(ref["cold_object_path"])) == original_sha


def test_historical_body_retention_moves_binary_without_touching_data_assets(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.historical_body_retention")
    workspace = _workspace(tmp_path)
    archive_path = (
        workspace
        / "runtime"
        / "artifacts"
        / "lifecycle_migration"
        / "quest-git-cutover"
        / "quest_git_archives"
        / "002-study.git.tar.gz"
    )
    archive_path.parent.mkdir(parents=True)
    archive_path.write_bytes(b"git-archive-body" * 1024)
    data_asset = workspace / "data" / "datasets" / "raw" / "source.zip"
    data_asset.parent.mkdir(parents=True)
    data_asset.write_bytes(b"do-not-touch" * 1024)
    archive_sha = _sha256(archive_path)
    data_sha = _sha256(data_asset)

    applied = module.run_historical_body_retention(
        root=workspace,
        apply=True,
        cold_store_root=tmp_path / "cold-store",
        min_mb=0,
    )

    assert applied["status"] == "applied"
    assert applied["candidate_count"] == 1
    assert archive_path.is_symlink()
    ref = json.loads(Path(f"{archive_path}.cold_ref.json").read_text(encoding="utf-8"))
    assert ref["original_sha256"] == archive_sha
    assert _sha256(data_asset) == data_sha


@pytest.mark.parametrize(
    ("relative_path", "surface_kind", "expected_kind"),
    [
        (
            "runtime/archives/legacy_mds/20260516T123324Z/med-deepscientist/events.jsonl.gz",
            None,
            "legacy_mds_archive_body",
        ),
        (
            "runtime/quests/002-study/artifacts/runtime/runtime_storage_maintenance/oversized_jsonl/events.jsonl.gz",
            None,
            "oversized_runtime_jsonl_archive_body",
        ),
        (
            "runtime/artifacts/legacy_physical_cleanup/history/20260516T125122Z.json",
            "workspace_legacy_physical_cleanup_apply",
            "legacy_physical_cleanup_history_body",
        ),
        (
            "archive/legacy_root_surfaces/20260607T064130Z/storage_audit/latest.json",
            "workspace_storage_audit",
            "legacy_root_storage_audit_latest_json",
        ),
        (
            "runtime/artifacts/legacy_physical_cleanup/latest.json",
            "workspace_legacy_physical_cleanup_plan",
            "legacy_physical_cleanup_latest_body",
        ),
        (
            "studies/002-study/artifacts/runtime/runtime_storage_maintenance/20260501T081152Z.json",
            "runtime_storage_maintenance",
            "runtime_storage_maintenance_report_body",
        ),
        (
            "archive/legacy_root_surfaces/20260607T064130Z/inbox/source.zip",
            None,
            "legacy_root_inbox_raw_archive_body",
        ),
        ("data/datasets/raw/source.zip", None, None),
    ],
)
def test_historical_body_retention_classifies_only_supported_historical_paths(
    tmp_path: Path,
    relative_path: str,
    surface_kind: str | None,
    expected_kind: str | None,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.historical_body_retention")
    workspace = _workspace(tmp_path)
    path = workspace / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    if surface_kind is None:
        path.write_bytes(b"body")
    else:
        path.write_text(json.dumps({"surface_kind": surface_kind}), encoding="utf-8")

    assert module._historical_surface_kind(root=workspace, path=path) == expected_kind


def test_historical_body_retention_file_root_is_workspace_scoped_and_idempotent(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.historical_body_retention")
    workspace = _workspace(tmp_path)
    inbox_zip = workspace / "archive" / "legacy_root_surfaces" / "20260607T064130Z" / "inbox" / "source.zip"
    inbox_zip.parent.mkdir(parents=True)
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

    receipt = workspace / "runtime" / "artifacts" / "historical_body_retention" / "latest.json"
    assert first["status"] == second["status"] == "applied"
    assert first["moved_count"] == 1
    assert second["already_retained_count"] == 1
    assert first["latest_receipt_path"] == str(receipt)
    assert first["cold_store_root"] == str(
        tmp_path / "cold-store" / "Study" / "historical_body_retention"
    )


def test_historical_body_retention_cli_dispatches_controller(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    called: dict[str, object] = {}

    def fake_run(**kwargs: object) -> dict[str, object]:
        called.update(kwargs)
        return {"surface_kind": "historical_body_retention", "status": "applied"}

    monkeypatch.setattr(cli.historical_body_retention, "run_historical_body_retention", fake_run)
    root = tmp_path / "workspace"
    cold_store = tmp_path / "cold-store"

    exit_code = cli.main(
        [
            "historical-body-retention",
            "--root",
            str(root),
            "--apply",
            "--cold-store-root",
            str(cold_store),
            "--min-mb",
            "3",
            "--max-files",
            "9",
        ]
    )

    assert exit_code == 0
    assert called == {
        "root": root,
        "apply": True,
        "cold_store_root": cold_store,
        "min_mb": 3,
        "max_files": 9,
    }
    assert json.loads(capsys.readouterr().out)["status"] == "applied"


def _sha256(path: Path) -> str:
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()
