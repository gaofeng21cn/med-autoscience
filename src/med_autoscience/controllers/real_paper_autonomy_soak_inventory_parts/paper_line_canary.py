from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from typing import Any

from ..body_free_evidence_packets import build_body_free_evidence_packet


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
    live_evidence_refs = _live_paper_line_evidence_refs(
        guarded_receipts=guarded_receipts,
        stable_blocker_refs=stable_blocker_refs,
    )
    no_forbidden_write_proof = _no_forbidden_write_proof(forbidden_write_guard)
    paper_line_results = _paper_line_owner_chain_results(
        guarded_receipts=guarded_receipts,
        no_forbidden_write_proof=no_forbidden_write_proof,
    )
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
        "paper_line_owner_chain_results": paper_line_results,
        "live_paper_line_evidence_refs": live_evidence_refs,
        "body_free_evidence_packets": _body_free_owner_chain_packets(
            owner_receipt_refs=owner_receipt_refs,
            stable_blocker_refs=stable_blocker_refs,
            live_evidence_refs=live_evidence_refs,
            no_forbidden_write_proof=no_forbidden_write_proof,
        ),
        "no_forbidden_write_proof": no_forbidden_write_proof,
        "authority_boundary": _authority_boundary(),
    }


def _paper_line_owner_chain_results(
    *,
    guarded_receipts: Sequence[Mapping[str, Any]],
    no_forbidden_write_proof: Mapping[str, Any],
) -> list[dict[str, Any]]:
    proof_ref = _text(no_forbidden_write_proof.get("proof_ref"))
    results: list[dict[str, Any]] = []
    for receipt in guarded_receipts:
        receipt_refs = _owner_receipt_refs([receipt])
        stable_blocker_refs = _dedupe_text(
            blocker.get("blocker_id") for blocker in _stable_mas_typed_blockers([receipt])
        )
        live_refs = _live_paper_line_evidence_refs(
            guarded_receipts=[receipt],
            stable_blocker_refs=stable_blocker_refs,
        )
        result_kind = (
            "owner_receipt"
            if receipt_refs
            else ("stable_typed_blocker" if stable_blocker_refs else "missing_owner_chain_result")
        )
        results.append(
            {
                "surface_kind": "mas_paper_line_owner_chain_result",
                "paper_line_id": _text(receipt.get("study_id")),
                "owner": "MedAutoScience",
                "result_kind": result_kind,
                "required_return_shape_satisfied": result_kind in {"owner_receipt", "stable_typed_blocker"},
                "owner_receipt_refs": receipt_refs,
                "stable_typed_blocker_refs": stable_blocker_refs
                or _sequence(live_refs.get("stable_typed_blocker_refs")),
                "progress_delta_refs": _sequence(live_refs.get("progress_delta_refs")),
                "ai_reviewer_gate_receipt_refs": _sequence(
                    live_refs.get("ai_reviewer_gate_receipt_refs")
                ),
                "artifact_movement_refs": _sequence(live_refs.get("artifact_movement_refs")),
                "human_gate_or_resume_refs": _sequence(
                    live_refs.get("human_gate_or_resume_refs")
                ),
                "no_forbidden_write_proof_ref": proof_ref,
                "body_included": False,
                "readiness_claims": dict(_mapping(live_refs.get("readiness_claims"))),
            }
        )
    return results


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
        "body_free_evidence_packets": _provider_unavailable_packets(provider_blocker_ref),
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


def _live_paper_line_evidence_refs(
    *,
    guarded_receipts: Sequence[Mapping[str, Any]],
    stable_blocker_refs: Sequence[str],
) -> dict[str, Any]:
    receipt = next((item for item in guarded_receipts if _text(item.get("study_id"))), {})
    return {
        "surface_kind": "mas_live_paper_line_owner_chain_evidence_refs",
        "paper_line_id": _text(receipt.get("study_id")),
        "owner": "MedAutoScience",
        "body_included": False,
        "progress_delta_refs": _refs_for_observed_flag(
            guarded_receipts,
            flag="evidence_progress_observed",
            fallback_suffix="artifacts/controller/repair_execution_evidence/latest.json",
        ),
        "ai_reviewer_gate_receipt_refs": _refs_for_apply_result(
            guarded_receipts,
            "ai_reviewer_re_eval",
        ),
        "artifact_movement_refs": _artifact_movement_refs(guarded_receipts),
        "human_gate_or_resume_refs": _refs_for_observed_flag(
            guarded_receipts,
            flag="human_gate_observed",
            fallback_suffix="artifacts/controller_decisions/latest.json",
        ),
        "stable_typed_blocker_refs": _refs_for_observed_flag(
            guarded_receipts,
            flag="stable_blocker_observed",
            fallback_suffix="artifacts/controller_decisions/latest.json",
        )
        or list(stable_blocker_refs),
        "no_forbidden_write_proof_ref": (
            "real_paper_autonomy_provider_hosted_guarded_apply_receipt/forbidden_write_guard"
        ),
        "readiness_claims": {
            "claims_paper_closure": False,
            "claims_publication_ready": False,
            "claims_artifact_mutation_authorized": False,
            "claims_current_package_updated": False,
        },
    }


