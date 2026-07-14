from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict
from typing import Any

from med_autoscience.literature_records import LiteratureRecord
from med_autoscience.research_integrity.provider_lookup import PROVIDER_RESOLUTION_ACTION
from med_autoscience.research_integrity.provider_lookup import provider_lookup_authority_boundary
from med_autoscience.research_integrity.reference_verification import (
    build_reference_verification_payload,
    provider_evidence_from_receipts,
)


SURFACE_KIND = "mas_literature_opl_connect_receipt_resolution.v1"
SUPPORTED_REQUEST_PROVIDERS = (
    "crossref",
    "pubmed",
    "pmc",
    "openalex",
    "semantic-scholar",
    "crossmark",
    "publisher",
)


def resolve_literature_records_from_receipts(
    *,
    references: Sequence[Mapping[str, Any]],
    provider_receipts: Sequence[Mapping[str, Any]] = (),
    providers: Sequence[str] = SUPPORTED_REQUEST_PROVIDERS,
    accepted_evidence_providers: Sequence[str] | None = None,
    relevance_role: str = "candidate",
    claim_support_scope: Sequence[str] = (),
) -> dict[str, Any]:
    """Resolve metadata from host-supplied receipts and emit a request when evidence is absent."""

    normalized_references = tuple(_reference(reference, index=index) for index, reference in enumerate(references))
    normalized_receipts = tuple(_mapping(receipt, field="provider_receipts") for receipt in provider_receipts)
    normalized_providers = tuple(_provider(provider) for provider in providers)
    accepted_providers = (
        {_provider(provider) for provider in accepted_evidence_providers}
        if accepted_evidence_providers is not None
        else None
    )
    if not normalized_references:
        return {
            "surface_kind": SURFACE_KIND,
            "status": "resolved",
            "records": [],
            "provider_receipt_refs": [],
            "source_refs": [],
            "missing_provider_evidence_reference_ids": [],
            "provider_resolution_request": {
                "action_id": PROVIDER_RESOLUTION_ACTION,
                "request_only": True,
                "references": [],
                "providers": list(normalized_providers),
            },
            "authority_boundary": {
                **provider_lookup_authority_boundary(),
                "provider_lookup_owner": "OPL Connect",
                "provider_evidence_input_only": True,
                "mas_can_call_external_provider": False,
                "can_materialize_provider_receipt": False,
            },
        }
    verification = build_reference_verification_payload(
        payload={
            "references": normalized_references,
            "provider_receipts": normalized_receipts,
            "provider_config": {"providers": normalized_providers},
        }
    )
    evidence = provider_evidence_from_receipts(normalized_receipts)
    evidence_by_reference = _evidence_by_reference(evidence, accepted_providers=accepted_providers)
    records: list[LiteratureRecord] = []
    missing_reference_ids: list[str] = []
    for reference in normalized_references:
        reference_id = str(reference["id"])
        record = _record_from_evidence(
            reference=reference,
            evidence=evidence_by_reference.get(reference_id, ()),
            relevance_role=relevance_role,
            claim_support_scope=tuple(_text(item) for item in claim_support_scope if _text(item)),
        )
        if record is None:
            missing_reference_ids.append(reference_id)
        else:
            records.append(record)

    if not missing_reference_ids:
        status = "resolved"
    elif not normalized_receipts:
        status = "request_only"
    else:
        status = "missing_evidence"
    return {
        "surface_kind": SURFACE_KIND,
        "status": status,
        "records": [asdict(record) for record in records],
        "provider_receipt_refs": list(verification["provider_receipt_refs"]),
        "source_refs": list(verification["source_refs"]),
        "missing_provider_evidence_reference_ids": missing_reference_ids,
        "provider_resolution_request": {
            "action_id": PROVIDER_RESOLUTION_ACTION,
            "request_only": True,
            "references": [dict(reference) for reference in normalized_references if str(reference["id"]) in missing_reference_ids],
            "providers": list(normalized_providers),
        },
        "authority_boundary": {
            **dict(verification["authority_boundary"]),
            "provider_lookup_owner": "OPL Connect",
            "provider_evidence_input_only": True,
            "mas_can_call_external_provider": False,
            "can_materialize_provider_receipt": False,
        },
    }


def records_from_resolution(resolution: Mapping[str, Any]) -> tuple[LiteratureRecord, ...]:
    records = resolution.get("records")
    if not isinstance(records, Sequence) or isinstance(records, (str, bytes, bytearray)):
        raise ValueError("literature receipt resolution requires a records array")
    return tuple(LiteratureRecord(**dict(_mapping(record, field="records"))) for record in records)


