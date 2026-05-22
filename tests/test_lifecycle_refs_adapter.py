from __future__ import annotations

import importlib
import json
from pathlib import Path
import sqlite3
import subprocess


def _expected_table_counts(**overrides: int) -> dict[str, int]:
    tables = {
        "watch_states": 0,
        "runtime_reports": 0,
        "workspace_storage_audits": 0,
        "lineage_nodes": 0,
        "lineage_edges": 0,
        "workspace_allocations": 0,
        "runtime_snapshots": 0,
        "snapshot_file_refs": 0,
        "revision_diffs": 0,
        "canvas_projection": 0,
        "runtime_events": 0,
        "archive_refs": 0,
        "study_macro_state_snapshots": 0,
        "owner_route_receipts": 0,
        "dispatch_receipts": 0,
        "turn_receipts": 0,
        "paper_work_unit_receipts": 0,
        "surface_refs": 0,
        "report_index": 0,
    }
    tables.update(overrides)
    return tables


def test_report_store_indexes_watch_state_and_reports_without_changing_file_surfaces(tmp_path: Path) -> None:
    report_store = importlib.import_module("med_autoscience.runtime_protocol.report_store")
    lifecycle_store = importlib.import_module("med_autoscience.runtime_protocol.lifecycle_refs_adapter")
    quest_root = tmp_path / "runtime" / "quests" / "q001"
    state = {"schema_version": 1, "updated_at": "2026-05-05T00:00:00+00:00", "controllers": {"gate": {}}}
    report = {
        "schema_version": 1,
        "scanned_at": "2026-05-05T00:00:00+00:00",
        "quest_status": "running",
    }

    report_store.save_watch_state(quest_root, state)
    json_path, md_path = report_store.write_timestamped_report(
        quest_root=quest_root,
        report_group="runtime_watch",
        timestamp="2026-05-05T00:00:00+00:00",
        report=report,
        markdown="# Runtime Watch\n",
    )

    assert json.loads((quest_root / "artifacts" / "reports" / "runtime_watch" / "state.json").read_text()) == state
    assert json.loads((quest_root / "artifacts" / "reports" / "runtime_watch" / "latest.json").read_text()) == report
    assert md_path.read_text(encoding="utf-8") == "# Runtime Watch\n"
    db_path = lifecycle_store.quest_lifecycle_store_path(quest_root)
    assert db_path.is_file()
    with sqlite3.connect(db_path) as conn:
        watch_row = conn.execute(
            "SELECT updated_at, payload_json FROM watch_states WHERE quest_root = ?",
            (str(quest_root.resolve()),),
        ).fetchone()
        report_row = conn.execute(
            """
            SELECT report_group, timestamp, status, json_path, md_path
            FROM runtime_reports
            WHERE quest_root = ?
            """,
            (str(quest_root.resolve()),),
        ).fetchone()

    assert watch_row[0] == "2026-05-05T00:00:00+00:00"
    assert json.loads(watch_row[1]) == state
    assert report_row == (
        "runtime_watch",
        "2026-05-05T00:00:00+00:00",
        "running",
        str(json_path.resolve()),
        str(md_path.resolve()),
    )
    assert lifecycle_store.inspect_lifecycle_store(db_path)["tables"] == _expected_table_counts(
        watch_states=1,
        runtime_reports=1,
        report_index=1,
    )
    with sqlite3.connect(db_path) as conn:
        report_index_row = conn.execute(
            """
            SELECT object_scope, report_group, timestamp, status, json_path, latest_json_path, latest_md_path
            FROM report_index
            WHERE object_root = ?
            """,
            (str(quest_root.resolve()),),
        ).fetchone()

    assert report_index_row == (
        "quest",
        "runtime_watch",
        "2026-05-05T00:00:00+00:00",
        "running",
        str(json_path.resolve()),
        str((quest_root / "artifacts" / "reports" / "runtime_watch" / "latest.json").resolve()),
        str((quest_root / "artifacts" / "reports" / "runtime_watch" / "latest.md").resolve()),
    )


