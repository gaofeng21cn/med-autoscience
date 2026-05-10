from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
import sqlite3
import subprocess
from typing import Any

from .runtime_lifecycle_contract import (
    DEFAULT_DB_FILENAME,
    SCHEMA_VERSION,
    SURFACE_KIND,
)
from .runtime_lifecycle_store_parts import family_adoption, lineage_indexes, report_payloads, sidecar_indexes


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
        _record_report_index_row(
            conn,
            object_root=str(resolved_quest_root),
            object_scope="quest",
            report_group=_require_text("report_group", report_group),
            timestamp=_require_text("timestamp", timestamp),
            status=status,
            json_path=str(Path(json_path).expanduser().resolve()),
            md_path=str(Path(md_path).expanduser().resolve()),
            latest_json_path=str(latest_json_path.expanduser().resolve()),
            latest_md_path=str(latest_md_path.expanduser().resolve()),
            payload_json=payload_json,
            recorded_at=_utc_now(),
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
    payload_json = report_payloads.workspace_storage_audit_projection_payload(
        report=report,
        report_path=report_path,
        latest_report_path=latest_report_path,
    )
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
                report_payloads.as_int(summary.get("study_count")),
                report_payloads.as_int(summary.get("estimated_release_bytes")),
                report_payloads.as_int(summary.get("actual_release_bytes")),
                report_payloads.as_int(summary.get("runtime_total_bytes")),
                report_payloads.as_int(summary.get("study_artifact_total_bytes")),
                _stable_json(summary),
                _stable_json(categories),
                _sha256(payload_json),
                payload_json,
            ),
        )
        _record_report_index_row(
            conn,
            object_root=str(resolved_workspace_root),
            object_scope="workspace",
            report_group="workspace_storage_audit",
            timestamp=recorded_at,
            status=_text(report.get("mode")) or "unknown",
            json_path=str(Path(report_path).expanduser().resolve()),
            md_path=None,
            latest_json_path=str(Path(latest_report_path).expanduser().resolve()),
            latest_md_path=None,
            payload_json=payload_json,
            recorded_at=recorded_at,
        )
    return _index_result(
        db_path=resolved_db_path,
        indexed_table="workspace_storage_audits",
        indexed_count=1,
        scope="workspace",
    )


def record_runtime_event(
    *,
    quest_root: Path,
    event: Mapping[str, Any],
    artifact_path: Path,
    latest_path: Path,
    db_path: Path | None = None,
) -> dict[str, Any]:
    resolved_quest_root = Path(quest_root).expanduser().resolve()
    resolved_db_path = _resolve_db_path(db_path, default=quest_lifecycle_store_path(resolved_quest_root))
    payload_json = _stable_json(event)
    emitted_at = _require_text("event.emitted_at", event.get("emitted_at"))
    event_id = _require_text("event.event_id", event.get("event_id"))
    status_snapshot = _mapping(event.get("status_snapshot"))
    outer_loop_input = _mapping(event.get("outer_loop_input"))
    with _connect(resolved_db_path) as conn:
        _ensure_schema(conn)
        conn.execute(
            """
            INSERT INTO runtime_events(
                quest_root, event_id, quest_id, study_id, emitted_at, event_source,
                event_kind, status, active_run_id, summary_ref, artifact_path,
                latest_path, cursor, payload_sha256, payload_json, recorded_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(quest_root, event_id) DO UPDATE SET
                quest_id=excluded.quest_id,
                study_id=excluded.study_id,
                emitted_at=excluded.emitted_at,
                event_source=excluded.event_source,
                event_kind=excluded.event_kind,
                status=excluded.status,
                active_run_id=excluded.active_run_id,
                summary_ref=excluded.summary_ref,
                artifact_path=excluded.artifact_path,
                latest_path=excluded.latest_path,
                cursor=excluded.cursor,
                payload_sha256=excluded.payload_sha256,
                payload_json=excluded.payload_json,
                recorded_at=excluded.recorded_at
            """,
            (
                str(resolved_quest_root),
                event_id,
                _require_text("event.quest_id", event.get("quest_id")),
                _text(event.get("study_id")),
                emitted_at,
                _require_text("event.event_source", event.get("event_source")),
                _require_text("event.event_kind", event.get("event_kind")),
                _event_status(status_snapshot=status_snapshot, outer_loop_input=outer_loop_input),
                _event_active_run_id(status_snapshot=status_snapshot, outer_loop_input=outer_loop_input),
                _require_text("event.summary_ref", event.get("summary_ref")),
                str(Path(artifact_path).expanduser().resolve()),
                str(Path(latest_path).expanduser().resolve()),
                _event_cursor(emitted_at=emitted_at, event_id=event_id),
                _sha256(payload_json),
                payload_json,
                _utc_now(),
            ),
        )
    return _index_result(
        db_path=resolved_db_path,
        indexed_table="runtime_events",
        indexed_count=1,
        scope="quest",
    )


