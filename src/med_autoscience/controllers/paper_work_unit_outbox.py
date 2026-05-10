from __future__ import annotations

from collections.abc import Mapping
import hashlib
import json
from pathlib import Path
from typing import Any

from med_autoscience.runtime_protocol import runtime_lifecycle_store


SCHEMA_VERSION = 1
RECEIPTS_RELATIVE_PATH = Path("artifacts/runtime/paper_work_unit_outbox/receipts.jsonl")
WORKER_STARTS_RELATIVE_PATH = Path("artifacts/runtime/paper_work_unit_outbox/worker_starts.jsonl")


def enqueue_paper_work_unit(
    *,
    study_root: Path,
    quest_root: Path,
    idempotency_key: str,
    intent: Mapping[str, Any],
    worker_start_ref: str,
    recorded_at: str,
    db_path: Path | None = None,
) -> dict[str, Any]:
    resolved_study_root = Path(study_root).expanduser().resolve()
    resolved_quest_root = Path(quest_root).expanduser().resolve()
    key = _require_text("idempotency_key", idempotency_key)
    recorded = _require_text("recorded_at", recorded_at)
    normalized_intent = _mapping(intent)
    intent_fingerprint = _intent_fingerprint(normalized_intent)
    source_fingerprint = _require_text(
        "intent.source_fingerprint",
        normalized_intent.get("source_fingerprint"),
    )
    existing_receipts = read_receipts(study_root=resolved_study_root)
    existing_for_key = _receipt_for_idempotency_key(existing_receipts, key)
    if existing_for_key is not None:
        if _text(existing_for_key.get("intent_fingerprint")) == intent_fingerprint:
            replay = dict(existing_for_key)
            replay["receipt_status"] = "replayed"
            return replay
        conflict = _receipt(
            study_root=resolved_study_root,
            quest_root=resolved_quest_root,
            idempotency_key=key,
            intent=normalized_intent,
            intent_fingerprint=intent_fingerprint,
            source_fingerprint=source_fingerprint,
            receipt_status="failed_closed",
            recorded_at=recorded,
            started_worker=False,
            worker_start_ref=None,
            duplicate_of_receipt_id=None,
            fail_closed_reason="idempotency_key_intent_conflict",
            conflicting_receipt_id=_text(existing_for_key.get("receipt_id")),
        )
        _append_receipt(resolved_study_root, conflict)
        _index_receipt(
            study_root=resolved_study_root,
            quest_root=resolved_quest_root,
            receipt=conflict,
            db_path=db_path,
        )
        return conflict

    duplicate = _started_receipt_for_source_fingerprint(existing_receipts, source_fingerprint)
    if duplicate is not None:
        receipt = _receipt(
            study_root=resolved_study_root,
            quest_root=resolved_quest_root,
            idempotency_key=key,
            intent=normalized_intent,
            intent_fingerprint=intent_fingerprint,
            source_fingerprint=source_fingerprint,
            receipt_status="duplicate_source_fingerprint",
            recorded_at=recorded,
            started_worker=False,
            worker_start_ref=_text(duplicate.get("worker_start_ref")),
            duplicate_of_receipt_id=_text(duplicate.get("receipt_id")),
            fail_closed_reason=None,
            conflicting_receipt_id=None,
        )
        _append_receipt(resolved_study_root, receipt)
        _index_receipt(
            study_root=resolved_study_root,
            quest_root=resolved_quest_root,
            receipt=receipt,
            db_path=db_path,
        )
        return receipt

    start_ref = _require_text("worker_start_ref", worker_start_ref)
    receipt = _receipt(
        study_root=resolved_study_root,
        quest_root=resolved_quest_root,
        idempotency_key=key,
        intent=normalized_intent,
        intent_fingerprint=intent_fingerprint,
        source_fingerprint=source_fingerprint,
        receipt_status="started",
        recorded_at=recorded,
        started_worker=True,
        worker_start_ref=start_ref,
        duplicate_of_receipt_id=None,
        fail_closed_reason=None,
        conflicting_receipt_id=None,
    )
    _append_receipt(resolved_study_root, receipt)
    _append_worker_start(resolved_study_root, receipt)
    _index_receipt(
        study_root=resolved_study_root,
        quest_root=resolved_quest_root,
        receipt=receipt,
        db_path=db_path,
    )
    return receipt


def receipts_path(study_root: Path) -> Path:
    return Path(study_root).expanduser().resolve() / RECEIPTS_RELATIVE_PATH


def worker_starts_path(study_root: Path) -> Path:
    return Path(study_root).expanduser().resolve() / WORKER_STARTS_RELATIVE_PATH


def read_receipts(*, study_root: Path) -> list[dict[str, Any]]:
    return _read_jsonl(receipts_path(study_root))


