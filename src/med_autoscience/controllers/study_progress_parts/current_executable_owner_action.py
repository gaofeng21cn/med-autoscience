from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .shared import _mapping_copy, _non_empty_text

SURFACE_KIND = "current_executable_owner_action"


def build_current_executable_owner_action(payload: Mapping[str, Any]) -> dict[str, Any] | None:
    next_forced_delta = _mapping_copy(payload.get("next_forced_delta"))
    owner_action = _mapping_copy(next_forced_delta.get("owner_action"))
    owner = _non_empty_text(owner_action.get("next_owner")) or _non_empty_text(
        next_forced_delta.get("next_owner")
    )
    work_unit_id = _non_empty_text(owner_action.get("work_unit_id")) or _non_empty_text(
        next_forced_delta.get("work_unit_id")
    )
    allowed_actions = _text_items(owner_action.get("allowed_actions")) or _text_items(
        next_forced_delta.get("allowed_actions")
    )
    if owner is None and work_unit_id is None and not allowed_actions:
        return _from_domain_transition(payload)
    return _compact(
        {
            "surface_kind": SURFACE_KIND,
            "schema_version": 1,
            "status": "ready",
            "source": "study_progress.next_forced_delta.owner_action",
            "next_owner": owner,
            "work_unit_id": work_unit_id,
            "allowed_actions": allowed_actions,
            "owner_receipt_required": owner_action.get("owner_receipt_required") is not False,
            "required_delta_kind": _non_empty_text(next_forced_delta.get("required_delta_kind")),
            "target_surface": _mapping_copy(next_forced_delta.get("target_surface")) or None,
            "target_surface_specificity": _non_empty_text(
                next_forced_delta.get("target_surface_specificity")
            ),
            "acceptance_refs": _text_items(next_forced_delta.get("acceptance_refs")),
            "authority_boundary": _authority_boundary(),
        }
    )


def owner_action_next_step(action: Mapping[str, Any]) -> str | None:
    owner = _non_empty_text(action.get("next_owner"))
    actions = _text_items(action.get("allowed_actions"))
    work_unit_id = _non_empty_text(action.get("work_unit_id"))
    if owner is None and not actions and work_unit_id is None:
        return None
    owner_text = f"{owner} owner" if owner is not None else "当前 owner"
    action_text = f"执行 {actions[0]}" if actions else "处理当前 owner action"
    work_unit_text = f"，处理 work unit {work_unit_id}" if work_unit_id is not None else ""
    return f"等待 {owner_text} {action_text}{work_unit_text}，产出 owner receipt、typed blocker 或下一 owner handoff。"


def _from_domain_transition(payload: Mapping[str, Any]) -> dict[str, Any] | None:
    transition = _mapping_copy(payload.get("domain_transition"))
    next_work_unit = _mapping_copy(transition.get("next_work_unit"))
    owner = _non_empty_text(transition.get("owner")) or _non_empty_text(transition.get("route_target"))
    work_unit_id = _non_empty_text(next_work_unit.get("unit_id"))
    action = _non_empty_text(transition.get("controller_action"))
    if owner is None and work_unit_id is None and action is None:
        return None
    return _compact(
        {
            "surface_kind": SURFACE_KIND,
            "schema_version": 1,
            "status": "ready",
            "source": "domain_transition",
            "next_owner": owner,
            "work_unit_id": work_unit_id,
            "allowed_actions": [action] if action is not None else [],
            "owner_receipt_required": True,
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


__all__ = [
    "SURFACE_KIND",
    "build_current_executable_owner_action",
    "owner_action_next_step",
]
