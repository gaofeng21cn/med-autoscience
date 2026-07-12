from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import tempfile
from typing import Any

from opl_framework.executor_client import run_opl_json

from med_autoscience.research_integrity.gate_bundle import (
    authority_boundary as gate_authority_boundary,
    build_research_integrity_gate_input_bundle,
)
from med_autoscience.research_integrity.reference_authenticity import (
    build_reference_verification_attestation_dict,
)


SURFACE_KIND = "reference_provider_lookup_bundle"
SCHEMA_VERSION = "mas-reference-provider-lookup.v2"
DEFAULT_PROVIDERS = ("crossref", "openalex", "semantic-scholar", "crossmark", "publisher")
SUPPORTED_LOOKUP_PROVIDERS = frozenset(DEFAULT_PROVIDERS)
PROVIDER_LOOKUP_MODE = "opl_connect_receipt_input_only"
AUTHORITATIVE_PROVIDER_TRUTH_OWNER = "external provider source systems"

OplJsonRunner = Callable[..., Mapping[str, Any] | None]


@dataclass(frozen=True)
class ProviderLookupConfig:
    providers: tuple[str, ...] = DEFAULT_PROVIDERS
    timeout_seconds: float = 30.0
    max_retries: int = 1
    cache_root: str | None = None

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any] | None = None) -> ProviderLookupConfig:
        payload = payload or {}
        raw_providers = payload.get("providers") or payload.get("provider") or DEFAULT_PROVIDERS
        if isinstance(raw_providers, str):
            raw_providers = (raw_providers,)
        if not isinstance(raw_providers, Sequence) or isinstance(raw_providers, (bytes, bytearray)):
            raise ValueError("provider lookup `providers` must be a string or string sequence")
        providers = tuple(_provider_name(provider) for provider in raw_providers)
        timeout_seconds = float(payload.get("timeout_seconds", 30.0))
        max_retries = int(payload.get("max_retries", 1))
        if timeout_seconds <= 0:
            raise ValueError("provider lookup timeout_seconds must be greater than zero")
        if max_retries < 0:
            raise ValueError("provider lookup max_retries must be non-negative")
        cache_root = _text(payload.get("cache_root"))
        return cls(
            providers=providers,
            timeout_seconds=timeout_seconds,
            max_retries=max_retries,
            cache_root=cache_root,
        )


