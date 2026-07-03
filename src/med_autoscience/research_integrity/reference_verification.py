from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from med_autoscience.research_integrity.gate_bundle import (
    authority_boundary as gate_authority_boundary,
    build_research_integrity_gate_input_bundle,
)
from med_autoscience.research_integrity.provider_lookup import (
    build_reference_provider_lookup_bundle,
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
    provider_evidence = _mapping_sequence(payload.get("provider_evidence")) + _provider_evidence_from_receipts(
        provider_receipts,
    )
    provider_receipt_refs = _provider_receipt_refs(provider_receipts)
    source_refs = _merge_ref_sequences(
        _ref_sequence(payload.get("source_refs")),
        _provider_receipt_source_refs(provider_receipts),
    )
    if provider_evidence:
        reference_checks = [
            {"reference": reference, "provider_evidence": list(_evidence_for_reference(reference, provider_evidence))}
            for reference in references
        ]
        gate_input = build_research_integrity_gate_input_bundle(
            reference_checks=reference_checks,
            **common_kwargs,
        )
        provider_lookup_bundle = None
        status = gate_input["status"]
        provider_summary = _provider_summary_from_evidence(reference_checks)
        boundary = _authority_boundary(external_provider_called=False)
    else:
        provider_lookup_bundle = build_reference_provider_lookup_bundle(
            references=references,
            provider_config=provider_config,
            **common_kwargs,
        )
        gate_input = provider_lookup_bundle["gate_input_bundle"]
        status = provider_lookup_bundle["status"]
        provider_summary = provider_lookup_bundle["provider_summary"]
        boundary = _authority_boundary(external_provider_called=True)

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
            "provider_lookup_bundle": provider_lookup_bundle,
            "research_integrity_gate_input_bundle": gate_input,
        },
        "blocker_candidates": gate_input["blocker_candidates"],
        "review_candidates": gate_input["review_candidates"],
        "authority_boundary": boundary,
    }


def _authority_boundary(*, external_provider_called: bool) -> dict[str, Any]:
    boundary = provider_lookup_authority_boundary() if external_provider_called else gate_authority_boundary()
    boundary["surface_role"] = "reference_verification_gate_input_only"
    boundary["can_call_external_provider"] = external_provider_called
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


def _evidence_for_reference(
    reference: Mapping[str, Any],
    provider_evidence: Sequence[Mapping[str, Any]],
) -> tuple[Mapping[str, Any], ...]:
    reference_id = _text(
        reference.get("reference_id")
        or reference.get("ref_id")
        or reference.get("id")
        or reference.get("ID")
        or reference.get("citation_key")
        or reference.get("key")
    )
    selected: list[Mapping[str, Any]] = []
    for evidence in provider_evidence:
        evidence_ref_id = _text(evidence.get("reference_id") or evidence.get("ref_id") or evidence.get("id"))
        if not evidence_ref_id or not reference_id or evidence_ref_id == reference_id:
            selected.append(evidence)
    return tuple(selected)


def _provider_evidence_from_receipts(
    provider_receipts: Sequence[Mapping[str, Any]],
) -> tuple[Mapping[str, Any], ...]:
    evidence: list[Mapping[str, Any]] = []
    for receipt in provider_receipts:
        receipt_ref = _provider_receipt_ref(receipt)
        source_refs = _receipt_source_refs(receipt)
        evidence.extend(
            _evidence_with_receipt_context(item, receipt_ref=receipt_ref, source_refs=source_refs)
            for item in _mapping_sequence(receipt.get("provider_evidence"))
        )
        for reference in _mapping_sequence(receipt.get("references")):
            reference_id = _reference_id(reference)
            evidence.extend(
                _evidence_with_receipt_context(
                    item,
                    receipt_ref=receipt_ref,
                    source_refs=source_refs,
                    reference_id=reference_id,
                )
                for item in _mapping_sequence(reference.get("provider_evidence"))
            )
        opl_connect = _optional_mapping(receipt.get("opl_connect_reference_verification")) or {}
        opl_source_refs = _merge_ref_sequences(source_refs, _ref_sequence(opl_connect.get("source_refs")))
        evidence.extend(
            _evidence_with_receipt_context(item, receipt_ref=receipt_ref, source_refs=opl_source_refs)
            for item in _mapping_sequence(opl_connect.get("provider_evidence"))
        )
    return tuple(evidence)


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


def _provider_receipt_refs(provider_receipts: Sequence[Mapping[str, Any]]) -> tuple[str, ...]:
    return tuple(ref for receipt in provider_receipts if (ref := _provider_receipt_ref(receipt)))


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


def _provider_summary_from_evidence(reference_checks: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    summary = {"found": 0, "not_found": 0, "error": 0}
    for check in reference_checks:
        for evidence in check.get("provider_evidence") or ():
            if not isinstance(evidence, Mapping):
                continue
            status = _text(evidence.get("lookup_status")) or "found"
            if status in summary:
                summary[status] += 1
            else:
                summary["found"] += 1
    return summary


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
]
