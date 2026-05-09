from __future__ import annotations

from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any


def launch_fields(payload: Mapping[str, Any], *, text: Callable[[object], str | None]) -> dict[str, Any]:
    return {
        "scheduled": bool(payload.get("scheduled")),
        "started": bool(payload.get("started")),
        "queued": bool(payload.get("queued")),
        "active_run_id": text(payload.get("active_run_id")),
    }


def schedule_result(
    *,
    quest_root: Path,
    status: str,
    backend_id: str,
    active_run_id: str | None,
    started: bool,
    queued: bool,
    scheduled: bool,
    reason: str,
    receipt: Mapping[str, Any],
    snapshot_payload: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "ok": True,
        "status": status,
        "source": backend_id,
        "quest_id": quest_root.name,
        "active_run_id": active_run_id,
        "scheduled": scheduled,
        "started": started,
        "queued": queued,
        "reason": reason,
        "turn_reason": reason,
        "idempotency_key": receipt.get("idempotency_key"),
        "turn_receipt": dict(receipt),
        "snapshot": dict(snapshot_payload),
    }


def turn_receipt_payload(
    *,
    quest_root: Path,
    run_id: str,
    reason: str,
    source: str,
    status: str,
    started: bool,
    queued: bool,
    idempotency_key: str,
    recorded_at: str,
    extra: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "schema_version": 1,
        "quest_id": quest_root.name,
        "run_id": run_id,
        "reason": reason,
        "source": source,
        "status": status,
        "started": started,
        "queued": queued,
        "scheduled": started or queued,
        "idempotency_key": idempotency_key,
        "recorded_at": recorded_at,
    }
    if extra:
        payload.update(dict(extra))
    return payload


def post_turn_storage_maintenance_payload(
    *,
    quest_id: str,
    run_id: str,
    source: str,
    recorded_at: str,
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "surface": "post_turn_storage_maintenance_hook",
        "status": "recorded",
        "quest_id": quest_id,
        "run_id": run_id,
        "source": source,
        "recorded_at": recorded_at,
        "maintenance_mode": "audit_hook_only",
    }


def record_post_turn_storage_maintenance_hook(
    *,
    quest_root: Path,
    quest_id: str,
    run_id: str,
    source: str,
    recorded_at: str,
    write_json: Callable[[Path, Mapping[str, Any]], None],
    append_runtime_event: Callable[..., None],
) -> None:
    payload = post_turn_storage_maintenance_payload(
        quest_id=quest_id,
        run_id=run_id,
        source=source,
        recorded_at=recorded_at,
    )
    root = quest_root / "artifacts" / "runtime" / "post_turn_storage_maintenance"
    write_json(root / "latest.json", payload)
    append_runtime_event(quest_root=quest_root, event={"event": "post_turn_storage_maintenance_hook", **payload})
