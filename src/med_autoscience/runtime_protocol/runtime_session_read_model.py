from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime
import json
from pathlib import Path
import sqlite3
from typing import Any

from . import runtime_lifecycle_store


SURFACE_KIND = "runtime_session_read_model"


def build_runtime_session_read_model(
    *,
    study_runtime_status: Mapping[str, Any] | None = None,
    study_runtime_status_path: Path | None = None,
    study_root: Path | None = None,
    quest_root: Path | None = None,
    db_path: Path | None = None,
    historical_fixture: Mapping[str, Any] | None = None,
    historical_fixture_path: Path | None = None,
    generated_at: str | None = None,
    freshness_ttl_seconds: int | None = None,
) -> dict[str, Any]:
    generated = _text(generated_at) or _utc_now()
    source = _resolve_source(
        study_runtime_status=study_runtime_status,
        study_runtime_status_path=study_runtime_status_path,
        study_root=study_root,
        quest_root=quest_root,
        db_path=db_path,
        historical_fixture=historical_fixture,
        historical_fixture_path=historical_fixture_path,
    )
    session = _session_from_source(
        source=source,
        generated_at=generated,
        freshness_ttl_seconds=freshness_ttl_seconds,
    )
    return {
        "surface_kind": SURFACE_KIND,
        "schema_version": runtime_lifecycle_store.SCHEMA_VERSION,
        "read_only": True,
        "authority": "projection_only",
        "runtime_session": session,
    }


def build_run_session_projection(**kwargs: Any) -> dict[str, Any]:
    projection = build_runtime_session_read_model(**kwargs)
    result = dict(projection)
    result["run_session_projection"] = dict(projection["runtime_session"])
    return result


def _resolve_source(
    *,
    study_runtime_status: Mapping[str, Any] | None,
    study_runtime_status_path: Path | None,
    study_root: Path | None,
    quest_root: Path | None,
    db_path: Path | None,
    historical_fixture: Mapping[str, Any] | None,
    historical_fixture_path: Path | None,
) -> dict[str, Any]:
    status_source = _study_runtime_status_source(
        study_runtime_status=study_runtime_status,
        study_runtime_status_path=study_runtime_status_path,
    )
    if status_source is not None:
        return status_source

    lifecycle_source = _runtime_lifecycle_event_source(quest_root=quest_root, db_path=db_path)
    if lifecycle_source is not None:
        return lifecycle_source

    receipt_source = _owner_route_receipt_source(study_root=study_root, quest_root=quest_root, db_path=db_path)
    if receipt_source is not None:
        return receipt_source

    legacy_source = _historical_fixture_source(
        historical_fixture=historical_fixture,
        historical_fixture_path=historical_fixture_path,
    )
    if legacy_source is not None:
        return legacy_source

    resolved_db_path = _resolve_lifecycle_db_path(quest_root=quest_root, db_path=db_path)
    evidence_refs = [{"source": "runtime_lifecycle_store", "path": str(resolved_db_path)}] if resolved_db_path else []
    return {
        "source_priority": "none",
        "payload": {},
        "evidence_refs": evidence_refs,
    }


def _study_runtime_status_source(
    *,
    study_runtime_status: Mapping[str, Any] | None,
    study_runtime_status_path: Path | None,
) -> dict[str, Any] | None:
    if study_runtime_status is not None:
        payload = dict(study_runtime_status)
        if payload:
            return {
                "source_priority": "study_runtime_status",
                "payload": payload,
                "evidence_refs": [{"source": "study_runtime_status"}],
            }
    if study_runtime_status_path is None:
        return None
    path = Path(study_runtime_status_path).expanduser().resolve()
    if not path.exists():
        return None
    payload = _read_json_mapping(path)
    if not payload:
        return None
    return {
        "source_priority": "study_runtime_status",
        "payload": payload,
        "evidence_refs": [{"source": "study_runtime_status", "path": str(path)}],
    }


