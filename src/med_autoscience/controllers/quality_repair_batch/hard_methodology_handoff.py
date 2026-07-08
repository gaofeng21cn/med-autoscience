from __future__ import annotations

from collections.abc import Mapping
from typing import Any


NEXT_OWNER = "analysis_harmonization_owner"
NEXT_WORK_UNIT = "unit_harmonized_external_validation_rerun"
BLOCKED_REASON = "unit_harmonized_rerun_required"


def target_from_publication_work_units(publication_work_unit_payload: Mapping[str, Any]) -> dict[str, Any] | None:
    target = publication_work_unit_payload.get("hard_methodology_target")
    return dict(target) if isinstance(target, Mapping) else None


def owner_handoff_record(
    *,
    schema_version: int,
    study_id: str,
    quest_id: str,
    source_eval_id: str | None,
    source_eval_artifact_path: str,
    source_summary_id: str | None,
    source_summary_artifact_path: str,
    authority_route_gate: Mapping[str, Any],
    paper_owner_surface_prepare: Mapping[str, Any],
    gate_clearing_result: Mapping[str, Any],
    hard_methodology_target: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": schema_version,
        "source_eval_id": source_eval_id,
        "source_eval_artifact_path": source_eval_artifact_path,
        "source_summary_id": source_summary_id,
        "source_summary_artifact_path": source_summary_artifact_path,
        "status": "blocked",
        "ok": False,
        "quest_id": quest_id,
        "study_id": study_id,
        "blocked_reason": BLOCKED_REASON,
        "next_owner": NEXT_OWNER,
        "next_work_unit": NEXT_WORK_UNIT,
        "hard_methodology_target": dict(hard_methodology_target),
        "gate_clearing_batch": dict(gate_clearing_result),
        "authority_route_gate": dict(authority_route_gate),
        "paper_owner_surface_prepare": dict(paper_owner_surface_prepare),
        "quality_gate_relaxation_allowed": False,
        "current_package_write_allowed": False,
    }


__all__ = [
    "BLOCKED_REASON",
    "NEXT_OWNER",
    "NEXT_WORK_UNIT",
    "owner_handoff_record",
    "target_from_publication_work_units",
]
