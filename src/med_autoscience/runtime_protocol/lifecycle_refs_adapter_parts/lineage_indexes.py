from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
import sqlite3
from typing import Any

from ..runtime_lifecycle_contract import FILE_AUTHORITY_SURFACES, SQLITE_FORBIDDEN_AUTHORITY_SURFACES

LINEAGE_INDEX_TABLE_NAMES = (
    "lineage_nodes",
    "lineage_edges",
    "workspace_allocations",
    "runtime_snapshots",
    "snapshot_file_refs",
    "revision_diffs",
    "canvas_projection",
)


def ensure_lineage_index_schema(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS lineage_nodes(
            workspace_root TEXT NOT NULL,
            node_id TEXT NOT NULL,
            node_kind TEXT NOT NULL,
            object_scope TEXT NOT NULL,
            study_id TEXT,
            quest_id TEXT,
            status TEXT NOT NULL,
            source_path TEXT,
            payload_sha256 TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            recorded_at TEXT NOT NULL,
            PRIMARY KEY (workspace_root, node_id)
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS lineage_edges(
            workspace_root TEXT NOT NULL,
            edge_id TEXT NOT NULL,
            source_node_id TEXT NOT NULL,
            target_node_id TEXT NOT NULL,
            edge_kind TEXT NOT NULL,
            payload_sha256 TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            recorded_at TEXT NOT NULL,
            PRIMARY KEY (workspace_root, edge_id)
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS workspace_allocations(
            workspace_root TEXT NOT NULL,
            allocation_id TEXT NOT NULL,
            quest_id TEXT,
            study_id TEXT,
            allocated_root TEXT,
            owner TEXT,
            status TEXT NOT NULL,
            payload_sha256 TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            recorded_at TEXT NOT NULL,
            PRIMARY KEY (workspace_root, allocation_id)
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS runtime_snapshots(
            workspace_root TEXT NOT NULL,
            snapshot_id TEXT NOT NULL,
            quest_id TEXT,
            study_id TEXT,
            snapshot_kind TEXT NOT NULL,
            created_at TEXT NOT NULL,
            source_path TEXT,
            payload_sha256 TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            recorded_at TEXT NOT NULL,
            PRIMARY KEY (workspace_root, snapshot_id)
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS snapshot_file_refs(
            workspace_root TEXT NOT NULL,
            snapshot_id TEXT NOT NULL,
            ref_id TEXT NOT NULL,
            ref_kind TEXT NOT NULL,
            target_path TEXT,
            target_sha256 TEXT,
            target_bytes INTEGER NOT NULL,
            payload_sha256 TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            recorded_at TEXT NOT NULL,
            PRIMARY KEY (workspace_root, snapshot_id, ref_id)
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS revision_diffs(
            workspace_root TEXT NOT NULL,
            diff_id TEXT NOT NULL,
            base_snapshot_id TEXT,
            target_snapshot_id TEXT,
            diff_kind TEXT NOT NULL,
            source_path TEXT,
            payload_sha256 TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            recorded_at TEXT NOT NULL,
            PRIMARY KEY (workspace_root, diff_id)
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS canvas_projection(
            workspace_root TEXT NOT NULL,
            projection_id TEXT NOT NULL,
            snapshot_id TEXT,
            canvas_id TEXT NOT NULL,
            projection_kind TEXT NOT NULL,
            status TEXT NOT NULL,
            source_path TEXT,
            payload_sha256 TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            recorded_at TEXT NOT NULL,
            PRIMARY KEY (workspace_root, projection_id)
        )
        """
    )


def record_lineage_node(
    *,
    connect: Any,
    ensure_schema: Any,
    resolve_db_path: Any,
    workspace_lifecycle_store_path: Any,
    index_result: Any,
    workspace_root: Path,
    node: Mapping[str, Any],
    db_path: Path | None = None,
) -> dict[str, Any]:
    resolved_workspace_root = Path(workspace_root).expanduser().resolve()
    resolved_db_path = resolve_db_path(db_path, default=workspace_lifecycle_store_path(resolved_workspace_root))
    _assert_index_only_payload(node)
    payload_json = _stable_json(node)
    row = {
        "workspace_root": str(resolved_workspace_root),
        "node_id": _require_text("node.node_id", node.get("node_id")),
        "node_kind": _require_text("node.node_kind", node.get("node_kind")),
        "object_scope": _text(node.get("object_scope")) or "quest",
        "study_id": _text(node.get("study_id")),
        "quest_id": _text(node.get("quest_id")),
        "status": _text(node.get("status")) or "unknown",
        "source_path": _resolved_optional_path(node.get("source_path")),
        "payload_sha256": _sha256(payload_json),
        "payload_json": payload_json,
        "recorded_at": _utc_now(),
    }
    with connect(resolved_db_path) as conn:
        ensure_schema(conn)
        _upsert_row(conn, table="lineage_nodes", conflict_columns=("workspace_root", "node_id"), row=row)
    return index_result(db_path=resolved_db_path, indexed_table="lineage_nodes", indexed_count=1, scope="workspace")


def record_lineage_edge(
    *,
    connect: Any,
    ensure_schema: Any,
    resolve_db_path: Any,
    workspace_lifecycle_store_path: Any,
    index_result: Any,
    workspace_root: Path,
    edge: Mapping[str, Any],
    db_path: Path | None = None,
) -> dict[str, Any]:
    resolved_workspace_root = Path(workspace_root).expanduser().resolve()
    resolved_db_path = resolve_db_path(db_path, default=workspace_lifecycle_store_path(resolved_workspace_root))
    _assert_index_only_payload(edge)
    payload_json = _stable_json(edge)
    row = {
        "workspace_root": str(resolved_workspace_root),
        "edge_id": _require_text("edge.edge_id", edge.get("edge_id")),
        "source_node_id": _require_text("edge.source_node_id", edge.get("source_node_id")),
        "target_node_id": _require_text("edge.target_node_id", edge.get("target_node_id")),
        "edge_kind": _require_text("edge.edge_kind", edge.get("edge_kind")),
        "payload_sha256": _sha256(payload_json),
        "payload_json": payload_json,
        "recorded_at": _utc_now(),
    }
    with connect(resolved_db_path) as conn:
        ensure_schema(conn)
        _upsert_row(conn, table="lineage_edges", conflict_columns=("workspace_root", "edge_id"), row=row)
    return index_result(db_path=resolved_db_path, indexed_table="lineage_edges", indexed_count=1, scope="workspace")


def record_workspace_allocation(
    *,
    connect: Any,
    ensure_schema: Any,
    resolve_db_path: Any,
    workspace_lifecycle_store_path: Any,
    index_result: Any,
    workspace_root: Path,
    allocation: Mapping[str, Any],
    db_path: Path | None = None,
) -> dict[str, Any]:
    resolved_workspace_root = Path(workspace_root).expanduser().resolve()
    resolved_db_path = resolve_db_path(db_path, default=workspace_lifecycle_store_path(resolved_workspace_root))
    _assert_index_only_payload(allocation)
    payload_json = _stable_json(allocation)
    row = {
        "workspace_root": str(resolved_workspace_root),
        "allocation_id": _require_text("allocation.allocation_id", allocation.get("allocation_id")),
        "quest_id": _text(allocation.get("quest_id")),
        "study_id": _text(allocation.get("study_id")),
        "allocated_root": _resolved_optional_path(allocation.get("allocated_root")),
        "owner": _text(allocation.get("owner")),
        "status": _text(allocation.get("status")) or "unknown",
        "payload_sha256": _sha256(payload_json),
        "payload_json": payload_json,
        "recorded_at": _utc_now(),
    }
    with connect(resolved_db_path) as conn:
        ensure_schema(conn)
        _upsert_row(conn, table="workspace_allocations", conflict_columns=("workspace_root", "allocation_id"), row=row)
    return index_result(db_path=resolved_db_path, indexed_table="workspace_allocations", indexed_count=1, scope="workspace")


def record_runtime_snapshot(
    *,
    connect: Any,
    ensure_schema: Any,
    resolve_db_path: Any,
    workspace_lifecycle_store_path: Any,
    index_result: Any,
    workspace_root: Path,
    snapshot: Mapping[str, Any],
    db_path: Path | None = None,
) -> dict[str, Any]:
    resolved_workspace_root = Path(workspace_root).expanduser().resolve()
    resolved_db_path = resolve_db_path(db_path, default=workspace_lifecycle_store_path(resolved_workspace_root))
    _assert_index_only_payload(snapshot)
    payload_json = _stable_json(snapshot)
    row = {
        "workspace_root": str(resolved_workspace_root),
        "snapshot_id": _require_text("snapshot.snapshot_id", snapshot.get("snapshot_id")),
        "quest_id": _text(snapshot.get("quest_id")),
        "study_id": _text(snapshot.get("study_id")),
        "snapshot_kind": _text(snapshot.get("snapshot_kind")) or "runtime",
        "created_at": _text(snapshot.get("created_at")) or _utc_now(),
        "source_path": _resolved_optional_path(snapshot.get("source_path")),
        "payload_sha256": _sha256(payload_json),
        "payload_json": payload_json,
        "recorded_at": _utc_now(),
    }
    with connect(resolved_db_path) as conn:
        ensure_schema(conn)
        _upsert_row(conn, table="runtime_snapshots", conflict_columns=("workspace_root", "snapshot_id"), row=row)
    return index_result(db_path=resolved_db_path, indexed_table="runtime_snapshots", indexed_count=1, scope="workspace")


def record_snapshot_file_ref(
    *,
    connect: Any,
    ensure_schema: Any,
    resolve_db_path: Any,
    workspace_lifecycle_store_path: Any,
    index_result: Any,
    workspace_root: Path,
    ref: Mapping[str, Any],
    db_path: Path | None = None,
) -> dict[str, Any]:
    resolved_workspace_root = Path(workspace_root).expanduser().resolve()
    resolved_db_path = resolve_db_path(db_path, default=workspace_lifecycle_store_path(resolved_workspace_root))
    _assert_index_only_payload(ref)
    payload_json = _stable_json(ref)
    row = {
        "workspace_root": str(resolved_workspace_root),
        "snapshot_id": _require_text("ref.snapshot_id", ref.get("snapshot_id")),
        "ref_id": _require_text("ref.ref_id", ref.get("ref_id")),
        "ref_kind": _text(ref.get("ref_kind")) or "file",
        "target_path": _resolved_optional_path(ref.get("path") or ref.get("target_path")),
        "target_sha256": _text(ref.get("sha256")) or _text(ref.get("target_sha256")),
        "target_bytes": _int(ref.get("bytes") or ref.get("target_bytes")),
        "payload_sha256": _sha256(payload_json),
        "payload_json": payload_json,
        "recorded_at": _utc_now(),
    }
    with connect(resolved_db_path) as conn:
        ensure_schema(conn)
        _upsert_row(conn, table="snapshot_file_refs", conflict_columns=("workspace_root", "snapshot_id", "ref_id"), row=row)
    return index_result(db_path=resolved_db_path, indexed_table="snapshot_file_refs", indexed_count=1, scope="workspace")


def record_revision_diff(
    *,
    connect: Any,
    ensure_schema: Any,
    resolve_db_path: Any,
    workspace_lifecycle_store_path: Any,
    index_result: Any,
    workspace_root: Path,
    diff: Mapping[str, Any],
    db_path: Path | None = None,
) -> dict[str, Any]:
    resolved_workspace_root = Path(workspace_root).expanduser().resolve()
    resolved_db_path = resolve_db_path(db_path, default=workspace_lifecycle_store_path(resolved_workspace_root))
    _assert_index_only_payload(diff)
    payload_json = _stable_json(diff)
    row = {
        "workspace_root": str(resolved_workspace_root),
        "diff_id": _require_text("diff.diff_id", diff.get("diff_id")),
        "base_snapshot_id": _text(diff.get("base_snapshot_id")),
        "target_snapshot_id": _text(diff.get("target_snapshot_id")),
        "diff_kind": _text(diff.get("diff_kind")) or "revision",
        "source_path": _resolved_optional_path(diff.get("source_path")),
        "payload_sha256": _sha256(payload_json),
        "payload_json": payload_json,
        "recorded_at": _utc_now(),
    }
    with connect(resolved_db_path) as conn:
        ensure_schema(conn)
        _upsert_row(conn, table="revision_diffs", conflict_columns=("workspace_root", "diff_id"), row=row)
    return index_result(db_path=resolved_db_path, indexed_table="revision_diffs", indexed_count=1, scope="workspace")


def record_canvas_projection(
    *,
    connect: Any,
    ensure_schema: Any,
    resolve_db_path: Any,
    workspace_lifecycle_store_path: Any,
    index_result: Any,
    workspace_root: Path,
    projection: Mapping[str, Any],
    db_path: Path | None = None,
) -> dict[str, Any]:
    resolved_workspace_root = Path(workspace_root).expanduser().resolve()
    resolved_db_path = resolve_db_path(db_path, default=workspace_lifecycle_store_path(resolved_workspace_root))
    _assert_index_only_payload(projection)
    payload_json = _stable_json(projection)
    row = {
        "workspace_root": str(resolved_workspace_root),
        "projection_id": _require_text("projection.projection_id", projection.get("projection_id")),
        "snapshot_id": _text(projection.get("snapshot_id")),
        "canvas_id": _require_text("projection.canvas_id", projection.get("canvas_id")),
        "projection_kind": _text(projection.get("projection_kind")) or "canvas",
        "status": _text(projection.get("status")) or "unknown",
        "source_path": _resolved_optional_path(projection.get("source_path")),
        "payload_sha256": _sha256(payload_json),
        "payload_json": payload_json,
        "recorded_at": _utc_now(),
    }
    with connect(resolved_db_path) as conn:
        ensure_schema(conn)
        _upsert_row(conn, table="canvas_projection", conflict_columns=("workspace_root", "projection_id"), row=row)
    return index_result(db_path=resolved_db_path, indexed_table="canvas_projection", indexed_count=1, scope="workspace")


def read_lifecycle_records(
    *,
    connect: Any,
    ensure_schema: Any,
    db_path: Path,
    table: str,
) -> list[dict[str, Any]]:
    if table not in LINEAGE_INDEX_TABLE_NAMES:
        raise ValueError(f"unsupported lifecycle table: {table}")
    resolved_db_path = Path(db_path).expanduser().resolve()
    if not resolved_db_path.exists():
        return []
    with connect(resolved_db_path) as conn:
        ensure_schema(conn)
        rows = conn.execute(f"SELECT payload_json FROM {table} ORDER BY rowid").fetchall()
    return [json.loads(row[0]) for row in rows]


def _upsert_row(
    conn: sqlite3.Connection,
    *,
    table: str,
    conflict_columns: tuple[str, ...],
    row: Mapping[str, object],
) -> None:
    columns = tuple(row.keys())
    assignments = tuple(column for column in columns if column not in set(conflict_columns))
    conn.execute(
        f"""
        INSERT INTO {table}({", ".join(columns)})
        VALUES ({", ".join("?" for _ in columns)})
        ON CONFLICT({", ".join(conflict_columns)}) DO UPDATE SET
            {", ".join(f"{column}=excluded.{column}" for column in assignments)}
        """,
        tuple(row.values()),
    )


def _stable_json(payload: object) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def _sha256(payload: str) -> str:
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def _text(value: object) -> str:
    return value.strip() if isinstance(value, str) else ""


def _require_text(label: str, value: object) -> str:
    text = _text(value)
    if not text:
        raise ValueError(f"{label} must be a non-empty string")
    return text


def _int(value: object) -> int:
    if isinstance(value, bool):
        return 0
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _resolved_optional_path(value: object) -> str | None:
    text = _text(value)
    return str(Path(text).expanduser().resolve()) if text else None


def _assert_index_only_payload(payload: Mapping[str, Any]) -> None:
    authority_scope = _string_list(payload.get("authority_scope"))
    authority_surfaces = _string_list(payload.get("authority_surfaces"))
    invalid_scopes = [scope for scope in authority_scope if scope in SQLITE_FORBIDDEN_AUTHORITY_SURFACES]
    forbidden_surfaces = [surface for surface in authority_surfaces if surface in FILE_AUTHORITY_SURFACES]
    if invalid_scopes or forbidden_surfaces:
        raise ValueError(
            "runtime lifecycle SQLite store is index-only; file/study/publication/artifact truth remains outside SQLite"
        )


def _string_list(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list | tuple | set):
        return [str(item) for item in value]
    return [str(value)]


__all__ = [
    "LINEAGE_INDEX_TABLE_NAMES",
    "ensure_lineage_index_schema",
    "read_lifecycle_records",
    "record_canvas_projection",
    "record_lineage_edge",
    "record_lineage_node",
    "record_revision_diff",
    "record_runtime_snapshot",
    "record_snapshot_file_ref",
    "record_workspace_allocation",
]
