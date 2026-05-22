from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
import sqlite3
from typing import Any

from . import lifecycle_refs_adapter


SURFACE_KIND = "runtime_lifecycle_read_model"
EXPORT_SURFACE_KIND = "runtime_lifecycle_export"
LEGACY_RESTORE_IMPORT_DIAGNOSTIC_SCOPE = "legacy_restore_import_diagnostic"
LEGACY_RESTORE_IMPORT_DIAGNOSTIC_SURFACES = frozenset({"watch_state", "runtime_report", "workspace_storage_audit"})
SQLITE_ONLY_SURFACE_TABLES = {
    "lineage_route": ("lineage_nodes", "lineage_edges"),
    "workspace_allocation": ("workspace_allocations",),
    "runtime_snapshot": ("runtime_snapshots", "snapshot_file_refs"),
    "revision_diff": ("revision_diffs",),
    "canvas_projection": ("canvas_projection",),
}
SQLITE_LEGACY_RESTORE_IMPORT_SURFACE_TABLES = {
    "watch_state": ("watch_states",),
    "runtime_report": ("runtime_reports",),
    "workspace_storage_audit": ("workspace_storage_audits",),
}
SUPPORTED_SURFACES = frozenset({*LEGACY_RESTORE_IMPORT_DIAGNOSTIC_SURFACES, *SQLITE_ONLY_SURFACE_TABLES})


def build_lifecycle_inventory(
    *,
    quest_root: Path | None = None,
    workspace_root: Path | None = None,
    db_path: Path | None = None,
) -> dict[str, Any]:
    resolved_db_path = _resolve_lifecycle_db_path(quest_root=quest_root, workspace_root=workspace_root, db_path=db_path)
    scope = _scope(quest_root=quest_root, workspace_root=workspace_root)
    if not resolved_db_path.exists():
        return {
            "surface_kind": SURFACE_KIND,
            "schema_version": lifecycle_refs_adapter.SCHEMA_VERSION,
            "mode": "inventory",
            "scope": scope,
            "db_path": str(resolved_db_path),
            "status": "missing",
            "read_only": True,
            "legacy_restore_import_used": False,
            "available_surfaces": [],
            "missing_reason": "lifecycle_refs_sqlite_missing",
        }

    with _connect_readonly(resolved_db_path) as conn:
        tables = {
            table: _table_count_if_present(conn, table)
            for table in (
                "watch_states",
                "runtime_reports",
                "workspace_storage_audits",
                "lineage_nodes",
                "lineage_edges",
                "workspace_allocations",
                "runtime_snapshots",
                "snapshot_file_refs",
                "revision_diffs",
                "canvas_projection",
                "runtime_events",
                "report_index",
            )
        }
        available_surfaces = _available_surfaces(conn)
        latest_refs = _latest_refs(conn)

    return {
        "surface_kind": SURFACE_KIND,
        "schema_version": lifecycle_refs_adapter.SCHEMA_VERSION,
        "mode": "inventory",
        "scope": scope,
        "db_path": str(resolved_db_path),
        "status": "ready",
        "read_only": True,
        "legacy_restore_import_used": False,
        "tables": tables,
        "available_surfaces": available_surfaces,
        "latest_refs": latest_refs,
    }


