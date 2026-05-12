from __future__ import annotations

from typing import Any


AUTHORITY_SCOPE = "submission_compliance_reviewer_input"
SUPPORT_PROVENANCE_KEYS = ("pubmed_id", "pmid", "doi", "publisher", "supplied_full_text", "full_text_path")


def _dict(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _list(value: object) -> list[object]:
    return value if isinstance(value, list) else []


def _has_value(value: object) -> bool:
    if isinstance(value, str):
        return bool(value.strip())
    return value is not None


def _has_medical_support_provenance(provenance: dict[str, Any]) -> bool:
    return any(_has_value(provenance.get(key)) for key in SUPPORT_PROVENANCE_KEYS)


def _project_ref(raw_ref: object) -> dict[str, Any]:
    ref = _dict(raw_ref)
    provenance = _dict(ref.get("provenance"))
    metadata_only = ref.get("metadata_only") is True
    blockers: list[str] = []
    if metadata_only:
        blockers.append("metadata_only_not_support_evidence")
    if not _has_medical_support_provenance(provenance):
        blockers.append("missing_medical_claim_full_text_or_indexed_provenance")
    eligible = not blockers
    return {
        "ref_id": ref.get("ref_id") if isinstance(ref.get("ref_id"), str) else None,
        "metadata_only": metadata_only,
        "provenance": provenance,
        "support_evidence_eligible": eligible,
        "blockers": blockers,
    }


def _project_claim(raw_claim: object) -> dict[str, Any]:
    claim = _dict(raw_claim)
    refs = [_project_ref(item) for item in _list(claim.get("candidate_citation_refs"))]
    eligible_refs = [item for item in refs if item["support_evidence_eligible"]]
    blockers = sorted({blocker for item in refs for blocker in item["blockers"]})
    support_grade = "supported" if eligible_refs else "unsupported"
    review_required_blocker = not eligible_refs
    return {
        "claim_segment_id": claim.get("claim_segment_id") if isinstance(claim.get("claim_segment_id"), str) else None,
        "candidate_citation_refs": refs,
        "support_grade": support_grade,
        "metadata_only_ref_count": sum(1 for item in refs if item["metadata_only"]),
        "review_required_blocker": review_required_blocker,
        "blockers": blockers if review_required_blocker else [],
        "export_ref_manager_note": "Export eligible supporting refs to the reference manager before submission.",
    }


def project_citation_integrity(*, claim_segments: list[dict[str, object]]) -> dict[str, Any]:
    projected_claims = [_project_claim(item) for item in claim_segments]
    return {
        "schema_version": 1,
        "authority_scope": AUTHORITY_SCOPE,
        "can_authorize_study_truth": False,
        "can_authorize_publication_verdict": False,
        "can_authorize_artifact_authority": False,
        "claim_segments": projected_claims,
        "review_required_blockers": [
            item["claim_segment_id"]
            for item in projected_claims
            if item["review_required_blocker"] and isinstance(item["claim_segment_id"], str)
        ],
    }
