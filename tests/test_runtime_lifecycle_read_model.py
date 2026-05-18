from __future__ import annotations

import importlib
import json
from pathlib import Path
import sqlite3


def test_lifecycle_read_model_reads_git_retirement_projection_surfaces_from_sqlite(tmp_path: Path) -> None:
    read_model = importlib.import_module("med_autoscience.runtime_protocol.runtime_lifecycle_read_model")
    workspace_root = (tmp_path / "workspace").resolve()
    quest_root = (workspace_root / "runtime" / "quests" / "quest-001").resolve()
    db_path = tmp_path / "runtime_lifecycle.sqlite"
    _write_projection_fixture(db_path=db_path, workspace_root=workspace_root, quest_root=quest_root)

    inventory = read_model.build_lifecycle_inventory(db_path=db_path)

    assert {
        "lineage_route",
        "workspace_allocation",
        "runtime_snapshot",
        "revision_diff",
        "canvas_projection",
    }.issubset(read_model.SUPPORTED_SURFACES)
    assert inventory["status"] == "ready"
    assert inventory["legacy_restore_import_used"] is False
    assert inventory["tables"]["lineage_nodes"] == 1
    assert inventory["tables"]["lineage_edges"] == 1
    assert inventory["tables"]["workspace_allocations"] == 1
    assert inventory["tables"]["runtime_snapshots"] == 1
    assert inventory["tables"]["snapshot_file_refs"] == 1
    assert inventory["tables"]["revision_diffs"] == 1
    assert inventory["tables"]["canvas_projection"] == 1
    assert {
        "lineage_route",
        "workspace_allocation",
        "runtime_snapshot",
        "revision_diff",
        "canvas_projection",
    }.issubset(set(inventory["available_surfaces"]))

    lineage = read_model.read_lifecycle_projection(
        surface="lineage_route",
        quest_root=quest_root,
        db_path=db_path,
    )
    allocation = read_model.read_lifecycle_projection(
        surface="workspace_allocation",
        workspace_root=workspace_root,
        db_path=db_path,
    )
    snapshot = read_model.read_lifecycle_projection(
        surface="runtime_snapshot",
        quest_root=quest_root,
        db_path=db_path,
    )
    revision = read_model.read_lifecycle_projection(
        surface="revision_diff",
        quest_root=quest_root,
        db_path=db_path,
    )
    canvas = read_model.read_lifecycle_projection(
        surface="canvas_projection",
        workspace_root=workspace_root,
        db_path=db_path,
    )

    assert lineage["status"] == "ready"
    assert lineage["legacy_restore_import_used"] is False
    assert lineage["source_paths"] == []
    assert lineage["payload"]["lineage_nodes"][0]["payload_json"] == {"route": "analysis"}
    assert lineage["payload"]["lineage_edges"][0]["relation"] == "continues"
    assert allocation["payload"]["workspace_allocations"][0]["state"] == "active"
    assert snapshot["payload"]["runtime_snapshots"][0]["manifest_json"] == {"files": 2}
    assert snapshot["payload"]["snapshot_file_refs"][0]["path"] == "paper/main.md"
    assert revision["payload"]["revision_diffs"][0]["summary_json"] == {"changed": ["paper/main.md"]}
    assert canvas["payload"]["canvas_projection"][0]["payload_json"] == {"nodes": ["node-001"], "edges": []}


def test_lifecycle_read_model_sqlite_only_surfaces_report_missing_without_legacy_restore_import(tmp_path: Path) -> None:
    read_model = importlib.import_module("med_autoscience.runtime_protocol.runtime_lifecycle_read_model")
    quest_root = tmp_path / "runtime" / "quests" / "quest-001"
    legacy_latest = quest_root / "artifacts" / "reports" / "runtime_watch" / "latest.json"
    legacy_latest.parent.mkdir(parents=True)
    legacy_latest.write_text(json.dumps({"legacy": True}), encoding="utf-8")

    projection = read_model.read_lifecycle_projection(surface="lineage_route", quest_root=quest_root)

    assert projection["status"] == "missing"
    assert projection["missing_reason"] == "runtime_lifecycle_sqlite_missing"
    assert projection["legacy_restore_import_used"] is False
    assert projection["source_paths"] == []
    assert projection["payload"] == {}


