from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
import sqlite3
from typing import Any

from med_autoscience.controllers.runtime_lifecycle_payload_retention_parts.sqlite_sidecars import (
    compact_database as _compact_database,
    sqlite_integrity_check as _sqlite_integrity_check,
    sqlite_sidecar_infos as _sqlite_sidecar_infos,
)
from med_autoscience.controllers.runtime_storage_maintenance_parts.restore_proof_compaction_helpers import (
    safe_artifact_id,
    write_json,
)


SURFACE_KIND = "runtime_lifecycle_payload_retention"
SCHEMA_VERSION = 1
_TIMESTAMP_FORMAT = "%Y%m%dT%H%M%SZ"
_RETIRED_COLD_PAYLOAD_SURFACE_KIND = "runtime_lifecycle_payload_semantic_retention_ref"
_RETENTION_REF_SURFACE_KIND = "runtime_lifecycle_payload_retention_ref"
_PAYLOAD_TABLE_COLUMNS = {
    "workspace_storage_audits": ("categories_json", "payload_json"),
    "report_index": ("payload_json",),
    "dispatch_receipts": ("payload_json",),
}


def run_runtime_lifecycle_payload_retention(
    *,
    db_path: Path,
    apply: bool,
    cold_store_root: Path,
    min_mb: int = 16,
    max_rows: int | None = None,
    compact: bool = False,
    retire_cold_payloads: bool = False,
) -> dict[str, Any]:
    resolved_db_path = Path(db_path).expanduser().resolve()
    recorded_at = _utc_now()
    threshold_bytes = max(0, int(min_mb)) * 1024 * 1024
    cold_root = _cold_store_root(db_path=resolved_db_path, cold_store_root=cold_store_root)
    candidates: list[dict[str, Any]] = []
    blockers: list[dict[str, Any]] = []
    moved_count = 0
    deduped_count = 0
    cold_payload_candidates: list[dict[str, Any]] = []
    retired_cold_payload_count = 0
    retired_cold_payload_release_bytes = 0
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
            cold_payload_candidates=[],
            retired_cold_payload_count=0,
            retired_cold_payload_release_bytes=0,
            actual_release_bytes=0,
            compact_result=None,
            retire_cold_payloads=retire_cold_payloads,
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
        if retire_cold_payloads:
            remaining = None if max_rows is None else max(0, int(max_rows) - len(candidates))
            for candidate in _iter_externalized_payload_candidates(
                conn=conn,
                db_path=resolved_db_path,
                cold_root=cold_root,
                threshold_bytes=threshold_bytes,
            ):
                if remaining is not None and len(cold_payload_candidates) >= remaining:
                    break
                if candidate.get("status") == "skipped_below_threshold":
                    cold_payload_candidates.append(candidate)
                    continue
                if str(candidate.get("status") or "").startswith("blocked"):
                    if candidate.get("status") == "blocked_already_retired" and apply:
                        applied = _apply_externalized_payload_candidate(
                            conn=conn,
                            db_path=resolved_db_path,
                            candidate=candidate,
                            cold_root=cold_root,
                            recorded_at=recorded_at,
                        )
                        candidate.update(applied)
                        if applied.get("status") == "runtime_lifecycle_payload_ref_synced_to_existing_semantic_ref":
                            retired_cold_payload_count += 1
                        elif str(applied.get("status") or "").startswith("blocked"):
                            blockers.append(candidate)
                        cold_payload_candidates.append(candidate)
                        continue
                    blockers.append(candidate)
                    cold_payload_candidates.append(candidate)
                    continue
                if apply:
                    applied = _apply_externalized_payload_candidate(
                        conn=conn,
                        db_path=resolved_db_path,
                        candidate=candidate,
                        cold_root=cold_root,
                        recorded_at=recorded_at,
                    )
                    candidate.update(applied)
                    if applied.get("status") == "runtime_lifecycle_payload_raw_body_retired":
                        retired_cold_payload_count += 1
                        retired_cold_payload_release_bytes += int(applied.get("release_bytes") or 0)
                    elif str(applied.get("status") or "").startswith("blocked"):
                        blockers.append(candidate)
                cold_payload_candidates.append(candidate)
        if apply and candidates:
            conn.commit()
        elif apply and cold_payload_candidates:
            conn.commit()

    compact_result = _compact_database(resolved_db_path) if apply and compact and not blockers else None
    actionable_cold_payload_count = _actionable_cold_payload_candidate_count(cold_payload_candidates)
    status = (
        "applied"
        if apply and (moved_count or deduped_count or retired_cold_payload_count) and not blockers
        else "compacted"
        if apply and compact_result and compact_result.get("status") == "compacted" and not blockers
        else "blocked"
        if apply and blockers
        else "planned"
        if candidates or actionable_cold_payload_count
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
        cold_payload_candidates=cold_payload_candidates,
        retired_cold_payload_count=retired_cold_payload_count,
        retired_cold_payload_release_bytes=retired_cold_payload_release_bytes,
        actual_release_bytes=actual_release_bytes,
        compact_result=compact_result,
        status=status,
        retire_cold_payloads=retire_cold_payloads,
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
    for table, columns in _PAYLOAD_TABLE_COLUMNS.items():
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


def _iter_externalized_payload_candidates(
    *,
    conn: sqlite3.Connection,
    db_path: Path,
    cold_root: Path,
    threshold_bytes: int,
) -> Iterable[dict[str, Any]]:
    for table, columns in _PAYLOAD_TABLE_COLUMNS.items():
        if not _table_exists(conn, table):
            continue
        for row in conn.execute(f"SELECT rowid, * FROM {table} ORDER BY rowid"):
            row_map = dict(row)
            for column in columns:
                ref_payload = _retention_ref_payload(row_map.get(column))
                if ref_payload is None:
                    continue
                if ref_payload.get("semantic_restore_policy"):
                    continue
                object_path = Path(str(ref_payload.get("cold_object_path") or "")).expanduser()
                cold_ref_path = Path(str(ref_payload.get("cold_ref_path") or "")).expanduser()
                original_sha = str(ref_payload.get("original_sha256") or "")
                original_bytes = _int_or_none(ref_payload.get("original_bytes"))
                candidate = {
                    "status": "candidate",
                    "db_path": str(db_path),
                    "table": table,
                    "rowid": int(row_map["rowid"]),
                    "column": column,
                    "primary_key": _primary_key_payload(table=table, row=row_map),
                    "cold_object_path": str(object_path),
                    "cold_ref_path": str(cold_ref_path),
                    "sha256": original_sha,
                    "bytes": original_bytes or 0,
                    "inline_ref_bytes": len(str(row_map.get(column) or "").encode("utf-8")),
                }
                blocker = _externalized_payload_blocker(
                    candidate=candidate,
                    object_path=object_path,
                    cold_ref_path=cold_ref_path,
                    cold_root=cold_root,
                    threshold_bytes=threshold_bytes,
                )
                if blocker:
                    candidate.update(blocker)
                yield candidate


def _externalized_payload_blocker(
    *,
    candidate: Mapping[str, Any],
    object_path: Path,
    cold_ref_path: Path,
    cold_root: Path,
    threshold_bytes: int,
) -> dict[str, Any] | None:
    if not str(candidate.get("sha256") or ""):
        return {"status": "blocked_missing_original_sha256"}
    if int(candidate.get("bytes") or 0) < threshold_bytes:
        return {"status": "skipped_below_threshold"}
    try:
        resolved_object = object_path.resolve()
    except OSError:
        return {"status": "blocked_missing_cold_object"}
    if not resolved_object.is_file() or resolved_object.is_symlink():
        return {"status": "blocked_missing_cold_object"}
    if not _is_relative_to(resolved_object, cold_root):
        return {"status": "blocked_cold_object_outside_cold_root", "cold_root": str(cold_root)}
    if _retired_cold_payload_object_payload(resolved_object) is not None:
        return {"status": "blocked_already_retired"}
    try:
        resolved_ref = cold_ref_path.resolve()
    except OSError:
        return {"status": "blocked_missing_cold_ref"}
    if not resolved_ref.is_file() or resolved_ref.is_symlink():
        return {"status": "blocked_missing_cold_ref"}
    try:
        cold_ref_payload = json.loads(resolved_ref.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return {"status": "blocked_unreadable_cold_ref", "error": str(exc)}
    if not isinstance(cold_ref_payload, dict) or cold_ref_payload.get("surface_kind") != _RETENTION_REF_SURFACE_KIND:
        return {"status": "blocked_non_runtime_lifecycle_payload_ref"}
    if cold_ref_payload.get("semantic_restore_policy"):
        return {"status": "blocked_cold_ref_already_retired"}
    if str(cold_ref_payload.get("cold_object_path") or "") != str(object_path):
        return {"status": "blocked_cold_ref_object_mismatch"}
    if str(cold_ref_payload.get("original_sha256") or "") != str(candidate.get("sha256") or ""):
        return {"status": "blocked_cold_ref_sha256_mismatch"}
    return None


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


def _apply_externalized_payload_candidate(
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
        return {"status": "blocked_row_missing", "release_bytes": 0}
    ref_payload = _retention_ref_payload(row[0])
    if ref_payload is None:
        return {"status": "blocked_inline_ref_missing", "release_bytes": 0}
    object_path = Path(str(ref_payload.get("cold_object_path") or "")).expanduser()
    cold_ref_path = Path(str(ref_payload.get("cold_ref_path") or "")).expanduser()
    expected_sha = str(ref_payload.get("original_sha256") or "")
    if expected_sha != str(candidate.get("sha256") or ""):
        return {"status": "blocked_inline_ref_sha256_changed", "release_bytes": 0}
    try:
        resolved_object = object_path.resolve()
    except OSError:
        return {"status": "blocked_missing_cold_object", "release_bytes": 0}
    if not resolved_object.is_file() or resolved_object.is_symlink():
        return {"status": "blocked_missing_cold_object", "release_bytes": 0}
    if not _is_relative_to(resolved_object, cold_root):
        return {
            "status": "blocked_cold_object_outside_cold_root",
            "cold_root": str(cold_root),
            "release_bytes": 0,
        }
    if not cold_ref_path.is_file() or cold_ref_path.is_symlink():
        return {"status": "blocked_missing_cold_ref", "release_bytes": 0}
    try:
        cold_ref_payload = json.loads(cold_ref_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return {"status": "blocked_unreadable_cold_ref", "error": str(exc), "release_bytes": 0}
    if not isinstance(cold_ref_payload, dict) or cold_ref_payload.get("surface_kind") != _RETENTION_REF_SURFACE_KIND:
        return {"status": "blocked_non_runtime_lifecycle_payload_ref", "release_bytes": 0}
    if str(cold_ref_payload.get("cold_object_path") or "") != str(object_path):
        return {"status": "blocked_cold_ref_object_mismatch", "release_bytes": 0}
    if str(cold_ref_payload.get("original_sha256") or "") != expected_sha:
        return {"status": "blocked_cold_ref_sha256_mismatch", "release_bytes": 0}

    retired_object_payload = _retired_cold_payload_object_payload(object_path)
    if retired_object_payload is not None:
        if str(retired_object_payload.get("original_sha256") or "") != expected_sha:
            return {"status": "blocked_existing_semantic_ref_sha256_mismatch", "release_bytes": 0}
        if str(retired_object_payload.get("semantic_capsule_path") or ""):
            restore_policy = {
                "status": "runtime_lifecycle_payload_raw_body_retired",
                "recorded_at": recorded_at,
                "semantic_capsule_path": str(retired_object_payload.get("semantic_capsule_path")),
                "byte_for_byte_restore_of_runtime_lifecycle_payload_body": False,
                "original_sha256": expected_sha,
                "original_bytes": ref_payload.get("original_bytes"),
                "body_included": False,
            }
            _sync_externalized_payload_ref(
                conn=conn,
                table=table,
                column=column,
                rowid=rowid,
                ref_payload=ref_payload,
                cold_ref_payload=cold_ref_payload,
                cold_ref_path=cold_ref_path,
                restore_policy=restore_policy,
            )
            return {
                "status": "runtime_lifecycle_payload_ref_synced_to_existing_semantic_ref",
                "semantic_capsule_path": str(retired_object_payload.get("semantic_capsule_path")),
                "release_bytes": 0,
            }
        return {"status": "blocked_existing_semantic_ref_missing_capsule", "release_bytes": 0}

    observed_sha = _sha256(object_path)
    if observed_sha != expected_sha:
        return {
            "status": "blocked_payload_sha256_changed",
            "expected_sha256": expected_sha,
            "observed_sha256": observed_sha,
            "release_bytes": 0,
        }
    original_bytes = object_path.stat().st_size
    capsule_root = object_path.parents[2] / ".retention" / SURFACE_KIND / "capsules" / _artifact_slug(recorded_at)
    capsule = _externalized_payload_capsule(
        db_path=db_path,
        candidate=candidate,
        object_path=object_path,
        cold_ref_path=cold_ref_path,
        recorded_at=recorded_at,
    )
    capsule_path = capsule_root / f"{safe_artifact_id(object_path.stem)[:80]}-{observed_sha[:12]}.json"
    write_json(capsule_path, capsule)
    restore_policy = {
        "status": "runtime_lifecycle_payload_raw_body_retired",
        "recorded_at": recorded_at,
        "semantic_capsule_path": str(capsule_path),
        "byte_for_byte_restore_of_runtime_lifecycle_payload_body": False,
        "original_sha256": observed_sha,
        "original_bytes": original_bytes,
        "body_included": False,
    }
    replacement = {
        "surface_kind": _RETIRED_COLD_PAYLOAD_SURFACE_KIND,
        "schema_version": SCHEMA_VERSION,
        "status": "runtime_lifecycle_payload_raw_body_retired",
        "recorded_at": recorded_at,
        "cold_object_path": str(object_path),
        "semantic_capsule_path": str(capsule_path),
        "original_sha256": observed_sha,
        "original_bytes": original_bytes,
        "body_included": False,
        "restore_policy": {
            "byte_for_byte_restore_of_runtime_lifecycle_payload_body": False,
            "restore_runtime_lifecycle_semantics_from_capsule": True,
            "reproducibility_basis": "runtime_lifecycle_route_primary_key_original_hash_digest_current_refs",
        },
    }
    object_path.write_text(json.dumps(replacement, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    _sync_externalized_payload_ref(
        conn=conn,
        table=table,
        column=column,
        rowid=rowid,
        ref_payload=dict(ref_payload),
        cold_ref_payload=dict(cold_ref_payload),
        cold_ref_path=cold_ref_path,
        restore_policy=restore_policy,
    )
    replacement_bytes = object_path.stat().st_size
    return {
        "status": "runtime_lifecycle_payload_raw_body_retired",
        "semantic_capsule_path": str(capsule_path),
        "replacement_bytes": replacement_bytes,
        "release_bytes": max(0, original_bytes - replacement_bytes),
    }


def _sync_externalized_payload_ref(
    *,
    conn: sqlite3.Connection,
    table: str,
    column: str,
    rowid: int,
    ref_payload: Mapping[str, Any],
    cold_ref_payload: Mapping[str, Any],
    cold_ref_path: Path,
    restore_policy: Mapping[str, Any],
) -> None:
    updated_ref = dict(ref_payload)
    updated_ref["semantic_restore_policy"] = dict(restore_policy)
    updated_ref["restore_command"] = None
    updated_ref["body_included"] = False
    updated_cold_ref = dict(cold_ref_payload)
    updated_cold_ref["semantic_restore_policy"] = dict(restore_policy)
    updated_cold_ref["restore_command"] = None
    updated_cold_ref["body_included"] = False
    write_json(cold_ref_path, updated_cold_ref)
    conn.execute(
        f"UPDATE {table} SET {column} = ? WHERE rowid = ?",
        (json.dumps(updated_ref, ensure_ascii=False, sort_keys=True), rowid),
    )


def _externalized_payload_capsule(
    *,
    db_path: Path,
    candidate: Mapping[str, Any],
    object_path: Path,
    cold_ref_path: Path,
    recorded_at: str,
) -> dict[str, Any]:
    head, tail = _head_tail_hex(object_path)
    return {
        "surface_kind": "runtime_lifecycle_payload_semantic_capsule",
        "schema_version": SCHEMA_VERSION,
        "status": "ready",
        "recorded_at": recorded_at,
        "db_path": str(db_path),
        "table": candidate.get("table"),
        "rowid": candidate.get("rowid"),
        "column": candidate.get("column"),
        "primary_key": candidate.get("primary_key"),
        "source_cold_object_path": str(object_path),
        "source_cold_ref_path": str(cold_ref_path),
        "source_sha256": candidate.get("sha256"),
        "source_bytes": candidate.get("bytes"),
        "byte_digest": {
            "sha256": candidate.get("sha256"),
            "bytes": candidate.get("bytes"),
            "head_hex": head,
            "tail_hex": tail,
        },
        "restore_policy": {
            "byte_for_byte_restore_of_runtime_lifecycle_payload_body": False,
            "runtime_lifecycle_payload_body_retired_by_explicit_policy": True,
            "route_and_primary_key_remain_inline": True,
        },
        "current_truth_refs": {
            "domain_truth_mutated": False,
            "publication_eval_mutated": False,
            "controller_decisions_mutated": False,
            "owner_receipts_mutated": False,
        },
        "body_included": False,
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
    cold_payload_candidates: list[dict[str, Any]],
    retired_cold_payload_count: int,
    retired_cold_payload_release_bytes: int,
    actual_release_bytes: int,
    compact_result: dict[str, Any] | None,
    retire_cold_payloads: bool = False,
    status: str | None = None,
) -> dict[str, Any]:
    return {
        "surface_kind": SURFACE_KIND,
        "schema_version": SCHEMA_VERSION,
        "status": status
        or (
            "applied"
            if apply and (moved_count or deduped_count or retired_cold_payload_count) and not blockers
            else "compacted"
            if apply and compact_result and compact_result.get("status") == "compacted" and not blockers
            else "blocked"
            if blockers
            else "planned"
            if candidates or _actionable_cold_payload_candidate_count(cold_payload_candidates)
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
        "cold_payload_candidate_count": len(cold_payload_candidates),
        "actionable_cold_payload_candidate_count": _actionable_cold_payload_candidate_count(cold_payload_candidates),
        "moved_count": moved_count,
        "deduped_count": deduped_count,
        "retire_cold_payloads": bool(retire_cold_payloads),
        "retired_cold_payload_count": retired_cold_payload_count,
        "retired_cold_payload_release_bytes": retired_cold_payload_release_bytes,
        "blocker_count": len(blockers),
        "actual_release_bytes": actual_release_bytes + retired_cold_payload_release_bytes,
        "compact": compact_result,
        "body_included": False,
        "mutation_policy": {
            "externalizes_large_derived_payload_columns": bool(apply),
            "retires_externalized_runtime_lifecycle_payload_body": bool(apply and retire_cold_payloads),
            "keeps_route_and_summary_columns_inline": True,
            "deletes_domain_truth": False,
            "compacts_database_file": bool(apply and compact),
            "removes_stale_sqlite_sidecars_after_compact": bool(
                compact_result and compact_result.get("sidecar_cleanup")
            ),
        },
        "candidate_samples": _sample_entries(candidates),
        "cold_payload_candidate_samples": _sample_entries(cold_payload_candidates),
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


def _int_or_none(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    row = conn.execute("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?", (table,)).fetchone()
    return row is not None


def _is_retention_ref(value: str) -> bool:
    return _retention_ref_payload(value) is not None


def _retention_ref_payload(value: Any) -> dict[str, Any] | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        payload = json.loads(value)
    except json.JSONDecodeError:
        return None
    if isinstance(payload, dict) and payload.get("surface_kind") == _RETENTION_REF_SURFACE_KIND:
        return payload
    return None


def _retired_cold_payload_object_payload(path: Path) -> dict[str, Any] | None:
    try:
        if path.stat().st_size > 1024 * 1024:
            return None
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    if isinstance(payload, dict) and payload.get("surface_kind") == _RETIRED_COLD_PAYLOAD_SURFACE_KIND:
        return payload
    return None


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _head_tail_hex(path: Path, limit: int = 4096) -> tuple[str, str]:
    size = path.stat().st_size
    with path.open("rb") as handle:
        head = handle.read(limit)
        if size > limit:
            handle.seek(max(0, size - limit))
            tail = handle.read(limit)
        else:
            tail = head
    return head.hex(), tail.hex()


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


def _actionable_cold_payload_candidate_count(entries: Iterable[Mapping[str, Any]]) -> int:
    return sum(1 for entry in entries if entry.get("status") != "skipped_below_threshold")

__all__ = ["repair_runtime_lifecycle_sqlite_sidecars", "run_runtime_lifecycle_payload_retention"]
