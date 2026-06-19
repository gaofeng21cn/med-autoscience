from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
import sqlite3
import subprocess
from typing import Any

from med_autoscience.runtime_protocol.workspace_artifacts import workspace_runtime_artifact_path

SCHEMA_VERSION = 1
SURFACE_KIND = "mas_domain_authority_refs_index"
DEFAULT_DB_FILENAME = "domain_authority_refs.sqlite"
SQLITE_GITIGNORE_PATTERNS = (
    "*.sqlite",
    "*.sqlite-wal",
    "*.sqlite-shm",
    "*.db-wal",
    "*.db-shm",
)

AUTHORITY_REF_TABLES = (
    "authority_ref_metadata",
    "archive_refs",
    "owner_route_receipts",
    "dispatch_receipts",
    "paper_progress_transition_refs",
    "stage_artifact_delta_refs",
)
OPL_FAMILY_ADAPTER_SOURCE_TABLES = AUTHORITY_REF_TABLES
LEGACY_TABLE_POLICY = {
    "runtime_events": "tombstone_provenance_only",
    "runtime_snapshots": "tombstone_provenance_only",
    "lineage_nodes": "tombstone_provenance_only",
    "workspace_allocations": "tombstone_provenance_only",
    "turn_receipts": "tombstone_provenance_only",
    "surface_refs": "tombstone_provenance_only",
    "report_index": "tombstone_provenance_only",
}


