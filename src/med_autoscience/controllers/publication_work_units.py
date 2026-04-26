from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping


_CLAIM_EVIDENCE_BLOCKERS = frozenset(
    {
        "claim_evidence_consistency_failed",
        "claim_evidence_map_missing",
        "claim_evidence_map_missing_or_incomplete",
        "claim_evidence_trace_missing",
        "missing_claim_evidence_map",
    }
)
_STORY_BLOCKERS = frozenset(
    {
        "storyline_evidence_map_missing",
        "storyline_not_publication_ready",
        "manuscript_story_incomplete",
        "missing_medical_story_contract",
        "medical_story_contract_missing",
        "story_contract_missing",
        "story_blocked",
        "reviewer_first_concerns_unresolved",
    }
)
_FIGURE_RESULTS_BLOCKERS = frozenset(
    {
        "figure_results_trace_incomplete",
        "figure_results_registry_missing",
        "figure_slots_missing",
        "figure_catalog_missing_or_incomplete",
        "figure_semantics_manifest_missing_or_incomplete",
        "results_narrative_map_missing_or_incomplete",
        "derived_analysis_manifest_missing_or_incomplete",
        "results_summary_missing",
        "missing_results_summary",
    }
)
_DISPLAY_REGISTRY_BLOCKERS = frozenset(
    {
        "display_registry_contract_missing",
        "display_registry_missing",
        "medical_display_registry_missing",
        "display_reporting_contract_missing",
        "registry_contract_mismatch",
    }
)
_LOCAL_ARCHITECTURE_BLOCKERS = frozenset(
    {
        "local_architecture_overview_shell_missing",
        "local_architecture_input_missing",
        "local_architecture_overview_missing",
        "missing_local_architecture_overview_shell",
        "missing_local_architecture_overview_inputs",
    }
)
_SUBMISSION_REFRESH_BLOCKERS = frozenset(
    {
        "stale_submission_minimal_authority",
        "submission_minimal_stale",
        "submission_minimal_missing",
        "current_package_outdated",
        "current_package_stale",
        "submission_package_stale",
        "submission_surface_qc_failure_present",
        "submission_hardening_incomplete",
        "study_delivery_stale",
        "complete_bundle_stage",
        "continue_bundle_stage",
    }
)
_TREATMENT_GAP_BLOCKERS = frozenset(
    {
        "treatment_gap_reporting_missing",
        "treatment_gap_table_missing",
        "treatment_gap_reporting_blocked",
        "treatment_gap_reporting_incomplete",
    }
)
_ACTIONABLE_OBJECT_KEYS = frozenset(
    {
        "claim_id",
        "claim_ref",
        "figure_id",
        "figure_ref",
        "table_id",
        "table_ref",
        "metric_id",
        "metric_ref",
        "citation_id",
        "citation_ref",
        "evidence_row_id",
        "evidence_row_ref",
        "package_artifact",
        "artifact_path",
        "source_path",
    }
)
_SPECIFICITY_QUESTIONS = (
    "Which exact claim, figure, table, metric, citation, evidence row, or package artifact is blocking the gate?",
    "Which durable source path proves the blocker and which controller surface should own the repair?",
)


def _text_sequence(payload: Mapping[str, Any], key: str) -> tuple[str, ...]:
    value = payload.get(key)
    if not isinstance(value, list):
        return ()
    return tuple(str(item).strip() for item in value if str(item).strip())


def _normalized_blockers(report: Mapping[str, Any]) -> tuple[str, ...]:
    blockers = {
        *_text_sequence(report, "blockers"),
        *_text_sequence(report, "medical_publication_surface_named_blockers"),
        *_text_sequence(report, "medical_publication_surface_blockers"),
        *_text_sequence(report, "reporting_blockers"),
    }
    delivery_status = str(report.get("study_delivery_status") or "").strip()
    if delivery_status:
        blockers.add(delivery_status)
    current_required_action = str(report.get("current_required_action") or "").strip()
    if current_required_action in {"complete_bundle_stage", "continue_bundle_stage"}:
        blockers.add(current_required_action)
    return tuple(sorted(blockers))


