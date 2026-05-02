from __future__ import annotations

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