def build_reference_provider_lookup_bundle(
    *,
    references: Sequence[Mapping[str, Any]] | Mapping[str, Any],
    provider_config: Mapping[str, Any] | ProviderLookupConfig | None = None,
    opl_runner: OplJsonRunner | None = None,
    claim_spans: Sequence[Mapping[str, Any]] = (),
    citation_refs: Sequence[Mapping[str, Any] | str] = (),
    evidence_refs: Sequence[Mapping[str, Any] | str] = (),
    reference_attestation_refs: Sequence[Mapping[str, Any] | str] = (),
    manuscript_sections: Mapping[str, Any] | None = None,
    numeric_facts: object = (),
    display_facts: object = (),
    reporting_checklist_expectations: object = (),
) -> dict[str, Any]:
    config = _config(provider_config)
    normalized_references = [_reference_with_id(reference) for reference in _reference_sequence(references)]
    provider_evidence = _lookup_through_opl_connect(
        normalized_references,
        config=config,
        opl_runner=opl_runner,
    )
    evidence_by_reference: dict[str, list[dict[str, Any]]] = {
        str(reference["id"]): [] for reference in normalized_references
    }
    for evidence in provider_evidence:
        reference_id = _text(evidence.get("reference_id"))
        if reference_id in evidence_by_reference:
            evidence_by_reference[reference_id].append(evidence)
    checks = [
        {
            "reference": reference,
            "provider_evidence": evidence_by_reference[str(reference["id"])],
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
    return {
        "surface_kind": SURFACE_KIND,
        "schema_version": SCHEMA_VERSION,
        "provider_lookup_mode": PROVIDER_LOOKUP_MODE,
        "receipt_first": True,
        "transition_only": False,
        "live_provider_authority_claimed": False,
        "authoritative_provider_truth_owner": AUTHORITATIVE_PROVIDER_TRUTH_OWNER,
        "status": gate_input["status"],
        "providers": list(config.providers),
        "references": attestations,
        "provider_summary": _provider_summary(attestations),
        "gate_input_bundle": gate_input,
        "authority_boundary": provider_lookup_authority_boundary(),
    }


def lookup_reference_provider_evidence(
    reference: Mapping[str, Any],
    *,
    provider_config: Mapping[str, Any] | ProviderLookupConfig | None = None,
    opl_runner: OplJsonRunner | None = None,
) -> list[dict[str, Any]]:
    config = _config(provider_config)
    return _lookup_through_opl_connect(
        [_reference_with_id(reference)],
        config=config,
        opl_runner=opl_runner,
    )


def provider_lookup_authority_boundary() -> dict[str, Any]:
    boundary = gate_authority_boundary()
    boundary.update(
        {
            "surface_role": "domain_consumes_opl_connect_provider_receipts",
            "provider_lookup_owner": "OPL Connect",
            "provider_lookup_mode": PROVIDER_LOOKUP_MODE,
            "receipt_first": True,
            "transition_only": False,
            "live_provider_authority_claimed": False,
            "authoritative_provider_truth_owner": AUTHORITATIVE_PROVIDER_TRUTH_OWNER,
            "mas_can_call_external_provider": False,
            "can_call_external_provider": False,
            "can_claim_live_provider_truth": False,
            "can_be_used_as_authoritative_provider_truth_without_owner_consumption": False,
            "can_write_provider_attempt": False,
            "can_write_provider_cache": False,
            "can_materialize_provider_receipt": False,
            "can_assert_publisher_or_crossmark_status_without_provider_receipt": False,
        }
    )
    return boundary


def _lookup_through_opl_connect(
    references: list[dict[str, Any]],
    *,
    config: ProviderLookupConfig,
    opl_runner: OplJsonRunner | None,
) -> list[dict[str, Any]]:
    runner = opl_runner or run_opl_json
    with tempfile.TemporaryDirectory(prefix="mas-opl-connect-references-") as temp_dir:
        references_path = Path(temp_dir) / "references.json"
        references_path.write_text(
            json.dumps({"references": references}, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        args = [
            "connect",
            "references",
            "verify",
            "--references-file",
            str(references_path),
            "--providers",
            ",".join(config.providers),
            "--max-retries",
            str(config.max_retries),
            "--json",
        ]
        if config.cache_root is not None:
            args.extend(["--cache-root", config.cache_root])
        response = runner(args, timeout_seconds=config.timeout_seconds)
    if not isinstance(response, Mapping):
        raise RuntimeError("OPL Connect reference verification returned no JSON object")
    surface = response.get("opl_connect_reference_verification")
    if not isinstance(surface, Mapping):
        raise RuntimeError("OPL Connect response is missing opl_connect_reference_verification")
    if surface.get("surface_kind") != "opl_connect_reference_verification_readonly":
        raise RuntimeError("OPL Connect returned an invalid reference verification surface")
    raw_evidence = surface.get("provider_evidence")
    if not isinstance(raw_evidence, list):
        raise RuntimeError("OPL Connect reference verification is missing provider_evidence")
    return [dict(item) for item in raw_evidence if isinstance(item, Mapping)]


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
            status = str(evidence.get("lookup_status") or "error")
            counts[status if status in counts else "error"] += 1
    return counts


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "AUTHORITATIVE_PROVIDER_TRUTH_OWNER",
    "DEFAULT_PROVIDERS",
    "PROVIDER_LOOKUP_MODE",
    "ProviderLookupConfig",
    "SCHEMA_VERSION",
    "SUPPORTED_LOOKUP_PROVIDERS",
    "SURFACE_KIND",
    "build_reference_provider_lookup_bundle",
    "lookup_reference_provider_evidence",
    "provider_lookup_authority_boundary",
]
