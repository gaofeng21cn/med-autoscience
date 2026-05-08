from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
import json
import sqlite3
from typing import Any

from ..runtime_lifecycle_contract import OPL_FAMILY_ADAPTER_SOURCE_TABLES

ADOPTION_SURFACE_KIND = "mas_opl_family_persistence_lifecycle_owner_route_adoption"
SOURCE_CONTRACT_REF = "contracts/opl-gateway/family-contract-adoption.json"
RUNTIME_LIFECYCLE_CONTRACT_REF = (
    "med_autoscience.runtime_protocol.runtime_lifecycle_contract.runtime_lifecycle_contract"
)

FORBIDDEN_OPL_AUTHORITY_SURFACES = (
    "publication_eval/latest.json",
    "controller_decisions/latest.json",
    "AI reviewer workflow",
    "paper/manuscript/current_package",
    "current_package.zip",
)


def build_opl_family_adoption_surface(
    *,
    connect: Any,
    ensure_schema: Any,
    inspect_lifecycle_store: Any,
    workspace_lifecycle_store_path: Any,
    workspace_root: Path,
    db_path: Path | None = None,
) -> dict[str, Any]:
    resolved_workspace_root = Path(workspace_root).expanduser().resolve()
    resolved_db_path = Path(db_path or workspace_lifecycle_store_path(resolved_workspace_root)).expanduser().resolve()
    inspection = inspect_lifecycle_store(resolved_db_path)
    payload = _empty_payload(inspection=inspection)
    if resolved_db_path.exists():
        with connect(resolved_db_path) as conn:
            ensure_schema(conn)
            payload = _payload_from_sidecar(conn, inspection=inspection)
    return {
        "surface_kind": ADOPTION_SURFACE_KIND,
        "schema_version": 1,
        "workspace_root": str(resolved_workspace_root),
        "refs": {
            "source_contract": SOURCE_CONTRACT_REF,
            "runtime_lifecycle_contract": RUNTIME_LIFECYCLE_CONTRACT_REF,
            "sqlite_sidecar": {
                "surface_kind": "runtime_lifecycle_sqlite_index",
                "workspace_relative_path": "artifacts/runtime/runtime_lifecycle.sqlite",
                "db_path": str(resolved_db_path),
                "status": inspection.get("status") or "missing",
            },
            "authority_boundary": {
                "domain_truth_owner": "MedAutoScience",
                "opl_role": "family-level discovery and indexing only",
                "allowed_operation": "refs_payload_projection_only",
                "forbidden_opl_authority_surfaces": list(FORBIDDEN_OPL_AUTHORITY_SURFACES),
            },
        },
        "payload": payload,
    }


def build_product_entry_adoption_projection(
    *,
    workspace_root: Path,
    db_path: Path | None = None,
) -> dict[str, Any]:
    resolved_workspace_root = Path(workspace_root).expanduser().resolve()
    resolved_db_path = Path(db_path or (resolved_workspace_root / "artifacts" / "runtime" / "runtime_lifecycle.sqlite")).resolve()
    return {
        "surface_kind": ADOPTION_SURFACE_KIND,
        "schema_version": 1,
        "workspace_root": str(resolved_workspace_root),
        "refs": {
            "source_contract": SOURCE_CONTRACT_REF,
            "runtime_lifecycle_contract": RUNTIME_LIFECYCLE_CONTRACT_REF,
            "sqlite_sidecar": {
                "surface_kind": "runtime_lifecycle_sqlite_index",
                "workspace_relative_path": "artifacts/runtime/runtime_lifecycle.sqlite",
                "db_path": str(resolved_db_path),
            },
            "authority_boundary": {
                "domain_truth_owner": "MedAutoScience",
                "opl_role": "family-level discovery and indexing only",
                "allowed_operation": "refs_payload_projection_only",
                "forbidden_opl_authority_surfaces": list(FORBIDDEN_OPL_AUTHORITY_SURFACES),
            },
        },
        "payload": {
            "persistence": {
                "maps_to_opl_contract": "opl_family_persistence_contract.v1",
                "sqlite_sidecar_ref": "/refs/sqlite_sidecar",
                "source_tables": list(OPL_FAMILY_ADAPTER_SOURCE_TABLES),
            },
            "lifecycle": {
                "maps_to_opl_contract": "opl_family_lifecycle_contract.v1",
                "source_tables": [
                    "runtime_snapshots",
                    "snapshot_file_refs",
                    "dispatch_receipts",
                    "archive_refs",
                    "report_index",
                ],
            },
            "owner_route": {
                "maps_to_opl_contract": "opl_family_owner_route_contract.v1",
                "source_table": "owner_route_receipts",
                "route_ticket_shape": ["idempotency_key", "route_epoch", "current_owner", "next_owner", "allowed_actions"],
            },
            "authority_boundary": {
                "publication_eval_owner": "MedAutoScience",
                "ai_reviewer_owner": "MedAutoScience",
                "paper_package_owner": "MedAutoScience",
                "opl_authority": "discovery_and_indexing_only",
            },
        },
    }