def record_archive_ref(
    *,
    quest_root: Path,
    archive_ref: Mapping[str, Any],
    db_path: Path | None = None,
) -> dict[str, Any]:
    resolved_quest_root = Path(quest_root).expanduser().resolve()
    resolved_db_path = _resolve_db_path(db_path, default=quest_lifecycle_store_path(resolved_quest_root))
    archive_id = _require_text("archive_ref.archive_id", archive_ref.get("archive_id"))
    archive_path = Path(_require_text("archive_ref.archive_path", archive_ref.get("archive_path"))).expanduser().resolve()
    source_manifest_path = _text(archive_ref.get("source_manifest_path"))
    restore_proof_path = _text(archive_ref.get("restore_proof_path"))
    archived_at = _text(archive_ref.get("archived_at")) or _utc_now()
    payload_json = _stable_json(archive_ref)
    with _connect(resolved_db_path) as conn:
        _ensure_schema(conn)
        conn.execute(
            """
            INSERT INTO archive_refs(
                quest_root, archive_id, archived_at, archive_path, archive_format,
                sha256, bytes, source_manifest_path, restore_proof_path,
                source_buckets_json, payload_sha256, payload_json, recorded_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(quest_root, archive_id) DO UPDATE SET
                archived_at=excluded.archived_at,
                archive_path=excluded.archive_path,
                archive_format=excluded.archive_format,
                sha256=excluded.sha256,
                bytes=excluded.bytes,
                source_manifest_path=excluded.source_manifest_path,
                restore_proof_path=excluded.restore_proof_path,
                source_buckets_json=excluded.source_buckets_json,
                payload_sha256=excluded.payload_sha256,
                payload_json=excluded.payload_json,
                recorded_at=excluded.recorded_at
            """,
            (
                str(resolved_quest_root),
                archive_id,
                archived_at,
                str(archive_path),
                _text(archive_ref.get("archive_format")) or "unknown",
                _require_text("archive_ref.sha256", archive_ref.get("sha256")),
                report_payloads.as_int(archive_ref.get("bytes")),
                str(Path(source_manifest_path).expanduser().resolve()) if source_manifest_path else None,
                str(Path(restore_proof_path).expanduser().resolve()) if restore_proof_path else None,
                _stable_json(archive_ref.get("source_buckets") if isinstance(archive_ref.get("source_buckets"), list) else []),
                _sha256(payload_json),
                payload_json,
                _utc_now(),
            ),
        )
    return _index_result(
        db_path=resolved_db_path,
        indexed_table="archive_refs",
        indexed_count=1,
        scope="quest",
    )


def record_lineage_node(
    *,
    workspace_root: Path,
    node: Mapping[str, Any],
    db_path: Path | None = None,
) -> dict[str, Any]:
    return lineage_indexes.record_lineage_node(
        connect=_connect,
        ensure_schema=_ensure_schema,
        resolve_db_path=_resolve_db_path,
        workspace_lifecycle_store_path=workspace_lifecycle_store_path,
        index_result=_index_result,
        workspace_root=workspace_root,
        node=node,
        db_path=db_path,
    )


