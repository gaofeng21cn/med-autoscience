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
SCHEMA_VERSION = 1
REFERENCE_HARD_STATUSES = frozenset(("contradicted", "retracted"))
REFERENCE_REVIEW_STATUSES = frozenset(("needs_review", "unresolved"))


def build_research_integrity_gate_input_bundle(
    *,
    reference_checks: Sequence[Mapping[str, Any]] = (),
    claim_spans: Sequence[Mapping[str, Any]] = (),
    citation_refs: Sequence[Mapping[str, Any] | str] = (),
    evidence_refs: Sequence[Mapping[str, Any] | str] = (),
    reference_attestation_refs: Sequence[Mapping[str, Any] | str] = (),
    manuscript_sections: Mapping[str, Any] | None = None,
    numeric_facts: object = (),
    display_facts: object = (),
    reporting_checklist_expectations: object = (),
) -> dict[str, Any]:
    reference_attestations = _reference_attestations(reference_checks)
    all_reference_attestation_refs = (
        tuple(reference_attestation_refs)
        + tuple(_reference_attestation_link(item) for item in reference_attestations)
    )
    claim_support = build_claim_citation_support_matrix_v2(
        claim_spans=claim_spans,
        citation_refs=citation_refs,
        evidence_refs=evidence_refs,
        reference_attestation_refs=all_reference_attestation_refs,
    )
    manuscript_review = build_manuscript_consistency_meta_review(
        manuscript_sections=manuscript_sections or {},
        numeric_facts=numeric_facts,
        display_facts=display_facts,
        reporting_checklist_expectations=reporting_checklist_expectations,
    )
    blocker_candidates = (
        _reference_blocker_candidates(reference_attestations)
        + _surface_blocker_candidates("claim_citation_support", claim_support["blocker_candidates"])
        + _surface_blocker_candidates("manuscript_consistency", manuscript_review["blocker_candidates"])
    )
    review_candidates = (
        _reference_review_candidates(reference_attestations)
        + _claim_review_candidates(claim_support)
        + _manuscript_review_candidates(manuscript_review)
    )
    return {
        "surface_kind": SURFACE_KIND,
        "schema_version": SCHEMA_VERSION,
        "status": _status(blocker_candidates=blocker_candidates, review_candidates=review_candidates),
        "surfaces": {
            "reference_verification_attestations": reference_attestations,
            "claim_citation_support_matrix_v2": claim_support,
            "manuscript_consistency_meta_review": manuscript_review,
        },
        "blocker_candidates": blocker_candidates,
        "review_candidates": review_candidates,
        "authority_boundary": authority_boundary(),
    }


def authority_boundary() -> dict[str, bool]:
    return {
        "can_write_mas_study_truth": False,
        "can_write_publication_eval_latest": False,
        "can_write_controller_decisions": False,
        "can_mutate_current_package": False,
        "can_sign_owner_receipt": False,
        "can_materialize_typed_blocker": False,
        "can_materialize_human_gate": False,
        "can_write_runtime_queue_or_provider_attempt": False,
        "can_authorize_publication_readiness": False,
        "can_authorize_submission_readiness": False,
    }


def _reference_attestations(reference_checks: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    attestations: list[dict[str, Any]] = []
    for item in reference_checks:
        reference = item.get("reference")
        evidence = item.get("provider_evidence") or item.get("evidence") or ()
        if not isinstance(reference, Mapping):
            continue
        if not isinstance(evidence, Sequence) or isinstance(evidence, (str, bytes, bytearray)):
            evidence = ()
        attestations.append(
            build_reference_verification_attestation_dict(
                reference,
                [payload for payload in evidence if isinstance(payload, Mapping)],
            )
        )
    return sorted(attestations, key=lambda item: str(item.get("reference_id") or ""))


def _reference_attestation_link(attestation: Mapping[str, Any]) -> dict[str, str]:
    reference_id = str(attestation.get("reference_id") or "")
    return {
        "citation_ref": f"ref:{reference_id}",
        "reference_attestation_ref": f"research_integrity/reference_verification_attestations/{reference_id}",
        "reference_attestation_status": str(attestation.get("status") or ""),
    }


def _reference_blocker_candidates(attestations: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [
        _candidate("reference_authenticity", str(item["reference_id"]), str(item["status"]))
        for item in attestations
        if item.get("status") in REFERENCE_HARD_STATUSES and item.get("reference_id")
    ]


def _reference_review_candidates(attestations: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [
        _candidate("reference_authenticity", str(item["reference_id"]), str(item["status"]))
        for item in attestations
        if item.get("status") in REFERENCE_REVIEW_STATUSES and item.get("reference_id")
    ]


def _claim_review_candidates(claim_support: Mapping[str, Any]) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for claim in claim_support.get("claims") or ():
        if not isinstance(claim, Mapping):
            continue
        grade = claim.get("support_grade")
        claim_id = claim.get("claim_id")
        if grade in {"partial_support", "background_only"} and claim_id:
            candidates.append(_candidate("claim_citation_support", str(claim_id), str(grade)))
    return candidates


def _manuscript_review_candidates(manuscript_review: Mapping[str, Any]) -> list[dict[str, Any]]:
    if manuscript_review.get("status") != "needs_review":
        return []
    candidates: list[dict[str, Any]] = []
    for finding in manuscript_review.get("findings") or ():
        if isinstance(finding, Mapping):
            candidates.append(
                _candidate(
                    "manuscript_consistency",
                    str(finding.get("fact_id") or "unknown"),
                    str(finding.get("code") or "needs_review"),
                )
            )
    return candidates


def _surface_blocker_candidates(family: str, candidates: object) -> list[dict[str, Any]]:
    tagged: list[dict[str, Any]] = []
    if not isinstance(candidates, Sequence) or isinstance(candidates, (str, bytes, bytearray)):
        return tagged
    for index, candidate in enumerate(candidates):
        if not isinstance(candidate, Mapping):
            continue
        payload = dict(candidate)
        payload.setdefault("family", family)
        payload.setdefault("target_id", str(payload.get("claim_id") or payload.get("fact_id") or index))
        payload.setdefault("reason", str(payload.get("reason") or payload.get("blocker_type") or "blocked"))
        payload.setdefault("authority_boundary", authority_boundary())
        tagged.append(payload)
    return tagged


def _candidate(family: str, target_id: str, reason: str) -> dict[str, Any]:
    return {
        "candidate_ref": f"research-integrity:{family}:{target_id}:{reason}",
        "family": family,
        "target_id": target_id,
        "reason": reason,
        "authority_boundary": authority_boundary(),
    }


def _status(*, blocker_candidates: Sequence[Mapping[str, Any]], review_candidates: Sequence[Mapping[str, Any]]) -> str:
    if blocker_candidates:
        return "blocked"
    if review_candidates:
        return "needs_review"
    return "clear"


__all__ = [
    "SCHEMA_VERSION",
    "SURFACE_KIND",
    "authority_boundary",
    "build_research_integrity_gate_input_bundle",
]
