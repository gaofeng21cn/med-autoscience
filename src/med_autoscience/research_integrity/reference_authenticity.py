from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
import re
from typing import Any, Literal


SURFACE_KIND = "reference_verification_attestation"
SCHEMA_VERSION = "mas-reference-verification-attestation.v1"
SUPPORTED_PROVIDERS = frozenset(
    {
        "crossref",
        "pubmed",
        "openalex",
        "semantic_scholar",
        "publisher",
        "crossmark",
    }
)
STATUS_VALUES = ("verified", "needs_review", "unresolved", "contradicted", "retracted")

ReferenceVerificationStatus = Literal[
    "verified",
    "needs_review",
    "unresolved",
    "contradicted",
    "retracted",
]

_IDENTIFIER_ALIASES = {
    "doi": ("doi", "DOI"),
    "pmid": ("pmid", "PMID", "pubmed_id", "PubMedID"),
    "pmcid": ("pmcid", "PMCID"),
    "openalex": ("openalex", "openalex_id", "OpenAlexID"),
    "semantic_scholar": (
        "semantic_scholar",
        "semantic_scholar_id",
        "s2_id",
        "SemanticScholarID",
    ),
}
_METADATA_ALIASES = {
    "title": ("title", "Title"),
    "year": ("year", "date", "published", "publication_year"),
    "journal": ("journal", "journaltitle", "container_title", "container-title"),
}
_FLAG_KEYS = (
    "retracted",
    "withdrawn",
    "expression_of_concern",
    "correction",
    "has_update",
    "updated",
    "update_type",
)
_RETRACTION_FLAGS = frozenset({"retracted", "withdrawn"})


@dataclass(frozen=True)
class ReferenceVerificationAttestation:
    surface_kind: str
    schema_version: str
    reference_id: str
    status: ReferenceVerificationStatus
    source_crosschecks: list[dict[str, Any]]
    identifier_conflicts: list[dict[str, Any]]
    metadata_mismatches: list[dict[str, Any]]
    retraction_or_update_flags: list[dict[str, Any]]
    authority_boundary: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_reference_verification_attestation(
    reference: Mapping[str, Any],
    provider_evidence: Sequence[Mapping[str, Any]],
    *,
    schema_version: str = SCHEMA_VERSION,
) -> ReferenceVerificationAttestation:
    reference_id = _reference_id(reference)
    reference_identifiers = _identifiers_from(reference)
    reference_metadata = _metadata_from(reference)

    source_crosschecks: list[dict[str, Any]] = []
    identifier_conflicts: list[dict[str, Any]] = []
    metadata_mismatches: list[dict[str, Any]] = []
    retraction_or_update_flags: list[dict[str, Any]] = []

    for evidence in provider_evidence:
        provider = _provider_name(evidence)
        evidence_identifiers = _identifiers_from(_merged_metadata_source(evidence, "matched_identifiers"))
        evidence_metadata = _metadata_from(_merged_metadata_source(evidence, "metadata"))
        matched_identifiers = _matched_identifiers(reference_identifiers, evidence_identifiers)
        conflicts = _identifier_conflicts(provider, reference_identifiers, evidence_identifiers)
        mismatches = _metadata_mismatches(provider, reference_metadata, evidence_metadata)
        flags = _flags(provider, evidence)

        source_crosschecks.append(
            {
                "provider": provider,
                "status": "matched" if matched_identifiers else "unmatched",
                "matched_identifiers": matched_identifiers,
                "evidence_identifiers": evidence_identifiers,
                "metadata": evidence_metadata,
                "retraction_or_update_flags": flags,
            }
        )
        identifier_conflicts.extend(conflicts)
        metadata_mismatches.extend(mismatches)
        retraction_or_update_flags.extend(flags)

    status = _status(
        source_crosschecks=source_crosschecks,
        identifier_conflicts=identifier_conflicts,
        metadata_mismatches=metadata_mismatches,
        retraction_or_update_flags=retraction_or_update_flags,
    )
    return ReferenceVerificationAttestation(
        surface_kind=SURFACE_KIND,
        schema_version=schema_version,
        reference_id=reference_id,
        status=status,
        source_crosschecks=source_crosschecks,
        identifier_conflicts=identifier_conflicts,
        metadata_mismatches=metadata_mismatches,
        retraction_or_update_flags=retraction_or_update_flags,
        authority_boundary=_authority_boundary(),
    )


def build_reference_verification_attestation_dict(
    reference: Mapping[str, Any],
    provider_evidence: Sequence[Mapping[str, Any]],
    *,
    schema_version: str = SCHEMA_VERSION,
) -> dict[str, Any]:
    return build_reference_verification_attestation(
        reference,
        provider_evidence,
        schema_version=schema_version,
    ).to_dict()


def _reference_id(reference: Mapping[str, Any]) -> str:
    for key in ("reference_id", "ref_id", "id", "ID", "citation_key", "key"):
        value = _text(reference.get(key))
        if value:
            return value
    raise ValueError("reference_id is required")


def _provider_name(evidence: Mapping[str, Any]) -> str:
    provider = _text(evidence.get("provider") or evidence.get("source"))
    if provider not in SUPPORTED_PROVIDERS:
        raise ValueError(f"unsupported reference evidence provider: {provider!r}")
    return provider


def _merged_metadata_source(evidence: Mapping[str, Any], nested_key: str) -> dict[str, Any]:
    merged = dict(evidence)
    nested = evidence.get(nested_key)
    if isinstance(nested, Mapping):
        merged.update(nested)
    return merged


