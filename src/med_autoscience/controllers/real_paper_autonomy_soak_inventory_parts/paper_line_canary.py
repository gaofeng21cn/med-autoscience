from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from typing import Any


GATE_ID = "real_paper_line_provider_canary"
TASK_ID = "agent-lab-task:mas/real-paper-line-provider-canary"
SELECTED_EVIDENCE_SURFACE = "product_entry_manifest.provider_guarded_soak_read_model.paper_line_guarded_apply_evidence"
SOURCE_ACCEPTANCE_REF = "contracts/production_acceptance/mas-production-acceptance.json#/paper_line_guarded_apply_evidence"
VERSION = "mas-real-paper-line-provider-canary.v1"
FORBIDDEN_SURFACES = (
    "publication_eval/latest.json",
    "controller_decisions/latest.json",
    "current_package",
    "publication_quality_verdict",
    "memory_body",
    "artifact_body",
)


def build_owner_chain_closeout_from_guarded_receipts(
    *,
    guarded_receipts: Sequence[Mapping[str, Any]],
    forbidden_write_guard: Mapping[str, Any],
) -> dict[str, Any]:
    owner_receipt_refs = _owner_receipt_refs(guarded_receipts)
    stable_blockers = _stable_mas_typed_blockers(guarded_receipts)
    stable_blocker_refs = _dedupe_text(blocker.get("blocker_id") for blocker in stable_blockers)
    result_kind = (
        "owner_receipt"
        if owner_receipt_refs
        else ("stable_typed_blocker" if stable_blocker_refs else "missing_owner_chain_result")
    )
    required_shape_satisfied = result_kind in {"owner_receipt", "stable_typed_blocker"}
    return {
        "surface_kind": "mas_real_paper_line_owner_chain_closeout",
        "version": VERSION,
        "gate_id": GATE_ID,
        "task_id": TASK_ID,
        "closeout_status": (
            "closed_by_mas_owner_chain"
            if required_shape_satisfied
            else "blocked_no_mas_owner_receipt_or_stable_typed_blocker"
        ),
        "success_criterion": "mas_owner_chain_returns_owner_receipt_or_stable_typed_blocker",
        "provider_completion_is_success": False,
        "selected_opl_ingestable_ref_surface": _selected_surface_ref(),
        "required_return_shape_satisfied": required_shape_satisfied,
        "owner_chain_result": {
            "result_kind": result_kind,
            "owner": "MedAutoScience",
            "owner_receipt_refs": owner_receipt_refs,
            "stable_typed_blocker_refs": stable_blocker_refs,
            "body_included": False,
        },
        "no_forbidden_write_proof": _no_forbidden_write_proof(forbidden_write_guard),
        "authority_boundary": _authority_boundary(),
    }


def build_provider_canary_closeout(
    *,
    provider_attempt: Mapping[str, Any],
    guarded_receipts: Sequence[Mapping[str, Any]],
    forbidden_write_guard: Mapping[str, Any],
    source_refs: Sequence[object],
    source_fingerprint: str,
) -> dict[str, Any]:
    owner_chain = build_owner_chain_closeout_from_guarded_receipts(
        guarded_receipts=guarded_receipts,
        forbidden_write_guard=forbidden_write_guard,
    )
    return {
        **owner_chain,
        "surface_kind": "mas_real_paper_line_provider_canary_closeout",
        "provider_attempt": {
            "attempt_id": _text(provider_attempt.get("attempt_id")),
            "attempt_owner": "one-person-lab",
            "attempt_state": _text(provider_attempt.get("attempt_state")),
            "attempt_ready": provider_attempt.get("attempt_ready") is True,
            "provider_attempt_is_truth": False,
            "provider_completion_is_success": False,
            "provider_attempt_wrote_mas_truth": False,
            "provider_attempt_wrote_mas_body_or_package": False,
        },
        "source_fingerprint": _text(source_fingerprint),
        "source_refs": _dedupe_text(source_refs),
    }


