from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any


_REQUIRED_DISPLAY_KEYS = {
    "time_to_event_discrimination_calibration_panel": ("time_to_event_discrimination_calibration_inputs.json", "time_to_event_discrimination_calibration_inputs_v1"),
    "time_to_event_risk_group_summary": ("time_to_event_grouped_inputs.json", "time_to_event_grouped_inputs_v1"),
    "time_to_event_decision_curve": ("time_to_event_decision_curve_inputs.json", "time_to_event_decision_curve_inputs_v1"),
    "multicenter_generalizability_overview": ("multicenter_generalizability_inputs.json", "multicenter_generalizability_inputs_v1"),
    "table2_time_to_event_performance_summary": ("time_to_event_performance_summary.json", "time_to_event_performance_summary_v1"),
}


_LEGACY_REQUIREMENT_KEY_ALIASES = {
    "time_to_event_risk_group_summary": ("kaplan_meier_grouped",),
}


_AUTHORITY_PAPER_SYNC_RELATIVE_PATHS = (
    "publication_style_profile.json",
    "display_overrides.json",
    "display_registry.json",
    "medical_reporting_contract.json",
    "methods_implementation_manifest.json",
    "results_narrative_map.json",
    "figure_semantics_manifest.json",
    "derived_analysis_manifest.json",
    "manuscript_safe_reproducibility_supplement.json",
    "endpoint_provenance_note.md",
    "draft.md",
    "cohort_flow.json",
    "submission_graphical_abstract.json",
    "tables/table2_performance_summary.md",
)


def _resolve_authority_paper_root(*, study_root: Path) -> Path | None:
    candidate = study_root / "paper"
    if not candidate.exists():
        return None
    return candidate


def _same_file_contents(*, source_path: Path, target_path: Path) -> bool:
    if not target_path.exists():
        return False
    return source_path.read_bytes() == target_path.read_bytes()


def _sync_authority_paper_truth(
    *,
    study_root: Path,
    paper_root: Path,
) -> dict[str, Any]:
    authority_paper_root = _resolve_authority_paper_root(study_root=study_root)
    summary: dict[str, Any] = {
        "status": "not_available",
        "source_paper_root": str(authority_paper_root) if authority_paper_root is not None else None,
        "target_paper_root": str(paper_root),
        "synced_files": [],
        "already_aligned": [],
        "missing_authority_files": [],
    }
    if authority_paper_root is None:
        return summary
    if authority_paper_root == paper_root:
        summary["status"] = "same_root"
        return summary

    synced_files: list[str] = []
    already_aligned: list[str] = []
    missing_authority_files: list[str] = []
    for relative_path in _AUTHORITY_PAPER_SYNC_RELATIVE_PATHS:
        source_path = authority_paper_root / relative_path
        if not source_path.exists():
            missing_authority_files.append(relative_path)
            continue
        target_path = paper_root / relative_path
        if _same_file_contents(source_path=source_path, target_path=target_path):
            already_aligned.append(relative_path)
            continue
        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, target_path)
        synced_files.append(str(target_path))

    summary["status"] = "synced" if synced_files else "already_aligned"
    summary["synced_files"] = synced_files
    summary["already_aligned"] = already_aligned
    summary["missing_authority_files"] = missing_authority_files
    return summary


def _normalize_required_display_registry(*, registry_payload: dict[str, Any]) -> bool:
    displays = registry_payload.get("displays")
    if not isinstance(displays, list):
        raise ValueError("display_registry.json missing displays list")
    updated = False
    for item in displays:
        if not isinstance(item, dict):
            continue
        raw_requirement_key = str(item.get("requirement_key") or "").strip()
        if not raw_requirement_key:
            continue
        for canonical_key, aliases in _LEGACY_REQUIREMENT_KEY_ALIASES.items():
            if raw_requirement_key not in aliases:
                continue
            item["requirement_key"] = canonical_key
            updated = True
            break
    return updated


def _require_binding(
    *,
    registry_payload: dict[str, Any],
    requirement_key: str,
) -> dict[str, str]:
    displays = registry_payload.get("displays")
    if not isinstance(displays, list):
        raise ValueError("display_registry.json missing displays list")
    for item in displays:
        if not isinstance(item, dict):
            continue
        if str(item.get("requirement_key") or "").strip() != requirement_key:
            continue
        display_id = str(item.get("display_id") or "").strip()
        catalog_id = str(item.get("catalog_id") or "").strip()
        display_kind = str(item.get("display_kind") or "").strip()
        if not display_id or not catalog_id or not display_kind:
            raise ValueError(f"display binding for {requirement_key} is incomplete")
        return {
            "display_id": display_id,
            "catalog_id": catalog_id,
            "display_kind": display_kind,
        }
    raise ValueError(f"missing required display binding: {requirement_key}")
