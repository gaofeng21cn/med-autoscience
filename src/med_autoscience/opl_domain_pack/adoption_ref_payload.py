from __future__ import annotations

from collections.abc import Mapping
import json
import sqlite3
from typing import Any

from med_autoscience.runtime_protocol.domain_authority_refs_index import OPL_FAMILY_ADAPTER_SOURCE_TABLES


def payload_from_authority_refs(conn: sqlite3.Connection, *, inspection: Mapping[str, Any]) -> dict[str, Any]:
    owner_route = _latest_owner_route(conn)
    return {
        "persistence": {
            "maps_to_opl_contract": "opl_family_persistence_contract.v1",
            "sqlite_tables": {
                table: int(_mapping(inspection.get("tables")).get(table) or 0)
                for table in OPL_FAMILY_ADAPTER_SOURCE_TABLES
            },
        },
        "lifecycle": {
            "maps_to_opl_contract": "opl_family_lifecycle_contract.v1",
            "dispatch_receipts": _dispatch_receipt_rows(conn),
            "archive_refs": _payload_rows(conn, "archive_refs", limit=20),
        },
        "owner_route": {
            "maps_to_opl_contract": "opl_family_owner_route_contract.v1",
            "source_table": "owner_route_receipts",
            "current_ticket": owner_route,
            "allowed_actions": list(owner_route.get("allowed_actions") or []),
        },
        "authority_boundary": {
            "publication_eval_owner": "MedAutoScience",
            "ai_reviewer_owner": "MedAutoScience",
            "paper_package_owner": "MedAutoScience",
            "opl_authority": "discovery_and_indexing_only",
        },
    }


def empty_payload(*, inspection: Mapping[str, Any]) -> dict[str, Any]:
    table_counts = {
        table: int(_mapping(inspection.get("tables")).get(table) or 0)
        for table in OPL_FAMILY_ADAPTER_SOURCE_TABLES
    }
    return {
        "persistence": {
            "maps_to_opl_contract": "opl_family_persistence_contract.v1",
            "sqlite_tables": table_counts,
        },
        "lifecycle": {
            "maps_to_opl_contract": "opl_family_lifecycle_contract.v1",
            "dispatch_receipts": [],
            "archive_refs": [],
        },
        "owner_route": {
            "maps_to_opl_contract": "opl_family_owner_route_contract.v1",
            "source_table": "owner_route_receipts",
            "current_ticket": {},
            "allowed_actions": [],
        },
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


__all__ = ["empty_payload", "payload_from_authority_refs"]
