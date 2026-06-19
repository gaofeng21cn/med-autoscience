from __future__ import annotations

from collections.abc import Mapping
from typing import Any


SURFACE_KIND = "mas_live_runtime_gap_work_orders"
VERSION = "mas-live-runtime-gap-work-orders.v1"
FORBIDDEN_CLAIM_TERMS = (
    "domain-ready",
    "live runtime ready",
    "paper complete",
    "paper progress",
    "provider running",
    "publication-ready",
    "ready",
    "runtime ready",
    "production-ready",
)


def live_runtime_gap_work_orders_from_completion_audit(
    completion_audit: Mapping[str, Any],
) -> list[dict[str, Any]]:
    live_completion = _live_completion(completion_audit)
    gaps = live_completion.get("open_live_runtime_gaps")
    gap_list = gaps if isinstance(gaps, list) else []
    return [_work_order_from_gap(str(gap)) for gap in gap_list if _text(gap) is not None]


def validate_live_runtime_gap_work_order_contract(
    contract: Mapping[str, Any],
    completion_audit: Mapping[str, Any],
) -> list[dict[str, str]]:
    violations: list[dict[str, str]] = []
    if contract.get("surface_kind") != SURFACE_KIND:
        violations.append(_violation("<contract>", "surface_kind_mismatch"))
    if contract.get("version") != VERSION:
        violations.append(_violation("<contract>", "version_mismatch"))
    if contract.get("repo_source_retirement_blocked") is not False:
        violations.append(_violation("<contract>", "repo_source_retirement_blocked"))
    if contract.get("live_runtime_readiness_claim_allowed") is not False:
        violations.append(_violation("<contract>", "live_runtime_claim_allowed"))
    schema_forbidden_terms = set(
        _text_list(_evidence_record_schema(contract).get("forbidden_claim_terms"))
    )
    if not set(FORBIDDEN_CLAIM_TERMS).issubset(schema_forbidden_terms):
        violations.append(_violation("<contract>", "missing_forbidden_claim_terms"))

    expected = {
        order["gap_id"]: order
        for order in live_runtime_gap_work_orders_from_completion_audit(completion_audit)
    }
    raw_orders = contract.get("work_orders")
    orders = raw_orders if isinstance(raw_orders, list) else []
    observed = {
        str(order.get("gap_id")): order
        for order in orders
        if isinstance(order, Mapping) and _text(order.get("gap_id")) is not None
    }
    if set(observed) != set(expected):
        violations.append(_violation("<contract>", "work_order_gap_set_mismatch"))
    for gap_id, expected_order in expected.items():
        observed_order = observed.get(gap_id)
        if not isinstance(observed_order, Mapping):
            continue
        for key in (
            "gap_text",
            "status",
            "next_owner",
            "repo_source_retirement_blocked",
            "live_runtime_readiness_claim_allowed",
            "typed_blocker_when_missing",
        ):
            if observed_order.get(key) != expected_order.get(key):
                violations.append(_violation(gap_id, f"field_mismatch:{key}"))
        for key in ("acceptable_evidence_ref_families", "forbidden_evidence_substitutes"):
            if _text_list(observed_order.get(key)) != _text_list(expected_order.get(key)):
                violations.append(_violation(gap_id, f"list_mismatch:{key}"))
    return violations