def test_lifecycle_read_model_sqlite_only_surfaces_report_capability_gap_for_missing_tables(tmp_path: Path) -> None:
    read_model = importlib.import_module("med_autoscience.runtime_protocol.runtime_lifecycle_read_model")
    db_path = tmp_path / "runtime_lifecycle.sqlite"
    with sqlite3.connect(db_path) as conn:
        conn.execute("CREATE TABLE lineage_nodes (node_id TEXT PRIMARY KEY, payload_json TEXT NOT NULL)")

    projection = read_model.read_lifecycle_projection(surface="lineage_route", db_path=db_path)

    assert projection["status"] == "capability_gap"
    assert projection["missing_reason"] == "runtime_lifecycle_sqlite_table_missing"
    assert projection["legacy_restore_import_used"] is False
    assert projection["payload"] == {"missing_tables": ["lineage_edges"]}


def test_lifecycle_read_model_legacy_surfaces_use_no_legacy_restore_import_by_default(tmp_path: Path) -> None:
    read_model = importlib.import_module("med_autoscience.runtime_protocol.runtime_lifecycle_read_model")
    quest_root = tmp_path / "runtime" / "quests" / "quest-001"
    legacy_latest = quest_root / "artifacts" / "reports" / "runtime_watch" / "latest.json"
    legacy_latest.parent.mkdir(parents=True)
    legacy_latest.write_text(json.dumps({"legacy": True}), encoding="utf-8")

    projection = read_model.read_lifecycle_projection(
        surface="runtime_report",
        quest_root=quest_root,
        report_group="runtime_watch",
    )

    assert projection["status"] == "missing"
    assert projection["missing_reason"] == "runtime_lifecycle_sqlite_missing"
    assert projection["legacy_restore_import_used"] is False
    assert projection["source_paths"] == []
    assert projection["payload"] == {}
    assert "diagnostic_scope" not in projection


def test_lifecycle_read_model_legacy_restore_import_diagnostic_can_read_explicit_legacy_restore_import_diagnostic(tmp_path: Path) -> None:
    read_model = importlib.import_module("med_autoscience.runtime_protocol.runtime_lifecycle_read_model")
    quest_root = tmp_path / "runtime" / "quests" / "quest-001"
    legacy_latest = quest_root / "artifacts" / "reports" / "runtime_watch" / "latest.json"
    legacy_latest.parent.mkdir(parents=True)
    legacy_payload = {"legacy": True}
    legacy_latest.write_text(json.dumps(legacy_payload), encoding="utf-8")

    projection = read_model.read_legacy_restore_import_diagnostic_projection(
        surface="runtime_report",
        quest_root=quest_root,
        report_group="runtime_watch",
    )

    assert projection["status"] == "legacy_restore_import_available"
    assert projection["payload"] == legacy_payload
    assert projection["legacy_restore_import_used"] is True
    assert projection["diagnostic_scope"] == "legacy_restore_import_diagnostic"
    assert projection["source_paths"] == [str(legacy_latest.resolve())]


def test_lifecycle_read_model_legacy_surfaces_report_capability_gap_for_missing_table(tmp_path: Path) -> None:
    read_model = importlib.import_module("med_autoscience.runtime_protocol.runtime_lifecycle_read_model")
    db_path = tmp_path / "runtime_lifecycle.sqlite"
    with sqlite3.connect(db_path) as conn:
        conn.execute("CREATE TABLE unrelated_surface (id TEXT PRIMARY KEY)")

    projection = read_model.read_lifecycle_projection(surface="runtime_report", db_path=db_path)

    assert projection["status"] == "capability_gap"
    assert projection["missing_reason"] == "runtime_lifecycle_sqlite_table_missing"
    assert projection["legacy_restore_import_used"] is False
    assert projection["payload"] == {"missing_tables": ["runtime_reports"]}