def worker_starts(*, study_root: Path) -> list[dict[str, Any]]:
    return _read_jsonl(worker_starts_path(study_root))


def _receipt(
    *,
    study_root: Path,
    quest_root: Path,
    idempotency_key: str,
    intent: Mapping[str, Any],
    intent_fingerprint: str,
    source_fingerprint: str,
    receipt_status: str,
    recorded_at: str,
    started_worker: bool,
    worker_start_ref: str | None,
    duplicate_of_receipt_id: str | None,
    fail_closed_reason: str | None,
    conflicting_receipt_id: str | None,
) -> dict[str, Any]:
    semantic_receipt = {
        "idempotency_key": idempotency_key,
        "study_id": _text(intent.get("study_id")),
        "quest_id": _text(intent.get("quest_id")),
        "unit_id": _text(intent.get("unit_id")),
        "action_type": _text(intent.get("action_type")),
        "lane": _text(intent.get("lane")),
        "intent_fingerprint": intent_fingerprint,
        "source_fingerprint": source_fingerprint,
        "started_worker": started_worker,
        "worker_start_ref": worker_start_ref,
        "duplicate_of_receipt_id": duplicate_of_receipt_id,
        "fail_closed_reason": fail_closed_reason,
        "conflicting_receipt_id": conflicting_receipt_id,
    }
    receipt_id = _stable_id("paper-work-unit-receipt", semantic_receipt)
    semantic_receipt["receipt_id"] = receipt_id
    return {
        "surface": "paper_work_unit_outbox_receipt",
        "schema_version": SCHEMA_VERSION,
        "receipt_id": receipt_id,
        "receipt_status": receipt_status,
        "recorded_at": recorded_at,
        "study_root": str(study_root),
        "quest_root": str(quest_root),
        **semantic_receipt,
        "intent": dict(intent),
        "semantic_receipt": semantic_receipt,
    }


def _append_receipt(study_root: Path, receipt: Mapping[str, Any]) -> None:
    _append_jsonl(receipts_path(study_root), receipt)


def _append_worker_start(study_root: Path, receipt: Mapping[str, Any]) -> None:
    _append_jsonl(
        worker_starts_path(study_root),
        {
            "surface": "paper_work_unit_worker_start",
            "schema_version": SCHEMA_VERSION,
            "receipt_id": receipt.get("receipt_id"),
            "idempotency_key": receipt.get("idempotency_key"),
            "source_fingerprint": receipt.get("source_fingerprint"),
            "worker_start_ref": receipt.get("worker_start_ref"),
            "recorded_at": receipt.get("recorded_at"),
        },
    )


def _index_receipt(
    *,
    study_root: Path,
    quest_root: Path,
    receipt: Mapping[str, Any],
    db_path: Path | None,
) -> None:
    runtime_lifecycle_store.record_paper_work_unit_receipt(
        study_root=study_root,
        quest_root=quest_root,
        receipt=receipt,
        receipt_path=receipts_path(study_root),
        db_path=db_path,
    )


def _receipt_for_idempotency_key(receipts: list[dict[str, Any]], idempotency_key: str) -> dict[str, Any] | None:
    for receipt in receipts:
        if _text(receipt.get("idempotency_key")) == idempotency_key:
            return receipt
    return None


def _started_receipt_for_source_fingerprint(
    receipts: list[dict[str, Any]],
    source_fingerprint: str,
) -> dict[str, Any] | None:
    for receipt in receipts:
        if _text(receipt.get("source_fingerprint")) != source_fingerprint:
            continue
        if receipt.get("started_worker") is True and _text(receipt.get("worker_start_ref")) is not None:
            return receipt
    return None


def _append_jsonl(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(_stable_json(payload) + "\n")


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        payload = json.loads(line)
        if isinstance(payload, dict):
            rows.append(payload)
    return rows


def _intent_fingerprint(intent: Mapping[str, Any]) -> str:
    return _stable_id("paper-work-unit-intent", intent)


def _stable_id(prefix: str, payload: Mapping[str, Any]) -> str:
    return f"{prefix}::sha256:{_sha256(_stable_json(payload))}"


def _stable_json(payload: object) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def _sha256(payload: str) -> str:
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _mapping(value: object) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError("intent must be a mapping")
    return dict(value)


def _text(value: object) -> str | None:
    text = value.strip() if isinstance(value, str) else ""
    return text or None


def _require_text(label: str, value: object) -> str:
    text = _text(value)
    if text is None:
        raise ValueError(f"{label} must be a non-empty string")
    return text


__all__ = [
    "enqueue_paper_work_unit",
    "read_receipts",
    "receipts_path",
    "worker_starts",
    "worker_starts_path",
]