def domain_authority_refs_index_contract() -> dict[str, Any]:
    return {
        "surface_kind": SURFACE_KIND,
        "schema_version": SCHEMA_VERSION,
        "default_db_filename": DEFAULT_DB_FILENAME,
        "sqlite_gitignore_patterns": list(SQLITE_GITIGNORE_PATTERNS),
        "authority_ref_tables": list(AUTHORITY_REF_TABLES),
        "role": "refs_only_domain_authority_receipt_index",
        "owner": "med-autoscience",
        "generic_persistence_owner": "one-person-lab",
        "generic_runtime_owner": "one-person-lab",
        "generic_persistence_engine_claim_allowed": False,
        "generic_scheduler_queue_attempt_claim_allowed": False,
        "default_record_behavior": "source_adapter_emitted_no_default_sqlite_persistence",
        "sqlite_persistence_policy": {
            "default_persist_sqlite": False,
            "requires_explicit_opt_in": True,
            "opt_in_parameter": "persist_sqlite",
            "allowed_use": "historical_replay_or_explicit_local_refs_inspection",
            "active_caller_db_path_does_not_imply_persistence": True,
        },
        "authority_policy": {
            "stores_body": False,
            "stores_domain_truth": False,
            "rebuildable": True,
            "started_worker": False,
            "outbox_record": False,
            "can_generate_next_action_authority": False,
            "can_authorize_provider_admission": False,
            "can_authorize_quality_verdict": False,
            "can_authorize_publication_ready": False,
            "provider_completion_is_domain_completion": False,
            "queue_succeeded_is_domain_completion": False,
            "domain_completion_owner": "med-autoscience",
            "runtime_control_owner": "one-person-lab",
        },
        "file_authority_surfaces": [
            "publication_eval/latest.json",
            "controller_decisions/latest.json",
            "domain_route_owner_route",
            "domain_owner_action_dispatch_receipt",
            "paper_progress_transition_ref_receipt",
        ],
        "standard_agent_purity_absent_surface_ids": [
            "mas_generic_runtime_lifecycle_contract",
            "mas_generic_runtime_lifecycle_read_model",
            "mas_generic_runtime_session_read_model",
            "mas_generic_quest_materializer",
            "mas_generic_lifecycle_refs_adapter",
            "runtime_protocol.lifecycle_refs_adapter",
            "runtime_protocol.lifecycle_refs_adapter_parts",
        ],
        "retired_absent_surfaces": [
            "src/med_autoscience/runtime_protocol/lifecycle_refs_adapter.py",
            "src/med_autoscience/runtime_protocol/lifecycle_refs_adapter_parts/",
        ],
        "forbidden_tables": [
            "runtime_events",
            "runtime_snapshots",
            "lineage_nodes",
            "workspace_allocations",
            "turn_receipts",
            "surface_refs",
            "report_index",
        ],
        "legacy_table_policy": dict(LEGACY_TABLE_POLICY),
        "opl_state_index_kernel_takeover_bridge": {
            "surface_kind": "domain_authority_refs_index_state_index_takeover_bridge",
            "bridge_status": "repo_replacement_parity_proven_live_takeover_tail_open",
            "replacement_owner_surface": "one-person-lab StateIndexKernel",
            "mas_source_adapter_role": "refs_only_domain_authority_receipt_source_adapter",
            "active_caller_status": "repo_active_callers_migrated_to_opl_state_index_source_adapter",
            "active_caller_effect": "opl_state_index_source_adapter_emitted_no_sqlite_persistence",
            "default_sqlite_persistence": False,
            "sqlite_persistence_requires_explicit_opt_in": True,
            "active_caller_db_path_does_not_imply_persistence": True,
            "active_caller_retains_surface": False,
            "active_caller_retains_authority": False,
            "legacy_domain_authority_refs_index_role": (
                "explicit_history_replay_or_local_refs_inspection_only"
            ),
            "source_tables": list(AUTHORITY_REF_TABLES),
            "forbidden_legacy_tables": list(LEGACY_TABLE_POLICY),
            "repo_replacement_parity_refs": [
                "src/med_autoscience/runtime_protocol/refs_only_state_index_pilot.py",
                "src/med_autoscience/controllers/opl_state_index_kernel.py",
                "tests/test_runtime_storage_maintenance_cases/runtime_refs_only_state_index_pilot.py::test_refs_only_state_index_pilot_indexes_small_runtime_refs_without_bodies",
                "tests/test_opl_state_index_kernel.py::test_state_index_kernel_rows_are_refs_only_and_rebuildable",
            ],
            "required_opl_readback_ref": (
                "src/med_autoscience/runtime_protocol/refs_only_state_index_pilot.py#"
                "opl_state_index_kernel_readback_requirement"
            ),
            "live_takeover_required_before_physical_delete": True,
            "no_active_caller_required_before_physical_delete": True,
            "tombstone_or_provenance_required_before_physical_delete": True,
            "completion_claim_requires_live_opl_readback_or_no_active_caller": True,
            "runtime_active_private_state_index_caller_scan": {
                "status": "no_runtime_active_private_state_index_callers",
                "no_runtime_active_private_state_index_caller_proven": True,
                "runtime_active_caller_count": 0,
                "active_runtime_callers": [],
                "current_runtime_caller_route": (
                    "med_autoscience.runtime_protocol.opl_state_index_source_adapter"
                ),
                "legacy_helper_status": (
                    "history_replay_or_local_inspection_only_tail_open"
                ),
                "physical_delete_allowed": False,
                "forbidden_completion_claims": [
                    "runtime_active_no_private_caller_as_physical_delete",
                    "history_replay_opt_in_as_runtime_active_caller",
                    "source_adapter_manifest_as_live_opl_state_index_readback",
                ],
            },
            "legacy_helper_active_caller_scan": {
                "status": "active_replay_or_local_inspection_callers_present_tail_open",
                "no_active_replay_or_local_inspection_caller_proven": False,
                "physical_delete_allowed": False,
                "required_before_physical_delete": (
                    "domain_authority_refs_index_live_state_index_takeover_or_"
                    "no_active_replay_local_inspection_caller_physical_delete_ref"
                ),
                "active_callers": [
                    (
                        "paper_progress_transition_refs.record_paper_progress_transition_ref::"
                        "persist_authority_refs_index_explicit_opt_in"
                    ),
                ],
                "allowed_consumption": [
                    "explicit_history_replay",
                    "explicit_local_refs_inspection",
                    "tombstone_provenance",
                ],
                "forbidden_completion_claims": [
                    "legacy_helper_active_scan_as_physical_delete",
                    "legacy_helper_active_callers_as_no_active_caller",
                    "opl_family_adoption_sqlite_inspection_as_current_projection",
                    "legacy_sqlite_payload_projection_as_state_index_kernel_takeover",
                    "explicit_replay_opt_in_as_live_opl_readback",
                ],
            },
            "mas_projection_cannot_replace": [
                "opl_state_index_kernel_readback",
                "opl_lifecycle_index",
                "opl_operator_read_model",
                "opl_artifact_index",
                "opl_queue_index",
            ],
        },
    }


