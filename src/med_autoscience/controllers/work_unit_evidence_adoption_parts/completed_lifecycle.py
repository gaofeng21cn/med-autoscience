from __future__ import annotations

from pathlib import Path
from typing import Any

from med_autoscience.controllers import publication_work_unit_lifecycle
from med_autoscience.controllers.work_unit_evidence_adoption_parts import generic_completed_work_unit


def mark_owner_handoff_if_completed(
    *,
    study_root: Path,
    authorization_context: dict[str, Any],
    evidence_adoption: dict[str, Any],
    read_json_mapping,
    write_json_mapping,
) -> None:
    if _text(evidence_adoption.get("status")) != "completed":
        return
    if _text(evidence_adoption.get("recommended_next_route")) != generic_completed_work_unit.RECOMMENDED_NEXT_ROUTE:
        return
    result = evidence_adoption.get("result")
    if not isinstance(result, dict) or result.get("publication_gate_recheck_required") is not True:
        return
    work_unit_id = _text(authorization_context.get("work_unit_id"))
    if work_unit_id is None:
        return
    if work_unit_id == generic_completed_work_unit.PUBLICATION_GATE_RECHECK_WORK_UNIT:
        return
    lifecycle_path = publication_work_unit_lifecycle.stable_publication_work_unit_lifecycle_path(
        study_root=study_root,
    )
    source_eval_id = _text(authorization_context.get("publication_eval_id"))
    if source_eval_id is None:
        source_eval_id = _text(read_json_mapping(lifecycle_path).get("source_eval_id"))
    if source_eval_id is None:
        return
    report_ref = _text(evidence_adoption.get("report_ref"))
    payload: dict[str, Any] = {
        "schema_version": publication_work_unit_lifecycle.SCHEMA_VERSION,
        "source_eval_id": source_eval_id,
        "study_id": _text(authorization_context.get("study_id")) or study_root.name,
        "quest_id": _text(authorization_context.get("quest_id")) or study_root.name,
        "status": "owner_handoff",
        "work_unit": dict(authorization_context.get("next_work_unit") or {"unit_id": work_unit_id}),
        "unit_statuses": [{"unit_id": work_unit_id, "status": "owner_handoff"}],
        "gate_replay_status": "pending_recheck",
        "terminal_consumed": True,
        "recommended_next_route": evidence_adoption.get("recommended_next_route")
        or generic_completed_work_unit.RECOMMENDED_NEXT_ROUTE,
        "next_owner": _text(evidence_adoption.get("next_owner")) or generic_completed_work_unit.NEXT_OWNER,
        "closed_by": "controller_work_unit_evidence_adoption",
        "evidence_adoption": {
            key: evidence_adoption.get(key)
            for key in (
                "active_run_id",
                "report_ref",
                "created_at",
                "recommended_next_route",
                "status",
            )
            if key in evidence_adoption
        },
        "quality_gate_relaxation_allowed": False,
    }
    if report_ref is not None:
        payload["report_ref"] = report_ref
    write_json_mapping(lifecycle_path, payload)


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None
