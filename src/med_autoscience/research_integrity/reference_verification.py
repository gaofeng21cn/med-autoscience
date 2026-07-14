from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from med_autoscience.research_integrity.provider_lookup import (
    build_reference_provider_receipt_consumption_bundle,
    provider_lookup_authority_boundary,
)


SURFACE_KIND = "research_integrity_reference_verification_gate_input_bundle"
SCHEMA_VERSION = 1


def build_reference_verification_payload(
    *,
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    if not isinstance(payload, Mapping):
        raise ValueError("reference verification `payload` 必须是 mapping。")
    references = _references(payload)
    if not references:
        raise ValueError("reference verification requires `reference` or `references`.")
    provider_config = _optional_mapping(payload.get("provider_config")) or {}
    common_kwargs = {
        "claim_spans": _mapping_sequence(_first_present(payload, "claim_spans", "claims", "claim")),
        "citation_refs": _ref_sequence(payload.get("citation_refs")),
        "evidence_refs": _ref_sequence(payload.get("evidence_refs")),
        "reference_attestation_refs": _ref_sequence(
            _first_present(payload, "reference_attestation_refs", "reference_attestations"),
        ),
        "manuscript_sections": _optional_mapping(_first_present(payload, "manuscript_sections", "manuscript")),
        "numeric_facts": _first_present(payload, "numeric_facts") or (),
        "display_facts": _first_present(payload, "display_facts", "display_to_claim_map") or (),
        "reporting_checklist_expectations": (
            _first_present(payload, "reporting_checklist_expectations", "reporting_guideline_expectations") or ()
        ),
    }
    provider_receipts = _mapping_sequence(payload.get("provider_receipts"))
    receipt_evidence = provider_evidence_from_receipts(provider_receipts)
    provider_evidence = _mapping_sequence(payload.get("provider_evidence")) + receipt_evidence
    provider_receipt_refs = _provider_receipt_refs(provider_receipts, receipt_evidence=receipt_evidence)
    source_refs = _merge_ref_sequences(
        _ref_sequence(payload.get("source_refs")),
        _provider_receipt_source_refs(provider_receipts),
    )
    provider_receipt_consumption = build_reference_provider_receipt_consumption_bundle(
        references=references,
        provider_evidence=provider_evidence,
        provider_config=provider_config,
        **common_kwargs,
    )
    gate_input = provider_receipt_consumption["gate_input_bundle"]
    status = provider_receipt_consumption["status"]
    provider_summary = provider_receipt_consumption["provider_summary"]
    boundary = _authority_boundary()

    return {
        "surface_kind": SURFACE_KIND,
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "reference_count": len(references),
        "source_refs": source_refs,
        "provider_receipt_refs": provider_receipt_refs,
        "reference_manager_ref": _text(payload.get("reference_manager_ref")),
        "manuscript_ref": _text(payload.get("manuscript_ref")),
        "provider_summary": provider_summary,
        "surfaces": {
            "provider_receipt_consumption_bundle": provider_receipt_consumption,
            "research_integrity_gate_input_bundle": gate_input,
        },
        "blocker_candidates": gate_input["blocker_candidates"],
        "review_candidates": gate_input["review_candidates"],
        "authority_boundary": boundary,
    }


def _authority_boundary() -> dict[str, Any]:
    boundary = provider_lookup_authority_boundary()
    boundary["surface_role"] = "reference_verification_gate_input_only"
    boundary["can_call_external_provider"] = False
    boundary["can_invoke_opl_connect"] = False
    boundary["can_write_provider_lookup_cache_or_receipt"] = False
    boundary["can_write_provider_attempt"] = False
    boundary["can_write_owner_receipt"] = False
    boundary["can_sign_owner_receipt"] = False
    boundary["can_run_independent_professional_skill"] = False
    return boundary


def _references(payload: Mapping[str, Any]) -> tuple[Mapping[str, Any], ...]:
    values = _mapping_sequence(payload.get("references"))
    if values:
        return values
    return _mapping_sequence(payload.get("reference"))


def provider_evidence_from_receipts(
    provider_receipts: Sequence[Mapping[str, Any]],
) -> tuple[Mapping[str, Any], ...]:
    """Normalize evidence carried by OPL Connect receipts without invoking transport."""

    evidence: list[Mapping[str, Any]] = []
    for receipt in provider_receipts:
        receipt_ref = _provider_receipt_ref(receipt)
        source_refs = _receipt_source_refs(receipt)
        _extend_receipt_evidence(
            evidence,
            _mapping_sequence(receipt.get("provider_evidence")),
            receipt_ref=receipt_ref,
            source_refs=source_refs,
        )
        for reference in _mapping_sequence(receipt.get("references")):
            reference_id = _reference_id(reference)
            _extend_receipt_evidence(
                evidence,
                _mapping_sequence(reference.get("provider_evidence")),
                receipt_ref=receipt_ref,
                source_refs=source_refs,
                reference_id=reference_id,
            )
        opl_connect = _optional_mapping(receipt.get("opl_connect_reference_verification")) or {}
        opl_source_refs = _merge_ref_sequences(source_refs, _ref_sequence(opl_connect.get("source_refs")))
        _extend_receipt_evidence(
            evidence,
            _mapping_sequence(opl_connect.get("provider_evidence")),
            receipt_ref=receipt_ref,
            source_refs=opl_source_refs,
        )
    return tuple(evidence)


def _extend_receipt_evidence(
    target: list[Mapping[str, Any]],
    candidates: Sequence[Mapping[str, Any]],
    *,
    receipt_ref: str | None,
    source_refs: Sequence[Mapping[str, Any] | str],
    reference_id: str | None = None,
) -> None:
    for candidate in candidates:
        normalized = _evidence_with_receipt_context(
            candidate,
            receipt_ref=receipt_ref,
            source_refs=source_refs,
            reference_id=reference_id,
        )
        if _text(normalized.get("receipt_ref")):
            target.append(normalized)


def _evidence_with_receipt_context(
    evidence: Mapping[str, Any],
    *,
    receipt_ref: str | None,
    source_refs: Sequence[Mapping[str, Any] | str],
    reference_id: str | None = None,
) -> Mapping[str, Any]:
    normalized = dict(evidence)
    if reference_id and not _reference_id(normalized):
        normalized["reference_id"] = reference_id
    if receipt_ref and not _text(normalized.get("receipt_ref")):
        normalized["receipt_ref"] = receipt_ref
    if source_refs:
        normalized["source_refs"] = list(
            _merge_ref_sequences(_ref_sequence(normalized.get("source_refs")), source_refs)
        )
    return normalized


def _provider_receipt_refs(
    provider_receipts: Sequence[Mapping[str, Any]],
    *,
    receipt_evidence: Sequence[Mapping[str, Any]],
) -> tuple[str, ...]:
    refs: list[str] = []
    for receipt in provider_receipts:
        if ref := _provider_receipt_ref(receipt):
            refs.append(ref)
        opl_connect = _optional_mapping(receipt.get("opl_connect_reference_verification")) or {}
        refs.extend(
            ref
            for nested in _mapping_sequence(opl_connect.get("provider_receipts"))
            if (ref := _provider_receipt_ref(nested))
        )
    refs.extend(
        ref
        for evidence in receipt_evidence
        if (ref := _text(evidence.get("receipt_ref")))
    )
    return tuple(dict.fromkeys(refs))


def _provider_receipt_source_refs(
    provider_receipts: Sequence[Mapping[str, Any]],
) -> tuple[Mapping[str, Any] | str, ...]:
    refs: list[Mapping[str, Any] | str] = []
    for receipt in provider_receipts:
        refs.extend(_receipt_source_refs(receipt))
        opl_connect = _optional_mapping(receipt.get("opl_connect_reference_verification")) or {}
        refs.extend(_ref_sequence(opl_connect.get("source_refs")))
    return _merge_ref_sequences(refs)


def _receipt_source_refs(receipt: Mapping[str, Any]) -> tuple[Mapping[str, Any] | str, ...]:
    return _merge_ref_sequences(_ref_sequence(receipt.get("source_refs")), _ref_sequence(receipt.get("source_ref")))


def _provider_receipt_ref(receipt: Mapping[str, Any]) -> str | None:
    return _text(
        receipt.get("receipt_ref")
        or receipt.get("provider_receipt_ref")
        or receipt.get("ref")
        or receipt.get("uri")
        or receipt.get("path")
    )


def _reference_id(reference: Mapping[str, Any]) -> str | None:
    return _text(
        reference.get("reference_id")
        or reference.get("ref_id")
        or reference.get("id")
        or reference.get("ID")
        or reference.get("citation_key")
        or reference.get("key")
    )


def _first_present(payload: Mapping[str, Any], *field_names: str) -> Any:
    for field_name in field_names:
        if field_name in payload:
            return payload[field_name]
    return None


def _mapping_sequence(value: Any) -> tuple[Mapping[str, Any], ...]:
    if value is None:
        return ()
    if isinstance(value, Mapping):
        return (value,)
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        result = tuple(item for item in value if isinstance(item, Mapping))
        if len(result) == len(value):
            return result
    raise ValueError("reference verification field must be a mapping or mapping array.")


def _ref_sequence(value: Any) -> tuple[Mapping[str, Any] | str, ...]:
    if value is None:
        return ()
    if isinstance(value, (str, Mapping)):
        return (value,)
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray)):
        result = tuple(item for item in value if isinstance(item, (str, Mapping)))
        if len(result) == len(value):
            return result
    raise ValueError("reference verification ref field must contain strings or mappings.")


def _merge_ref_sequences(
    *sequences: Sequence[Mapping[str, Any] | str],
) -> tuple[Mapping[str, Any] | str, ...]:
    refs: list[Mapping[str, Any] | str] = []
    seen: set[str] = set()
    for sequence in sequences:
        for ref in sequence:
            key = repr(ref)
            if key not in seen:
                refs.append(ref)
                seen.add(key)
    return tuple(refs)


def _optional_mapping(value: Any) -> Mapping[str, Any] | None:
    if value is None:
        return None
    if isinstance(value, Mapping):
        return value
    raise ValueError("reference verification optional mapping field must be a mapping.")


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "SCHEMA_VERSION",
    "SURFACE_KIND",
    "build_reference_verification_payload",
    "provider_evidence_from_receipts",
]