def quest_authority_refs_index_path(quest_root: Path) -> Path:
    return Path(quest_root).expanduser().resolve() / "artifacts" / "runtime" / DEFAULT_DB_FILENAME


def workspace_authority_refs_index_path(workspace_root: Path) -> Path:
    return workspace_runtime_artifact_path(workspace_root, DEFAULT_DB_FILENAME)


def record_archive_ref(
    *,
    quest_root: Path,
    archive_ref: Mapping[str, Any],
    db_path: Path | None = None,
    persist_sqlite: bool = False,
) -> dict[str, Any]:
    resolved_quest_root = Path(quest_root).expanduser().resolve()
    resolved_db_path = _resolve_db_path(db_path, default=quest_authority_refs_index_path(resolved_quest_root))
    archive_id = _require_text("archive_ref.archive_id", archive_ref.get("archive_id"))
    archive_path = Path(_require_text("archive_ref.archive_path", archive_ref.get("archive_path"))).expanduser().resolve()
    source_manifest_path = _text(archive_ref.get("source_manifest_path"))
    restore_proof_path = _text(archive_ref.get("restore_proof_path"))
    archived_at = _text(archive_ref.get("archived_at")) or _utc_now()
    payload_json = _stable_json(_archive_ref_projection_payload(archive_ref))
    payload_sha256 = _sha256(_stable_json(archive_ref))
    if not persist_sqlite:
        return _source_adapter_result(
            indexed_table="archive_refs",
            scope="quest",
            source_path=archive_path,
            payload_sha256=payload_sha256,
            db_path=resolved_db_path,
        )
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
                _as_int(archive_ref.get("bytes")),
                str(Path(source_manifest_path).expanduser().resolve()) if source_manifest_path else None,
                str(Path(restore_proof_path).expanduser().resolve()) if restore_proof_path else None,
                _stable_json(archive_ref.get("source_buckets") if isinstance(archive_ref.get("source_buckets"), list) else []),
                payload_sha256,
                payload_json,
                _utc_now(),
            ),
        )
    return _index_result(db_path=resolved_db_path, indexed_table="archive_refs", indexed_count=1, scope="quest")


def record_owner_route_receipt(
    *,
    study_root: Path,
    receipt: Mapping[str, Any],
    receipt_path: Path,
    db_path: Path | None = None,
    persist_sqlite: bool = False,
) -> dict[str, Any]:
    resolved_study_root = Path(study_root).expanduser().resolve()
    resolved_db_path = _resolve_db_path(db_path, default=workspace_authority_refs_index_path(resolved_study_root.parent.parent))
    resolved_receipt_path = Path(receipt_path).expanduser().resolve()
    payload_json = _stable_json(_owner_route_projection_payload(receipt))
    payload_sha256 = _sha256(_stable_json(receipt))
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
        "payload_sha256": payload_sha256,
        "payload_json": payload_json,
        "recorded_at": _utc_now(),
    }
    if not persist_sqlite:
        return _source_adapter_result(
            indexed_table="owner_route_receipts",
            scope="study",
            source_path=resolved_receipt_path,
            payload_sha256=payload_sha256,
            db_path=resolved_db_path,
        )
    with _connect(resolved_db_path) as conn:
        _ensure_schema(conn)
        _upsert_row(conn, table="owner_route_receipts", conflict_columns=("study_root", "idempotency_key"), row=row)
    return _index_result(db_path=resolved_db_path, indexed_table="owner_route_receipts", indexed_count=1, scope="study")


