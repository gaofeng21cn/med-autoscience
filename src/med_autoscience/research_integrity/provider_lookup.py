from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import hashlib
import json
from typing import Any

from med_autoscience.research_integrity.gate_bundle import (
    authority_boundary as gate_authority_boundary,
    build_research_integrity_gate_input_bundle,
)
from med_autoscience.research_integrity.reference_authenticity import (
    build_reference_verification_attestation_dict,
)


SURFACE_KIND = "reference_provider_receipt_consumption_bundle"
SCHEMA_VERSION = "mas-reference-provider-receipt-consumption.v1"
DEFAULT_PROVIDERS = (
    "crossref",
    "pubmed",
    "pmc",
    "openalex",
    "semantic-scholar",
    "crossmark",
    "publisher",
)
SUPPORTED_LOOKUP_PROVIDERS = frozenset(DEFAULT_PROVIDERS)
PROVIDER_LOOKUP_MODE = "opl_connect_receipt_input_only"
PROVIDER_RESOLUTION_ACTION = "opl_connect_reference_verification"
AUTHORITATIVE_PROVIDER_TRUTH_OWNER = "external provider source systems"


@dataclass(frozen=True)
class ProviderLookupConfig:
    """Requested OPL Connect providers, not a MAS transport configuration."""

    providers: tuple[str, ...] = DEFAULT_PROVIDERS

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any] | None = None) -> ProviderLookupConfig:
        payload = payload or {}
        raw_providers = payload.get("providers") or payload.get("provider") or DEFAULT_PROVIDERS
        if isinstance(raw_providers, str):
            raw_providers = (raw_providers,)
        if not isinstance(raw_providers, Sequence) or isinstance(raw_providers, (bytes, bytearray)):
            raise ValueError("provider lookup `providers` must be a string or string sequence")
        return cls(providers=tuple(_provider_name(provider) for provider in raw_providers))


def build_reference_provider_receipt_consumption_bundle(
    *,
    references: Sequence[Mapping[str, Any]] | Mapping[str, Any],
    provider_evidence: Sequence[Mapping[str, Any]] = (),
    provider_config: Mapping[str, Any] | ProviderLookupConfig | None = None,
    claim_spans: Sequence[Mapping[str, Any]] = (),
    citation_refs: Sequence[Mapping[str, Any] | str] = (),
    evidence_refs: Sequence[Mapping[str, Any] | str] = (),
    reference_attestation_refs: Sequence[Mapping[str, Any] | str] = (),
    manuscript_sections: Mapping[str, Any] | None = None,
    numeric_facts: object = (),
    display_facts: object = (),
    reporting_checklist_expectations: object = (),
) -> dict[str, Any]:
    """Apply MAS integrity judgment to host-supplied OPL Connect evidence."""

    config = _config(provider_config)
    normalized_references = [_reference_with_id(reference) for reference in _reference_sequence(references)]
    normalized_evidence = [dict(item) for item in _mapping_sequence(provider_evidence)]
    checks = [
        {
            "reference": reference,
            "provider_evidence": list(_evidence_for_reference(reference, normalized_evidence)),
        }
        for reference in normalized_references
    ]
    attestations = [
        {
            "reference_id": str(check["reference"]["id"]),
            "reference": check["reference"],
            "provider_evidence": check["provider_evidence"],
            "attestation": build_reference_verification_attestation_dict(
                check["reference"],
                check["provider_evidence"],
            ),
        }
        for check in checks
    ]
    gate_input = build_research_integrity_gate_input_bundle(
        reference_checks=checks,
        claim_spans=claim_spans,
        citation_refs=citation_refs,
        evidence_refs=evidence_refs,
        reference_attestation_refs=reference_attestation_refs,
        manuscript_sections=manuscript_sections,
        numeric_facts=numeric_facts,
        display_facts=display_facts,
        reporting_checklist_expectations=reporting_checklist_expectations,
    )
    missing_evidence_ids = [
        str(check["reference"]["id"])
        for check in checks
        if not check["provider_evidence"]
    ]
    return {
        "surface_kind": SURFACE_KIND,
        "schema_version": SCHEMA_VERSION,
        "provider_lookup_mode": PROVIDER_LOOKUP_MODE,
        "provider_resolution_action": PROVIDER_RESOLUTION_ACTION,
        "provider_evidence_input_only": True,
        "provider_receipt_required": bool(missing_evidence_ids),
        "missing_provider_evidence_reference_ids": missing_evidence_ids,
        "live_provider_authority_claimed": False,
        "authoritative_provider_truth_owner": AUTHORITATIVE_PROVIDER_TRUTH_OWNER,
        "status": gate_input["status"],
        "providers": list(config.providers),
        "references": attestations,
        "provider_summary": _provider_summary(attestations),
        "gate_input_bundle": gate_input,
        "authority_boundary": provider_lookup_authority_boundary(),
    }