def _payload_from_sidecar(conn: sqlite3.Connection, *, inspection: Mapping[str, Any]) -> dict[str, Any]:
    owner_route = _latest_owner_route(conn)
    return {
        "persistence": {
            "maps_to_opl_contract": "opl_family_persistence_contract.v1",
            "sqlite_tables": {
                table: int(_mapping(inspection.get("tables")).get(table) or 0)
                for table in OPL_FAMILY_ADAPTER_SOURCE_TABLES
            },
            "lineage_nodes": _payload_rows(conn, "lineage_nodes", limit=20),
            "workspace_allocations": _payload_rows(conn, "workspace_allocations", limit=20),
        },
        "lifecycle": {
            "maps_to_opl_contract": "opl_family_lifecycle_contract.v1",
            "runtime_snapshots": _payload_rows(conn, "runtime_snapshots", limit=20),
            "dispatch_receipts": _dispatch_receipt_rows(conn),
            "archive_refs": _payload_rows(conn, "archive_refs", limit=20),
            "report_index": _report_index_rows(conn),
        },
        "owner_route": {
            "maps_to_opl_contract": "opl_family_owner_route_contract.v1",
            "source_table": "owner_route_receipts",
            "current_ticket": owner_route,
            "allowed_actions": list(owner_route.get("allowed_actions") or []),
        },
        "surface_refs": _surface_ref_rows(conn),
        "authority_boundary": {
            "publication_eval_owner": "MedAutoScience",
            "ai_reviewer_owner": "MedAutoScience",
            "paper_package_owner": "MedAutoScience",
            "opl_authority": "discovery_and_indexing_only",
        },
    }


def _empty_payload(*, inspection: Mapping[str, Any]) -> dict[str, Any]:
    table_counts = {
        table: int(_mapping(inspection.get("tables")).get(table) or 0)
        for table in OPL_FAMILY_ADAPTER_SOURCE_TABLES
    }
    return {
        "persistence": {
            "maps_to_opl_contract": "opl_family_persistence_contract.v1",
            "sqlite_tables": table_counts,
            "lineage_nodes": [],
            "workspace_allocations": [],
        },
        "lifecycle": {
            "maps_to_opl_contract": "opl_family_lifecycle_contract.v1",
            "runtime_snapshots": [],
            "dispatch_receipts": [],
            "archive_refs": [],
            "report_index": [],
        },
        "owner_route": {
            "maps_to_opl_contract": "opl_family_owner_route_contract.v1",
            "source_table": "owner_route_receipts",
            "current_ticket": {},
            "allowed_actions": [],
        },
        "surface_refs": [],
        "authority_boundary": {
            "publication_eval_owner": "MedAutoScience",
            "ai_reviewer_owner": "MedAutoScience",
            "paper_package_owner": "MedAutoScience",
            "opl_authority": "discovery_and_indexing_only",
        },
    }


def _latest_owner_route(conn: sqlite3.Connection) -> dict[str, Any]:
    row = conn.execute(
        """
        SELECT idempotency_key, route_epoch, current_owner, next_owner,
               owner_reason, allowed_actions_json, source_refs_json, source_path, payload_json
        FROM owner_route_receipts
        ORDER BY recorded_at DESC, rowid DESC
        LIMIT 1
        """
    ).fetchone()
    if row is None:
        return {}
    payload = _load_json(row[8])
    return {
        "idempotency_key": row[0],
        "route_epoch": row[1],
        "current_owner": row[2],
        "next_owner": row[3],
        "owner_reason": row[4],
        "allowed_actions": _load_json(row[5], default=[]),
        "source_refs": _load_json(row[6]),
        "source_path": row[7],
        "payload": payload,
    }


def _dispatch_receipt_rows(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT dispatch_id, study_id, quest_id, created_at, status, idempotency_key, source_path, payload_json
        FROM dispatch_receipts
        ORDER BY recorded_at DESC, rowid DESC
        LIMIT 20
        """
    ).fetchall()
    return [
        {
            "dispatch_id": row[0],
            "study_id": row[1],
            "quest_id": row[2],
            "created_at": row[3],
            "status": row[4],
            "idempotency_key": row[5],
            "source_path": row[6],
            "payload": _load_json(row[7]),
        }
        for row in rows
    ]


def _surface_ref_rows(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT object_scope, ref_key, surface, study_id, quest_id, target_path,
               source_path, target_sha256, observed_at
        FROM surface_refs
        ORDER BY recorded_at DESC, rowid DESC
        LIMIT 50
        """
    ).fetchall()
    return [
        {
            "object_scope": row[0],
            "ref_key": row[1],
            "surface": row[2],
            "study_id": row[3],
            "quest_id": row[4],
            "target_path": row[5],
            "source_path": row[6],
            "target_sha256": row[7],
            "observed_at": row[8],
        }
        for row in rows
    ]


def _report_index_rows(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT object_root, object_scope, report_group, timestamp, status,
               json_path, latest_json_path
        FROM report_index
        ORDER BY recorded_at DESC, rowid DESC
        LIMIT 20
        """
    ).fetchall()
    return [
        {
            "object_root": row[0],
            "object_scope": row[1],
            "report_group": row[2],
            "timestamp": row[3],
            "status": row[4],
            "json_path": row[5],
            "latest_json_path": row[6],
        }
        for row in rows
    ]


def _payload_rows(conn: sqlite3.Connection, table: str, *, limit: int) -> list[dict[str, Any]]:
    rows = conn.execute(
        f"SELECT payload_json FROM {table} ORDER BY recorded_at DESC, rowid DESC LIMIT ?",
        (limit,),
    ).fetchall()
    return [_load_json(row[0]) for row in rows]


def _load_json(value: object, default: object | None = None) -> Any:
    if default is None:
        default = {}
    if not isinstance(value, str) or not value:
        return default
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return default


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


__all__ = [
    "ADOPTION_SURFACE_KIND",
    "build_opl_family_adoption_surface",
    "build_product_entry_adoption_projection",
]