def build_provider_unavailable_canary_closeout(
    *,
    provider_attempt: Mapping[str, Any],
    typed_blocker: Mapping[str, Any],
    forbidden_write_guard: Mapping[str, Any],
    source_fingerprint: str,
) -> dict[str, Any]:
    provider_blocker_ref = _text(typed_blocker.get("blocker_id"))
    return {
        "surface_kind": "mas_real_paper_line_provider_canary_closeout",
        "version": VERSION,
        "gate_id": GATE_ID,
        "task_id": TASK_ID,
        "closeout_status": "blocked_before_mas_owner_chain_provider_unavailable",
        "success_criterion": "mas_owner_chain_returns_owner_receipt_or_stable_typed_blocker",
        "provider_completion_is_success": False,
        "selected_opl_ingestable_ref_surface": _selected_surface_ref(),
        "required_return_shape_satisfied": False,
        "owner_chain_result": {
            "result_kind": "provider_typed_blocker",
            "owner": "one-person-lab",
            "owner_receipt_refs": [],
            "stable_typed_blocker_refs": [],
            "provider_typed_blocker_refs": [provider_blocker_ref] if provider_blocker_ref else [],
            "body_included": False,
        },
        "provider_attempt": {
            "attempt_id": _text(provider_attempt.get("attempt_id")),
            "attempt_owner": "one-person-lab",
            "attempt_state": _text(provider_attempt.get("attempt_state")),
            "attempt_ready": provider_attempt.get("attempt_ready") is True,
            "provider_attempt_is_truth": False,
            "provider_completion_is_success": False,
            "provider_attempt_wrote_mas_truth": False,
            "provider_attempt_wrote_mas_body_or_package": False,
        },
        "no_forbidden_write_proof": _no_forbidden_write_proof(forbidden_write_guard),
        "source_fingerprint": _text(source_fingerprint),
        "source_refs": [],
        "authority_boundary": _authority_boundary(),
    }


def _owner_receipt_refs(guarded_receipts: Sequence[Mapping[str, Any]]) -> list[str]:
    return _dedupe_text(
        ref
        for receipt in guarded_receipts
        if _text(receipt.get("apply_result")) != "typed_blocker"
        for ref in receipt.get("mas_owner_apply_receipt_refs", [])
    )


def _stable_mas_typed_blockers(guarded_receipts: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    blockers: list[dict[str, Any]] = []
    for receipt in guarded_receipts:
        blocker = _mapping(receipt.get("typed_blocker"))
        if (
            _text(blocker.get("blocker_id"))
            and _text(blocker.get("owner")) == "MedAutoScience"
            and blocker.get("write_permitted") is False
        ):
            blockers.append(dict(blocker))
    return blockers


def _selected_surface_ref() -> dict[str, Any]:
    return {
        "ref": SELECTED_EVIDENCE_SURFACE,
        "role": "only_opl_ingestable_refs_surface",
        "body_included": False,
    }


def _no_forbidden_write_proof(forbidden_write_guard: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "proof_ref": "real_paper_autonomy_provider_hosted_guarded_apply_receipt/forbidden_write_guard",
        "guard_result": _text(forbidden_write_guard.get("aggregate_result") or forbidden_write_guard.get("result")),
        "provider_or_opl_wrote_domain_truth": False,
        "provider_or_opl_wrote_artifact_body": False,
        "provider_or_opl_wrote_memory_body": False,
        "provider_or_opl_wrote_current_package": False,
        "body_included": False,
        "forbidden_surfaces": list(FORBIDDEN_SURFACES),
    }


def _authority_boundary() -> dict[str, Any]:
    return {
        "domain_truth_owner": "med-autoscience",
        "provider_attempt_owner": "one-person-lab",
        "owner_chain_authority": "MedAutoScience",
        "opl_ingestable_surface": SELECTED_EVIDENCE_SURFACE,
        "provider_completion_can_close_canary": False,
        "opl_can_write_mas_truth": False,
        "opl_can_write_artifact_body": False,
        "opl_can_write_memory_body": False,
        "opl_can_write_current_package": False,
    }


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str:
    return str(value or "").strip()


def _dedupe_text(values: Iterable[object]) -> list[str]:
    return list(dict.fromkeys(_text(value) for value in values if _text(value)))


__all__ = [
    "build_owner_chain_closeout_from_guarded_receipts",
    "build_provider_canary_closeout",
    "build_provider_unavailable_canary_closeout",
]