def _runtime_lifecycle_event_source(*, quest_root: Path | None, db_path: Path | None) -> dict[str, Any] | None:
    resolved_db_path = _resolve_lifecycle_db_path(quest_root=quest_root, db_path=db_path)
    if resolved_db_path is None or not resolved_db_path.exists():
        return None
    resolved_quest_root = Path(quest_root).expanduser().resolve() if quest_root is not None else None
    try:
        with _connect_readonly(resolved_db_path) as conn:
            if not _table_exists(conn, "runtime_events"):
                return None
            if resolved_quest_root is not None:
                row = conn.execute(
                    """
                    SELECT quest_root, event_id, quest_id, study_id, emitted_at, active_run_id,
                           summary_ref, artifact_path, latest_path, cursor, payload_json, recorded_at
                    FROM runtime_events
                    WHERE quest_root = ?
                    ORDER BY emitted_at DESC, recorded_at DESC
                    LIMIT 1
                    """,
                    (str(resolved_quest_root),),
                ).fetchone()
            else:
                row = conn.execute(
                    """
                    SELECT quest_root, event_id, quest_id, study_id, emitted_at, active_run_id,
                           summary_ref, artifact_path, latest_path, cursor, payload_json, recorded_at
                    FROM runtime_events
                    ORDER BY emitted_at DESC, recorded_at DESC
                    LIMIT 1
                    """
                ).fetchone()
    except sqlite3.DatabaseError:
        return None
    if row is None:
        return None
    payload = _read_row_payload(row)
    payload.setdefault("study_id", _text(row["study_id"]))
    payload.setdefault("quest_id", _text(row["quest_id"]))
    payload.setdefault("emitted_at", _text(row["emitted_at"]))
    payload["last_event_cursor"] = _text(row["cursor"])
    evidence_refs = [
        {"source": "runtime_lifecycle_store", "path": str(resolved_db_path)},
        {"source": "runtime_event_artifact", "path": _text(row["artifact_path"])},
        {"source": "runtime_event_latest", "path": _text(row["latest_path"])},
        {"source": "runtime_event_summary", "path": _text(row["summary_ref"])},
    ]
    return {
        "source_priority": "runtime_lifecycle_store",
        "payload": payload,
        "evidence_refs": [ref for ref in evidence_refs if ref.get("path")],
    }


def _owner_route_receipt_source(
    *,
    study_root: Path | None,
    quest_root: Path | None,
    db_path: Path | None,
) -> dict[str, Any] | None:
    resolved_db_path = _resolve_lifecycle_db_path(quest_root=quest_root, db_path=db_path)
    if resolved_db_path is None or not resolved_db_path.exists():
        return None
    resolved_study_root = Path(study_root).expanduser().resolve() if study_root is not None else None
    resolved_quest_root = Path(quest_root).expanduser().resolve() if quest_root is not None else None
    try:
        with _connect_readonly(resolved_db_path) as conn:
            owner_row = _latest_owner_receipt_row(conn, study_root=resolved_study_root)
            dispatch_row = _latest_dispatch_receipt_row(conn, quest_root=resolved_quest_root)
    except sqlite3.DatabaseError:
        return None
    if owner_row is None and dispatch_row is None:
        return None
    owner_payload = _read_row_payload(owner_row) if owner_row is not None else {}
    dispatch_payload = _read_row_payload(dispatch_row) if dispatch_row is not None else {}
    payload = {
        "owner_receipt": owner_payload,
        "dispatch_receipt": dispatch_payload,
        "study_id": _first_text(
            dispatch_payload.get("study_id"),
            owner_payload.get("study_id"),
            dispatch_row["study_id"] if dispatch_row is not None else None,
            owner_row["study_id"] if owner_row is not None else None,
        ),
        "quest_id": _first_text(
            dispatch_payload.get("quest_id"),
            owner_payload.get("quest_id"),
            dispatch_row["quest_id"] if dispatch_row is not None else None,
            owner_row["quest_id"] if owner_row is not None else None,
        ),
        "worker_state": _first_text(
            dispatch_payload.get("status"),
            dispatch_row["status"] if dispatch_row is not None else None,
            owner_payload.get("next_owner"),
            owner_row["next_owner"] if owner_row is not None else None,
        ),
        "last_seen_at": _latest_timestamp(
            _text(dispatch_payload.get("created_at")),
            _text(dispatch_row["created_at"] if dispatch_row is not None else None),
            _text(dispatch_row["recorded_at"] if dispatch_row is not None else None),
            _text(owner_row["recorded_at"] if owner_row is not None else None),
            _text(owner_payload.get("route_epoch")),
        ),
    }
    evidence_refs: list[dict[str, str]] = []
    if owner_row is not None and _text(owner_row["source_path"]):
        evidence_refs.append({"source": "owner_route_receipts", "path": _text(owner_row["source_path"])})
    if dispatch_row is not None and _text(dispatch_row["source_path"]):
        evidence_refs.append({"source": "dispatch_receipts", "path": _text(dispatch_row["source_path"])})
    evidence_refs.append({"source": "runtime_lifecycle_store", "path": str(resolved_db_path)})
    return {
        "source_priority": "owner_route_receipts",
        "payload": payload,
        "evidence_refs": evidence_refs,
    }


