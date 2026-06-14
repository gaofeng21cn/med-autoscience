from __future__ import annotations

from typing import Any

from med_autoscience.controllers.study_progress_parts.shared import _non_empty_text


def progress_ai_first_and_snapshot_fields(
    *,
    ai_first_default_entry_state: dict[str, Any],
    paper_orchestra_operator_projection: dict[str, Any],
    ai_first_observability_snapshots: dict[str, Any],
    ai_first_operations_dashboard: dict[str, Any],
    study_truth_snapshot: dict[str, Any],
    runtime_health_snapshot: dict[str, Any],
    authority_snapshot: dict[str, Any],
    module_surfaces: dict[str, Any],
    runtime_efficiency: dict[str, Any],
    paper_progress_stall: dict[str, Any],
    outer_supervision_slo: dict[str, Any],
    autonomy_slo_status: dict[str, Any] | None,
    ai_doctor_state: dict[str, Any],
    repair_recommendation: dict[str, Any],
    ai_repair_lifecycle: dict[str, Any] | None,
) -> dict[str, Any]:
    return {
        "ai_first_default_entry_state": ai_first_default_entry_state,
        "paper_orchestra_operator_projection": paper_orchestra_operator_projection or None,
        "ai_first_observability_snapshots": ai_first_observability_snapshots,
        "ai_first_operations_dashboard": ai_first_operations_dashboard,
        "study_truth_snapshot": study_truth_snapshot or None,
        "runtime_health_snapshot": runtime_health_snapshot or None,
        "authority_snapshot": authority_snapshot or None,
        "module_surfaces": module_surfaces,
        "runtime_efficiency": runtime_efficiency,
        "paper_progress_stall": paper_progress_stall,
        "outer_supervision_slo": outer_supervision_slo,
        "autonomy_slo": autonomy_slo_status,
        "ai_doctor_state": ai_doctor_state,
        "repair_recommendation": repair_recommendation or None,
        "ai_repair_lifecycle": ai_repair_lifecycle,
        "last_meaningful_progress_at": _last_meaningful_progress_at(autonomy_slo_status),
    }


def _last_meaningful_progress_at(autonomy_slo_status: dict[str, Any] | None) -> str | None:
    if autonomy_slo_status is None:
        return None
    return _non_empty_text(autonomy_slo_status.get("last_meaningful_progress_at"))
