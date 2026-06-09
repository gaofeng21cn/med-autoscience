from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
import sqlite3
import tempfile
from typing import Any

from med_autoscience.controllers.runtime_storage_maintenance_parts.restore_proof_compaction_helpers import (
    safe_artifact_id,
    write_json,
)


SURFACE_KIND = "runtime_lifecycle_payload_retention"
SCHEMA_VERSION = 1
_TIMESTAMP_FORMAT = "%Y%m%dT%H%M%SZ"


def run_runtime_lifecycle_payload_retention(
    *,
    db_path: Path,
    apply: bool,
    cold_store_root: Path,
    min_mb: int = 16,
    max_rows: int | None = None,
    compact: bool = False,
) -> dict[str, Any]:
    resolved_db_path = Path(db_path).expanduser().resolve()
    recorded_at = _utc_now()
    threshold_bytes = max(0, int(min_mb)) * 1024 * 1024
    cold_root = _cold_store_root(db_path=resolved_db_path, cold_store_root=cold_store_root)
    candidates: list[dict[str, Any]] = []
    blockers: list[dict[str, Any]] = []
    moved_count = 0
    deduped_count = 0
    actual_release_bytes = 0

    if not resolved_db_path.is_file():
        receipt = _receipt(
            db_path=resolved_db_path,
            recorded_at=recorded_at,
            apply=apply,
            compact=compact,
            threshold_bytes=threshold_bytes,
            max_rows=max_rows,
            cold_root=cold_root,
            candidates=[],
            blockers=[{"status": "blocked", "reason": "db_not_found", "db_path": str(resolved_db_path)}],
            moved_count=0,
            deduped_count=0,
            actual_release_bytes=0,
            compact_result=None,
        )
        _write_receipt(db_path=resolved_db_path, receipt=receipt, recorded_at=recorded_at)
        return receipt

    with sqlite3.connect(resolved_db_path) as conn:
        conn.row_factory = sqlite3.Row
        for candidate in _iter_candidates(conn=conn, db_path=resolved_db_path, threshold_bytes=threshold_bytes):
            if max_rows is not None and len(candidates) >= max(0, int(max_rows)):
                break
            if apply:
                applied = _apply_candidate(
                    conn=conn,
                    db_path=resolved_db_path,
                    candidate=candidate,
                    cold_root=cold_root,
                    recorded_at=recorded_at,
                )
                candidate.update(applied)
                actual_release_bytes += int(applied.get("online_release_bytes") or 0)
                if applied.get("status") == "moved_to_cold_object":
                    moved_count += 1
                elif applied.get("status") == "deduped_to_existing_cold_object":
                    deduped_count += 1
                elif str(applied.get("status") or "").startswith("blocked"):
                    blockers.append(candidate)
            candidates.append(candidate)
        if apply and candidates:
            conn.commit()

    compact_result = _compact_database(resolved_db_path) if apply and compact and candidates and not blockers else None
    status = (
        "applied"
        if apply and (moved_count or deduped_count) and not blockers
        else "blocked"
        if apply and blockers
        else "planned"
        if candidates
        else "nothing_to_retain"
    )
    receipt = _receipt(
        db_path=resolved_db_path,
        recorded_at=recorded_at,
        apply=apply,
        compact=compact,
        threshold_bytes=threshold_bytes,
        max_rows=max_rows,
        cold_root=cold_root,
        candidates=candidates,
        blockers=blockers,
        moved_count=moved_count,
        deduped_count=deduped_count,
        actual_release_bytes=actual_release_bytes,
        compact_result=compact_result,
        status=status,
    )
    _write_receipt(db_path=resolved_db_path, receipt=receipt, recorded_at=recorded_at)
    return receipt


