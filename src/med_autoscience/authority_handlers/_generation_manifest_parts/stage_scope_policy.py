"""Stage scope minimums and fixed review lane values."""

from __future__ import annotations

STAGE_MINIMUM_SCOPE = {
    "direction_and_route_selection": "analysis_generation",
    "baseline_and_evidence_setup": "analysis_generation",
    "bounded_analysis_campaign": "analysis_generation",
    "manuscript_authoring": "manuscript_generation",
    "review_and_quality_gate": "manuscript_generation",
    "finalize_and_publication_handoff": "publication_generation",
}
STAGE_FIXED_REVIEW_LANE = {
    "bounded_analysis_campaign": "statistical",
}
_SCOPE_RANK = {
    "analysis_generation": 0,
    "manuscript_generation": 1,
    "publication_generation": 2,
}

