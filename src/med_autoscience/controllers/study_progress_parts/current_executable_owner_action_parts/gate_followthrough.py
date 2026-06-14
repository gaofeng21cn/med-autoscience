from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.controllers.study_progress_parts.shared import (
    _mapping_copy,
    _non_empty_text,
)

from .action_types import QUALITY_REPAIR_ACTION

GATE_CLEARING_FOLLOWTHROUGH_CONSUMED_STATUSES = frozenset(
    {
        "closed",
        "completed",
        "executed",
        "fresh",
        "skipped_duplicate_eval",
        "skipped_stale_gate_replay_closed",
    }
)


def owner_action_from_gate_followthrough_current_work_unit(
    payload: Mapping[str, Any],
    *,
    surface_kind: str,
) -> dict[str, Any] | None:
    followthrough = _mapping_copy(payload.get("gate_clearing_batch_followthrough"))
    if _non_empty_text(followthrough.get("status")) not in GATE_CLEARING_FOLLOWTHROUGH_CONSUMED_STATUSES:
        return None
    if _non_empty_text(followthrough.get("gate_replay_status")) != "blocked":
        return None
    currentness = _mapping_copy(followthrough.get("work_unit_currentness"))
    if _non_empty_text(currentness.get("current_actionability_status")) != "actionable":
        return None
    if currentness.get("lacks_specific_blocker_object") is True:
        return None
    followthrough_work_unit_id = _non_empty_text(followthrough.get("work_unit_id"))
    explicit_work_unit_id = (
        _non_empty_text(currentness.get("explicit_publication_work_unit_id"))
        or followthrough_work_unit_id
        or _non_empty_text(_mapping_copy(followthrough.get("explicit_publication_work_unit")).get("unit_id"))
    )
    current_publication_work_unit = _mapping_copy(followthrough.get("current_publication_work_unit"))
    current_work_unit_id = (
        _non_empty_text(currentness.get("current_publication_work_unit_id"))
        or _non_empty_text(current_publication_work_unit.get("unit_id"))
    )
    if current_work_unit_id is None:
        return None
    if current_work_unit_id == explicit_work_unit_id:
        selected_work_unit_id = _non_empty_text(currentness.get("selected_publication_work_unit_id"))
        if current_work_unit_id not in {followthrough_work_unit_id, selected_work_unit_id}:
            return None
    lane = _non_empty_text(current_publication_work_unit.get("lane"))
    next_owner = lane if lane in {"write", "analysis-campaign", "finalize"} else "write"
    work_unit_fingerprint = _non_empty_text(currentness.get("current_work_unit_fingerprint"))
    source_eval_id = _non_empty_text(followthrough.get("source_eval_id"))
    source_ref = _non_empty_text(followthrough.get("latest_record_path"))
    owner_route_currentness_basis = _compact(
        {
            "source": "gate_clearing_batch_followthrough.actionable_current_work_unit",
            "source_eval_id": source_eval_id,
            "work_unit_id": current_work_unit_id,
            "work_unit_fingerprint": work_unit_fingerprint,
            "explicit_publication_work_unit_id": explicit_work_unit_id,
        }
    )
    return _compact(
        {
            "surface_kind": surface_kind,
            "schema_version": 1,
            "status": "ready",
            "source": "gate_clearing_batch_followthrough.actionable_current_work_unit",
            "next_owner": next_owner,
            "work_unit_id": current_work_unit_id,
            "work_unit_fingerprint": work_unit_fingerprint,
            "action_fingerprint": work_unit_fingerprint,
            "source_eval_id": source_eval_id,
            "owner_route_currentness_basis": owner_route_currentness_basis or None,
            "action_type": QUALITY_REPAIR_ACTION,
            "allowed_actions": [QUALITY_REPAIR_ACTION],
            "owner_receipt_required": True,
            "required_delta_kind": "publication_gate_actionable_repair_delta_or_typed_blocker",
            "target_surface": {
                "ref_kind": "publication_work_unit",
                "route_target": next_owner,
                "surface_ref": "artifacts/controller/repair_execution_evidence/latest.json",
                "gate_clearing_batch_ref": source_ref,
                "gate_replay_blockers": _text_items(followthrough.get("gate_replay_blockers")),
                "current_publication_work_unit": current_publication_work_unit or None,
            },
            "target_surface_specificity": "gate_followthrough_actionable_publication_work_unit",
            "acceptance_refs": [ref for ref in [source_ref] if ref],
            "authority_boundary": _authority_boundary(),
        }
    )


def _authority_boundary() -> dict[str, bool]:
    return {
        "refs_only": True,
        "can_write_runtime_owned_surfaces": False,
        "can_write_paper_or_package": False,
        "can_authorize_quality_verdict": False,
        "can_authorize_publication_ready": False,
    }


def _text_items(value: object) -> list[str]:
    if isinstance(value, str):
        text = _non_empty_text(value)
        return [text] if text is not None else []
    if not isinstance(value, list | tuple | set):
        return []
    result: list[str] = []
    for item in value:
        text = _non_empty_text(item)
        if text is not None and text not in result:
            result.append(text)
    return result


def _compact(payload: Mapping[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in payload.items() if value not in (None, "", [], {})}


__all__ = ["owner_action_from_gate_followthrough_current_work_unit"]