def record_lineage_edge(
    *,
    workspace_root: Path,
    edge: Mapping[str, Any],
    db_path: Path | None = None,
) -> dict[str, Any]:
    return lineage_indexes.record_lineage_edge(
        connect=_connect,
        ensure_schema=_ensure_schema,
        resolve_db_path=_resolve_db_path,
        workspace_lifecycle_store_path=workspace_lifecycle_store_path,
        index_result=_index_result,
        workspace_root=workspace_root,
        edge=edge,
        db_path=db_path,
    )


def record_workspace_allocation(
    *,
    workspace_root: Path,
    allocation: Mapping[str, Any],
    db_path: Path | None = None,
) -> dict[str, Any]:
    return lineage_indexes.record_workspace_allocation(
        connect=_connect,
        ensure_schema=_ensure_schema,
        resolve_db_path=_resolve_db_path,
        workspace_lifecycle_store_path=workspace_lifecycle_store_path,
        index_result=_index_result,
        workspace_root=workspace_root,
        allocation=allocation,
        db_path=db_path,
    )


def record_runtime_snapshot(
    *,
    workspace_root: Path,
    snapshot: Mapping[str, Any],
    db_path: Path | None = None,
) -> dict[str, Any]:
    return lineage_indexes.record_runtime_snapshot(
        connect=_connect,
        ensure_schema=_ensure_schema,
        resolve_db_path=_resolve_db_path,
        workspace_lifecycle_store_path=workspace_lifecycle_store_path,
        index_result=_index_result,
        workspace_root=workspace_root,
        snapshot=snapshot,
        db_path=db_path,
    )


def record_snapshot_file_ref(
    *,
    workspace_root: Path,
    ref: Mapping[str, Any],
    db_path: Path | None = None,
) -> dict[str, Any]:
    return lineage_indexes.record_snapshot_file_ref(
        connect=_connect,
        ensure_schema=_ensure_schema,
        resolve_db_path=_resolve_db_path,
        workspace_lifecycle_store_path=workspace_lifecycle_store_path,
        index_result=_index_result,
        workspace_root=workspace_root,
        ref=ref,
        db_path=db_path,
    )


def record_revision_diff(
    *,
    workspace_root: Path,
    diff: Mapping[str, Any],
    db_path: Path | None = None,
) -> dict[str, Any]:
    return lineage_indexes.record_revision_diff(
        connect=_connect,
        ensure_schema=_ensure_schema,
        resolve_db_path=_resolve_db_path,
        workspace_lifecycle_store_path=workspace_lifecycle_store_path,
        index_result=_index_result,
        workspace_root=workspace_root,
        diff=diff,
        db_path=db_path,
    )


def record_canvas_projection(
    *,
    workspace_root: Path,
    projection: Mapping[str, Any],
    db_path: Path | None = None,
) -> dict[str, Any]:
    return lineage_indexes.record_canvas_projection(
        connect=_connect,
        ensure_schema=_ensure_schema,
        resolve_db_path=_resolve_db_path,
        workspace_lifecycle_store_path=workspace_lifecycle_store_path,
        index_result=_index_result,
        workspace_root=workspace_root,
        projection=projection,
        db_path=db_path,
    )


def record_study_macro_state_snapshot(
    *,
    study_root: Path,
    snapshot: Mapping[str, Any],
    snapshot_path: Path,
    db_path: Path | None = None,
) -> dict[str, Any]:
    return sidecar_indexes.record_study_macro_state_snapshot(
        connect=_connect,
        ensure_schema=_ensure_schema,
        resolve_db_path=_resolve_db_path,
        workspace_lifecycle_store_path=workspace_lifecycle_store_path,
        index_result=_index_result,
        study_root=study_root,
        snapshot=snapshot,
        snapshot_path=snapshot_path,
        db_path=db_path,
    )