def _identifiers_from(payload: Mapping[str, Any]) -> dict[str, str]:
    identifiers: dict[str, str] = {}
    identifiers_payload = payload.get("identifiers")
    if isinstance(identifiers_payload, Mapping):
        payload = {**payload, **identifiers_payload}
    for canonical, aliases in _IDENTIFIER_ALIASES.items():
        value = _first_text(payload, aliases)
        if value:
            identifiers[canonical] = _normalize_identifier(canonical, value)
    return identifiers


def _metadata_from(payload: Mapping[str, Any]) -> dict[str, str]:
    metadata: dict[str, str] = {}
    for canonical, aliases in _METADATA_ALIASES.items():
        value = _first_text(payload, aliases)
        if value:
            metadata[canonical] = _normalize_metadata(canonical, value)
    return metadata


def _matched_identifiers(reference: Mapping[str, str], evidence: Mapping[str, str]) -> list[str]:
    return [
        identifier
        for identifier in _IDENTIFIER_ALIASES
        if reference.get(identifier) and reference.get(identifier) == evidence.get(identifier)
    ]


def _identifier_conflicts(
    provider: str,
    reference: Mapping[str, str],
    evidence: Mapping[str, str],
) -> list[dict[str, str]]:
    conflicts: list[dict[str, str]] = []
    for identifier in _IDENTIFIER_ALIASES:
        reference_value = reference.get(identifier)
        evidence_value = evidence.get(identifier)
        if reference_value and evidence_value and reference_value != evidence_value:
            conflicts.append(
                {
                    "provider": provider,
                    "identifier": identifier,
                    "reference_value": reference_value,
                    "evidence_value": evidence_value,
                }
            )
    return conflicts


def _metadata_mismatches(
    provider: str,
    reference: Mapping[str, str],
    evidence: Mapping[str, str],
) -> list[dict[str, str]]:
    mismatches: list[dict[str, str]] = []
    for field in _METADATA_ALIASES:
        reference_value = reference.get(field)
        evidence_value = evidence.get(field)
        if reference_value and evidence_value and reference_value != evidence_value:
            mismatches.append(
                {
                    "provider": provider,
                    "field": field,
                    "reference_value": reference_value,
                    "evidence_value": evidence_value,
                }
            )
    return mismatches


def _flags(provider: str, evidence: Mapping[str, Any]) -> list[dict[str, Any]]:
    flag_payload = evidence.get("retraction_or_update_flags")
    if isinstance(flag_payload, Mapping):
        source = {**evidence, **flag_payload}
    else:
        source = evidence
    flags: list[dict[str, Any]] = []
    for key in _FLAG_KEYS:
        value = source.get(key)
        if key == "update_type":
            if _text(value):
                flags.append({"provider": provider, "flag": key, "value": value})
            continue
        if _truthy_flag(value):
            flags.append({"provider": provider, "flag": key, "value": value})
    return flags


def _status(
    *,
    source_crosschecks: Sequence[Mapping[str, Any]],
    identifier_conflicts: Sequence[Mapping[str, Any]],
    metadata_mismatches: Sequence[Mapping[str, Any]],
    retraction_or_update_flags: Sequence[Mapping[str, Any]],
) -> ReferenceVerificationStatus:
    if any(_is_retraction_flag(flag) for flag in retraction_or_update_flags):
        return "retracted"
    if identifier_conflicts:
        return "contradicted"
    if metadata_mismatches or retraction_or_update_flags:
        return "needs_review"
    if any(crosscheck.get("matched_identifiers") for crosscheck in source_crosschecks):
        return "verified"
    return "unresolved"


def _is_retraction_flag(flag: Mapping[str, Any]) -> bool:
    flag_name = _text(flag.get("flag"))
    value = flag.get("value")
    if flag_name in _RETRACTION_FLAGS and value is True:
        return True
    return flag_name == "update_type" and _text(value) == "retraction"


def _authority_boundary() -> dict[str, Any]:
    return {
        "surface_role": "gate_input_and_blocker_candidate_evidence_only",
        "can_write_publication_authority": False,
        "can_write_publication_eval": False,
        "can_write_controller_decisions": False,
        "can_sign_owner_receipt": False,
        "can_create_owner_receipt": False,
        "can_create_typed_blocker": False,
        "can_create_human_gate": False,
        "can_mutate_reference_manager": False,
        "can_call_external_provider": False,
        "produces_gate_input": True,
        "produces_blocker_candidate_evidence": True,
    }


def _first_text(payload: Mapping[str, Any], keys: Sequence[str]) -> str | None:
    for key in keys:
        value = _text(payload.get(key))
        if value:
            return value
    return None


def _normalize_identifier(identifier: str, value: str) -> str:
    text = _collapse_space(value)
    if identifier == "doi":
        text = text.removeprefix("https://doi.org/").removeprefix("http://doi.org/")
        text = text.removeprefix("doi:")
        return text.lower()
    return text


def _normalize_metadata(field: str, value: str) -> str:
    text = _collapse_space(value)
    if field == "year":
        match = re.search(r"\d{4}", text)
        return match.group(0) if match else text
    return text.lower()


def _collapse_space(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip())


def _truthy_flag(value: object) -> bool:
    if value is True:
        return True
    if isinstance(value, str):
        return value.strip().lower() not in {"", "0", "false", "no", "none", "null"}
    return False


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "SCHEMA_VERSION",
    "SURFACE_KIND",
    "SUPPORTED_PROVIDERS",
    "ReferenceVerificationAttestation",
    "ReferenceVerificationStatus",
    "build_reference_verification_attestation",
    "build_reference_verification_attestation_dict",
]