def record_dispatch_receipt(
    *,
    quest_root: Path,
    receipt: Mapping[str, Any],
    receipt_path: Path,
    db_path: Path | None = None,
    persist_sqlite: bool = False,
) -> dict[str, Any]:
    resolved_quest_root = Path(quest_root).expanduser().resolve()
    resolved_db_path = _resolve_db_path(db_path, default=quest_authority_refs_index_path(resolved_quest_root))
    resolved_receipt_path = Path(receipt_path).expanduser().resolve()
    payload_json = _stable_json(_dispatch_projection_payload(receipt))
    payload_sha256 = _sha256(_stable_json(receipt))
    row = {
        "quest_root": str(resolved_quest_root),
        "dispatch_id": _dispatch_id(receipt=receipt, source_path=resolved_receipt_path, payload_sha256=payload_sha256),
        "study_id": _require_text("receipt.study_id", receipt.get("study_id")),
        "quest_id": _text(receipt.get("quest_id")),
        "action_type": _text(receipt.get("action_type")),
        "created_at": _dispatch_created_at(receipt),
        "status": _dispatch_status(receipt),
        "idempotency_key": _text(receipt.get("idempotency_key")),
        "owner_route_json": _stable_json(_mapping(receipt.get("owner_route"))),
        "source_path": str(resolved_receipt_path),
        "payload_sha256": payload_sha256,
        "payload_json": payload_json,
        "recorded_at": _utc_now(),
    }
    if not persist_sqlite:
        return _source_adapter_result(
            indexed_table="dispatch_receipts",
            scope="quest",
            source_path=resolved_receipt_path,
            payload_sha256=payload_sha256,
            db_path=resolved_db_path,
        )
    with _connect(resolved_db_path) as conn:
        _ensure_schema(conn)
        _upsert_row(conn, table="dispatch_receipts", conflict_columns=("quest_root", "dispatch_id"), row=row)
    return _index_result(db_path=resolved_db_path, indexed_table="dispatch_receipts", indexed_count=1, scope="quest")


def record_paper_progress_transition_ref(
    *,
    study_root: Path,
    quest_root: Path,
    receipt: Mapping[str, Any],
    receipt_path: Path,
    db_path: Path | None = None,
    persist_sqlite: bool = False,
) -> dict[str, Any]:
    return _record_study_receipt_ref(
        table="paper_progress_transition_refs",
        study_root=study_root,
        quest_root=quest_root,
        receipt=receipt,
        receipt_path=receipt_path,
        db_path=db_path,
        persist_sqlite=persist_sqlite,
    )


def record_stage_artifact_delta_ref(
    *,
    study_root: Path,
    quest_root: Path,
    receipt: Mapping[str, Any],
    receipt_path: Path,
    db_path: Path | None = None,
    persist_sqlite: bool = False,
) -> dict[str, Any]:
    return _record_study_receipt_ref(
        table="stage_artifact_delta_refs",
        study_root=study_root,
        quest_root=quest_root,
        receipt=receipt,
        receipt_path=receipt_path,
        db_path=db_path,
        persist_sqlite=persist_sqlite,
    )