def test_workspace_storage_audit_indexes_summary_in_workspace_lifecycle_store(tmp_path: Path) -> None:
    lifecycle_store = importlib.import_module("med_autoscience.runtime_protocol.lifecycle_refs_adapter")
    runtime_storage = importlib.import_module("med_autoscience.controllers.runtime_storage_maintenance")
    profile = importlib.import_module("tests.study_runtime_test_helpers").make_profile(tmp_path)

    result = runtime_storage.audit_workspace_storage(profile=profile, all_studies=True, apply=False)

    db_path = lifecycle_store.workspace_lifecycle_store_path(profile.workspace_root)
    assert result["runtime_lifecycle_index"] == {
        "surface_kind": "lifecycle_refs_sqlite_index",
        "schema_version": 1,
        "status": "indexed",
        "scope": "workspace",
        "db_path": str(db_path),
        "indexed_table": "workspace_storage_audits",
        "indexed_count": 1,
    }
    assert json.loads(Path(result["latest_report_path"]).read_text(encoding="utf-8"))["runtime_lifecycle_index"] == result[
        "runtime_lifecycle_index"
    ]
    with sqlite3.connect(db_path) as conn:
        row = conn.execute(
            """
            SELECT mode, study_count, estimated_release_bytes, actual_release_bytes,
                   runtime_total_bytes, study_artifact_total_bytes, summary_json, payload_json
            FROM workspace_storage_audits
            WHERE workspace_root = ?
            """,
            (str(profile.workspace_root.resolve()),),
        ).fetchone()

    assert row[0] == "dry-run"
    assert row[1] == result["summary"]["study_count"]
    assert row[2] == result["summary"]["estimated_release_bytes"]
    assert row[3] == 0
    assert row[4] == result["summary"]["runtime_total_bytes"]
    assert row[5] == result["summary"]["study_artifact_total_bytes"]
    assert json.loads(row[6]) == result["summary"]
    indexed_payload = json.loads(row[7])
    assert indexed_payload["projection_policy"] == "compact_sqlite_index_full_report_in_file_authority"
    assert indexed_payload["source_report_path"] == str(Path(result["report_path"]).resolve())
    assert "categories" not in indexed_payload
    assert lifecycle_store.inspect_lifecycle_store(db_path)["tables"] == _expected_table_counts(
        workspace_storage_audits=1,
        report_index=1,
    )


def test_workspace_storage_audit_indexes_compact_payload_for_large_reports(tmp_path: Path) -> None:
    lifecycle_store = importlib.import_module("med_autoscience.runtime_protocol.lifecycle_refs_adapter")
    workspace_root = tmp_path / "workspace"
    report_path = workspace_root / "storage_audit" / "20260505T000000Z.json"
    latest_path = workspace_root / "storage_audit" / "latest.json"
    large_report = {
        "schema_version": 1,
        "recorded_at": "2026-05-05T00:00:00+00:00",
        "workspace_root": str(workspace_root),
        "mode": "dry-run",
        "selection": {"restore_proof_buckets": ["cold_archive"]},
        "summary": {
            "study_count": 1,
            "estimated_release_bytes": 0,
            "actual_release_bytes": 0,
            "runtime_total_bytes": 1,
            "study_artifact_total_bytes": 0,
        },
        "categories": {
            "runtime": {
                "category": "runtime",
                "bytes": 1,
                "candidate_action": "restore-proof-compaction",
                "estimated_release_bytes": 0,
                "actual_release_bytes": 0,
                "studies": [
                    {
                        "study_id": "001-risk",
                        "quest_id": "quest-001",
                        "quest_root": str(workspace_root / "runtime" / "quests" / "quest-001"),
                        "status": "audited",
                        "quest_runtime": {"status": "paused", "active_run_id": None},
                        "runtime": {
                            "candidate_action": "restore-proof-compaction",
                            "estimated_release_bytes": 0,
                            "actual_release_bytes": 0,
                            "huge_debug_blob": "x" * 1_000_000,
                        },
                    }
                ],
            }
        },
    }

    lifecycle_store.record_workspace_storage_audit(
        workspace_root=workspace_root,
        report=large_report,
        report_path=report_path,
        latest_report_path=latest_path,
    )

    db_path = lifecycle_store.workspace_lifecycle_store_path(workspace_root)
    with sqlite3.connect(db_path) as conn:
        payload_json = conn.execute("SELECT payload_json FROM workspace_storage_audits").fetchone()[0]
    indexed_payload = json.loads(payload_json)
    assert len(payload_json) < 20_000
    assert indexed_payload["runtime_projection"]["studies"][0]["study_id"] == "001-risk"
    assert "huge_debug_blob" not in payload_json


def test_lifecycle_store_fails_closed_when_sqlite_refs_index_is_git_tracked(tmp_path: Path) -> None:
    lifecycle_store = importlib.import_module("med_autoscience.runtime_protocol.lifecycle_refs_adapter")
    repo_root = tmp_path / "workspace"
    repo_root.mkdir()
    subprocess.run(["git", "init"], cwd=repo_root, check=True, text=True, capture_output=True)
    db_path = repo_root / "artifacts" / "runtime" / "runtime_lifecycle.sqlite"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    db_path.write_text("tracked placeholder\n", encoding="utf-8")
    subprocess.run(["git", "add", str(db_path.relative_to(repo_root))], cwd=repo_root, check=True, text=True)

    try:
        lifecycle_store.record_watch_state(
            quest_root=repo_root / "ops" / "med-deepscientist" / "runtime" / "quests" / "q001",
            payload={"updated_at": "2026-05-05T00:00:00+00:00"},
            db_path=db_path,
        )
    except RuntimeError as exc:
        assert "runtime lifecycle SQLite refs index must not be tracked by Git" in str(exc)
        assert "artifacts/runtime/runtime_lifecycle.sqlite" in str(exc)
    else:
        raise AssertionError("tracked lifecycle DB refs index must fail closed")