def _reference(reference: Mapping[str, Any], *, index: int) -> dict[str, Any]:
    normalized = dict(_mapping(reference, field="references"))
    reference_id = _text(
        normalized.get("id")
        or normalized.get("reference_id")
        or normalized.get("record_id")
        or normalized.get("pmid")
        or normalized.get("pmcid")
        or normalized.get("doi")
    )
    normalized["id"] = reference_id or f"reference-{index + 1}"
    return normalized


def _evidence_by_reference(
    evidence: Sequence[Mapping[str, Any]],
    *,
    accepted_providers: set[str] | None,
) -> dict[str, tuple[Mapping[str, Any], ...]]:
    grouped: dict[str, list[Mapping[str, Any]]] = {}
    for item in evidence:
        provider = _provider(item.get("provider_id") or item.get("provider"))
        if accepted_providers is not None and provider not in accepted_providers:
            continue
        reference_id = _text(item.get("reference_id") or item.get("ref_id"))
        if reference_id:
            grouped.setdefault(reference_id, []).append(item)
    return {reference_id: tuple(items) for reference_id, items in grouped.items()}


def _record_from_evidence(
    *,
    reference: Mapping[str, Any],
    evidence: Sequence[Mapping[str, Any]],
    relevance_role: str,
    claim_support_scope: tuple[str, ...],
) -> LiteratureRecord | None:
    for item in evidence:
        if not _usable_evidence(item) or not _identifiers_match_reference(reference, item):
            continue
        metadata = _optional_mapping(item.get("metadata")) or {}
        normalized = _optional_mapping(item.get("normalized")) or {}
        identifiers = _optional_mapping(item.get("provider_identifiers")) or {}
        matched_identifiers = _optional_mapping(item.get("matched_identifiers")) or {}
        doi = _first_text(normalized, matched_identifiers, identifiers, reference, keys=("doi", "DOI"))
        pmid = _first_text(normalized, matched_identifiers, identifiers, reference, keys=("pmid", "PMID", "PubMed"))
        pmcid = _first_text(normalized, matched_identifiers, identifiers, reference, keys=("pmcid", "PMCID", "PMC"))
        title = _first_text(metadata, normalized, reference, keys=("title",))
        if not title:
            continue
        abstract = _first_text(metadata, keys=("abstract",))
        provider = _provider(item.get("provider_id") or item.get("provider"))
        provider_record_id = _first_text(
            identifiers,
            keys=("semantic_scholar", "semantic_scholar_id", "paperId", "openalex"),
        )
        return LiteratureRecord(
            record_id=_record_id(
                reference=reference,
                provider=provider,
                provider_record_id=provider_record_id,
                doi=doi,
                pmid=pmid,
                pmcid=pmcid,
            ),
            title=title,
            authors=_authors(metadata.get("authors")),
            year=_year(metadata.get("year")),
            journal=_first_text(metadata, keys=("journal", "venue")),
            doi=doi,
            pmid=pmid,
            pmcid=pmcid.removeprefix("PMC") if pmcid and pmcid.upper().startswith("PMC") else pmcid,
            arxiv_id=_first_text(identifiers, reference, keys=("arxiv_id", "ArXiv")),
            abstract=abstract,
            full_text_availability=_full_text_availability(item, abstract=abstract),
            source_priority=_source_priority(provider),
            citation_payload={
                "provider": provider,
                "receipt_ref": _text(item.get("receipt_ref")),
                "opl_connect_provider_evidence": dict(item),
            },
            local_asset_paths=(),
            relevance_role=relevance_role,
            claim_support_scope=claim_support_scope,
        )
    return None


def _usable_evidence(evidence: Mapping[str, Any]) -> bool:
    lookup_status = _text(evidence.get("lookup_status"))
    status = _text(evidence.get("status"))
    match_status = _text(evidence.get("match_status"))
    if lookup_status in {"not_found", "deferred", "error"}:
        return False
    if status in {"deferred", "error", "missing"}:
        return False
    if match_status in {"metadata_conflict", "provider_found", "deferred", "error"}:
        return False
    return bool(
        _optional_mapping(evidence.get("matched_identifiers"))
        or match_status == "identifier_matched"
        or status == "matched"
    )