def repair_runtime_lifecycle_sqlite_sidecars(
    *,
    db_path: Path,
    apply: bool,
) -> dict[str, Any]:
    resolved_db_path = Path(db_path).expanduser().resolve()
    recorded_at = _utc_now()
    if not resolved_db_path.is_file():
        receipt = _sidecar_repair_receipt(
            db_path=resolved_db_path,
            recorded_at=recorded_at,
            apply=apply,
            immutable_integrity=None,
            normal_integrity_before=None,
            normal_integrity_after=None,
            sidecars=[],
            blockers=[
                {
                    "status": "blocked",
                    "reason": "db_not_found",
                    "db_path": str(resolved_db_path),
                }
            ],
        )
        _write_receipt(db_path=resolved_db_path, receipt=receipt, recorded_at=recorded_at)
        return receipt

    sidecars = _sqlite_sidecar_infos(resolved_db_path)
    immutable_integrity = _sqlite_integrity_check(resolved_db_path, immutable=True)
    normal_integrity_before = _sqlite_integrity_check(resolved_db_path, immutable=False)
    blockers: list[dict[str, Any]] = []
    if immutable_integrity.get("status") != "ok":
        blockers.append(
            {
                "status": "blocked_immutable_integrity_check_failed",
                "integrity_check": immutable_integrity,
            }
        )
    if sidecars and normal_integrity_before.get("status") == "ok":
        blockers.append(
            {
                "status": "blocked_live_sqlite_sidecars_may_hold_checkpoint_data",
                "integrity_check": normal_integrity_before,
            }
        )
    if not sidecars:
        status = "nothing_to_repair"
    elif blockers:
        status = "blocked"
    elif apply:
        for sidecar in sidecars:
            Path(str(sidecar["path"])).unlink()
            sidecar["status"] = "removed_stale_sqlite_sidecar"
        status = "applied"
    else:
        for sidecar in sidecars:
            sidecar["status"] = "candidate_stale_sqlite_sidecar"
        status = "planned"
    normal_integrity_after = _sqlite_integrity_check(resolved_db_path, immutable=False) if apply and not blockers else None
    receipt = _sidecar_repair_receipt(
        db_path=resolved_db_path,
        recorded_at=recorded_at,
        apply=apply,
        immutable_integrity=immutable_integrity,
        normal_integrity_before=normal_integrity_before,
        normal_integrity_after=normal_integrity_after,
        sidecars=sidecars,
        blockers=blockers,
        status=status,
    )
    _write_receipt(db_path=resolved_db_path, receipt=receipt, recorded_at=recorded_at)
    return receipt


def _iter_candidates(*, conn: sqlite3.Connection, db_path: Path, threshold_bytes: int) -> Iterable[dict[str, Any]]:
    table_columns = {
        "workspace_storage_audits": ("categories_json", "payload_json"),
        "report_index": ("payload_json",),
        "dispatch_receipts": ("payload_json",),
    }
    for table, columns in table_columns.items():
        if not _table_exists(conn, table):
            continue
        for row in conn.execute(f"SELECT rowid, * FROM {table} ORDER BY rowid"):
            row_map = dict(row)
            for column in columns:
                value = row_map.get(column)
                if not isinstance(value, str) or not value:
                    continue
                if _is_retention_ref(value):
                    continue
                payload_bytes = value.encode("utf-8")
                if len(payload_bytes) < threshold_bytes:
                    continue
                sha256 = hashlib.sha256(payload_bytes).hexdigest()
                yield {
                    "status": "candidate",
                    "db_path": str(db_path),
                    "table": table,
                    "rowid": int(row_map["rowid"]),
                    "column": column,
                    "bytes": len(payload_bytes),
                    "sha256": sha256,
                    "primary_key": _primary_key_payload(table=table, row=row_map),
                    "payload_sha256_column": row_map.get("payload_sha256"),
                }


