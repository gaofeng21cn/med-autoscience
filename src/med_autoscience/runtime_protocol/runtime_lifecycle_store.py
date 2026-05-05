from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
import sqlite3
from typing import Any


SCHEMA_VERSION = 1
SURFACE_KIND = "runtime_lifecycle_sqlite_index"
DEFAULT_DB_FILENAME = "runtime_lifecycle.sqlite"


def quest_lifecycle_store_path(quest_root: Path) -> Path:
    return Path(quest_root).expanduser().resolve() / "artifacts" / "runtime" / DEFAULT_DB_FILENAME


def workspace_lifecycle_store_path(workspace_root: Path) -> Path:
    return Path(workspace_root).expanduser().resolve() / "artifacts" / "runtime" / DEFAULT_DB_FILENAME


def record_watch_state(
    *,
    quest_root: Path,
    payload: Mapping[str, Any],
    db_path: Path | None = None,
) -> dict[str, Any]:
    resolved_quest_root = Path(quest_root).expanduser().resolve()
    resolved_db_path = _resolve_db_path(db_path, default=quest_lifecycle_store_path(resolved_quest_root))
    payload_json = _stable_json(payload)
    updated_at = _text(payload.get("updated_at")) or _utc_now()
    with _connect(resolved_db_path) as conn:
        _ensure_schema(conn)
        conn.execute(
            """
            INSERT INTO watch_states(
                quest_root, updated_at, controllers_json, payload_json, payload_sha256
            ) VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(quest_root) DO UPDATE SET
                updated_at=excluded.updated_at,
                controllers_json=excluded.controllers_json,
                payload_json=excluded.payload_json,
                payload_sha256=excluded.payload_sha256
            """,
            (
                str(resolved_quest_root),
                updated_at,
                _stable_json(payload.get("controllers") if isinstance(payload.get("controllers"), Mapping) else {}),
                payload_json,
                _sha256(payload_json),
            ),
        )
    return _index_result(
        db_path=resolved_db_path,
        indexed_table="watch_states",
        indexed_count=1,
        scope="quest",
    )