def _latest_owner_receipt_row(conn: sqlite3.Connection, *, study_root: Path | None) -> sqlite3.Row | None:
    if not _table_exists(conn, "owner_route_receipts"):
        return None
    if study_root is not None:
        return conn.execute(
            """
            SELECT study_root, study_id, quest_id, idempotency_key, route_epoch,
                   current_owner, next_owner, owner_reason, source_path,
                   payload_json, recorded_at
            FROM owner_route_receipts
            WHERE study_root = ?
            ORDER BY recorded_at DESC, route_epoch DESC
            LIMIT 1
            """,
            (str(study_root),),
        ).fetchone()
    return conn.execute(
        """
        SELECT study_root, study_id, quest_id, idempotency_key, route_epoch,
               current_owner, next_owner, owner_reason, source_path,
               payload_json, recorded_at
        FROM owner_route_receipts
        ORDER BY recorded_at DESC, route_epoch DESC
        LIMIT 1
        """
    ).fetchone()


def _latest_dispatch_receipt_row(conn: sqlite3.Connection, *, quest_root: Path | None) -> sqlite3.Row | None:
    if not _table_exists(conn, "dispatch_receipts"):
        return None
    if quest_root is not None:
        return conn.execute(
            """
            SELECT quest_root, dispatch_id, study_id, quest_id, action_type,
                   created_at, status, idempotency_key, owner_route_json,
                   source_path, payload_json, recorded_at
            FROM dispatch_receipts
            WHERE quest_root = ?
            ORDER BY created_at DESC, recorded_at DESC
            LIMIT 1
            """,
            (str(quest_root),),
        ).fetchone()
    return conn.execute(
        """
        SELECT quest_root, dispatch_id, study_id, quest_id, action_type,
               created_at, status, idempotency_key, owner_route_json,
               source_path, payload_json, recorded_at
        FROM dispatch_receipts
        ORDER BY created_at DESC, recorded_at DESC
        LIMIT 1
        """
    ).fetchone()


def _historical_fixture_source(
    *,
    historical_fixture: Mapping[str, Any] | None,
    historical_fixture_path: Path | None,
) -> dict[str, Any] | None:
    if historical_fixture is not None:
        payload = dict(historical_fixture)
        if payload:
            return {
                "source_priority": "historical_fixture_ref",
                "payload": payload,
                "evidence_refs": [{"source": "historical_fixture_ref"}],
            }
    if historical_fixture_path is None:
        return None
    path = Path(historical_fixture_path).expanduser().resolve()
    if not path.exists():
        return None
    payload = _read_json_mapping(path)
    if not payload:
        return None
    return {
        "source_priority": "historical_fixture_ref",
        "payload": payload,
        "evidence_refs": [{"source": "historical_fixture_ref", "path": str(path)}],
    }


def _session_from_source(
    *,
    source: Mapping[str, Any],
    generated_at: str,
    freshness_ttl_seconds: int | None,
) -> dict[str, Any]:
    source_priority = _text(source.get("source_priority")) or "none"
    payload = _mapping(source.get("payload"))
    event_payload = _event_status_payload(payload)
    facts_payload = event_payload or payload
    worker_running = _worker_running(source_priority=source_priority, payload=facts_payload)
    runtime_liveness_status = _runtime_liveness_status(source_priority=source_priority, payload=facts_payload)
    observed_run_id = _observed_run_id(facts_payload)
    strict_live_run_id = (
        observed_run_id
        if runtime_liveness_status == "live" and worker_running is True and observed_run_id is not None
        else None
    )
    last_known_run_id = None if strict_live_run_id is not None else _first_text(observed_run_id, facts_payload.get("last_known_run_id"))
    last_seen_at = _last_seen_at(source_priority=source_priority, payload=facts_payload, event_payload=payload)
    freshness_age_seconds = _age_seconds(generated_at=generated_at, observed_at=last_seen_at)
    return {
        "study_id": _study_id(payload=facts_payload, event_payload=payload),
        "quest_id": _quest_id(payload=facts_payload, event_payload=payload),
        "active_run_id": strict_live_run_id,
        "last_known_run_id": last_known_run_id,
        "worker_state": _worker_state(source_priority=source_priority, payload=facts_payload),
        "worker_running": worker_running,
        "runtime_liveness_status": runtime_liveness_status,
        "started_at": _started_at(facts_payload),
        "last_seen_at": last_seen_at,
        "last_event_cursor": _first_text(facts_payload.get("last_event_cursor"), payload.get("last_event_cursor")),
        "last_stdout_ref": _last_stdout_ref(facts_payload),
        "freshness_state": _freshness_state(age_seconds=freshness_age_seconds, ttl_seconds=freshness_ttl_seconds),
        "freshness_age_seconds": freshness_age_seconds,
        "evidence_refs": list(source.get("evidence_refs") if isinstance(source.get("evidence_refs"), list) else []),
        "source_priority": source_priority,
        "generated_at": generated_at,
    }


