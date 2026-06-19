from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any


SURFACE_KIND = "mas_claim_citation_support_matrix"
SCHEMA_VERSION = 1
VALID_SUPPORT_GRADES = frozenset(
    (
        "supportive",
        "partial",
        "contradictory",
        "metadata_only",
        "unverified",
    )
)
REQUIRED_REF_FIELDS = ("claim_ref", "evidence_refs", "citation_refs")
REQUIRED_TEXT_FIELDS = ("claim_id", "source_tier", "checked_at")


def build_claim_citation_support_matrix(
    claims: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    entries: list[dict[str, Any]] = []
    missing_required_refs: list[dict[str, str]] = []
    typed_blocker_candidates: list[dict[str, Any]] = []

    for index, claim in enumerate(claims):
        entry, missing, blockers = _matrix_entry(claim, index=index)
        entries.append(entry)
        missing_required_refs.extend(missing)
        typed_blocker_candidates.extend(blockers)

    return {
        "surface_kind": SURFACE_KIND,
        "schema_version": SCHEMA_VERSION,
        "status": (
            "typed_blocker_candidate"
            if typed_blocker_candidates or missing_required_refs
            else "complete"
        ),
        "refs_only": True,
        "fail_open": True,
        "mainline_waits_for_support_matrix": False,
        "can_block_current_owner_action": False,
        "matrix_entries": entries,
        "missing_required_refs": missing_required_refs,
        "typed_blocker_candidates": typed_blocker_candidates,
        "source_refs": _source_refs(),
        "authority_boundary": _authority_boundary(),
    }


def _matrix_entry(
    claim: Mapping[str, Any],
    *,
    index: int,
) -> tuple[dict[str, Any], list[dict[str, str]], list[dict[str, Any]]]:
    claim_id = _text(claim.get("claim_id")) or f"claim_index_{index}"
    claim_ref = _ref_from_value(claim.get("claim_ref"))
    evidence_refs = _refs(claim.get("evidence_refs"), preferred_keys=("evidence_ref", "ref"))
    citation_refs = _refs(
        claim.get("citation_refs"),
        preferred_keys=("citation_ref", "ref", "doi", "pmid"),
    )
    support_grade = _text(claim.get("support_grade"))
    source_tier = _text(claim.get("source_tier"))
    checked_at = _text(claim.get("checked_at"))
    expires_or_stale_after = _text(claim.get("expires_or_stale_after"))
    metadata_only = bool(claim.get("metadata_only_candidate_flag"))
    limiting_refs = _refs(
        claim.get("contradictory_or_limiting_refs"),
        preferred_keys=("citation_ref", "ref", "doi", "pmid"),
    )

    missing = _missing_required_refs(
        claim_id=claim_id,
        claim_ref=claim_ref,
        evidence_refs=evidence_refs,
        citation_refs=citation_refs,
        source_tier=source_tier,
        checked_at=checked_at,
    )
    blockers = _typed_blocker_candidates(
        claim_id=claim_id,
        missing=missing,
        support_grade=support_grade,
        metadata_only=metadata_only,
        limiting_refs=limiting_refs,
        expires_or_stale_after=expires_or_stale_after,
    )
    entry_status = "typed_blocker_candidate" if missing or blockers else "complete"
    entry = {
        "claim_id": claim_id,
        "claim_ref": claim_ref,
        "evidence_refs": evidence_refs,
        "citation_refs": citation_refs,
        "support_grade": support_grade,
        "source_tier": source_tier,
        "checked_at": checked_at,
        "expires_or_stale_after": expires_or_stale_after,
        "metadata_only_candidate_flag": metadata_only,
        "contradictory_or_limiting_refs": limiting_refs,
        "status": entry_status,
        "typed_blocker_candidate_refs": [
            candidate["candidate_ref"] for candidate in blockers
        ],
    }
    return entry, missing, blockers


def _missing_required_refs(
    *,
    claim_id: str,
    claim_ref: str | None,
    evidence_refs: list[str],
    citation_refs: list[str],
    source_tier: str | None,
    checked_at: str | None,
) -> list[dict[str, str]]:
    missing: list[dict[str, str]] = []
    if claim_ref is None:
        missing.append(_missing_ref(claim_id, "claim_ref", "missing_required_ref"))
    if not evidence_refs:
        missing.append(_missing_ref(claim_id, "evidence_refs", "missing_required_ref"))
    if not citation_refs:
        missing.append(_missing_ref(claim_id, "citation_refs", "missing_required_ref"))
    if source_tier is None:
        missing.append(_missing_ref(claim_id, "source_tier", "missing_required_field"))
    if checked_at is None:
        missing.append(_missing_ref(claim_id, "checked_at", "missing_required_field"))
    return missing


def _typed_blocker_candidates(
    *,
    claim_id: str,
    missing: list[dict[str, str]],
    support_grade: str | None,
    metadata_only: bool,
    limiting_refs: list[str],
    expires_or_stale_after: str | None,
) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    if support_grade not in VALID_SUPPORT_GRADES:
        candidates.append(_candidate(claim_id, "invalid_support_grade"))
    if missing:
        candidates.append(_candidate(claim_id, "missing_required_ref"))
    if metadata_only or support_grade == "metadata_only":
        candidates.append(_candidate(claim_id, "metadata_only_candidate"))
    if limiting_refs or support_grade == "contradictory":
        candidates.append(_candidate(claim_id, "contradictory_or_limiting_refs_present"))
    if expires_or_stale_after is not None:
        candidates.append(_candidate(claim_id, "support_stale_after_expiry"))
    return candidates


def _candidate(claim_id: str, reason: str) -> dict[str, Any]:
    return {
        "candidate_ref": f"claim-support:{claim_id}:{reason}",
        "blocker_type": "citation_support_or_export_blocker",
        "claim_id": claim_id,
        "reason": reason,
        "refs_only": True,
        "fail_open": True,
        "can_block_current_owner_action": False,
        "recommended_owner_action": _recommended_owner_action(reason),
        "authority_boundary": _authority_boundary(),
    }


def _recommended_owner_action(reason: str) -> str:
    if reason == "missing_required_ref":
        return "repair_claim_evidence_or_citation_refs"
    if reason == "invalid_support_grade":
        return "review_claim_support_grade"
    if reason == "metadata_only_candidate":
        return "replace_metadata_only_candidate_or_mark_unverified"
    if reason == "contradictory_or_limiting_refs_present":
        return "revise_or_downgrade_claim_boundary"
    if reason == "support_stale_after_expiry":
        return "refresh_claim_support_currentness"
    return "route_to_ai_reviewer"


def _missing_ref(claim_id: str, field: str, reason: str) -> dict[str, str]:
    return {"claim_id": claim_id, "field": field, "reason": reason}


def _refs(value: object, *, preferred_keys: tuple[str, ...]) -> list[str]:
    if isinstance(value, Mapping):
        ref = _ref_from_mapping(value, preferred_keys=preferred_keys)
        return [ref] if ref else []
    if isinstance(value, str):
        ref = _ref_from_value(value)
        return [ref] if ref else []
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray)):
        refs: list[str] = []
        for item in value:
            if isinstance(item, Mapping):
                ref = _ref_from_mapping(item, preferred_keys=preferred_keys)
            else:
                ref = _ref_from_value(item)
            if ref and ref not in refs:
                refs.append(ref)
        return refs
    return []


def _ref_from_mapping(
    value: Mapping[str, Any],
    *,
    preferred_keys: tuple[str, ...],
) -> str | None:
    for key in preferred_keys:
        ref = _text(value.get(key))
        if ref:
            if key == "doi" and not ref.startswith("doi:"):
                return f"doi:{ref}"
            if key == "pmid" and not ref.startswith("pmid:"):
                return f"pmid:{ref}"
            return ref
    return None


def _ref_from_value(value: object) -> str | None:
    return _text(value)


def _text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    text = value.strip()
    return text or None


def _source_refs() -> dict[str, list[str]]:
    return {
        "external_skill_refs": [
            "nature-skills@1cb9070:skills/nature-academic-search",
            "nature-skills@1cb9070:skills/nature-citation",
        ],
        "mas_contract_refs": ["citation_integrity_pack"],
    }


def _authority_boundary() -> dict[str, bool]:
    return {
        "can_write_mas_truth": False,
        "can_mutate_paper_body": False,
        "can_authorize_quality_verdict": False,
        "can_authorize_publication_readiness": False,
        "can_run_external_search": False,
    }


__all__ = [
    "SCHEMA_VERSION",
    "SURFACE_KIND",
    "build_claim_citation_support_matrix",
]
