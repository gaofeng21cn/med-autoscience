from __future__ import annotations

from typing import Any, Mapping

from .shared import _mapping_copy, _non_empty_text, _read_json_object


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
