from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
import sqlite3
from typing import Any

SIDECAR_INDEX_TABLE_NAMES = (
    "study_macro_state_snapshots",
    "owner_route_receipts",
    "dispatch_receipts",
    "turn_receipts",
    "paper_work_unit_receipts",
    "surface_refs",
)


def ensure_sidecar_index_schema(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS study_macro_state_snapshots(
            study_root TEXT NOT NULL,
            study_id TEXT NOT NULL,
            quest_id TEXT,
            snapshot_id TEXT NOT NULL,
            observed_at TEXT NOT NULL,
            macro_state TEXT NOT NULL,
            writer_state TEXT,
            user_next TEXT,
            reason TEXT,
            decision_owner TEXT,
            owner_route_json TEXT NOT NULL,
            surface_refs_json TEXT NOT NULL,
            source_path TEXT NOT NULL,
            payload_sha256 TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            recorded_at TEXT NOT NULL,
            PRIMARY KEY (study_root, snapshot_id)
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS owner_route_receipts(
            study_root TEXT NOT NULL,
            study_id TEXT NOT NULL,
            quest_id TEXT,
            idempotency_key TEXT NOT NULL,
            route_epoch TEXT,
            current_owner TEXT,
            next_owner TEXT,
            owner_reason TEXT,
            allowed_actions_json TEXT NOT NULL,
            source_refs_json TEXT NOT NULL,
            source_path TEXT NOT NULL,
            payload_sha256 TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            recorded_at TEXT NOT NULL,
            PRIMARY KEY (study_root, idempotency_key)
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS dispatch_receipts(
            quest_root TEXT NOT NULL,
            dispatch_id TEXT NOT NULL,
            study_id TEXT NOT NULL,
            quest_id TEXT,
            action_type TEXT,
            created_at TEXT NOT NULL,
            status TEXT NOT NULL,
            idempotency_key TEXT,
            owner_route_json TEXT NOT NULL,
            source_path TEXT NOT NULL,
            payload_sha256 TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            recorded_at TEXT NOT NULL,
            PRIMARY KEY (quest_root, dispatch_id)
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS turn_receipts(
            quest_root TEXT NOT NULL,
            run_id TEXT NOT NULL,
            reason TEXT NOT NULL,
            source TEXT NOT NULL,
            status TEXT NOT NULL,
            idempotency_key TEXT NOT NULL,
            started INTEGER NOT NULL,
            queued INTEGER NOT NULL,
            scheduled INTEGER NOT NULL,
            recorded_at TEXT NOT NULL,
            source_path TEXT NOT NULL,
            payload_sha256 TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            PRIMARY KEY (quest_root, idempotency_key)
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS paper_work_unit_receipts(
            study_root TEXT NOT NULL,
            quest_root TEXT NOT NULL,
            receipt_id TEXT NOT NULL,
            study_id TEXT NOT NULL,
            quest_id TEXT,
            idempotency_key TEXT NOT NULL,
            intent_fingerprint TEXT NOT NULL,
            source_fingerprint TEXT NOT NULL,
            receipt_status TEXT NOT NULL,
            started_worker INTEGER NOT NULL,
            worker_start_ref TEXT,
            duplicate_of_receipt_id TEXT,
            fail_closed_reason TEXT,
            source_path TEXT NOT NULL,
            payload_sha256 TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            recorded_at TEXT NOT NULL,
            PRIMARY KEY (study_root, receipt_id)
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS surface_refs(
            object_root TEXT NOT NULL,
            object_scope TEXT NOT NULL,
            ref_key TEXT NOT NULL,
            surface TEXT NOT NULL,
            study_id TEXT,
            quest_id TEXT,
            target_path TEXT,
            source_path TEXT NOT NULL,
            target_sha256 TEXT,
            observed_at TEXT,
            payload_sha256 TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            recorded_at TEXT NOT NULL,
            PRIMARY KEY (object_root, object_scope, ref_key, surface)
        )
        """
    )


def record_study_macro_state_snapshot(
    *,
    connect: Any,
    ensure_schema: Any,
    resolve_db_path: Any,
    workspace_lifecycle_store_path: Any,
    index_result: Any,
    study_root: Path,
    snapshot: Mapping[str, Any],
    snapshot_path: Path,
    db_path: Path | None = None,
) -> dict[str, Any]:
    resolved_study_root = Path(study_root).expanduser().resolve()
    resolved_db_path = resolve_db_path(db_path, default=workspace_lifecycle_store_path(resolved_study_root.parent.parent))
    resolved_snapshot_path = Path(snapshot_path).expanduser().resolve()
    payload_json = _stable_json(snapshot)
    row = {
        "study_root": str(resolved_study_root),
        "study_id": _require_text("snapshot.study_id", snapshot.get("study_id")),
        "quest_id": _text(snapshot.get("quest_id")),
        "snapshot_id": _macro_snapshot_id(snapshot=snapshot, source_path=resolved_snapshot_path, payload_json=payload_json),
        "observed_at": _macro_observed_at(snapshot),
        "macro_state": _macro_state_label(snapshot),
        "writer_state": _text(snapshot.get("writer_state")),
        "user_next": _text(snapshot.get("user_next")),
        "reason": _text(snapshot.get("reason")),
        "decision_owner": _macro_decision_owner(snapshot),
        "owner_route_json": _stable_json(_mapping(snapshot.get("owner_route"))),
        "surface_refs_json": _stable_json(_mapping(snapshot.get("surface_refs"))),
        "source_path": str(resolved_snapshot_path),
        "payload_sha256": _sha256(payload_json),
        "payload_json": payload_json,
        "recorded_at": _utc_now(),
    }
    with connect(resolved_db_path) as conn:
        ensure_schema(conn)
        _upsert_row(conn, table="study_macro_state_snapshots", conflict_columns=("study_root", "snapshot_id"), row=row)
    return index_result(db_path=resolved_db_path, indexed_table="study_macro_state_snapshots", indexed_count=1, scope="study")


def record_owner_route_receipt(
    *,
    connect: Any,
    ensure_schema: Any,
    resolve_db_path: Any,
    workspace_lifecycle_store_path: Any,
    index_result: Any,
    study_root: Path,
    receipt: Mapping[str, Any],
    receipt_path: Path,
    db_path: Path | None = None,
) -> dict[str, Any]:
    resolved_study_root = Path(study_root).expanduser().resolve()
    resolved_db_path = resolve_db_path(db_path, default=workspace_lifecycle_store_path(resolved_study_root.parent.parent))
    resolved_receipt_path = Path(receipt_path).expanduser().resolve()
    payload_json = _stable_json(receipt)
    row = {
        "study_root": str(resolved_study_root),
        "study_id": _require_text("receipt.study_id", receipt.get("study_id")),
        "quest_id": _text(receipt.get("quest_id")),
        "idempotency_key": _require_text("receipt.idempotency_key", receipt.get("idempotency_key")),
        "route_epoch": _text(receipt.get("route_epoch")),
        "current_owner": _text(receipt.get("current_owner")),
        "next_owner": _text(receipt.get("next_owner")),
        "owner_reason": _text(receipt.get("owner_reason")),
        "allowed_actions_json": _stable_json(receipt.get("allowed_actions") if isinstance(receipt.get("allowed_actions"), list) else []),
        "source_refs_json": _stable_json(_mapping(receipt.get("source_refs"))),
        "source_path": str(resolved_receipt_path),
        "payload_sha256": _sha256(payload_json),
        "payload_json": payload_json,
        "recorded_at": _utc_now(),
    }
    with connect(resolved_db_path) as conn:
        ensure_schema(conn)
        _upsert_row(conn, table="owner_route_receipts", conflict_columns=("study_root", "idempotency_key"), row=row)
    return index_result(db_path=resolved_db_path, indexed_table="owner_route_receipts", indexed_count=1, scope="study")


def record_dispatch_receipt(
    *,
    connect: Any,
    ensure_schema: Any,
    resolve_db_path: Any,
    quest_lifecycle_store_path: Any,
    index_result: Any,
    quest_root: Path,
    receipt: Mapping[str, Any],
    receipt_path: Path,
    db_path: Path | None = None,
) -> dict[str, Any]:
    resolved_quest_root = Path(quest_root).expanduser().resolve()
    resolved_db_path = resolve_db_path(db_path, default=quest_lifecycle_store_path(resolved_quest_root))
    resolved_receipt_path = Path(receipt_path).expanduser().resolve()
    payload_json = _stable_json(receipt)
    row = {
        "quest_root": str(resolved_quest_root),
        "dispatch_id": _dispatch_id(receipt=receipt, source_path=resolved_receipt_path, payload_json=payload_json),
        "study_id": _require_text("receipt.study_id", receipt.get("study_id")),
        "quest_id": _text(receipt.get("quest_id")),
        "action_type": _text(receipt.get("action_type")),
        "created_at": _dispatch_created_at(receipt),
        "status": _dispatch_status(receipt),
        "idempotency_key": _text(receipt.get("idempotency_key")),
        "owner_route_json": _stable_json(_mapping(receipt.get("owner_route"))),
        "source_path": str(resolved_receipt_path),
        "payload_sha256": _sha256(payload_json),
        "payload_json": payload_json,
        "recorded_at": _utc_now(),
    }
    with connect(resolved_db_path) as conn:
        ensure_schema(conn)
        _upsert_row(conn, table="dispatch_receipts", conflict_columns=("quest_root", "dispatch_id"), row=row)
    return index_result(db_path=resolved_db_path, indexed_table="dispatch_receipts", indexed_count=1, scope="quest")


def record_turn_receipt(
    *,
    connect: Any,
    ensure_schema: Any,
    resolve_db_path: Any,
    quest_lifecycle_store_path: Any,
    index_result: Any,
    quest_root: Path,
    receipt: Mapping[str, Any],
    receipt_path: Path,
    db_path: Path | None = None,
) -> dict[str, Any]:
    resolved_quest_root = Path(quest_root).expanduser().resolve()
    resolved_db_path = resolve_db_path(db_path, default=quest_lifecycle_store_path(resolved_quest_root))
    resolved_receipt_path = Path(receipt_path).expanduser().resolve()
    payload_json = _stable_json(receipt)
    row = {
        "quest_root": str(resolved_quest_root),
        "run_id": _require_text("receipt.run_id", receipt.get("run_id")),
        "reason": _require_text("receipt.reason", receipt.get("reason")),
        "source": _require_text("receipt.source", receipt.get("source")),
        "status": _require_text("receipt.status", receipt.get("status")),
        "idempotency_key": _require_text("receipt.idempotency_key", receipt.get("idempotency_key")),
        "started": 1 if receipt.get("started") is True else 0,
        "queued": 1 if receipt.get("queued") is True else 0,
        "scheduled": 1 if receipt.get("scheduled") is True else 0,
        "recorded_at": _require_text("receipt.recorded_at", receipt.get("recorded_at")),
        "source_path": str(resolved_receipt_path),
        "payload_sha256": _sha256(payload_json),
        "payload_json": payload_json,
    }
    with connect(resolved_db_path) as conn:
        ensure_schema(conn)
        _upsert_row(conn, table="turn_receipts", conflict_columns=("quest_root", "idempotency_key"), row=row)
    return index_result(db_path=resolved_db_path, indexed_table="turn_receipts", indexed_count=1, scope="quest")


def record_paper_work_unit_receipt(
    *,
    connect: Any,
    ensure_schema: Any,
    resolve_db_path: Any,
    workspace_lifecycle_store_path: Any,
    index_result: Any,
    study_root: Path,
    quest_root: Path,
    receipt: Mapping[str, Any],
    receipt_path: Path,
    db_path: Path | None = None,
) -> dict[str, Any]:
    resolved_study_root = Path(study_root).expanduser().resolve()
    resolved_quest_root = Path(quest_root).expanduser().resolve()
    resolved_db_path = resolve_db_path(db_path, default=workspace_lifecycle_store_path(resolved_study_root.parent.parent))
    resolved_receipt_path = Path(receipt_path).expanduser().resolve()
    payload_json = _stable_json(receipt)
    row = {
        "study_root": str(resolved_study_root),
        "quest_root": str(resolved_quest_root),
        "receipt_id": _require_text("receipt.receipt_id", receipt.get("receipt_id")),
        "study_id": _require_text("receipt.study_id", receipt.get("study_id")),
        "quest_id": _text(receipt.get("quest_id")),
        "idempotency_key": _require_text("receipt.idempotency_key", receipt.get("idempotency_key")),
        "intent_fingerprint": _require_text("receipt.intent_fingerprint", receipt.get("intent_fingerprint")),
        "source_fingerprint": _require_text("receipt.source_fingerprint", receipt.get("source_fingerprint")),
        "receipt_status": _require_text("receipt.receipt_status", receipt.get("receipt_status")),
        "started_worker": 1 if receipt.get("started_worker") is True else 0,
        "worker_start_ref": _text(receipt.get("worker_start_ref")),
        "duplicate_of_receipt_id": _text(receipt.get("duplicate_of_receipt_id")),
        "fail_closed_reason": _text(receipt.get("fail_closed_reason")),
        "source_path": str(resolved_receipt_path),
        "payload_sha256": _sha256(payload_json),
        "payload_json": payload_json,
        "recorded_at": _require_text("receipt.recorded_at", receipt.get("recorded_at")),
    }
    with connect(resolved_db_path) as conn:
        ensure_schema(conn)
        _upsert_row(conn, table="paper_work_unit_receipts", conflict_columns=("study_root", "receipt_id"), row=row)
    return index_result(db_path=resolved_db_path, indexed_table="paper_work_unit_receipts", indexed_count=1, scope="study")


def record_surface_ref(
    *,
    connect: Any,
    ensure_schema: Any,
    resolve_db_path: Any,
    workspace_lifecycle_store_path: Any,
    index_result: Any,
    object_root: Path,
    object_scope: str,
    ref: Mapping[str, Any],
    ref_path: Path,
    db_path: Path | None = None,
) -> dict[str, Any]:
    resolved_object_root = Path(object_root).expanduser().resolve()
    resolved_db_path = resolve_db_path(db_path, default=workspace_lifecycle_store_path(resolved_object_root.parent.parent))
    resolved_ref_path = Path(ref_path).expanduser().resolve()
    payload_json = _stable_json(ref)
    row = {
        "object_root": str(resolved_object_root),
        "object_scope": _require_text("object_scope", object_scope),
        "ref_key": _surface_ref_key(ref=ref, ref_path=resolved_ref_path),
        "surface": _require_text("ref.surface", ref.get("surface")),
        "study_id": _text(ref.get("study_id")),
        "quest_id": _text(ref.get("quest_id")),
        "target_path": _surface_target_path(ref, base_dir=resolved_object_root),
        "source_path": str(resolved_ref_path),
        "target_sha256": _text(ref.get("sha256")) or _text(ref.get("target_sha256")),
        "observed_at": _text(ref.get("observed_at")) or _text(ref.get("updated_at")) or _text(ref.get("created_at")),
        "payload_sha256": _sha256(payload_json),
        "payload_json": payload_json,
        "recorded_at": _utc_now(),
    }
    with connect(resolved_db_path) as conn:
        ensure_schema(conn)
        _upsert_row(conn, table="surface_refs", conflict_columns=("object_root", "object_scope", "ref_key", "surface"), row=row)
    return index_result(db_path=resolved_db_path, indexed_table="surface_refs", indexed_count=1, scope=row["object_scope"])


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


def _macro_snapshot_id(*, snapshot: Mapping[str, Any], source_path: Path, payload_json: str) -> str:
    return (
        _text(snapshot.get("snapshot_id"))
        or _text(snapshot.get("source_fingerprint"))
        or f"{source_path}::{_sha256(payload_json)}"
    )


def _macro_observed_at(snapshot: Mapping[str, Any]) -> str:
    for key in ("observed_at", "updated_at", "generated_at", "created_at"):
        if value := _text(snapshot.get(key)):
            return value
    return _utc_now()


def _macro_state_label(snapshot: Mapping[str, Any]) -> str:
    for key in ("macro_state", "writer_state", "state"):
        if value := _text(snapshot.get(key)):
            return value
    return "unknown"


def _macro_decision_owner(snapshot: Mapping[str, Any]) -> str:
    if value := _text(snapshot.get("decision_owner")):
        return value
    details = _mapping(snapshot.get("details"))
    if value := _text(details.get("decision_owner")):
        return value
    owner_route = _mapping(snapshot.get("owner_route"))
    return _text(owner_route.get("next_owner"))


def _dispatch_id(*, receipt: Mapping[str, Any], source_path: Path, payload_json: str) -> str:
    for key in ("dispatch_id", "request_id", "execution_id", "action_id"):
        if value := _text(receipt.get(key)):
            return value
    return f"{source_path}::{_sha256(payload_json)}"


def _dispatch_created_at(receipt: Mapping[str, Any]) -> str:
    for key in ("created_at", "generated_at", "emitted_at", "executed_at"):
        if value := _text(receipt.get(key)):
            return value
    return _utc_now()


def _dispatch_status(receipt: Mapping[str, Any]) -> str:
    for key in ("status", "dispatch_status", "execution_status"):
        if value := _text(receipt.get(key)):
            return value
    return "unknown"


def _surface_ref_key(*, ref: Mapping[str, Any], ref_path: Path) -> str:
    for key in ("ref_key", "surface_key", "name"):
        if value := _text(ref.get(key)):
            return value
    return ref_path.stem


def _surface_target_path(ref: Mapping[str, Any], *, base_dir: Path) -> str:
    for key in ("path", "target_path", "latest_path", "source_path"):
        if value := _text(ref.get(key)):
            path = Path(value).expanduser()
            if not path.is_absolute():
                path = base_dir / path
            return str(path.resolve())
    return ""


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
    "SIDECAR_INDEX_TABLE_NAMES",
    "ensure_sidecar_index_schema",
    "record_dispatch_receipt",
    "record_owner_route_receipt",
    "record_paper_work_unit_receipt",
    "record_study_macro_state_snapshot",
    "record_surface_ref",
    "record_turn_receipt",
]
