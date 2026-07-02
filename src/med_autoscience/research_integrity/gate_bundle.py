from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from med_autoscience.research_integrity.claim_citation_support_v2 import (
    build_claim_citation_support_matrix_v2,
)
from med_autoscience.research_integrity.manuscript_consistency import (
    build_manuscript_consistency_meta_review,
)
from med_autoscience.research_integrity.reference_authenticity import (
    build_reference_verification_attestation_dict,
)


SURFACE_KIND = "research_integrity_gate_input_bundle"
SCHEMA_VERSION = "mas-research-integrity-gate-input.v1"


def build_research_integrity_gate_input_bundle(*, payload: Mapping[str, Any]) -> dict[str, Any]:
    normalized = dict(payload)
    references = _references(normalized)
    provider_evidence = _sequence_of_mappings(normalized.get("provider_evidence"))
    provided_attestations = _sequence_of_mappings(normalized.get("reference_attestations"))
    reference_attestations = provided_attestations or _reference_attestations(
        references=references,
        provider_evidence=provider_evidence,
    )
    claims = _claims(normalized)
    manuscript = _mapping(normalized.get("manuscript"))
    display_to_claim_map = normalized.get("display_to_claim_map")
    reporting_expectations = normalized.get("reporting_guideline_expectations")

    citation_support = build_claim_citation_support_matrix_v2(
        claim_spans=claims,
        citation_refs=references,
        evidence_refs=_sequence_of_mappings(normalized.get("evidence_refs"))
        or _sequence_of_mappings(normalized.get("evidence"))
        or provider_evidence,
        reference_attestation_refs=reference_attestations,
    )
    manuscript_consistency = build_manuscript_consistency_meta_review(
        manuscript_sections=manuscript,
        numeric_facts=normalized.get("numeric_facts") or normalized.get("facts") or (),
        display_facts=display_to_claim_map or normalized.get("display_facts") or (),
        reporting_checklist_expectations=reporting_expectations or (),
    )
    blocker_candidates = _blocker_candidates(
        citation_support=citation_support,
        manuscript_consistency=manuscript_consistency,
        reference_attestations=reference_attestations,
    )
    return {
        "surface_kind": SURFACE_KIND,
        "schema_version": SCHEMA_VERSION,
        "status": _status(blocker_candidates=blocker_candidates),
        "reference_attestations": reference_attestations,
        "claim_citation_support_matrix": citation_support,
        "manuscript_consistency_meta_review": manuscript_consistency,
        "blocker_candidates": blocker_candidates,
        "authority_boundary": authority_boundary(),
    }


def authority_boundary() -> dict[str, Any]:
    return {
        "outputs_are_gate_inputs": True,
        "candidate_evidence_only": True,
        "can_write_mas_study_truth": False,
        "can_write_publication_eval_latest": False,
        "can_write_publication_eval": False,
        "can_write_controller_decisions": False,
        "can_mutate_current_package": False,
        "can_write_current_package": False,
        "can_sign_owner_receipt": False,
        "can_write_owner_receipt": False,
        "can_materialize_typed_blocker": False,
        "can_write_typed_blocker": False,
        "can_materialize_human_gate": False,
        "can_write_runtime_queue_or_provider_attempt": False,
        "can_authorize_publication_quality": False,
        "can_authorize_publication_readiness": False,
        "can_authorize_submission_readiness": False,
    }


def _references(payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    references = _sequence_of_mappings(payload.get("references"))
    if references:
        return references
    reference = _mapping(payload.get("reference"))
    return [reference] if reference else []


def _claims(payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    claims = _sequence_of_mappings(payload.get("claims"))
    if claims:
        return claims
    claim = _mapping(payload.get("claim"))
    return [claim] if claim else []


def _reference_attestations(
    *,
    references: Sequence[Mapping[str, Any]],
    provider_evidence: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    attestations: list[dict[str, Any]] = []
    for reference in references:
        evidence = _provider_evidence_for_reference(reference, provider_evidence)
        if not evidence:
            continue
        try:
            attestations.append(
                build_reference_verification_attestation_dict(reference, evidence)
            )
        except ValueError as exc:
            attestations.append(
                {
                    "surface_kind": "reference_verification_attestation",
                    "reference_id": _reference_id(reference) or "unknown_reference",
                    "status": "unresolved",
                    "source_crosschecks": [],
                    "identifier_conflicts": [],
                    "metadata_mismatches": [],
                    "retraction_or_update_flags": [],
                    "error": str(exc),
                    "authority_boundary": authority_boundary(),
                }
            )
    return attestations


def _provider_evidence_for_reference(
    reference: Mapping[str, Any],
    provider_evidence: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    reference_id = _reference_id(reference)
    scoped: list[dict[str, Any]] = []
    unscoped: list[dict[str, Any]] = []
    for evidence in provider_evidence:
        evidence_ref = _text(
            evidence.get("reference_id")
            or evidence.get("ref_id")
            or evidence.get("citation_key")
            or evidence.get("key")
        )
        if evidence_ref is None:
            unscoped.append(dict(evidence))
        elif reference_id is not None and evidence_ref == reference_id:
            scoped.append(dict(evidence))
    return scoped or (unscoped if len(provider_evidence) == 1 else [])


def _blocker_candidates(
    *,
    citation_support: Mapping[str, Any],
    manuscript_consistency: Mapping[str, Any],
    reference_attestations: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    candidates.extend(_sequence_of_mappings(citation_support.get("blocker_candidates")))
    candidates.extend(_sequence_of_mappings(manuscript_consistency.get("blocker_candidates")))
    for attestation in reference_attestations:
        status = _text(attestation.get("status"))
        if status in {"unresolved", "contradicted", "retracted"}:
            candidates.append(
                {
                    "candidate_ref": "reference-attestation:"
                    + (_text(attestation.get("reference_id")) or "unknown_reference")
                    + ":"
                    + status,
                    "blocker_type": "reference_verification_attestation_candidate",
                    "reason": f"reference_{status}",
                    "reference_id": _text(attestation.get("reference_id")),
                    "refs_only": True,
                    "authority_boundary": authority_boundary(),
                }
            )
    return sorted(
        candidates,
        key=lambda item: (
            str(item.get("blocker_type") or ""),
            str(item.get("candidate_ref") or ""),
        ),
    )


def _status(*, blocker_candidates: Sequence[Mapping[str, Any]]) -> str:
    return "blocked" if blocker_candidates else "clear"


def _sequence_of_mappings(value: object) -> list[dict[str, Any]]:
    if isinstance(value, Mapping):
        return [dict(value)]
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [dict(item) for item in value if isinstance(item, Mapping)]
    return []


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _reference_id(reference: Mapping[str, Any]) -> str | None:
    for key in ("reference_id", "ref_id", "id", "ID", "citation_key", "key"):
        text = _text(reference.get(key))
        if text:
            return text
    return None


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "SCHEMA_VERSION",
    "SURFACE_KIND",
    "authority_boundary",
    "build_research_integrity_gate_input_bundle",
]
