from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Mapping, Sequence
from typing import Any


def build_provider_hosted_guarded_apply_receipt_from_proof(
    *,
    proof: Mapping[str, Any],
    schema_version: int,
    surface: str,
    provider_attempt_id: str,
    idempotency_key: str,
    target_studies: Sequence[str],
) -> dict[str, Any]:
    guarded_receipts = [
        dict(_mapping(receipt))
        for receipt in proof.get("guarded_apply_receipts", [])
        if isinstance(receipt, Mapping)
    ]
    typed_blockers = [
        dict(_mapping(receipt.get("typed_blocker")))
        for receipt in guarded_receipts
        if _mapping(receipt.get("typed_blocker"))
    ]
    accepted_receipts = [
        receipt
        for receipt in guarded_receipts
        if _text(receipt.get("apply_result")) != "typed_blocker"
    ]
    memory_proof = _mapping(proof.get("publication_route_memory_final_proof"))
    status = "applied" if accepted_receipts and not typed_blockers else "typed_blocker"
    source_fingerprint = _fingerprint(
        {
            "provider_attempt_id": provider_attempt_id,
            "idempotency_key": idempotency_key,
            "target_studies": list(target_studies),
            "guarded_apply_receipts": guarded_receipts,
            "publication_route_memory_final_proof": memory_proof,
        }
    )
    return {
        "surface": surface,
        "schema_version": schema_version,
        "status": status,
        "target_studies": list(target_studies),
        "provider_attempt": {
            "attempt_id": _text(provider_attempt_id),
            "attempt_owner": "one-person-lab",
            "provider_attempt_is_truth": False,
            "provider_attempt_wrote_workspace": False,
        },
        "idempotency_key": _text(idempotency_key),
        "source_fingerprint": source_fingerprint,
        "guarded_apply_status": proof.get("guarded_apply_status"),
        "guarded_apply_receipts": guarded_receipts,
        "typed_blockers": typed_blockers,
        "publication_route_memory_final_proof": dict(memory_proof),
        "forbidden_write_guard": dict(_mapping(proof.get("forbidden_write_guard"))),
        "source_refs": _source_refs(guarded_receipts=guarded_receipts, memory_proof=memory_proof),
        "summary": {
            **dict(_mapping(proof.get("summary"))),
            "status": status,
            "provider_attempt_wrote_workspace": False,
            "writes_performed_by_this_receipt": False,
            "receipt_wrote_forbidden_surfaces": False,
        },
        "authority_boundary": dict(_mapping(proof.get("authority_boundary"))),
        "source_guarded_apply_proof_summary": {
            "surface": proof.get("surface"),
            "schema_version": proof.get("schema_version"),
            "mode": proof.get("mode"),
            "guarded_apply_status": proof.get("guarded_apply_status"),
            "summary": dict(_mapping(proof.get("summary"))),
        },
    }


def _source_refs(
    *,
    guarded_receipts: Sequence[Mapping[str, Any]],
    memory_proof: Mapping[str, Any],
) -> list[str]:
    return _dedupe_text(
        [
            *[ref for receipt in guarded_receipts for ref in receipt.get("source_refs", [])],
            *[ref for receipt in guarded_receipts for ref in receipt.get("mas_owner_apply_receipt_refs", [])],
            *list(memory_proof.get("consumed_refs") or []),
            *list(memory_proof.get("writeback_receipt_refs") or []),
        ]
    )


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str:
    return str(value or "").strip()


def _dedupe_text(values: Iterable[object]) -> list[str]:
    return list(dict.fromkeys(_text(value) for value in values if _text(value)))


def _fingerprint(payload: object) -> str:
    rendered = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha256(rendered.encode("utf-8")).hexdigest()[:16]


__all__ = ["build_provider_hosted_guarded_apply_receipt_from_proof"]