def _apply_candidate(
    *,
    conn: sqlite3.Connection,
    db_path: Path,
    candidate: Mapping[str, Any],
    cold_root: Path,
    recorded_at: str,
) -> dict[str, Any]:
    table = str(candidate.get("table") or "")
    column = str(candidate.get("column") or "")
    rowid = int(candidate.get("rowid") or 0)
    row = conn.execute(f"SELECT {column} FROM {table} WHERE rowid = ?", (rowid,)).fetchone()
    if row is None:
        return {"status": "blocked_row_missing", "online_release_bytes": 0}
    value = row[0]
    if not isinstance(value, str) or not value:
        return {"status": "blocked_payload_missing", "online_release_bytes": 0}
    payload_bytes = value.encode("utf-8")
    observed_sha = hashlib.sha256(payload_bytes).hexdigest()
    expected_sha = str(candidate.get("sha256") or "")
    if observed_sha != expected_sha:
        return {
            "status": "blocked_payload_sha256_changed",
            "expected_sha256": expected_sha,
            "observed_sha256": observed_sha,
            "online_release_bytes": 0,
        }
    object_path = cold_root / "objects" / observed_sha[:2] / f"{observed_sha}.json"
    object_path.parent.mkdir(parents=True, exist_ok=True)
    if object_path.exists():
        if _sha256(object_path) != observed_sha:
            return {
                "status": "blocked_cold_object_sha256_mismatch",
                "cold_object_path": str(object_path),
                "online_release_bytes": 0,
            }
        status = "deduped_to_existing_cold_object"
    else:
        object_path.write_bytes(payload_bytes)
        status = "moved_to_cold_object"
    ref_path = _cold_ref_path(db_path=db_path, cold_root=cold_root, candidate=candidate, sha256=observed_sha)
    ref_payload = _ref_payload(
        db_path=db_path,
        object_path=object_path,
        ref_path=ref_path,
        candidate=candidate,
        recorded_at=recorded_at,
    )
    write_json(ref_path, ref_payload)
    inline_ref = json.dumps(ref_payload, ensure_ascii=False, sort_keys=True)
    conn.execute(f"UPDATE {table} SET {column} = ? WHERE rowid = ?", (inline_ref, rowid))
    return {
        "status": status,
        "cold_object_path": str(object_path),
        "cold_ref_path": str(ref_path),
        "online_release_bytes": max(0, len(payload_bytes) - len(inline_ref.encode("utf-8"))),
    }


def _ref_payload(
    *,
    db_path: Path,
    object_path: Path,
    ref_path: Path,
    candidate: Mapping[str, Any],
    recorded_at: str,
) -> dict[str, Any]:
    return {
        "surface_kind": "runtime_lifecycle_payload_retention_ref",
        "schema_version": SCHEMA_VERSION,
        "status": "payload_moved_to_cold_object",
        "recorded_at": recorded_at,
        "db_path": str(db_path),
        "table": candidate.get("table"),
        "rowid": candidate.get("rowid"),
        "column": candidate.get("column"),
        "primary_key": candidate.get("primary_key"),
        "cold_object_path": str(object_path),
        "cold_ref_path": str(ref_path),
        "original_sha256": candidate.get("sha256"),
        "original_bytes": candidate.get("bytes"),
        "restore_command": f"sqlite3 {db_path} <restore-sql-using-{object_path}>",
        "body_included": False,
    }


def _compact_database(db_path: Path) -> dict[str, Any]:
    before_bytes = db_path.stat().st_size
    sidecars_before = _sqlite_sidecar_infos(db_path)
    with tempfile.TemporaryDirectory(prefix="mas-runtime-lifecycle-retention.") as tmpdir:
        compacted = Path(tmpdir) / "runtime_lifecycle.compacted.sqlite"
        with sqlite3.connect(db_path) as conn:
            quoted_compacted = str(compacted).replace("'", "''")
            conn.execute(f"VACUUM INTO '{quoted_compacted}'")
        with sqlite3.connect(compacted) as conn:
            integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
        if integrity != "ok":
            return {
                "status": "blocked_compacted_integrity_check_failed",
                "bytes_before": before_bytes,
                "integrity_check": integrity,
            }
        compacted.replace(db_path)
    sidecar_cleanup = _remove_sqlite_sidecars(db_path, status="removed_after_compact_replace")
    after_bytes = db_path.stat().st_size
    return {
        "status": "compacted",
        "bytes_before": before_bytes,
        "bytes_after": after_bytes,
        "release_bytes": max(0, before_bytes - after_bytes),
        "sidecars_before": sidecars_before,
        "sidecar_cleanup": sidecar_cleanup,
    }