def _refs_for_observed_flag(
    guarded_receipts: Sequence[Mapping[str, Any]],
    *,
    flag: str,
    fallback_suffix: str,
) -> list[str]:
    return _dedupe_text(
        ref
        for receipt in guarded_receipts
        if _mapping(receipt.get("mas_owner_apply_evidence")).get(flag) is True
        for ref in _matching_refs(receipt, fallback_suffix)
    )


def _refs_for_apply_result(
    guarded_receipts: Sequence[Mapping[str, Any]],
    apply_result: str,
) -> list[str]:
    return _dedupe_text(
        ref
        for receipt in guarded_receipts
        if _text(receipt.get("apply_result")) == apply_result
        for ref in receipt.get("mas_owner_apply_receipt_refs", [])
    )


def _artifact_movement_refs(guarded_receipts: Sequence[Mapping[str, Any]]) -> list[str]:
    return _dedupe_text(
        ref
        for receipt in guarded_receipts
        if _text(receipt.get("apply_result")) == "artifact_delta"
        for ref in receipt.get("mas_owner_apply_receipt_refs", [])
        if "repair_execution_receipts/latest.json" in ref
    )


def _matching_refs(receipt: Mapping[str, Any], suffix: str) -> list[str]:
    refs = [ref for ref in receipt.get("mas_owner_apply_receipt_refs", []) if suffix in _text(ref)]
    if refs:
        return refs
    return [
        ref
        for ref in receipt.get("mas_owner_apply_receipt_refs", [])
        if _text(ref)
    ]


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


def _body_free_owner_chain_packets(
    *,
    owner_receipt_refs: Sequence[str],
    stable_blocker_refs: Sequence[str],
    live_evidence_refs: Mapping[str, Any],
    no_forbidden_write_proof: Mapping[str, Any],
) -> list[dict[str, Any]]:
    packet_specs: list[tuple[str, str]] = []
    packet_specs.extend(("owner_receipt_ref", ref) for ref in owner_receipt_refs)
    packet_specs.extend(("stable_typed_blocker_ref", ref) for ref in stable_blocker_refs)
    packet_specs.extend(
        ("progress_delta_ref", ref)
        for ref in _sequence(live_evidence_refs.get("progress_delta_refs"))
    )
    packet_specs.extend(
        ("ai_reviewer_gate_receipt_ref", ref)
        for ref in _sequence(live_evidence_refs.get("ai_reviewer_gate_receipt_refs"))
    )
    packet_specs.extend(
        ("artifact_movement_ref", ref)
        for ref in _sequence(live_evidence_refs.get("artifact_movement_refs"))
    )
    packet_specs.extend(
        ("human_gate_or_resume_ref", ref)
        for ref in _sequence(live_evidence_refs.get("human_gate_or_resume_refs"))
    )
    packet_specs.extend(
        ("stable_typed_blocker_ref", ref)
        for ref in _sequence(live_evidence_refs.get("stable_typed_blocker_refs"))
    )
    proof_ref = _text(no_forbidden_write_proof.get("proof_ref"))
    if proof_ref:
        packet_specs.append(("no_forbidden_write_proof_ref", proof_ref))

    packets: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for role, ref in packet_specs:
        ref_text = _text(ref)
        if not ref_text or (role, ref_text) in seen:
            continue
        seen.add((role, ref_text))
        packets.append(
            build_body_free_evidence_packet(
                ref=ref_text,
                role=role,
                owner="MedAutoScience",
            )
        )
    return packets


def _provider_unavailable_packets(provider_blocker_ref: str) -> list[dict[str, Any]]:
    if not provider_blocker_ref:
        return []
    return [
        build_body_free_evidence_packet(
            ref=provider_blocker_ref,
            role="provider_typed_blocker_ref",
            owner="one-person-lab",
        )
    ]


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


def _sequence(value: object) -> list[Any]:
    return list(value) if isinstance(value, Sequence) and not isinstance(value, str | bytes) else []


def _text(value: object) -> str:
    return str(value or "").strip()


def _dedupe_text(values: Iterable[object]) -> list[str]:
    return list(dict.fromkeys(_text(value) for value in values if _text(value)))


__all__ = [
    "build_owner_chain_closeout_from_guarded_receipts",
    "build_provider_canary_closeout",
    "build_provider_unavailable_canary_closeout",
]
