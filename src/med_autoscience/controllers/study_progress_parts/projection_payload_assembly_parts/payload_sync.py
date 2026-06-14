from __future__ import annotations

from typing import Any

from ..shared import _mapping_copy


def sync_progress_first_owner_action_admission(payload: dict[str, Any]) -> dict[str, Any]:
    monitoring = _mapping_copy(payload.get("progress_first_monitoring_summary"))
    admission = _mapping_copy(monitoring.get("owner_action_admission"))
    if not admission:
        return payload
    updated = dict(payload)
    updated["owner_action_admission"] = admission
    return updated


def sync_study_macro_state_from_user_visible_projection(payload: dict[str, Any]) -> dict[str, Any]:
    user_visible = _mapping_copy(payload.get("user_visible_projection"))
    macro_state = _mapping_copy(user_visible.get("study_macro_state"))
    if not macro_state:
        return payload
    updated = dict(payload)
    updated["study_macro_state"] = macro_state
    return updated


__all__ = [
    "sync_progress_first_owner_action_admission",
    "sync_study_macro_state_from_user_visible_projection",
]
