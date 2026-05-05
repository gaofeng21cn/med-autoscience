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


def medical_surface_display_repair_requested(
    gate_report: dict[str, Any],
    *,
    submission_minimal_repair_gate_blockers: frozenset[str],
) -> bool:
    if str(gate_report.get("medical_publication_surface_status") or "").strip() != "blocked":
        return False
    blockers = medical_surface_repair_blockers(gate_report)
    if blockers & REPAIRABLE_MEDICAL_SURFACE_BLOCKERS:
        return True
    if "claim_evidence_consistency_failed" in blockers:
        return True
    named_blockers = {
        str(item or "").strip()
        for key in ("medical_publication_surface_named_blockers", "medical_publication_surface_blockers")
        for item in (gate_report.get(key) or [])
        if str(item or "").strip()
    }
    if named_blockers:
        return not named_blockers <= submission_minimal_repair_gate_blockers
    return "medical_publication_surface_blocked" in _gate_blockers(gate_report)


def repairable_medical_surface(gate_report: dict[str, Any]) -> bool:
    blockers = medical_surface_repair_blockers(gate_report)
    return bool(blockers & REPAIRABLE_MEDICAL_SURFACE_BLOCKERS or "claim_evidence_consistency_failed" in blockers)


def _gate_blockers(gate_report: dict[str, Any]) -> set[str]:
    return {
        str(item or "").strip()
        for item in (gate_report.get("blockers") or [])
        if str(item or "").strip()
    }