def test_lifecycle_store_allows_ignored_untracked_sqlite_refs_index(tmp_path: Path) -> None:
    lifecycle_store = importlib.import_module("med_autoscience.runtime_protocol.lifecycle_refs_adapter")
    repo_root = tmp_path / "workspace"
    repo_root.mkdir()
    subprocess.run(["git", "init"], cwd=repo_root, check=True, text=True, capture_output=True)
    (repo_root / ".gitignore").write_text("*.sqlite\n*.sqlite-wal\n*.sqlite-shm\n", encoding="utf-8")
    db_path = repo_root / "artifacts" / "runtime" / "runtime_lifecycle.sqlite"

    result = lifecycle_store.record_watch_state(
        quest_root=repo_root / "ops" / "med-deepscientist" / "runtime" / "quests" / "q001",
        payload={"updated_at": "2026-05-05T00:00:00+00:00"},
        db_path=db_path,
    )

    assert result["status"] == "indexed"
    assert db_path.is_file()
    assert subprocess.run(
        ["git", "-C", str(repo_root), "check-ignore", "--quiet", str(db_path.relative_to(repo_root))],
        check=False,
    ).returncode == 0
    assert subprocess.run(
        ["git", "-C", str(repo_root), "ls-files", "--cached", "--error-unmatch", "--", str(db_path.relative_to(repo_root))],
        check=False,
        text=True,
        capture_output=True,
    ).returncode != 0


def test_runtime_event_record_indexes_event_without_replacing_latest_authority(tmp_path: Path) -> None:
    record_module = importlib.import_module("med_autoscience.runtime_event_record")
    protocol = importlib.import_module("med_autoscience.runtime_protocol.study_runtime")
    lifecycle_store = importlib.import_module("med_autoscience.runtime_protocol.lifecycle_refs_adapter")
    quest_root = tmp_path / "runtime" / "quests" / "quest-001"
    launch_report_path = tmp_path / "studies" / "001-risk" / "artifacts" / "runtime" / "last_launch_report.json"
    record = record_module.RuntimeEventRecord(
        schema_version=1,
        event_id="runtime-event::001-risk::quest-001::status_observed::2026-05-05T00:00:00+00:00",
        study_id="001-risk",
        quest_id="quest-001",
        emitted_at="2026-05-05T00:00:00+00:00",
        event_source="study_runtime_status",
        event_kind="status_observed",
        summary_ref=str(launch_report_path),
        status_snapshot={
            "quest_status": "running",
            "decision": "continue",
            "reason": "runtime_watch",
            "active_run_id": "run-001",
            "runtime_liveness_status": "live",
            "worker_running": True,
            "continuation_policy": "auto",
            "continuation_reason": "runtime_watch",
            "supervisor_tick_status": "fresh",
            "controller_owned_finalize_parking": False,
            "runtime_escalation_ref": None,
        },
        outer_loop_input={
            "quest_status": "running",
            "decision": "continue",
            "reason": "runtime_watch",
            "active_run_id": "run-001",
            "runtime_liveness_status": "live",
            "worker_running": True,
            "supervisor_tick_status": "fresh",
            "controller_owned_finalize_parking": False,
            "interaction_action": None,
            "interaction_requires_user_input": False,
            "runtime_escalation_ref": None,
        },
    )

    written = protocol.write_runtime_event_record(quest_root=quest_root, record=record)

    event_path = Path(written.artifact_path)
    latest_path = event_path.parent / "latest.json"
    latest_payload = json.loads(latest_path.read_text(encoding="utf-8"))
    assert latest_payload == written.to_dict()
    db_path = lifecycle_store.quest_lifecycle_store_path(quest_root)
    with sqlite3.connect(db_path) as conn:
        row = conn.execute(
            """
            SELECT event_id, quest_id, study_id, emitted_at, event_source, event_kind,
                   status, active_run_id, summary_ref, artifact_path, latest_path, cursor, payload_json
            FROM runtime_events
            WHERE quest_root = ?
            """,
            (str(quest_root.resolve()),),
        ).fetchone()

    assert row[:-1] == (
        record.event_id,
        "quest-001",
        "001-risk",
        "2026-05-05T00:00:00+00:00",
        "study_runtime_status",
        "status_observed",
        "running",
        "run-001",
        str(launch_report_path),
        str(event_path.resolve()),
        str(latest_path.resolve()),
        f"2026-05-05T00:00:00+00:00::{record.event_id}",
    )
    assert json.loads(row[-1]) == latest_payload
    assert lifecycle_store.inspect_lifecycle_store(db_path)["tables"]["runtime_events"] == 1