def test_lifecycle_read_model_legacy_surfaces_report_missing_for_missing_row(tmp_path: Path) -> None:
    read_model = importlib.import_module("med_autoscience.runtime_protocol.runtime_lifecycle_read_model")
    db_path = tmp_path / "runtime_lifecycle.sqlite"
    quest_root = (tmp_path / "runtime" / "quests" / "quest-001").resolve()
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE runtime_reports(
                quest_root TEXT NOT NULL,
                report_group TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                status TEXT NOT NULL,
                json_path TEXT NOT NULL,
                md_path TEXT NOT NULL,
                latest_json_path TEXT NOT NULL,
                latest_md_path TEXT NOT NULL,
                payload_sha256 TEXT NOT NULL,
                payload_json TEXT NOT NULL
            )
            """
        )

    projection = read_model.read_lifecycle_projection(
        surface="runtime_report",
        quest_root=quest_root,
        report_group="runtime_watch",
        db_path=db_path,
    )

    assert projection["status"] == "missing"
    assert projection["missing_reason"] == "runtime_lifecycle_sqlite_row_missing"
    assert projection["legacy_restore_import_used"] is False
    assert projection["payload"] == {}


def test_lifecycle_read_model_exports_sqlite_only_projection_as_json_and_markdown(tmp_path: Path) -> None:
    read_model = importlib.import_module("med_autoscience.runtime_protocol.runtime_lifecycle_read_model")
    workspace_root = (tmp_path / "workspace").resolve()
    quest_root = (workspace_root / "runtime" / "quests" / "quest-001").resolve()
    db_path = tmp_path / "runtime_lifecycle.sqlite"
    json_path = tmp_path / "exports" / "canvas.json"
    markdown_path = tmp_path / "exports" / "canvas.md"
    _write_projection_fixture(db_path=db_path, workspace_root=workspace_root, quest_root=quest_root)

    json_export = read_model.export_lifecycle_projection(
        surface="canvas_projection",
        workspace_root=workspace_root,
        db_path=db_path,
        export_format="json",
        output_path=json_path,
    )
    markdown_export = read_model.export_lifecycle_projection(
        surface="canvas_projection",
        workspace_root=workspace_root,
        db_path=db_path,
        export_format="markdown",
        output_path=markdown_path,
    )

    assert json_export["surface"] == "canvas_projection"
    assert json_export["legacy_restore_import_used"] is False
    assert json_export["output_path"] == str(json_path.resolve())
    assert json.loads(json_path.read_text(encoding="utf-8"))["canvas_projection"][0]["payload_json"] == {
        "nodes": ["node-001"],
        "edges": [],
    }
    markdown = markdown_path.read_text(encoding="utf-8")
    assert markdown_export["export_format"] == "markdown"
    assert "- surface: `canvas_projection`" in markdown
    assert '"nodes": [' in markdown


def test_lifecycle_read_model_export_uses_no_legacy_restore_import_by_default(tmp_path: Path) -> None:
    read_model = importlib.import_module("med_autoscience.runtime_protocol.runtime_lifecycle_read_model")
    quest_root = tmp_path / "runtime" / "quests" / "quest-001"
    legacy_latest = quest_root / "artifacts" / "reports" / "runtime_watch" / "latest.json"
    output_path = tmp_path / "exports" / "runtime_report.json"
    legacy_latest.parent.mkdir(parents=True)
    legacy_latest.write_text(json.dumps({"legacy": True}), encoding="utf-8")

    export = read_model.export_lifecycle_projection(
        surface="runtime_report",
        quest_root=quest_root,
        report_group="runtime_watch",
        export_format="json",
        output_path=output_path,
    )

    assert export["legacy_restore_import_used"] is False
    assert export["payload"] == {}
    assert json.loads(output_path.read_text(encoding="utf-8")) == {}


def _write_projection_fixture(*, db_path: Path, workspace_root: Path, quest_root: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        conn.executescript(
            """
            CREATE TABLE lineage_nodes (
                node_id TEXT PRIMARY KEY,
                quest_root TEXT NOT NULL,
                node_kind TEXT NOT NULL,
                route_state TEXT NOT NULL,
                payload_json TEXT NOT NULL
            );
            CREATE TABLE lineage_edges (
                edge_id TEXT PRIMARY KEY,
                quest_root TEXT NOT NULL,
                parent_node_id TEXT NOT NULL,
                child_node_id TEXT NOT NULL,
                relation TEXT NOT NULL
            );
            CREATE TABLE workspace_allocations (
                workspace_id TEXT PRIMARY KEY,
                workspace_root TEXT NOT NULL,
                node_id TEXT NOT NULL,
                root_ref TEXT NOT NULL,
                state TEXT NOT NULL
            );
            CREATE TABLE runtime_snapshots (
                snapshot_id TEXT PRIMARY KEY,
                quest_root TEXT NOT NULL,
                node_id TEXT NOT NULL,
                manifest_json TEXT NOT NULL,
                archive_ref TEXT NOT NULL
            );
            CREATE TABLE snapshot_file_refs (
                snapshot_id TEXT NOT NULL,
                quest_root TEXT NOT NULL,
                path TEXT NOT NULL,
                content_sha256 TEXT NOT NULL,
                size_bytes INTEGER NOT NULL
            );
            CREATE TABLE revision_diffs (
                diff_id TEXT PRIMARY KEY,
                quest_root TEXT NOT NULL,
                source_snapshot_id TEXT NOT NULL,
                target_snapshot_id TEXT NOT NULL,
                summary_json TEXT NOT NULL
            );
            CREATE TABLE canvas_projection (
                projection_id TEXT PRIMARY KEY,
                workspace_root TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                rebuilt_at TEXT NOT NULL
            );
            """
        )
        conn.execute(
            """
            INSERT INTO lineage_nodes
            (node_id, quest_root, node_kind, route_state, payload_json)
            VALUES (?, ?, ?, ?, ?)
            """,
            ("node-001", str(quest_root), "analysis", "active", json.dumps({"route": "analysis"})),
        )
        conn.execute(
            """
            INSERT INTO lineage_edges
            (edge_id, quest_root, parent_node_id, child_node_id, relation)
            VALUES (?, ?, ?, ?, ?)
            """,
            ("edge-001", str(quest_root), "node-000", "node-001", "continues"),
        )
        conn.execute(
            """
            INSERT INTO workspace_allocations
            (workspace_id, workspace_root, node_id, root_ref, state)
            VALUES (?, ?, ?, ?, ?)
            """,
            ("workspace-001", str(workspace_root), "node-001", "runtime/quests/quest-001", "active"),
        )
        conn.execute(
            """
            INSERT INTO runtime_snapshots
            (snapshot_id, quest_root, node_id, manifest_json, archive_ref)
            VALUES (?, ?, ?, ?, ?)
            """,
            ("snapshot-001", str(quest_root), "node-001", json.dumps({"files": 2}), "archive-001.tar.gz"),
        )
        conn.execute(
            """
            INSERT INTO snapshot_file_refs
            (snapshot_id, quest_root, path, content_sha256, size_bytes)
            VALUES (?, ?, ?, ?, ?)
            """,
            ("snapshot-001", str(quest_root), "paper/main.md", "abc123", 128),
        )
        conn.execute(
            """
            INSERT INTO revision_diffs
            (diff_id, quest_root, source_snapshot_id, target_snapshot_id, summary_json)
            VALUES (?, ?, ?, ?, ?)
            """,
            ("diff-001", str(quest_root), "snapshot-000", "snapshot-001", json.dumps({"changed": ["paper/main.md"]})),
        )
        conn.execute(
            """
            INSERT INTO canvas_projection
            (projection_id, workspace_root, payload_json, rebuilt_at)
            VALUES (?, ?, ?, ?)
            """,
            (
                "canvas-001",
                str(workspace_root),
                json.dumps({"nodes": ["node-001"], "edges": []}),
                "2026-05-06T00:00:00+00:00",
            ),
        )
