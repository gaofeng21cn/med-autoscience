from __future__ import annotations

from typing import Any

from ..shared import _mapping_copy, _non_empty_text


def sync_supervision_from_user_visible_projection(payload: dict[str, Any]) -> dict[str, Any]:
    user_visible = _mapping_copy(payload.get("user_visible_projection"))
    user_supervision = _mapping_copy(user_visible.get("supervision"))
    supervision = _mapping_copy(payload.get("supervision"))
    active_run_id = (
        _non_empty_text(supervision.get("active_run_id"))
        or _non_empty_text(user_supervision.get("active_run_id"))
        or _non_empty_text(supervision.get("stale_active_run_id"))
    )
    if active_run_id is None:
        return payload
    if (
        _non_empty_text(payload.get("active_run_id")) is None
        and _non_empty_text(supervision.get("active_run_id")) == active_run_id
    ):
        updated = dict(payload)
        updated["active_run_id"] = active_run_id
        return updated
    if _non_empty_text(supervision.get("active_run_id")) is not None:
        return payload
    stale_active_run_id = _non_empty_text(supervision.get("stale_active_run_id"))
    if stale_active_run_id != active_run_id:
        return payload
    updated = dict(payload)
    supervision["active_run_id"] = active_run_id
    supervision.pop("stale_active_run_id", None)
    supervision.pop("liveness_suppressed_by", None)
    updated["active_run_id"] = active_run_id
    updated["supervision"] = supervision
    return updated


__all__ = ["sync_supervision_from_user_visible_projection"]