def test_lifecycle_store_records_archive_refs_without_replacing_restore_authority(tmp_path: Path) -> None:
    lifecycle_store = importlib.import_module("med_autoscience.runtime_protocol.lifecycle_refs_adapter")
    quest_root = tmp_path / "runtime" / "quests" / "quest-001"
    archive_path = quest_root / ".ds" / "cold_archive" / "restore-proof" / "quest-001.tar.gz"
    manifest_path = archive_path.with_suffix(".manifest.json")
    proof_path = archive_path.with_suffix(".restore_proof.json")
    for path, content in (
        (archive_path, "archive bytes"),
        (manifest_path, "{}\n"),
        (proof_path, "{}\n"),
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    archive_ref = {
        "surface_kind": "runtime_archive_ref",
        "schema_version": 1,
        "archive_id": "runtime-restore-proof-compaction::quest-001::20260505T000000Z",
        "quest_id": "quest-001",
        "quest_root": str(quest_root),
        "archived_at": "2026-05-05T00:00:00+00:00",
        "archive_path": str(archive_path),
        "archive_format": "tar.gz",
        "sha256": "abc123",
        "bytes": archive_path.stat().st_size,
        "source_manifest_path": str(manifest_path),
        "restore_proof_path": str(proof_path),
        "source_buckets": ["runs"],
    }

    result = lifecycle_store.record_archive_ref(quest_root=quest_root, archive_ref=archive_ref)

    assert result["indexed_table"] == "archive_refs"
    db_path = lifecycle_store.quest_lifecycle_store_path(quest_root)
    with sqlite3.connect(db_path) as conn:
        row = conn.execute(
            """
            SELECT archive_id, archive_path, restore_proof_path, source_buckets_json, payload_json
            FROM archive_refs
            WHERE quest_root = ?
            """,
            (str(quest_root.resolve()),),
        ).fetchone()

    assert row[0] == archive_ref["archive_id"]
    assert row[1] == str(archive_path.resolve())
    assert row[2] == str(proof_path.resolve())
    assert json.loads(row[3]) == ["runs"]
    assert json.loads(row[4]) == archive_ref
    assert lifecycle_store.inspect_lifecycle_store(db_path)["tables"]["archive_refs"] == 1


def test_lifecycle_store_records_q1_lineage_snapshot_allocation_indexes(tmp_path: Path) -> None:
    lifecycle_store = importlib.import_module("med_autoscience.runtime_protocol.lifecycle_refs_adapter")
    workspace_root = tmp_path / "workspace"
    db_path = lifecycle_store.workspace_lifecycle_store_path(workspace_root)
    node = {
        "node_id": "quest-001",
        "node_kind": "quest",
        "object_scope": "quest",
        "study_id": "001-risk",
        "quest_id": "quest-001",
        "status": "active",
    }
    parent_node = {
        "node_id": "workspace-root",
        "node_kind": "workspace",
        "object_scope": "workspace",
        "status": "active",
    }
    edge = {
        "edge_id": "workspace-root->quest-001",
        "source_node_id": "workspace-root",
        "target_node_id": "quest-001",
        "edge_kind": "allocates",
    }
    allocation = {
        "allocation_id": "alloc-001",
        "quest_id": "quest-001",
        "study_id": "001-risk",
        "allocated_root": str(workspace_root / "runtime" / "quests" / "quest-001"),
        "owner": "runtime",
        "status": "allocated",
    }
    snapshot = {
        "snapshot_id": "snap-001",
        "quest_id": "quest-001",
        "study_id": "001-risk",
        "snapshot_kind": "runtime",
        "created_at": "2026-05-06T00:00:00+00:00",
    }
    file_ref = {
        "snapshot_id": "snap-001",
        "ref_id": "runtime-watch",
        "ref_kind": "runtime_report",
        "path": str(workspace_root / "runtime" / "quests" / "quest-001" / "artifacts" / "reports" / "runtime_watch.json"),
        "sha256": "abc123",
        "bytes": 12,
    }
    diff = {
        "diff_id": "diff-001",
        "base_snapshot_id": "snap-000",
        "target_snapshot_id": "snap-001",
        "diff_kind": "runtime_revision",
    }
    projection = {
        "projection_id": "canvas-001",
        "snapshot_id": "snap-001",
        "canvas_id": "main-runtime-canvas",
        "projection_kind": "runtime_canvas",
        "status": "projected",
    }

    assert lifecycle_store.record_lineage_node(workspace_root=workspace_root, node=parent_node)["indexed_table"] == "lineage_nodes"
    assert lifecycle_store.record_lineage_node(workspace_root=workspace_root, node=node)["indexed_table"] == "lineage_nodes"
    assert lifecycle_store.record_lineage_edge(workspace_root=workspace_root, edge=edge)["indexed_table"] == "lineage_edges"
    assert lifecycle_store.record_workspace_allocation(workspace_root=workspace_root, allocation=allocation)["indexed_table"] == (
        "workspace_allocations"
    )
    assert lifecycle_store.record_runtime_snapshot(workspace_root=workspace_root, snapshot=snapshot)["indexed_table"] == (
        "runtime_snapshots"
    )
    assert lifecycle_store.record_snapshot_file_ref(workspace_root=workspace_root, ref=file_ref)["indexed_table"] == (
        "snapshot_file_refs"
    )
    assert lifecycle_store.record_revision_diff(workspace_root=workspace_root, diff=diff)["indexed_table"] == "revision_diffs"
    assert lifecycle_store.record_canvas_projection(workspace_root=workspace_root, projection=projection)["indexed_table"] == (
        "canvas_projection"
    )

    with sqlite3.connect(db_path) as conn:
        node_row = conn.execute(
            """
            SELECT node_kind, object_scope, study_id, quest_id, status, payload_json
            FROM lineage_nodes
            WHERE workspace_root = ? AND node_id = ?
            """,
            (str(workspace_root.resolve()), "quest-001"),
        ).fetchone()
        edge_row = conn.execute(
            """
            SELECT source_node_id, target_node_id, edge_kind, payload_json
            FROM lineage_edges
            WHERE workspace_root = ? AND edge_id = ?
            """,
            (str(workspace_root.resolve()), "workspace-root->quest-001"),
        ).fetchone()
        allocation_row = conn.execute(
            """
            SELECT quest_id, study_id, allocated_root, owner, status, payload_json
            FROM workspace_allocations
            WHERE workspace_root = ? AND allocation_id = ?
            """,
            (str(workspace_root.resolve()), "alloc-001"),
        ).fetchone()
        snapshot_row = conn.execute(
            """
            SELECT quest_id, study_id, snapshot_kind, created_at, payload_json
            FROM runtime_snapshots
            WHERE workspace_root = ? AND snapshot_id = ?
            """,
            (str(workspace_root.resolve()), "snap-001"),
        ).fetchone()
        file_ref_row = conn.execute(
            """
            SELECT ref_kind, target_path, target_sha256, target_bytes, payload_json
            FROM snapshot_file_refs
            WHERE workspace_root = ? AND snapshot_id = ? AND ref_id = ?
            """,
            (str(workspace_root.resolve()), "snap-001", "runtime-watch"),
        ).fetchone()
        diff_row = conn.execute(
            """
            SELECT base_snapshot_id, target_snapshot_id, diff_kind, payload_json
            FROM revision_diffs
            WHERE workspace_root = ? AND diff_id = ?
            """,
            (str(workspace_root.resolve()), "diff-001"),
        ).fetchone()
        projection_row = conn.execute(
            """
            SELECT snapshot_id, canvas_id, projection_kind, status, payload_json
            FROM canvas_projection
            WHERE workspace_root = ? AND projection_id = ?
            """,
            (str(workspace_root.resolve()), "canvas-001"),
        ).fetchone()

    assert node_row[:-1] == ("quest", "quest", "001-risk", "quest-001", "active")
    assert json.loads(node_row[-1]) == node
    assert edge_row[:-1] == ("workspace-root", "quest-001", "allocates")
    assert json.loads(edge_row[-1]) == edge
    assert allocation_row[:-1] == (
        "quest-001",
        "001-risk",
        str((workspace_root / "runtime" / "quests" / "quest-001").resolve()),
        "runtime",
        "allocated",
    )
    assert json.loads(allocation_row[-1]) == allocation
    assert snapshot_row[:-1] == ("quest-001", "001-risk", "runtime", "2026-05-06T00:00:00+00:00")
    assert json.loads(snapshot_row[-1]) == snapshot
    assert file_ref_row[:-1] == (
        "runtime_report",
        str((workspace_root / "runtime" / "quests" / "quest-001" / "artifacts" / "reports" / "runtime_watch.json").resolve()),
        "abc123",
        12,
    )
    assert json.loads(file_ref_row[-1]) == file_ref
    assert diff_row[:-1] == ("snap-000", "snap-001", "runtime_revision")
    assert json.loads(diff_row[-1]) == diff
    assert projection_row[:-1] == ("snap-001", "main-runtime-canvas", "runtime_canvas", "projected")
    assert json.loads(projection_row[-1]) == projection
    assert lifecycle_store.read_lifecycle_records(db_path, "runtime_snapshots") == [snapshot]
    assert lifecycle_store.inspect_lifecycle_store(db_path)["tables"] == _expected_table_counts(
        lineage_nodes=2,
        lineage_edges=1,
        workspace_allocations=1,
        runtime_snapshots=1,
        snapshot_file_refs=1,
        revision_diffs=1,
        canvas_projection=1,
    )


def test_lifecycle_store_rejects_publication_study_artifact_authority_in_q1_indexes(tmp_path: Path) -> None:
    lifecycle_store = importlib.import_module("med_autoscience.runtime_protocol.lifecycle_refs_adapter")
    workspace_root = tmp_path / "workspace"

    try:
        lifecycle_store.record_runtime_snapshot(
            workspace_root=workspace_root,
            snapshot={
                "snapshot_id": "snap-publication-truth",
                "authority_scope": ["runtime_lifecycle", "publication_authority"],
                "authority_surfaces": ["publication_eval/latest.json", "current_package.zip"],
            },
        )
    except ValueError as exc:
        assert "index-only" in str(exc)
        assert "file/study/publication/artifact truth remains outside SQLite" in str(exc)
    else:
        raise AssertionError("SQLite lifecycle store must reject publication/artifact truth authority")

    db_path = lifecycle_store.workspace_lifecycle_store_path(workspace_root)
    assert not db_path.exists()


def test_lifecycle_store_indexes_macro_state_and_routing_receipts_without_replacing_authority_files(
    tmp_path: Path,
) -> None:
    lifecycle_store = importlib.import_module("med_autoscience.runtime_protocol.lifecycle_refs_adapter")
    study_root = tmp_path / "studies" / "001-risk"
    quest_root = tmp_path / "runtime" / "quests" / "quest-001"
    db_path = tmp_path / "artifacts" / "runtime" / "runtime_lifecycle.sqlite"
    macro_state_path = study_root / "artifacts" / "runtime" / "study_macro_state" / "latest.json"
    owner_receipt_path = study_root / "artifacts" / "runtime" / "owner_route" / "latest.json"
    dispatch_receipt_path = quest_root / "artifacts" / "runtime" / "dispatch" / "dispatch-001.json"
    paper_work_unit_receipt_path = study_root / "artifacts" / "runtime" / "paper_work_unit_outbox" / "receipts.jsonl"
    surface_ref_path = study_root / "artifacts" / "runtime" / "surface_refs" / "publication_eval.json"
    for path in (macro_state_path, owner_receipt_path, dispatch_receipt_path, paper_work_unit_receipt_path, surface_ref_path):
        path.parent.mkdir(parents=True, exist_ok=True)
    macro_state = {
        "surface": "study_macro_state",
        "schema_version": 1,
        "study_id": "001-risk",
        "quest_id": "quest-001",
        "snapshot_id": "macro-001",
        "observed_at": "2026-05-06T00:00:00+00:00",
        "macro_state": "runtime_active",
        "decision_owner": "mas_controller",
        "owner_route": {"idempotency_key": "route-001", "next_owner": "mas_controller"},
        "surface_refs": {
            "publication_eval": {
                "surface": "publication_eval/latest.json",
                "path": str(study_root / "artifacts" / "publication_eval" / "latest.json"),
            }
        },
    }
    owner_receipt = {
        "surface": "domain_route_owner_route",
        "study_id": "001-risk",
        "quest_id": "quest-001",
        "idempotency_key": "route-001",
        "route_epoch": "truth-epoch-001",
        "current_owner": "runtime",
        "next_owner": "mas_controller",
        "owner_reason": "runtime_controller_redrive_required",
    }
    dispatch_receipt = {
        "surface": "domain_owner_action_dispatch_receipt",
        "dispatch_id": "dispatch-001",
        "study_id": "001-risk",
        "quest_id": "quest-001",
        "created_at": "2026-05-06T00:01:00+00:00",
        "owner_route": owner_receipt,
        "status": "dispatched",
    }
    paper_work_unit_receipt = {
        "surface": "paper_work_unit_outbox_receipt",
        "schema_version": 1,
        "receipt_id": "paper-work-unit-receipt::001",
        "receipt_status": "started",
        "recorded_at": "2026-05-06T00:01:30+00:00",
        "study_id": "001-risk",
        "quest_id": "quest-001",
        "idempotency_key": "paper-work-unit::001",
        "intent_fingerprint": "paper-work-unit-intent::001",
        "source_fingerprint": "publication-blockers::001",
        "started_worker": True,
        "worker_start_ref": "worker::run-001",
    }
    surface_ref = {
        "surface": "publication_eval/latest.json",
        "study_id": "001-risk",
        "quest_id": "quest-001",
        "ref_key": "publication_eval",
        "path": str(study_root / "artifacts" / "publication_eval" / "latest.json"),
        "sha256": "abc123",
        "observed_at": "2026-05-06T00:02:00+00:00",
    }
    macro_state_path.write_text(json.dumps(macro_state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    owner_receipt_path.write_text(json.dumps(owner_receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    dispatch_receipt_path.write_text(json.dumps(dispatch_receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    paper_work_unit_receipt_path.write_text(json.dumps(paper_work_unit_receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    surface_ref_path.write_text(json.dumps(surface_ref, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    mtimes = {
        path: path.stat().st_mtime_ns
        for path in (macro_state_path, owner_receipt_path, dispatch_receipt_path, paper_work_unit_receipt_path, surface_ref_path)
    }

    macro_index = lifecycle_store.record_study_macro_state_snapshot(
        study_root=study_root,
        snapshot=macro_state,
        snapshot_path=macro_state_path,
        db_path=db_path,
    )
    owner_index = lifecycle_store.record_owner_route_receipt(
        study_root=study_root,
        receipt=owner_receipt,
        receipt_path=owner_receipt_path,
        db_path=db_path,
    )
    dispatch_index = lifecycle_store.record_dispatch_receipt(
        quest_root=quest_root,
        receipt=dispatch_receipt,
        receipt_path=dispatch_receipt_path,
        db_path=db_path,
    )
    paper_work_unit_index = lifecycle_store.record_paper_work_unit_receipt(
        study_root=study_root,
        quest_root=quest_root,
        receipt=paper_work_unit_receipt,
        receipt_path=paper_work_unit_receipt_path,
        db_path=db_path,
    )
    surface_ref_index = lifecycle_store.record_surface_ref(
        object_root=study_root,
        object_scope="study",
        ref=surface_ref,
        ref_path=surface_ref_path,
        db_path=db_path,
    )

    assert macro_index["indexed_table"] == "study_macro_state_snapshots"
    assert owner_index["indexed_table"] == "owner_route_receipts"
    assert dispatch_index["indexed_table"] == "dispatch_receipts"
    assert paper_work_unit_index["indexed_table"] == "paper_work_unit_receipts"
    assert surface_ref_index["indexed_table"] == "surface_refs"
    assert {path: path.stat().st_mtime_ns for path in mtimes} == mtimes
    with sqlite3.connect(db_path) as conn:
        macro_row = conn.execute(
            """
            SELECT study_id, quest_id, snapshot_id, observed_at, macro_state,
                   decision_owner, owner_route_json, surface_refs_json, payload_json, source_path
            FROM study_macro_state_snapshots
            WHERE study_root = ?
            """,
            (str(study_root.resolve()),),
        ).fetchone()
        owner_row = conn.execute(
            """
            SELECT study_id, quest_id, idempotency_key, route_epoch, current_owner,
                   next_owner, owner_reason, payload_json, source_path
            FROM owner_route_receipts
            WHERE study_root = ?
            """,
            (str(study_root.resolve()),),
        ).fetchone()
        dispatch_row = conn.execute(
            """
            SELECT dispatch_id, study_id, quest_id, created_at, status,
                   owner_route_json, payload_json, source_path
            FROM dispatch_receipts
            WHERE quest_root = ?
            """,
            (str(quest_root.resolve()),),
        ).fetchone()
        paper_work_unit_row = conn.execute(
            """
            SELECT receipt_id, study_id, quest_id, idempotency_key, intent_fingerprint,
                   source_fingerprint, receipt_status, started_worker, worker_start_ref,
                   payload_json, source_path
            FROM paper_work_unit_receipts
            WHERE study_root = ?
            """,
            (str(study_root.resolve()),),
        ).fetchone()
        ref_row = conn.execute(
            """
            SELECT object_scope, ref_key, surface, study_id, quest_id, target_path,
                   source_path, target_sha256, payload_json
            FROM surface_refs
            WHERE object_root = ?
            """,
            (str(study_root.resolve()),),
        ).fetchone()

    assert macro_row[:6] == (
        "001-risk",
        "quest-001",
        "macro-001",
        "2026-05-06T00:00:00+00:00",
        "runtime_active",
        "mas_controller",
    )
    assert json.loads(macro_row[6]) == macro_state["owner_route"]
    assert json.loads(macro_row[7]) == macro_state["surface_refs"]
    assert json.loads(macro_row[8]) == macro_state
    assert macro_row[9] == str(macro_state_path.resolve())
    assert owner_row[:-2] == (
        "001-risk",
        "quest-001",
        "route-001",
        "truth-epoch-001",
        "runtime",
        "mas_controller",
        "runtime_controller_redrive_required",
    )
    assert json.loads(owner_row[-2]) == owner_receipt
    assert owner_row[-1] == str(owner_receipt_path.resolve())
    assert dispatch_row[:5] == (
        "dispatch-001",
        "001-risk",
        "quest-001",
        "2026-05-06T00:01:00+00:00",
        "dispatched",
    )
    assert json.loads(dispatch_row[5]) == owner_receipt
    assert json.loads(dispatch_row[6]) == dispatch_receipt
    assert dispatch_row[7] == str(dispatch_receipt_path.resolve())
    assert paper_work_unit_row[:9] == (
        "paper-work-unit-receipt::001",
        "001-risk",
        "quest-001",
        "paper-work-unit::001",
        "paper-work-unit-intent::001",
        "publication-blockers::001",
        "started",
        1,
        "worker::run-001",
    )
    assert json.loads(paper_work_unit_row[9]) == paper_work_unit_receipt
    assert paper_work_unit_row[10] == str(paper_work_unit_receipt_path.resolve())
    assert ref_row == (
        "study",
        "publication_eval",
        "publication_eval/latest.json",
        "001-risk",
        "quest-001",
        str((study_root / "artifacts" / "publication_eval" / "latest.json").resolve()),
        str(surface_ref_path.resolve()),
        "abc123",
        json.dumps(surface_ref, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str),
    )
    tables = lifecycle_store.inspect_lifecycle_store(db_path)["tables"]
    assert tables["study_macro_state_snapshots"] == 1
    assert tables["owner_route_receipts"] == 1
    assert tables["dispatch_receipts"] == 1
    assert tables["turn_receipts"] == 0
    assert tables["paper_work_unit_receipts"] == 1
    assert tables["surface_refs"] == 1


def test_surface_ref_relative_target_paths_are_resolved_against_object_root(tmp_path: Path) -> None:
    lifecycle_store = importlib.import_module("med_autoscience.runtime_protocol.lifecycle_refs_adapter")
    study_root = tmp_path / "studies" / "001-risk"
    db_path = tmp_path / "artifacts" / "runtime" / "runtime_lifecycle.sqlite"
    ref_path = study_root / "artifacts" / "runtime" / "surface_refs" / "publication_eval.json"
    ref_path.parent.mkdir(parents=True)
    ref = {
        "surface": "publication_eval/latest.json",
        "study_id": "001-risk",
        "ref_key": "publication_eval",
        "path": "artifacts/publication_eval/latest.json",
    }
    ref_path.write_text(json.dumps(ref, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lifecycle_store.record_surface_ref(
        object_root=study_root,
        object_scope="study",
        ref=ref,
        ref_path=ref_path,
        db_path=db_path,
    )

    with sqlite3.connect(db_path) as conn:
        target_path = conn.execute(
            "SELECT target_path FROM surface_refs WHERE object_root = ?",
            (str(study_root.resolve()),),
        ).fetchone()[0]
    assert target_path == str((study_root / "artifacts" / "publication_eval" / "latest.json").resolve())


def test_lifecycle_read_model_exports_sqlite_runtime_report_without_touching_latest_files(tmp_path: Path) -> None:
    report_store = importlib.import_module("med_autoscience.runtime_protocol.report_store")
    read_model = importlib.import_module("med_autoscience.runtime_protocol.runtime_lifecycle_read_model")
    quest_root = tmp_path / "runtime" / "quests" / "q001"
    report = {
        "schema_version": 1,
        "scanned_at": "2026-05-05T00:00:00+00:00",
        "quest_status": "running",
    }
    report_store.write_timestamped_report(
        quest_root=quest_root,
        report_group="runtime_watch",
        timestamp="2026-05-05T00:00:00+00:00",
        report=report,
        markdown="# Runtime Watch\n",
    )
    latest_json = quest_root / "artifacts" / "reports" / "runtime_watch" / "latest.json"
    latest_mtime = latest_json.stat().st_mtime_ns

    projection = read_model.read_lifecycle_projection(
        surface="runtime_report",
        quest_root=quest_root,
        report_group="runtime_watch",
    )
    export_path = tmp_path / "exports" / "runtime_watch_latest.json"
    export = read_model.export_lifecycle_projection(
        surface="runtime_report",
        quest_root=quest_root,
        report_group="runtime_watch",
        export_format="json",
        output_path=export_path,
    )

    assert projection["surface_kind"] == "runtime_lifecycle_read_model"
    assert projection["payload"] == report
    assert projection["legacy_restore_import_used"] is False
    assert projection["read_only"] is True
    assert "ORDER BY timestamp DESC LIMIT 1" in projection["source_query"]
    assert export["surface_kind"] == "runtime_lifecycle_export"
    assert export["legacy_restore_import_used"] is False
    assert export["output_path"] == str(export_path.resolve())
    assert json.loads(export_path.read_text(encoding="utf-8")) == report
    assert latest_json.stat().st_mtime_ns == latest_mtime


def test_lifecycle_read_model_missing_sqlite_does_not_default_to_legacy_restore_import(tmp_path: Path) -> None:
    read_model = importlib.import_module("med_autoscience.runtime_protocol.runtime_lifecycle_read_model")
    quest_root = tmp_path / "runtime" / "quests" / "q001"
    legacy_latest = quest_root / "artifacts" / "reports" / "runtime_watch" / "latest.json"
    legacy_latest.parent.mkdir(parents=True, exist_ok=True)
    legacy_payload = {"schema_version": 1, "quest_status": "stopped"}
    legacy_latest.write_text(json.dumps(legacy_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    db_path = quest_root / "artifacts" / "runtime" / "runtime_lifecycle.sqlite"

    projection = read_model.read_lifecycle_projection(
        surface="runtime_report",
        quest_root=quest_root,
    )
    inventory = read_model.build_lifecycle_inventory(quest_root=quest_root)

    assert projection["status"] == "missing"
    assert projection["missing_reason"] == "lifecycle_refs_sqlite_missing"
    assert projection["payload"] == {}
    assert projection["legacy_restore_import_used"] is False
    assert projection["source_paths"] == []
    assert inventory["status"] == "missing"
    assert inventory["legacy_restore_import_used"] is False
    assert not db_path.exists()

    diagnostic_projection = read_model.read_lifecycle_projection(
        surface="runtime_report",
        quest_root=quest_root,
        legacy_restore_import_diagnostic=True,
    )
    assert diagnostic_projection["status"] == "legacy_restore_import_available"
    assert diagnostic_projection["payload"] == legacy_payload
    assert diagnostic_projection["legacy_restore_import_used"] is True
    assert diagnostic_projection["diagnostic_scope"] == "legacy_restore_import_diagnostic"
    assert diagnostic_projection["source_paths"] == [str(legacy_latest.resolve())]


def test_lifecycle_inventory_lists_workspace_storage_audit_from_sqlite(tmp_path: Path) -> None:
    lifecycle_store = importlib.import_module("med_autoscience.runtime_protocol.lifecycle_refs_adapter")
    read_model = importlib.import_module("med_autoscience.runtime_protocol.runtime_lifecycle_read_model")
    runtime_storage = importlib.import_module("med_autoscience.controllers.runtime_storage_maintenance")
    profile = importlib.import_module("tests.study_runtime_test_helpers").make_profile(tmp_path)

    runtime_storage.audit_workspace_storage(profile=profile, all_studies=True, apply=False)

    db_path = lifecycle_store.workspace_lifecycle_store_path(profile.workspace_root)
    inventory = read_model.build_lifecycle_inventory(workspace_root=profile.workspace_root)
    projection = read_model.read_lifecycle_projection(
        surface="workspace_storage_audit",
        workspace_root=profile.workspace_root,
    )

    assert inventory["status"] == "ready"
    assert inventory["db_path"] == str(db_path)
    assert inventory["available_surfaces"] == ["workspace_storage_audit"]
    assert inventory["tables"]["workspace_storage_audits"] == 1
    assert inventory["tables"]["report_index"] == 1
    assert projection["legacy_restore_import_used"] is False
    assert projection["payload"]["workspace_root"] == str(profile.workspace_root.resolve())