def _event_status_payload(payload: Mapping[str, Any]) -> Mapping[str, Any]:
    status_snapshot = _mapping(payload.get("status_snapshot"))
    if status_snapshot:
        return status_snapshot
    outer_loop_input = _mapping(payload.get("outer_loop_input"))
    return outer_loop_input


def _study_id(*, payload: Mapping[str, Any], event_payload: Mapping[str, Any]) -> str | None:
    return _first_text(
        payload.get("study_id"),
        _mapping(payload.get("runtime_liveness_audit")).get("study_id"),
        _mapping(payload.get("runtime_audit")).get("study_id"),
        event_payload.get("study_id"),
        _mapping(event_payload.get("owner_receipt")).get("study_id"),
        _mapping(event_payload.get("dispatch_receipt")).get("study_id"),
    )


def _quest_id(*, payload: Mapping[str, Any], event_payload: Mapping[str, Any]) -> str | None:
    return _first_text(
        payload.get("quest_id"),
        _mapping(payload.get("runtime_liveness_audit")).get("quest_id"),
        _mapping(payload.get("runtime_audit")).get("quest_id"),
        event_payload.get("quest_id"),
        _mapping(event_payload.get("owner_receipt")).get("quest_id"),
        _mapping(event_payload.get("dispatch_receipt")).get("quest_id"),
    )


def _runtime_liveness_status(*, source_priority: str, payload: Mapping[str, Any]) -> str:
    if source_priority == "owner_route_receipts":
        return "unknown"
    liveness = _mapping(payload.get("runtime_liveness_audit"))
    runtime_audit = _runtime_audit(payload)
    return _first_text(
        payload.get("runtime_liveness_status"),
        liveness.get("status"),
        runtime_audit.get("status"),
    ) or "unknown"


def _worker_running(*, source_priority: str, payload: Mapping[str, Any]) -> bool | None:
    if source_priority in {"owner_route_receipts", "historical_fixture_ref", "none"}:
        return None
    liveness = _mapping(payload.get("runtime_liveness_audit"))
    runtime_audit = _runtime_audit(payload)
    for value in (
        runtime_audit.get("worker_running"),
        liveness.get("worker_running"),
        payload.get("worker_running"),
        _mapping(payload.get("mds_worker_activity")).get("worker_running"),
    ):
        if isinstance(value, bool):
            return value
    return None


def _worker_state(*, source_priority: str, payload: Mapping[str, Any]) -> str | None:
    if source_priority == "owner_route_receipts":
        return _first_text(payload.get("worker_state"), payload.get("status"))
    runtime_audit = _runtime_audit(payload)
    liveness = _mapping(payload.get("runtime_liveness_audit"))
    worker_liveness_state = _mapping(payload.get("worker_liveness_state"))
    runtime_worker_liveness_state = _mapping(runtime_audit.get("worker_liveness_state"))
    return _first_text(
        payload.get("worker_state"),
        runtime_audit.get("worker_state"),
        runtime_worker_liveness_state.get("state"),
        liveness.get("worker_state"),
        worker_liveness_state.get("state"),
        _mapping(payload.get("mds_worker_activity")).get("activity_state"),
        payload.get("status") if source_priority == "historical_fixture_ref" else None,
        "running" if _worker_running(source_priority=source_priority, payload=payload) is True else None,
    )


def _observed_run_id(payload: Mapping[str, Any]) -> str | None:
    liveness = _mapping(payload.get("runtime_liveness_audit"))
    runtime_audit = _runtime_audit(payload)
    return _first_text(
        payload.get("active_run_id"),
        liveness.get("active_run_id"),
        runtime_audit.get("active_run_id"),
        _mapping(payload.get("mds_worker_activity")).get("active_run_id"),
        payload.get("last_known_run_id"),
    )


