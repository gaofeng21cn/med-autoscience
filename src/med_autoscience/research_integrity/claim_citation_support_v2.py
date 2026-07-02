from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any


SURFACE_KIND = "claim_citation_support_matrix_v2"
SCHEMA_VERSION = 2
SUPPORT_GRADES = frozenset(
    (
        "direct_support",
        "partial_support",
        "background_only",
        "unsupported",
        "contradicted",
    )
)
HARD_GATE_SUPPORT_GRADES = frozenset(("unsupported", "contradicted"))
HARD_GATE_ATTESTATION_STATUSES = frozenset(("retracted", "unresolved"))
ATTESTATION_STATUSES = frozenset(("supported", "verified", "retracted", "unresolved"))


def build_claim_citation_support_matrix_v2(
    *,
    claim_spans: Sequence[Mapping[str, Any]],
    citation_refs: Sequence[Mapping[str, Any] | str] = (),
    evidence_refs: Sequence[Mapping[str, Any] | str] = (),
    reference_attestation_refs: Sequence[Mapping[str, Any] | str] = (),
) -> dict[str, Any]:
    citations_by_claim = _refs_by_claim(citation_refs, ref_keys=("citation_ref", "ref", "doi", "pmid"))
    evidence_by_claim = _refs_by_claim(evidence_refs, ref_keys=("evidence_ref", "ref"))
    attestations_by_citation = _attestations_by_citation(reference_attestation_refs)
    sole_claim_id = _sole_claim_id(claim_spans)
    unscoped_citations = _unscoped_refs(citation_refs, ref_keys=("citation_ref", "ref", "doi", "pmid"))
    unscoped_evidence = _unscoped_refs(evidence_refs, ref_keys=("evidence_ref", "ref"))

    claims: list[dict[str, Any]] = []
    citation_links: list[dict[str, Any]] = []
    blocker_candidates: list[dict[str, Any]] = []

    for index, span in enumerate(claim_spans):
        claim_id = _text(span.get("claim_id") or span.get("id")) or f"claim_index_{index}"
        claim_citations = _dedupe(
            _refs(span.get("citation_refs"), ref_keys=("citation_ref", "ref", "doi", "pmid"))
            + citations_by_claim.get(claim_id, [])
            + (unscoped_citations if claim_id == sole_claim_id else [])
        )
        claim_evidence = _dedupe(
            _refs(span.get("evidence_refs"), ref_keys=("evidence_ref", "ref"))
            + evidence_by_claim.get(claim_id, [])
            + (unscoped_evidence if claim_id == sole_claim_id else [])
        )
        support_grade = _claim_support_grade(span, claim_citations, claim_evidence)

        claim = {
            "claim_id": claim_id,
            "claim_ref": _text(span.get("claim_ref") or span.get("span_ref") or span.get("ref")),
            "claim_text": _text(span.get("claim_text") or span.get("text")),
            "citation_refs": claim_citations,
            "evidence_refs": claim_evidence,
            "support_grade": support_grade,
        }
        claims.append(claim)

        if support_grade in HARD_GATE_SUPPORT_GRADES:
            blocker_candidates.append(
                _blocker_candidate(
                    claim_id=claim_id,
                    reason=f"claim_{support_grade}",
                    support_grade=support_grade,
                )
            )

        for citation_ref in claim_citations:
            attestations = attestations_by_citation.get(citation_ref, [])
            citation_links.append(
                {
                    "claim_id": claim_id,
                    "citation_ref": citation_ref,
                    "evidence_refs": claim_evidence,
                    "support_grade": support_grade,
                    "reference_attestations": attestations,
                }
            )
            for attestation in attestations:
                status = attestation["status"]
                if status in HARD_GATE_ATTESTATION_STATUSES:
                    blocker_candidates.append(
                        _blocker_candidate(
                            claim_id=claim_id,
                            reason=f"reference_attestation_{status}",
                            support_grade=support_grade,
                            citation_ref=citation_ref,
                            reference_attestation_ref=attestation["reference_attestation_ref"],
                            reference_attestation_status=status,
                        )
                    )

    return {
        "surface_kind": SURFACE_KIND,
        "schema_version": SCHEMA_VERSION,
        "claims": sorted(claims, key=lambda item: item["claim_id"]),
        "citation_links": sorted(
            citation_links,
            key=lambda item: (item["claim_id"], item["citation_ref"]),
        ),
        "blocker_candidates": sorted(
            blocker_candidates,
            key=lambda item: (item["claim_id"], item["reason"], item.get("citation_ref") or ""),
        ),
        "authority_boundary": _authority_boundary(),
    }


def _claim_support_grade(
    span: Mapping[str, Any],
    citation_refs: Sequence[str],
    evidence_refs: Sequence[str],
) -> str:
    grade = _text(span.get("support_grade"))
    if grade in SUPPORT_GRADES:
        return grade
    if citation_refs and evidence_refs:
        return "direct_support"
    return "unsupported"