def evaluate_live_runtime_gap_evidence_record(
    work_order: Mapping[str, Any],
    evidence_record: Mapping[str, Any],
) -> dict[str, Any]:
    gap_id = _text(work_order.get("gap_id")) or "<missing>"
    accepted_refs = set(_text_list(work_order.get("acceptable_evidence_ref_families")))
    forbidden_substitutes = set(_text_list(work_order.get("forbidden_evidence_substitutes")))
    provided_refs = set(_text_list(evidence_record.get("evidence_ref_families")))
    provided_substitutes = set(_text_list(evidence_record.get("evidence_substitutes")))
    matched_refs = sorted(accepted_refs & provided_refs)
    forbidden_matches = sorted(forbidden_substitutes & provided_substitutes)
    forbidden_claim_terms = _forbidden_claim_terms(work_order, evidence_record)
    evidence_source = _text(evidence_record.get("evidence_source"))
    typed_blocker = _text(work_order.get("typed_blocker_when_missing")) or (
        f"{gap_id}_live_runtime_evidence_required"
    )
    satisfied = (
        bool(matched_refs)
        and not forbidden_matches
        and not forbidden_claim_terms
        and evidence_source is not None
    )
    return {
        "gap_id": gap_id,
        "status": "satisfied_by_accepted_ref" if satisfied else "typed_blocker_required",
        "matched_evidence_ref_families": matched_refs,
        "forbidden_evidence_substitutes_present": forbidden_matches,
        "forbidden_claim_terms_present": forbidden_claim_terms,
        "typed_blocker": None if satisfied else typed_blocker,
        "live_runtime_readiness_claim_allowed": satisfied,
        "repo_source_retirement_blocked": False,
        "evidence_source": evidence_source,
    }


def live_runtime_gap_evidence_intake_summary(
    contract: Mapping[str, Any],
    evidence_records: list[Mapping[str, Any]] | Mapping[str, Any],
) -> dict[str, Any]:
    orders = {
        str(order.get("gap_id")): order
        for order in contract.get("work_orders", [])
        if isinstance(order, Mapping) and _text(order.get("gap_id")) is not None
    }
    records_iterable: list[Mapping[str, Any]]
    if isinstance(evidence_records, list):
        records_iterable = [record for record in evidence_records if isinstance(record, Mapping)]
    else:
        records_iterable = []
    records = {
        str(record.get("gap_id")): record
        for record in records_iterable
        if _text(record.get("gap_id")) is not None
    }
    forbidden_claim_terms = _evidence_record_schema(contract).get("forbidden_claim_terms", [])
    results = [
        evaluate_live_runtime_gap_evidence_record(
            order,
            {
                **records.get(gap_id, {}),
                "_forbidden_claim_terms": forbidden_claim_terms,
            },
        )
        for gap_id, order in sorted(orders.items())
    ]
    blocked = [
        result["gap_id"] for result in results if result["status"] == "typed_blocker_required"
    ]
    satisfied = [
        result["gap_id"] for result in results if result["status"] == "satisfied_by_accepted_ref"
    ]
    return {
        "surface_kind": "mas_live_runtime_gap_evidence_intake_summary",
        "total_work_order_count": len(orders),
        "satisfied_count": len(satisfied),
        "typed_blocker_count": len(blocked),
        "satisfied_gap_ids": satisfied,
        "typed_blocker_gap_ids": blocked,
        "repo_source_retirement_blocked": False,
        "live_runtime_readiness_claim_allowed": bool(orders) and not blocked,
        "results": results,
    }


def _live_completion(completion_audit: Mapping[str, Any]) -> Mapping[str, Any]:
    columns = completion_audit.get("completion_columns")
    if not isinstance(columns, Mapping):
        return {}
    live = columns.get("live_runtime_readiness_completion")
    return live if isinstance(live, Mapping) else {}


def _work_order_from_gap(gap: str) -> dict[str, Any]:
    gap_id = _gap_id(gap)
    return {
        "gap_id": gap_id,
        "gap_text": gap,
        "status": "evidence_required",
        "next_owner": _next_owner_for_gap(gap),
        "repo_source_retirement_blocked": False,
        "live_runtime_readiness_claim_allowed": False,
        "typed_blocker_when_missing": f"{gap_id}_live_runtime_evidence_required",
        "acceptable_evidence_ref_families": _acceptable_refs_for_gap(gap),
        "forbidden_evidence_substitutes": _forbidden_substitutes_for_gap(gap),
    }


