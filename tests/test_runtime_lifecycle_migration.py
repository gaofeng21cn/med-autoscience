from __future__ import annotations

import importlib
import json
from pathlib import Path
import subprocess


def test_runtime_lifecycle_migration_ledger_is_contract_valid_and_writes_pointer(tmp_path: Path) -> None:
    lifecycle_store = importlib.import_module("med_autoscience.runtime_protocol.runtime_lifecycle_store")
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
        write_compat_export=True,
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
    assert ledger["compatibility_exports"][0]["compatibility_fallback_used"] is False
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
        skipped_reasons: tuple[str, ...],
        next_required_action: str | None,
        output_root: Path | None,
        write: bool,
        write_compat_export: bool,
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
                "write_compat_export": write_compat_export,
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
            "--write-compat-export",
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
        "write_compat_export": True,
    }
    assert json.loads(captured.out)["validation"]["ok"] is True