def read_lifecycle_projection(
    *,
    surface: str,
    quest_root: Path | None = None,
    workspace_root: Path | None = None,
    report_group: str = "runtime_watch",
    db_path: Path | None = None,
    legacy_restore_import_diagnostic: bool = False,
) -> dict[str, Any]:
    normalized_surface = _require_surface(surface)
    resolved_db_path = _resolve_lifecycle_db_path(quest_root=quest_root, workspace_root=workspace_root, db_path=db_path)
    if not resolved_db_path.exists():
        projection = _missing_sqlite_projection(
            surface=normalized_surface,
            db_path=resolved_db_path,
            status="missing",
            missing_reason="lifecycle_refs_sqlite_missing",
        )
        return _maybe_legacy_restore_import_diagnostic(
            projection=projection,
            surface=normalized_surface,
            quest_root=quest_root,
            workspace_root=workspace_root,
            report_group=report_group,
            db_path=resolved_db_path,
            legacy_restore_import_diagnostic=legacy_restore_import_diagnostic,
        )

    with _connect_readonly(resolved_db_path) as conn:
        if normalized_surface in LEGACY_RESTORE_IMPORT_DIAGNOSTIC_SURFACES:
            projection = _read_sqlite_legacy_import_projection(
                conn=conn,
                surface=normalized_surface,
                quest_root=quest_root,
                workspace_root=workspace_root,
                report_group=report_group,
                db_path=resolved_db_path,
            )
        else:
            projection = _read_sqlite_only_projection(
                conn=conn,
                surface=normalized_surface,
                quest_root=quest_root,
                workspace_root=workspace_root,
                db_path=resolved_db_path,
            )
    return _maybe_legacy_restore_import_diagnostic(
        projection=projection,
        surface=normalized_surface,
        quest_root=quest_root,
        workspace_root=workspace_root,
        report_group=report_group,
        db_path=resolved_db_path,
        legacy_restore_import_diagnostic=legacy_restore_import_diagnostic,
    )


def read_legacy_restore_import_diagnostic_projection(
    *,
    surface: str,
    quest_root: Path | None = None,
    workspace_root: Path | None = None,
    report_group: str = "runtime_watch",
    db_path: Path | None = None,
) -> dict[str, Any]:
    return read_lifecycle_projection(
        surface=surface,
        quest_root=quest_root,
        workspace_root=workspace_root,
        report_group=report_group,
        db_path=db_path,
        legacy_restore_import_diagnostic=True,
    )


def export_lifecycle_projection(
    *,
    surface: str,
    export_format: str,
    quest_root: Path | None = None,
    workspace_root: Path | None = None,
    report_group: str = "runtime_watch",
    output_path: Path | None = None,
    db_path: Path | None = None,
    legacy_restore_import_diagnostic: bool = False,
) -> dict[str, Any]:
    normalized_format = _require_export_format(export_format)
    projection = read_lifecycle_projection(
        surface=surface,
        quest_root=quest_root,
        workspace_root=workspace_root,
        report_group=report_group,
        db_path=db_path,
        legacy_restore_import_diagnostic=legacy_restore_import_diagnostic,
    )
    source_payload = projection.get("payload") if isinstance(projection.get("payload"), Mapping) else {}
    exported_at = _utc_now()
    rendered = (
        _render_markdown_export(projection=projection, exported_at=exported_at)
        if normalized_format == "markdown"
        else _render_json_export(projection=projection, exported_at=exported_at)
    )
    export_payload = {
        "surface_kind": EXPORT_SURFACE_KIND,
        "schema_version": lifecycle_refs_adapter.SCHEMA_VERSION,
        "surface": projection["surface"],
        "export_format": normalized_format,
        "exported_at": exported_at,
        "source_query": projection["source_query"],
        "source_db_path": projection["db_path"],
        "source_payload_sha256": _sha256(_stable_json(source_payload)),
        "legacy_restore_import_used": bool(projection.get("legacy_restore_import_used")),
        "output_path": str(Path(output_path).expanduser().resolve()) if output_path is not None else None,
        "payload": source_payload,
    }
    if "diagnostic_scope" in projection:
        export_payload["diagnostic_scope"] = projection["diagnostic_scope"]
    if output_path is not None:
        resolved_output_path = Path(output_path).expanduser().resolve()
        resolved_output_path.parent.mkdir(parents=True, exist_ok=True)
        resolved_output_path.write_text(rendered, encoding="utf-8")
    return export_payload


def _read_watch_state_projection(
    *,
    conn: sqlite3.Connection,
    quest_root: Path | None,
    db_path: Path,
) -> dict[str, Any] | None:
    resolved_quest_root = _require_root("quest_root", quest_root)
    row = conn.execute(
        """
        SELECT updated_at, payload_json, payload_sha256
        FROM watch_states
        WHERE quest_root = ?
        """,
        (str(resolved_quest_root),),
    ).fetchone()
    if row is None:
        return None
    return _projection(
        surface="watch_state",
        db_path=db_path,
        source_query="SELECT updated_at, payload_json, payload_sha256 FROM watch_states WHERE quest_root = ?",
        payload=json.loads(row["payload_json"]),
        payload_sha256=str(row["payload_sha256"]),
        legacy_restore_import_used=False,
        source_paths=[],
    )