def _identifiers_match_reference(reference: Mapping[str, Any], evidence: Mapping[str, Any]) -> bool:
    requested = _reference_identifiers(reference)
    matched = _identifier_values(_optional_mapping(evidence.get("matched_identifiers")) or {})
    if not requested or not matched:
        return False
    common = requested.keys() & matched.keys()
    return bool(common) and all(requested[key] == matched[key] for key in common)


def _reference_identifiers(reference: Mapping[str, Any]) -> dict[str, str]:
    identifiers = _identifier_values(reference)
    reference_id = _text(reference.get("id") or reference.get("reference_id"))
    if reference_id:
        prefix, separator, value = reference_id.partition(":")
        canonical = {"doi": "doi", "pmid": "pmid", "pmc": "pmcid", "pmcid": "pmcid"}.get(
            prefix.lower()
        )
        if canonical and separator and value:
            identifiers.setdefault(canonical, _normalize_identifier(canonical, value))
    return identifiers


def _identifier_values(payload: Mapping[str, Any]) -> dict[str, str]:
    identifiers: dict[str, str] = {}
    aliases = {
        "doi": ("doi", "DOI"),
        "pmid": ("pmid", "PMID", "PubMed"),
        "pmcid": ("pmcid", "PMCID", "PMC"),
        "arxiv_id": ("arxiv_id", "ArXiv"),
    }
    for canonical, keys in aliases.items():
        value = _first_text(payload, keys=keys)
        if value:
            identifiers[canonical] = _normalize_identifier(canonical, value)
    return identifiers


def _normalize_identifier(identifier: str, value: str) -> str:
    normalized = value.strip()
    if identifier == "doi":
        lowered = normalized.lower()
        for prefix in ("https://doi.org/", "http://doi.org/", "doi:"):
            if lowered.startswith(prefix):
                lowered = lowered[len(prefix) :]
                break
        return lowered
    if identifier == "pmid":
        return normalized.lower().removeprefix("pmid:")
    if identifier == "pmcid":
        return normalized.upper().removeprefix("PMC:").removeprefix("PMC")
    return normalized.lower()


def _record_id(
    *,
    reference: Mapping[str, Any],
    provider: str,
    provider_record_id: str | None,
    doi: str | None,
    pmid: str | None,
    pmcid: str | None,
) -> str:
    if pmid:
        return f"pmid:{pmid}"
    if pmcid:
        return f"pmc:{pmcid}"
    if doi:
        return f"doi:{doi}"
    if provider_record_id:
        return f"{provider.replace('-', '_')}:{provider_record_id}"
    return f"provider:{reference['id']}"


def _full_text_availability(evidence: Mapping[str, Any], *, abstract: str | None) -> str:
    scope = _optional_mapping(evidence.get("verification_scope")) or {}
    # Provider availability is not proof that MAS received and verified the body bytes.
    if scope.get("full_text_body_verified") is True:
        return "full_text"
    return "abstract_only" if abstract else "metadata_only"


def _source_priority(provider: str) -> int:
    return {
        "pmc": 1,
        "pubmed": 2,
        "crossref": 3,
        "semantic-scholar": 4,
        "openalex": 4,
    }.get(provider, 5)


def _authors(value: object) -> tuple[str, ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return ()
    authors: list[str] = []
    for item in value:
        if isinstance(item, Mapping):
            text = _first_text(item, keys=("name", "display_name", "literal"))
            if not text:
                given = _text(item.get("given"))
                family = _text(item.get("family"))
                text = " ".join(part for part in (given, family) if part) or None
        else:
            text = _text(item)
        if text:
            authors.append(text)
    return tuple(authors)


def _year(value: object) -> int | None:
    if isinstance(value, int):
        return value
    text = _text(value)
    return int(text) if text and text.isdigit() else None


def _first_text(*mappings: Mapping[str, Any], keys: Sequence[str]) -> str | None:
    for mapping in mappings:
        for key in keys:
            text = _text(mapping.get(key))
            if text:
                return text
    return None


def _mapping(value: object, *, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{field} must contain mappings")
    return value


def _optional_mapping(value: object) -> Mapping[str, Any] | None:
    return value if isinstance(value, Mapping) else None


def _provider(value: object) -> str:
    return _text(value).lower().replace("_", "-") if _text(value) else ""


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "SUPPORTED_REQUEST_PROVIDERS",
    "SURFACE_KIND",
    "records_from_resolution",
    "resolve_literature_records_from_receipts",
]