def _record_study_receipt_ref(
    *,
    table: str,
    study_root: Path,
    quest_root: Path,
    receipt: Mapping[str, Any],
    receipt_path: Path,
    db_path: Path | None,
    persist_sqlite: bool,
) -> dict[str, Any]:
    resolved_study_root = Path(study_root).expanduser().resolve()
    resolved_quest_root = Path(quest_root).expanduser().resolve()
    resolved_db_path = _resolve_db_path(db_path, default=workspace_authority_refs_index_path(resolved_study_root.parent.parent))
    resolved_receipt_path = Path(receipt_path).expanduser().resolve()
    payload_sha256 = _sha256(_stable_json(receipt))
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
        "started_worker": 0,
        "worker_start_ref": None,
        "duplicate_of_receipt_id": _text(receipt.get("duplicate_of_receipt_id")),
        "fail_closed_reason": _text(receipt.get("fail_closed_reason")),
        "source_path": str(resolved_receipt_path),
        "payload_sha256": payload_sha256,
        "recorded_at": _require_text("receipt.recorded_at", receipt.get("recorded_at")),
    }
    if not persist_sqlite:
        result = _source_adapter_result(
            indexed_table=table,
            scope="study",
            source_path=resolved_receipt_path,
            payload_sha256=payload_sha256,
            db_path=resolved_db_path,
        )
        result.update(
            {
                "started_worker": False,
                "worker_start_ref": None,
                "outbox_record": False,
                "body_included": False,
                "authority_boundary": _refs_only_authority_boundary(),
            }
        )
        return result
    with _connect(resolved_db_path) as conn:
        _ensure_schema(conn)
        _upsert_row(conn, table=table, conflict_columns=("study_root", "receipt_id"), row=row)
    result = _index_result(db_path=resolved_db_path, indexed_table=table, indexed_count=1, scope="study")
    result.update(
        {
            "payload_sha256": payload_sha256,
            "started_worker": False,
            "worker_start_ref": None,
            "outbox_record": False,
            "body_included": False,
            "authority_boundary": _refs_only_authority_boundary(),
        }
    )
    return result


def inspect_authority_refs_index(db_path: Path) -> dict[str, Any]:
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
        tables = {table: _table_count(conn, table) for table in AUTHORITY_REF_TABLES}
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