def select_reference_provider_evidence(
    reference: Mapping[str, Any],
    *,
    provider_evidence: Sequence[Mapping[str, Any]] = (),
) -> list[dict[str, Any]]:
    normalized = _reference_with_id(reference)
    return [
        dict(item)
        for item in _evidence_for_reference(normalized, _mapping_sequence(provider_evidence))
    ]


def provider_lookup_authority_boundary() -> dict[str, Any]:
    boundary = gate_authority_boundary()
    boundary.update(
        {
            "surface_role": "domain_consumes_opl_connect_provider_receipts",
            "provider_lookup_owner": "OPL Connect",
            "provider_lookup_mode": PROVIDER_LOOKUP_MODE,
            "provider_resolution_action": PROVIDER_RESOLUTION_ACTION,
            "provider_evidence_input_only": True,
            "live_provider_authority_claimed": False,
            "authoritative_provider_truth_owner": AUTHORITATIVE_PROVIDER_TRUTH_OWNER,
            "mas_can_call_external_provider": False,
            "can_call_external_provider": False,
            "can_invoke_opl_connect": False,
            "can_claim_live_provider_truth": False,
            "can_be_used_as_authoritative_provider_truth_without_owner_consumption": False,
            "can_write_provider_attempt": False,
            "can_write_provider_cache": False,
            "can_materialize_provider_receipt": False,
            "can_assert_publisher_or_crossmark_status_without_provider_receipt": False,
        }
    )
    return boundary


def _config(value: Mapping[str, Any] | ProviderLookupConfig | None) -> ProviderLookupConfig:
    if isinstance(value, ProviderLookupConfig):
        return value
    return ProviderLookupConfig.from_mapping(value)


def _provider_name(value: object) -> str:
    provider = str(value or "").strip().lower().replace("_", "-")
    if provider not in SUPPORTED_LOOKUP_PROVIDERS:
        raise ValueError(f"unsupported provider lookup provider: {provider}")
    return provider


def _reference_sequence(
    references: Sequence[Mapping[str, Any]] | Mapping[str, Any],
) -> list[Mapping[str, Any]]:
    if isinstance(references, Mapping):
        return [references]
    if not isinstance(references, Sequence) or isinstance(references, (str, bytes)):
        raise ValueError("references must be a mapping or sequence of mappings")
    if not all(isinstance(reference, Mapping) for reference in references):
        raise ValueError("references must contain mappings")
    return list(references)


def _mapping_sequence(value: object) -> tuple[Mapping[str, Any], ...]:
    if value is None:
        return ()
    if isinstance(value, Mapping):
        return (value,)
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        result = tuple(item for item in value if isinstance(item, Mapping))
        if len(result) == len(value):
            return result
    raise ValueError("provider evidence must be a mapping or mapping sequence")


def _evidence_for_reference(
    reference: Mapping[str, Any],
    provider_evidence: Sequence[Mapping[str, Any]],
) -> tuple[Mapping[str, Any], ...]:
    reference_id = _text(reference.get("id") or reference.get("reference_id"))
    return tuple(
        evidence
        for evidence in provider_evidence
        if not (evidence_id := _text(evidence.get("reference_id") or evidence.get("id")))
        or not reference_id
        or evidence_id == reference_id
    )


def _reference_with_id(reference: Mapping[str, Any]) -> dict[str, Any]:
    payload = dict(reference)
    reference_id = _text(payload.get("id")) or _text(payload.get("reference_id"))
    if reference_id is None:
        digest = hashlib.sha256(
            json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
        ).hexdigest()[:12]
        reference_id = f"ref_{digest}"
    payload["id"] = reference_id
    return payload


def _provider_summary(references: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    counts = {"found": 0, "not_found": 0, "error": 0}
    for reference in references:
        for evidence in reference.get("provider_evidence", []):
            if not isinstance(evidence, Mapping):
                continue
            status = str(evidence.get("lookup_status") or "found")
            counts[status if status in counts else "error"] += 1
    return counts


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "AUTHORITATIVE_PROVIDER_TRUTH_OWNER",
    "DEFAULT_PROVIDERS",
    "PROVIDER_LOOKUP_MODE",
    "PROVIDER_RESOLUTION_ACTION",
    "ProviderLookupConfig",
    "SCHEMA_VERSION",
    "SUPPORTED_LOOKUP_PROVIDERS",
    "SURFACE_KIND",
    "build_reference_provider_receipt_consumption_bundle",
    "select_reference_provider_evidence",
    "provider_lookup_authority_boundary",
]