def record_owner_route_receipt(
    *,
    study_root: Path,
    receipt: Mapping[str, Any],
    receipt_path: Path,
    db_path: Path | None = None,
) -> dict[str, Any]:
    return sidecar_indexes.record_owner_route_receipt(
        connect=_connect,
        ensure_schema=_ensure_schema,
        resolve_db_path=_resolve_db_path,
        workspace_lifecycle_store_path=workspace_lifecycle_store_path,
        index_result=_index_result,
        study_root=study_root,
        receipt=receipt,
        receipt_path=receipt_path,
        db_path=db_path,
    )


def record_dispatch_receipt(
    *,
    quest_root: Path,
    receipt: Mapping[str, Any],
    receipt_path: Path,
    db_path: Path | None = None,
) -> dict[str, Any]:
    return sidecar_indexes.record_dispatch_receipt(
        connect=_connect,
        ensure_schema=_ensure_schema,
        resolve_db_path=_resolve_db_path,
        quest_lifecycle_store_path=quest_lifecycle_store_path,
        index_result=_index_result,
        quest_root=quest_root,
        receipt=receipt,
        receipt_path=receipt_path,
        db_path=db_path,
    )


def record_turn_receipt(*, quest_root: Path, receipt: Mapping[str, Any], receipt_path: Path, db_path: Path | None = None) -> dict[str, Any]:
    return sidecar_indexes.record_turn_receipt(
        connect=_connect, ensure_schema=_ensure_schema, resolve_db_path=_resolve_db_path,
        quest_lifecycle_store_path=quest_lifecycle_store_path, index_result=_index_result,
        quest_root=quest_root, receipt=receipt, receipt_path=receipt_path, db_path=db_path,
    )


def record_paper_work_unit_receipt(
    *,
    study_root: Path,
    quest_root: Path,
    receipt: Mapping[str, Any],
    receipt_path: Path,
    db_path: Path | None = None,
) -> dict[str, Any]:
    return sidecar_indexes.record_paper_work_unit_receipt(
        connect=_connect,
        ensure_schema=_ensure_schema,
        resolve_db_path=_resolve_db_path,
        workspace_lifecycle_store_path=workspace_lifecycle_store_path,
        index_result=_index_result,
        study_root=study_root,
        quest_root=quest_root,
        receipt=receipt,
        receipt_path=receipt_path,
        db_path=db_path,
    )


def record_surface_ref(
    *,
    object_root: Path,
    object_scope: str,
    ref: Mapping[str, Any],
    ref_path: Path,
    db_path: Path | None = None,
) -> dict[str, Any]:
    return sidecar_indexes.record_surface_ref(
        connect=_connect,
        ensure_schema=_ensure_schema,
        resolve_db_path=_resolve_db_path,
        workspace_lifecycle_store_path=workspace_lifecycle_store_path,
        index_result=_index_result,
        object_root=object_root,
        object_scope=object_scope,
        ref=ref,
        ref_path=ref_path,
        db_path=db_path,
    )


def build_opl_family_adoption_surface(
    *,
    workspace_root: Path,
    db_path: Path | None = None,
) -> dict[str, Any]:
    return family_adoption.build_opl_family_adoption_surface(
        connect=_connect,
        ensure_schema=_ensure_schema,
        inspect_lifecycle_store=inspect_lifecycle_store,
        workspace_lifecycle_store_path=workspace_lifecycle_store_path,
        workspace_root=workspace_root,
        db_path=db_path,
    )


