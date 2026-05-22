from __future__ import annotations

import importlib
import json
from pathlib import Path
import subprocess


def test_runtime_lifecycle_migration_ledger_is_contract_valid_and_writes_pointer(tmp_path: Path) -> None:
    lifecycle_store = importlib.import_module("med_autoscience.runtime_protocol.lifecycle_refs_adapter")
    migration = importlib.import_module("med_autoscience.runtime_protocol.runtime_lifecycle_migration")
    contract = importlib.import_module("med_autoscience.runtime_protocol.runtime_lifecycle_contract")
    workspace_root = tmp_path / "workspace"
    workspace_root.mkdir()
    subprocess.run(["git", "init"], cwd=workspace_root, check=True, text=True, capture_output=True)
    (workspace_root / ".gitignore").write_text("*.sqlite\n*.sqlite-wal\n*.sqlite-shm\n", encoding="utf-8")
    audit_path = workspace_root / "storage_audit" / "latest.json"
    report_path = workspace_root / "storage_audit" / "20260505T000000Z.json"
    report = {
        "schema_version": 1,
        "recorded_at": "2026-05-05T00:00:00+00:00",
        "workspace_root": str(workspace_root),
        "mode": "apply",
        "summary": {
            "study_count": 1,
            "estimated_release_bytes": 2048,
            "actual_release_bytes": 0,
            "runtime_total_bytes": 4096,
            "runtime_estimated_release_bytes": 2048,
            "runtime_actual_release_bytes": 1024,
            "study_artifact_total_bytes": 128,
        },
        "categories": {
            "runtime": {
                "category": "runtime",
                "bytes": 4096,
                "candidate_action": "restore-proof-compaction",
                "estimated_release_bytes": 2048,
                "actual_release_bytes": 1024,
                "studies": [
                    {
                        "study_id": "001-risk",
                        "quest_id": "quest-001",
                        "quest_root": str(workspace_root / "ops" / "runtime" / "quests" / "quest-001"),
                        "status": "audited",
                        "quest_runtime": {"status": "completed", "active_run_id": None},
                        "runtime": {
                            "bytes": 4096,
                            "candidate_action": "restore-proof-compaction",
                            "estimated_release_bytes": 2048,
                            "actual_release_bytes": 1024,
                        },
                        "restore_proof_compaction": {
                            "status": "compacted",
                            "restore_proof_path": str(
                                workspace_root
                                / "ops"
                                / "runtime"
                                / "quests"
                                / "quest-001"
                                / ".ds"
                                / "cold_archive"
                                / "restore_proof_compaction"
                                / "quest-001.restore_proof.json"
                            ),
                            "archive_ref": {
                                "archive_path": str(
                                    workspace_root
                                    / "ops"
                                    / "runtime"
                                    / "quests"
                                    / "quest-001"
                                    / ".ds"
                                    / "cold_archive"
                                    / "restore_proof_compaction"
                                    / "quest-001.tar.gz"
                                ),
                                "sha256": "abc123",
                                "source_file_count": 12,
                            },
                            "restore_proof": {
                                "status": "verified",
                                "archive_sha256": "abc123",
                                "source_file_count": 12,
                                "verified_file_count": 12,
                            },
                        },
                    }
                ],
            },
            "cache": {
                "category": "cache",
                "bytes": 512,
                "candidate_action": "delete-safe",
                "estimated_release_bytes": 256,
                "actual_release_bytes": 0,
            },
        },
        "latest_report_path": str(audit_path),
        "report_path": str(report_path),
    }
    audit_path.parent.mkdir(parents=True)
    audit_path.write_text(json.dumps(report), encoding="utf-8")
    report_path.write_text(json.dumps(report), encoding="utf-8")
    lifecycle_store.record_workspace_storage_audit(
        workspace_root=workspace_root,
        report=report,
        report_path=report_path,
        latest_report_path=audit_path,
    )

    ledger = migration.build_migration_ledger(
        workspace_root=workspace_root,
        mode="dry_run",
        workspace_classification="stopped_cold",
        migration_run_id="run-ledger-001",
        skipped_reasons=(),
        write=True,
        write_lifecycle_export=True,
    )

    assert contract.validate_migration_ledger(ledger)["ok"] is True
    assert ledger["validation"]["ok"] is True
    assert ledger["bucket_baseline"]["summary"]["runtime_total_bytes"] == 4096
    assert ledger["quest_classifications"][0]["classification"] == "stopped_cold"
    assert ledger["planned_actions"][0]["bucket_name"] == "cache"
    assert ledger["applied_actions"][0]["bucket_name"] == "runtime"
    assert ledger["restore_proofs"] == [
        {
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "quest_root": str(workspace_root / "ops" / "runtime" / "quests" / "quest-001"),
            "status": "verified",
            "restore_proof_path": str(
                workspace_root
                / "ops"
                / "runtime"
                / "quests"
                / "quest-001"
                / ".ds"
                / "cold_archive"
                / "restore_proof_compaction"
                / "quest-001.restore_proof.json"
            ),
            "archive_path": str(
                workspace_root
                / "ops"
                / "runtime"
                / "quests"
                / "quest-001"
                / ".ds"
                / "cold_archive"
                / "restore_proof_compaction"
                / "quest-001.tar.gz"
            ),
            "archive_sha256": "abc123",
            "source_file_count": 12,
            "verified_file_count": 12,
        }
    ]
    assert ledger["git_tracking_check"]["sidecar_gitignore_ok"] is True
    assert ledger["lifecycle_exports"][0]["legacy_restore_import_used"] is False
    run_path = Path(ledger["ledger_paths"]["ledger_path"])
    latest_path = Path(ledger["ledger_paths"]["latest_path"])
    assert json.loads(run_path.read_text(encoding="utf-8"))["migration_run_id"] == "run-ledger-001"
    latest = json.loads(latest_path.read_text(encoding="utf-8"))
    assert latest["surface_kind"] == "runtime_lifecycle_migration_latest"
    assert latest["ledger_path"] == str(run_path)