def _sqlite_sidecar_infos(db_path: Path) -> list[dict[str, Any]]:
    sidecars: list[dict[str, Any]] = []
    for path in (Path(f"{db_path}-wal"), Path(f"{db_path}-shm")):
        if not path.exists():
            continue
        sidecars.append(
            {
                "path": str(path),
                "bytes": path.stat().st_size,
                "sha256": _sha256(path),
            }
        )
    return sidecars


def _remove_sqlite_sidecars(db_path: Path, *, status: str) -> list[dict[str, Any]]:
    removed: list[dict[str, Any]] = []
    for sidecar in _sqlite_sidecar_infos(db_path):
        Path(str(sidecar["path"])).unlink()
        sidecar["status"] = status
        removed.append(sidecar)
    return removed


def _sqlite_integrity_check(db_path: Path, *, immutable: bool) -> dict[str, Any]:
    uri = f"file:{db_path.as_posix()}?mode=ro"
    if immutable:
        uri = f"{uri}&immutable=1"
    try:
        with sqlite3.connect(uri, uri=True) as conn:
            value = conn.execute("PRAGMA integrity_check").fetchone()[0]
    except sqlite3.Error as exc:
        return {
            "status": "error",
            "mode": "immutable" if immutable else "normal_readonly",
            "error": str(exc),
        }
    return {
        "status": "ok" if value == "ok" else "failed",
        "mode": "immutable" if immutable else "normal_readonly",
        "result": value,
    }


def _receipt(
    *,
    db_path: Path,
    recorded_at: str,
    apply: bool,
    compact: bool,
    threshold_bytes: int,
    max_rows: int | None,
    cold_root: Path,
    candidates: list[dict[str, Any]],
    blockers: list[dict[str, Any]],
    moved_count: int,
    deduped_count: int,
    actual_release_bytes: int,
    compact_result: dict[str, Any] | None,
    status: str | None = None,
) -> dict[str, Any]:
    return {
        "surface_kind": SURFACE_KIND,
        "schema_version": SCHEMA_VERSION,
        "status": status
        or (
            "applied"
            if apply and (moved_count or deduped_count) and not blockers
            else "blocked"
            if blockers
            else "planned"
            if candidates
            else "nothing_to_retain"
        ),
        "recorded_at": recorded_at,
        "db_path": str(db_path),
        "apply": bool(apply),
        "compact_requested": bool(compact),
        "min_bytes": threshold_bytes,
        "max_rows": max_rows,
        "cold_store_root": str(cold_root),
        "candidate_count": len(candidates),
        "moved_count": moved_count,
        "deduped_count": deduped_count,
        "blocker_count": len(blockers),
        "actual_release_bytes": actual_release_bytes,
        "compact": compact_result,
        "body_included": False,
        "mutation_policy": {
            "externalizes_large_derived_payload_columns": bool(apply),
            "keeps_route_and_summary_columns_inline": True,
            "deletes_domain_truth": False,
            "compacts_database_file": bool(apply and compact),
            "removes_stale_sqlite_sidecars_after_compact": bool(
                compact_result and compact_result.get("sidecar_cleanup")
            ),
        },
        "candidate_samples": _sample_entries(candidates),
        "blocker_samples": _sample_entries(blockers),
    }