def _acceptable_refs_for_gap(gap: str) -> list[str]:
    if "DHD apply" in gap:
        return [
            "DHD_apply_exactly_one_live_outcome_ref",
            "MAS_owner_receipt_or_stable_typed_blocker_or_human_gate_or_route_back_ref",
        ]
    if "paper-line accepted outcome" in gap:
        return [
            "fresh_DM002_DM003_paper_line_accepted_outcome_ref",
            "MAS_owner_receipt_or_stable_typed_blocker_or_human_gate_or_route_back_ref",
        ]
    if "provider-admission live readback" in gap:
        return [
            "same_identity_opl_provider_admission_live_readback_ref",
            "OPL_domain_progress_transition_runtime_live_readback_same_identity_ref",
        ]
    if "provider admission arbiter" in gap:
        return [
            "provider_admission_arbiter_consumes_opl_transition_event_ref",
            "OPL_command_event_outbox_live_readback_ref",
            "StageRun_identity_packet_currentness_ref",
        ]
    return [
        "OPL_domain_progress_transition_runtime_live_readback_same_identity_ref",
        "OPL_command_event_outbox_live_readback_ref",
        "StageRun_identity_packet_currentness_ref",
    ]


def _forbidden_substitutes_for_gap(gap: str) -> list[str]:
    common = [
        "repo_source_retirement_complete",
        "docs_updated",
        "contract_landed",
        "focused_tests_passed",
        "make_test_meta_passed",
        "scripts_verify_passed",
        "queue_empty",
        "DHD_dry_run",
        "provider_admission_pending_count=0",
        "transition_request_pending_count=0",
    ]
    if "replay fixture" in gap:
        common.append("provider_admission_same_identity_replay_as_fresh_opl_readback")
    if "paper-line" in gap:
        common.append("same_identity_readback_consumes_transition_request_as_paper_line_outcome")
    return common


def _next_owner_for_gap(gap: str) -> str:
    if "DHD apply" in gap:
        return "MAS DHD apply owner with OPL runtime authorization"
    if "provider admission arbiter" in gap:
        return "MAS provider-admission arbiter owner plus OPL transition runtime owner"
    if "provider-admission live readback" in gap:
        return "one-person-lab DomainProgressTransitionRuntime owner"
    if "paper-line accepted outcome" in gap:
        return "MAS study owner / paper-line owner"
    return "one-person-lab DomainProgressTransitionRuntime / StageRun owner"


def _gap_id(gap: str) -> str:
    text = gap.lower()
    chars = [ch if ch.isalnum() else "_" for ch in text]
    collapsed = "_".join(part for part in "".join(chars).split("_") if part)
    return collapsed[:96]


def _text_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return sorted(text for item in value if (text := _text(item)) is not None)
    text = _text(value)
    return [text] if text is not None else []


def _text(value: Any) -> str | None:
    text = str(value or "").strip()
    return text or None


def _evidence_record_schema(contract: Mapping[str, Any]) -> Mapping[str, Any]:
    boundary = contract.get("completion_claim_boundary")
    if not isinstance(boundary, Mapping):
        return {}
    schema = boundary.get("evidence_record_schema")
    return schema if isinstance(schema, Mapping) else {}


def _forbidden_claim_terms(
    work_order: Mapping[str, Any],
    evidence_record: Mapping[str, Any],
) -> list[str]:
    claim = (_text(evidence_record.get("claim")) or "").casefold()
    if not claim:
        return []
    terms = _text_list(
        evidence_record.get("_forbidden_claim_terms")
        or work_order.get("forbidden_claim_terms")
        or list(FORBIDDEN_CLAIM_TERMS)
    )
    return sorted(term for term in terms if term.casefold() in claim)


def _violation(gap_id: str, reason: str) -> dict[str, str]:
    return {"gap_id": gap_id, "reason": reason}


__all__ = [
    "SURFACE_KIND",
    "VERSION",
    "FORBIDDEN_CLAIM_TERMS",
    "evaluate_live_runtime_gap_evidence_record",
    "live_runtime_gap_evidence_intake_summary",
    "live_runtime_gap_work_orders_from_completion_audit",
    "validate_live_runtime_gap_work_order_contract",
]
