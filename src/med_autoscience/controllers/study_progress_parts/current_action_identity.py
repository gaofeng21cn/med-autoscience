from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def action_matches_canonical_executable_work_unit(
    *,
    action: Mapping[str, Any] | None,
    current_work_unit: Mapping[str, Any] | None,
    require_ready_status: bool = False,
) -> bool:
    current_action = _mapping(action)
    canonical_work_unit = _mapping(current_work_unit)
    if not current_action or _text(canonical_work_unit.get("status")) != "executable_owner_action":
        return False
    if require_ready_status and _text(current_action.get("status")) not in {None, "ready"}:
        return False
    owner = _text(canonical_work_unit.get("owner"))
    action_owner = _text(current_action.get("next_owner")) or _text(current_action.get("owner"))
    if owner is not None and action_owner != owner:
        return False
    action_type = _text(canonical_work_unit.get("action_type"))
    action_types = set(_dedupe_text([current_action.get("action_type"), *_text_items(current_action.get("allowed_actions"))]))
    if action_type is not None and action_type not in action_types:
        return False
    work_unit_id = _text(canonical_work_unit.get("work_unit_id"))
    if work_unit_id is not None and _text(current_action.get("work_unit_id")) != work_unit_id:
        return False
    fingerprint = _text(canonical_work_unit.get("work_unit_fingerprint")) or _text(
        canonical_work_unit.get("action_fingerprint")
    )
    action_fingerprint = _text(current_action.get("work_unit_fingerprint")) or _text(
        current_action.get("action_fingerprint")
    )
    if fingerprint is not None and action_fingerprint != fingerprint:
        return False
    return True


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _text_items(value: object) -> list[str]:
    if isinstance(value, str):
        text = _text(value)
        return [text] if text is not None else []
    if not isinstance(value, list | tuple | set):
        return []
    result: list[str] = []
    for item in value:
        text = _text(item)
        if text is not None and text not in result:
            result.append(text)
    return result


def _dedupe_text(items: list[object]) -> list[str]:
    result: list[str] = []
    for item in items:
        text = _text(item)
        if text is not None and text not in result:
            result.append(text)
    return result


__all__ = ["action_matches_canonical_executable_work_unit"]
