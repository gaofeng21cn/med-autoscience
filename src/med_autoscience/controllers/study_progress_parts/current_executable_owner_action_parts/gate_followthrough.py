from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.controllers.study_progress_parts.shared import (
    _mapping_copy,
    _non_empty_text,
)

from .action_types import QUALITY_REPAIR_ACTION
from .publication_repair import (
    _publication_eval_route_back_action,
    _specificity_derived_publication_work_units,
)

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
    selected_publication_work_unit = _mapping_copy(
        followthrough.get("selected_publication_work_unit")
    )
    selected_work_unit_id = (
        _non_empty_text(currentness.get("selected_publication_work_unit_id"))
        or _non_empty_text(selected_publication_work_unit.get("unit_id"))
    )
    explicit_work_unit_id = (
        _non_empty_text(currentness.get("explicit_publication_work_unit_id"))
        or followthrough_work_unit_id
        or _non_empty_text(_mapping_copy(followthrough.get("explicit_publication_work_unit")).get("unit_id"))
    )
    explicit_publication_work_unit = _mapping_copy(followthrough.get("explicit_publication_work_unit"))
    current_publication_work_unit = _mapping_copy(followthrough.get("current_publication_work_unit"))
    current_work_unit_id = (
        _non_empty_text(currentness.get("current_publication_work_unit_id"))
        or _non_empty_text(current_publication_work_unit.get("unit_id"))
    )
    selected_work_unit_overrides_current = (
        selected_work_unit_id is not None and selected_work_unit_id != current_work_unit_id
    )
    if selected_work_unit_overrides_current:
        current_publication_work_unit = selected_publication_work_unit
        if not current_publication_work_unit and selected_work_unit_id == explicit_work_unit_id:
            current_publication_work_unit = explicit_publication_work_unit
        current_work_unit_id = selected_work_unit_id
    if current_work_unit_id is None:
        return None
    work_unit_fingerprint = (
        _non_empty_text(currentness.get("selected_work_unit_fingerprint"))
        or _non_empty_text(currentness.get("selected_publication_work_unit_fingerprint"))
        or _non_empty_text(currentness.get("explicit_work_unit_fingerprint"))
        if selected_work_unit_overrides_current
        else None
    ) or _non_empty_text(currentness.get("current_work_unit_fingerprint"))
    derived = _publication_eval_specificity_work_unit_for_gate_followthrough(
        payload=payload,
        current_work_unit_id=current_work_unit_id,
        work_unit_fingerprint=work_unit_fingerprint,
    )
    if derived:
        current_publication_work_unit = _mapping_copy(derived.get("next_work_unit")) or current_publication_work_unit
        current_work_unit_id = _non_empty_text(current_publication_work_unit.get("unit_id")) or current_work_unit_id
    if current_work_unit_id == explicit_work_unit_id:
        selected_work_unit_id = _non_empty_text(currentness.get("selected_publication_work_unit_id"))
        if current_work_unit_id not in {followthrough_work_unit_id, selected_work_unit_id}:
            return None
    lane = _non_empty_text(current_publication_work_unit.get("lane"))
    next_owner = lane if lane in {"write", "analysis-campaign", "finalize"} else "write"
    work_unit_fingerprint = _non_empty_text(derived.get("fingerprint")) or work_unit_fingerprint
    source_eval_id = _non_empty_text(followthrough.get("source_eval_id"))
    source_ref = _non_empty_text(followthrough.get("latest_record_path"))
    owner_route_currentness_basis = _compact(
        {
            "source": "gate_clearing_batch_followthrough.actionable_current_work_unit",
            "source_eval_id": source_eval_id,
            "work_unit_id": current_work_unit_id,
            "work_unit_fingerprint": work_unit_fingerprint,
            "explicit_publication_work_unit_id": explicit_work_unit_id,
            "selected_publication_work_unit_id": selected_work_unit_id,
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
                "next_work_unit": _mapping_copy(derived.get("next_work_unit")) or None,
                "blocking_work_units": _mapping_items(derived.get("blocking_work_units")),
                "specificity_targets": _mapping_items(derived.get("specificity_targets")),
            },
            "target_surface_specificity": "gate_followthrough_actionable_publication_work_unit",
            "acceptance_refs": [ref for ref in [source_ref] if ref],
            "authority_boundary": _authority_boundary(),
        }
    )


def _publication_eval_specificity_work_unit_for_gate_followthrough(
    *,
    payload: Mapping[str, Any],
    current_work_unit_id: str,
    work_unit_fingerprint: str | None,
) -> dict[str, Any]:
    publication_eval = _mapping_copy(payload.get("publication_eval"))
    action = _publication_eval_route_back_action(publication_eval)
    if not action:
        source_publication_eval = _mapping_copy(publication_eval.get("source_publication_eval"))
        action = _publication_eval_route_back_action(source_publication_eval)
        if action:
            publication_eval = source_publication_eval
    if not action:
        return {}
    action_work_unit = _mapping_copy(action.get("next_work_unit"))
    action_work_unit_id = _non_empty_text(action_work_unit.get("unit_id"))
    if action_work_unit_id is not None and action_work_unit_id != current_work_unit_id:
        return {}
    action_fingerprint = _non_empty_text(action.get("work_unit_fingerprint"))
    if work_unit_fingerprint is not None and action_fingerprint not in {None, work_unit_fingerprint}:
        return {}
    derived = _specificity_derived_publication_work_units(
        action=action,
        publication_eval=publication_eval,
    )
    next_work_unit = _mapping_copy(derived.get("next_work_unit"))
    lane = _non_empty_text(next_work_unit.get("lane"))
    if lane not in {"write", "analysis-campaign"}:
        return {}
    if _non_empty_text(next_work_unit.get("unit_id")) is None:
        return {}
    return {
        **derived,
        "specificity_targets": _mapping_items(action.get("specificity_targets")),
    }


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


def _mapping_items(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list | tuple):
        return []
    return [dict(item) for item in value if isinstance(item, Mapping)]


def _compact(payload: Mapping[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in payload.items() if value not in (None, "", [], {})}


__all__ = ["owner_action_from_gate_followthrough_current_work_unit"]