def _read_runtime_report_projection(
    *,
    conn: sqlite3.Connection,
    quest_root: Path | None,
    report_group: str,
    db_path: Path,
) -> dict[str, Any] | None:
    resolved_quest_root = _require_root("quest_root", quest_root)
    row = conn.execute(
        """
        SELECT report_group, timestamp, status, json_path, md_path, latest_json_path,
               latest_md_path, payload_sha256, payload_json
        FROM runtime_reports
        WHERE quest_root = ? AND report_group = ?
        ORDER BY timestamp DESC
        LIMIT 1
        """,
        (str(resolved_quest_root), _require_text("report_group", report_group)),
    ).fetchone()
    if row is None:
        return None
    return _projection(
        surface="runtime_report",
        db_path=db_path,
        source_query=(
            "SELECT report_group, timestamp, status, json_path, md_path, latest_json_path, "
            "latest_md_path, payload_sha256, payload_json FROM runtime_reports "
            "WHERE quest_root = ? AND report_group = ? ORDER BY timestamp DESC LIMIT 1"
        ),
        payload=json.loads(row["payload_json"]),
        payload_sha256=str(row["payload_sha256"]),
        legacy_restore_import_used=False,
        source_paths=[
            str(row["json_path"]),
            str(row["md_path"]),
            str(row["latest_json_path"]),
            str(row["latest_md_path"]),
        ],
    )


def _read_workspace_storage_audit_projection(
    *,
    conn: sqlite3.Connection,
    workspace_root: Path | None,
    db_path: Path,
) -> dict[str, Any] | None:
    resolved_workspace_root = _require_root("workspace_root", workspace_root)
    row = conn.execute(
        """
        SELECT recorded_at, mode, report_path, latest_report_path, payload_sha256, payload_json
        FROM workspace_storage_audits
        WHERE workspace_root = ?
        ORDER BY recorded_at DESC
        LIMIT 1
        """,
        (str(resolved_workspace_root),),
    ).fetchone()
    if row is None:
        return None
    return _projection(
        surface="workspace_storage_audit",
        db_path=db_path,
        source_query=(
            "SELECT recorded_at, mode, report_path, latest_report_path, payload_sha256, payload_json "
            "FROM workspace_storage_audits WHERE workspace_root = ? ORDER BY recorded_at DESC LIMIT 1"
        ),
        payload=json.loads(row["payload_json"]),
        payload_sha256=str(row["payload_sha256"]),
        legacy_restore_import_used=False,
        source_paths=[str(row["report_path"]), str(row["latest_report_path"])],
    )


def _read_sqlite_legacy_import_projection(
    *,
    conn: sqlite3.Connection,
    surface: str,
    quest_root: Path | None,
    workspace_root: Path | None,
    report_group: str,
    db_path: Path,
) -> dict[str, Any]:
    required_tables = SQLITE_LEGACY_RESTORE_IMPORT_SURFACE_TABLES[surface]
    missing_tables = [table for table in required_tables if not _table_exists(conn, table)]
    if missing_tables:
        return _missing_sqlite_projection(
            surface=surface,
            db_path=db_path,
            status="capability_gap",
            missing_reason="lifecycle_refs_sqlite_table_missing",
            missing_tables=missing_tables,
        )

    if surface == "watch_state":
        projection = _read_watch_state_projection(conn=conn, quest_root=quest_root, db_path=db_path)
    elif surface == "runtime_report":
        projection = _read_runtime_report_projection(
            conn=conn,
            quest_root=quest_root,
            report_group=report_group,
            db_path=db_path,
        )
    else:
        projection = _read_workspace_storage_audit_projection(
            conn=conn,
            workspace_root=workspace_root,
            db_path=db_path,
        )
    if projection is not None:
        return projection
    return _missing_sqlite_projection(
        surface=surface,
        db_path=db_path,
        status="missing",
        missing_reason="lifecycle_refs_sqlite_row_missing",
    )