def record_runtime_report(
    *,
    quest_root: Path,
    report_group: str,
    timestamp: str,
    report: Mapping[str, Any],
    json_path: Path,
    md_path: Path,
    db_path: Path | None = None,
) -> dict[str, Any]:
    resolved_quest_root = Path(quest_root).expanduser().resolve()
    resolved_db_path = _resolve_db_path(db_path, default=quest_lifecycle_store_path(resolved_quest_root))
    payload_json = _stable_json(report)
    status = _report_status(report)
    latest_json_path = Path(json_path).parent / "latest.json"
    latest_md_path = Path(md_path).parent / "latest.md"
    with _connect(resolved_db_path) as conn:
        _ensure_schema(conn)
        conn.execute(
            """
            INSERT INTO runtime_reports(
                quest_root, report_group, timestamp, status, json_path, md_path,
                latest_json_path, latest_md_path, payload_sha256, payload_json, recorded_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(quest_root, report_group, timestamp) DO UPDATE SET
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
                str(resolved_quest_root),
                _require_text("report_group", report_group),
                _require_text("timestamp", timestamp),
                status,
                str(Path(json_path).expanduser().resolve()),
                str(Path(md_path).expanduser().resolve()),
                str(latest_json_path.expanduser().resolve()),
                str(latest_md_path.expanduser().resolve()),
                _sha256(payload_json),
                payload_json,
                _utc_now(),
            ),
        )
    return _index_result(
        db_path=resolved_db_path,
        indexed_table="runtime_reports",
        indexed_count=1,
        scope="quest",
    )


def record_workspace_storage_audit(
    *,
    workspace_root: Path,
    report: Mapping[str, Any],
    report_path: Path,
    latest_report_path: Path,
    db_path: Path | None = None,
) -> dict[str, Any]:
    resolved_workspace_root = Path(workspace_root).expanduser().resolve()
    resolved_db_path = _resolve_db_path(db_path, default=workspace_lifecycle_store_path(resolved_workspace_root))
    summary = _mapping(report.get("summary"))
    categories = _mapping(report.get("categories"))
    recorded_at = _require_text("report.recorded_at", report.get("recorded_at"))
    payload_json = _stable_json(report)
    with _connect(resolved_db_path) as conn:
        _ensure_schema(conn)
        conn.execute(
            """
            INSERT INTO workspace_storage_audits(
                workspace_root, recorded_at, mode, report_path, latest_report_path,
                study_count, estimated_release_bytes, actual_release_bytes,
                runtime_total_bytes, study_artifact_total_bytes,
                summary_json, categories_json, payload_sha256, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(workspace_root, recorded_at) DO UPDATE SET
                mode=excluded.mode,
                report_path=excluded.report_path,
                latest_report_path=excluded.latest_report_path,
                study_count=excluded.study_count,
                estimated_release_bytes=excluded.estimated_release_bytes,
                actual_release_bytes=excluded.actual_release_bytes,
                runtime_total_bytes=excluded.runtime_total_bytes,
                study_artifact_total_bytes=excluded.study_artifact_total_bytes,
                summary_json=excluded.summary_json,
                categories_json=excluded.categories_json,
                payload_sha256=excluded.payload_sha256,
                payload_json=excluded.payload_json
            """,
            (
                str(resolved_workspace_root),
                recorded_at,
                _text(report.get("mode")) or "unknown",
                str(Path(report_path).expanduser().resolve()),
                str(Path(latest_report_path).expanduser().resolve()),
                _int(summary.get("study_count")),
                _int(summary.get("estimated_release_bytes")),
                _int(summary.get("actual_release_bytes")),
                _int(summary.get("runtime_total_bytes")),
                _int(summary.get("study_artifact_total_bytes")),
                _stable_json(summary),
                _stable_json(categories),
                _sha256(payload_json),
                payload_json,
            ),
        )
    return _index_result(
        db_path=resolved_db_path,
        indexed_table="workspace_storage_audits",
        indexed_count=1,
        scope="workspace",
    )


def inspect_lifecycle_store(db_path: Path) -> dict[str, Any]:
    resolved_db_path = Path(db_path).expanduser().resolve()
    if not resolved_db_path.exists():
        return {
            "surface_kind": SURFACE_KIND,
            "schema_version": SCHEMA_VERSION,
            "db_path": str(resolved_db_path),
            "status": "missing",
            "tables": {},
        }
    with _connect(resolved_db_path) as conn:
        _ensure_schema(conn)
        tables = {
            table: _table_count(conn, table)
            for table in ("watch_states", "runtime_reports", "workspace_storage_audits")
        }
    return {
        "surface_kind": SURFACE_KIND,
        "schema_version": SCHEMA_VERSION,
        "db_path": str(resolved_db_path),
        "status": "ready",
        "tables": tables,
    }


def _connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 5000")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def _ensure_schema(conn: sqlite3.Connection) -> None:
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
    conn.execute(
        "INSERT OR REPLACE INTO lifecycle_metadata(key, value) VALUES ('schema_version', ?)",
        (str(SCHEMA_VERSION),),
    )
    conn.execute(
        "INSERT OR REPLACE INTO lifecycle_metadata(key, value) VALUES ('surface_kind', ?)",
        (SURFACE_KIND,),
    )


def _table_count(conn: sqlite3.Connection, table: str) -> int:
    row = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()
    return int(row[0]) if row else 0


def _index_result(*, db_path: Path, indexed_table: str, indexed_count: int, scope: str) -> dict[str, Any]:
    return {
        "surface_kind": SURFACE_KIND,
        "schema_version": SCHEMA_VERSION,
        "status": "indexed",
        "scope": scope,
        "db_path": str(db_path),
        "indexed_table": indexed_table,
        "indexed_count": indexed_count,
    }


def _resolve_db_path(db_path: Path | None, *, default: Path) -> Path:
    return Path(db_path if db_path is not None else default).expanduser().resolve()


def _report_status(report: Mapping[str, Any]) -> str:
    for key in ("status", "quest_status", "state"):
        value = _text(report.get(key))
        if value:
            return value
    return "unknown"


def _stable_json(payload: object) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def _sha256(payload: str) -> str:
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


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


__all__ = [
    "DEFAULT_DB_FILENAME",
    "SCHEMA_VERSION",
    "SURFACE_KIND",
    "inspect_lifecycle_store",
    "quest_lifecycle_store_path",
    "record_runtime_report",
    "record_watch_state",
    "record_workspace_storage_audit",
    "workspace_lifecycle_store_path",
]