def _fingerprint(blockers: tuple[str, ...]) -> str:
    digest = hashlib.sha256(
        json.dumps(blockers, ensure_ascii=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()[:16]
    return f"publication-blockers::{digest}"


def _unit(unit_id: str, lane: str, summary: str) -> dict[str, str]:
    return {
        "unit_id": unit_id,
        "lane": lane,
        "summary": summary,
    }


def _mapping_has_actionable_object_ref(payload: Mapping[str, Any]) -> bool:
    for key in _ACTIONABLE_OBJECT_KEYS:
        if str(payload.get(key) or "").strip():
            return True
    return False


def _has_actionable_object_ref(report: Mapping[str, Any]) -> bool:
    if _mapping_has_actionable_object_ref(report):
        return True
    for key in ("blocker_details", "gate_blocker_details", "gaps"):
        value = report.get(key)
        if isinstance(value, Mapping) and _mapping_has_actionable_object_ref(value):
            return True
        if isinstance(value, list):
            for item in value:
                if isinstance(item, Mapping) and _mapping_has_actionable_object_ref(item):
                    return True
    return False


def derive_publication_work_units(report: Mapping[str, Any]) -> dict[str, Any]:
    blockers = _normalized_blockers(report)
    blocker_set = set(blockers)
    units: list[dict[str, str]] = []

    if blocker_set & _CLAIM_EVIDENCE_BLOCKERS:
        units.append(
            _unit(
                "analysis_claim_evidence_repair",
                "analysis-campaign",
                "Repair claim-evidence, story, figure, and results traceability blockers.",
            )
        )
    if blocker_set & _STORY_BLOCKERS:
        units.append(
            _unit(
                "manuscript_story_repair",
                "write",
                "Repair the paper story around the current evidence and claim boundary.",
            )
        )
    if blocker_set & _FIGURE_RESULTS_BLOCKERS:
        units.append(
            _unit(
                "figure_results_trace_repair",
                "write",
                "Repair figure and results traceability against the publication evidence surface.",
            )
        )
    if blocker_set & _TREATMENT_GAP_BLOCKERS:
        units.append(
            _unit(
                "treatment_gap_reporting_repair",
                "write",
                "Repair treatment-gap reporting so the clinical narrative is publication-ready.",
            )
        )
    if blocker_set & _SUBMISSION_REFRESH_BLOCKERS or "stale" in str(report.get("study_delivery_status") or ""):
        units.append(
            _unit(
                "submission_minimal_refresh",
                "finalize",
                "Refresh the stale submission_minimal package and current delivery bundle.",
            )
        )
    if blocker_set & _DISPLAY_REGISTRY_BLOCKERS:
        units.append(
            _unit(
                "display_reporting_contract_repair",
                "finalize",
                "Repair display registry and local architecture reporting contracts.",
            )
        )
    if blocker_set & _LOCAL_ARCHITECTURE_BLOCKERS:
        units.append(
            _unit(
                "local_architecture_overview_repair",
                "finalize",
                "Repair the local architecture overview shell and input reporting surface.",
            )
        )

    actionability_status = "actionable"
    specificity_questions: tuple[str, ...] = ()

    if not units and blockers and not _has_actionable_object_ref(report):
        actionability_status = "blocked_by_non_actionable_gate"
        specificity_questions = _SPECIFICITY_QUESTIONS
        units.append(
            _unit(
                "gate_needs_specificity",
                "controller",
                "Ask the publication gate to identify concrete claim, display, evidence, citation, metric, or package-artifact targets.",
            )
        )
    elif not units:
        actionability_status = "actionable_review_required" if blockers else "clear_or_unspecified"
        units.append(
            _unit(
                "publication_gate_blocker_review",
                "review",
                "Review the current publication gate blockers and select the narrowest repair unit.",
            )
        )

    return {
        "fingerprint": _fingerprint(blockers),
        "blockers": list(blockers),
        "actionability_status": actionability_status,
        "specificity_questions": list(specificity_questions),
        "blocking_work_units": units,
        "next_work_unit": units[0],
    }