def build_product_entry_adoption_projection(
    *,
    workspace_root: Path,
    db_path: Path | None = None,
) -> dict[str, Any]:
    return family_adoption.build_product_entry_adoption_projection(
        workspace_root=workspace_root,
        db_path=db_path,
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
            for table in (
                "watch_states",
                "runtime_reports",
                "workspace_storage_audits",
                *lineage_indexes.LINEAGE_INDEX_TABLE_NAMES,
                "runtime_events",
                "archive_refs",
                *sidecar_indexes.SIDECAR_INDEX_TABLE_NAMES,
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


def _connect(db_path: Path) -> sqlite3.Connection:
    _assert_db_not_tracked(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 5000")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def _assert_db_not_tracked(db_path: Path) -> None:
    tracked_paths = _tracked_sqlite_sidecars(db_path)
    if tracked_paths:
        tracked = ", ".join(tracked_paths)
        raise RuntimeError(f"runtime lifecycle SQLite sidecar must not be tracked by Git: {tracked}")


def _tracked_sqlite_sidecars(db_path: Path) -> tuple[str, ...]:
    resolved_db_path = Path(db_path).expanduser().resolve()
    git_root = _git_root_for_path(resolved_db_path.parent)
    if git_root is None:
        return ()
    candidates = (
        resolved_db_path,
        Path(f"{resolved_db_path}-wal"),
        Path(f"{resolved_db_path}-shm"),
    )
    tracked: list[str] = []
    for candidate in candidates:
        try:
            relative = candidate.relative_to(git_root)
        except ValueError:
            continue
        result = subprocess.run(
            ["git", "-C", str(git_root), "ls-files", "--cached", "--error-unmatch", "--", relative.as_posix()],
            check=False,
            text=True,
            capture_output=True,
        )
        if result.returncode == 0:
            tracked.append(relative.as_posix())
    return tuple(tracked)


def _git_root_for_path(path: Path) -> Path | None:
    result = subprocess.run(
        ["git", "-C", str(path), "rev-parse", "--show-toplevel"],
        check=False,
        text=True,
        capture_output=True,
    )
    if result.returncode != 0:
        return None
    root = result.stdout.strip()
    return Path(root).resolve() if root else None


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
    sidecar_indexes.ensure_sidecar_index_schema(conn)
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


def read_lifecycle_records(db_path: Path, table: str) -> list[dict[str, Any]]:
    return lineage_indexes.read_lifecycle_records(
        connect=_connect,
        ensure_schema=_ensure_schema,
        db_path=db_path,
        table=table,
    )


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


def _record_report_index_row(
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


def _event_status(*, status_snapshot: Mapping[str, Any], outer_loop_input: Mapping[str, Any]) -> str:
    for payload in (status_snapshot, outer_loop_input):
        for key in ("quest_status", "display_status", "status"):
            value = _text(payload.get(key))
            if value:
                return value
    return "unknown"


def _event_active_run_id(*, status_snapshot: Mapping[str, Any], outer_loop_input: Mapping[str, Any]) -> str | None:
    for payload in (status_snapshot, outer_loop_input):
        value = _text(payload.get("active_run_id"))
        if value:
            return value
    return None


def _event_cursor(*, emitted_at: str, event_id: str) -> str:
    return f"{emitted_at}::{event_id}"


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


__all__ = [
    "DEFAULT_DB_FILENAME",
    "SCHEMA_VERSION",
    "SURFACE_KIND",
    "build_opl_family_adoption_surface",
    "build_product_entry_adoption_projection",
    "inspect_lifecycle_store",
    "quest_lifecycle_store_path",
    "record_archive_ref",
    "read_lifecycle_records",
    "record_canvas_projection",
    "record_dispatch_receipt",
    "record_lineage_edge",
    "record_lineage_node",
    "record_owner_route_receipt",
    "record_paper_work_unit_receipt",
    "record_revision_diff",
    "record_runtime_event",
    "record_runtime_report",
    "record_study_macro_state_snapshot",
    "record_turn_receipt",
    "record_runtime_snapshot",
    "record_snapshot_file_ref",
    "record_surface_ref",
    "record_watch_state",
    "record_workspace_allocation",
    "record_workspace_storage_audit",
    "workspace_lifecycle_store_path",
]
