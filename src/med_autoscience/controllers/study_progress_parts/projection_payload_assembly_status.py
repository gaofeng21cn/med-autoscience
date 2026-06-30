from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from .shared import _mapping_copy, _non_empty_text, _read_json_object


def stage_native_current_owner_action(*, study_root: Path) -> dict[str, Any] | None:
    next_action = _read_json_object(study_root / "control" / "next_action.json")
    if not isinstance(next_action, Mapping):
        return None
    if _non_empty_text(next_action.get("status")) != "ready_for_owner_action":
        return None
    action_type = _non_empty_text(next_action.get("action_id")) or _non_empty_text(
        next_action.get("action_type")
    )
    owner = _non_empty_text(next_action.get("owner")) or _non_empty_text(
        next_action.get("next_owner")
    )
    if action_type is None and owner is None:
        return None
    work_unit_id = _non_empty_text(next_action.get("next_work_unit")) or action_type
    source_ref = study_root / "control" / "next_action.json"
    return {
        "surface_kind": "stage_native_workspace_next_action_diagnostic",
        "schema_version": 1,
        "status": "diagnostic_only",
        "source": "stage_native_workspace_next_action",
        "authority": "stage_native_workspace_next_action_diagnostic_only",
        "legacy_surface_role": "diagnostic_only",
        "replacement_authority": "NextActionEnvelope.action_family",
        "next_owner": owner,
        "work_unit_id": work_unit_id,
        "action_type": action_type,
        "allowed_actions": [action_type] if action_type is not None else [],
        "owner_receipt_required": False,
        "required_delta_kind": _non_empty_text(
            next_action.get("required_delta_kind")
        )
        or _non_empty_text(next_action.get("required_output_surface")),
        "target_surface": {
            "ref_kind": "stage_native_next_action",
            "surface_ref": _non_empty_text(next_action.get("source_surface")),
            "current_stage_id": _non_empty_text(next_action.get("current_stage_id")),
            "stage_index_ref": _non_empty_text(next_action.get("stage_index_ref")),
            "required_output_surface": _non_empty_text(
                next_action.get("required_output_surface")
            ),
        },
        "source_ref": str(source_ref),
        "authority_boundary": {
            "refs_only": True,
            "next_action_authority": False,
            "can_write_runtime_owned_surfaces": False,
            "can_write_paper_or_package": False,
            "can_authorize_quality_verdict": False,
            "can_authorize_publication_ready": False,
            "stage_native_next_action_is_control_projection": True,
            "stage_native_next_action_is_diagnostic_only": True,
        },
    }


def apply_runtime_medical_publication_surface_user_visible_status(
    payload: dict[str, Any],
) -> dict[str, Any]:
    blockers = _current_runtime_medical_publication_surface_blockers(payload)
    if not blockers:
        return payload
    updated = dict(payload)
    updated["current_blockers"] = _merge_blockers(updated.get("current_blockers"), blockers)
    user_visible = _mapping_copy(updated.get("user_visible_projection"))
    if user_visible:
        user_visible["current_blockers"] = _merge_blockers(user_visible.get("current_blockers"), blockers)
        user_visible["state_summary"] = _non_empty_text(user_visible.get("state_summary")) or blockers[0]
        user_visible["current_stage_summary"] = (
            _non_empty_text(user_visible.get("current_stage_summary")) or user_visible["state_summary"]
        )
        updated["user_visible_projection"] = user_visible
    status_contract = _mapping_copy(updated.get("status_narration_contract"))
    if status_contract:
        status_contract["current_blockers"] = _merge_blockers(status_contract.get("current_blockers"), blockers)[:8]
        updated["status_narration_contract"] = status_contract
    return updated


def _current_runtime_medical_publication_surface_blockers(payload: Mapping[str, Any]) -> list[str]:
    surface = _mapping_copy(payload.get("runtime_medical_publication_surface"))
    if _non_empty_text(surface.get("status")) != "blocked":
        return []
    return [
        text
        for item in surface.get("blocker_summaries") or surface.get("blockers") or []
        if (text := _non_empty_text(item)) is not None
    ]


def _merge_blockers(existing: object, blockers: list[str]) -> list[str]:
    merged: list[str] = []
    for item in [*(existing or []), *blockers]:
        text = _non_empty_text(item)
        if text is not None and text not in merged:
            merged.append(text)
    return merged
