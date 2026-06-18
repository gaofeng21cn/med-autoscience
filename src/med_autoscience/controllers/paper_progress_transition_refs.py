from __future__ import annotations

from collections.abc import Mapping
import hashlib
import json
from pathlib import Path
from typing import Any

from med_autoscience.controllers.domain_health_diagnostic_parts.opl_transition_readback import (
    required_opl_transition_readback_shape,
)
from med_autoscience.runtime_protocol import domain_authority_refs_index
from med_autoscience.runtime_protocol import opl_state_index_source_adapter


SCHEMA_VERSION = 1
RECEIPTS_RELATIVE_PATH = Path("artifacts/runtime/paper_progress_transition_refs/receipts.jsonl")
TRANSITION_REQUEST_PENDING = "transition_request_pending_opl_runtime_required"


def record_paper_progress_transition_ref(
    *,
    study_root: Path,
    quest_root: Path,
    idempotency_key: str,
    intent: Mapping[str, Any],
    recorded_at: str,
    db_path: Path | None = None,
    persist_authority_refs_index: bool = False,
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
    existing_receipts = read_transition_refs(study_root=resolved_study_root)
    existing_for_key = _receipt_for_idempotency_key(existing_receipts, key)
    if existing_for_key is not None:
        if _text(existing_for_key.get("intent_fingerprint")) == intent_fingerprint:
            replay = dict(existing_for_key)
            replay["receipt_status"] = "replayed_transition_request_ref"
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
            persist_authority_refs_index=persist_authority_refs_index,
        )
        return conflict

    duplicate = _receipt_for_source_fingerprint(existing_receipts, source_fingerprint)
    if duplicate is not None:
        receipt = _receipt(
            study_root=resolved_study_root,
            quest_root=resolved_quest_root,
            idempotency_key=key,
            intent=normalized_intent,
            intent_fingerprint=intent_fingerprint,
            source_fingerprint=source_fingerprint,
            receipt_status="duplicate_source_fingerprint_ref",
            recorded_at=recorded,
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
            persist_authority_refs_index=persist_authority_refs_index,
        )
        return receipt

    receipt = _receipt(
        study_root=resolved_study_root,
        quest_root=resolved_quest_root,
        idempotency_key=key,
        intent=normalized_intent,
        intent_fingerprint=intent_fingerprint,
        source_fingerprint=source_fingerprint,
        receipt_status=TRANSITION_REQUEST_PENDING,
        recorded_at=recorded,
        duplicate_of_receipt_id=None,
        fail_closed_reason=None,
        conflicting_receipt_id=None,
    )
    _append_receipt(resolved_study_root, receipt)
    _index_receipt(
        study_root=resolved_study_root,
        quest_root=resolved_quest_root,
        receipt=receipt,
        db_path=db_path,
        persist_authority_refs_index=persist_authority_refs_index,
    )
    return receipt


def transition_refs_path(study_root: Path) -> Path:
    return Path(study_root).expanduser().resolve() / RECEIPTS_RELATIVE_PATH


def read_transition_refs(*, study_root: Path) -> list[dict[str, Any]]:
    return _read_jsonl(transition_refs_path(study_root))


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
        "lane": _text(intent.get("lane")) or "paper-progress-transition",
        "intent_fingerprint": intent_fingerprint,
        "source_fingerprint": source_fingerprint,
        "transition_runtime_owner": "one-person-lab",
        "transition_request_pending": receipt_status in {
            TRANSITION_REQUEST_PENDING,
            "duplicate_source_fingerprint_ref",
        },
        "duplicate_of_receipt_id": duplicate_of_receipt_id,
        "fail_closed_reason": fail_closed_reason,
        "conflicting_receipt_id": conflicting_receipt_id,
    }
    receipt_id = _stable_id("paper-progress-transition-ref", semantic_receipt)
    semantic_receipt["receipt_id"] = receipt_id
    return {
        "surface": "paper_progress_transition_ref_receipt",
        "schema_version": SCHEMA_VERSION,
        "receipt_id": receipt_id,
        "receipt_status": receipt_status,
        "recorded_at": recorded_at,
        "study_root": str(study_root),
        "quest_root": str(quest_root),
        "refs_only": True,
        "mas_can_authorize_provider_admission": False,
        "mas_can_own_event_log_or_outbox": False,
        "mas_can_create_opl_outbox_record": False,
        "mas_can_append_opl_event_log": False,
        "mas_can_emit_opl_outbox_item": False,
        "mas_can_create_opl_event": False,
        "mas_can_create_opl_stage_run": False,
        "provider_admission_authority": False,
        "provider_admission_effect": "transition_request_pending",
        "requires_opl_transition_readback": True,
        "required_opl_transition_runtime_readback": _required_opl_transition_runtime_readback(),
        "required_opl_transactional_outbox": _required_opl_transactional_outbox(),
        "deprecated_projection_fields_authority": False,
        **semantic_receipt,
        "intent": dict(intent),
        "semantic_receipt": semantic_receipt,
    }


def _append_receipt(study_root: Path, receipt: Mapping[str, Any]) -> None:
    _append_jsonl(transition_refs_path(study_root), receipt)


def _required_opl_transition_runtime_readback() -> dict[str, Any]:
    return required_opl_transition_readback_shape()


def _required_opl_transactional_outbox() -> dict[str, Any]:
    readback_shape = required_opl_transition_readback_shape()
    return {
        "runtime_owner": _text(readback_shape.get("runtime_owner")) or "one-person-lab",
        "runtime_kind": _text(readback_shape.get("runtime_kind"))
        or "DomainProgressTransitionRuntime",
        "command_present": True,
        "event_present": True,
        "outbox_item_present": True,
        "same_transaction_event_and_outbox": True,
        "stage_run_identity_required": "stage_run_identity"
        in set(readback_shape.get("required_runtime_refs") or []),
        "mas_can_create_command_event_outbox_or_stage_run": False,
    }


def _index_receipt(
    *,
    study_root: Path,
    quest_root: Path,
    receipt: Mapping[str, Any],
    db_path: Path | None,
    persist_authority_refs_index: bool,
) -> None:
    if persist_authority_refs_index:
        domain_authority_refs_index.record_paper_progress_transition_ref(
            study_root=study_root,
            quest_root=quest_root,
            receipt=receipt,
            receipt_path=transition_refs_path(study_root),
            db_path=db_path,
            persist_sqlite=True,
        )
        return
    opl_state_index_source_adapter.emit_paper_progress_transition_source(
        study_root=study_root,
        quest_root=quest_root,
        receipt=receipt,
        receipt_path=transition_refs_path(study_root),
        db_path=db_path,
    )


def _receipt_for_idempotency_key(receipts: list[dict[str, Any]], idempotency_key: str) -> dict[str, Any] | None:
    for receipt in receipts:
        if _text(receipt.get("idempotency_key")) == idempotency_key:
            return receipt
    return None


def _receipt_for_source_fingerprint(
    receipts: list[dict[str, Any]],
    source_fingerprint: str,
) -> dict[str, Any] | None:
    for receipt in receipts:
        if _text(receipt.get("source_fingerprint")) == source_fingerprint:
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
    return _stable_id("paper-progress-transition-intent", intent)


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
    "TRANSITION_REQUEST_PENDING",
    "read_transition_refs",
    "record_paper_progress_transition_ref",
    "transition_refs_path",
]