def _read_sqlite_only_projection(
    *,
    conn: sqlite3.Connection,
    surface: str,
    quest_root: Path | None,
    workspace_root: Path | None,
    db_path: Path,
) -> dict[str, Any]:
    required_tables = SQLITE_ONLY_SURFACE_TABLES[surface]
    missing_tables = [table for table in required_tables if not _table_exists(conn, table)]
    if missing_tables:
        return _missing_sqlite_projection(
            surface=surface,
            db_path=db_path,
            status="capability_gap",
            missing_reason="lifecycle_refs_sqlite_table_missing",
            missing_tables=missing_tables,
        )

    payload: dict[str, Any] = {}
    source_queries: list[str] = []
    for table in required_tables:
        query, values = _projection_table_query(
            conn=conn,
            table=table,
            quest_root=quest_root,
            workspace_root=workspace_root,
        )
        source_queries.append(query)
        payload[table] = [_normalize_sqlite_row(row) for row in conn.execute(query, values).fetchall()]
    return _projection(
        surface=surface,
        db_path=db_path,
        source_query="; ".join(source_queries),
        payload=payload,
        payload_sha256=_sha256(_stable_json(payload)),
        legacy_restore_import_used=False,
        source_paths=[],
    )


def _projection_table_query(
    *,
    conn: sqlite3.Connection,
    table: str,
    quest_root: Path | None,
    workspace_root: Path | None,
) -> tuple[str, tuple[str, ...]]:
    columns = _table_columns(conn, table)
    if quest_root is not None and "quest_root" in columns:
        return f"SELECT * FROM {table} WHERE quest_root = ? ORDER BY rowid", (str(Path(quest_root).expanduser().resolve()),)
    if workspace_root is not None and "workspace_root" in columns:
        return (
            f"SELECT * FROM {table} WHERE workspace_root = ? ORDER BY rowid",
            (str(Path(workspace_root).expanduser().resolve()),),
        )
    return f"SELECT * FROM {table} ORDER BY rowid", ()


def _normalize_sqlite_row(row: sqlite3.Row) -> dict[str, Any]:
    normalized: dict[str, Any] = {}
    for key in row.keys():
        value = row[key]
        if isinstance(value, str) and (key.endswith("_json") or key in {"payload", "payload_json"}):
            try:
                normalized[key] = json.loads(value)
            except json.JSONDecodeError:
                normalized[key] = value
        else:
            normalized[key] = value
    return normalized