def _sidecar_repair_receipt(
    *,
    db_path: Path,
    recorded_at: str,
    apply: bool,
    immutable_integrity: Mapping[str, Any] | None,
    normal_integrity_before: Mapping[str, Any] | None,
    normal_integrity_after: Mapping[str, Any] | None,
    sidecars: list[dict[str, Any]],
    blockers: list[dict[str, Any]],
    status: str | None = None,
) -> dict[str, Any]:
    return {
        "surface_kind": "runtime_lifecycle_sqlite_sidecar_repair",
        "schema_version": SCHEMA_VERSION,
        "status": status
        or (
            "blocked"
            if blockers
            else "applied"
            if apply and sidecars
            else "planned"
            if sidecars
            else "nothing_to_repair"
        ),
        "recorded_at": recorded_at,
        "db_path": str(db_path),
        "apply": bool(apply),
        "sidecar_count": len(sidecars),
        "sidecars": sidecars,
        "blocker_count": len(blockers),
        "blockers": blockers,
        "immutable_integrity_check": dict(immutable_integrity or {}),
        "normal_integrity_check_before": dict(normal_integrity_before or {}),
        "normal_integrity_check_after": dict(normal_integrity_after or {}),
        "body_included": False,
        "mutation_policy": {
            "deletes_domain_truth": False,
            "deletes_payload_body": False,
            "requires_immutable_integrity_ok_before_sidecar_removal": True,
            "removes_only_sqlite_wal_shm_sidecars": True,
        },
    }


def _write_receipt(*, db_path: Path, receipt: dict[str, Any], recorded_at: str) -> None:
    receipt_root = db_path.parent / "retention" / "runtime_lifecycle_payload"
    receipt_path = receipt_root / f"{_artifact_slug(recorded_at)}.json"
    latest_path = receipt_root / "latest.json"
    write_json(receipt_path, receipt)
    write_json(latest_path, receipt)
    receipt["receipt_path"] = str(receipt_path)
    receipt["latest_receipt_path"] = str(latest_path)


def _cold_store_root(*, db_path: Path, cold_store_root: Path) -> Path:
    namespace = db_path.parent.name
    parts = db_path.parts
    if len(parts) >= 6 and parts[-3:] == ("artifacts", "runtime", db_path.name) and parts[-5] == "quests":
        namespace = parts[-4]
    elif len(parts) >= 4 and parts[-3:] == ("runtime", "artifacts", db_path.name):
        namespace = parts[-4]
    elif len(parts) >= 5 and parts[-3:] == ("artifacts", "runtime", db_path.name):
        namespace = parts[-5]
    return (
        Path(cold_store_root).expanduser().resolve()
        / safe_artifact_id(namespace)
        / "runtime_lifecycle_payload"
        / safe_artifact_id(db_path.name)
    )


def _cold_ref_path(*, db_path: Path, cold_root: Path, candidate: Mapping[str, Any], sha256: str) -> Path:
    return (
        db_path.parent
        / "retention"
        / "runtime_lifecycle_payload"
        / "refs"
        / str(candidate.get("table"))
        / f"row{candidate.get('rowid')}-{candidate.get('column')}-{sha256[:12]}.cold_ref.json"
    )


def _primary_key_payload(*, table: str, row: Mapping[str, Any]) -> dict[str, Any]:
    keys = {
        "workspace_storage_audits": ("workspace_root", "recorded_at"),
        "report_index": ("object_root", "object_scope", "report_group", "timestamp"),
        "dispatch_receipts": ("quest_root", "dispatch_id"),
    }.get(table, ("rowid",))
    return {key: row.get(key) for key in keys if key in row}


def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    row = conn.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?", (table,)).fetchone()
    return row is not None


def _is_retention_ref(value: str) -> bool:
    try:
        payload = json.loads(value)
    except json.JSONDecodeError:
        return False
    return isinstance(payload, dict) and payload.get("surface_kind") == "runtime_lifecycle_payload_retention_ref"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def _artifact_slug(value: str) -> str:
    normalized = value.strip()
    if normalized.endswith("Z"):
        normalized = f"{normalized[:-1]}+00:00"
    return datetime.fromisoformat(normalized).astimezone(UTC).strftime(_TIMESTAMP_FORMAT)


def _sample_entries(entries: Iterable[Mapping[str, Any]], limit: int = 20) -> list[dict[str, Any]]:
    return [dict(entry) for entry in list(entries)[:limit]]


__all__ = ["repair_runtime_lifecycle_sqlite_sidecars", "run_runtime_lifecycle_payload_retention"]