def _refs_by_claim(
    values: Sequence[Mapping[str, Any] | str],
    *,
    ref_keys: tuple[str, ...],
) -> dict[str, list[str]]:
    refs_by_claim: dict[str, list[str]] = {}
    for value in values:
        if not isinstance(value, Mapping):
            continue
        ref = _ref_from_mapping(value, ref_keys=ref_keys)
        if ref is None:
            continue
        for claim_id in _claim_ids(value):
            refs_by_claim.setdefault(claim_id, []).append(ref)
    return {claim_id: _dedupe(refs) for claim_id, refs in refs_by_claim.items()}


def _unscoped_refs(
    values: Sequence[Mapping[str, Any] | str],
    *,
    ref_keys: tuple[str, ...],
) -> list[str]:
    refs: list[str] = []
    for value in values:
        if isinstance(value, Mapping):
            if _claim_ids(value):
                continue
            ref = _ref_from_mapping(value, ref_keys=ref_keys)
        else:
            ref = _text(value)
        if ref:
            refs.append(ref)
    return _dedupe(refs)


def _attestations_by_citation(
    values: Sequence[Mapping[str, Any] | str],
) -> dict[str, list[dict[str, str]]]:
    attestations: dict[str, list[dict[str, str]]] = {}
    for value in values:
        if not isinstance(value, Mapping):
            continue
        citation_ref = _ref_from_mapping(value, ref_keys=("citation_ref", "reference_ref", "ref", "doi", "pmid"))
        attestation_ref = _text(value.get("reference_attestation_ref") or value.get("attestation_ref"))
        status = _text(value.get("reference_attestation_status") or value.get("status"))
        if citation_ref is None or attestation_ref is None or status not in ATTESTATION_STATUSES:
            continue
        attestations.setdefault(citation_ref, []).append(
            {
                "reference_attestation_ref": attestation_ref,
                "status": status,
            }
        )
    return {
        citation_ref: sorted(items, key=lambda item: (item["status"], item["reference_attestation_ref"]))
        for citation_ref, items in attestations.items()
    }


def _claim_ids(value: Mapping[str, Any]) -> list[str]:
    claim_ids = _refs(value.get("claim_ids"), ref_keys=("claim_id", "id", "ref"))
    claim_id = _text(value.get("claim_id"))
    if claim_id:
        claim_ids.append(claim_id)
    return _dedupe(claim_ids)


def _sole_claim_id(claim_spans: Sequence[Mapping[str, Any]]) -> str | None:
    if len(claim_spans) != 1:
        return None
    return _text(claim_spans[0].get("claim_id") or claim_spans[0].get("id")) or "claim_index_0"


def _refs(value: object, *, ref_keys: tuple[str, ...]) -> list[str]:
    if isinstance(value, Mapping):
        ref = _ref_from_mapping(value, ref_keys=ref_keys)
        return [ref] if ref else []
    if isinstance(value, str):
        ref = _text(value)
        return [ref] if ref else []
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray)):
        refs: list[str] = []
        for item in value:
            if isinstance(item, Mapping):
                ref = _ref_from_mapping(item, ref_keys=ref_keys)
            else:
                ref = _text(item)
            if ref:
                refs.append(ref)
        return _dedupe(refs)
    return []


def _ref_from_mapping(value: Mapping[str, Any], *, ref_keys: tuple[str, ...]) -> str | None:
    for key in ref_keys:
        ref = _text(value.get(key))
        if ref is None:
            continue
        if key == "doi" and not ref.startswith("doi:"):
            return f"doi:{ref}"
        if key == "pmid" and not ref.startswith("pmid:"):
            return f"pmid:{ref}"
        return ref
    return None


def _dedupe(values: Sequence[str]) -> list[str]:
    return sorted(dict.fromkeys(values))


def _text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    text = value.strip()
    return text or None


def _blocker_candidate(
    *,
    claim_id: str,
    reason: str,
    support_grade: str,
    citation_ref: str | None = None,
    reference_attestation_ref: str | None = None,
    reference_attestation_status: str | None = None,
) -> dict[str, Any]:
    return {
        "candidate_ref": ":".join(
            value
            for value in (
                "claim-citation-support-v2",
                claim_id,
                citation_ref,
                reference_attestation_ref,
                reason,
            )
            if value
        ),
        "blocker_type": "claim_citation_support_hard_gate_candidate",
        "hard_gate": True,
        "claim_id": claim_id,
        "reason": reason,
        "support_grade": support_grade,
        "citation_ref": citation_ref,
        "reference_attestation_ref": reference_attestation_ref,
        "reference_attestation_status": reference_attestation_status,
        "authority_boundary": _authority_boundary(),
    }


def _authority_boundary() -> dict[str, bool]:
    return {
        "candidate_evidence_only": True,
        "can_write_typed_blocker": False,
        "can_write_owner_receipt": False,
        "can_mutate_claims": False,
        "can_mutate_reference_attestations": False,
        "can_authorize_publication_readiness": False,
    }


__all__ = [
    "SCHEMA_VERSION",
    "SURFACE_KIND",
    "build_claim_citation_support_matrix_v2",
]