def _missing_sqlite_projection(
    *,
    surface: str,
    db_path: Path,
    status: str,
    missing_reason: str,
    missing_tables: list[str] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    if missing_tables is not None:
        payload["missing_tables"] = list(missing_tables)
    return _projection(
        surface=surface,
        db_path=db_path,
        source_query="sqlite projection unavailable",
        payload=payload,
        payload_sha256=_sha256(_stable_json(payload)),
        legacy_restore_import_used=False,
        source_paths=[],
        status=status,
        missing_reason=missing_reason,
    )


def _legacy_restore_import_projection(
    *,
    surface: str,
    quest_root: Path | None,
    workspace_root: Path | None,
    report_group: str,
    db_path: Path,
) -> dict[str, Any]:
    if surface == "watch_state":
        root = _require_root("quest_root", quest_root)
        source_path = root / "artifacts" / "reports" / "runtime_watch" / "state.json"
    elif surface == "runtime_report":
        root = _require_root("quest_root", quest_root)
        source_path = root / "artifacts" / "reports" / _require_text("report_group", report_group) / "latest.json"
    else:
        root = _require_root("workspace_root", workspace_root)
        source_path = root / "storage_audit" / "latest.json"

    resolved_source_path = source_path.expanduser().resolve()
    payload = _read_json_mapping(resolved_source_path) if resolved_source_path.exists() else {}
    return _projection(
        surface=surface,
        db_path=db_path,
        source_query=f"legacy restore import diagnostic: {resolved_source_path}",
        payload=payload,
        payload_sha256=_sha256(_stable_json(payload)),
        legacy_restore_import_used=True,
        source_paths=[str(resolved_source_path)],
        status="legacy_restore_import_available" if resolved_source_path.exists() else "missing",
        missing_reason=None if resolved_source_path.exists() else "sqlite_projection_and_legacy_latest_missing",
    )


def _maybe_legacy_restore_import_diagnostic(
    *,
    projection: dict[str, Any],
    surface: str,
    quest_root: Path | None,
    workspace_root: Path | None,
    report_group: str,
    db_path: Path,
    legacy_restore_import_diagnostic: bool,
) -> dict[str, Any]:
    if (
        not legacy_restore_import_diagnostic
        or surface not in LEGACY_RESTORE_IMPORT_DIAGNOSTIC_SURFACES
        or projection.get("status") == "ready"
    ):
        return projection
    diagnostic_projection = _legacy_restore_import_projection(
        surface=surface,
        quest_root=quest_root,
        workspace_root=workspace_root,
        report_group=report_group,
        db_path=db_path,
    )
    diagnostic_projection["diagnostic_scope"] = LEGACY_RESTORE_IMPORT_DIAGNOSTIC_SCOPE
    return diagnostic_projection


def _projection(
    *,
    surface: str,
    db_path: Path,
    source_query: str,
    payload: Mapping[str, Any],
    payload_sha256: str,
    legacy_restore_import_used: bool,
    source_paths: list[str],
    status: str = "ready",
    missing_reason: str | None = None,
) -> dict[str, Any]:
    result = {
        "surface_kind": SURFACE_KIND,
        "schema_version": lifecycle_refs_adapter.SCHEMA_VERSION,
        "surface": surface,
        "status": status,
        "read_only": True,
        "db_path": str(db_path),
        "source_query": source_query,
        "source_paths": source_paths,
        "payload_sha256": payload_sha256,
        "legacy_restore_import_used": legacy_restore_import_used,
        "payload": dict(payload),
    }
    if missing_reason is not None:
        result["missing_reason"] = missing_reason
    return result


def _available_surfaces(conn: sqlite3.Connection) -> list[str]:
    surfaces: list[str] = []
    if _table_count_if_present(conn, "watch_states") > 0:
        surfaces.append("watch_state")
    if _table_count_if_present(conn, "runtime_reports") > 0:
        surfaces.append("runtime_report")
    if _table_count_if_present(conn, "workspace_storage_audits") > 0:
        surfaces.append("workspace_storage_audit")
    for surface, tables in SQLITE_ONLY_SURFACE_TABLES.items():
        if all(_table_exists(conn, table) for table in tables) and any(_table_count_if_present(conn, table) > 0 for table in tables):
            surfaces.append(surface)
    return surfaces


def _latest_refs(conn: sqlite3.Connection) -> dict[str, Any]:
    refs: dict[str, Any] = {}
    if _table_exists(conn, "watch_states"):
        row = conn.execute(
            "SELECT quest_root, updated_at FROM watch_states ORDER BY updated_at DESC LIMIT 1"
        ).fetchone()
        if row is not None:
            refs["watch_state"] = {"quest_root": row["quest_root"], "updated_at": row["updated_at"]}
    if _table_exists(conn, "runtime_reports"):
        row = conn.execute(
            """
            SELECT quest_root, report_group, timestamp, latest_json_path, latest_md_path
            FROM runtime_reports
            ORDER BY timestamp DESC
            LIMIT 1
            """
        ).fetchone()
        if row is not None:
            refs["runtime_report"] = {
                "quest_root": row["quest_root"],
                "report_group": row["report_group"],
                "timestamp": row["timestamp"],
                "latest_json_path": row["latest_json_path"],
                "latest_md_path": row["latest_md_path"],
            }
    if _table_exists(conn, "workspace_storage_audits"):
        row = conn.execute(
            """
            SELECT workspace_root, recorded_at, latest_report_path
            FROM workspace_storage_audits
            ORDER BY recorded_at DESC
            LIMIT 1
            """
        ).fetchone()
        if row is not None:
            refs["workspace_storage_audit"] = {
                "workspace_root": row["workspace_root"],
                "recorded_at": row["recorded_at"],
                "latest_report_path": row["latest_report_path"],
            }
    for surface, tables in SQLITE_ONLY_SURFACE_TABLES.items():
        if all(_table_exists(conn, table) for table in tables):
            refs[surface] = {
                "tables": {table: _table_count_if_present(conn, table) for table in tables},
            }
    return refs


def _render_json_export(*, projection: Mapping[str, Any], exported_at: str) -> str:
    payload = projection.get("payload") if isinstance(projection.get("payload"), Mapping) else {}
    return json.dumps(dict(payload), ensure_ascii=False, indent=2) + "\n"


def _render_markdown_export(*, projection: Mapping[str, Any], exported_at: str) -> str:
    payload = projection.get("payload") if isinstance(projection.get("payload"), Mapping) else {}
    lines = [
        "# Runtime Lifecycle Compatibility Export",
        "",
        f"- surface: `{projection.get('surface')}`",
        f"- exported_at: `{exported_at}`",
        f"- schema_version: `{lifecycle_refs_adapter.SCHEMA_VERSION}`",
        f"- legacy_restore_import_used: `{bool(projection.get('legacy_restore_import_used'))}`",
        f"- source_query: `{projection.get('source_query')}`",
        f"- payload_sha256: `{projection.get('payload_sha256')}`",
        "",
        "```json",
        json.dumps(dict(payload), ensure_ascii=False, indent=2),
        "```",
        "",
    ]
    return "\n".join(lines)


def _resolve_lifecycle_db_path(
    *,
    quest_root: Path | None,
    workspace_root: Path | None,
    db_path: Path | None,
) -> Path:
    if db_path is not None:
        return Path(db_path).expanduser().resolve()
    if quest_root is not None:
        return lifecycle_refs_adapter.quest_lifecycle_store_path(Path(quest_root))
    if workspace_root is not None:
        return lifecycle_refs_adapter.workspace_lifecycle_store_path(Path(workspace_root))
    raise ValueError("Specify one of quest_root, workspace_root, or db_path")


def _scope(*, quest_root: Path | None, workspace_root: Path | None) -> str:
    if quest_root is not None:
        return "quest"
    if workspace_root is not None:
        return "workspace"
    return "db"


def _connect_readonly(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(f"file:{Path(db_path).as_posix()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def _table_count_if_present(conn: sqlite3.Connection, table: str) -> int:
    if not _table_exists(conn, table):
        return 0
    row = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()
    return int(row[0]) if row is not None else 0


def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    return (
        conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
            (table,),
        ).fetchone()
        is not None
    )


def _table_columns(conn: sqlite3.Connection, table: str) -> set[str]:
    return {str(row["name"]) for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}


def _read_json_mapping(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return dict(payload) if isinstance(payload, Mapping) else {}


def _require_surface(surface: str) -> str:
    normalized = str(surface or "").strip()
    if normalized not in SUPPORTED_SURFACES:
        raise ValueError(f"unsupported runtime lifecycle surface: {surface!r}")
    return normalized


def _require_export_format(export_format: str) -> str:
    normalized = str(export_format or "").strip()
    if normalized not in {"json", "markdown"}:
        raise ValueError(f"unsupported runtime lifecycle export format: {export_format!r}")
    return normalized


def _require_root(label: str, value: Path | None) -> Path:
    if value is None:
        raise ValueError(f"{label} is required for this runtime lifecycle surface")
    return Path(value).expanduser().resolve()


def _require_text(label: str, value: object) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"{label} must be a non-empty string")
    return text


def _stable_json(payload: object) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def _sha256(payload: str) -> str:
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


__all__ = [
    "EXPORT_SURFACE_KIND",
    "SUPPORTED_SURFACES",
    "SURFACE_KIND",
    "build_lifecycle_inventory",
    "export_lifecycle_projection",
    "read_lifecycle_projection",
    "read_legacy_restore_import_diagnostic_projection",
]
