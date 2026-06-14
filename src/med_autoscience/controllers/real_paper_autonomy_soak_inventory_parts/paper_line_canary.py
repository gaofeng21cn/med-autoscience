from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from typing import Any

from ..body_free_evidence_packets import build_body_free_evidence_packet
from ..domain_dispatch_evidence_payload import build_domain_dispatch_evidence_record_payload
from .evidence_tail_closure import build_evidence_tail_closure_summary
from .stage_expected_receipts import (
    build_stage_expected_receipt_payload_summary,
    stage_expected_receipt_refs,
    stage_monitor_freshness_refs,
)


GATE_ID = "real_paper_line_provider_canary"
TASK_ID = "agent-lab-task:mas/real-paper-line-provider-canary"
SELECTED_EVIDENCE_SURFACE = "product_entry_manifest.provider_guarded_soak_read_model.paper_line_guarded_apply_evidence"
SOURCE_ACCEPTANCE_REF = "contracts/production_acceptance/mas-production-acceptance.json#/paper_line_guarded_apply_evidence"
VERSION = "mas-real-paper-line-provider-canary.v1"
ORDINARY_PROGRESS_HANDOFF_POLICY_REF = (
    "contracts/stage_run_kernel_profile.json#/ordinary_progress_handoff"
)
ORDINARY_PROGRESS_HANDOFF_ROUTE_POLICY_REF = (
    "agent/stages/stage_route_contract.yaml#/ordinary_progress_handoff_policy"
)
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
    paper_line_payloads = _paper_line_domain_dispatch_evidence_record_payloads(
        guarded_receipts=guarded_receipts,
        no_forbidden_write_proof=no_forbidden_write_proof,
    )
    dispatch_evidence_payload = _domain_dispatch_evidence_record_payload(
        owner_receipt_refs=owner_receipt_refs,
        stable_blocker_refs=stable_blocker_refs,
        live_evidence_refs=live_evidence_refs,
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
        "paper_line_domain_dispatch_evidence_record_payloads": paper_line_payloads,
        "paper_line_owner_payload_summary": _paper_line_owner_payload_summary(paper_line_payloads),
        "stage_expected_receipt_payload_summary": build_stage_expected_receipt_payload_summary(
            paper_line_payloads
        ),
        "live_paper_line_evidence_refs": live_evidence_refs,
        "domain_dispatch_evidence_record_payload": dispatch_evidence_payload,
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
        family_transition_refs = stage_expected_receipt_refs(
            owner_receipt_refs=receipt_refs,
            stable_blocker_refs=stable_blocker_refs,
            live_evidence_refs=live_refs,
            no_forbidden_write_ref=proof_ref,
        )
        if stable_blocker_refs and not receipt_refs:
            family_transition_refs = stable_blocker_refs
        result_kind = (
            "owner_receipt"
            if receipt_refs
            else ("stable_typed_blocker" if stable_blocker_refs else "missing_owner_chain_result")
        )
        terminal_blocker_refs = (
            []
            if receipt_refs
            else stable_blocker_refs
            or _sequence(live_refs.get("stable_typed_blocker_refs"))
        )
        accepted_closeout_shape = _accepted_closeout_shape(result_kind)
        next_required_delta = _next_required_delta(
            result_kind=result_kind,
            owner_receipt_refs=receipt_refs,
            stable_typed_blocker_refs=terminal_blocker_refs,
        )
        readiness_jit_scope = _readiness_jit_scope(
            owner_receipt_refs=receipt_refs,
            stable_typed_blocker_refs=terminal_blocker_refs,
            live_evidence_refs=live_refs,
        )
        terminal_shape_source = _terminal_shape_source(result_kind)
        ordinary_handoff_proof = _ordinary_progress_handoff_proof(
            paper_line_id=_text(receipt.get("study_id")),
            accepted_closeout_shape=accepted_closeout_shape,
            terminal_shape_source=terminal_shape_source,
            next_required_delta=next_required_delta,
            readiness_jit_scope=readiness_jit_scope,
        )
        results.append(
            {
                "surface_kind": "mas_paper_line_owner_chain_result",
                "paper_line_id": _text(receipt.get("study_id")),
                "owner": "MedAutoScience",
                "result_kind": result_kind,
                "accepted_closeout_shape": accepted_closeout_shape,
                "ProgressDeltaReceipt_or_OwnerReceipt_or_TypedBlocker": (
                    accepted_closeout_shape
                ),
                "next_owner": "MedAutoScience",
                "next_required_delta": next_required_delta,
                "readiness_jit_scope": readiness_jit_scope,
                "audit_sidecar_passive": True,
                "ordinary_progress_handoff_proof": ordinary_handoff_proof,
                "required_return_shape_satisfied": result_kind in {"owner_receipt", "stable_typed_blocker"},
                "owner_receipt_refs": receipt_refs,
                "stable_typed_blocker_refs": stable_blocker_refs
                or _sequence(live_refs.get("stable_typed_blocker_refs")),
                "progress_delta_refs": _sequence(live_refs.get("progress_delta_refs")),
                "ai_reviewer_gate_receipt_refs": _sequence(
                    live_refs.get("ai_reviewer_gate_receipt_refs")
                ),
                "artifact_movement_refs": _sequence(live_refs.get("artifact_movement_refs")),
                "publication_route_memory_writeback_receipt_refs": _sequence(
                    live_refs.get("publication_route_memory_writeback_receipt_refs")
                ),
                "artifact_lifecycle_receipt_refs": _sequence(
                    live_refs.get("artifact_lifecycle_receipt_refs")
                ),
                "human_gate_or_resume_refs": _sequence(
                    live_refs.get("human_gate_or_resume_refs")
                ),
                "evidence_tail_closure_summary": build_evidence_tail_closure_summary(
                    study_id=_text(receipt.get("study_id")),
                    owner_receipt_refs=receipt_refs,
                    stable_blocker_refs=stable_blocker_refs,
                    live_evidence_refs=live_refs,
                    family_transition_receipt_refs=family_transition_refs,
                ),
                "no_forbidden_write_proof_ref": proof_ref,
                "body_included": False,
                "readiness_claims": dict(_mapping(live_refs.get("readiness_claims"))),
            }
        )
    return results


def _accepted_closeout_shape(result_kind: str) -> str:
    if result_kind == "owner_receipt":
        return "OwnerReceipt"
    if result_kind == "stable_typed_blocker":
        return "TypedBlocker"
    return "missing_owner_chain_result"


def _terminal_shape_source(result_kind: str) -> str:
    if result_kind == "owner_receipt":
        return "owner_receipt_refs"
    if result_kind == "stable_typed_blocker":
        return "stable_typed_blocker_refs"
    return "owner_receipt_refs_or_stable_typed_blocker_refs"


def _next_required_delta(
    *,
    result_kind: str,
    owner_receipt_refs: Sequence[str],
    stable_typed_blocker_refs: Sequence[str],
) -> dict[str, Any]:
    if result_kind == "owner_receipt":
        return {
            "delta_kind": "consume_owner_receipt_refs",
            "required_ref_field": "owner_receipt_refs",
            "required_refs": list(owner_receipt_refs),
        }
    if result_kind == "stable_typed_blocker":
        return {
            "delta_kind": "route_stable_typed_blocker",
            "required_ref_field": "stable_typed_blocker_refs",
            "required_refs": list(stable_typed_blocker_refs),
        }
    return {
        "delta_kind": "emit_owner_receipt_or_stable_typed_blocker",
        "required_ref_field": "owner_receipt_refs_or_stable_typed_blocker_refs",
        "required_refs": [],
    }


def _readiness_jit_scope(
    *,
    owner_receipt_refs: Sequence[str],
    stable_typed_blocker_refs: Sequence[str],
    live_evidence_refs: Mapping[str, Any],
) -> dict[str, Any]:
    ref_fields = [
        field
        for field, refs in (
            ("owner_receipt_refs", owner_receipt_refs),
            ("stable_typed_blocker_refs", stable_typed_blocker_refs),
            ("progress_delta_refs", _sequence(live_evidence_refs.get("progress_delta_refs"))),
            (
                "ai_reviewer_gate_receipt_refs",
                _sequence(live_evidence_refs.get("ai_reviewer_gate_receipt_refs")),
            ),
            (
                "publication_route_memory_writeback_receipt_refs",
                _sequence(live_evidence_refs.get("publication_route_memory_writeback_receipt_refs")),
            ),
            (
                "artifact_lifecycle_receipt_refs",
                _sequence(live_evidence_refs.get("artifact_lifecycle_receipt_refs")),
            ),
            (
                "human_gate_or_resume_refs",
                _sequence(live_evidence_refs.get("human_gate_or_resume_refs")),
            ),
        )
        if refs
    ]
    return {
        "default_mode": "just_in_time_for_current_delta",
        "check_scope_source": "stage_run_current_owner_delta.next_required_delta",
        "full_readiness_inventory_role": "audit_or_terminal_gate_only",
        "current_delta_ref_fields": ref_fields,
    }


def _ordinary_progress_handoff_proof(
    *,
    paper_line_id: str,
    accepted_closeout_shape: str,
    terminal_shape_source: str,
    next_required_delta: Mapping[str, Any],
    readiness_jit_scope: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "surface_kind": "mas_ordinary_owner_chain_handoff_proof",
        "policy_ref": ORDINARY_PROGRESS_HANDOFF_POLICY_REF,
        "route_policy_ref": ORDINARY_PROGRESS_HANDOFF_ROUTE_POLICY_REF,
        "paper_line_id": paper_line_id,
        "accepted_closeout_shape": accepted_closeout_shape,
        "ProgressDeltaReceipt_or_OwnerReceipt_or_TypedBlocker": accepted_closeout_shape,
        "terminal_shape_source": terminal_shape_source,
        "next_owner": "MedAutoScience",
        "next_required_delta": dict(next_required_delta),
        "readiness_jit_scope": dict(readiness_jit_scope),
        "audit_sidecar_passive": True,
        "provider_completion_can_close": False,
        "audit_sidecar_can_generate_default_next_action": False,
        "readiness_inventory_can_generate_default_next_action": False,
        "provider_completion_is_success": False,
        "success_path_requires_owner_receipt_or_stable_typed_blocker": True,
        "body_included": False,
    }


def _paper_line_domain_dispatch_evidence_record_payloads(
    *,
    guarded_receipts: Sequence[Mapping[str, Any]],
    no_forbidden_write_proof: Mapping[str, Any],
) -> list[dict[str, Any]]:
    payloads: list[dict[str, Any]] = []
    for receipt in guarded_receipts:
        receipt_refs = _owner_receipt_refs([receipt])
        stable_blocker_refs = _dedupe_text(
            blocker.get("blocker_id") for blocker in _stable_mas_typed_blockers([receipt])
        )
        live_refs = _live_paper_line_evidence_refs(
            guarded_receipts=[receipt],
            stable_blocker_refs=stable_blocker_refs,
        )
        payloads.append(
            _domain_dispatch_evidence_record_payload(
                owner_receipt_refs=receipt_refs,
                stable_blocker_refs=stable_blocker_refs,
                live_evidence_refs=live_refs,
                no_forbidden_write_proof=no_forbidden_write_proof,
            )
        )
    return payloads


def _paper_line_owner_payload_summary(payloads: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    return {
        "paper_line_count": len(payloads),
        "success_payload_count": sum(
            1
            for payload in payloads
            if _text(payload.get("mode")) == "refs_only_domain_owned_success_payload"
        ),
        "typed_blocker_payload_count": sum(
            1
            for payload in payloads
            if _text(payload.get("mode")) == "refs_only_domain_owned_typed_blocker_payload"
        ),
        "domain_ready_claim_count": sum(
            1 for payload in payloads if payload.get("domain_ready_claimed") is True
        ),
        "production_ready_claim_count": sum(
            1
            for payload in payloads
            if _mapping(payload.get("authority_boundary")).get("provider_completion_is_domain_ready")
            is True
        ),
        "artifact_mutation_authorized_count": sum(
            1 for payload in payloads if payload.get("artifact_mutation_authorized") is True
        ),
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
        "publication_route_memory_writeback_receipt_refs": (
            _publication_route_memory_writeback_receipt_refs(guarded_receipts)
        ),
        "artifact_lifecycle_receipt_refs": _artifact_lifecycle_receipt_refs(
            guarded_receipts
        ),
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


def _publication_route_memory_writeback_receipt_refs(
    guarded_receipts: Sequence[Mapping[str, Any]],
) -> list[str]:
    return _dedupe_text(
        ref
        for receipt in guarded_receipts
        for ref in _sequence(receipt.get("publication_route_memory_writeback_receipt_refs"))
    )


def _artifact_lifecycle_receipt_refs(
    guarded_receipts: Sequence[Mapping[str, Any]],
) -> list[str]:
    return _dedupe_text(
        ref
        for receipt in guarded_receipts
        for ref in _sequence(receipt.get("artifact_lifecycle_receipt_refs"))
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


def _domain_dispatch_evidence_record_payload(
    *,
    owner_receipt_refs: Sequence[str],
    stable_blocker_refs: Sequence[str],
    live_evidence_refs: Mapping[str, Any],
    no_forbidden_write_proof: Mapping[str, Any],
) -> dict[str, Any]:
    paper_line_id = _text(live_evidence_refs.get("paper_line_id"))
    no_forbidden_write_ref = _text(no_forbidden_write_proof.get("proof_ref"))
    evidence_refs = _dedupe_text(
        [
            *owner_receipt_refs,
            *stable_blocker_refs,
            *_sequence(live_evidence_refs.get("progress_delta_refs")),
            *_sequence(live_evidence_refs.get("ai_reviewer_gate_receipt_refs")),
            *_sequence(live_evidence_refs.get("artifact_movement_refs")),
            *_sequence(live_evidence_refs.get("publication_route_memory_writeback_receipt_refs")),
            *_sequence(live_evidence_refs.get("artifact_lifecycle_receipt_refs")),
            *_sequence(live_evidence_refs.get("human_gate_or_resume_refs")),
            *_sequence(live_evidence_refs.get("stable_typed_blocker_refs")),
            no_forbidden_write_ref,
            SOURCE_ACCEPTANCE_REF,
        ]
    )
    expected_receipt_refs = stage_expected_receipt_refs(
        owner_receipt_refs=owner_receipt_refs,
        stable_blocker_refs=stable_blocker_refs,
        live_evidence_refs=live_evidence_refs,
        no_forbidden_write_ref=no_forbidden_write_ref,
    )
    monitor_freshness_refs = stage_monitor_freshness_refs(
        owner_receipt_refs=owner_receipt_refs,
        stable_blocker_refs=stable_blocker_refs,
        live_evidence_refs=live_evidence_refs,
        no_forbidden_write_ref=no_forbidden_write_ref,
    )
    research_audit_details = _research_audit_ref_family_details(
        paper_line_id=paper_line_id,
        owner_receipt_refs=owner_receipt_refs,
        stable_blocker_refs=stable_blocker_refs,
        live_evidence_refs=live_evidence_refs,
        stage_expected_receipt_refs=(
            stable_blocker_refs
            if stable_blocker_refs and not owner_receipt_refs
            else expected_receipt_refs
        ),
    )
    return build_domain_dispatch_evidence_record_payload(
        task_kind="paper_autonomy/guarded-apply",
        study_id=paper_line_id,
        stage_id="finalize_and_publication_handoff",
        stage_evidence_stage_id="finalize_and_publication_handoff",
        reason=(
            "real_paper_line_owner_receipt_observed"
            if owner_receipt_refs
            else "real_paper_line_stable_typed_blocker_observed"
        ),
        evidence_refs=evidence_refs,
        domain_owner_receipt_refs=owner_receipt_refs,
        typed_blocker_refs=stable_blocker_refs,
        no_regression_evidence_refs=[no_forbidden_write_ref] if no_forbidden_write_ref else [],
        expected_receipt_refs=expected_receipt_refs,
        monitor_freshness_refs=monitor_freshness_refs,
        reason_details=research_audit_details,
    )


def _research_audit_ref_family_details(
    *,
    paper_line_id: str,
    owner_receipt_refs: Sequence[str],
    stable_blocker_refs: Sequence[str],
    live_evidence_refs: Mapping[str, Any],
    stage_expected_receipt_refs: Sequence[str],
) -> dict[str, Any]:
    progress_refs = _sequence(live_evidence_refs.get("progress_delta_refs"))
    artifact_movement_refs = _sequence(live_evidence_refs.get("artifact_movement_refs"))
    memory_writeback_refs = _sequence(
        live_evidence_refs.get("publication_route_memory_writeback_receipt_refs")
    )
    artifact_lifecycle_refs = _sequence(
        live_evidence_refs.get("artifact_lifecycle_receipt_refs")
    )
    decision_trace_refs = _dedupe_text(
        [
            *_refs_with_suffix(owner_receipt_refs, "gate_replay_requests/latest.json"),
            *_refs_with_suffix(owner_receipt_refs, "controller_decisions/latest.json"),
            *_sequence(live_evidence_refs.get("human_gate_or_resume_refs")),
        ]
    )
    if owner_receipt_refs and not decision_trace_refs:
        decision_trace_refs = _dedupe_text([*owner_receipt_refs, *progress_refs])
    artifact_lineage_refs = _artifact_lineage_refs(live_evidence_refs)
    reproducibility_refs = _dedupe_text(
        [*artifact_movement_refs, *artifact_lifecycle_refs]
    )
    lineage_or_reproducibility_refs = _dedupe_text(
        [*artifact_lineage_refs, *reproducibility_refs]
    )
    negative_failed_path_refs = _dedupe_text(stable_blocker_refs) or [
        _negative_failed_path_ledger_ref(paper_line_id)
    ]
    missing_ref_family_refs = [
        family
        for family, refs in (
            ("negative_or_failed_path_ledger_refs", negative_failed_path_refs),
            ("decision_trace_refs", decision_trace_refs),
            ("artifact_lineage_or_reproducibility_refs", lineage_or_reproducibility_refs),
        )
        if not refs
    ]
    return {
        "negative_failed_path_refs": negative_failed_path_refs,
        "decision_trace_refs": decision_trace_refs,
        "artifact_lineage_refs": artifact_lineage_refs,
        "reproducibility_refs": reproducibility_refs,
        "evidence_tail_closure_summary": build_evidence_tail_closure_summary(
            study_id=paper_line_id,
            owner_receipt_refs=owner_receipt_refs,
            stable_blocker_refs=stable_blocker_refs,
            live_evidence_refs=live_evidence_refs,
            family_transition_receipt_refs=stage_expected_receipt_refs,
        ),
        "publication_route_memory_writeback_receipt_refs": memory_writeback_refs,
        "artifact_lifecycle_receipt_refs": artifact_lifecycle_refs,
        "artifact_lineage_or_reproducibility_refs": lineage_or_reproducibility_refs,
        "routeback_owner_refs": ["MedAutoScience:finalize_and_publication_handoff"],
        "missing_ref_family_refs": missing_ref_family_refs,
    }


def _artifact_lineage_refs(
    live_evidence_refs: Mapping[str, Any],
) -> list[str]:
    refs: list[str] = []
    for progress_ref in _sequence(live_evidence_refs.get("progress_delta_refs")):
        progress_text = _text(progress_ref)
        if not progress_text:
            continue
        refs.append(f"{progress_text}#/candidate_package_freshness")
        refs.append(f"{progress_text}#/display_freshness")
    refs.extend(_sequence(live_evidence_refs.get("artifact_movement_refs")))
    return _dedupe_text(refs)


def _refs_with_suffix(refs: Sequence[str], suffix: str) -> list[str]:
    return [ref for ref in refs if suffix in _text(ref)]


def _negative_failed_path_ledger_ref(paper_line_id: str) -> str:
    token = _text(paper_line_id).replace("/", "_") or "paper-line"
    return f"mas-negative-failed-path-ledger:medautoscience:paper_autonomy_guarded-apply:{token}"


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
        ("publication_route_memory_writeback_receipt_ref", ref)
        for ref in _sequence(live_evidence_refs.get("publication_route_memory_writeback_receipt_refs"))
    )
    packet_specs.extend(
        ("artifact_lifecycle_receipt_ref", ref)
        for ref in _sequence(live_evidence_refs.get("artifact_lifecycle_receipt_refs"))
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
