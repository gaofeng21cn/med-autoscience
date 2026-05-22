from __future__ import annotations

import hashlib
from pathlib import Path
import sqlite3
from typing import Any

from ..runtime_lifecycle_contract import SCHEMA_VERSION, SURFACE_KIND
from . import git_tracking, lineage_indexes, lifecycle_ref_indexes


def connect(db_path: Path) -> sqlite3.Connection:
    git_tracking.assert_db_not_tracked(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 5000")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS lifecycle_metadata(
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS watch_states(
            quest_root TEXT PRIMARY KEY,
            updated_at TEXT NOT NULL,
            controllers_json TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            payload_sha256 TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS runtime_reports(
            quest_root TEXT NOT NULL,
            report_group TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            status TEXT NOT NULL,
            json_path TEXT NOT NULL,
            md_path TEXT NOT NULL,
            latest_json_path TEXT NOT NULL,
            latest_md_path TEXT NOT NULL,
            payload_sha256 TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            recorded_at TEXT NOT NULL,
            PRIMARY KEY (quest_root, report_group, timestamp)
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS workspace_storage_audits(
            workspace_root TEXT NOT NULL,
            recorded_at TEXT NOT NULL,
            mode TEXT NOT NULL,
            report_path TEXT NOT NULL,
            latest_report_path TEXT NOT NULL,
            study_count INTEGER NOT NULL,
            estimated_release_bytes INTEGER NOT NULL,
            actual_release_bytes INTEGER NOT NULL,
            runtime_total_bytes INTEGER NOT NULL,
            study_artifact_total_bytes INTEGER NOT NULL,
            summary_json TEXT NOT NULL,
            categories_json TEXT NOT NULL,
            payload_sha256 TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            PRIMARY KEY (workspace_root, recorded_at)
        )
        """
    )
    lineage_indexes.ensure_lineage_index_schema(conn)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS runtime_events(
            quest_root TEXT NOT NULL,
            event_id TEXT NOT NULL,
            quest_id TEXT NOT NULL,
            study_id TEXT NOT NULL,
            emitted_at TEXT NOT NULL,
            event_source TEXT NOT NULL,
            event_kind TEXT NOT NULL,
            status TEXT NOT NULL,
            active_run_id TEXT,
            summary_ref TEXT NOT NULL,
            artifact_path TEXT NOT NULL,
            latest_path TEXT NOT NULL,
            cursor TEXT NOT NULL,
            payload_sha256 TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            recorded_at TEXT NOT NULL,
            PRIMARY KEY (quest_root, event_id)
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS archive_refs(
            quest_root TEXT NOT NULL,
            archive_id TEXT NOT NULL,
            archived_at TEXT NOT NULL,
            archive_path TEXT NOT NULL,
            archive_format TEXT NOT NULL,
            sha256 TEXT NOT NULL,
            bytes INTEGER NOT NULL,
            source_manifest_path TEXT,
            restore_proof_path TEXT,
            source_buckets_json TEXT NOT NULL,
            payload_sha256 TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            recorded_at TEXT NOT NULL,
            PRIMARY KEY (quest_root, archive_id)
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS report_index(
            object_root TEXT NOT NULL,
            object_scope TEXT NOT NULL,
            report_group TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            status TEXT NOT NULL,
            json_path TEXT NOT NULL,
            md_path TEXT,
            latest_json_path TEXT NOT NULL,
            latest_md_path TEXT,
            payload_sha256 TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            recorded_at TEXT NOT NULL,
            PRIMARY KEY (object_root, object_scope, report_group, timestamp)
        )
        """
    )
    lifecycle_ref_indexes.ensure_lifecycle_ref_index_schema(conn)
    conn.execute(
        "INSERT OR REPLACE INTO lifecycle_metadata(key, value) VALUES ('schema_version', ?)",
        (str(SCHEMA_VERSION),),
    )
    conn.execute(
        "INSERT OR REPLACE INTO lifecycle_metadata(key, value) VALUES ('surface_kind', ?)",
        (SURFACE_KIND,),
    )


def inspect_store(db_path: Path) -> dict[str, Any]:
    resolved_db_path = Path(db_path).expanduser().resolve()
    if not resolved_db_path.exists():
        return {
            "surface_kind": SURFACE_KIND,
            "schema_version": SCHEMA_VERSION,
            "db_path": str(resolved_db_path),
            "status": "missing",
            "tables": {},
        }
    with connect(resolved_db_path) as conn:
        ensure_schema(conn)
        tables = {
            table: _table_count(conn, table)
            for table in (
                "watch_states",
                "runtime_reports",
                "workspace_storage_audits",
                *lineage_indexes.LINEAGE_INDEX_TABLE_NAMES,
                "runtime_events",
                "archive_refs",
                *lifecycle_ref_indexes.LIFECYCLE_REF_INDEX_TABLE_NAMES,
                "report_index",
            )
        }
    return {
        "surface_kind": SURFACE_KIND,
        "schema_version": SCHEMA_VERSION,
        "db_path": str(resolved_db_path),
        "status": "ready",
        "tables": tables,
    }


def record_report_index_row(
    conn: sqlite3.Connection,
    *,
    object_root: str,
    object_scope: str,
    report_group: str,
    timestamp: str,
    status: str,
    json_path: str,
    md_path: str | None,
    latest_json_path: str,
    latest_md_path: str | None,
    payload_json: str,
    recorded_at: str,
) -> None:
    conn.execute(
        """
        INSERT INTO report_index(
            object_root, object_scope, report_group, timestamp, status, json_path,
            md_path, latest_json_path, latest_md_path, payload_sha256, payload_json, recorded_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(object_root, object_scope, report_group, timestamp) DO UPDATE SET
            status=excluded.status,
            json_path=excluded.json_path,
            md_path=excluded.md_path,
            latest_json_path=excluded.latest_json_path,
            latest_md_path=excluded.latest_md_path,
            payload_sha256=excluded.payload_sha256,
            payload_json=excluded.payload_json,
            recorded_at=excluded.recorded_at
        """,
        (
            object_root,
            object_scope,
            report_group,
            timestamp,
            status,
            json_path,
            md_path,
            latest_json_path,
            latest_md_path,
            _sha256(payload_json),
            payload_json,
            recorded_at,
        ),
    )


def index_result(*, db_path: Path, indexed_table: str, indexed_count: int, scope: str) -> dict[str, Any]:
    return {
        "surface_kind": SURFACE_KIND,
        "schema_version": SCHEMA_VERSION,
        "status": "indexed",
        "scope": scope,
        "db_path": str(db_path),
        "indexed_table": indexed_table,
        "indexed_count": indexed_count,
    }


def resolve_db_path(db_path: Path | None, *, default: Path) -> Path:
    return Path(db_path if db_path is not None else default).expanduser().resolve()


def _table_count(conn: sqlite3.Connection, table: str) -> int:
    row = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()
    return int(row[0]) if row else 0


def _sha256(payload: str) -> str:
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


__all__ = [
    "connect",
    "ensure_schema",
    "index_result",
    "inspect_store",
    "record_report_index_row",
    "resolve_db_path",
]
