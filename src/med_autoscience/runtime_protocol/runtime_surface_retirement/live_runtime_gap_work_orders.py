from __future__ import annotations

from collections.abc import Mapping
import re
from typing import Any

from med_autoscience.runtime_protocol.runtime_surface_retirement.surface_helpers import (
    _text,
    _text_list as _base_text_list,
)


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
AUTHORITY_OUTCOME_REF_REQUIRED_FAMILIES = (
    "MAS_owner_receipt_or_stable_typed_blocker_or_human_gate_or_route_back_ref",
)
AUTHORITY_OUTCOME_REF_FIELDS = (
    "owner_receipt_ref",
    "typed_blocker_ref",
    "human_gate_ref",
    "route_back_ref",
)
CONCRETE_EVIDENCE_REF_FIELDS = (
    "evidence_refs",
    "owner_receipt_ref",
    "typed_blocker_ref",
    "human_gate_ref",
    "route_back_ref",
)
ACCEPTED_EVIDENCE_SOURCE_PREFIXES = (
    "live_soak:",
    "mas_owner_gate:",
    "opl_live_readback:",
    "operator_readback:",
    "owner_readback:",
    "runtime_readback:",
)
FORBIDDEN_EVIDENCE_SOURCE_PREFIXES = (
    "domain_diagnostic_dry_run",
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
TRANSITION_IDENTITY_REF_REQUIRED_FAMILIES = (
    "domain_diagnostic_apply_exactly_one_live_outcome_ref",
    "MAS_owner_receipt_or_stable_typed_blocker_or_human_gate_or_route_back_ref",
    "OPL_command_event_outbox_live_readback_ref",
    "OPL_domain_progress_transition_runtime_live_readback_same_identity_ref",
    "StageRun_identity_packet_currentness_ref",
    "fresh_DM002_DM003_paper_line_accepted_outcome_ref",
    "provider_admission_arbiter_consumes_opl_transition_event_ref",
    "same_identity_opl_provider_admission_live_readback_ref",
)
TRANSITION_IDENTITY_REF_FIELDS = (
    "study_id",
    "work_unit_id",
    "work_unit_fingerprint",
    "route_identity_key",
    "attempt_idempotency_key",
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
    schema = _evidence_record_schema(contract)
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
    if _text_list(schema.get("accepted_evidence_source_prefixes")) != sorted(
        ACCEPTED_EVIDENCE_SOURCE_PREFIXES
    ):
        violations.append(_violation("<contract>", "accepted_source_prefixes_mismatch"))
    if _text_list(schema.get("forbidden_evidence_source_prefixes")) != sorted(
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
    if (
        _text_list(schema.get("authority_outcome_ref_required_for_families"))
        != sorted(AUTHORITY_OUTCOME_REF_REQUIRED_FAMILIES)
    ):
        violations.append(_violation("<contract>", "authority_outcome_ref_families_mismatch"))
    if (
        _text_list(schema.get("authority_outcome_ref_fields"))
        != sorted(AUTHORITY_OUTCOME_REF_FIELDS)
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
            _violation("<contract>", "missing_authority_outcome_ref_does_not_block_live_readiness")
        )
    if _text_list(schema.get("concrete_evidence_ref_fields")) != sorted(
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
    if _text_list(schema.get("transition_identity_ref_required_for_families")) != sorted(
        TRANSITION_IDENTITY_REF_REQUIRED_FAMILIES
    ):
        violations.append(_violation("<contract>", "transition_identity_ref_families_mismatch"))
    if _text_list(schema.get("transition_identity_ref_fields")) != sorted(
        TRANSITION_IDENTITY_REF_FIELDS
    ):
        violations.append(_violation("<contract>", "transition_identity_ref_fields_mismatch"))
    if schema.get("missing_transition_identity_ref_status") != "typed_blocker_required":
        violations.append(_violation("<contract>", "missing_transition_identity_ref_status"))
    if (
        schema.get("same_identity_family_without_transition_identity_can_satisfy_work_order")
        is not False
    ):
        violations.append(
            _violation("<contract>", "same_identity_without_transition_identity_can_satisfy")
        )
    if (
        schema.get("missing_transition_identity_ref_blocks_live_runtime_readiness_claim")
        is not True
    ):
        violations.append(
            _violation(
                "<contract>",
                "missing_transition_identity_ref_does_not_block_live_readiness",
            )
        )

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
    evidence_gap_id = _text(evidence_record.get("gap_id"))
    evidence_record_id_mismatch = evidence_gap_id is not None and evidence_gap_id != gap_id
    accepted_refs = set(_text_list(work_order.get("acceptable_evidence_ref_families")))
    forbidden_substitutes = set(_text_list(work_order.get("forbidden_evidence_substitutes")))
    provided_refs = set(_text_list(evidence_record.get("evidence_ref_families")))
    provided_substitutes = set(_text_list(evidence_record.get("evidence_substitutes")))
    matched_refs = sorted(accepted_refs & provided_refs)
    forbidden_matches = sorted(forbidden_substitutes & provided_substitutes)
    forbidden_claim_terms = _forbidden_claim_terms(work_order, evidence_record)
    missing_authority_outcome_refs = _missing_authority_outcome_ref_families(
        matched_refs,
        evidence_record,
    )
    concrete_ref_fields = _concrete_evidence_ref_fields_present(evidence_record)
    missing_concrete_evidence_ref_families = matched_refs if not concrete_ref_fields else []
    missing_transition_identity_ref_families = _missing_transition_identity_ref_families(
        matched_refs,
        evidence_record,
    )
    evidence_source = _text(evidence_record.get("evidence_source"))
    accepted_source_prefix = _accepted_evidence_source_prefix(evidence_source)
    forbidden_source_prefixes = _forbidden_evidence_source_prefixes(evidence_source)
    typed_blocker = _text(work_order.get("typed_blocker_when_missing")) or (
        f"{gap_id}_live_runtime_evidence_required"
    )
    satisfied = (
        bool(matched_refs)
        and not evidence_record_id_mismatch
        and not forbidden_matches
        and not forbidden_claim_terms
        and not missing_authority_outcome_refs
        and not missing_concrete_evidence_ref_families
        and not missing_transition_identity_ref_families
        and accepted_source_prefix is not None
        and not forbidden_source_prefixes
    )
    return {
        "gap_id": gap_id,
        "evidence_record_gap_id": evidence_gap_id,
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
        "missing_transition_identity_ref_families": missing_transition_identity_ref_families,
        "transition_identity_ref_fields_present": _transition_identity_ref_fields_present(
            evidence_record
        ),
        "accepted_evidence_source_prefix": accepted_source_prefix,
        "forbidden_evidence_source_prefixes_present": forbidden_source_prefixes,
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
    records_iterable: list[Any]
    if isinstance(evidence_records, list):
        records_iterable = list(evidence_records)
    else:
        records_iterable = []
    records, unknown_gap_ids, duplicate_gap_ids = _records_by_gap_id(
        records_iterable,
        orders,
    )
    malformed_record_indexes = _malformed_record_indexes(records_iterable)
    missing_gap_id_record_indexes = _missing_gap_id_record_indexes(records_iterable)
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
    intake_violations = [
        {
            "violation_id": f"unknown_gap_id:{gap_id}",
            "status": "typed_blocker_required",
            "gap_id": gap_id,
            "typed_blocker": "unknown_live_runtime_gap_evidence_gap_id",
        }
        for gap_id in unknown_gap_ids
    ] + [
        {
            "violation_id": f"duplicate_gap_id:{gap_id}",
            "status": "typed_blocker_required",
            "gap_id": gap_id,
            "typed_blocker": "duplicate_live_runtime_gap_evidence_gap_id",
        }
        for gap_id in duplicate_gap_ids
    ] + [
        {
            "violation_id": f"missing_gap_id_record:{index}",
            "status": "typed_blocker_required",
            "record_index": index,
            "typed_blocker": "missing_live_runtime_gap_evidence_gap_id",
        }
        for index in missing_gap_id_record_indexes
    ] + [
        {
            "violation_id": f"malformed_record:{index}",
            "status": "typed_blocker_required",
            "record_index": index,
            "typed_blocker": "malformed_live_runtime_gap_evidence_record",
        }
        for index in malformed_record_indexes
    ]
    return {
        "surface_kind": "mas_live_runtime_gap_evidence_intake_summary",
        "total_work_order_count": len(orders),
        "satisfied_count": len(satisfied),
        "typed_blocker_count": len(blocked) + len(intake_violations),
        "satisfied_gap_ids": satisfied,
        "typed_blocker_gap_ids": blocked,
        "intake_violation_count": len(intake_violations),
        "intake_violations": intake_violations,
        "unknown_gap_ids": unknown_gap_ids,
        "duplicate_gap_ids": duplicate_gap_ids,
        "missing_gap_id_record_indexes": missing_gap_id_record_indexes,
        "malformed_record_indexes": malformed_record_indexes,
        "repo_source_retirement_blocked": False,
        "live_runtime_readiness_claim_allowed": bool(orders)
        and not blocked
        and not intake_violations,
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
    if "domain diagnostic apply" in gap:
        return [
            "domain_diagnostic_apply_exactly_one_live_outcome_ref",
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
        "domain_diagnostic_dry_run",
        "provider_admission_pending_count=0",
        "transition_request_pending_count=0",
    ]
    if "replay fixture" in gap:
        common.append("provider_admission_same_identity_replay_as_fresh_opl_readback")
    if "paper-line" in gap:
        common.append("same_identity_readback_consumes_transition_request_as_paper_line_outcome")
    return common


def _next_owner_for_gap(gap: str) -> str:
    if "domain diagnostic apply" in gap:
        return "MAS domain diagnostic apply owner with OPL runtime authorization"
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
    return _base_text_list(value, sort=True)


def _authority_outcome_ref_fields_present(evidence_record: Mapping[str, Any]) -> list[str]:
    return sorted(
        field
        for field in AUTHORITY_OUTCOME_REF_FIELDS
        if _text(evidence_record.get(field)) is not None
    )


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


def _undeclared_concrete_evidence_ref_fields(schema: Mapping[str, Any]) -> list[str]:
    declared_fields = set(_text_list(schema.get("required_fields"))) | set(
        _text_list(schema.get("optional_fields"))
    )
    return [
        field
        for field in _text_list(schema.get("concrete_evidence_ref_fields"))
        if field not in declared_fields
    ]


def _missing_authority_outcome_ref_families(
    matched_refs: list[str],
    evidence_record: Mapping[str, Any],
) -> list[str]:
    required_families = set(AUTHORITY_OUTCOME_REF_REQUIRED_FAMILIES)
    matched_required_families = sorted(required_families & set(matched_refs))
    if not matched_required_families:
        return []
    if _authority_outcome_ref_fields_present(evidence_record):
        return []
    return matched_required_families


def _transition_identity_ref_fields_present(evidence_record: Mapping[str, Any]) -> list[str]:
    return sorted(
        field
        for field in TRANSITION_IDENTITY_REF_FIELDS
        if _text(evidence_record.get(field)) is not None
    )


def _missing_transition_identity_ref_families(
    matched_refs: list[str],
    evidence_record: Mapping[str, Any],
) -> list[str]:
    matched_required_families = sorted(
        set(TRANSITION_IDENTITY_REF_REQUIRED_FAMILIES) & set(matched_refs)
    )
    if not matched_required_families:
        return []
    if set(_transition_identity_ref_fields_present(evidence_record)) == set(
        TRANSITION_IDENTITY_REF_FIELDS
    ):
        return []
    return matched_required_families


def _records_by_gap_id(
    evidence_records: list[Any],
    orders: Mapping[str, Mapping[str, Any]],
) -> tuple[dict[str, Mapping[str, Any]], list[str], list[str]]:
    records: dict[str, Mapping[str, Any]] = {}
    seen: set[str] = set()
    duplicate_gap_ids: set[str] = set()
    unknown_gap_ids: set[str] = set()
    for record in evidence_records:
        if not isinstance(record, Mapping):
            continue
        gap_id = _text(record.get("gap_id"))
        if gap_id is None:
            continue
        if gap_id in seen:
            duplicate_gap_ids.add(gap_id)
        else:
            records[gap_id] = record
            seen.add(gap_id)
        if gap_id not in orders:
            unknown_gap_ids.add(gap_id)
    return records, sorted(unknown_gap_ids), sorted(duplicate_gap_ids)


def _missing_gap_id_record_indexes(evidence_records: list[Any]) -> list[int]:
    return [
        index
        for index, record in enumerate(evidence_records)
        if isinstance(record, Mapping) and _text(record.get("gap_id")) is None
    ]


def _malformed_record_indexes(evidence_records: list[Any]) -> list[int]:
    return [
        index for index, record in enumerate(evidence_records) if not isinstance(record, Mapping)
    ]


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
    return sorted(term for term in terms if _claim_contains_term(claim, term))


def _claim_contains_term(claim: str, term: str) -> bool:
    folded_term = term.casefold().strip()
    if not folded_term:
        return False
    pattern = rf"(?<![a-z0-9]){re.escape(folded_term)}(?![a-z0-9])"
    return re.search(pattern, claim) is not None


def _violation(gap_id: str, reason: str) -> dict[str, str]:
    return {"gap_id": gap_id, "reason": reason}


__all__ = [
    "SURFACE_KIND",
    "VERSION",
    "ACCEPTED_EVIDENCE_SOURCE_PREFIXES",
    "FORBIDDEN_CLAIM_TERMS",
    "AUTHORITY_OUTCOME_REF_FIELDS",
    "AUTHORITY_OUTCOME_REF_REQUIRED_FAMILIES",
    "CONCRETE_EVIDENCE_REF_FIELDS",
    "FORBIDDEN_EVIDENCE_SOURCE_PREFIXES",
    "TRANSITION_IDENTITY_REF_FIELDS",
    "TRANSITION_IDENTITY_REF_REQUIRED_FAMILIES",
    "evaluate_live_runtime_gap_evidence_record",
    "live_runtime_gap_evidence_intake_summary",
    "live_runtime_gap_work_orders_from_completion_audit",
    "validate_live_runtime_gap_work_order_contract",
]
