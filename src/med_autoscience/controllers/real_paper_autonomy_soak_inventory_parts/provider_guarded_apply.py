from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Mapping, Sequence
from typing import Any

from . import paper_line_canary


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
    attempt_state = "mas_owner_receipt_present" if status == "applied" else "mas_owner_receipt_missing"
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
            "attempt_state": attempt_state,
            "attempt_ready": True,
            "provider_attempt_is_truth": False,
            "provider_attempt_wrote_workspace": False,
        },
        "idempotency_key": _text(idempotency_key),
        "source_fingerprint": source_fingerprint,
        "guarded_apply_status": proof.get("guarded_apply_status"),
        "guarded_apply_receipts": guarded_receipts,
        "typed_blockers": typed_blockers,
        "publication_route_memory_final_proof": dict(memory_proof),
        "paper_line_provider_canary_closeout": paper_line_canary.build_provider_canary_closeout(
            provider_attempt={
                "attempt_id": provider_attempt_id,
                "attempt_state": attempt_state,
                "attempt_ready": True,
            },
            guarded_receipts=guarded_receipts,
            forbidden_write_guard=_mapping(proof.get("forbidden_write_guard")),
            source_refs=_source_refs(guarded_receipts=guarded_receipts, memory_proof=memory_proof),
            source_fingerprint=source_fingerprint,
        ),
        "forbidden_write_guard": dict(_mapping(proof.get("forbidden_write_guard"))),
        "source_refs": _source_refs(guarded_receipts=guarded_receipts, memory_proof=memory_proof),
        "summary": {
            **dict(_mapping(proof.get("summary"))),
            "status": status,
            "provider_attempt_state": attempt_state,
            "provider_attempt_ready": True,
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


def build_provider_unavailable_guarded_apply_receipt(
    *,
    schema_version: int,
    surface: str,
    provider_attempt_id: str,
    idempotency_key: str,
    target_studies: Sequence[str],
    reason: str,
) -> dict[str, Any]:
    blocker_id = f"provider_guarded_apply_unavailable:{_fingerprint([provider_attempt_id, idempotency_key, target_studies, reason])}"
    typed_blocker = {
        "blocker_id": blocker_id,
        "owner": "one-person-lab",
        "reason": _text(reason) or "provider guarded apply request cannot be evaluated by MAS domain-handler",
        "required_owner_surface": "OPL provider ready contract / MAS domain-handler guarded-apply task",
        "write_permitted": False,
    }
    source_fingerprint = _fingerprint(
        {
            "provider_attempt_id": provider_attempt_id,
            "idempotency_key": idempotency_key,
            "target_studies": list(target_studies),
            "typed_blocker": typed_blocker,
        }
    )
    return {
        "surface": surface,
        "schema_version": schema_version,
        "status": "typed_blocker",
        "target_studies": list(target_studies),
        "provider_attempt": {
            "attempt_id": _text(provider_attempt_id),
            "attempt_owner": "one-person-lab",
            "attempt_state": "provider_unavailable",
            "attempt_ready": False,
            "provider_attempt_is_truth": False,
            "provider_attempt_wrote_workspace": False,
        },
        "idempotency_key": _text(idempotency_key),
        "source_fingerprint": source_fingerprint,
        "guarded_apply_status": "provider_unavailable",
        "guarded_apply_receipts": [],
        "typed_blockers": [typed_blocker],
        "publication_route_memory_final_proof": {
            "status": "typed_blocker_provider_unavailable",
            "body_included": False,
            "memory_body_included": False,
            "opl_can_read_memory_body": False,
            "opl_can_accept_or_reject_writeback": False,
        },
        "paper_line_provider_canary_closeout": paper_line_canary.build_provider_unavailable_canary_closeout(
            provider_attempt={
                "attempt_id": provider_attempt_id,
                "attempt_state": "provider_unavailable",
                "attempt_ready": False,
            },
            typed_blocker=typed_blocker,
            forbidden_write_guard={
                "aggregate_result": "fail_closed_provider_unavailable",
                "can_write_domain_truth": False,
                "can_write_current_package": False,
            },
            source_fingerprint=source_fingerprint,
        ),
        "forbidden_write_guard": {
            "aggregate_result": "fail_closed_provider_unavailable",
            "can_write_domain_truth": False,
            "can_write_current_package": False,
        },
        "source_refs": [],
        "summary": {
            "status": "typed_blocker",
            "provider_attempt_state": "provider_unavailable",
            "provider_attempt_ready": False,
            "provider_attempt_wrote_workspace": False,
            "writes_performed": False,
            "real_workspace_mutation_allowed": False,
            "writes_performed_by_this_receipt": False,
            "receipt_wrote_forbidden_surfaces": False,
            "typed_blocker_count": 1,
        },
        "authority_boundary": {
            "provider_attempt_owner": "one-person-lab",
            "domain_truth_owner": "med-autoscience",
            "quality_gate_owner": "med-autoscience",
            "artifact_authority_owner": "med-autoscience",
            "provider_attempt_is_truth": False,
            "provider_completion_is_publication_quality": False,
            "opl_can_write_mas_truth": False,
            "opl_can_write_artifact_authority": False,
            "opl_can_write_memory_body": False,
        },
        "source_guarded_apply_proof_summary": None,
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


__all__ = [
    "build_provider_hosted_guarded_apply_receipt_from_proof",
    "build_provider_unavailable_guarded_apply_receipt",
]
