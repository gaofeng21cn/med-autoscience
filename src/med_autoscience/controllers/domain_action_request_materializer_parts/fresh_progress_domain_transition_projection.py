from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def canonical_projection(
    *,
    action: Mapping[str, Any],
    progress: Mapping[str, Any],
    current_action: Mapping[str, Any],
) -> dict[str, Any]:
    projected = dict(action)
    next_action = _mapping(progress.get("next_action"))
    original_authority = _text(projected.get("authority"))
    original_source_surface = (
        _text(projected.get("source_surface"))
        or _text(projected.get("source"))
        or "domain_transition"
    )
    original_handoff = _mapping(projected.get("handoff_packet"))
    projected["authority"] = "mas_next_action_envelope"
    projected["source_surface"] = "mas_next_action_envelope"
    projected["projection_source_surface"] = original_source_surface
    projected["current_action_source"] = (
        _text(current_action.get("source"))
        or _text(current_action.get("source_surface"))
        or original_source_surface
    )
    projected["source_ref"] = _text(current_action.get("source_ref")) or _text(
        projected.get("source_ref")
    )
    projected["work_unit_id"] = (
        _text(current_action.get("work_unit_id"))
        or _work_unit_id(current_action.get("next_work_unit"))
        or _text(projected.get("work_unit_id"))
        or _text(projected.get("next_work_unit"))
    )
    projected["next_action"] = dict(next_action)
    projected["domain_transition_projection"] = {
        "authority": original_authority,
        "source_surface": original_source_surface,
        "current_action_source": projected["current_action_source"],
        "source_ref": projected.get("source_ref"),
    }
    handoff = dict(original_handoff)
    handoff["authority"] = "mas_next_action_envelope"
    handoff["source_surface"] = "mas_next_action_envelope"
    handoff["projection_source_surface"] = original_source_surface
    handoff["current_action_source"] = projected["current_action_source"]
    if projected.get("source_ref") is not None:
        handoff["source_ref"] = projected["source_ref"]
    projected["handoff_packet"] = handoff
    return {key: value for key, value in projected.items() if value is not None}


def _work_unit_id(value: object) -> str | None:
    if isinstance(value, Mapping):
        return _text(value.get("work_unit_id")) or _text(value.get("unit_id"))
    return _text(value)


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = ["canonical_projection"]
