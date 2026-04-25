from __future__ import annotations

from typing import Any


REPAIRABLE_MEDICAL_SURFACE_BLOCKERS = frozenset(
    {
        "missing_medical_story_contract",
        "claim_evidence_map_missing_or_incomplete",
        "figure_catalog_missing_or_incomplete",
        "table_catalog_missing_or_incomplete",
        "required_display_catalog_coverage_incomplete",
        "results_narrative_map_missing_or_incomplete",
        "figure_semantics_manifest_missing_or_incomplete",
        "derived_analysis_manifest_missing_or_incomplete",
        "undefined_methodology_labels_present",
        "treatment_gap_reporting_incomplete",
        "invalid_display_registry",
    }
)


def medical_surface_repair_blockers(gate_report: dict[str, Any]) -> set[str]:
    blockers = {
        str(item or "").strip()
        for item in (gate_report.get("medical_publication_surface_named_blockers") or [])
        if str(item or "").strip()
    }
    blockers.update(
        str(item or "").strip()
        for item in (gate_report.get("medical_publication_surface_blockers") or [])
        if str(item or "").strip()
    )
    if str(gate_report.get("medical_publication_surface_status") or "").strip() == "blocked":
        blockers.update(
            str(item or "").strip()
            for item in (gate_report.get("blockers") or [])
            if str(item or "").strip()
        )
    return blockers
