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
    provider_evidence = _mapping_sequence(payload.get("provider_evidence"))
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
        "source_refs": _ref_sequence(payload.get("source_refs")),
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
