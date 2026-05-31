from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from typing import Any

from ..body_free_evidence_packets import build_body_free_evidence_packet
from ..domain_dispatch_evidence_payload import build_domain_dispatch_evidence_record_payload
from .evidence_tail_closure import build_evidence_tail_closure_summary


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
MAS_RUNTIME_GUARD_STAGE_IDS = (
    "direction_and_route_selection",
    "baseline_and_evidence_setup",
    "bounded_analysis_campaign",
    "manuscript_authoring",
    "review_and_quality_gate",
    "finalize_and_publication_handoff",
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
        "stage_expected_receipt_payload_summary": _stage_expected_receipt_payload_summary(
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
        family_transition_refs = _stage_expected_receipt_refs(
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


def _stage_expected_receipt_payload_summary(
    payloads: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    success_payload_count = sum(
        1
        for payload in payloads
        if _text(payload.get("mode")) == "refs_only_domain_owned_success_payload"
    )
    typed_blocker_payload_count = sum(
        1
        for payload in payloads
        if _text(payload.get("mode")) == "refs_only_domain_owned_typed_blocker_payload"
    )
    stage_payloads = [
        stage
        for stage in (_stage_expected_receipt_stage_payload(stage_id, payloads) for stage_id in _stage_ids(payloads))
        if stage
    ]
    return {
        "surface_kind": "mas_stage_expected_receipt_payload_summary",
        "owner": "med-autoscience",
        "consumer": "one_person_lab",
        "status": "per_stage_expected_receipt_payload_refs_ready_with_live_evidence_typed_blockers",
        "payload_kind": "stage_expected_receipt_or_monitor_freshness_refs",
        "payload_path_policy": (
            "operator_must_choose_success_refs_path_or_domain_owned_typed_blocker_path_empty_template_blocks"
        ),
        "payload_body_allowed": False,
        "empty_payload_template_is_success_evidence": False,
        "body_included": False,
        "summary_source_surface": "domain_dispatch_payload_summaries",
        "paper_line_count": len(payloads),
        "success_payload_count": success_payload_count,
        "typed_blocker_payload_count": typed_blocker_payload_count,
        "domain_ready_claim_count": 0,
        "production_ready_claim_count": 0,
        "publication_ready_claim_count": 0,
        "artifact_mutation_authorized_count": 0,
        "current_package_mutation_authorized_count": 0,
        "required_operator_payload_refs": [
            "domain_receipt_refs",
            "monitor_freshness_refs",
            "runtime_event_refs",
            "typed_blocker_refs",
        ],
        "required_return_shapes": [
            "domain_receipt_ref",
            "monitor_freshness_ref",
            "runtime_event_ref",
            "typed_blocker_ref",
        ],
        "accepted_payload_paths_ref": (
            "/real_paper_autonomy_guarded_apply_proof/paper_line_provider_canary_closeout/"
            "stage_expected_receipt_payload_summary"
        ),
        "stage_count": len(stage_payloads),
        "stages": stage_payloads,
    }


def _stage_expected_receipt_stage_payload(
    stage_id: str,
    payloads: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    stage_payloads = [
        payload for payload in payloads if _record_stage_id(payload) == stage_id
    ]
    success_payloads = [
        payload
        for payload in stage_payloads
        if _text(payload.get("mode")) == "refs_only_domain_owned_success_payload"
    ]
    typed_blocker_payloads = [
        payload
        for payload in stage_payloads
        if _record_payload_refs(payload, "typed_blocker_refs")
    ]
    domain_owner_receipt_refs = _dedupe_text(
        ref
        for payload in success_payloads
        for ref in _record_payload_refs(payload, "domain_owner_receipt_refs")
    )
    expected_receipt_refs = _dedupe_text(
        ref
        for payload in success_payloads
        for ref in _record_payload_refs(payload, "stage_expected_receipt_refs")
    )
    monitor_freshness_refs = _dedupe_text(
        ref
        for payload in success_payloads
        for ref in _record_payload_refs(payload, "stage_monitor_freshness_refs")
    )
    runtime_event_refs = _dedupe_text(
        ref
        for payload in success_payloads
        for ref in _record_payload_refs(payload, "stage_runtime_event_refs")
    )
    typed_blocker_refs = _dedupe_text(
        ref
        for payload in typed_blocker_payloads
        for ref in _record_payload_refs(payload, "typed_blocker_refs")
    )
    if not typed_blocker_refs and stage_id in MAS_RUNTIME_GUARD_STAGE_IDS:
        typed_blocker_refs = [_stage_typed_blocker_ref(stage_id)]
    if not (
        expected_receipt_refs
        or monitor_freshness_refs
        or runtime_event_refs
        or typed_blocker_refs
    ):
        return {}
    stage_payload_count = len(stage_payloads)
    return {
        "stage_id": stage_id,
        "sequence": _stage_sequence(stage_id),
        "paper_line_count": stage_payload_count or len(payloads),
        "success_payload_count": len(success_payloads),
        "typed_blocker_payload_count": len(typed_blocker_payloads) or int(bool(typed_blocker_refs)),
        "domain_owner_receipt_ref_count": len(domain_owner_receipt_refs),
        "stable_typed_blocker_ref_count": len(typed_blocker_refs),
        "stage_expected_receipt_ref_count": len(expected_receipt_refs),
        "stage_monitor_freshness_ref_count": len(monitor_freshness_refs),
        "no_forbidden_write_guard_ref_count": sum(
            len(_record_payload_refs(payload, "forbidden_write_guard_refs"))
            for payload in stage_payloads
        ),
        "payload_kind": "stage_expected_receipt_or_monitor_freshness_refs",
        "current_payload_template": {
            "domain_receipt_refs": [],
            "monitor_freshness_refs": [],
            "runtime_event_refs": [],
            "typed_blocker_refs": [],
        },
        "success_refs_path_source": (
            "domain_dispatch_payload_summaries[mode=refs_only_domain_owned_success_payload]"
        ),
        "typed_blocker_path_source": (
            "domain_dispatch_payload_summaries[mode=refs_only_domain_owned_typed_blocker_payload]"
        ),
        "success_refs_path_payload": {
            "domain_receipt_refs": expected_receipt_refs,
            "monitor_freshness_refs": monitor_freshness_refs,
            "runtime_event_refs": runtime_event_refs,
            "typed_blocker_refs": [],
        },
        "typed_blocker_path_payload": {
            "domain_receipt_refs": [],
            "monitor_freshness_refs": _dedupe_text(
                ref
                for payload in typed_blocker_payloads
                for ref in _record_payload_refs(payload, "stage_monitor_freshness_refs")
            ),
            "runtime_event_refs": [],
            "typed_blocker_refs": typed_blocker_refs,
        },
        "monitor_status": (
            "success_refs_observed_with_typed_blocker_tail"
            if expected_receipt_refs and typed_blocker_refs
            else "success_refs_observed"
            if expected_receipt_refs or monitor_freshness_refs or runtime_event_refs
            else "typed_blocker_path_available"
        ),
        "operator_payload_submitted": False,
        "recommended_current_payload_path": (
            "typed_blocker_path" if typed_blocker_refs else "success_refs_path"
        ),
        "success_refs_visible_is_completion": False,
        "typed_blocker_visible_is_domain_ready": False,
        "payload_body_allowed": False,
        "domain_readiness_claimed": False,
        "production_readiness_claimed": False,
        "publication_readiness_claimed": False,
        "publication_ready_claimed": False,
        "artifact_mutation_authorized": False,
        "current_package_mutation_authorized": False,
        "production_soak_complete_claimed": False,
    }


def _stage_ids(payloads: Sequence[Mapping[str, Any]]) -> list[str]:
    return _dedupe_text([*MAS_RUNTIME_GUARD_STAGE_IDS, *(_record_stage_id(payload) for payload in payloads)])


def _stage_typed_blocker_ref(stage_id: str) -> str:
    return (
        "mas-stage-typed-blocker:"
        f"medautoscience:{stage_id}:"
        "real-paper-line-owner-receipt-or-monitor-freshness-pending"
    )


def _record_stage_id(payload: Mapping[str, Any]) -> str:
    return _text(_mapping(payload.get("record_payload")).get("stage_id")) or _text(payload.get("stage_id"))


def _record_payload_refs(payload: Mapping[str, Any], key: str) -> list[str]:
    record_payload = _mapping(payload.get("record_payload"))
    refs = _sequence(record_payload.get(key))
    return _dedupe_text(refs or _sequence(payload.get(key)))


def _stage_sequence(stage_id: str) -> int:
    return {
        "direction_and_route_selection": 1,
        "baseline_and_evidence_setup": 2,
        "bounded_analysis_campaign": 3,
        "manuscript_authoring": 4,
        "review_and_quality_gate": 5,
        "finalize_and_publication_handoff": 6,
    }.get(stage_id, 0)


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
    expected_receipt_refs = _stage_expected_receipt_refs(
        owner_receipt_refs=owner_receipt_refs,
        stable_blocker_refs=stable_blocker_refs,
        live_evidence_refs=live_evidence_refs,
        no_forbidden_write_ref=no_forbidden_write_ref,
    )
    monitor_freshness_refs = _stage_monitor_freshness_refs(
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


def _stage_expected_receipt_refs(
    *,
    owner_receipt_refs: Sequence[str],
    stable_blocker_refs: Sequence[str],
    live_evidence_refs: Mapping[str, Any],
    no_forbidden_write_ref: str | None,
) -> list[str]:
    return _dedupe_text(
        [
            *owner_receipt_refs,
            *_sequence(live_evidence_refs.get("progress_delta_refs")),
            *_sequence(live_evidence_refs.get("ai_reviewer_gate_receipt_refs")),
            *_sequence(live_evidence_refs.get("artifact_movement_refs")),
            *_sequence(live_evidence_refs.get("publication_route_memory_writeback_receipt_refs")),
            *_sequence(live_evidence_refs.get("artifact_lifecycle_receipt_refs")),
            *_sequence(live_evidence_refs.get("human_gate_or_resume_refs")),
            *stable_blocker_refs,
            *_sequence(live_evidence_refs.get("stable_typed_blocker_refs")),
            no_forbidden_write_ref,
        ]
    )


def _stage_monitor_freshness_refs(
    *,
    owner_receipt_refs: Sequence[str],
    stable_blocker_refs: Sequence[str],
    live_evidence_refs: Mapping[str, Any],
    no_forbidden_write_ref: str | None,
) -> list[str]:
    return _dedupe_text(
        [
            *_sequence(live_evidence_refs.get("progress_delta_refs")),
            *_sequence(live_evidence_refs.get("ai_reviewer_gate_receipt_refs")),
            *_sequence(live_evidence_refs.get("artifact_movement_refs")),
            *_sequence(live_evidence_refs.get("publication_route_memory_writeback_receipt_refs")),
            *_sequence(live_evidence_refs.get("artifact_lifecycle_receipt_refs")),
            *_sequence(live_evidence_refs.get("human_gate_or_resume_refs")),
            *stable_blocker_refs,
            *_sequence(live_evidence_refs.get("stable_typed_blocker_refs")),
            *owner_receipt_refs,
            no_forbidden_write_ref,
        ]
    )


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