def _ensure_schema(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS authority_ref_metadata(
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
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
        CREATE TABLE IF NOT EXISTS paper_progress_transition_refs(
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
            recorded_at TEXT NOT NULL,
            PRIMARY KEY (study_root, receipt_id)
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS stage_artifact_delta_refs(
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
            recorded_at TEXT NOT NULL,
            PRIMARY KEY (study_root, receipt_id)
        )
        """
    )
    conn.execute(
        "INSERT OR REPLACE INTO authority_ref_metadata(key, value) VALUES ('schema_version', ?)",
        (str(SCHEMA_VERSION),),
    )
    conn.execute(
        "INSERT OR REPLACE INTO authority_ref_metadata(key, value) VALUES ('surface_kind', ?)",
        (SURFACE_KIND,),
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


def _resolve_db_path(db_path: Path | None, *, default: Path) -> Path:
    return Path(db_path if db_path is not None else default).expanduser().resolve()


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


def _source_adapter_result(
    *,
    indexed_table: str,
    scope: str,
    source_path: Path,
    payload_sha256: str,
    db_path: Path,
) -> dict[str, Any]:
    return {
        "surface_kind": SURFACE_KIND,
        "schema_version": SCHEMA_VERSION,
        "status": "source_adapter_emitted",
        "scope": scope,
        "indexed_table": indexed_table,
        "indexed_count": 0,
        "sqlite_persisted": False,
        "sqlite_persistence_requires_explicit_opt_in": True,
        "db_path": str(db_path),
        "source_path": str(source_path),
        "payload_sha256": payload_sha256,
        "source_adapter_role": "refs_only_domain_authority_receipt_source_adapter",
        "replacement_owner_surface": "one-person-lab StateIndexKernel",
        "opl_state_index_kernel_required": True,
        "completion_claim_requires_live_opl_readback_or_no_active_caller": True,
        "authority_boundary": _refs_only_authority_boundary(),
    }


def _refs_only_authority_boundary() -> dict[str, Any]:
    return {
        "surface_kind": "mas_domain_authority_refs_index_boundary",
        "refs_only": True,
        "body_included": False,
        "rebuildable": True,
        "started_worker": False,
        "outbox_record": False,
        "can_start_worker": False,
        "can_create_outbox_record": False,
        "can_generate_next_action_authority": False,
        "can_authorize_provider_admission": False,
        "can_authorize_quality_verdict": False,
        "can_authorize_publication_ready": False,
    }


def _archive_ref_projection_payload(archive_ref: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "archive_id": _text(archive_ref.get("archive_id")),
        "archive_path": _text(archive_ref.get("archive_path")),
        "archive_format": _text(archive_ref.get("archive_format")),
        "sha256": _text(archive_ref.get("sha256")),
        "bytes": _as_int(archive_ref.get("bytes")),
        "source_manifest_path": _text(archive_ref.get("source_manifest_path")),
        "restore_proof_path": _text(archive_ref.get("restore_proof_path")),
        "body_included": False,
    }


def _owner_route_projection_payload(receipt: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "surface": _text(receipt.get("surface")),
        "study_id": _text(receipt.get("study_id")),
        "quest_id": _text(receipt.get("quest_id")),
        "idempotency_key": _text(receipt.get("idempotency_key")),
        "route_epoch": _text(receipt.get("route_epoch")),
        "current_owner": _text(receipt.get("current_owner")),
        "next_owner": _text(receipt.get("next_owner")),
        "owner_reason": _text(receipt.get("owner_reason")),
        "allowed_actions": list(receipt.get("allowed_actions") or [])
        if isinstance(receipt.get("allowed_actions"), list)
        else [],
        "source_refs": dict(_mapping(receipt.get("source_refs"))),
        "body_included": False,
    }


def _dispatch_projection_payload(receipt: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "surface": _text(receipt.get("surface")),
        "dispatch_id": _text(receipt.get("dispatch_id")),
        "study_id": _text(receipt.get("study_id")),
        "quest_id": _text(receipt.get("quest_id")),
        "action_type": _text(receipt.get("action_type")),
        "created_at": _dispatch_created_at(receipt),
        "status": _dispatch_status(receipt),
        "idempotency_key": _text(receipt.get("idempotency_key")),
        "owner_route": _owner_route_projection_payload(_mapping(receipt.get("owner_route"))),
        "why_not_applied": _text(receipt.get("why_not_applied")),
        "body_included": False,
    }


def _dispatch_id(*, receipt: Mapping[str, Any], source_path: Path, payload_sha256: str) -> str:
    for key in ("dispatch_id", "request_id", "execution_id", "action_id"):
        if value := _text(receipt.get(key)):
            return value
    return f"{source_path}::{payload_sha256}"


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


def _assert_db_not_tracked(db_path: Path) -> None:
    tracked_paths = _tracked_sqlite_refs_indexes(db_path)
    if tracked_paths:
        tracked = ", ".join(tracked_paths)
        raise RuntimeError(f"domain authority refs SQLite index must not be tracked by Git: {tracked}")


def _tracked_sqlite_refs_indexes(db_path: Path) -> tuple[str, ...]:
    resolved_db_path = Path(db_path).expanduser().resolve()
    git_root = _git_root_for_path(resolved_db_path.parent)
    if git_root is None:
        return ()
    candidates = (resolved_db_path, Path(f"{resolved_db_path}-wal"), Path(f"{resolved_db_path}-shm"))
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


def _table_count(conn: sqlite3.Connection, table: str) -> int:
    row = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()
    return int(row[0]) if row else 0


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


def _as_int(value: object) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str) and value.strip():
        try:
            return int(float(value))
        except ValueError:
            return 0
    return 0


__all__ = [
    "AUTHORITY_REF_TABLES",
    "DEFAULT_DB_FILENAME",
    "OPL_FAMILY_ADAPTER_SOURCE_TABLES",
    "SCHEMA_VERSION",
    "SQLITE_GITIGNORE_PATTERNS",
    "SURFACE_KIND",
    "domain_authority_refs_index_contract",
    "inspect_authority_refs_index",
    "quest_authority_refs_index_path",
    "record_archive_ref",
    "record_dispatch_receipt",
    "record_owner_route_receipt",
    "record_paper_progress_transition_ref",
    "record_stage_artifact_delta_ref",
    "workspace_authority_refs_index_path",
]
