from __future__ import annotations

from collections.abc import Mapping
import re
from typing import Any


SURFACE_KIND = "mas_runtime_live_tail_work_orders"
VERSION = "mas-runtime-live-tail-work-orders.v1"
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
CONCRETE_EVIDENCE_REF_FIELDS = (
    "evidence_refs",
    "owner_receipt_ref",
    "typed_blocker_ref",
    "human_gate_ref",
    "route_back_ref",
)
AUTHORITY_OUTCOME_REQUIRED_OUTCOMES = (
    "owner_receipt_or_stable_typed_blocker_or_human_gate_or_route_back",
)
AUTHORITY_OUTCOME_REF_REQUIRED_FAMILIES = (
    "owner_receipt_or_stable_typed_blocker_or_human_gate_or_route_back_ref",
)
AUTHORITY_OUTCOME_REF_FIELDS = (
    "owner_receipt_ref",
    "typed_blocker_ref",
    "human_gate_ref",
    "route_back_ref",
)
ACCEPTED_EVIDENCE_SOURCE_PREFIXES = (
    "live_soak:",
    "mas_owner_gate:",
    "no_active_caller_scan:",
    "operator_readback:",
    "owner_readback:",
    "production_caller_scan:",
    "runtime_readback:",
)
FORBIDDEN_EVIDENCE_SOURCE_PREFIXES = (
    "DHD_dry_run",
    "contract_landed",
    "docs",
    "focused_tests",
    "make_test_meta",
    "queue_empty",
    "replay_fixture",
    "repo_source_retirement_complete",
    "repo_tests",
    "scripts_verify",
)


def live_tail_work_orders_from_audit(audit: Mapping[str, Any]) -> list[dict[str, Any]]:
    live_completion = audit.get("live_runtime_readiness_completion")
    if not isinstance(live_completion, Mapping):
        return []
    tails = live_completion.get("open_surface_tails")
    if not isinstance(tails, list):
        return []
    return [_work_order_from_tail(tail) for tail in tails if isinstance(tail, Mapping)]