def _started_at(payload: Mapping[str, Any]) -> str | None:
    runtime_audit = _runtime_audit(payload)
    liveness = _mapping(payload.get("runtime_liveness_audit"))
    return _first_text(
        payload.get("started_at"),
        runtime_audit.get("started_at"),
        liveness.get("started_at"),
        payload.get("run_started_at"),
        runtime_audit.get("run_started_at"),
    )


def _last_seen_at(
    *,
    source_priority: str,
    payload: Mapping[str, Any],
    event_payload: Mapping[str, Any],
) -> str | None:
    runtime_audit = _runtime_audit(payload)
    liveness = _mapping(payload.get("runtime_liveness_audit"))
    return _first_text(
        payload.get("last_seen_at"),
        runtime_audit.get("last_seen_at"),
        liveness.get("last_seen_at"),
        payload.get("observed_at"),
        runtime_audit.get("observed_at"),
        liveness.get("observed_at"),
        payload.get("updated_at"),
        payload.get("recorded_at"),
        event_payload.get("last_seen_at"),
        event_payload.get("emitted_at") if source_priority == "runtime_lifecycle_store" else None,
    )


def _last_stdout_ref(payload: Mapping[str, Any]) -> str | None:
    runtime_audit = _runtime_audit(payload)
    return _first_text(
        payload.get("last_stdout_ref"),
        payload.get("stdout_ref"),
        payload.get("stdout_path"),
        runtime_audit.get("last_stdout_ref"),
        runtime_audit.get("stdout_ref"),
        runtime_audit.get("stdout_path"),
        runtime_audit.get("active_stdout_path"),
    )


def _runtime_audit(payload: Mapping[str, Any]) -> Mapping[str, Any]:
    explicit = _mapping(payload.get("runtime_audit"))
    if explicit:
        return explicit
    liveness = _mapping(payload.get("runtime_liveness_audit"))
    return _mapping(liveness.get("runtime_audit"))


def _resolve_lifecycle_db_path(*, quest_root: Path | None, db_path: Path | None) -> Path | None:
    if db_path is not None:
        return Path(db_path).expanduser().resolve()
    if quest_root is not None:
        return runtime_lifecycle_store.quest_lifecycle_store_path(Path(quest_root))
    return None


def _connect_readonly(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(f"file:{Path(db_path).as_posix()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    return (
        conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
            (table,),
        ).fetchone()
        is not None
    )


def _read_row_payload(row: sqlite3.Row | None) -> dict[str, Any]:
    if row is None:
        return {}
    try:
        payload = json.loads(row["payload_json"])
    except (json.JSONDecodeError, KeyError, TypeError):
        return {}
    return dict(payload) if isinstance(payload, Mapping) else {}


def _read_json_mapping(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return dict(payload) if isinstance(payload, Mapping) else {}


def _latest_timestamp(*values: str) -> str | None:
    timestamp_values = [value for value in values if value]
    if not timestamp_values:
        return None
    parsed = [(parsed_value, value) for value in timestamp_values if (parsed_value := _parse_timestamp(value)) is not None]
    if parsed:
        return max(parsed, key=lambda item: item[0])[1]
    return timestamp_values[0]


def _age_seconds(*, generated_at: str, observed_at: str | None) -> int | None:
    generated = _parse_timestamp(generated_at)
    observed = _parse_timestamp(observed_at)
    if generated is None or observed is None:
        return None
    return max(int((generated - observed).total_seconds()), 0)


def _freshness_state(*, age_seconds: int | None, ttl_seconds: int | None) -> str:
    if age_seconds is None:
        return "unknown"
    if ttl_seconds is None:
        return "measured"
    return "fresh" if age_seconds <= ttl_seconds else "stale"


def _parse_timestamp(value: object) -> datetime | None:
    text = _text(value)
    if not text:
        return None
    normalized = f"{text[:-1]}+00:00" if text.endswith("Z") else text
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _first_text(*values: object) -> str | None:
    for value in values:
        text = _text(value)
        if text:
            return text
    return None


def _text(value: object) -> str:
    return value.strip() if isinstance(value, str) else ""


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


__all__ = [
    "SURFACE_KIND",
    "build_run_session_projection",
    "build_runtime_session_read_model",
]
