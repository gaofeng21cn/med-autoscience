from __future__ import annotations

from pathlib import Path
from typing import Any

from .discovery_and_drift import _non_empty_text


MEDICAL_SURFACE_BLOCKER_ARTIFACTS: dict[str, tuple[tuple[str, str], ...]] = {
    "missing_medical_story_contract": (("medical_story_contract.json", "medical_story_contract"),),
    "medical_story_contract_missing": (("medical_story_contract.json", "medical_story_contract"),),
    "story_contract_missing": (("medical_story_contract.json", "medical_story_contract"),),
    "storyline_evidence_map_missing": (
        ("medical_story_contract.json", "medical_story_contract"),
        ("claim_evidence_map.json", "claim_evidence_map"),
    ),
    "claim_evidence_consistency_failed": (
        ("claim_evidence_map.json", "claim_evidence_map"),
        ("evidence_ledger.md", "evidence_ledger"),
    ),
    "claim_evidence_map_missing": (("claim_evidence_map.json", "claim_evidence_map"),),
    "claim_evidence_map_missing_or_incomplete": (("claim_evidence_map.json", "claim_evidence_map"),),
    "missing_claim_evidence_map": (("claim_evidence_map.json", "claim_evidence_map"),),
    "figure_semantics_manifest_missing_or_incomplete": (
        ("figure_semantics_manifest.json", "figure_semantics_manifest"),
        ("figures/figure_catalog.json", "figure_catalog"),
    ),
    "figure_catalog_missing_or_incomplete": (("figures/figure_catalog.json", "figure_catalog"),),
    "results_narrative_map_missing_or_incomplete": (("results_narrative_map.json", "results_narrative_map"),),
    "derived_analysis_manifest_missing_or_incomplete": (
        ("derived_analysis_manifest.json", "derived_analysis_manifest"),
    ),
    "reviewer_first_concerns_unresolved": (("review/review_ledger.json", "review_ledger"),),
    "submission_hardening_incomplete": (
        ("submission_minimal/submission_manifest.json", "submission_minimal_authority"),
    ),
}


def _append_blocking_artifact_ref(
    refs: list[dict[str, Any]],
    *,
    blocker: str,
    artifact_path: str | None,
    artifact_role: str,
    stale_reason: str | None = None,
    source_path: str | None = None,
) -> None:
    if artifact_path is None:
        return
    payload = {
        "blocker": blocker,
        "artifact_path": artifact_path,
        "artifact_role": artifact_role,
    }
    if stale_reason is not None:
        payload["stale_reason"] = stale_reason
    if source_path is not None:
        payload["source_path"] = source_path
    if payload not in refs:
        refs.append(payload)


def build_blocking_artifact_refs(
    *,
    blockers: list[str],
    paper_root: Path | None,
    submission_minimal_manifest_path: Path | None,
    submission_minimal_authority_stale_reason: str | None,
    study_delivery: dict[str, Any],
    medical_publication_surface_named_blockers: list[str],
    submission_surface_qc_failures: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    blocker_set = {str(item or "").strip() for item in blockers if str(item or "").strip()}
    if "stale_submission_minimal_authority" in blocker_set:
        _append_blocking_artifact_ref(
            refs,
            blocker="stale_submission_minimal_authority",
            artifact_path=str(submission_minimal_manifest_path) if submission_minimal_manifest_path else None,
            artifact_role="submission_minimal_authority",
            stale_reason=submission_minimal_authority_stale_reason,
        )
    if "stale_study_delivery_mirror" in blocker_set:
        _append_blocking_artifact_ref(
            refs,
            blocker="stale_study_delivery_mirror",
            artifact_path=_non_empty_text(study_delivery.get("delivery_manifest_path")),
            artifact_role="study_delivery_mirror",
            stale_reason=_non_empty_text(study_delivery.get("stale_reason")),
        )
    if paper_root is not None:
        named_blocker_set = {
            str(item or "").strip()
            for item in medical_publication_surface_named_blockers
            if str(item or "").strip()
        }
        for blocker in sorted(named_blocker_set):
            for relative_path, artifact_role in MEDICAL_SURFACE_BLOCKER_ARTIFACTS.get(blocker, ()):
                _append_blocking_artifact_ref(
                    refs,
                    blocker=blocker,
                    artifact_path=str(paper_root / relative_path),
                    artifact_role=artifact_role,
                )
        if named_blocker_set & {
            "display_registry_contract_missing",
            "display_registry_missing",
            "missing_display_registry",
            "invalid_display_registry",
            "medical_display_registry_missing",
            "display_reporting_contract_missing",
            "registry_contract_mismatch",
        }:
            _append_blocking_artifact_ref(
                refs,
                blocker="display_registry_contract_missing",
                artifact_path=str(paper_root / "display_registry.json"),
                artifact_role="display_registry",
            )
    for failure in submission_surface_qc_failures:
        if not isinstance(failure, dict):
            continue
        artifact_path = _non_empty_text(failure.get("source_markdown_path")) or _non_empty_text(
            failure.get("artifact_path")
        )
        _append_blocking_artifact_ref(
            refs,
            blocker="submission_surface_qc_failure_present",
            artifact_path=artifact_path,
            artifact_role="submission_surface_qc",
            stale_reason=_non_empty_text(failure.get("failure_reason")),
        )
    return refs