def validate_live_tail_work_order_contract(
    contract: Mapping[str, Any],
    audit: Mapping[str, Any],
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
    schema = _evidence_record_schema(contract)
    schema_forbidden_terms = set(_text_list(schema.get("forbidden_claim_terms")))
    if not set(FORBIDDEN_CLAIM_TERMS).issubset(schema_forbidden_terms):
        violations.append(_violation("<contract>", "missing_forbidden_claim_terms"))
    if schema.get("unknown_evidence_record_id_status") != "typed_blocker_required":
        violations.append(_violation("<contract>", "missing_unknown_id_typed_blocker_status"))
    if schema.get("duplicate_evidence_record_id_status") != "typed_blocker_required":
        violations.append(_violation("<contract>", "missing_duplicate_id_typed_blocker_status"))
    if schema.get("unknown_or_duplicate_evidence_record_can_satisfy_work_order") is not False:
        violations.append(_violation("<contract>", "unknown_or_duplicate_can_satisfy_work_order"))
    if (
        schema.get("unknown_or_duplicate_evidence_record_blocks_live_runtime_readiness_claim")
        is not True
    ):
        violations.append(
            _violation("<contract>", "unknown_or_duplicate_does_not_block_live_readiness")
        )
    if schema.get("missing_evidence_record_id_status") != "typed_blocker_required":
        violations.append(_violation("<contract>", "missing_id_typed_blocker_status"))
    if schema.get("malformed_evidence_record_status") != "typed_blocker_required":
        violations.append(_violation("<contract>", "malformed_record_typed_blocker_status"))
    if schema.get("missing_or_malformed_evidence_record_can_satisfy_work_order") is not False:
        violations.append(_violation("<contract>", "missing_or_malformed_can_satisfy_work_order"))
    if (
        schema.get("missing_or_malformed_evidence_record_blocks_live_runtime_readiness_claim")
        is not True
    ):
        violations.append(
            _violation("<contract>", "missing_or_malformed_does_not_block_live_readiness")
        )
    if _text_list(schema.get("accepted_evidence_source_prefixes")) != list(
        ACCEPTED_EVIDENCE_SOURCE_PREFIXES
    ):
        violations.append(_violation("<contract>", "accepted_source_prefixes_mismatch"))
    if _text_list(schema.get("forbidden_evidence_source_prefixes")) != list(
        FORBIDDEN_EVIDENCE_SOURCE_PREFIXES
    ):
        violations.append(_violation("<contract>", "forbidden_source_prefixes_mismatch"))
    if schema.get("unaccepted_evidence_source_status") != "typed_blocker_required":
        violations.append(_violation("<contract>", "unaccepted_source_status_mismatch"))
    if schema.get("forbidden_evidence_source_status") != "typed_blocker_required":
        violations.append(_violation("<contract>", "forbidden_source_status_mismatch"))
    if schema.get("forbidden_or_unaccepted_source_can_satisfy_work_order") is not False:
        violations.append(_violation("<contract>", "forbidden_or_unaccepted_source_can_satisfy"))
    if (
        schema.get("forbidden_or_unaccepted_source_blocks_live_runtime_readiness_claim")
        is not True
    ):
        violations.append(
            _violation("<contract>", "forbidden_or_unaccepted_source_does_not_block")
        )
    if _text_list(schema.get("concrete_evidence_ref_fields")) != list(
        CONCRETE_EVIDENCE_REF_FIELDS
    ):
        violations.append(_violation("<contract>", "concrete_evidence_ref_fields_mismatch"))
    if _undeclared_concrete_evidence_ref_fields(schema):
        violations.append(_violation("<contract>", "undeclared_concrete_evidence_ref_fields"))
    if schema.get("missing_concrete_evidence_ref_status") != "typed_blocker_required":
        violations.append(_violation("<contract>", "missing_concrete_evidence_ref_status"))
    if schema.get("accepted_family_without_concrete_ref_can_satisfy_work_order") is not False:
        violations.append(
            _violation("<contract>", "accepted_family_without_concrete_ref_can_satisfy")
        )
    if (
        schema.get("missing_concrete_evidence_ref_blocks_live_runtime_readiness_claim")
        is not True
    ):
        violations.append(
            _violation("<contract>", "missing_concrete_ref_does_not_block_live_readiness")
        )
    accepted_outcomes = set(
        _text_list(_completion_claim_boundary(contract).get("accepted_outcomes"))
    )
    if accepted_outcomes & set(AUTHORITY_OUTCOME_REQUIRED_OUTCOMES):
        if (
            _text_list(schema.get("authority_outcome_ref_required_for_families"))
            != sorted(AUTHORITY_OUTCOME_REF_REQUIRED_FAMILIES)
        ):
            violations.append(_violation("<contract>", "authority_outcome_ref_families_mismatch"))
        if _text_list(schema.get("authority_outcome_ref_fields")) != list(
            AUTHORITY_OUTCOME_REF_FIELDS
        ):
            violations.append(_violation("<contract>", "authority_outcome_ref_fields_mismatch"))
        if schema.get("missing_authority_outcome_ref_status") != "typed_blocker_required":
            violations.append(_violation("<contract>", "missing_authority_outcome_ref_status"))
        if schema.get("authority_family_without_outcome_ref_can_satisfy_work_order") is not False:
            violations.append(
                _violation("<contract>", "authority_family_without_outcome_ref_can_satisfy")
            )
        if (
            schema.get("missing_authority_outcome_ref_blocks_live_runtime_readiness_claim")
            is not True
        ):
            violations.append(
                _violation(
                    "<contract>",
                    "missing_authority_outcome_ref_does_not_block_live_readiness",
                )
            )

    expected = {
        order["surface_id"]: order
        for order in live_tail_work_orders_from_audit(audit)
        if _text(order.get("surface_id")) is not None
    }
    raw_orders = contract.get("work_orders")
    orders = raw_orders if isinstance(raw_orders, list) else []
    observed = {
        str(order.get("surface_id")): order
        for order in orders
        if isinstance(order, Mapping) and _text(order.get("surface_id")) is not None
    }
    if set(observed) != set(expected):
        violations.append(_violation("<contract>", "work_order_surface_set_mismatch"))

    for surface_id, expected_order in expected.items():
        observed_order = observed.get(surface_id)
        if not isinstance(observed_order, Mapping):
            continue
        for key in (
            "status",
            "next_owner",
            "repo_source_retirement_blocked",
            "live_runtime_readiness_claim_allowed",
            "missing_evidence_status",
            "typed_blocker_when_missing",
        ):
            if observed_order.get(key) != expected_order.get(key):
                violations.append(_violation(surface_id, f"field_mismatch:{key}"))
        for key in (
            "acceptable_evidence_ref_families",
            "forbidden_evidence_substitutes",
        ):
            if sorted(str(item) for item in observed_order.get(key, [])) != sorted(
                str(item) for item in expected_order.get(key, [])
            ):
                violations.append(_violation(surface_id, f"list_mismatch:{key}"))
    return violations


def evaluate_live_tail_evidence_record(
    work_order: Mapping[str, Any],
    evidence_record: Mapping[str, Any],
) -> dict[str, Any]:
    surface_id = _text(work_order.get("surface_id")) or "<missing>"
    evidence_surface_id = _text(evidence_record.get("surface_id"))
    evidence_record_id_mismatch = (
        evidence_surface_id is not None and evidence_surface_id != surface_id
    )
    accepted_refs = _text_set(work_order.get("acceptable_evidence_ref_families"))
    forbidden_substitutes = _text_set(work_order.get("forbidden_evidence_substitutes"))
    provided_refs = _text_set(evidence_record.get("evidence_ref_families"))
    provided_substitutes = _text_set(evidence_record.get("evidence_substitutes"))

    matched_refs = sorted(accepted_refs & provided_refs)
    forbidden_matches = sorted(forbidden_substitutes & provided_substitutes)
    claim = _text(evidence_record.get("claim"))
    forbidden_claim_terms = _forbidden_claim_terms(work_order, evidence_record)
    concrete_ref_fields = _concrete_evidence_ref_fields_present(evidence_record)
    missing_authority_outcome_refs = _missing_authority_outcome_ref_families(
        matched_refs,
        evidence_record,
    )
    missing_concrete_evidence_ref_families = matched_refs if not concrete_ref_fields else []
    evidence_source = _text(evidence_record.get("evidence_source"))
    accepted_source_prefix = _accepted_evidence_source_prefix(evidence_source)
    forbidden_source_prefixes = _forbidden_evidence_source_prefixes(evidence_source)
    typed_blocker = _text(work_order.get("typed_blocker_when_missing")) or (
        f"{surface_id}_live_runtime_readiness_evidence_required"
    )
    satisfied = (
        bool(matched_refs)
        and not evidence_record_id_mismatch
        and not forbidden_matches
        and not forbidden_claim_terms
        and not missing_authority_outcome_refs
        and not missing_concrete_evidence_ref_families
        and accepted_source_prefix is not None
        and not forbidden_source_prefixes
    )
    return {
        "surface_id": surface_id,
        "evidence_record_surface_id": evidence_surface_id,
        "evidence_record_id_mismatch": evidence_record_id_mismatch,
        "status": "satisfied_by_accepted_ref" if satisfied else "typed_blocker_required",
        "matched_evidence_ref_families": matched_refs,
        "forbidden_evidence_substitutes_present": forbidden_matches,
        "forbidden_claim_terms_present": forbidden_claim_terms,
        "missing_authority_outcome_ref_families": missing_authority_outcome_refs,
        "authority_outcome_ref_fields_present": _authority_outcome_ref_fields_present(
            evidence_record
        ),
        "missing_concrete_evidence_ref_families": missing_concrete_evidence_ref_families,
        "concrete_evidence_ref_fields_present": concrete_ref_fields,
        "accepted_evidence_source_prefix": accepted_source_prefix,
        "forbidden_evidence_source_prefixes_present": forbidden_source_prefixes,
        "typed_blocker": None if satisfied else typed_blocker,
        "live_runtime_readiness_claim_allowed": satisfied,
        "repo_source_retirement_blocked": False,
        "claim": claim,
        "evidence_source": evidence_source,
    }


def live_tail_evidence_intake_summary(
    contract: Mapping[str, Any],
    evidence_records: list[Mapping[str, Any]],
) -> dict[str, Any]:
    orders = {
        str(order.get("surface_id")): order
        for order in contract.get("work_orders", [])
        if isinstance(order, Mapping) and _text(order.get("surface_id")) is not None
    }
    records, unknown_surface_ids, duplicate_surface_ids = _records_by_surface_id(
        evidence_records,
        orders,
    )
    malformed_record_indexes = _malformed_record_indexes(evidence_records)
    missing_surface_id_record_indexes = _missing_surface_id_record_indexes(evidence_records)
    results = [
        evaluate_live_tail_evidence_record(
            order,
            {
                **records.get(surface_id, {}),
                "_forbidden_claim_terms": _evidence_record_schema(contract).get(
                    "forbidden_claim_terms", []
                ),
            },
        )
        for surface_id, order in sorted(orders.items())
    ]
    satisfied = [
        result["surface_id"]
        for result in results
        if result["status"] == "satisfied_by_accepted_ref"
    ]
    blocked = [
        result["surface_id"]
        for result in results
        if result["status"] == "typed_blocker_required"
    ]
    intake_violations = [
        {
            "violation_id": f"unknown_surface_id:{surface_id}",
            "status": "typed_blocker_required",
            "surface_id": surface_id,
            "typed_blocker": "unknown_live_tail_evidence_surface_id",
        }
        for surface_id in unknown_surface_ids
    ] + [
        {
            "violation_id": f"duplicate_surface_id:{surface_id}",
            "status": "typed_blocker_required",
            "surface_id": surface_id,
            "typed_blocker": "duplicate_live_tail_evidence_surface_id",
        }
        for surface_id in duplicate_surface_ids
    ] + [
        {
            "violation_id": f"missing_surface_id_record:{index}",
            "status": "typed_blocker_required",
            "record_index": index,
            "typed_blocker": "missing_live_tail_evidence_surface_id",
        }
        for index in missing_surface_id_record_indexes
    ] + [
        {
            "violation_id": f"malformed_record:{index}",
            "status": "typed_blocker_required",
            "record_index": index,
            "typed_blocker": "malformed_live_tail_evidence_record",
        }
        for index in malformed_record_indexes
    ]
    return {
        "surface_kind": "mas_runtime_live_tail_evidence_intake_summary",
        "total_work_order_count": len(orders),
        "satisfied_count": len(satisfied),
        "typed_blocker_count": len(blocked) + len(intake_violations),
        "satisfied_surface_ids": satisfied,
        "typed_blocker_surface_ids": blocked,
        "intake_violation_count": len(intake_violations),
        "intake_violations": intake_violations,
        "unknown_surface_ids": unknown_surface_ids,
        "duplicate_surface_ids": duplicate_surface_ids,
        "missing_surface_id_record_indexes": missing_surface_id_record_indexes,
        "malformed_record_indexes": malformed_record_indexes,
        "repo_source_retirement_blocked": False,
        "live_runtime_readiness_claim_allowed": bool(orders)
        and not blocked
        and not intake_violations,
        "results": results,
    }


def _work_order_from_tail(tail: Mapping[str, Any]) -> dict[str, Any]:
    gate = tail.get("evidence_gate")
    gate_mapping = gate if isinstance(gate, Mapping) else {}
    surface_id = str(tail.get("surface_id"))
    return {
        "surface_id": surface_id,
        "status": "evidence_required",
        "next_owner": str(gate_mapping.get("next_owner", "surface owner")),
        "repo_source_retirement_blocked": False,
        "live_runtime_readiness_claim_allowed": False,
        "missing_evidence_status": str(
            gate_mapping.get("missing_evidence_status", "evidence_required")
        ),
        "typed_blocker_when_missing": f"{surface_id}_live_runtime_readiness_evidence_required",
        "acceptable_evidence_ref_families": sorted(
            str(item)
            for item in gate_mapping.get("acceptable_evidence_ref_families", [])
        ),
        "forbidden_evidence_substitutes": sorted(
            str(item)
            for item in gate_mapping.get("forbidden_evidence_substitutes", [])
        ),
    }


def _text(value: Any) -> str | None:
    text = str(value or "").strip()
    return text or None


def _text_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [text for item in value if (text := _text(item)) is not None]
    text = _text(value)
    return [text] if text is not None else []


def _text_set(value: Any) -> set[str]:
    if isinstance(value, list):
        return {text for item in value if (text := _text(item)) is not None}
    text = _text(value)
    return {text} if text is not None else set()


def _concrete_evidence_ref_fields_present(evidence_record: Mapping[str, Any]) -> list[str]:
    return sorted(
        field
        for field in CONCRETE_EVIDENCE_REF_FIELDS
        if _has_concrete_evidence_ref(evidence_record.get(field))
    )


def _has_concrete_evidence_ref(value: Any) -> bool:
    if isinstance(value, list):
        return any(_text(item) is not None for item in value)
    return _text(value) is not None


def _accepted_evidence_source_prefix(evidence_source: str | None) -> str | None:
    if evidence_source is None:
        return None
    return next(
        (
            prefix
            for prefix in ACCEPTED_EVIDENCE_SOURCE_PREFIXES
            if evidence_source.startswith(prefix)
        ),
        None,
    )


def _forbidden_evidence_source_prefixes(evidence_source: str | None) -> list[str]:
    if evidence_source is None:
        return []
    return [
        prefix
        for prefix in FORBIDDEN_EVIDENCE_SOURCE_PREFIXES
        if evidence_source.startswith(prefix)
    ]


def _authority_outcome_ref_fields_present(evidence_record: Mapping[str, Any]) -> list[str]:
    return sorted(
        field
        for field in AUTHORITY_OUTCOME_REF_FIELDS
        if _text(evidence_record.get(field)) is not None
    )


def _missing_authority_outcome_ref_families(
    matched_refs: list[str],
    evidence_record: Mapping[str, Any],
) -> list[str]:
    matched_required_families = sorted(
        set(AUTHORITY_OUTCOME_REF_REQUIRED_FAMILIES) & set(matched_refs)
    )
    if not matched_required_families:
        return []
    if _authority_outcome_ref_fields_present(evidence_record):
        return []
    return matched_required_families


def _undeclared_concrete_evidence_ref_fields(schema: Mapping[str, Any]) -> list[str]:
    declared_fields = set(_text_list(schema.get("required_fields"))) | set(
        _text_list(schema.get("optional_fields"))
    )
    return [
        field
        for field in _text_list(schema.get("concrete_evidence_ref_fields"))
        if field not in declared_fields
    ]


def _records_by_surface_id(
    evidence_records: list[Mapping[str, Any]],
    orders: Mapping[str, Mapping[str, Any]],
) -> tuple[dict[str, Mapping[str, Any]], list[str], list[str]]:
    records: dict[str, Mapping[str, Any]] = {}
    seen: set[str] = set()
    duplicate_surface_ids: set[str] = set()
    unknown_surface_ids: set[str] = set()
    for record in evidence_records:
        if not isinstance(record, Mapping):
            continue
        surface_id = _text(record.get("surface_id"))
        if surface_id is None:
            continue
        if surface_id in seen:
            duplicate_surface_ids.add(surface_id)
        else:
            records[surface_id] = record
            seen.add(surface_id)
        if surface_id not in orders:
            unknown_surface_ids.add(surface_id)
    return records, sorted(unknown_surface_ids), sorted(duplicate_surface_ids)


def _missing_surface_id_record_indexes(evidence_records: list[Any]) -> list[int]:
    return [
        index
        for index, record in enumerate(evidence_records)
        if isinstance(record, Mapping) and _text(record.get("surface_id")) is None
    ]


def _malformed_record_indexes(evidence_records: list[Any]) -> list[int]:
    return [
        index for index, record in enumerate(evidence_records) if not isinstance(record, Mapping)
    ]


def _evidence_record_schema(contract: Mapping[str, Any]) -> Mapping[str, Any]:
    boundary = _completion_claim_boundary(contract)
    schema = boundary.get("evidence_record_schema")
    return schema if isinstance(schema, Mapping) else {}


def _completion_claim_boundary(contract: Mapping[str, Any]) -> Mapping[str, Any]:
    boundary = contract.get("completion_claim_boundary")
    if not isinstance(boundary, Mapping):
        return {}
    return boundary


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
    return sorted(term for term in terms if _claim_contains_term(claim, term))


def _claim_contains_term(claim: str, term: str) -> bool:
    folded_term = term.casefold().strip()
    if not folded_term:
        return False
    pattern = rf"(?<![a-z0-9]){re.escape(folded_term)}(?![a-z0-9])"
    return re.search(pattern, claim) is not None


def _violation(surface_id: str, reason: str) -> dict[str, str]:
    return {"surface_id": surface_id, "reason": reason}


__all__ = [
    "SURFACE_KIND",
    "VERSION",
    "ACCEPTED_EVIDENCE_SOURCE_PREFIXES",
    "CONCRETE_EVIDENCE_REF_FIELDS",
    "FORBIDDEN_EVIDENCE_SOURCE_PREFIXES",
    "FORBIDDEN_CLAIM_TERMS",
    "evaluate_live_tail_evidence_record",
    "live_tail_evidence_intake_summary",
    "live_tail_work_orders_from_audit",
    "validate_live_tail_work_order_contract",
]
