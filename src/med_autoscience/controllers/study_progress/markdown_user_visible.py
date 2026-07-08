from __future__ import annotations

from typing import Any, Mapping

from .publication_runtime import _blocker_label
from .shared import (
    _current_stage_label,
    _display_text,
    _non_empty_text,
    _normalize_study_progress_payload,
)
from .user_visible_projection import build_user_visible_projection


def _current_user_visible_projection(payload: Mapping[str, Any]) -> dict[str, Any]:
    projection = payload.get("user_visible_projection")
    if (
        isinstance(projection, Mapping)
        and projection.get("schema_version") == 2
        and _non_empty_text(projection.get("writer_state")) is not None
        and _non_empty_text(projection.get("user_next")) is not None
        and _non_empty_text(projection.get("reason")) is not None
    ):
        return dict(projection)
    return {}


def _normalized_payload_with_user_visible(payload: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    normalized_payload = _normalize_study_progress_payload(payload)
    user_visible_projection = _current_user_visible_projection(normalized_payload)
    if not user_visible_projection:
        user_visible_projection = build_user_visible_projection(normalized_payload)
        normalized_payload["user_visible_projection"] = user_visible_projection
    return normalized_payload, user_visible_projection


def _progress_blocker_labels(payload: Mapping[str, Any]) -> list[str]:
    user_visible = _current_user_visible_projection(payload)
    blocker_source = user_visible.get("current_blockers") if user_visible else payload.get("current_blockers")
    blockers: list[str] = []
    for item in blocker_source or []:
        if not str(item).strip():
            continue
        label = _blocker_label(item) or str(item)
        if label not in blockers:
            blockers.append(label)
    return blockers


def _current_stage_context(
    payload: Mapping[str, Any],
    status_human_view: Mapping[str, Any],
    user_visible_projection: Mapping[str, Any],
) -> tuple[str, str]:
    if user_visible_projection:
        return (
            _non_empty_text(user_visible_projection.get("state_label"))
            or _non_empty_text(user_visible_projection.get("current_stage_label"))
            or "状态需要检查",
            _non_empty_text(user_visible_projection.get("state_summary"))
            or _non_empty_text(user_visible_projection.get("current_stage_summary"))
            or "",
        )
    has_status_contract = isinstance(payload.get("status_narration_contract"), Mapping)
    current_stage = (
        _non_empty_text(status_human_view.get("current_stage_label"))
        or _current_stage_label(payload.get("current_stage"))
        or "未知"
    )
    if has_status_contract:
        current_judgment = _non_empty_text(status_human_view.get("status_summary")) or _non_empty_text(
            status_human_view.get("latest_update")
        )
    else:
        current_judgment = _non_empty_text(status_human_view.get("latest_update")) or _non_empty_text(
            status_human_view.get("status_summary")
        )
    if not current_judgment:
        current_judgment = _display_text(payload.get("current_stage_summary")) or str(
            payload.get("current_stage_summary") or ""
        ).strip()
    return current_stage, current_judgment


def _next_step_summary(
    payload: Mapping[str, Any],
    status_human_view: Mapping[str, Any],
    user_visible_projection: Mapping[str, Any],
) -> str:
    if user_visible_projection:
        return (
            _non_empty_text(user_visible_projection.get("next_system_action"))
            or _non_empty_text(user_visible_projection.get("next_step"))
            or ""
        )
    return _non_empty_text(status_human_view.get("next_step")) or str(payload.get("next_system_action") or "").strip()