def test_runtime_lifecycle_ledger_cli_dispatches_migration_builder(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    workspace_root = tmp_path / "workspace"
    output_root = tmp_path / "out"
    called: dict[str, object] = {}

    def fake_build_migration_ledger(
        *,
        workspace_root: Path,
        mode: str,
        workspace_classification: str,
        migration_run_id: str | None,
        quest_git_cutover_status=None,
        quest_git_inventory=(),
        legacy_import_retirement=None,
        skipped_reasons: tuple[str, ...],
        next_required_action: str | None,
        output_root: Path | None,
        write: bool,
        write_lifecycle_export: bool,
    ) -> dict[str, object]:
        called.update(
            {
                "workspace_root": workspace_root,
                "mode": mode,
                "workspace_classification": workspace_classification,
                "migration_run_id": migration_run_id,
                "skipped_reasons": skipped_reasons,
                "next_required_action": next_required_action,
                "output_root": output_root,
                "write": write,
                "write_lifecycle_export": write_lifecycle_export,
            }
        )
        return {
            "surface_kind": "runtime_lifecycle_migration_ledger",
            "migration_run_id": migration_run_id,
            "validation": {"ok": True},
        }

    monkeypatch.setattr(cli.runtime_lifecycle_migration, "build_migration_ledger", fake_build_migration_ledger)

    exit_code = cli.main(
        [
            "runtime",
            "lifecycle-ledger",
            "--workspace-root",
            str(workspace_root),
            "--mode",
            "dry_run",
            "--workspace-classification",
            "pinned_or_unknown_owner",
            "--migration-run-id",
            "ledger-001",
            "--skipped-reason",
            "dirty_workspace",
            "--next-required-action",
            "review owner boundary",
            "--output-root",
            str(output_root),
            "--write",
            "--write-lifecycle-export",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called == {
        "workspace_root": workspace_root,
        "mode": "dry_run",
        "workspace_classification": "pinned_or_unknown_owner",
        "migration_run_id": "ledger-001",
        "skipped_reasons": ("dirty_workspace",),
        "next_required_action": "review owner boundary",
        "output_root": output_root,
        "write": True,
        "write_lifecycle_export": True,
    }
    assert json.loads(captured.out)["validation"]["ok"] is True


def test_runtime_lifecycle_quest_git_inventory_cli_dispatches_builder(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    workspace_root = tmp_path / "workspace"
    called: dict[str, object] = {}

    def fake_build_quest_git_inventory(*, workspace_root: Path) -> dict[str, object]:
        called["workspace_root"] = workspace_root
        return {
            "surface_kind": "quest_git_inventory",
            "summary": {"item_count": 0, "active_git_count": 0, "retired_count": 0, "pending_count": 0},
            "items": [],
        }

    monkeypatch.setattr(cli.runtime_lifecycle_migration, "build_quest_git_inventory", fake_build_quest_git_inventory)

    exit_code = cli.main(
        [
            "runtime",
            "lifecycle-quest-git-inventory",
            "--workspace-root",
            str(workspace_root),
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called == {"workspace_root": workspace_root}
    payload = json.loads(captured.out)
    assert payload["surface_kind"] == "quest_git_inventory"
    assert payload["summary"]["item_count"] == 0


def test_quest_git_inventory_discovers_active_legacy_git_roots(tmp_path: Path) -> None:
    migration = importlib.import_module("med_autoscience.runtime_protocol.runtime_lifecycle_migration")
    workspace_root = tmp_path / "workspace"
    workspace_root.mkdir()
    runtime_git = workspace_root / "runtime" / "quests" / "quest-runtime" / ".git"
    mds_git = workspace_root / "ops" / "med-deepscientist" / "runtime" / "quests" / "quest-mds" / ".git"
    worktree_git = workspace_root / ".ds" / "worktrees" / "quest-worktree" / ".git"
    runtime_git.mkdir(parents=True)
    mds_git.mkdir(parents=True)
    worktree_git.parent.mkdir(parents=True)
    worktree_git.write_text("gitdir: /tmp/example.git\n", encoding="utf-8")

    inventory = migration.build_quest_git_inventory(workspace_root=workspace_root)

    assert inventory["surface_kind"] == "quest_git_inventory"
    assert inventory["summary"] == {
        "item_count": 3,
        "active_git_count": 3,
        "retired_count": 0,
        "pending_count": 3,
    }
    items_by_quest = {item["quest_id"]: item for item in inventory["items"]}
    assert items_by_quest["quest-runtime"]["source"] == "workspace_runtime_quests"
    assert items_by_quest["quest-mds"]["source"] == "med_deepscientist_runtime_quests"
    assert items_by_quest["quest-worktree"]["source"] == "legacy_ds_worktrees"
    assert items_by_quest["quest-runtime"]["status"] == "pending"
    assert items_by_quest["quest-runtime"]["action"] == "audit_only"
    assert items_by_quest["quest-runtime"]["active_path"] == str(runtime_git.parent)
    assert items_by_quest["quest-runtime"]["git_path"] == str(runtime_git)
    assert items_by_quest["quest-runtime"]["quest_git_present_in_active_path"] is True
    assert items_by_quest["quest-runtime"]["quest_git_active_path_retired"] is False
    assert items_by_quest["quest-runtime"]["skipped_reason"] == "active_quest_git_present"


def test_runtime_lifecycle_ledger_auto_inventory_blocks_verified_cutover_for_active_git(tmp_path: Path) -> None:
    migration = importlib.import_module("med_autoscience.runtime_protocol.runtime_lifecycle_migration")
    workspace_root = tmp_path / "workspace"
    workspace_root.mkdir()
    subprocess.run(["git", "init"], cwd=workspace_root, check=True, text=True, capture_output=True)
    (workspace_root / ".gitignore").write_text("*.sqlite\n*.sqlite-wal\n*.sqlite-shm\n", encoding="utf-8")
    subprocess.run(["git", "add", ".gitignore"], cwd=workspace_root, check=True, text=True, capture_output=True)
    subprocess.run(
        ["git", "-c", "user.name=MAS Test", "-c", "user.email=mas@example.test", "commit", "-m", "init"],
        cwd=workspace_root,
        check=True,
        text=True,
        capture_output=True,
    )
    quest_git = workspace_root / "runtime" / "quests" / "quest-active" / ".git"
    quest_git.mkdir(parents=True)

    ledger = migration.build_migration_ledger(
        workspace_root=workspace_root,
        mode="verify",
        workspace_classification="parked_controller_stop",
        quest_git_cutover_status={"status": "verified"},
    )

    cutover = ledger["git_lifecycle_cutover"]
    assert cutover["status"] == "pending"
    assert cutover["quest_git_active_path_retired"] is False
    assert cutover["unresolved_active_git_paths"][0]["quest_id"] == "quest-active"
    assert cutover["unresolved_active_git_paths"][0]["active_path"] == str(quest_git.parent)
    assert cutover["unresolved_active_git_paths"][0]["git_path"] == str(quest_git)
    assert cutover["unresolved_active_git_paths"][0]["skipped_reason"] == "active_quest_git_present"
    assert {
        "scope": "quest_git",
        "quest_id": "quest-active",
        "study_id": None,
        "reason": "active_quest_git_present",
        "action": "audit_only",
    } in ledger["skipped_items"]


def test_quest_git_cutover_dry_run_plans_only_safe_stopped_quests(tmp_path: Path) -> None:
    migration = importlib.import_module("med_autoscience.runtime_protocol.runtime_lifecycle_migration")
    workspace_root = tmp_path / "workspace"
    safe_git = workspace_root / "runtime" / "quests" / "quest-stopped" / ".git"
    live_git = workspace_root / "runtime" / "quests" / "quest-active" / ".git"
    safe_git.mkdir(parents=True)
    live_git.mkdir(parents=True)
    (safe_git.parent / ".ds").mkdir()
    (live_git.parent / ".ds").mkdir()
    (safe_git.parent / ".ds" / "runtime_state.json").write_text(
        json.dumps({"status": "stopped", "active_run_id": None, "worker_running": False}),
        encoding="utf-8",
    )
    (live_git.parent / ".ds" / "runtime_state.json").write_text(
        json.dumps({"status": "active", "active_run_id": None, "worker_running": False}),
        encoding="utf-8",
    )

    result = migration.cutover_quest_git_active_paths(workspace_root=workspace_root, mode="dry_run")

    items_by_quest = {item["quest_id"]: item for item in result["items"]}
    assert items_by_quest["quest-stopped"]["status"] == "planned"
    assert items_by_quest["quest-stopped"]["action"] == "archive_then_remove_active_git"
    assert items_by_quest["quest-stopped"]["gate"]["reason"] == "controller_operator_safe_state"
    assert items_by_quest["quest-active"]["status"] == "skipped"
    assert items_by_quest["quest-active"]["skipped_reason"] == "live_or_active_quest"
    assert safe_git.exists()
    assert live_git.exists()
    assert result["summary"]["planned_count"] == 1
    assert result["summary"]["skipped_count"] == 1


def test_quest_git_cutover_apply_archives_and_removes_safe_active_path_git(tmp_path: Path) -> None:
    migration = importlib.import_module("med_autoscience.runtime_protocol.runtime_lifecycle_migration")
    workspace_root = tmp_path / "workspace"
    quest_git = workspace_root / "runtime" / "quests" / "quest-paused" / ".git"
    quest_git.mkdir(parents=True)
    (quest_git / "HEAD").write_text("ref: refs/heads/main\n", encoding="utf-8")
    (quest_git.parent / ".ds").mkdir()
    (quest_git.parent / ".ds" / "runtime_state.json").write_text(
        json.dumps({"status": "paused", "active_run_id": None, "worker_running": False}),
        encoding="utf-8",
    )

    result = migration.cutover_quest_git_active_paths(
        workspace_root=workspace_root,
        mode="apply",
        migration_run_id="quest-git-cutover-test",
    )

    item = result["items"][0]
    assert item["status"] == "retired"
    assert item["action"] == "archived_and_removed_active_git"
    assert item["quest_git_active_path_retired"] is True
    assert item["quest_git_present_in_active_path_after"] is False
    assert not quest_git.exists()
    manifest_path = Path(item["archive_manifest_path"])
    archive_path = Path(item["archive_ref"])
    assert manifest_path.exists()
    assert archive_path.exists()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["restore_proof"]["status"] == "verified"
    assert manifest["restore_proof"]["active_git_removed"] is True
    assert "tar -xzf" in manifest["restore_command"]
    latest = workspace_root / "artifacts" / "runtime" / "lifecycle_migration" / "quest_git_active_path_cutover.latest.json"
    assert json.loads(latest.read_text(encoding="utf-8"))["status"] == "verified"

    ledger = migration.build_migration_ledger(
        workspace_root=workspace_root,
        mode="verify",
        workspace_classification="stopped_cold",
    )

    cutover = ledger["git_lifecycle_cutover"]
    assert cutover["status"] == "verified"
    assert cutover["quest_git_active_path_retired"] is True
    assert cutover["unresolved_active_git_paths"] == []
    inventory_item = cutover["quest_git_inventory"][0]
    assert inventory_item["quest_id"] == "quest-paused"
    assert inventory_item["quest_git_present_in_active_path"] is False
    assert inventory_item["quest_git_active_path_retired"] is True
    assert inventory_item["archive_ref"] == str(archive_path)
    assert inventory_item["restore_proof_path"] == str(manifest_path)
    assert ledger["quest_git_cutover_record"]["migration_run_id"] == "quest-git-cutover-test"


def test_quest_git_cutover_apply_keeps_unknown_runtime_state_audit_only(tmp_path: Path) -> None:
    migration = importlib.import_module("med_autoscience.runtime_protocol.runtime_lifecycle_migration")
    workspace_root = tmp_path / "workspace"
    quest_git = workspace_root / "runtime" / "quests" / "quest-unknown" / ".git"
    quest_git.mkdir(parents=True)

    result = migration.cutover_quest_git_active_paths(workspace_root=workspace_root, mode="apply")

    item = result["items"][0]
    assert item["status"] == "skipped"
    assert item["action"] == "audit_only"
    assert item["skipped_reason"] == "runtime_state_missing"
    assert item["quest_git_present_in_active_path_after"] is True
    assert quest_git.exists()
    assert result["status"] == "pending"


def test_runtime_lifecycle_ledger_auto_inventory_allows_verified_cutover_with_archived_proof_refs(tmp_path: Path) -> None:
    migration = importlib.import_module("med_autoscience.runtime_protocol.runtime_lifecycle_migration")
    workspace_root = tmp_path / "workspace"
    workspace_root.mkdir()
    subprocess.run(["git", "init"], cwd=workspace_root, check=True, text=True, capture_output=True)
    (workspace_root / ".gitignore").write_text("*.sqlite\n*.sqlite-wal\n*.sqlite-shm\n", encoding="utf-8")
    subprocess.run(["git", "add", ".gitignore"], cwd=workspace_root, check=True, text=True, capture_output=True)
    subprocess.run(
        ["git", "-c", "user.name=MAS Test", "-c", "user.email=mas@example.test", "commit", "-m", "init"],
        cwd=workspace_root,
        check=True,
        text=True,
        capture_output=True,
    )
    quest_root = workspace_root / "runtime" / "quests" / "quest-retired"
    proof_path = quest_root / ".ds" / "restore_proof_archives" / "runtime_bucket_compaction" / "quest-retired.restore_proof.json"
    archive_path = proof_path.with_suffix(".tar.gz")
    audit_path = workspace_root / "storage_audit" / "latest.json"
    audit_path.parent.mkdir(parents=True)
    audit_path.write_text(
        json.dumps(
            {
                "categories": {
                    "runtime": {
                        "studies": [
                            {
                                "study_id": "001-risk",
                                "quest_id": "quest-retired",
                                "quest_root": str(quest_root),
                                "status": "audited",
                                "quest_runtime": {"status": "completed", "active_run_id": None},
                                "restore_proof_compaction": {
                                    "status": "compacted",
                                    "restore_proof_path": str(proof_path),
                                    "archive_ref": {
                                        "archive_path": str(archive_path),
                                        "sha256": "abc123",
                                        "source_file_count": 4,
                                    },
                                    "restore_proof": {
                                        "status": "verified",
                                        "archive_sha256": "abc123",
                                        "source_file_count": 4,
                                        "verified_file_count": 4,
                                    },
                                },
                            }
                        ]
                    }
                }
            }
        ),
        encoding="utf-8",
    )

    ledger = migration.build_migration_ledger(
        workspace_root=workspace_root,
        mode="verify",
        workspace_classification="stopped_cold",
        quest_git_cutover_status={"status": "verified"},
    )

    cutover = ledger["git_lifecycle_cutover"]
    assert cutover["status"] == "verified"
    assert cutover["quest_git_active_path_retired"] is True
    assert cutover["unresolved_active_git_paths"] == []
    inventory_item = cutover["quest_git_inventory"][0]
    assert inventory_item["quest_id"] == "quest-retired"
    assert inventory_item["quest_git_present_in_active_path"] is False
    assert inventory_item["quest_git_active_path_retired"] is True
    assert inventory_item["archive_ref"] == str(archive_path)
    assert inventory_item["restore_proof_path"] == str(proof_path)
    assert inventory_item["projection_equivalence"] == "verified"
    assert inventory_item["status"] == "retired"


def test_runtime_lifecycle_ledger_blocks_git_retirement_until_active_path_cutover_is_verified(tmp_path: Path) -> None:
    migration = importlib.import_module("med_autoscience.runtime_protocol.runtime_lifecycle_migration")
    workspace_root = tmp_path / "workspace"
    workspace_root.mkdir()
    subprocess.run(["git", "init"], cwd=workspace_root, check=True, text=True, capture_output=True)
    (workspace_root / ".gitignore").write_text("*.sqlite\n*.sqlite-wal\n*.sqlite-shm\n", encoding="utf-8")
    quest_git = workspace_root / "runtime" / "quests" / "quest-001" / ".git"
    quest_git.mkdir(parents=True)

    ledger = migration.build_migration_ledger(
        workspace_root=workspace_root,
        mode="dry_run",
        workspace_classification="parked_controller_stop",
        quest_git_cutover_status={"status": "pending"},
        quest_git_inventory=[
            {
                "study_id": "001-risk",
                "quest_id": "quest-001",
                "active_path": str(quest_git.parent),
                "git_path": str(quest_git),
                "quest_git_present_in_active_path": True,
                "quest_git_active_path_retired": False,
            }
        ],
        legacy_import_retirement={
            "current_projects_cutover_verified": False,
            "old_readers_equivalent": True,
            "restore_import_diagnostic_retained": True,
            "default_legacy_reader_removed": False,
            "default_callers": ["runtime_watch"],
        },
    )

    cutover = ledger["git_lifecycle_cutover"]
    assert cutover["status"] == "pending"
    assert cutover["quest_git_active_path_retired"] is False
    assert cutover["unresolved_active_git_paths"][0]["quest_id"] == "quest-001"
    assert cutover["legacy_import_retirement"]["allowed"] is False
    assert "Q1-Q5" in ledger["next_required_action"]


def test_runtime_lifecycle_ledger_allows_legacy_import_retirement_only_after_verified_cutover(tmp_path: Path) -> None:
    migration = importlib.import_module("med_autoscience.runtime_protocol.runtime_lifecycle_migration")
    workspace_root = tmp_path / "workspace"
    workspace_root.mkdir()
    subprocess.run(["git", "init"], cwd=workspace_root, check=True, text=True, capture_output=True)
    (workspace_root / ".gitignore").write_text("*.sqlite\n*.sqlite-wal\n*.sqlite-shm\n", encoding="utf-8")
    subprocess.run(["git", "add", ".gitignore"], cwd=workspace_root, check=True, text=True, capture_output=True)
    subprocess.run(
        ["git", "-c", "user.name=MAS Test", "-c", "user.email=mas@example.test", "commit", "-m", "init"],
        cwd=workspace_root,
        check=True,
        text=True,
        capture_output=True,
    )

    ledger = migration.build_migration_ledger(
        workspace_root=workspace_root,
        mode="verify",
        workspace_classification="stopped_cold",
        quest_git_cutover_status={"status": "verified"},
        quest_git_inventory=[
            {
                "study_id": "001-risk",
                "quest_id": "quest-001",
                "active_path": str(workspace_root / "runtime" / "quests" / "quest-001"),
                "quest_git_present_in_active_path": False,
                "quest_git_active_path_retired": True,
                "archive_ref": "runtime/archives/quest-001.git.bundle",
                "projection_equivalence": "verified",
            }
        ],
        legacy_import_retirement={
            "current_projects_cutover_verified": True,
            "old_readers_equivalent": True,
            "restore_import_diagnostic_retained": True,
            "default_legacy_reader_removed": True,
            "default_callers": ["legacy_restore_import_diagnostic"],
        },
    )

    cutover = ledger["git_lifecycle_cutover"]
    assert cutover["status"] == "verified"
    assert cutover["quest_git_active_path_retired"] is True
    assert cutover["unresolved_active_git_paths"] == []
    assert cutover["legacy_import_retirement"]["allowed"] is True
    assert ledger["next_required_action"] == "Run storage-audit dry-run to create the runtime lifecycle SQLite refs index."


def test_legacy_import_retirement_validation_requires_restore_import_diagnostic() -> None:
    migration = importlib.import_module("med_autoscience.runtime_protocol.runtime_lifecycle_migration")

    result = migration.validate_legacy_import_retirement(
        {
            "current_projects_cutover_verified": True,
            "old_readers_equivalent": True,
            "restore_import_diagnostic_retained": False,
            "default_legacy_reader_removed": True,
            "default_callers": ["runtime_watch"],
        }
    )

    assert result == {
        "allowed": False,
        "missing_true_fields": ["restore_import_diagnostic_retained"],
        "disallowed_default_callers": ["runtime_watch"],
        "retained_scope": "legacy_restore_import_diagnostic",
    }
